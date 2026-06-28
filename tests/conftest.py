"""Lightweight Home Assistant test stubs."""

from __future__ import annotations

import sys
from types import ModuleType, SimpleNamespace
from typing import Any


def _module(name: str) -> ModuleType:
    module = ModuleType(name)
    sys.modules[name] = module
    return module


homeassistant = _module("homeassistant")

config_entries = _module("homeassistant.config_entries")
homeassistant.config_entries = config_entries


class ConfigEntry(SimpleNamespace):
    """ConfigEntry stub."""

    @classmethod
    def __class_getitem__(cls, item: Any) -> type[ConfigEntry]:
        return cls


class ConfigFlow:
    """ConfigFlow stub."""

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__()

    async def async_set_unique_id(self, unique_id: str) -> None:
        self.unique_id = unique_id

    def _abort_if_unique_id_configured(self) -> None:
        return None

    def async_create_entry(
        self,
        *,
        title: str,
        data: dict[str, Any],
        options: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        return {
            "type": "create_entry",
            "title": title,
            "data": data,
            "options": options or {},
        }

    def async_show_form(
        self,
        *,
        step_id: str,
        data_schema: Any,
        errors: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        return {
            "type": "form",
            "step_id": step_id,
            "data_schema": data_schema,
            "errors": errors or {},
        }


class OptionsFlow:
    """OptionsFlow stub."""

    def async_create_entry(self, *, title: str, data: dict[str, Any]) -> dict[str, Any]:
        return {"type": "create_entry", "title": title, "data": data}

    def async_show_form(
        self,
        *,
        step_id: str,
        data_schema: Any,
        errors: dict[str, str] | None = None,
    ) -> dict[str, Any]:
        return {
            "type": "form",
            "step_id": step_id,
            "data_schema": data_schema,
            "errors": errors or {},
        }


config_entries.ConfigEntry = ConfigEntry
config_entries.ConfigFlow = ConfigFlow
config_entries.OptionsFlow = OptionsFlow

core = _module("homeassistant.core")


class HomeAssistant(SimpleNamespace):
    """HomeAssistant stub."""


def callback(func: Any) -> Any:
    """Return callback unchanged."""
    return func


core.HomeAssistant = HomeAssistant
core.callback = callback

const = _module("homeassistant.const")


class Platform:
    """Platform constants."""

    WEATHER = "weather"
    SENSOR = "sensor"


class UnitOfTemperature:
    """Temperature units."""

    CELSIUS = "°C"


class UnitOfPressure:
    """Pressure units."""

    HPA = "hPa"


class UnitOfSpeed:
    """Speed units."""

    METERS_PER_SECOND = "m/s"


class UnitOfPrecipitationDepth:
    """Precipitation depth units."""

    MILLIMETERS = "mm"


class EntityCategory:
    """Entity category constants."""

    DIAGNOSTIC = "diagnostic"


const.Platform = Platform
const.UnitOfTemperature = UnitOfTemperature
const.UnitOfPressure = UnitOfPressure
const.UnitOfSpeed = UnitOfSpeed
const.UnitOfPrecipitationDepth = UnitOfPrecipitationDepth
const.EntityCategory = EntityCategory
const.PERCENTAGE = "%"
const.DEGREE = "°"

helpers = _module("homeassistant.helpers")
homeassistant.helpers = helpers

aiohttp_client = _module("homeassistant.helpers.aiohttp_client")
helpers.aiohttp_client = aiohttp_client
aiohttp_client.async_get_clientsession = lambda hass: getattr(hass, "session", None)

entity_platform = _module("homeassistant.helpers.entity_platform")
helpers.entity_platform = entity_platform
entity_platform.AddEntitiesCallback = object

update_coordinator = _module("homeassistant.helpers.update_coordinator")
helpers.update_coordinator = update_coordinator


class UpdateFailed(Exception):
    """UpdateFailed stub."""


class DataUpdateCoordinator:
    """DataUpdateCoordinator stub."""

    def __init__(self, hass: Any, logger: Any, **kwargs: Any) -> None:
        self.hass = hass
        self.logger = logger
        self.data = None
        self.kwargs = kwargs

    @classmethod
    def __class_getitem__(cls, item: Any) -> type[DataUpdateCoordinator]:
        return cls

    async def async_config_entry_first_refresh(self) -> None:
        self.data = await self._async_update_data()


class CoordinatorEntity:
    """CoordinatorEntity stub."""

    def __init__(self, coordinator: Any) -> None:
        self.coordinator = coordinator

    @classmethod
    def __class_getitem__(cls, item: Any) -> type[CoordinatorEntity]:
        return cls


update_coordinator.UpdateFailed = UpdateFailed
update_coordinator.DataUpdateCoordinator = DataUpdateCoordinator
update_coordinator.CoordinatorEntity = CoordinatorEntity

components = _module("homeassistant.components")
homeassistant.components = components

weather = _module("homeassistant.components.weather")
components.weather = weather


class WeatherEntity:
    """WeatherEntity stub."""


weather.WeatherEntity = WeatherEntity

sensor = _module("homeassistant.components.sensor")
components.sensor = sensor


class SensorEntity:
    """SensorEntity stub."""


class SensorEntityDescription:
    """SensorEntityDescription stub."""

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__()

    def __init__(self, **kwargs: Any) -> None:
        self.device_class = None
        self.last_reset = None
        self.native_unit_of_measurement = None
        self.options = None
        self.state_class = None
        self.suggested_display_precision = None
        self.suggested_unit_of_measurement = None
        self.unit_of_measurement = None
        for key, value in kwargs.items():
            setattr(self, key, value)


class SensorDeviceClass:
    """Sensor device classes."""

    TEMPERATURE = "temperature"
    HUMIDITY = "humidity"
    PRESSURE = "pressure"
    PRECIPITATION = "precipitation"
    WIND_SPEED = "wind_speed"
    WIND_DIRECTION = "wind_direction"
    TIMESTAMP = "timestamp"


class SensorStateClass:
    """Sensor state classes."""

    MEASUREMENT = "measurement"
    MEASUREMENT_ANGLE = "measurement_angle"
    TOTAL_INCREASING = "total_increasing"


sensor.SensorEntity = SensorEntity
sensor.SensorEntityDescription = SensorEntityDescription
sensor.SensorDeviceClass = SensorDeviceClass
sensor.SensorStateClass = SensorStateClass

voluptuous = _module("voluptuous")


class Marker(str):
    """Voluptuous marker stub preserving defaults."""

    def __new__(cls, key: str, default: Any = None) -> Marker:
        """Create a marker."""
        marker = str.__new__(cls, key)
        marker.default = default
        return marker


class Schema:
    """Voluptuous Schema stub."""

    def __init__(self, schema: Any) -> None:
        self.schema = schema

    def __call__(self, value: Any) -> Any:
        return value


def _marker(key: str, default: Any = None) -> str:
    return Marker(key, default)


def _identity(*args: Any, **kwargs: Any) -> Any:
    if args:
        return args[0]
    return lambda value: value


voluptuous.Schema = Schema
voluptuous.Required = _marker
voluptuous.Optional = _marker
voluptuous.All = lambda *args, **kwargs: args[0] if args else (lambda value: value)
voluptuous.Coerce = lambda value_type: value_type
voluptuous.Range = _identity
voluptuous.In = _identity
