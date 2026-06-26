"""Tests for CHMI Weather coordinator."""

from __future__ import annotations

import asyncio
from types import SimpleNamespace

import pytest
from homeassistant.helpers.update_coordinator import UpdateFailed

from custom_components.chmi_weather.api import ChmiApiDataError
from custom_components.chmi_weather.const import CONF_STATION_ID
from custom_components.chmi_weather.coordinator import ChmiDataUpdateCoordinator


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
