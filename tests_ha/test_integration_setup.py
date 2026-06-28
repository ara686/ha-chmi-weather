"""Smoke tests using real Home Assistant test fixtures."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import pytest
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components import chmi_weather
from custom_components.chmi_weather.const import (
    CONF_DIAGNOSTIC_SENSORS,
    CONF_FORECAST_SOURCE,
    CONF_LATITUDE,
    CONF_LONGITUDE,
    CONF_OBSERVATION_INTERVAL_MINUTES,
    CONF_STATION_ID,
    CONF_STATION_NAME,
    CONF_SUPPORTED_ELEMENTS,
    CONF_UPDATE_INTERVAL,
    DEFAULT_FORECAST_SOURCE,
    DOMAIN,
)
from custom_components.chmi_weather.models import (
    ChmiObservation,
    ChmiStationCapabilities,
)

STATION_ID = "0-203-0-11521"

pytestmark = pytest.mark.asyncio


class FakeChmiApiClient:
    """Deterministic CHMI client used by HA integration tests."""

    def __init__(self, session: Any) -> None:
        """Initialize fake client."""
        self.session = session

    async def async_get_station_capabilities(
        self,
        station_id: str,
    ) -> ChmiStationCapabilities:
        """Return station capabilities."""
        return ChmiStationCapabilities(
            station_id=station_id,
            supported_elements=("D", "F", "Fmax", "H", "SRA10M", "T"),
            observation_type="10M",
            observation_interval_minutes=10,
        )

    async def async_get_current_observations(
        self,
        station_id: str,
        *,
        interval_minutes: int,
    ) -> ChmiObservation:
        """Return a current observation."""
        assert interval_minutes == 10
        return ChmiObservation(
            station_id=station_id,
            observed_at=datetime(2026, 6, 26, 8, 50, tzinfo=UTC),
            temperature=32.7,
            humidity=37.0,
            pressure=None,
            precipitation_10m=0.0,
            wind_speed=1.3,
            wind_gust=2.9,
            wind_direction=222.0,
            precipitation_1h=1.2,
            precipitation_today=4.8,
            available_elements=("D", "F", "Fmax", "H", "SRA10M", "T"),
        )


async def test_config_entry_sets_up_weather_and_supported_sensors(
    hass: HomeAssistant,
    monkeypatch,
) -> None:
    """Set up the integration through HA and assert states via the state machine."""
    monkeypatch.setattr(chmi_weather, "ChmiApiClient", FakeChmiApiClient)
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="CHMI Dobrichovice",
        data={
            CONF_STATION_ID: STATION_ID,
            CONF_STATION_NAME: "Dobrichovice",
            CONF_LATITUDE: 49.9335,
            CONF_LONGITUDE: 14.2759,
        },
        options={
            CONF_UPDATE_INTERVAL: 10,
            CONF_DIAGNOSTIC_SENSORS: True,
            CONF_FORECAST_SOURCE: DEFAULT_FORECAST_SOURCE,
        },
    )
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    weather_state = hass.states.get("weather.chmi_dobrichovice")
    temperature_state = hass.states.get("sensor.chmi_dobrichovice_temperature")
    precipitation_hour_state = hass.states.get(
        "sensor.chmi_dobrichovice_precipitation_1h"
    )
    precipitation_today_state = hass.states.get(
        "sensor.chmi_dobrichovice_precipitation_today"
    )
    wind_speed_state = hass.states.get("sensor.chmi_dobrichovice_wind_speed")
    pressure_state = hass.states.get("sensor.chmi_dobrichovice_pressure")

    assert entry.runtime_data.coordinator.data is not None
    assert entry.data[CONF_SUPPORTED_ELEMENTS] == ["D", "F", "Fmax", "H", "SRA10M", "T"]
    assert entry.data[CONF_OBSERVATION_INTERVAL_MINUTES] == 10
    assert weather_state is not None
    assert weather_state.state == "partlycloudy"
    assert temperature_state is not None
    assert temperature_state.state == "32.7"
    assert precipitation_hour_state is not None
    assert precipitation_hour_state.state == "1.2"
    assert precipitation_today_state is not None
    assert precipitation_today_state.state == "4.8"
    assert wind_speed_state is not None
    assert wind_speed_state.state == "4.68"
    assert pressure_state is None

    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()
