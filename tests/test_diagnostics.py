"""Tests for CHMI Weather diagnostics."""

from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from types import SimpleNamespace

from custom_components.chmi_weather.const import (
    CONF_OBSERVATION_INTERVAL_MINUTES,
    CONF_STATION_ID,
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
        available_elements=("D", "F", "Fmax", "H", "SRA10M", "T"),
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
        },
        options={CONF_UPDATE_INTERVAL: 60},
        runtime_data=SimpleNamespace(coordinator=coordinator),
    )
    hass = SimpleNamespace(data={DOMAIN: {}})

    diagnostics = asyncio.run(async_get_config_entry_diagnostics(hass, config_entry))

    assert diagnostics["last_observed_timestamp"] == "2026-06-26T08:50:00+00:00"
    assert diagnostics["last_successful_poll_timestamp"] == "2026-06-26T08:51:00+00:00"
    assert diagnostics["observation_interval_minutes"] == 10
    assert diagnostics["configured_update_interval_minutes"] == 60
    assert diagnostics["effective_update_interval_minutes"] == 10
