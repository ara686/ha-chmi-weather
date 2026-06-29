"""Async CHMI OpenData client and parser."""

from __future__ import annotations

import asyncio
import json
import math
import re
from collections.abc import Mapping, Sequence
from datetime import UTC, date, datetime, timedelta, tzinfo
from typing import Any

from .const import (
    CHMI_BASE_URL,
    CHMI_ELEMENT_BY_FIELD,
    CHMI_METADATA_BASE_URL,
    DEFAULT_OBSERVATION_INTERVAL_MINUTES,
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
    OBSERVATION_VALUE_FIELDS,
)
from .models import (
    ChmiNearestStation,
    ChmiObservation,
    ChmiPrecipitationSample,
    ChmiStationCapabilities,
    ChmiStationMetadata,
)

DEFAULT_TIMEOUT_SECONDS = 20
STATION_ID_PATTERN = re.compile(r"^[A-Za-z0-9-]+$")
OBSERVATION_TYPE_PATTERN = re.compile(r"^(\d+)([DHM])$")


class ChmiApiError(Exception):
    """Base class for CHMI API errors."""


class ChmiApiConnectionError(ChmiApiError):
    """Raised when the CHMI endpoint cannot be reached."""


class ChmiApiNotFoundError(ChmiApiError):
    """Raised when a CHMI daily file is not available."""


class ChmiApiDataError(ChmiApiError):
    """Raised when CHMI data cannot be parsed into a usable observation."""


class ChmiApiClient:
    """Minimal async client for CHMI OpenData current station observations."""

    def __init__(
        self,
        session: Any,
        *,
        base_url: str = CHMI_BASE_URL,
        metadata_base_url: str = CHMI_METADATA_BASE_URL,
        timeout: int = DEFAULT_TIMEOUT_SECONDS,
    ) -> None:
        """Initialize the client."""
        self._session = session
        self._base_url = base_url.rstrip("/")
        self._metadata_base_url = metadata_base_url.rstrip("/")
        self._timeout = timeout

    async def async_get_current_observations(
        self,
        station_id: str,
        *,
        interval_minutes: int = DEFAULT_OBSERVATION_INTERVAL_MINUTES,
        precipitation_timezone: tzinfo | None = None,
        precipitation_1h_interval_minutes: int | None = None,
    ) -> ChmiObservation:
        """Return current observations for a station, falling back to yesterday."""
        today = datetime.now(UTC).date()
        last_error: ChmiApiError | None = None
        observations: list[ChmiObservation] = []

        for day in (today, today - timedelta(days=1)):
            try:
                observation = await self.async_get_current_observations_for_date(
                    station_id,
                    day,
                    interval_minutes=interval_minutes,
                )
            except (ChmiApiNotFoundError, ChmiApiDataError) as err:
                last_error = err
                continue

            if precipitation_timezone is None:
                observations.append(observation)
                break
            observations.append(observation)

        if observations:
            observation = observations[0]
            if precipitation_timezone is not None:
                observation = _with_precipitation_statistics(
                    observation,
                    observations,
                    precipitation_timezone=precipitation_timezone,
                    precipitation_date=datetime.now(precipitation_timezone).date(),
                )

            if (
                precipitation_1h_interval_minutes is not None
                and precipitation_1h_interval_minutes != interval_minutes
            ):
                hourly_observation = await self._async_get_optional_current_observation(
                    station_id,
                    today,
                    interval_minutes=precipitation_1h_interval_minutes,
                )
                if (
                    hourly_observation is not None
                    and hourly_observation.precipitation_1h is not None
                ):
                    _apply_observed_precipitation_1h(observation, hourly_observation)
            return observation

        raise last_error or ChmiApiDataError("No usable CHMI observations found")

    async def _async_get_optional_current_observation(
        self,
        station_id: str,
        today: date,
        *,
        interval_minutes: int,
    ) -> ChmiObservation | None:
        """Return optional companion observations without failing the main update."""
        for day in (today, today - timedelta(days=1)):
            try:
                return await self.async_get_current_observations_for_date(
                    station_id,
                    day,
                    interval_minutes=interval_minutes,
                )
            except ChmiApiError:
                continue
        return None

    async def async_get_current_observations_for_date(
        self,
        station_id: str,
        day: date,
        *,
        interval_minutes: int = DEFAULT_OBSERVATION_INTERVAL_MINUTES,
    ) -> ChmiObservation:
        """Return observations for one UTC date."""
        url = self._build_current_url(
            station_id,
            day,
            interval_minutes=interval_minutes,
        )
        payload = await self._async_get_json(url)
        return parse_current_observations(payload, station_id)

    def _build_current_url(
        self,
        station_id: str,
        day: date,
        *,
        interval_minutes: int = DEFAULT_OBSERVATION_INTERVAL_MINUTES,
    ) -> str:
        """Build a CHMI current observation URL."""
        normalized_station_id = _normalize_station_id(station_id)
        file_prefix = _data_file_prefix(interval_minutes)
        return (
            f"{self._base_url}/{file_prefix}-{normalized_station_id}-{day:%Y%m%d}.json"
        )

    async def async_get_station_metadata(
        self,
        station_id: str,
    ) -> ChmiStationMetadata:
        """Return station metadata, falling back to yesterday's metadata file."""
        today = datetime.now(UTC).date()
        last_error: ChmiApiError | None = None

        for day in (today, today - timedelta(days=1)):
            try:
                return await self.async_get_station_metadata_for_date(station_id, day)
            except (ChmiApiNotFoundError, ChmiApiDataError) as err:
                last_error = err

        raise last_error or ChmiApiDataError("No usable CHMI station metadata found")

    async def async_get_station_metadata_for_date(
        self,
        station_id: str,
        day: date,
    ) -> ChmiStationMetadata:
        """Return station metadata from one UTC date."""
        url = self._build_station_metadata_url(day)
        payload = await self._async_get_json(url)
        return parse_station_metadata(payload, station_id)

    def _build_station_metadata_url(self, day: date) -> str:
        """Build a CHMI station metadata URL."""
        return f"{self._metadata_base_url}/meta1-{day:%Y%m%d}.json"

    async def async_get_all_station_metadata(self) -> tuple[ChmiStationMetadata, ...]:
        """Return all stations from CHMI metadata, falling back to yesterday."""
        today = datetime.now(UTC).date()
        last_error: ChmiApiError | None = None

        for day in (today, today - timedelta(days=1)):
            try:
                return await self.async_get_all_station_metadata_for_date(day)
            except (ChmiApiNotFoundError, ChmiApiDataError) as err:
                last_error = err

        raise last_error or ChmiApiDataError("No usable CHMI station metadata found")

    async def async_get_all_station_metadata_for_date(
        self,
        day: date,
    ) -> tuple[ChmiStationMetadata, ...]:
        """Return all station metadata rows from one UTC date."""
        url = self._build_station_metadata_url(day)
        payload = await self._async_get_json(url)
        return parse_station_metadata_list(payload)

    async def async_get_nearest_stations(
        self,
        latitude: float,
        longitude: float,
        *,
        limit: int,
    ) -> tuple[ChmiNearestStation, ...]:
        """Return nearest stations for a GPS coordinate."""
        stations = await self.async_get_all_station_metadata()
        return nearest_stations(stations, latitude, longitude, limit=limit)

    async def async_get_station_capabilities(
        self,
        station_id: str,
    ) -> ChmiStationCapabilities:
        """Return measurable elements and best observation interval for a station."""
        today = datetime.now(UTC).date()
        last_error: ChmiApiError | None = None

        for day in (today, today - timedelta(days=1)):
            try:
                return await self.async_get_station_capabilities_for_date(
                    station_id,
                    day,
                )
            except (ChmiApiNotFoundError, ChmiApiDataError) as err:
                last_error = err

        raise last_error or ChmiApiDataError(
            "No usable CHMI station capabilities found"
        )

    async def async_get_station_capabilities_for_date(
        self,
        station_id: str,
        day: date,
    ) -> ChmiStationCapabilities:
        """Return measurable elements from one UTC date."""
        url = self._build_station_capabilities_url(day)
        payload = await self._async_get_json(url)
        return parse_station_capabilities(payload, station_id)

    def _build_station_capabilities_url(self, day: date) -> str:
        """Build a CHMI station capability metadata URL."""
        return f"{self._metadata_base_url}/meta2-{day:%Y%m%d}.json"

    async def async_get_flag_descriptions(self) -> dict[str, dict[str, str]]:
        """Return CHMI flag descriptions from current metadata."""
        today = datetime.now(UTC).date()
        last_error: ChmiApiError | None = None

        for day in (today, today - timedelta(days=1)):
            try:
                return await self.async_get_flag_descriptions_for_date(day)
            except (ChmiApiNotFoundError, ChmiApiDataError) as err:
                last_error = err

        raise last_error or ChmiApiDataError("No usable CHMI flag metadata found")

    async def async_get_flag_descriptions_for_date(
        self,
        day: date,
    ) -> dict[str, dict[str, str]]:
        """Return CHMI flag descriptions from one UTC date."""
        url = self._build_flag_descriptions_url(day)
        payload = await self._async_get_json(url)
        return parse_flag_descriptions(payload)

    def _build_flag_descriptions_url(self, day: date) -> str:
        """Build a CHMI flag description metadata URL."""
        return f"{self._metadata_base_url}/meta3-{day:%Y%m%d}.json"

    async def async_get_quality_descriptions(self) -> dict[int, str]:
        """Return CHMI quality-code descriptions from current metadata."""
        today = datetime.now(UTC).date()
        last_error: ChmiApiError | None = None

        for day in (today, today - timedelta(days=1)):
            try:
                return await self.async_get_quality_descriptions_for_date(day)
            except (ChmiApiNotFoundError, ChmiApiDataError) as err:
                last_error = err

        raise last_error or ChmiApiDataError("No usable CHMI quality metadata found")

    async def async_get_quality_descriptions_for_date(
        self,
        day: date,
    ) -> dict[int, str]:
        """Return CHMI quality-code descriptions from one UTC date."""
        url = self._build_quality_descriptions_url(day)
        payload = await self._async_get_json(url)
        return parse_quality_descriptions(payload)

    def _build_quality_descriptions_url(self, day: date) -> str:
        """Build a CHMI quality description metadata URL."""
        return f"{self._metadata_base_url}/meta4-{day:%Y%m%d}.json"

    async def _async_get_json(self, url: str) -> Mapping[str, Any]:
        """Fetch a JSON document."""
        try:
            async with asyncio.timeout(self._timeout):
                async with self._session.get(url) as response:
                    status = getattr(response, "status", None)
                    if status == 404:
                        raise ChmiApiNotFoundError(f"CHMI file not found: {url}")
                    if status is not None and status >= 400:
                        raise ChmiApiConnectionError(
                            f"CHMI endpoint returned HTTP {status}"
                        )

                    try:
                        payload = await response.json(content_type=None)
                    except Exception as err:
                        text = await response.text()
                        if not text.strip():
                            raise ChmiApiDataError("CHMI response is empty") from err
                        payload = json.loads(text)
        except ChmiApiError:
            raise
        except TimeoutError as err:
            raise ChmiApiConnectionError("Timed out while reading CHMI data") from err
        except Exception as err:
            raise ChmiApiConnectionError("Failed to read CHMI data") from err

        if not isinstance(payload, Mapping):
            raise ChmiApiDataError("CHMI response is not a JSON object")
        return payload


def parse_current_observations(
    payload: Mapping[str, Any],
    station_id: str,
) -> ChmiObservation:
    """Parse a CHMI DataCollection payload into the latest valid observation."""
    normalized_station_id = _normalize_station_id(station_id)
    values = _extract_values(payload)
    if not values:
        raise ChmiApiDataError("CHMI response does not contain observation rows")

    indices = _extract_header_indices(payload)
    selected: dict[str, tuple[datetime | None, float, str | None, float | None]] = {}
    available_elements: set[str] = set()
    precipitation_by_timestamp: dict[datetime, float] = {}

    for row in values:
        if not _is_row(row):
            continue

        station = _row_value(row, indices, "STATION", 0)
        if str(station).strip() != normalized_station_id:
            continue

        element = _row_value(row, indices, "ELEMENT", 1)
        if element is None:
            continue

        element_code = str(element).strip()
        available_elements.add(element_code)
        if element_code not in CHMI_ELEMENT_BY_FIELD.values():
            continue

        value = _as_float(_row_value(row, indices, "VAL", 3))
        if value is None:
            continue

        observed_at = _parse_datetime(_row_value(row, indices, "DT", 2))
        flag = _as_str(_row_value(row, indices, "FLAG", 4))
        quality = _as_float(_row_value(row, indices, "QUALITY", 5))
        if element_code == ELEMENT_PRECIPITATION_10M and observed_at is not None:
            precipitation_by_timestamp[observed_at] = value

        current = selected.get(element_code)
        if current is None or _is_newer_or_equal(observed_at, current[0]):
            selected[element_code] = (observed_at, value, flag, quality)

    precipitation_samples = _precipitation_samples(precipitation_by_timestamp)
    precipitation_1h = _selected_value(selected, ELEMENT_PRECIPITATION_1H)
    if precipitation_1h is None:
        precipitation_1h = _precipitation_last_hour(precipitation_samples)

    observation = ChmiObservation(
        station_id=normalized_station_id,
        observed_at=_latest_observed_at(selected),
        temperature=_selected_value(selected, ELEMENT_TEMPERATURE),
        temperature_max_10m=_selected_value(selected, ELEMENT_TEMPERATURE_MAX_10M),
        temperature_min_10m=_selected_value(selected, ELEMENT_TEMPERATURE_MIN_10M),
        apparent_temperature=_selected_value(selected, ELEMENT_APPARENT_TEMPERATURE),
        humidity=_selected_value(selected, ELEMENT_HUMIDITY),
        pressure=_selected_value(selected, ELEMENT_PRESSURE),
        precipitation_10m=_selected_value(selected, ELEMENT_PRECIPITATION_10M),
        wind_speed=_selected_value(selected, ELEMENT_WIND_SPEED),
        wind_speed_avg=_selected_value(selected, ELEMENT_WIND_SPEED_AVG),
        wind_gust=_selected_value(selected, ELEMENT_WIND_GUST),
        wind_direction=_selected_value(selected, ELEMENT_WIND_DIRECTION),
        wind_direction_avg=_selected_value(selected, ELEMENT_WIND_DIRECTION_AVG),
        wind_gust_direction=_selected_value(selected, ELEMENT_WIND_GUST_DIRECTION),
        precipitation_1h=precipitation_1h,
        precipitation_today=_precipitation_total(precipitation_samples),
        precipitation_samples=precipitation_samples,
        available_elements=tuple(sorted(available_elements)),
        quality_by_element=_quality_by_element(selected),
        flag_by_element=_flag_by_element(selected),
    )

    if not has_usable_observation(observation):
        raise ChmiApiDataError("CHMI response does not contain usable observations")

    return observation


def parse_station_metadata(
    payload: Mapping[str, Any],
    station_id: str,
) -> ChmiStationMetadata:
    """Parse CHMI meta1 station metadata for one station."""
    normalized_station_id = _normalize_station_id(station_id)
    for station in parse_station_metadata_list(payload):
        if station.station_id == normalized_station_id:
            return station

    raise ChmiApiDataError("CHMI metadata does not contain the requested station")


def parse_station_metadata_list(
    payload: Mapping[str, Any],
) -> tuple[ChmiStationMetadata, ...]:
    """Parse CHMI meta1 station metadata rows."""
    values = _extract_values(payload)
    if not values:
        raise ChmiApiDataError("CHMI metadata response does not contain station rows")

    indices = _extract_header_indices(payload)
    stations: list[ChmiStationMetadata] = []

    for row in values:
        if not _is_row(row):
            continue

        metadata = _parse_station_metadata_row(row, indices)
        if metadata is None:
            continue
        stations.append(metadata)

    if not stations:
        raise ChmiApiDataError("CHMI metadata does not contain usable stations")

    return tuple(stations)


def nearest_stations(
    stations: Sequence[ChmiStationMetadata],
    latitude: float,
    longitude: float,
    *,
    limit: int,
) -> tuple[ChmiNearestStation, ...]:
    """Return stations sorted by distance from GPS coordinates."""
    if limit <= 0:
        return ()

    nearest = (
        ChmiNearestStation(
            station=station,
            distance_km=_distance_km(
                latitude,
                longitude,
                station.latitude,
                station.longitude,
            ),
        )
        for station in stations
    )
    return tuple(sorted(nearest, key=lambda item: item.distance_km)[:limit])


def parse_station_capabilities(
    payload: Mapping[str, Any],
    station_id: str,
    *,
    observation_type: str | None = None,
) -> ChmiStationCapabilities:
    """Parse CHMI meta2 measurable element metadata for one station."""
    values = _extract_values(payload)
    if not values:
        raise ChmiApiDataError("CHMI capability metadata does not contain rows")

    indices = _extract_header_indices(payload)
    normalized_station_id = _normalize_station_id(station_id)
    normalized_observation_type = (
        observation_type.strip().upper() if observation_type else None
    )
    selected_observation_type: str | None = None
    selected_interval_minutes: int | None = None
    supported_elements: set[str] = set()
    supported_elements_by_interval: dict[int, set[str]] = {}
    station_rows: list[Sequence[Any]] = []

    for row in values:
        if not _is_row(row):
            continue

        row_station_id = _row_value(row, indices, "WSI", 1)
        if str(row_station_id).strip() != normalized_station_id:
            continue

        station_rows.append(row)

    if not station_rows:
        raise ChmiApiDataError(
            "CHMI capability metadata does not contain supported elements"
        )

    for row in station_rows:
        row_interval_minutes = _observation_type_interval_minutes(
            _row_observation_type(row, indices)
        )
        element = _as_str(_row_value(row, indices, "EG_EL_ABBREVIATION", 2))
        if row_interval_minutes is None or element is None:
            continue
        supported_elements_by_interval.setdefault(row_interval_minutes, set()).add(
            element
        )

    if normalized_observation_type is not None:
        selected_observation_type = normalized_observation_type
        selected_interval_minutes = _observation_type_interval_minutes(
            selected_observation_type
        )
    else:
        for row in station_rows:
            row_observation_type = _row_observation_type(row, indices)
            row_interval_minutes = _observation_type_interval_minutes(
                row_observation_type
            )
            if row_observation_type is None or row_interval_minutes is None:
                continue
            if (
                selected_interval_minutes is None
                or row_interval_minutes < selected_interval_minutes
            ):
                selected_observation_type = row_observation_type
                selected_interval_minutes = row_interval_minutes

    if selected_observation_type is None or selected_interval_minutes is None:
        raise ChmiApiDataError("CHMI capability metadata has no usable interval")

    for row in station_rows:
        row_observation_type = _row_observation_type(row, indices)
        if row_observation_type != selected_observation_type:
            continue

        element = _as_str(_row_value(row, indices, "EG_EL_ABBREVIATION", 2))
        if element is not None:
            supported_elements.add(element)

    if not supported_elements:
        raise ChmiApiDataError(
            "CHMI capability metadata does not contain supported elements"
        )

    return ChmiStationCapabilities(
        station_id=normalized_station_id,
        supported_elements=tuple(sorted(supported_elements)),
        observation_type=selected_observation_type,
        observation_interval_minutes=selected_interval_minutes,
        supported_elements_by_interval={
            interval: tuple(sorted(elements))
            for interval, elements in sorted(supported_elements_by_interval.items())
        },
    )


def parse_flag_descriptions(payload: Mapping[str, Any]) -> dict[str, dict[str, str]]:
    """Parse CHMI meta3 flag descriptions."""
    values = _extract_values(payload)
    if not values:
        raise ChmiApiDataError("CHMI flag metadata does not contain rows")

    indices = _extract_header_indices(payload)
    descriptions: dict[str, dict[str, str]] = {}

    for row in values:
        if not _is_row(row):
            continue

        element = _as_str(_row_value(row, indices, "EL_ABBREVIATION", 0))
        flag = _as_str(_row_value(row, indices, "FLAG", 1))
        description = _as_str(_row_value(row, indices, "DESCRIPTION", 2))
        if element is None or flag is None or description is None:
            continue

        descriptions.setdefault(element, {})[flag] = description

    if not descriptions:
        raise ChmiApiDataError("CHMI flag metadata has no usable descriptions")
    return descriptions


def parse_quality_descriptions(payload: Mapping[str, Any]) -> dict[int, str]:
    """Parse CHMI meta4 quality-code descriptions."""
    values = _extract_values(payload)
    if not values:
        raise ChmiApiDataError("CHMI quality metadata does not contain rows")

    indices = _extract_header_indices(payload)
    descriptions: dict[int, str] = {}

    for row in values:
        if not _is_row(row):
            continue

        code = _as_int(_row_value(row, indices, "FLAG2", 0))
        description = _as_str(_row_value(row, indices, "DESCRIPTION", 1))
        if code is None or description is None:
            continue
        descriptions[code] = description

    if not descriptions:
        raise ChmiApiDataError("CHMI quality metadata has no usable descriptions")
    return descriptions


def _normalize_station_id(station_id: str) -> str:
    normalized = station_id.strip()
    if not normalized or STATION_ID_PATTERN.fullmatch(normalized) is None:
        raise ChmiApiDataError("Invalid CHMI station ID")
    return normalized


def _observation_type_interval_minutes(value: str | None) -> int | None:
    if value is None:
        return None

    match = OBSERVATION_TYPE_PATTERN.fullmatch(value.strip().upper())
    if match is None:
        return None

    amount = int(match.group(1))
    unit = match.group(2)
    if amount <= 0:
        return None
    if unit == "M":
        return amount
    if unit == "H":
        return amount * 60
    return amount * 24 * 60


def _data_file_prefix(interval_minutes: int) -> str:
    if interval_minutes <= 0:
        raise ChmiApiDataError("Invalid CHMI observation interval")
    if interval_minutes % (24 * 60) == 0:
        return f"{interval_minutes // (24 * 60)}d"
    if interval_minutes % 60 == 0:
        return f"{interval_minutes // 60}h"
    return f"{interval_minutes}m"


def _row_observation_type(
    row: Sequence[Any],
    indices: Mapping[str, int],
) -> str | None:
    observation_type = _as_str(_row_value(row, indices, "OBS_TYPE", 0))
    if observation_type is not None:
        return observation_type.upper()

    schedule = _as_str(_row_value(row, indices, "SCHEDULE", 6))
    if schedule is not None:
        return schedule.upper()
    return None


def has_usable_observation(observation: ChmiObservation) -> bool:
    """Return whether at least one weather value is available."""
    return any(
        getattr(observation, field) is not None for field in OBSERVATION_VALUE_FIELDS
    )


def _extract_values(payload: Mapping[str, Any]) -> Sequence[Any]:
    data = payload.get("data")
    if isinstance(data, Mapping):
        nested = data.get("data")
        if isinstance(nested, Mapping) and isinstance(nested.get("values"), Sequence):
            return nested["values"]
        if isinstance(data.get("values"), Sequence):
            return data["values"]
    if isinstance(payload.get("values"), Sequence):
        return payload["values"]
    return ()


def _extract_header_indices(payload: Mapping[str, Any]) -> dict[str, int]:
    header: Any = None
    data = payload.get("data")
    if isinstance(data, Mapping):
        nested = data.get("data")
        if isinstance(nested, Mapping):
            header = nested.get("header")
        if header is None:
            header = data.get("header")
    if header is None:
        header = payload.get("header")

    if not isinstance(header, str):
        return {}

    return {
        part.strip().upper(): index
        for index, part in enumerate(header.replace("\r", "").split(","))
    }


def _is_row(value: Any) -> bool:
    return isinstance(value, Sequence) and not isinstance(value, str | bytes)


def _row_value(
    row: Sequence[Any],
    indices: Mapping[str, int],
    key: str,
    default_index: int,
) -> Any:
    index = indices.get(key, default_index)
    if index >= len(row):
        return None
    return row[index]


def _parse_station_metadata_row(
    row: Sequence[Any],
    indices: Mapping[str, int],
) -> ChmiStationMetadata | None:
    station_id = _as_str(_row_value(row, indices, "WSI", 0))
    full_name = _as_str(_row_value(row, indices, "FULL_NAME", 2))
    longitude = _as_float(_row_value(row, indices, "GEOGR1", 3))
    latitude = _as_float(_row_value(row, indices, "GEOGR2", 4))
    if station_id is None or full_name is None or latitude is None or longitude is None:
        return None

    return ChmiStationMetadata(
        station_id=station_id,
        gh_id=_as_str(_row_value(row, indices, "GH_ID", 1)),
        full_name=full_name,
        latitude=latitude,
        longitude=longitude,
        elevation=_as_float(_row_value(row, indices, "ELEVATION", 5)),
        begin_date=_parse_datetime(_row_value(row, indices, "BEGIN_DATE", 6)),
    )


def _distance_km(
    latitude_a: float,
    longitude_a: float,
    latitude_b: float,
    longitude_b: float,
) -> float:
    radius_km = 6371.0088
    lat_a = math.radians(latitude_a)
    lat_b = math.radians(latitude_b)
    delta_lat = math.radians(latitude_b - latitude_a)
    delta_lon = math.radians(longitude_b - longitude_a)

    haversine = (
        math.sin(delta_lat / 2) ** 2
        + math.cos(lat_a) * math.cos(lat_b) * math.sin(delta_lon / 2) ** 2
    )
    return radius_km * 2 * math.atan2(math.sqrt(haversine), math.sqrt(1 - haversine))


def _as_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _as_int(value: Any) -> int | None:
    parsed = _as_float(value)
    if parsed is None:
        return None

    code = int(parsed)
    if parsed != code:
        return None
    return code


def _as_str(value: Any) -> str | None:
    if value is None:
        return None
    normalized = str(value).strip()
    return normalized or None


def _parse_datetime(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None

    normalized = value.replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None

    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def _is_newer_or_equal(
    candidate: datetime | None,
    current: datetime | None,
) -> bool:
    if candidate is None:
        return current is None
    if current is None:
        return True
    return candidate >= current


def _selected_value(
    selected: Mapping[str, tuple[datetime | None, float, str | None, float | None]],
    element: str,
) -> float | None:
    item = selected.get(element)
    if item is None:
        return None
    return item[1]


def _latest_observed_at(
    selected: Mapping[str, tuple[datetime | None, float, str | None, float | None]],
) -> datetime | None:
    timestamps = [
        observed_at
        for observed_at, _value, _flag, _quality in selected.values()
        if observed_at
    ]
    if not timestamps:
        return None
    return max(timestamps)


def _quality_by_element(
    selected: Mapping[str, tuple[datetime | None, float, str | None, float | None]],
) -> dict[str, float | None]:
    return {
        element: quality
        for element, (_observed_at, _value, _flag, quality) in selected.items()
    }


def _flag_by_element(
    selected: Mapping[str, tuple[datetime | None, float, str | None, float | None]],
) -> dict[str, str | None]:
    return {
        element: flag
        for element, (_observed_at, _value, flag, _quality) in selected.items()
    }


def _precipitation_samples(
    precipitation_by_timestamp: Mapping[datetime, float],
) -> tuple[ChmiPrecipitationSample, ...]:
    return tuple(
        ChmiPrecipitationSample(observed_at=observed_at, amount=amount)
        for observed_at, amount in sorted(precipitation_by_timestamp.items())
    )


def _precipitation_total(
    samples: Sequence[ChmiPrecipitationSample],
) -> float | None:
    if not samples:
        return None
    return round(sum(sample.amount for sample in samples), 3)


def _precipitation_last_hour(
    samples: Sequence[ChmiPrecipitationSample],
) -> float | None:
    if not samples:
        return None

    latest_observed_at = max(sample.observed_at for sample in samples)
    threshold = latest_observed_at - timedelta(hours=1)
    return round(
        sum(
            sample.amount
            for sample in samples
            if threshold < sample.observed_at <= latest_observed_at
        ),
        3,
    )


def _with_precipitation_statistics(
    observation: ChmiObservation,
    observations: Sequence[ChmiObservation],
    *,
    precipitation_timezone: tzinfo,
    precipitation_date: date,
) -> ChmiObservation:
    samples = _combined_precipitation_samples(observations)
    local_day_samples = [
        sample
        for sample in samples
        if sample.observed_at.astimezone(precipitation_timezone).date()
        == precipitation_date
    ]

    observation.precipitation_samples = samples
    precipitation_1h = _precipitation_last_hour(samples)
    if precipitation_1h is not None:
        observation.precipitation_1h = precipitation_1h
    observation.precipitation_today = _precipitation_total(local_day_samples)
    return observation


def _combined_precipitation_samples(
    observations: Sequence[ChmiObservation],
) -> tuple[ChmiPrecipitationSample, ...]:
    return tuple(
        sorted(
            (
                sample
                for observation in observations
                for sample in observation.precipitation_samples
            ),
            key=lambda sample: sample.observed_at,
        )
    )


def _apply_observed_precipitation_1h(
    observation: ChmiObservation,
    hourly_observation: ChmiObservation,
) -> None:
    observation.precipitation_1h = hourly_observation.precipitation_1h
    if ELEMENT_PRECIPITATION_1H in hourly_observation.quality_by_element:
        observation.quality_by_element[ELEMENT_PRECIPITATION_1H] = (
            hourly_observation.quality_by_element[ELEMENT_PRECIPITATION_1H]
        )
    if ELEMENT_PRECIPITATION_1H in hourly_observation.flag_by_element:
        observation.flag_by_element[ELEMENT_PRECIPITATION_1H] = (
            hourly_observation.flag_by_element[ELEMENT_PRECIPITATION_1H]
        )
    observation.available_elements = tuple(
        sorted({*observation.available_elements, ELEMENT_PRECIPITATION_1H})
    )
