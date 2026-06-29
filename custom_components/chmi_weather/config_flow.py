"""Config flow for CHMI Weather."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import (
    ChmiApiClient,
    ChmiApiConnectionError,
    ChmiApiDataError,
    ChmiApiError,
    has_usable_observation,
)
from .const import (
    CONF_DIAGNOSTIC_SENSORS,
    CONF_LATITUDE,
    CONF_LONGITUDE,
    CONF_OBSERVATION_INTERVAL_MINUTES,
    CONF_STATION_ID,
    CONF_STATION_NAME,
    CONF_SUPPORTED_ELEMENTS,
    CONF_SUPPORTED_ELEMENTS_BY_INTERVAL,
    CONF_UPDATE_INTERVAL,
    DEFAULT_DIAGNOSTIC_SENSORS,
    DEFAULT_OBSERVATION_INTERVAL_MINUTES,
    DEFAULT_STATION_SELECTION_LIMIT,
    DOMAIN,
)
from .models import ChmiNearestStation


class ChmiWeatherConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for CHMI Weather."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize config flow state."""
        super().__init__()
        self._nearest_stations: tuple[ChmiNearestStation, ...] = ()
        self._location_input: dict[str, Any] = _default_location_input()

    async def async_step_user(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Ask for GPS coordinates used to suggest nearby stations."""
        errors: dict[str, str] = {}

        if user_input is not None:
            self._location_input = _normalize_location_input(user_input)
            self._nearest_stations, errors = await _async_get_nearest_stations(
                self.hass,
                self._location_input[CONF_LATITUDE],
                self._location_input[CONF_LONGITUDE],
            )

            if not errors:
                return await self.async_step_station()
        else:
            self._location_input = _default_location_input(self.hass)

        return self.async_show_form(
            step_id="user",
            data_schema=_location_schema(self._location_input),
            errors=errors,
        )

    async def async_step_station(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Let the user select one of the nearest stations."""
        errors: dict[str, str] = {}
        if not self._nearest_stations:
            return await self.async_step_user()

        if user_input is not None:
            station_id = str(user_input[CONF_STATION_ID]).strip()
            station = _station_by_id(self._nearest_stations, station_id)
            if station is None:
                errors["base"] = "unknown"
            else:
                data = _data_from_station(station)
                data, errors = await _validate_and_enrich_user_input(self.hass, data)
                if not errors:
                    await self.async_set_unique_id(data[CONF_STATION_ID])
                    self._abort_if_unique_id_configured()
                    return self.async_create_entry(
                        title=f"CHMI {data[CONF_STATION_NAME]}",
                        data=data,
                        options={
                            CONF_UPDATE_INTERVAL: _data_observation_interval_minutes(
                                data
                            ),
                            CONF_DIAGNOSTIC_SENSORS: DEFAULT_DIAGNOSTIC_SENSORS,
                        },
                    )

        return self.async_show_form(
            step_id="station",
            data_schema=_station_schema(self._nearest_stations),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> ChmiWeatherOptionsFlow:
        """Create the options flow."""
        return ChmiWeatherOptionsFlow(config_entry)


class ChmiWeatherOptionsFlow(config_entries.OptionsFlow):
    """Handle CHMI Weather options."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self._config_entry = config_entry

    async def async_step_init(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Manage integration options."""
        observation_interval_minutes = _entry_observation_interval_minutes(
            self._config_entry
        )
        if user_input is not None:
            options = dict(user_input)
            options[CONF_UPDATE_INTERVAL] = max(
                1,
                min(
                    int(options[CONF_UPDATE_INTERVAL]),
                    observation_interval_minutes,
                ),
            )
            return self.async_create_entry(title="", data=options)

        options = self._config_entry.options
        default_update_interval = max(
            1,
            min(
                int(options.get(CONF_UPDATE_INTERVAL, observation_interval_minutes)),
                observation_interval_minutes,
            ),
        )
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_UPDATE_INTERVAL,
                        default=default_update_interval,
                    ): vol.All(
                        vol.Coerce(int),
                        vol.Range(min=1, max=observation_interval_minutes),
                    ),
                    vol.Required(
                        CONF_DIAGNOSTIC_SENSORS,
                        default=options.get(
                            CONF_DIAGNOSTIC_SENSORS,
                            DEFAULT_DIAGNOSTIC_SENSORS,
                        ),
                    ): bool,
                }
            ),
        )


def _default_location_input(hass: HomeAssistant | None = None) -> dict[str, Any]:
    hass_config = getattr(hass, "config", None)
    latitude = getattr(hass_config, "latitude", None)
    longitude = getattr(hass_config, "longitude", None)
    if latitude is None or longitude is None:
        return {}

    return {CONF_LATITUDE: latitude, CONF_LONGITUDE: longitude}


def _normalize_location_input(user_input: dict[str, Any]) -> dict[str, Any]:
    return {
        CONF_LATITUDE: float(user_input[CONF_LATITUDE]),
        CONF_LONGITUDE: float(user_input[CONF_LONGITUDE]),
    }


def _location_schema(defaults: dict[str, Any]) -> vol.Schema:
    latitude_marker = (
        vol.Required(CONF_LATITUDE, default=defaults[CONF_LATITUDE])
        if CONF_LATITUDE in defaults
        else vol.Required(CONF_LATITUDE)
    )
    longitude_marker = (
        vol.Required(CONF_LONGITUDE, default=defaults[CONF_LONGITUDE])
        if CONF_LONGITUDE in defaults
        else vol.Required(CONF_LONGITUDE)
    )

    return vol.Schema(
        {
            latitude_marker: vol.All(vol.Coerce(float), vol.Range(min=-90, max=90)),
            longitude_marker: vol.All(vol.Coerce(float), vol.Range(min=-180, max=180)),
        }
    )


def _station_schema(stations: tuple[ChmiNearestStation, ...]) -> vol.Schema:
    return vol.Schema(
        {
            vol.Required(CONF_STATION_ID): vol.In(
                {item.station.station_id: _station_label(item) for item in stations}
            )
        }
    )


def _station_label(station: ChmiNearestStation) -> str:
    return (
        f"{station.station.full_name} - "
        f"{station.distance_km:.1f} km ({station.station.station_id})"
    )


def _station_by_id(
    stations: tuple[ChmiNearestStation, ...],
    station_id: str,
) -> ChmiNearestStation | None:
    for station in stations:
        if station.station.station_id == station_id:
            return station
    return None


def _data_from_station(station: ChmiNearestStation) -> dict[str, Any]:
    return {
        CONF_STATION_NAME: station.station.full_name,
        CONF_STATION_ID: station.station.station_id,
        CONF_LATITUDE: station.station.latitude,
        CONF_LONGITUDE: station.station.longitude,
    }


async def _async_get_nearest_stations(
    hass: HomeAssistant,
    latitude: float,
    longitude: float,
) -> tuple[tuple[ChmiNearestStation, ...], dict[str, str]]:
    client = ChmiApiClient(async_get_clientsession(hass))
    try:
        stations = await client.async_get_nearest_stations(
            latitude,
            longitude,
            limit=DEFAULT_STATION_SELECTION_LIMIT,
        )
    except ChmiApiConnectionError:
        return (), {"base": "cannot_connect"}
    except ChmiApiDataError:
        return (), {"base": "no_stations"}
    except ChmiApiError:
        return (), {"base": "unknown"}

    if not stations:
        return (), {"base": "no_stations"}

    return stations, {}


async def _validate_user_input(
    hass: HomeAssistant,
    data: dict[str, Any],
) -> dict[str, str]:
    """Validate user input and return only form errors."""
    _, errors = await _validate_and_enrich_user_input(hass, data)
    return errors


async def _validate_and_enrich_user_input(
    hass: HomeAssistant,
    data: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, str]]:
    """Validate station input and enrich it from official CHMI metadata."""
    errors: dict[str, str] = {}
    if not data[CONF_STATION_ID]:
        return data, {"base": "no_station_id"}

    client = ChmiApiClient(async_get_clientsession(hass))
    enriched_data = dict(data)

    try:
        metadata = await client.async_get_station_metadata(data[CONF_STATION_ID])
    except ChmiApiError:
        if not enriched_data[CONF_STATION_NAME]:
            enriched_data[CONF_STATION_NAME] = enriched_data[CONF_STATION_ID]
    else:
        enriched_data.update(
            {
                CONF_STATION_NAME: metadata.full_name,
                CONF_LATITUDE: metadata.latitude,
                CONF_LONGITUDE: metadata.longitude,
            }
        )

    try:
        capabilities = await client.async_get_station_capabilities(
            data[CONF_STATION_ID]
        )
    except ChmiApiError:
        pass
    else:
        enriched_data[CONF_SUPPORTED_ELEMENTS] = list(capabilities.supported_elements)
        elements_by_interval = capabilities.supported_elements_by_interval
        enriched_data[CONF_SUPPORTED_ELEMENTS_BY_INTERVAL] = {
            str(interval): list(elements)
            for interval, elements in elements_by_interval.items()
        }
        enriched_data[CONF_OBSERVATION_INTERVAL_MINUTES] = (
            capabilities.observation_interval_minutes
        )

    try:
        observation = await client.async_get_current_observations(
            data[CONF_STATION_ID],
            interval_minutes=_data_observation_interval_minutes(enriched_data),
        )
    except ChmiApiConnectionError:
        errors["base"] = "cannot_connect"
    except ChmiApiDataError:
        errors["base"] = "no_data"
    except ChmiApiError:
        errors["base"] = "unknown"
    else:
        if not has_usable_observation(observation):
            errors["base"] = "no_data"

    return enriched_data, errors


def _data_observation_interval_minutes(data: dict[str, Any]) -> int:
    return max(
        1,
        int(
            data.get(
                CONF_OBSERVATION_INTERVAL_MINUTES,
                DEFAULT_OBSERVATION_INTERVAL_MINUTES,
            )
        ),
    )


def _entry_observation_interval_minutes(
    config_entry: config_entries.ConfigEntry,
) -> int:
    return _data_observation_interval_minutes(dict(config_entry.data))
