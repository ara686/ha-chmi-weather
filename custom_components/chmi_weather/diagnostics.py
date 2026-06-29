"""Diagnostics support for CHMI Weather."""

from __future__ import annotations

from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import (
    CHMI_QUALITY_DESCRIPTIONS,
    CONF_DIAGNOSTIC_SENSORS,
    CONF_LATITUDE,
    CONF_LONGITUDE,
    CONF_OBSERVATION_INTERVAL_MINUTES,
    CONF_STATION_ID,
    CONF_STATION_NAME,
    CONF_SUPPORTED_ELEMENTS,
    CONF_SUPPORTED_ELEMENTS_BY_INTERVAL,
    CONF_UPDATE_INTERVAL,
    DEFAULT_DIAGNOSTIC_SENSORS,
    DEFAULT_OBSERVATION_INTERVAL_MINUTES,
    DOMAIN,
)


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    runtime_data = getattr(config_entry, "runtime_data", None)
    if runtime_data is None:
        runtime_data = hass.data.get(DOMAIN, {}).get(config_entry.entry_id)

    observation = None
    if runtime_data is not None:
        observation = (
            runtime_data.coordinator.last_observation or runtime_data.coordinator.data
        )
    observation_interval_minutes = max(
        1,
        int(
            config_entry.data.get(
                CONF_OBSERVATION_INTERVAL_MINUTES,
                DEFAULT_OBSERVATION_INTERVAL_MINUTES,
            )
        ),
    )
    configured_update_interval_minutes = int(
        config_entry.options.get(
            CONF_UPDATE_INTERVAL,
            observation_interval_minutes,
        )
    )
    effective_update_interval_minutes = max(
        1,
        min(
            configured_update_interval_minutes,
            observation_interval_minutes,
        ),
    )
    if runtime_data is not None:
        effective_update_interval_minutes = getattr(
            runtime_data.coordinator,
            "update_interval_minutes",
            effective_update_interval_minutes,
        )

    return {
        "station_id": config_entry.data.get(CONF_STATION_ID),
        "station_name": config_entry.data.get(CONF_STATION_NAME),
        "latitude": config_entry.data.get(CONF_LATITUDE),
        "longitude": config_entry.data.get(CONF_LONGITUDE),
        "observation_interval_minutes": observation_interval_minutes,
        "configured_update_interval_minutes": configured_update_interval_minutes,
        "effective_update_interval_minutes": effective_update_interval_minutes,
        "update_interval_minutes": effective_update_interval_minutes,
        "diagnostic_sensors_enabled": config_entry.options.get(
            CONF_DIAGNOSTIC_SENSORS,
            DEFAULT_DIAGNOSTIC_SENSORS,
        ),
        "supported_elements": list(config_entry.data.get(CONF_SUPPORTED_ELEMENTS, [])),
        "supported_elements_by_interval": dict(
            config_entry.data.get(CONF_SUPPORTED_ELEMENTS_BY_INTERVAL, {})
        ),
        "last_observed_timestamp": (
            observation.observed_at.isoformat()
            if observation is not None and observation.observed_at is not None
            else None
        ),
        "last_successful_poll_timestamp": (
            runtime_data.coordinator.last_successful_poll.isoformat()
            if runtime_data is not None
            and runtime_data.coordinator.last_successful_poll is not None
            else None
        ),
        "available_elements": (
            list(observation.available_elements) if observation is not None else []
        ),
        "quality_by_element": (
            _quality_by_element(observation.quality_by_element)
            if observation is not None
            else {}
        ),
        "flag_by_element": observation.flag_by_element
        if observation is not None
        else {},
        "quality_code_descriptions": {
            str(code): description
            for code, description in CHMI_QUALITY_DESCRIPTIONS.items()
        },
    }


def _quality_by_element(
    quality_by_element: dict[str, float | None],
) -> dict[str, dict[str, float | str | None]]:
    """Return diagnostic-friendly CHMI quality details."""
    return {
        element: {
            "code": quality,
            "description": _quality_description(quality),
        }
        for element, quality in quality_by_element.items()
    }


def _quality_description(quality: float | None) -> str | None:
    if quality is None:
        return None

    code = int(quality)
    if quality != code:
        return None
    return CHMI_QUALITY_DESCRIPTIONS.get(code)
