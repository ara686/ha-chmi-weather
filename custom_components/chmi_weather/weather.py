"""Weather platform for CHMI Weather."""

from __future__ import annotations

from homeassistant.components.weather import WeatherEntity
from homeassistant.const import (
    UnitOfPrecipitationDepth,
    UnitOfPressure,
    UnitOfSpeed,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import ChmiWeatherConfigEntry
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
    entry: ChmiWeatherConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up CHMI Weather weather entities."""
    runtime_data = entry.runtime_data
    async_add_entities([ChmiWeatherEntity(runtime_data.coordinator, entry)])


class ChmiWeatherEntity(CoordinatorEntity[ChmiDataUpdateCoordinator], WeatherEntity):
    """Weather entity for one CHMI OpenData station."""

    _attr_attribution = ATTRIBUTION
    _attr_has_entity_name = True
    _attr_name = None
    _attr_should_poll = False

    def __init__(
        self,
        coordinator: ChmiDataUpdateCoordinator,
        entry: ChmiWeatherConfigEntry,
    ) -> None:
        """Initialize the weather entity."""
        super().__init__(coordinator)
        self._entry = entry
        self._station_id = entry.data[CONF_STATION_ID]
        self._station_name = entry.data[CONF_STATION_NAME]
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
    """Return a best-effort HA condition from measured station elements."""
    present_weather = _condition_from_present_weather(
        _int_code(observation.present_weather_code)
    )
    if present_weather is not None:
        return present_weather

    if observation.precipitation_10m is not None and observation.precipitation_10m > 0:
        return "rainy"

    if _is_low_visibility(observation.visibility_code) or _is_near_saturation(
        observation
    ):
        return "fog"

    cloud_condition = _condition_from_cloud_coverage(
        _int_code(observation.cloud_coverage)
    )
    if cloud_condition is not None:
        return cloud_condition

    past_weather = _condition_from_past_weather(
        _int_code(observation.past_weather_code_1)
    ) or _condition_from_past_weather(_int_code(observation.past_weather_code_2))
    if past_weather is not None:
        return past_weather

    return "partlycloudy"


def _int_code(value: float | None) -> int | None:
    if value is None:
        return None

    code = int(value)
    if value != code:
        return None
    return code


def _condition_from_present_weather(code: int | None) -> str | None:
    if code is None:
        return None
    if code in {4, 5, 10, 11, 12, 28} or 40 <= code <= 49:
        return "fog"
    if code in {13, 17}:
        return "lightning"
    if code == 18:
        return "windy"
    if 30 <= code <= 39:
        return "windy"
    if code in {20, 21, 24, 25} or 50 <= code <= 59:
        return "pouring" if code in {58, 59} else "rainy"
    if 60 <= code <= 67:
        return "pouring" if code in {63, 64, 65, 66, 67} else "rainy"
    if code in {22, 26} or 70 <= code <= 79 or 85 <= code <= 86:
        return "snowy"
    if code in {23, 68, 69, 83, 84}:
        return "snowy-rainy"
    if 80 <= code <= 82:
        return "pouring" if code == 82 else "rainy"
    if code in {27} or 87 <= code <= 90:
        return "hail"
    if code == 29 or 91 <= code <= 99:
        return "lightning-rainy"
    return None


def _condition_from_cloud_coverage(code: int | None) -> str | None:
    if code is None:
        return None
    if code <= 0:
        return "sunny"
    if code <= 5:
        return "partlycloudy"
    return "cloudy"


def _condition_from_past_weather(code: int | None) -> str | None:
    if code is None:
        return None
    if code == 4:
        return "fog"
    if code in {5, 6, 8}:
        return "rainy"
    if code == 7:
        return "snowy"
    if code == 9:
        return "lightning-rainy"
    return None


def _is_low_visibility(visibility_code: float | None) -> bool:
    code = _int_code(visibility_code)
    return code is not None and code <= 10


def _is_near_saturation(observation: ChmiObservation) -> bool:
    return (
        observation.temperature is not None
        and observation.dew_point is not None
        and observation.humidity is not None
        and observation.humidity >= 95
        and abs(observation.temperature - observation.dew_point) <= 1
    )
