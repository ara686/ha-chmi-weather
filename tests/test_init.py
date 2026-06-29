"""Tests for CHMI Weather setup helpers."""

from __future__ import annotations

import asyncio
from types import SimpleNamespace

from custom_components.chmi_weather import _async_refresh_station_capabilities
from custom_components.chmi_weather.const import (
    CONF_OBSERVATION_INTERVAL_MINUTES,
    CONF_STATION_ID,
    CONF_SUPPORTED_ELEMENTS,
    CONF_SUPPORTED_ELEMENTS_BY_INTERVAL,
)
from custom_components.chmi_weather.models import ChmiStationCapabilities


class FakeConfigEntries:
    """Config entries manager stub."""

    def __init__(self) -> None:
        """Initialize the stub."""
        self.updated_data = None

    def async_update_entry(self, entry, *, data):
        """Record updated entry data."""
        self.updated_data = data
        entry.data = data


class FakeClient:
    """Client stub returning station capabilities."""

    async def async_get_station_capabilities(self, station_id: str):
        """Return station capabilities."""
        return ChmiStationCapabilities(
            station_id=station_id,
            supported_elements=("D", "F", "Fmax", "H", "SRA10M", "T"),
            observation_type="10M",
            observation_interval_minutes=10,
            supported_elements_by_interval={
                10: ("D", "F", "Fmax", "H", "SRA10M", "T"),
                60: ("SRA1H",),
            },
        )


def test_refresh_station_capabilities_updates_entry_data() -> None:
    hass = SimpleNamespace(config_entries=FakeConfigEntries())
    entry = SimpleNamespace(data={CONF_STATION_ID: "0-203-0-11521"})

    asyncio.run(_async_refresh_station_capabilities(hass, entry, FakeClient()))

    assert hass.config_entries.updated_data[CONF_SUPPORTED_ELEMENTS] == [
        "D",
        "F",
        "Fmax",
        "H",
        "SRA10M",
        "T",
    ]
    assert entry.data[CONF_SUPPORTED_ELEMENTS] == [
        "D",
        "F",
        "Fmax",
        "H",
        "SRA10M",
        "T",
    ]
    assert entry.data[CONF_OBSERVATION_INTERVAL_MINUTES] == 10
    assert entry.data[CONF_SUPPORTED_ELEMENTS_BY_INTERVAL] == {
        "10": ["D", "F", "Fmax", "H", "SRA10M", "T"],
        "60": ["SRA1H"],
    }
