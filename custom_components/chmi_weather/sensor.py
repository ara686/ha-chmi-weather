"""Sensor platform for CHMI Weather."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    DEGREE,
    PERCENTAGE,
    EntityCategory,
    UnitOfPrecipitationDepth,
    UnitOfPressure,
    UnitOfSpeed,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    CONF_DIAGNOSTIC_SENSORS,
    CONF_STATION_ID,
    CONF_STATION_NAME,
    DEFAULT_DIAGNOSTIC_SENSORS,
    DOMAIN,
    MANUFACTURER,
    MODEL,
)
from .coordinator import ChmiDataUpdateCoordinator
from .models import ChmiObservation


@dataclass(frozen=True, slots=True)
class ChmiSensorDescription:
    """Description for a CHMI sensor entity."""

    key: str
    name: str
    translation_key: str
    value_fn: Callable[[ChmiObservation], Any]
    native_unit_of_measurement: str | None = None
    device_class: SensorDeviceClass | None = None
    state_class: SensorStateClass | None = None


SENSOR_DESCRIPTIONS: tuple[ChmiSensorDescription, ...] = (
    ChmiSensorDescription(
        key="temperature",
        name="Temperature",
        translation_key="temperature",
        value_fn=lambda observation: observation.temperature,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    ChmiSensorDescription(
        key="humidity",
        name="Humidity",
        translation_key="humidity",
        value_fn=lambda observation: observation.humidity,
        native_unit_of_measurement=PERCENTAGE,
        device_class=SensorDeviceClass.HUMIDITY,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    ChmiSensorDescription(
        key="pressure",
        name="Pressure",
        translation_key="pressure",
        value_fn=lambda observation: observation.pressure,
        native_unit_of_measurement=UnitOfPressure.HPA,
        device_class=SensorDeviceClass.PRESSURE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    ChmiSensorDescription(
        key="precipitation_10m",
        name="Precipitation 10m",
        translation_key="precipitation_10m",
        value_fn=lambda observation: observation.precipitation_10m,
        native_unit_of_measurement=UnitOfPrecipitationDepth.MILLIMETERS,
        device_class=SensorDeviceClass.PRECIPITATION,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    ChmiSensorDescription(
        key="wind_speed",
        name="Wind speed",
        translation_key="wind_speed",
        value_fn=lambda observation: observation.wind_speed,
        native_unit_of_measurement=UnitOfSpeed.METERS_PER_SECOND,
        device_class=SensorDeviceClass.WIND_SPEED,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    ChmiSensorDescription(
        key="wind_gust",
        name="Wind gust",
        translation_key="wind_gust",
        value_fn=lambda observation: observation.wind_gust,
        native_unit_of_measurement=UnitOfSpeed.METERS_PER_SECOND,
        device_class=SensorDeviceClass.WIND_SPEED,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    ChmiSensorDescription(
        key="wind_direction",
        name="Wind direction",
        translation_key="wind_direction",
        value_fn=lambda observation: observation.wind_direction,
        native_unit_of_measurement=DEGREE,
        device_class=SensorDeviceClass.WIND_DIRECTION,
        state_class=SensorStateClass.MEASUREMENT_ANGLE,
    ),
    ChmiSensorDescription(
        key="last_update",
        name="Last update",
        translation_key="last_update",
        value_fn=lambda observation: observation.observed_at,
        device_class=SensorDeviceClass.TIMESTAMP,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up CHMI Weather sensor entities."""
    if not entry.options.get(CONF_DIAGNOSTIC_SENSORS, DEFAULT_DIAGNOSTIC_SENSORS):
        async_add_entities([])
        return

    runtime_data = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            ChmiSensorEntity(runtime_data.coordinator, entry, description)
            for description in SENSOR_DESCRIPTIONS
        ]
    )


class ChmiSensorEntity(CoordinatorEntity[ChmiDataUpdateCoordinator], SensorEntity):
    """Sensor entity backed by the shared CHMI coordinator."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_should_poll = False

    def __init__(
        self,
        coordinator: ChmiDataUpdateCoordinator,
        entry: ConfigEntry,
        description: ChmiSensorDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._station_id = entry.data[CONF_STATION_ID]
        self._station_name = entry.data[CONF_STATION_NAME]
        self._attr_name = f"CHMI {self._station_name} {description.name}"
        self._attr_unique_id = f"{self._station_id}_{description.key}"
        self._attr_translation_key = description.translation_key

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
    def native_value(self) -> float | datetime | None:
        """Return the sensor value."""
        return self.entity_description.value_fn(self.observation)

    @property
    def native_unit_of_measurement(self) -> str | None:
        """Return native unit."""
        return self.entity_description.native_unit_of_measurement

    @property
    def device_class(self) -> SensorDeviceClass | None:
        """Return sensor device class."""
        return self.entity_description.device_class

    @property
    def state_class(self) -> SensorStateClass | None:
        """Return sensor state class."""
        return self.entity_description.state_class

    @property
    def observation(self) -> ChmiObservation:
        """Return coordinator data or the last valid observation."""
        return self.coordinator.data or self.coordinator.last_observation
