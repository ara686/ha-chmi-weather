"""Constants for the CHMI Weather integration."""

DOMAIN = "chmi_weather"
NAME = "CHMI Weather"

MANUFACTURER = "\u010cHM\u00da OpenData"
MODEL = "OpenData weather station"
ATTRIBUTION = (
    "Data source: Czech Hydrometeorological Institute (CHMI) OpenData, CC BY 4.0"
)

DEFAULT_STATION_NAME = "Dobrichovice"
DEFAULT_STATION_ID = "0-203-0-11521"
DEFAULT_LATITUDE = 49.9335
DEFAULT_LONGITUDE = 14.2759

DEFAULT_UPDATE_INTERVAL_MINUTES = 10
MAX_UPDATE_INTERVAL_MINUTES = 60
DEFAULT_OBSERVATION_INTERVAL_MINUTES = 10
DEFAULT_DIAGNOSTIC_SENSORS = True
DEFAULT_STATION_SELECTION_LIMIT = 10

CONF_STATION_ID = "station_id"
CONF_STATION_NAME = "station_name"
CONF_SUPPORTED_ELEMENTS = "supported_elements"
CONF_SUPPORTED_ELEMENTS_BY_INTERVAL = "supported_elements_by_interval"
CONF_OBSERVATION_INTERVAL_MINUTES = "observation_interval_minutes"
CONF_LATITUDE = "latitude"
CONF_LONGITUDE = "longitude"
CONF_UPDATE_INTERVAL = "update_interval_minutes"
CONF_DIAGNOSTIC_SENSORS = "diagnostic_sensors"

CHMI_BASE_URL = "https://opendata.chmi.cz/meteorology/climate/now/data"
CHMI_METADATA_BASE_URL = "https://opendata.chmi.cz/meteorology/climate/now/metadata"
CHMI_RECENT_DAILY_BASE_URL = (
    "https://opendata.chmi.cz/meteorology/climate/recent/data/daily"
)

ELEMENT_TEMPERATURE = "T"
ELEMENT_TEMPERATURE_MAX_10M = "TMA"
ELEMENT_TEMPERATURE_MIN_10M = "TMI"
ELEMENT_APPARENT_TEMPERATURE = "TPM"
ELEMENT_HUMIDITY = "H"
ELEMENT_PRESSURE = "P"
ELEMENT_PRECIPITATION_10M = "SRA10M"
ELEMENT_PRECIPITATION_1H = "SRA1H"
ELEMENT_WIND_SPEED = "F"
ELEMENT_WIND_SPEED_AVG = "Fprum"
ELEMENT_WIND_GUST = "Fmax"
ELEMENT_WIND_DIRECTION = "D"
ELEMENT_WIND_DIRECTION_AVG = "Dprum"
ELEMENT_WIND_GUST_DIRECTION = "Dmax"
ELEMENT_DAILY_PRECIPITATION = "SRA"
ELEMENT_CLOUD_COVERAGE = "N"
ELEMENT_DEW_POINT = "Td"
ELEMENT_PRESENT_WEATHER = "ww"
ELEMENT_PAST_WEATHER_1 = "W1"
ELEMENT_PAST_WEATHER_2 = "W2"
ELEMENT_VISIBILITY = "VV"

OBSERVATION_VALUE_FIELDS = (
    "temperature",
    "temperature_max_10m",
    "temperature_min_10m",
    "apparent_temperature",
    "humidity",
    "pressure",
    "precipitation_10m",
    "precipitation_1h",
    "wind_speed",
    "wind_speed_avg",
    "wind_gust",
    "wind_direction",
    "wind_direction_avg",
    "wind_gust_direction",
    "cloud_coverage",
    "dew_point",
    "visibility_code",
    "present_weather_code",
    "past_weather_code_1",
    "past_weather_code_2",
)

CHMI_ELEMENT_BY_FIELD = {
    "temperature": ELEMENT_TEMPERATURE,
    "temperature_max_10m": ELEMENT_TEMPERATURE_MAX_10M,
    "temperature_min_10m": ELEMENT_TEMPERATURE_MIN_10M,
    "apparent_temperature": ELEMENT_APPARENT_TEMPERATURE,
    "humidity": ELEMENT_HUMIDITY,
    "pressure": ELEMENT_PRESSURE,
    "precipitation_10m": ELEMENT_PRECIPITATION_10M,
    "precipitation_1h": ELEMENT_PRECIPITATION_1H,
    "wind_speed": ELEMENT_WIND_SPEED,
    "wind_speed_avg": ELEMENT_WIND_SPEED_AVG,
    "wind_gust": ELEMENT_WIND_GUST,
    "wind_direction": ELEMENT_WIND_DIRECTION,
    "wind_direction_avg": ELEMENT_WIND_DIRECTION_AVG,
    "wind_gust_direction": ELEMENT_WIND_GUST_DIRECTION,
    "cloud_coverage": ELEMENT_CLOUD_COVERAGE,
    "dew_point": ELEMENT_DEW_POINT,
    "visibility_code": ELEMENT_VISIBILITY,
    "present_weather_code": ELEMENT_PRESENT_WEATHER,
    "past_weather_code_1": ELEMENT_PAST_WEATHER_1,
    "past_weather_code_2": ELEMENT_PAST_WEATHER_2,
}

WEATHER_CONDITION_ELEMENTS = (
    ELEMENT_CLOUD_COVERAGE,
    ELEMENT_DEW_POINT,
    ELEMENT_VISIBILITY,
    ELEMENT_PRESENT_WEATHER,
    ELEMENT_PAST_WEATHER_1,
    ELEMENT_PAST_WEATHER_2,
)

CHMI_QUALITY_DESCRIPTIONS = {
    0: "Good",
    1: "Suspect",
    2: "Poor",
    3: "Estimated",
    4: "Missing",
    5: "Unknown",
}
