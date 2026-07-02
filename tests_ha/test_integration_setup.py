"""Smoke tests using real Home Assistant test fixtures."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

import pytest
from homeassistant.components.sensor import DOMAIN as SENSOR_DOMAIN
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components import chmi_weather
from custom_components.chmi_weather.const import (
    CONF_DIAGNOSTIC_SENSORS,
    CONF_LATITUDE,
    CONF_LONGITUDE,
    CONF_OBSERVATION_INTERVAL_MINUTES,
    CONF_STATION_ID,
    CONF_STATION_NAME,
    CONF_SUPPORTED_ELEMENTS,
    CONF_SUPPORTED_ELEMENTS_BY_INTERVAL,
    CONF_UPDATE_INTERVAL,
    DOMAIN,
)
from custom_components.chmi_weather.models import (
    ChmiDailySummary,
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

    async def async_get_flag_descriptions(self) -> dict[str, dict[str, str]]:
        """Return CHMI flag descriptions."""
        return {"D": {"V": "Variable"}}

    async def async_get_quality_descriptions(self) -> dict[int, str]:
        """Return CHMI quality-code descriptions."""
        return {0: "Good/Kvalitni hodnota", 5: "Unknown/Kvalita neznama"}

    async def async_get_recent_daily_summary(
        self,
        station_id: str,
        summary_date,
    ) -> ChmiDailySummary:
        """Return recent daily summary values."""
        return ChmiDailySummary(
            station_id=station_id,
            summary_date=summary_date,
            yesterday_precipitation=0.8,
            yesterday_temperature_max=30.4,
            yesterday_temperature_min=13.2,
            yesterday_wind_gust_max=6.8,
            month_precipitation_chmi=3.4,
        )

    async def async_get_station_capabilities(
        self,
        station_id: str,
    ) -> ChmiStationCapabilities:
        """Return station capabilities."""
        return ChmiStationCapabilities(
            station_id=station_id,
            supported_elements=(
                "D",
                "Dmax",
                "Dprum",
                "F",
                "Fmax",
                "Fprum",
                "H",
                "SRA10M",
                "T",
                "TMA",
                "TMI",
                "TPM",
            ),
            observation_type="10M",
            observation_interval_minutes=10,
            supported_elements_by_interval={
                10: (
                    "D",
                    "Dmax",
                    "Dprum",
                    "F",
                    "Fmax",
                    "Fprum",
                    "H",
                    "SRA10M",
                    "T",
                    "TMA",
                    "TMI",
                    "TPM",
                ),
                60: ("SRA1H",),
            },
        )

    async def async_get_current_observations(
        self,
        station_id: str,
        *,
        interval_minutes: int,
        precipitation_timezone,
        precipitation_1h_interval_minutes,
        weather_condition_interval_minutes,
    ) -> ChmiObservation:
        """Return a current observation."""
        assert interval_minutes == 10
        assert precipitation_1h_interval_minutes == 60
        assert weather_condition_interval_minutes is None
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
            temperature_max_10m=33.0,
            temperature_min_10m=31.8,
            apparent_temperature=25.0,
            wind_speed_avg=1.1,
            wind_direction_avg=218.0,
            wind_gust_direction=200.0,
            precipitation_1h=1.2,
            precipitation_today=4.8,
            available_elements=(
                "D",
                "Dmax",
                "Dprum",
                "F",
                "Fmax",
                "Fprum",
                "H",
                "SRA10M",
                "T",
                "TMA",
                "TMI",
                "TPM",
            ),
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
        },
    )
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    weather_state = hass.states.get("weather.chmi_dobrichovice")
    temperature_state = hass.states.get("sensor.chmi_dobrichovice_temperature")
    apparent_temperature_state = hass.states.get(
        "sensor.chmi_dobrichovice_apparent_temperature"
    )
    precipitation_hour_state = hass.states.get(
        "sensor.chmi_dobrichovice_precipitation_1h"
    )
    precipitation_today_state = hass.states.get(
        "sensor.chmi_dobrichovice_precipitation_today"
    )
    month_precipitation_state = hass.states.get(
        "sensor.chmi_dobrichovice_precipitation_this_month"
    )
    wind_speed_state = hass.states.get("sensor.chmi_dobrichovice_wind_speed")
    wind_speed_avg_state = hass.states.get(
        "sensor.chmi_dobrichovice_average_wind_speed"
    )
    wind_gust_direction_state = hass.states.get(
        "sensor.chmi_dobrichovice_wind_gust_direction"
    )
    observation_time_state = hass.states.get(
        "sensor.chmi_dobrichovice_observation_time"
    )
    last_successful_poll_state = hass.states.get(
        "sensor.chmi_dobrichovice_last_successful_poll"
    )
    pressure_state = hass.states.get("sensor.chmi_dobrichovice_pressure")

    assert entry.runtime_data.coordinator.data is not None
    assert entry.data[CONF_SUPPORTED_ELEMENTS] == [
        "D",
        "Dmax",
        "Dprum",
        "F",
        "Fmax",
        "Fprum",
        "H",
        "SRA10M",
        "T",
        "TMA",
        "TMI",
        "TPM",
    ]
    assert entry.data[CONF_SUPPORTED_ELEMENTS_BY_INTERVAL] == {
        "10": [
            "D",
            "Dmax",
            "Dprum",
            "F",
            "Fmax",
            "Fprum",
            "H",
            "SRA10M",
            "T",
            "TMA",
            "TMI",
            "TPM",
        ],
        "60": ["SRA1H"],
    }
    assert entry.data[CONF_OBSERVATION_INTERVAL_MINUTES] == 10
    assert entry.runtime_data.flag_descriptions == {"D": {"V": "Variable"}}
    assert entry.runtime_data.quality_descriptions == {
        0: "Good/Kvalitni hodnota",
        5: "Unknown/Kvalita neznama",
    }
    assert weather_state is not None
    assert weather_state.state == "partlycloudy"
    assert temperature_state is not None
    assert temperature_state.state == "32.7"
    assert apparent_temperature_state is not None
    assert apparent_temperature_state.state == "25.0"
    assert precipitation_hour_state is not None
    assert precipitation_hour_state.state == "1.2"
    assert precipitation_today_state is not None
    assert precipitation_today_state.state == "4.8"
    assert hass.states.get("sensor.chmi_dobrichovice_yesterday_precipitation") is None
    assert (
        hass.states.get("sensor.chmi_dobrichovice_yesterday_temperature_maximum")
        is None
    )
    assert (
        hass.states.get("sensor.chmi_dobrichovice_yesterday_temperature_minimum")
        is None
    )
    assert (
        hass.states.get("sensor.chmi_dobrichovice_yesterday_wind_gust_maximum") is None
    )
    assert month_precipitation_state is not None
    assert month_precipitation_state.state == "3.4"
    _assert_sensor_display_precision(
        hass,
        "sensor.chmi_dobrichovice_precipitation_1h",
        1,
    )
    _assert_sensor_display_precision(
        hass,
        "sensor.chmi_dobrichovice_precipitation_today",
        1,
    )
    _assert_sensor_display_precision(
        hass,
        "sensor.chmi_dobrichovice_precipitation_this_month",
        1,
    )
    assert wind_speed_state is not None
    assert wind_speed_state.state == "4.68"
    assert wind_speed_avg_state is not None
    assert wind_speed_avg_state.state == "3.96"
    assert wind_gust_direction_state is not None
    assert wind_gust_direction_state.state == "200.0"
    assert observation_time_state is not None
    assert last_successful_poll_state is not None
    assert pressure_state is None
    _assert_entity_category(hass, "sensor.chmi_dobrichovice_temperature", None)
    _assert_entity_category(
        hass,
        "sensor.chmi_dobrichovice_precipitation_today",
        None,
    )
    _assert_entity_category(
        hass,
        "sensor.chmi_dobrichovice_observation_time",
        EntityCategory.DIAGNOSTIC,
    )
    _assert_entity_category(
        hass,
        "sensor.chmi_dobrichovice_last_successful_poll",
        EntityCategory.DIAGNOSTIC,
    )

    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()


async def test_measurement_sensors_remain_when_diagnostic_sensors_are_disabled(
    hass: HomeAssistant,
    monkeypatch,
) -> None:
    """Set up measured station sensors even when technical diagnostics are off."""
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
            CONF_DIAGNOSTIC_SENSORS: False,
        },
    )
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert hass.states.get("sensor.chmi_dobrichovice_temperature") is not None
    assert hass.states.get("sensor.chmi_dobrichovice_precipitation_today") is not None
    assert hass.states.get("sensor.chmi_dobrichovice_wind_speed") is not None
    assert hass.states.get("sensor.chmi_dobrichovice_observation_time") is None
    assert hass.states.get("sensor.chmi_dobrichovice_last_successful_poll") is None

    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()


def _assert_entity_category(
    hass: HomeAssistant,
    entity_id: str,
    expected_category: EntityCategory | None,
) -> None:
    registry_entry = er.async_get(hass).async_get(entity_id)
    assert registry_entry is not None
    assert registry_entry.entity_category == expected_category


def _assert_sensor_display_precision(
    hass: HomeAssistant,
    entity_id: str,
    expected_precision: int,
) -> None:
    registry_entry = er.async_get(hass).async_get(entity_id)
    assert registry_entry is not None
    assert registry_entry.options[SENSOR_DOMAIN]["suggested_display_precision"] == (
        expected_precision
    )
