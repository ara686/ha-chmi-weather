"""Diagnostics support for CHMI Weather."""

from __future__ import annotations

from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import (
    CONF_DIAGNOSTIC_SENSORS,
    CONF_LATITUDE,
    CONF_LONGITUDE,
    CONF_STATION_ID,
    CONF_STATION_NAME,
    CONF_UPDATE_INTERVAL,
    DEFAULT_DIAGNOSTIC_SENSORS,
    DEFAULT_UPDATE_INTERVAL_MINUTES,
    DOMAIN,
)


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    runtime_data = hass.data.get(DOMAIN, {}).get(config_entry.entry_id)
    observation = None
    if runtime_data is not None:
        observation = (
            runtime_data.coordinator.last_observation or runtime_data.coordinator.data
        )

    return {
        "station_id": config_entry.data.get(CONF_STATION_ID),
        "station_name": config_entry.data.get(CONF_STATION_NAME),
        "latitude": config_entry.data.get(CONF_LATITUDE),
        "longitude": config_entry.data.get(CONF_LONGITUDE),
        "update_interval_minutes": config_entry.options.get(
            CONF_UPDATE_INTERVAL,
            DEFAULT_UPDATE_INTERVAL_MINUTES,
        ),
        "diagnostic_sensors_enabled": config_entry.options.get(
            CONF_DIAGNOSTIC_SENSORS,
            DEFAULT_DIAGNOSTIC_SENSORS,
        ),
        "last_observed_timestamp": (
            observation.observed_at.isoformat()
            if observation is not None and observation.observed_at is not None
            else None
        ),
        "available_elements": (
            list(observation.available_elements) if observation is not None else []
        ),
    }
