"""Tests for CHMI Weather coordinator."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import pytest
from homeassistant.helpers.update_coordinator import UpdateFailed

from custom_components.chmi_weather.api import ChmiApiDataError
from custom_components.chmi_weather.const import (
    CONF_OBSERVATION_INTERVAL_MINUTES,
    CONF_STATION_ID,
    CONF_SUPPORTED_ELEMENTS_BY_INTERVAL,
    CONF_UPDATE_INTERVAL,
)
from custom_components.chmi_weather.coordinator import ChmiDataUpdateCoordinator
from custom_components.chmi_weather.models import ChmiDailySummary, ChmiObservation


def _observation() -> ChmiObservation:
    return ChmiObservation(
        station_id="0-203-0-11521",
        observed_at=datetime(2026, 6, 26, 8, 50, tzinfo=UTC),
        temperature=32.7,
        humidity=37.0,
        pressure=None,
        precipitation_10m=0.0,
        wind_speed=1.3,
        wind_gust=2.9,
        wind_direction=222.0,
    )


class SuccessfulClient:
    """Client that returns one observation."""

    def __init__(self) -> None:
        """Initialize call recording."""
        self.calls = []
        self.daily_calls = []

    async def async_get_current_observations(
        self,
        station_id: str,
        *,
        interval_minutes: int,
        precipitation_timezone,
        precipitation_1h_interval_minutes,
    ):
        self.calls.append(
            (
                station_id,
                interval_minutes,
                precipitation_timezone,
                precipitation_1h_interval_minutes,
            )
        )
        return _observation()

    async def async_get_recent_daily_summary(self, station_id: str, summary_date):
        self.daily_calls.append((station_id, summary_date))
        return ChmiDailySummary(
            station_id=station_id,
            summary_date=summary_date,
            yesterday_precipitation=0.8,
            yesterday_temperature_max=30.4,
            yesterday_temperature_min=13.2,
            yesterday_wind_gust_max=6.8,
            month_precipitation_chmi=3.4,
        )


class FailingClient:
    """Client that always fails."""

    async def async_get_current_observations(
        self,
        station_id: str,
        *,
        interval_minutes: int,
        precipitation_timezone,
        precipitation_1h_interval_minutes,
    ):
        raise ChmiApiDataError("bad data")


class DailySummaryFailingClient(SuccessfulClient):
    """Client that returns current data but fails for recent daily summary."""

    async def async_get_recent_daily_summary(self, station_id: str, summary_date):
        self.daily_calls.append((station_id, summary_date))
        raise ChmiApiDataError("bad daily data")


def _config_entry(*, options=None):
    return SimpleNamespace(
        data={
            CONF_STATION_ID: "0-203-0-11521",
            CONF_OBSERVATION_INTERVAL_MINUTES: 10,
            CONF_SUPPORTED_ELEMENTS_BY_INTERVAL: {"10": ["SRA10M"], "60": ["SRA1H"]},
        },
        options=options or {},
    )


def test_coordinator_raises_update_failed_on_api_error() -> None:
    coordinator = ChmiDataUpdateCoordinator(
        hass=SimpleNamespace(),
        config_entry=_config_entry(),
        client=FailingClient(),
    )

    with pytest.raises(UpdateFailed):
        asyncio.run(coordinator._async_update_data())


def test_coordinator_clamps_update_interval_to_observation_interval() -> None:
    coordinator = ChmiDataUpdateCoordinator(
        hass=SimpleNamespace(),
        config_entry=_config_entry(options={CONF_UPDATE_INTERVAL: 60}),
        client=SuccessfulClient(),
    )

    assert coordinator.update_interval_minutes == 10
    assert coordinator.kwargs["update_interval"] == timedelta(minutes=10)


def test_coordinator_records_last_successful_poll() -> None:
    client = SuccessfulClient()
    coordinator = ChmiDataUpdateCoordinator(
        hass=SimpleNamespace(),
        config_entry=_config_entry(),
        client=client,
    )

    observation = asyncio.run(coordinator._async_update_data())

    assert observation.temperature == _observation().temperature
    assert coordinator.last_observation == observation
    assert coordinator.last_successful_poll is not None
    assert coordinator.last_successful_poll.tzinfo == UTC
    assert client.calls == [("0-203-0-11521", 10, UTC, 60)]
    assert client.daily_calls == [("0-203-0-11521", observation.daily_summary_date)]
    assert observation.yesterday_precipitation == 0.8
    assert observation.yesterday_temperature_max == 30.4
    assert observation.yesterday_temperature_min == 13.2
    assert observation.yesterday_wind_gust_max == 6.8
    assert observation.month_precipitation_chmi == 3.4


def test_coordinator_passes_home_assistant_timezone() -> None:
    client = SuccessfulClient()
    coordinator = ChmiDataUpdateCoordinator(
        hass=SimpleNamespace(config=SimpleNamespace(time_zone="Europe/Prague")),
        config_entry=_config_entry(),
        client=client,
    )

    asyncio.run(coordinator._async_update_data())

    assert client.calls[0][2].key == "Europe/Prague"


def test_coordinator_keeps_current_observation_when_daily_summary_fails() -> None:
    client = DailySummaryFailingClient()
    coordinator = ChmiDataUpdateCoordinator(
        hass=SimpleNamespace(),
        config_entry=_config_entry(),
        client=client,
    )

    observation = asyncio.run(coordinator._async_update_data())

    assert observation.temperature == 32.7
    assert observation.yesterday_precipitation is None
    assert client.daily_calls
