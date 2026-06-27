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
    CONF_UPDATE_INTERVAL,
)
from custom_components.chmi_weather.coordinator import ChmiDataUpdateCoordinator
from custom_components.chmi_weather.models import ChmiObservation


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

    async def async_get_current_observations(
        self,
        station_id: str,
        *,
        interval_minutes: int,
    ):
        self.calls.append((station_id, interval_minutes))
        return _observation()


class FailingClient:
    """Client that always fails."""

    async def async_get_current_observations(
        self,
        station_id: str,
        *,
        interval_minutes: int,
    ):
        raise ChmiApiDataError("bad data")


def _config_entry(*, options=None):
    return SimpleNamespace(
        data={
            CONF_STATION_ID: "0-203-0-11521",
            CONF_OBSERVATION_INTERVAL_MINUTES: 10,
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

    assert observation == _observation()
    assert coordinator.last_observation == _observation()
    assert coordinator.last_successful_poll is not None
    assert coordinator.last_successful_poll.tzinfo == UTC
    assert client.calls == [("0-203-0-11521", 10)]
