"""DataUpdateCoordinator for CHMI Weather."""

from __future__ import annotations

import logging
from datetime import UTC, datetime, timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import ChmiApiClient, ChmiApiError
from .const import (
    CONF_STATION_ID,
    CONF_UPDATE_INTERVAL,
    DEFAULT_UPDATE_INTERVAL_MINUTES,
    DOMAIN,
)
from .models import ChmiObservation

_LOGGER = logging.getLogger(__name__)


class ChmiDataUpdateCoordinator(DataUpdateCoordinator[ChmiObservation]):
    """Coordinate polling of one CHMI OpenData station file."""

    def __init__(
        self,
        hass: HomeAssistant,
        config_entry: ConfigEntry,
        client: ChmiApiClient,
    ) -> None:
        """Initialize the coordinator."""
        self.config_entry = config_entry
        self.client = client
        self.last_observation: ChmiObservation | None = None
        self.last_successful_poll: datetime | None = None

        update_interval_minutes = int(
            config_entry.options.get(
                CONF_UPDATE_INTERVAL,
                DEFAULT_UPDATE_INTERVAL_MINUTES,
            )
        )

        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN}_{config_entry.data[CONF_STATION_ID]}",
            config_entry=config_entry,
            update_interval=timedelta(minutes=update_interval_minutes),
            always_update=True,
        )

    async def _async_update_data(self) -> ChmiObservation:
        """Fetch the latest observation from CHMI OpenData."""
        station_id = self.config_entry.data[CONF_STATION_ID]
        try:
            observation = await self.client.async_get_current_observations(station_id)
        except ChmiApiError as err:
            raise UpdateFailed(f"Failed to update CHMI observations: {err}") from err
        except Exception as err:
            raise UpdateFailed(
                "Unexpected error while updating CHMI observations"
            ) from err

        self.last_observation = observation
        self.last_successful_poll = datetime.now(UTC)
        _LOGGER.debug(
            "Updated CHMI observation for %s at %s; poll completed at %s",
            station_id,
            observation.observed_at,
            self.last_successful_poll,
        )
        return observation
