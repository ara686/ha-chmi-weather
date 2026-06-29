"""Tests for CHMI Weather sensors."""

from __future__ import annotations

from datetime import UTC, datetime
from types import SimpleNamespace

from custom_components.chmi_weather.const import CONF_STATION_ID, CONF_STATION_NAME
from custom_components.chmi_weather.models import ChmiObservation
from custom_components.chmi_weather.sensor import (
    SENSOR_DESCRIPTIONS,
    ChmiSensorEntity,
    supported_sensor_descriptions,
)


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


def _entity(key: str) -> ChmiSensorEntity:
    description = next(item for item in SENSOR_DESCRIPTIONS if item.key == key)
    return ChmiSensorEntity(
        coordinator=SimpleNamespace(
            data=_observation(),
            last_observation=None,
            last_successful_poll=datetime(2026, 6, 26, 8, 51, tzinfo=UTC),
        ),
        entry=SimpleNamespace(
            data={
                CONF_STATION_ID: "0-203-0-11521",
                CONF_STATION_NAME: "Dobrichovice",
            }
        ),
        description=description,
    )


def test_temperature_sensor_native_value() -> None:
    entity = _entity("temperature")

    assert entity.native_value == 32.7
    assert entity.native_unit_of_measurement == "°C"
    assert entity.device_class == "temperature"
    assert entity.state_class == "measurement"
    assert entity.device_info["name"] == "CHMI Dobrichovice"


def test_last_update_sensor_native_value() -> None:
    entity = _entity("last_update")

    assert entity.native_value == datetime(2026, 6, 26, 8, 50, tzinfo=UTC)
    assert entity.entity_description.translation_key == "observation_time"
    assert entity.device_class == "timestamp"
    assert entity.state_class is None


def test_precipitation_hour_sensor_native_value() -> None:
    entity = _entity("precipitation_1h")

    assert entity.native_value == 1.2
    assert entity.native_unit_of_measurement == "mm"
    assert entity.device_class == "precipitation"
    assert entity.state_class is None


def test_apparent_temperature_sensor_native_value() -> None:
    entity = _entity("apparent_temperature")

    assert entity.native_value == 25.0
    assert entity.native_unit_of_measurement == "°C"
    assert entity.device_class == "temperature"
    assert entity.state_class == "measurement"


def test_average_wind_speed_sensor_native_value() -> None:
    entity = _entity("wind_speed_avg")

    assert entity.native_value == 1.1
    assert entity.native_unit_of_measurement == "m/s"
    assert entity.device_class == "wind_speed"
    assert entity.state_class == "measurement"


def test_wind_gust_direction_sensor_native_value() -> None:
    entity = _entity("wind_gust_direction")

    assert entity.native_value == 200.0
    assert entity.native_unit_of_measurement == "°"
    assert entity.device_class == "wind_direction"
    assert entity.state_class == "measurement_angle"


def test_precipitation_total_sensor_native_value() -> None:
    entity = _entity("precipitation_today")

    assert entity.native_value == 4.8
    assert entity.native_unit_of_measurement == "mm"
    assert entity.device_class == "precipitation"
    assert entity.state_class == "total_increasing"


def test_last_successful_poll_sensor_native_value() -> None:
    entity = _entity("last_successful_poll")

    assert entity.native_value == datetime(2026, 6, 26, 8, 51, tzinfo=UTC)
    assert entity.device_class == "timestamp"
    assert entity.state_class is None


def test_supported_sensor_descriptions_follow_station_capabilities() -> None:
    descriptions = supported_sensor_descriptions(
        {
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
        }
    )
    keys = {description.key for description in descriptions}

    assert "temperature" in keys
    assert "temperature_max_10m" in keys
    assert "temperature_min_10m" in keys
    assert "apparent_temperature" in keys
    assert "humidity" in keys
    assert "precipitation_10m" in keys
    assert "precipitation_1h" in keys
    assert "precipitation_today" in keys
    assert "wind_speed" in keys
    assert "wind_speed_avg" in keys
    assert "wind_gust" in keys
    assert "wind_direction" in keys
    assert "wind_direction_avg" in keys
    assert "wind_gust_direction" in keys
    assert "last_update" in keys
    assert "last_successful_poll" in keys
    assert "pressure" not in keys


def test_hourly_precipitation_sensor_supports_sra1h_only_station() -> None:
    descriptions = supported_sensor_descriptions({"SRA1H"})
    keys = {description.key for description in descriptions}

    assert "precipitation_1h" in keys
    assert "precipitation_10m" not in keys
    assert "precipitation_today" not in keys


def test_supported_sensor_descriptions_keep_legacy_entries() -> None:
    assert supported_sensor_descriptions(None) == SENSOR_DESCRIPTIONS
