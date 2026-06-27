"""Tests for CHMI Weather coordinator."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from types import SimpleNamespace

import pytest
from homeassistant.helpers.update_coordinator import UpdateFailed

from custom_components.chmi_weather.api import ChmiApiDataError
from custom_components.chmi_weather.const import CONF_STATION_ID
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

    async def async_get_current_observations(self, station_id: str):
        return _observation()


class FailingClient:
    """Client that always fails."""

    async def async_get_current_observations(self, station_id: str):
        raise ChmiApiDataError("bad data")


def test_coordinator_raises_update_failed_on_api_error() -> None:
    coordinator = ChmiDataUpdateCoordinator(
        hass=SimpleNamespace(),
        config_entry=SimpleNamespace(
            data={CONF_STATION_ID: "0-203-0-11521"},
            options={},
        ),
        client=FailingClient(),
    )

    with pytest.raises(UpdateFailed):
        asyncio.run(coordinator._async_update_data())


def test_coordinator_records_last_successful_poll() -> None:
    coordinator = ChmiDataUpdateCoordinator(
        hass=SimpleNamespace(),
        config_entry=SimpleNamespace(
            data={CONF_STATION_ID: "0-203-0-11521"},
            options={},
        ),
        client=SuccessfulClient(),
    )

    observation = asyncio.run(coordinator._async_update_data())

    assert observation == _observation()
    assert coordinator.last_observation == _observation()
    assert coordinator.last_successful_poll is not None
    assert coordinator.last_successful_poll.tzinfo == UTC
