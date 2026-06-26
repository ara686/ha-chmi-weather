"""Constants for the CHMI Weather integration."""

DOMAIN = "chmi_weather"
NAME = "CHMI Weather"

MANUFACTURER = "\u010cHM\u00da"
MODEL = "OpenData weather station"
ATTRIBUTION = "Data provided by CHMI OpenData"

DEFAULT_STATION_NAME = "Dobrichovice"
DEFAULT_STATION_ID = "0-203-0-11521"
DEFAULT_LATITUDE = 49.9335
DEFAULT_LONGITUDE = 14.2759

DEFAULT_UPDATE_INTERVAL_MINUTES = 10
DEFAULT_DIAGNOSTIC_SENSORS = True
DEFAULT_FORECAST_SOURCE = "none"

CONF_STATION_ID = "station_id"
CONF_STATION_NAME = "station_name"
CONF_LATITUDE = "latitude"
CONF_LONGITUDE = "longitude"
CONF_UPDATE_INTERVAL = "update_interval_minutes"
CONF_DIAGNOSTIC_SENSORS = "diagnostic_sensors"
CONF_FORECAST_SOURCE = "forecast_source"

CHMI_BASE_URL = "https://opendata.chmi.cz/meteorology/climate/now/data"

ELEMENT_TEMPERATURE = "T"
ELEMENT_HUMIDITY = "H"
ELEMENT_PRESSURE = "P"
ELEMENT_PRECIPITATION_10M = "SRA10M"
ELEMENT_WIND_SPEED = "F"
ELEMENT_WIND_GUST = "Fmax"
ELEMENT_WIND_DIRECTION = "D"

OBSERVATION_VALUE_FIELDS = (
    "temperature",
    "humidity",
    "pressure",
    "precipitation_10m",
    "wind_speed",
    "wind_gust",
    "wind_direction",
)

CHMI_ELEMENT_BY_FIELD = {
    "temperature": ELEMENT_TEMPERATURE,
    "humidity": ELEMENT_HUMIDITY,
    "pressure": ELEMENT_PRESSURE,
    "precipitation_10m": ELEMENT_PRECIPITATION_10M,
    "wind_speed": ELEMENT_WIND_SPEED,
    "wind_gust": ELEMENT_WIND_GUST,
    "wind_direction": ELEMENT_WIND_DIRECTION,
}
