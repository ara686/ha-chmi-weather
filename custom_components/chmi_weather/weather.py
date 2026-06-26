"""Weather platform for CHMI Weather."""

from __future__ import annotations

from homeassistant.components.weather import WeatherEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    UnitOfPrecipitationDepth,
    UnitOfPressure,
    UnitOfSpeed,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    ATTRIBUTION,
    CONF_STATION_ID,
    CONF_STATION_NAME,
    DOMAIN,
    MANUFACTURER,
    MODEL,
)
from .coordinator import ChmiDataUpdateCoordinator
from .models import ChmiObservation


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up CHMI Weather weather entities."""
    runtime_data = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([ChmiWeatherEntity(runtime_data.coordinator, entry)])


class ChmiWeatherEntity(CoordinatorEntity[ChmiDataUpdateCoordinator], WeatherEntity):
    """Weather entity for one CHMI OpenData station."""

    _attr_attribution = ATTRIBUTION
    _attr_should_poll = False

    def __init__(
        self,
        coordinator: ChmiDataUpdateCoordinator,
        entry: ConfigEntry,
    ) -> None:
        """Initialize the weather entity."""
        super().__init__(coordinator)
        self._entry = entry
        self._station_id = entry.data[CONF_STATION_ID]
        self._station_name = entry.data[CONF_STATION_NAME]
        self._attr_name = f"CHMI {self._station_name}"
        self._attr_unique_id = f"{self._station_id}_weather"

    @property
    def device_info(self) -> dict[str, object]:
        """Return device registry information."""
        return {
            "identifiers": {(DOMAIN, self._station_id)},
            "manufacturer": MANUFACTURER,
            "model": MODEL,
            "name": f"CHMI {self._station_name}",
        }

    @property
    def condition(self) -> str | None:
        """Return the current weather condition."""
        return condition_from_observation(self.observation)

    @property
    def native_temperature(self) -> float | None:
        """Return native temperature."""
        return self.observation.temperature

    @property
    def native_temperature_unit(self) -> str:
        """Return native temperature unit."""
        return UnitOfTemperature.CELSIUS

    @property
    def humidity(self) -> float | None:
        """Return relative humidity."""
        return self.observation.humidity

    @property
    def native_pressure(self) -> float | None:
        """Return native pressure."""
        return self.observation.pressure

    @property
    def native_pressure_unit(self) -> str:
        """Return native pressure unit."""
        return UnitOfPressure.HPA

    @property
    def native_wind_speed(self) -> float | None:
        """Return native wind speed."""
        return self.observation.wind_speed

    @property
    def native_wind_gust_speed(self) -> float | None:
        """Return native wind gust speed."""
        return self.observation.wind_gust

    @property
    def native_wind_speed_unit(self) -> str:
        """Return native wind speed unit."""
        return UnitOfSpeed.METERS_PER_SECOND

    @property
    def wind_bearing(self) -> float | None:
        """Return wind bearing."""
        return self.observation.wind_direction

    @property
    def native_precipitation_unit(self) -> str:
        """Return precipitation unit."""
        return UnitOfPrecipitationDepth.MILLIMETERS

    @property
    def observation(self) -> ChmiObservation:
        """Return coordinator data or the last valid observation."""
        return self.coordinator.data or self.coordinator.last_observation


def condition_from_observation(observation: ChmiObservation) -> str:
    """Return a best-effort HA condition until a better CHMI condition source exists."""
    if observation.precipitation_10m is not None and observation.precipitation_10m > 0:
        return "rainy"
    return "partlycloudy"
