"""Tests for CHMI Weather weather entity."""

from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace

from custom_components.chmi_weather.const import CONF_STATION_ID, CONF_STATION_NAME
from custom_components.chmi_weather.models import ChmiObservation
from custom_components.chmi_weather.weather import (
    ChmiWeatherEntity,
    condition_from_observation,
)


def _observation(precipitation: float | None = 0.0) -> ChmiObservation:
    return ChmiObservation(
        station_id="0-203-0-11521",
        observed_at=datetime(2026, 6, 26, 8, 50, tzinfo=UTC),
        temperature=32.7,
        humidity=37.0,
        pressure=None,
        precipitation_10m=precipitation,
        wind_speed=1.3,
        wind_gust=2.9,
        wind_direction=222.0,
        available_elements=("D", "F", "Fmax", "H", "SRA10M", "T"),
    )


def test_weather_entity_returns_properties() -> None:
    entity = ChmiWeatherEntity(
        coordinator=SimpleNamespace(data=_observation(), last_observation=None),
        entry=SimpleNamespace(
            data={
                CONF_STATION_ID: "0-203-0-11521",
                CONF_STATION_NAME: "Dobrichovice",
            }
        ),
    )

    assert entity.native_temperature == 32.7
    assert entity.humidity == 37.0
    assert entity.native_pressure is None
    assert entity.native_wind_speed == 1.3
    assert entity.native_wind_gust_speed == 2.9
    assert entity.wind_bearing == 222.0
    assert entity.condition == "partlycloudy"
    assert entity.device_info["name"] == "CHMI Dobrichovice"


def test_condition_uses_precipitation_best_effort() -> None:
    assert condition_from_observation(_observation(0.1)) == "rainy"
    assert condition_from_observation(_observation(0.0)) == "partlycloudy"
    assert condition_from_observation(_observation(None)) == "partlycloudy"
