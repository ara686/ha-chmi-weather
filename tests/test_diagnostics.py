"""Tests for CHMI Weather diagnostics."""

from __future__ import annotations

import asyncio
from datetime import UTC, date, datetime
from types import SimpleNamespace

from custom_components.chmi_weather.const import (
    CONF_OBSERVATION_INTERVAL_MINUTES,
    CONF_STATION_ID,
    CONF_SUPPORTED_ELEMENTS_BY_INTERVAL,
    CONF_UPDATE_INTERVAL,
    DOMAIN,
)
from custom_components.chmi_weather.diagnostics import (
    async_get_config_entry_diagnostics,
)
from custom_components.chmi_weather.models import ChmiObservation


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
        daily_summary_date=date(2026, 6, 25),
        available_elements=("D", "F", "Fmax", "H", "SRA10M", "T"),
        quality_by_element={"T": 5.0, "SRA10M": 0.0, "D": 0.0},
        flag_by_element={"T": None, "SRA10M": None, "D": "V"},
    )


def test_diagnostics_include_poll_and_observation_timestamps() -> None:
    coordinator = SimpleNamespace(
        data=_observation(),
        last_observation=None,
        last_successful_poll=datetime(2026, 6, 26, 8, 51, tzinfo=UTC),
    )
    config_entry = SimpleNamespace(
        entry_id="entry-id",
        data={
            CONF_STATION_ID: "0-203-0-11521",
            CONF_OBSERVATION_INTERVAL_MINUTES: 10,
            CONF_SUPPORTED_ELEMENTS_BY_INTERVAL: {"10": ["SRA10M"], "60": ["SRA1H"]},
        },
        options={CONF_UPDATE_INTERVAL: 60},
        runtime_data=SimpleNamespace(
            coordinator=coordinator,
            flag_descriptions={"D": {"V": "Variable"}},
            quality_descriptions={
                0: "Good/Kvalitni hodnota",
                5: "Unknown/Kvalita neznama",
            },
        ),
    )
    hass = SimpleNamespace(data={DOMAIN: {}})

    diagnostics = asyncio.run(async_get_config_entry_diagnostics(hass, config_entry))

    assert diagnostics["last_observed_timestamp"] == "2026-06-26T08:50:00+00:00"
    assert diagnostics["last_successful_poll_timestamp"] == "2026-06-26T08:51:00+00:00"
    assert diagnostics["daily_summary_date"] == "2026-06-25"
    assert diagnostics["observation_interval_minutes"] == 10
    assert diagnostics["configured_update_interval_minutes"] == 60
    assert diagnostics["effective_update_interval_minutes"] == 60
    assert diagnostics["supported_elements_by_interval"] == {
        "10": ["SRA10M"],
        "60": ["SRA1H"],
    }
    assert diagnostics["quality_by_element"]["T"] == {
        "code": 5.0,
        "description": "Unknown/Kvalita neznama",
    }
    assert diagnostics["quality_by_element"]["SRA10M"] == {
        "code": 0.0,
        "description": "Good/Kvalitni hodnota",
    }
    assert diagnostics["flag_by_element"]["T"] == {
        "flag": None,
        "description": None,
    }
    assert diagnostics["flag_by_element"]["D"] == {
        "flag": "V",
        "description": "Variable",
    }
    assert diagnostics["quality_code_descriptions"]["0"] == "Good/Kvalitni hodnota"
