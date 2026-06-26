"""Tests for CHMI Weather config flow."""

from __future__ import annotations

import asyncio
from types import SimpleNamespace

from custom_components.chmi_weather import config_flow
from custom_components.chmi_weather.const import (
    CONF_DIAGNOSTIC_SENSORS,
    CONF_LATITUDE,
    CONF_LONGITUDE,
    CONF_STATION_ID,
    CONF_STATION_NAME,
    CONF_UPDATE_INTERVAL,
    DEFAULT_UPDATE_INTERVAL_MINUTES,
)


def test_config_flow_creates_entry(monkeypatch) -> None:
    async def fake_validate(hass, data):
        return {}

    async def run() -> dict:
        flow = config_flow.ChmiWeatherConfigFlow()
        flow.hass = SimpleNamespace()
        return await flow.async_step_user(
            {
                CONF_STATION_NAME: "Dobrichovice",
                CONF_STATION_ID: "0-203-0-11521",
                CONF_LATITUDE: 49.9335,
                CONF_LONGITUDE: 14.2759,
            }
        )

    monkeypatch.setattr(config_flow, "_validate_user_input", fake_validate)

    result = asyncio.run(run())

    assert result["type"] == "create_entry"
    assert result["title"] == "CHMI Dobrichovice"
    assert result["data"][CONF_STATION_ID] == "0-203-0-11521"
    assert result["options"][CONF_UPDATE_INTERVAL] == DEFAULT_UPDATE_INTERVAL_MINUTES
    assert result["options"][CONF_DIAGNOSTIC_SENSORS] is True


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
