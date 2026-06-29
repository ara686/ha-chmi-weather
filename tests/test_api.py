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
    parse_flag_descriptions,
    parse_quality_descriptions,
    parse_recent_daily_summary,
    parse_station_capabilities,
    parse_station_metadata,
    parse_station_metadata_list,
)

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "chmi_dobrichovice_current.json"
RECENT_DAILY_FIXTURE_PATH = (
    Path(__file__).parent / "fixtures" / "chmi_dobrichovice_recent_daily.json"
)
SYNOP_STATION_FIXTURE_PATH = (
    Path(__file__).parent / "fixtures" / "chmi_synop_station_current.json"
)
SYNOP_STATION_HOURLY_FIXTURE_PATH = (
    Path(__file__).parent / "fixtures" / "chmi_synop_station_current_1h.json"
)
HOURLY_FIXTURE_PATH = (
    Path(__file__).parent / "fixtures" / "chmi_dobrichovice_current_1h.json"
)
METADATA_FIXTURE_PATH = Path(__file__).parent / "fixtures" / "chmi_meta1_current.json"
CAPABILITIES_FIXTURE_PATH = (
    Path(__file__).parent / "fixtures" / "chmi_meta2_current.json"
)
FLAG_METADATA_FIXTURE_PATH = (
    Path(__file__).parent / "fixtures" / "chmi_meta3_current.json"
)
QUALITY_METADATA_FIXTURE_PATH = (
    Path(__file__).parent / "fixtures" / "chmi_meta4_current.json"
)
STATION_ID = "0-203-0-11521"
SYNOP_STATION_ID = "0-20000-0-11406"


def _fixture() -> dict:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def _hourly_fixture() -> dict:
    return json.loads(HOURLY_FIXTURE_PATH.read_text(encoding="utf-8"))


def _recent_daily_fixture() -> dict:
    return json.loads(RECENT_DAILY_FIXTURE_PATH.read_text(encoding="utf-8"))


def _synop_station_fixture() -> dict:
    return json.loads(SYNOP_STATION_FIXTURE_PATH.read_text(encoding="utf-8"))


def _synop_station_hourly_fixture() -> dict:
    return json.loads(SYNOP_STATION_HOURLY_FIXTURE_PATH.read_text(encoding="utf-8"))


def _metadata_fixture() -> dict:
    return json.loads(METADATA_FIXTURE_PATH.read_text(encoding="utf-8"))


def _capabilities_fixture() -> dict:
    return json.loads(CAPABILITIES_FIXTURE_PATH.read_text(encoding="utf-8"))


def _flag_metadata_fixture() -> dict:
    return json.loads(FLAG_METADATA_FIXTURE_PATH.read_text(encoding="utf-8"))


def _quality_metadata_fixture() -> dict:
    return json.loads(QUALITY_METADATA_FIXTURE_PATH.read_text(encoding="utf-8"))


def _values(payload: dict) -> list:
    return payload["data"]["data"]["values"]


def test_parser_selects_latest_valid_values() -> None:
    observation = parse_current_observations(_fixture(), STATION_ID)

    assert observation.station_id == STATION_ID
    assert observation.observed_at.isoformat() == "2026-06-26T08:50:00+00:00"
    assert observation.temperature == 32.7
    assert observation.temperature_max_10m == 33.0
    assert observation.temperature_min_10m == 31.8
    assert observation.apparent_temperature == 25.0
    assert observation.humidity == 37.0
    assert observation.pressure is None
    assert observation.precipitation_10m == 0.0
    assert observation.wind_speed == 1.3
    assert observation.wind_speed_avg == 1.1
    assert observation.wind_gust == 2.9
    assert observation.wind_direction == 222.0
    assert observation.wind_direction_avg == 218.0
    assert observation.wind_gust_direction == 200.0
    assert "TPM" in observation.available_elements
    assert observation.quality_by_element["T"] == 5.0
    assert observation.flag_by_element["T"] is None


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


def test_parser_reads_observed_hourly_precipitation() -> None:
    observation = parse_current_observations(_hourly_fixture(), STATION_ID)

    assert observation.observed_at.isoformat() == "2026-06-26T09:00:00+00:00"
    assert observation.precipitation_1h == 2.1
    assert observation.precipitation_10m is None
    assert observation.precipitation_today is None
    assert observation.precipitation_samples == ()
    assert observation.quality_by_element["SRA1H"] == 5.0


def test_parser_reads_synop_weather_condition_elements() -> None:
    payload = deepcopy(_hourly_fixture())
    rows = _values(payload)
    rows.extend(
        [
            [STATION_ID, "N", "2026-06-26T09:00:00Z", 8.0, "", 0.0],
            [STATION_ID, "Td", "2026-06-26T09:00:00Z", 16.4, "", 0.0],
            [STATION_ID, "VV", "2026-06-26T09:00:00Z", 70.0, "", 0.0],
            [STATION_ID, "ww", "2026-06-26T09:00:00Z", 61.0, "", 0.0],
            [STATION_ID, "W1", "2026-06-26T09:00:00Z", 6.0, "", 0.0],
            [STATION_ID, "W2", "2026-06-26T09:00:00Z", 2.0, "", 0.0],
        ]
    )

    observation = parse_current_observations(payload, STATION_ID)

    assert observation.cloud_coverage == 8.0
    assert observation.dew_point == 16.4
    assert observation.visibility_code == 70.0
    assert observation.present_weather_code == 61.0
    assert observation.past_weather_code_1 == 6.0
    assert observation.past_weather_code_2 == 2.0


def test_parser_reads_additional_station_current_observations() -> None:
    observation = parse_current_observations(
        _synop_station_fixture(),
        SYNOP_STATION_ID,
    )

    assert observation.station_id == SYNOP_STATION_ID
    assert observation.observed_at.isoformat() == "2026-06-29T10:50:00+00:00"
    assert observation.temperature == 24.0
    assert observation.humidity == 69.0
    assert observation.pressure == 965.7
    assert observation.available_elements == ("H", "P", "T")
    assert observation.quality_by_element["P"] == 5.0


def test_parser_reads_additional_station_hourly_synop_observations() -> None:
    observation = parse_current_observations(
        _synop_station_hourly_fixture(),
        SYNOP_STATION_ID,
    )

    assert observation.station_id == SYNOP_STATION_ID
    assert observation.observed_at.isoformat() == "2026-06-29T10:00:00+00:00"
    assert observation.precipitation_1h == 0.0
    assert observation.dew_point == 17.2
    assert observation.visibility_code == 40.0
    assert observation.present_weather_code == 100.0
    assert observation.past_weather_code_1 == 18.0
    assert observation.past_weather_code_2 == 18.0
    assert "ww" in observation.available_elements


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


def test_api_client_prefers_companion_hourly_precipitation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FrozenDatetime(datetime):
        @classmethod
        def now(cls, tz=None):
            return cls(2026, 6, 26, 9, 30, tzinfo=tz or UTC)

    class PayloadClient(ChmiApiClient):
        def __init__(self):
            super().__init__(session=object())
            self.calls = []

        async def async_get_current_observations_for_date(
            self,
            station_id: str,
            day: date,
            *,
            interval_minutes: int = 10,
        ):
            self.calls.append((day, interval_minutes))
            if interval_minutes == 60:
                return parse_current_observations(_hourly_fixture(), station_id)
            return parse_current_observations(_fixture(), station_id)

    client = PayloadClient()
    monkeypatch.setattr(api, "datetime", FrozenDatetime)

    observation = asyncio.run(
        client.async_get_current_observations(
            STATION_ID,
            precipitation_1h_interval_minutes=60,
        )
    )

    assert observation.precipitation_1h == 2.1
    assert observation.precipitation_10m == 0.0
    assert observation.available_elements[-1] == "TPM"
    assert "SRA1H" in observation.available_elements
    assert observation.quality_by_element["SRA1H"] == 5.0
    assert client.calls == [(date(2026, 6, 26), 10), (date(2026, 6, 26), 60)]


def test_api_client_applies_companion_hourly_weather_condition_elements(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class FrozenDatetime(datetime):
        @classmethod
        def now(cls, tz=None):
            return cls(2026, 6, 26, 9, 30, tzinfo=tz or UTC)

    class PayloadClient(ChmiApiClient):
        def __init__(self):
            super().__init__(session=object())
            self.calls = []

        async def async_get_current_observations_for_date(
            self,
            station_id: str,
            day: date,
            *,
            interval_minutes: int = 10,
        ):
            self.calls.append((day, interval_minutes))
            if interval_minutes == 60:
                payload = deepcopy(_hourly_fixture())
                _values(payload).append(
                    [STATION_ID, "ww", "2026-06-26T09:00:00Z", 61.0, "", 0.0]
                )
                return parse_current_observations(payload, station_id)
            return parse_current_observations(_fixture(), station_id)

    client = PayloadClient()
    monkeypatch.setattr(api, "datetime", FrozenDatetime)

    observation = asyncio.run(
        client.async_get_current_observations(
            STATION_ID,
            weather_condition_interval_minutes=60,
        )
    )

    assert observation.present_weather_code == 61.0
    assert "ww" in observation.available_elements
    assert client.calls == [(date(2026, 6, 26), 10), (date(2026, 6, 26), 60)]


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
    assert "TMA" in capabilities.supported_elements
    assert "TMI" in capabilities.supported_elements
    assert "TPM" in capabilities.supported_elements
    assert "Dmax" in capabilities.supported_elements
    assert "Dprum" in capabilities.supported_elements
    assert "Fprum" in capabilities.supported_elements
    assert "P" not in capabilities.supported_elements
    assert "SRA1H" not in capabilities.supported_elements
    assert capabilities.supported_elements_by_interval[10] == (
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
    )
    assert capabilities.supported_elements_by_interval[60] == ("SRA1H",)


def test_parser_falls_back_to_hourly_station_capabilities() -> None:
    payload = deepcopy(_capabilities_fixture())
    payload["data"]["data"]["values"] = [
        row for row in _values(payload) if row[1] != STATION_ID or row[0] == "1H"
    ]

    capabilities = parse_station_capabilities(payload, STATION_ID)

    assert capabilities.observation_type == "1H"
    assert capabilities.observation_interval_minutes == 60
    assert capabilities.supported_elements == ("SRA1H",)
    assert capabilities.supported_elements_by_interval == {60: ("SRA1H",)}


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


def test_parser_reads_flag_descriptions() -> None:
    descriptions = parse_flag_descriptions(_flag_metadata_fixture())

    assert descriptions["D"]["V"] == "Variable"
    assert descriptions["Dmax"]["V"] == "Variable"
    assert descriptions["SCE"]["A"] == "Ovlivneno umelym snezenim"


def test_parser_reads_quality_descriptions() -> None:
    descriptions = parse_quality_descriptions(_quality_metadata_fixture())

    assert descriptions[0] == "Good/Kvalitni hodnota"
    assert descriptions[1] == "Suspect/Podezrela hodnota"
    assert descriptions[5] == "Unknown/Kvalita neznama"


def test_api_client_builds_flag_descriptions_url() -> None:
    client = ChmiApiClient(session=object())

    url = client._build_flag_descriptions_url(date(2026, 6, 26))

    assert (
        url == "https://opendata.chmi.cz/meteorology/climate/now/metadata/"
        "meta3-20260626.json"
    )


def test_api_client_builds_quality_descriptions_url() -> None:
    client = ChmiApiClient(session=object())

    url = client._build_quality_descriptions_url(date(2026, 6, 26))

    assert (
        url == "https://opendata.chmi.cz/meteorology/climate/now/metadata/"
        "meta4-20260626.json"
    )


def test_parser_reads_recent_daily_summary() -> None:
    summary = parse_recent_daily_summary(
        _recent_daily_fixture(),
        STATION_ID,
        date(2026, 6, 28),
    )

    assert summary.station_id == STATION_ID
    assert summary.summary_date == date(2026, 6, 28)
    assert summary.yesterday_precipitation == 0.8
    assert summary.yesterday_temperature_max == 30.4
    assert summary.yesterday_temperature_min == 13.2
    assert summary.yesterday_wind_gust_max == 6.8
    assert summary.month_precipitation_chmi == 3.4


def test_api_client_builds_recent_daily_url() -> None:
    client = ChmiApiClient(session=object())

    url = client._build_recent_daily_url(STATION_ID, date(2026, 6, 28))

    assert (
        url == "https://opendata.chmi.cz/meteorology/climate/recent/data/daily/"
        "dly-0-203-0-11521-202606.json"
    )


def test_api_client_rejects_unsafe_station_id_for_recent_daily_url() -> None:
    client = ChmiApiClient(session=object())

    with pytest.raises(ChmiApiDataError):
        client._build_recent_daily_url("../0-203-0-11521?x=1", date(2026, 6, 28))
