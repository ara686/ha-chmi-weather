"""Sensor platform for CHMI Weather."""

from __future__ import annotations

from collections.abc import Callable, Collection
from datetime import datetime
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import (
    DEGREE,
    EntityCategory,
    UnitOfPrecipitationDepth,
    UnitOfPressure,
    UnitOfSpeed,
    UnitOfTemperature,
)

try:
    from homeassistant.const import UnitOfRatio
except ImportError:
    from homeassistant.const import PERCENTAGE as UNIT_PERCENTAGE
else:
    UNIT_PERCENTAGE = UnitOfRatio.PERCENTAGE

from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import ChmiWeatherConfigEntry
from .const import (
    CONF_DIAGNOSTIC_SENSORS,
    CONF_STATION_ID,
    CONF_STATION_NAME,
    CONF_SUPPORTED_ELEMENTS,
    DEFAULT_DIAGNOSTIC_SENSORS,
    DOMAIN,
    ELEMENT_APPARENT_TEMPERATURE,
    ELEMENT_HUMIDITY,
    ELEMENT_PRECIPITATION_1H,
    ELEMENT_PRECIPITATION_10M,
    ELEMENT_PRESSURE,
    ELEMENT_TEMPERATURE,
    ELEMENT_TEMPERATURE_MAX_10M,
    ELEMENT_TEMPERATURE_MIN_10M,
    ELEMENT_WIND_DIRECTION,
    ELEMENT_WIND_DIRECTION_AVG,
    ELEMENT_WIND_GUST,
    ELEMENT_WIND_GUST_DIRECTION,
    ELEMENT_WIND_SPEED,
    ELEMENT_WIND_SPEED_AVG,
    MANUFACTURER,
    MODEL,
)
from .coordinator import ChmiDataUpdateCoordinator
from .models import ChmiObservation


class ChmiSensorDescription(SensorEntityDescription, frozen_or_thawed=True):
    """Description for a CHMI sensor entity."""

    value_fn: Callable[[ChmiDataUpdateCoordinator, ChmiObservation], Any]
    required_elements: tuple[str, ...] = ()
    any_required_elements: tuple[str, ...] = ()
    entity_category: EntityCategory | None = None


PRECIPITATION_DISPLAY_PRECISION = 1

SENSOR_DESCRIPTIONS: tuple[ChmiSensorDescription, ...] = (
    ChmiSensorDescription(
        key="temperature",
        name="Temperature",
        translation_key="temperature",
        value_fn=lambda coordinator, observation: observation.temperature,
        required_elements=(ELEMENT_TEMPERATURE,),
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    ChmiSensorDescription(
        key="temperature_max_10m",
        name="Temperature maximum 10m",
        translation_key="temperature_max_10m",
        value_fn=lambda coordinator, observation: observation.temperature_max_10m,
        required_elements=(ELEMENT_TEMPERATURE_MAX_10M,),
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    ChmiSensorDescription(
        key="temperature_min_10m",
        name="Temperature minimum 10m",
        translation_key="temperature_min_10m",
        value_fn=lambda coordinator, observation: observation.temperature_min_10m,
        required_elements=(ELEMENT_TEMPERATURE_MIN_10M,),
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    ChmiSensorDescription(
        key="apparent_temperature",
        name="Apparent temperature",
        translation_key="apparent_temperature",
        value_fn=lambda coordinator, observation: observation.apparent_temperature,
        required_elements=(ELEMENT_APPARENT_TEMPERATURE,),
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    ChmiSensorDescription(
        key="humidity",
        name="Humidity",
        translation_key="humidity",
        value_fn=lambda coordinator, observation: observation.humidity,
        required_elements=(ELEMENT_HUMIDITY,),
        native_unit_of_measurement=UNIT_PERCENTAGE,
        device_class=SensorDeviceClass.HUMIDITY,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    ChmiSensorDescription(
        key="pressure",
        name="Pressure",
        translation_key="pressure",
        value_fn=lambda coordinator, observation: observation.pressure,
        required_elements=(ELEMENT_PRESSURE,),
        native_unit_of_measurement=UnitOfPressure.HPA,
        device_class=SensorDeviceClass.PRESSURE,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    ChmiSensorDescription(
        key="precipitation_10m",
        name="Precipitation 10m",
        translation_key="precipitation_10m",
        value_fn=lambda coordinator, observation: observation.precipitation_10m,
        required_elements=(ELEMENT_PRECIPITATION_10M,),
        native_unit_of_measurement=UnitOfPrecipitationDepth.MILLIMETERS,
        device_class=SensorDeviceClass.PRECIPITATION,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=PRECIPITATION_DISPLAY_PRECISION,
    ),
    ChmiSensorDescription(
        key="precipitation_1h",
        name="Precipitation 1h",
        translation_key="precipitation_1h",
        value_fn=lambda coordinator, observation: observation.precipitation_1h,
        any_required_elements=(ELEMENT_PRECIPITATION_10M, ELEMENT_PRECIPITATION_1H),
        native_unit_of_measurement=UnitOfPrecipitationDepth.MILLIMETERS,
        device_class=SensorDeviceClass.PRECIPITATION,
        suggested_display_precision=PRECIPITATION_DISPLAY_PRECISION,
    ),
    ChmiSensorDescription(
        key="precipitation_today",
        name="Precipitation today",
        translation_key="precipitation_today",
        value_fn=lambda coordinator, observation: observation.precipitation_today,
        required_elements=(ELEMENT_PRECIPITATION_10M,),
        native_unit_of_measurement=UnitOfPrecipitationDepth.MILLIMETERS,
        device_class=SensorDeviceClass.PRECIPITATION,
        state_class=SensorStateClass.TOTAL_INCREASING,
        suggested_display_precision=PRECIPITATION_DISPLAY_PRECISION,
    ),
    ChmiSensorDescription(
        key="month_precipitation_chmi",
        name="Precipitation this month",
        translation_key="month_precipitation_chmi",
        value_fn=lambda coordinator, observation: observation.month_precipitation_chmi,
        any_required_elements=(ELEMENT_PRECIPITATION_10M, ELEMENT_PRECIPITATION_1H),
        native_unit_of_measurement=UnitOfPrecipitationDepth.MILLIMETERS,
        device_class=SensorDeviceClass.PRECIPITATION,
        state_class=SensorStateClass.MEASUREMENT,
        suggested_display_precision=PRECIPITATION_DISPLAY_PRECISION,
    ),
    ChmiSensorDescription(
        key="wind_speed",
        name="Wind speed",
        translation_key="wind_speed",
        value_fn=lambda coordinator, observation: observation.wind_speed,
        required_elements=(ELEMENT_WIND_SPEED,),
        native_unit_of_measurement=UnitOfSpeed.METERS_PER_SECOND,
        device_class=SensorDeviceClass.WIND_SPEED,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    ChmiSensorDescription(
        key="wind_speed_avg",
        name="Average wind speed",
        translation_key="wind_speed_avg",
        value_fn=lambda coordinator, observation: observation.wind_speed_avg,
        required_elements=(ELEMENT_WIND_SPEED_AVG,),
        native_unit_of_measurement=UnitOfSpeed.METERS_PER_SECOND,
        device_class=SensorDeviceClass.WIND_SPEED,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    ChmiSensorDescription(
        key="wind_gust",
        name="Wind gust",
        translation_key="wind_gust",
        value_fn=lambda coordinator, observation: observation.wind_gust,
        required_elements=(ELEMENT_WIND_GUST,),
        native_unit_of_measurement=UnitOfSpeed.METERS_PER_SECOND,
        device_class=SensorDeviceClass.WIND_SPEED,
        state_class=SensorStateClass.MEASUREMENT,
    ),
    ChmiSensorDescription(
        key="wind_direction",
        name="Wind direction",
        translation_key="wind_direction",
        value_fn=lambda coordinator, observation: observation.wind_direction,
        required_elements=(ELEMENT_WIND_DIRECTION,),
        native_unit_of_measurement=DEGREE,
        device_class=SensorDeviceClass.WIND_DIRECTION,
        state_class=SensorStateClass.MEASUREMENT_ANGLE,
    ),
    ChmiSensorDescription(
        key="wind_direction_avg",
        name="Average wind direction",
        translation_key="wind_direction_avg",
        value_fn=lambda coordinator, observation: observation.wind_direction_avg,
        required_elements=(ELEMENT_WIND_DIRECTION_AVG,),
        native_unit_of_measurement=DEGREE,
        device_class=SensorDeviceClass.WIND_DIRECTION,
        state_class=SensorStateClass.MEASUREMENT_ANGLE,
    ),
    ChmiSensorDescription(
        key="wind_gust_direction",
        name="Wind gust direction",
        translation_key="wind_gust_direction",
        value_fn=lambda coordinator, observation: observation.wind_gust_direction,
        required_elements=(ELEMENT_WIND_GUST_DIRECTION,),
        native_unit_of_measurement=DEGREE,
        device_class=SensorDeviceClass.WIND_DIRECTION,
        state_class=SensorStateClass.MEASUREMENT_ANGLE,
    ),
    ChmiSensorDescription(
        key="last_update",
        name="Observation time",
        translation_key="observation_time",
        value_fn=lambda coordinator, observation: observation.observed_at,
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
    ChmiSensorDescription(
        key="last_successful_poll",
        name="Last successful poll",
        translation_key="last_successful_poll",
        value_fn=lambda coordinator, observation: coordinator.last_successful_poll,
        device_class=SensorDeviceClass.TIMESTAMP,
        entity_category=EntityCategory.DIAGNOSTIC,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ChmiWeatherConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up CHMI Weather sensor entities."""
    runtime_data = entry.runtime_data
    descriptions = supported_sensor_descriptions(
        entry.data.get(CONF_SUPPORTED_ELEMENTS)
    )
    if not entry.options.get(CONF_DIAGNOSTIC_SENSORS, DEFAULT_DIAGNOSTIC_SENSORS):
        descriptions = tuple(
            description
            for description in descriptions
            if description.entity_category != EntityCategory.DIAGNOSTIC
        )

    async_add_entities(
        [
            ChmiSensorEntity(runtime_data.coordinator, entry, description)
            for description in descriptions
        ]
    )


def supported_sensor_descriptions(
    supported_elements: Collection[str] | None,
) -> tuple[ChmiSensorDescription, ...]:
    """Return sensors supported by station capabilities.

    Existing config entries may not have capability metadata yet. In that case,
    keep the old behavior and expose all known sensors.
    """
    if supported_elements is None:
        return SENSOR_DESCRIPTIONS

    normalized_supported_elements = {str(element) for element in supported_elements}
    return tuple(
        description
        for description in SENSOR_DESCRIPTIONS
        if (
            not description.required_elements
            or all(
                element in normalized_supported_elements
                for element in description.required_elements
            )
        )
        and (
            not description.any_required_elements
            or any(
                element in normalized_supported_elements
                for element in description.any_required_elements
            )
        )
    )


class ChmiSensorEntity(CoordinatorEntity[ChmiDataUpdateCoordinator], SensorEntity):
    """Sensor entity backed by the shared CHMI coordinator."""

    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(
        self,
        coordinator: ChmiDataUpdateCoordinator,
        entry: ChmiWeatherConfigEntry,
        description: ChmiSensorDescription,
    ) -> None:
        """Initialize the sensor."""
        super().__init__(coordinator)
        self.entity_description = description
        self._station_id = entry.data[CONF_STATION_ID]
        self._station_name = entry.data[CONF_STATION_NAME]
        self._attr_entity_category = description.entity_category
        self._attr_name = description.name
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
        return self.entity_description.value_fn(self.coordinator, self.observation)

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
