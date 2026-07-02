"""DataUpdateCoordinator for CHMI Weather."""

from __future__ import annotations

import logging
from collections.abc import Mapping
from datetime import UTC, date, datetime, timedelta, tzinfo
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import ChmiApiClient, ChmiApiError
from .const import (
    CONF_OBSERVATION_INTERVAL_MINUTES,
    CONF_STATION_ID,
    CONF_SUPPORTED_ELEMENTS_BY_INTERVAL,
    CONF_UPDATE_INTERVAL,
    DEFAULT_OBSERVATION_INTERVAL_MINUTES,
    DOMAIN,
    ELEMENT_PRECIPITATION_1H,
    WEATHER_CONDITION_ELEMENTS,
)
from .models import ChmiDailySummary, ChmiObservation

_LOGGER = logging.getLogger(__name__)


class ChmiDataUpdateCoordinator(DataUpdateCoordinator[ChmiObservation]):
    """Coordinate polling of one CHMI OpenData station file."""

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        client: ChmiApiClient,
    ) -> None:
        """Initialize the coordinator."""
        self.config_entry = config_entry
        self.client = client
        self.last_observation: ChmiObservation | None = None
        self.last_successful_poll: datetime | None = None
        self.precipitation_timezone = _hass_timezone(hass)
        self.observation_interval_minutes = max(
            1,
            int(
                config_entry.data.get(
                    CONF_OBSERVATION_INTERVAL_MINUTES,
                    DEFAULT_OBSERVATION_INTERVAL_MINUTES,
                )
            ),
        )
        self.precipitation_1h_interval_minutes = _interval_with_supported_element(
            config_entry.data.get(CONF_SUPPORTED_ELEMENTS_BY_INTERVAL),
            ELEMENT_PRECIPITATION_1H,
        )
        self.weather_condition_interval_minutes = _interval_with_any_supported_element(
            config_entry.data.get(CONF_SUPPORTED_ELEMENTS_BY_INTERVAL),
            WEATHER_CONDITION_ELEMENTS,
        )

        configured_update_interval_minutes = int(
            config_entry.options.get(
                CONF_UPDATE_INTERVAL,
                self.observation_interval_minutes,
            )
        )
        self.update_interval_minutes = max(
            1,
            min(
                configured_update_interval_minutes,
                self.observation_interval_minutes,
            ),
        )

        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{config_entry.data[CONF_STATION_ID]}",
            config_entry=config_entry,
            update_interval=timedelta(minutes=self.update_interval_minutes),
            always_update=True,
        )

    async def _async_update_data(self) -> ChmiObservation:
        """Fetch the latest observation from CHMI OpenData."""
        station_id = self.config_entry.data[CONF_STATION_ID]
        previous_observation = self.last_observation
        try:
            observation = await self.client.async_get_current_observations(
                station_id,
                interval_minutes=self.observation_interval_minutes,
                precipitation_timezone=self.precipitation_timezone,
                precipitation_1h_interval_minutes=(
                    self.precipitation_1h_interval_minutes
                ),
                weather_condition_interval_minutes=(
                    self.weather_condition_interval_minutes
                ),
            )
        except ChmiApiError as err:
            raise UpdateFailed(f"Failed to update CHMI observations: {err}") from err
        except Exception as err:
            raise UpdateFailed(
                "Unexpected error while updating CHMI observations"
            ) from err

        daily_summary_date = datetime.now(self.precipitation_timezone).date() - (
            timedelta(days=1)
        )
        try:
            daily_summary = await self.client.async_get_recent_daily_summary(
                station_id,
                daily_summary_date,
            )
        except ChmiApiError as err:
            _LOGGER.debug("Failed to update CHMI recent daily summary: %s", err)
            if (
                previous_observation is not None
                and previous_observation.daily_summary_date == daily_summary_date
            ):
                _copy_daily_summary(observation, previous_observation)
            elif previous_observation is not None and _same_month(
                previous_observation.daily_summary_date,
                daily_summary_date,
            ):
                _copy_month_precipitation(observation, previous_observation)
        else:
            _apply_daily_summary(
                observation,
                daily_summary,
                previous_observation,
                self.precipitation_timezone,
            )

        self.last_observation = observation
        self.last_successful_poll = datetime.now(UTC)
        _LOGGER.debug(
            "Updated CHMI observation for %s at %s; poll completed at %s",
            station_id,
            observation.observed_at,
            self.last_successful_poll,
        )
        return observation


def _hass_timezone(hass: HomeAssistant) -> tzinfo:
    config = getattr(hass, "config", None)
    time_zone = getattr(config, "time_zone", None)
    if not time_zone:
        return UTC

    try:
        return ZoneInfo(str(time_zone))
    except ZoneInfoNotFoundError:
        _LOGGER.warning("Invalid Home Assistant timezone %s; using UTC", time_zone)
        return UTC


def _interval_with_supported_element(
    elements_by_interval: object,
    element: str,
) -> int | None:
    """Return the observation interval that advertises an element."""
    if not isinstance(elements_by_interval, Mapping):
        return None

    for interval, elements in elements_by_interval.items():
        if not isinstance(elements, list | tuple | set):
            continue
        if element not in {str(item) for item in elements}:
            continue
        try:
            return max(1, int(interval))
        except (TypeError, ValueError):
            continue
    return None


def _interval_with_any_supported_element(
    elements_by_interval: object,
    elements: tuple[str, ...],
) -> int | None:
    """Return the first interval that advertises any of the requested elements."""
    if not isinstance(elements_by_interval, Mapping):
        return None

    requested_elements = set(elements)
    for interval, interval_elements in elements_by_interval.items():
        if not isinstance(interval_elements, list | tuple | set):
            continue
        if requested_elements.isdisjoint({str(item) for item in interval_elements}):
            continue
        try:
            return max(1, int(interval))
        except (TypeError, ValueError):
            continue
    return None


def _apply_daily_summary(
    observation: ChmiObservation,
    daily_summary: ChmiDailySummary,
    previous_observation: ChmiObservation | None = None,
    precipitation_timezone: tzinfo = UTC,
) -> None:
    """Attach recent daily summary values to a current observation."""
    observation.daily_summary_date = daily_summary.summary_date
    observation.yesterday_precipitation = daily_summary.yesterday_precipitation
    observation.yesterday_temperature_max = daily_summary.yesterday_temperature_max
    observation.yesterday_temperature_min = daily_summary.yesterday_temperature_min
    observation.yesterday_wind_gust_max = daily_summary.yesterday_wind_gust_max
    observation.month_precipitation_chmi = _month_precipitation_with_current_fallback(
        observation,
        daily_summary,
        precipitation_timezone,
    )
    if (
        observation.month_precipitation_chmi is None
        and previous_observation is not None
        and _same_month(
            previous_observation.daily_summary_date,
            daily_summary.summary_date,
        )
    ):
        observation.month_precipitation_chmi = (
            previous_observation.month_precipitation_chmi
        )


def _copy_daily_summary(
    observation: ChmiObservation,
    previous_observation: ChmiObservation,
) -> None:
    """Keep same-day daily summary values during temporary daily endpoint errors."""
    observation.daily_summary_date = previous_observation.daily_summary_date
    observation.yesterday_precipitation = previous_observation.yesterday_precipitation
    observation.yesterday_temperature_max = (
        previous_observation.yesterday_temperature_max
    )
    observation.yesterday_temperature_min = (
        previous_observation.yesterday_temperature_min
    )
    observation.yesterday_wind_gust_max = previous_observation.yesterday_wind_gust_max
    observation.month_precipitation_chmi = previous_observation.month_precipitation_chmi


def _copy_month_precipitation(
    observation: ChmiObservation,
    previous_observation: ChmiObservation,
) -> None:
    """Keep same-month precipitation total during incomplete daily updates."""
    observation.daily_summary_date = previous_observation.daily_summary_date
    observation.month_precipitation_chmi = previous_observation.month_precipitation_chmi


def _same_month(left: date | None, right: date) -> bool:
    """Return whether both dates are in the same calendar month."""
    return left is not None and left.year == right.year and left.month == right.month


def _month_precipitation_with_current_fallback(
    observation: ChmiObservation,
    daily_summary: ChmiDailySummary,
    precipitation_timezone: tzinfo,
) -> float | None:
    """Return monthly precipitation, supplementing missing daily SRA if possible."""
    month_precipitation = daily_summary.month_precipitation_chmi
    if daily_summary.yesterday_precipitation is not None:
        return month_precipitation

    fallback_precipitation = _precipitation_total_for_date(
        observation,
        daily_summary.summary_date,
        precipitation_timezone,
    )
    if fallback_precipitation is None:
        return month_precipitation

    return round((month_precipitation or 0.0) + fallback_precipitation, 3)


def _precipitation_total_for_date(
    observation: ChmiObservation,
    precipitation_date: date,
    precipitation_timezone: tzinfo,
) -> float | None:
    """Return interval precipitation total for one Home Assistant local date."""
    samples = [
        sample
        for sample in observation.precipitation_samples
        if sample.observed_at.astimezone(precipitation_timezone).date()
        == precipitation_date
    ]
    if not samples:
        return None
    return round(sum(sample.amount for sample in samples), 3)
