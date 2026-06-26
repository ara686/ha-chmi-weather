"""Config flow for CHMI Weather."""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import (
    ChmiApiClient,
    ChmiApiConnectionError,
    ChmiApiDataError,
    ChmiApiError,
    has_usable_observation,
)
from .const import (
    CONF_DIAGNOSTIC_SENSORS,
    CONF_FORECAST_SOURCE,
    CONF_LATITUDE,
    CONF_LONGITUDE,
    CONF_STATION_ID,
    CONF_STATION_NAME,
    CONF_UPDATE_INTERVAL,
    DEFAULT_DIAGNOSTIC_SENSORS,
    DEFAULT_FORECAST_SOURCE,
    DEFAULT_LATITUDE,
    DEFAULT_LONGITUDE,
    DEFAULT_STATION_ID,
    DEFAULT_STATION_NAME,
    DEFAULT_UPDATE_INTERVAL_MINUTES,
    DOMAIN,
)


class ChmiWeatherConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for CHMI Weather."""

    VERSION = 1

    async def async_step_user(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Handle the initial setup step."""
        errors: dict[str, str] = {}

        if user_input is not None:
            data = _normalize_user_input(user_input)
            errors = await _validate_user_input(self.hass, data)

            if not errors:
                await self.async_set_unique_id(data[CONF_STATION_ID])
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=f"CHMI {data[CONF_STATION_NAME]}",
                    data=data,
                    options={
                        CONF_UPDATE_INTERVAL: DEFAULT_UPDATE_INTERVAL_MINUTES,
                        CONF_DIAGNOSTIC_SENSORS: DEFAULT_DIAGNOSTIC_SENSORS,
                        CONF_FORECAST_SOURCE: DEFAULT_FORECAST_SOURCE,
                    },
                )
        else:
            data = _default_user_input()

        return self.async_show_form(
            step_id="user",
            data_schema=_user_schema(data),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> ChmiWeatherOptionsFlow:
        """Create the options flow."""
        return ChmiWeatherOptionsFlow(config_entry)


class ChmiWeatherOptionsFlow(config_entries.OptionsFlow):
    """Handle CHMI Weather options."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self._config_entry = config_entry

    async def async_step_init(
        self,
        user_input: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Manage integration options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        options = self._config_entry.options
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_UPDATE_INTERVAL,
                        default=options.get(
                            CONF_UPDATE_INTERVAL,
                            DEFAULT_UPDATE_INTERVAL_MINUTES,
                        ),
                    ): vol.All(vol.Coerce(int), vol.Range(min=1, max=1440)),
                    vol.Required(
                        CONF_DIAGNOSTIC_SENSORS,
                        default=options.get(
                            CONF_DIAGNOSTIC_SENSORS,
                            DEFAULT_DIAGNOSTIC_SENSORS,
                        ),
                    ): bool,
                    vol.Required(
                        CONF_FORECAST_SOURCE,
                        default=options.get(
                            CONF_FORECAST_SOURCE,
                            DEFAULT_FORECAST_SOURCE,
                        ),
                    ): vol.In([DEFAULT_FORECAST_SOURCE]),
                }
            ),
        )


def _default_user_input() -> dict[str, Any]:
    return {
        CONF_STATION_NAME: DEFAULT_STATION_NAME,
        CONF_STATION_ID: DEFAULT_STATION_ID,
        CONF_LATITUDE: DEFAULT_LATITUDE,
        CONF_LONGITUDE: DEFAULT_LONGITUDE,
    }


def _normalize_user_input(user_input: dict[str, Any]) -> dict[str, Any]:
    return {
        CONF_STATION_NAME: str(user_input[CONF_STATION_NAME]).strip(),
        CONF_STATION_ID: str(user_input[CONF_STATION_ID]).strip(),
        CONF_LATITUDE: float(user_input[CONF_LATITUDE]),
        CONF_LONGITUDE: float(user_input[CONF_LONGITUDE]),
    }


def _user_schema(defaults: dict[str, Any]) -> vol.Schema:
    return vol.Schema(
        {
            vol.Required(
                CONF_STATION_NAME,
                default=defaults.get(CONF_STATION_NAME, DEFAULT_STATION_NAME),
            ): str,
            vol.Required(
                CONF_STATION_ID,
                default=defaults.get(CONF_STATION_ID, DEFAULT_STATION_ID),
            ): str,
            vol.Required(
                CONF_LATITUDE,
                default=defaults.get(CONF_LATITUDE, DEFAULT_LATITUDE),
            ): vol.All(vol.Coerce(float), vol.Range(min=-90, max=90)),
            vol.Required(
                CONF_LONGITUDE,
                default=defaults.get(CONF_LONGITUDE, DEFAULT_LONGITUDE),
            ): vol.All(vol.Coerce(float), vol.Range(min=-180, max=180)),
        }
    )


async def _validate_user_input(
    hass: HomeAssistant,
    data: dict[str, Any],
) -> dict[str, str]:
    errors: dict[str, str] = {}
    if not data[CONF_STATION_ID]:
        errors["base"] = "no_station_id"
        return errors

    client = ChmiApiClient(async_get_clientsession(hass))
    try:
        observation = await client.async_get_current_observations(data[CONF_STATION_ID])
    except ChmiApiConnectionError:
        errors["base"] = "cannot_connect"
    except ChmiApiDataError:
        errors["base"] = "no_data"
    except ChmiApiError:
        errors["base"] = "unknown"
    else:
        if not has_usable_observation(observation):
            errors["base"] = "no_data"

    return errors
