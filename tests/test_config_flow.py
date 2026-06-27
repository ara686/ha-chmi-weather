"""Tests for CHMI Weather config flow."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from types import SimpleNamespace

from custom_components.chmi_weather import config_flow
from custom_components.chmi_weather.const import (
    CONF_DIAGNOSTIC_SENSORS,
    CONF_LATITUDE,
    CONF_LONGITUDE,
    CONF_STATION_ID,
    CONF_STATION_NAME,
    CONF_SUPPORTED_ELEMENTS,
    CONF_UPDATE_INTERVAL,
    DEFAULT_UPDATE_INTERVAL_MINUTES,
)
from custom_components.chmi_weather.models import (
    ChmiNearestStation,
    ChmiObservation,
    ChmiStationCapabilities,
    ChmiStationMetadata,
)


def test_config_flow_creates_entry(monkeypatch) -> None:
    nearest_station = ChmiNearestStation(
        station=ChmiStationMetadata(
            station_id="0-203-0-11521",
            gh_id="P1DOBE01",
            full_name="Dobřichovice",
            latitude=49.9335,
            longitude=14.27585,
            elevation=205.0,
            begin_date=datetime(1999, 4, 1, tzinfo=UTC),
        ),
        distance_km=0.01,
    )

    async def fake_nearest_stations(hass, latitude, longitude):
        return (nearest_station,), {}

    async def fake_validate_and_enrich(hass, data):
        data = dict(data)
        data.update(
            {
                CONF_STATION_NAME: "Dobřichovice",
                CONF_LATITUDE: 49.9335,
                CONF_LONGITUDE: 14.27585,
                CONF_SUPPORTED_ELEMENTS: ["D", "F", "Fmax", "H", "SRA10M", "T"],
            }
        )
        return data, {}

    async def run() -> dict:
        flow = config_flow.ChmiWeatherConfigFlow()
        flow.hass = SimpleNamespace()
        first_result = await flow.async_step_user(
            {
                CONF_LATITUDE: 49.9335,
                CONF_LONGITUDE: 14.2759,
            }
        )
        assert first_result["type"] == "form"
        assert first_result["step_id"] == "station"
        return await flow.async_step_station({CONF_STATION_ID: "0-203-0-11521"})

    monkeypatch.setattr(
        config_flow,
        "_async_get_nearest_stations",
        fake_nearest_stations,
    )
    monkeypatch.setattr(
        config_flow,
        "_validate_and_enrich_user_input",
        fake_validate_and_enrich,
    )

    result = asyncio.run(run())

    assert result["type"] == "create_entry"
    assert result["title"] == "CHMI Dobřichovice"
    assert result["data"][CONF_STATION_ID] == "0-203-0-11521"
    assert result["data"][CONF_STATION_NAME] == "Dobřichovice"
    assert result["data"][CONF_LONGITUDE] == 14.27585
    assert result["data"][CONF_SUPPORTED_ELEMENTS] == [
        "D",
        "F",
        "Fmax",
        "H",
        "SRA10M",
        "T",
    ]
    assert result["options"][CONF_UPDATE_INTERVAL] == DEFAULT_UPDATE_INTERVAL_MINUTES
    assert result["options"][CONF_DIAGNOSTIC_SENSORS] is True


def test_config_flow_prefills_home_assistant_location() -> None:
    flow = config_flow.ChmiWeatherConfigFlow()
    flow.hass = SimpleNamespace(
        config=SimpleNamespace(latitude=50.0875, longitude=14.4213)
    )

    result = asyncio.run(flow.async_step_user())
    schema = result["data_schema"].schema

    assert result["type"] == "form"
    assert result["step_id"] == "user"
    assert _schema_marker(schema, CONF_LATITUDE).default == 50.0875
    assert _schema_marker(schema, CONF_LONGITUDE).default == 14.4213


def test_config_flow_does_not_prefill_location_without_ha_coordinates() -> None:
    flow = config_flow.ChmiWeatherConfigFlow()
    flow.hass = SimpleNamespace(config=SimpleNamespace())

    result = asyncio.run(flow.async_step_user())
    schema = result["data_schema"].schema

    assert result["type"] == "form"
    assert result["step_id"] == "user"
    assert _schema_marker(schema, CONF_LATITUDE).default is None
    assert _schema_marker(schema, CONF_LONGITUDE).default is None


def _schema_marker(schema: dict, key: str):
    return next(marker for marker in schema if marker == key)


def test_config_flow_requires_station_id() -> None:
    result = asyncio.run(
        config_flow._validate_user_input(
            SimpleNamespace(session=None),
            {
                CONF_STATION_NAME: "Dobrichovice",
                CONF_STATION_ID: "",
                CONF_LATITUDE: 49.9335,
                CONF_LONGITUDE: 14.2759,
            },
        )
    )

    assert result == {"base": "no_station_id"}


def test_config_flow_gets_nearest_stations(monkeypatch) -> None:
    nearest_station = ChmiNearestStation(
        station=ChmiStationMetadata(
            station_id="0-203-0-11521",
            gh_id="P1DOBE01",
            full_name="Dobřichovice",
            latitude=49.9335,
            longitude=14.27585,
            elevation=205.0,
            begin_date=datetime(1999, 4, 1, tzinfo=UTC),
        ),
        distance_km=0.01,
    )

    class FakeClient:
        def __init__(self, session):
            self.session = session

        async def async_get_nearest_stations(
            self,
            latitude: float,
            longitude: float,
            *,
            limit: int,
        ):
            assert latitude == 49.9335
            assert longitude == 14.2759
            assert limit == 10
            return (nearest_station,)

    monkeypatch.setattr(config_flow, "ChmiApiClient", FakeClient)

    stations, errors = asyncio.run(
        config_flow._async_get_nearest_stations(
            SimpleNamespace(session=None),
            49.9335,
            14.2759,
        )
    )

    assert errors == {}
    assert stations == (nearest_station,)


def test_config_flow_enriches_station_from_metadata(monkeypatch) -> None:
    class FakeClient:
        def __init__(self, session):
            self.session = session

        async def async_get_station_metadata(self, station_id: str):
            return ChmiStationMetadata(
                station_id=station_id,
                gh_id="P1DOBE01",
                full_name="Dobřichovice",
                latitude=49.9335,
                longitude=14.27585,
                elevation=205.0,
                begin_date=datetime(1999, 4, 1, tzinfo=UTC),
            )

        async def async_get_station_capabilities(self, station_id: str):
            return ChmiStationCapabilities(
                station_id=station_id,
                supported_elements=("D", "F", "Fmax", "H", "SRA10M", "T"),
            )

        async def async_get_current_observations(self, station_id: str):
            return ChmiObservation(
                station_id=station_id,
                observed_at=datetime(2026, 6, 26, 8, 50, tzinfo=UTC),
                temperature=32.7,
                humidity=None,
                pressure=None,
                precipitation_10m=None,
                wind_speed=None,
                wind_gust=None,
                wind_direction=None,
            )

    monkeypatch.setattr(config_flow, "ChmiApiClient", FakeClient)

    data, errors = asyncio.run(
        config_flow._validate_and_enrich_user_input(
            SimpleNamespace(session=None),
            {
                CONF_STATION_NAME: "Manual name",
                CONF_STATION_ID: "0-203-0-11521",
                CONF_LATITUDE: 0.0,
                CONF_LONGITUDE: 0.0,
            },
        )
    )

    assert errors == {}
    assert data[CONF_STATION_NAME] == "Dobřichovice"
    assert data[CONF_LATITUDE] == 49.9335
    assert data[CONF_LONGITUDE] == 14.27585
    assert data[CONF_SUPPORTED_ELEMENTS] == ["D", "F", "Fmax", "H", "SRA10M", "T"]
