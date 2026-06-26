"""Tests for CHMI API parsing."""

from __future__ import annotations

import json
from copy import deepcopy
from datetime import date
from pathlib import Path

import pytest

from custom_components.chmi_weather.api import (
    ChmiApiClient,
    ChmiApiDataError,
    parse_current_observations,
)

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "chmi_dobrichovice_current.json"
STATION_ID = "0-203-0-11521"


def _fixture() -> dict:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


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
