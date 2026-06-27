"""CHMI Weather integration for Home Assistant."""

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import ChmiApiClient, ChmiApiError
from .const import CONF_STATION_ID, CONF_SUPPORTED_ELEMENTS
from .coordinator import ChmiDataUpdateCoordinator

PLATFORMS: tuple[Platform, ...] = (Platform.WEATHER, Platform.SENSOR)


@dataclass(slots=True)
class ChmiWeatherRuntimeData:
    """Runtime objects shared by CHMI Weather platforms."""

    client: ChmiApiClient
    coordinator: ChmiDataUpdateCoordinator


type ChmiWeatherConfigEntry = ConfigEntry[ChmiWeatherRuntimeData]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ChmiWeatherConfigEntry,
) -> bool:
    """Set up CHMI Weather from a config entry."""
    session = async_get_clientsession(hass)
    client = ChmiApiClient(session)
    await _async_refresh_station_capabilities(hass, entry, client)
    coordinator = ChmiDataUpdateCoordinator(hass, entry, client)
    await coordinator.async_config_entry_first_refresh()

    entry.runtime_data = ChmiWeatherRuntimeData(
        client=client,
        coordinator=coordinator,
    )
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(
    hass: HomeAssistant,
    entry: ChmiWeatherConfigEntry,
) -> bool:
    """Unload a CHMI Weather config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_reload_entry(
    hass: HomeAssistant,
    entry: ChmiWeatherConfigEntry,
) -> None:
    """Reload a CHMI Weather config entry."""
    await async_unload_entry(hass, entry)
    await async_setup_entry(hass, entry)


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload entry when options are updated."""
    await hass.config_entries.async_reload(entry.entry_id)


async def _async_refresh_station_capabilities(
    hass: HomeAssistant,
    entry: ConfigEntry,
    client: ChmiApiClient,
) -> None:
    """Refresh capability metadata so entities match station measurements."""
    try:
        capabilities = await client.async_get_station_capabilities(
            entry.data[CONF_STATION_ID]
        )
    except ChmiApiError:
        return

    supported_elements = list(capabilities.supported_elements)
    if entry.data.get(CONF_SUPPORTED_ELEMENTS) == supported_elements:
        return

    hass.config_entries.async_update_entry(
        entry,
        data={**entry.data, CONF_SUPPORTED_ELEMENTS: supported_elements},
    )
