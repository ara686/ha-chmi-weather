"""Tests for CHMI API parsing."""

from __future__ import annotations

import asyncio
import json
from copy import deepcopy
from datetime import UTC, date, datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest

from custom_components.chmi_weather import api
from custom_components.chmi_weather.api import (
    ChmiApiClient,
    ChmiApiDataError,
    nearest_stations,
    parse_current_observations,
    parse_station_capabilities,
    parse_station_metadata,
    parse_station_metadata_list,
)

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "chmi_dobrichovice_current.json"
METADATA_FIXTURE_PATH = Path(__file__).parent / "fixtures" / "chmi_meta1_current.json"
CAPABILITIES_FIXTURE_PATH = (
    Path(__file__).parent / "fixtures" / "chmi_meta2_current.json"
)
STATION_ID = "0-203-0-11521"


def _fixture() -> dict:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def _metadata_fixture() -> dict:
    return json.loads(METADATA_FIXTURE_PATH.read_text(encoding="utf-8"))


def _capabilities_fixture() -> dict:
    return json.loads(CAPABILITIES_FIXTURE_PATH.read_text(encoding="utf-8"))


def _values(payload: dict) -> list:
    return payload["data"]["data"]["values"]


def test_parser_selects_latest_valid_values() -> None:
    observation = parse_current_observations(_fixture(), STATION_ID)

    assert observation.station_id == STATION_ID
    assert observation.observed_at.isoformat() == "2026-06-26T08:50:00+00:00"
    assert observation.temperature == 32.7
    assert observation.humidity == 37.0
    assert observation.pressure is None
    assert observation.precipitation_10m == 0.0
    assert observation.wind_speed == 1.3
    assert observation.wind_gust == 2.9
    assert observation.wind_direction == 222.0
    assert "TPM" in observation.available_elements


def test_parser_calculates_precipitation_totals() -> None:
    payload = deepcopy(_fixture())
    rows = _values(payload)
    rows.extend(
        [
            [STATION_ID, "SRA10M", "2026-06-26T07:50:00Z", 5.0, "", 5.0],
            [STATION_ID, "SRA10M", "2026-06-26T08:00:00Z", 1.0, "", 5.0],
            [STATION_ID, "SRA10M", "2026-06-26T08:10:00Z", 0.5, "", 5.0],
            [STATION_ID, "SRA10M", "2026-06-26T08:50:00Z", 0.2, "", 5.0],
        ]
    )

    observation = parse_current_observations(payload, STATION_ID)

    assert observation.precipitation_10m == 0.2
    assert observation.precipitation_1h == 1.7
    assert observation.precipitation_today == 6.7
    assert [
        (sample.observed_at.isoformat(), sample.amount)
        for sample in observation.precipitation_samples
        if sample.amount
    ] == [
        ("2026-06-26T07:50:00+00:00", 5.0),
        ("2026-06-26T08:00:00+00:00", 1.0),
        ("2026-06-26T08:10:00+00:00", 0.5),
        ("2026-06-26T08:50:00+00:00", 0.2),
    ]


def test_api_client_calculates_precipitation_today_for_local_date(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FrozenDatetime(datetime):
        @classmethod
        def now(cls, tz=None):
            return cls(2026, 6, 29, 8, 0, tzinfo=tz or UTC)

    class PayloadClient(ChmiApiClient):
        def __init__(self, payloads_by_day):
            super().__init__(session=object())
            self.payloads_by_day = payloads_by_day
            self.days = []

        async def async_get_current_observations_for_date(
            self,
            station_id: str,
            day: date,
            *,
            interval_minutes: int = 10,
        ):
            self.days.append(day)
            return parse_current_observations(self.payloads_by_day[day], station_id)

    previous_payload = deepcopy(_fixture())
    previous_rows = _values(previous_payload)
    previous_rows.extend(
        [
            [STATION_ID, "SRA10M", "2026-06-28T21:50:00Z", 2.0, "", 5.0],
            [STATION_ID, "SRA10M", "2026-06-28T22:10:00Z", 0.1, "", 5.0],
            [STATION_ID, "SRA10M", "2026-06-28T22:20:00Z", 3.7, "", 5.0],
            [STATION_ID, "SRA10M", "2026-06-28T22:30:00Z", 0.8, "", 5.0],
            [STATION_ID, "SRA10M", "2026-06-28T23:10:00Z", 0.1, "", 5.0],
        ]
    )
    current_payload = deepcopy(_fixture())
    current_rows = _values(current_payload)
    current_rows.extend(
        [
            [STATION_ID, "SRA10M", "2026-06-29T00:00:00Z", 0.0, "", 5.0],
            [STATION_ID, "SRA10M", "2026-06-29T00:10:00Z", 0.0, "", 5.0],
        ]
    )
    client = PayloadClient(
        {
            date(2026, 6, 29): current_payload,
            date(2026, 6, 28): previous_payload,
        }
    )
    monkeypatch.setattr(api, "datetime", FrozenDatetime)

    observation = asyncio.run(
        client.async_get_current_observations(
            STATION_ID,
            precipitation_timezone=ZoneInfo("Europe/Prague"),
        )
    )

    assert client.days == [date(2026, 6, 29), date(2026, 6, 28)]
    assert observation.precipitation_today == 4.7
    assert observation.precipitation_10m == 0.0


def test_parser_ignores_none_and_empty_values() -> None:
    payload = _fixture()
    rows = _values(payload)
    rows.append([STATION_ID, "T", "2026-06-26T09:00:00Z", None, "", 5.0])
    rows.append([STATION_ID, "T", "2026-06-26T09:10:00Z", "", "", 5.0])

    observation = parse_current_observations(payload, STATION_ID)

    assert observation.temperature == 32.7


def test_parser_handles_missing_element() -> None:
    payload = deepcopy(_fixture())
    payload["data"]["data"]["values"] = [
        row for row in _values(payload) if row[1] != "H"
    ]

    observation = parse_current_observations(payload, STATION_ID)

    assert observation.humidity is None
    assert observation.temperature == 32.7


def test_parser_rejects_empty_payload() -> None:
    with pytest.raises(ChmiApiDataError):
        parse_current_observations({"data": {"data": {"values": []}}}, STATION_ID)


def test_api_client_builds_current_url() -> None:
    client = ChmiApiClient(session=object())

    url = client._build_current_url(STATION_ID, date(2026, 6, 26))

    assert (
        url == "https://opendata.chmi.cz/meteorology/climate/now/data/"
        "10m-0-203-0-11521-20260626.json"
    )


def test_api_client_builds_hourly_current_url() -> None:
    client = ChmiApiClient(session=object())

    url = client._build_current_url(
        STATION_ID,
        date(2026, 6, 26),
        interval_minutes=60,
    )

    assert (
        url == "https://opendata.chmi.cz/meteorology/climate/now/data/"
        "1h-0-203-0-11521-20260626.json"
    )


def test_api_client_rejects_unsafe_station_id() -> None:
    client = ChmiApiClient(session=object())

    with pytest.raises(ChmiApiDataError):
        client._build_current_url("../0-203-0-11521?x=1", date(2026, 6, 26))


def test_parser_reads_station_metadata() -> None:
    metadata = parse_station_metadata(_metadata_fixture(), STATION_ID)

    assert metadata.station_id == STATION_ID
    assert metadata.gh_id == "P1DOBE01"
    assert metadata.full_name == "Dobřichovice"
    assert metadata.latitude == 49.9335
    assert metadata.longitude == 14.27585
    assert metadata.elevation == 205.0
    assert metadata.begin_date is not None
    assert metadata.begin_date.isoformat() == "1999-04-01T00:00:00+00:00"


def test_parser_reads_station_metadata_list() -> None:
    stations = parse_station_metadata_list(_metadata_fixture())
    station_ids = {station.station_id for station in stations}

    assert STATION_ID in station_ids
    assert "0-203-0-11603" in station_ids


def test_parser_rejects_missing_station_metadata() -> None:
    with pytest.raises(ChmiApiDataError):
        parse_station_metadata(_metadata_fixture(), "0-203-0-missing")


def test_api_client_builds_station_metadata_url() -> None:
    client = ChmiApiClient(session=object())

    url = client._build_station_metadata_url(date(2026, 6, 26))

    assert (
        url == "https://opendata.chmi.cz/meteorology/climate/now/metadata/"
        "meta1-20260626.json"
    )


def test_nearest_stations_sorts_by_distance() -> None:
    stations = parse_station_metadata_list(_metadata_fixture())

    nearest = nearest_stations(stations, 49.9335, 14.2759, limit=2)

    assert [item.station.station_id for item in nearest] == [
        "0-203-0-11521",
        "0-203-0-11603",
    ]
    assert nearest[0].distance_km < 0.1


def test_parser_reads_station_capabilities() -> None:
    capabilities = parse_station_capabilities(_capabilities_fixture(), STATION_ID)

    assert capabilities.station_id == STATION_ID
    assert capabilities.observation_type == "10M"
    assert capabilities.observation_interval_minutes == 10
    assert "D" in capabilities.supported_elements
    assert "F" in capabilities.supported_elements
    assert "Fmax" in capabilities.supported_elements
    assert "H" in capabilities.supported_elements
    assert "P" not in capabilities.supported_elements
    assert "SRA1H" not in capabilities.supported_elements


def test_parser_falls_back_to_hourly_station_capabilities() -> None:
    payload = deepcopy(_capabilities_fixture())
    payload["data"]["data"]["values"] = [
        row for row in _values(payload) if row[1] != STATION_ID or row[0] == "1H"
    ]

    capabilities = parse_station_capabilities(payload, STATION_ID)

    assert capabilities.observation_type == "1H"
    assert capabilities.observation_interval_minutes == 60
    assert capabilities.supported_elements == ("SRA1H",)


def test_parser_rejects_missing_station_capabilities() -> None:
    with pytest.raises(ChmiApiDataError):
        parse_station_capabilities(_capabilities_fixture(), "0-203-0-missing")


def test_api_client_builds_station_capabilities_url() -> None:
    client = ChmiApiClient(session=object())

    url = client._build_station_capabilities_url(date(2026, 6, 26))

    assert (
        url == "https://opendata.chmi.cz/meteorology/climate/now/metadata/"
        "meta2-20260626.json"
    )
