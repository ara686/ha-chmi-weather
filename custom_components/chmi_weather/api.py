"""Async CHMI OpenData client and parser."""

from __future__ import annotations

import asyncio
import json
import math
from collections.abc import Mapping, Sequence
from datetime import UTC, date, datetime, timedelta
from typing import Any

from .const import (
    CHMI_BASE_URL,
    CHMI_ELEMENT_BY_FIELD,
    CHMI_METADATA_BASE_URL,
    ELEMENT_HUMIDITY,
    ELEMENT_PRECIPITATION_10M,
    ELEMENT_PRESSURE,
    ELEMENT_TEMPERATURE,
    ELEMENT_WIND_DIRECTION,
    ELEMENT_WIND_GUST,
    ELEMENT_WIND_SPEED,
    OBSERVATION_VALUE_FIELDS,
)
from .models import (
    ChmiNearestStation,
    ChmiObservation,
    ChmiStationCapabilities,
    ChmiStationMetadata,
)

DEFAULT_TIMEOUT_SECONDS = 20


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
    ) -> ChmiObservation:
        """Return current observations for a station, falling back to yesterday."""
        today = datetime.now(UTC).date()
        last_error: ChmiApiError | None = None

        for day in (today, today - timedelta(days=1)):
            try:
                return await self.async_get_current_observations_for_date(
                    station_id,
                    day,
                )
            except (ChmiApiNotFoundError, ChmiApiDataError) as err:
                last_error = err

        raise last_error or ChmiApiDataError("No usable CHMI observations found")

    async def async_get_current_observations_for_date(
        self,
        station_id: str,
        day: date,
    ) -> ChmiObservation:
        """Return observations for one UTC date."""
        url = self._build_current_url(station_id, day)
        payload = await self._async_get_json(url)
        return parse_current_observations(payload, station_id)

    def _build_current_url(self, station_id: str, day: date) -> str:
        """Build a CHMI current observation URL."""
        return f"{self._base_url}/10m-{station_id.strip()}-{day:%Y%m%d}.json"

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
        """Return measurable 10-minute elements for a station."""
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
    values = _extract_values(payload)
    if not values:
        raise ChmiApiDataError("CHMI response does not contain observation rows")

    indices = _extract_header_indices(payload)
    selected: dict[str, tuple[datetime | None, float]] = {}
    available_elements: set[str] = set()

    for row in values:
        if not _is_row(row):
            continue

        station = _row_value(row, indices, "STATION", 0)
        if station_id and str(station).strip() != station_id:
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
        current = selected.get(element_code)
        if current is None or _is_newer_or_equal(observed_at, current[0]):
            selected[element_code] = (observed_at, value)

    observation = ChmiObservation(
        station_id=station_id,
        observed_at=_latest_observed_at(selected),
        temperature=_selected_value(selected, ELEMENT_TEMPERATURE),
        humidity=_selected_value(selected, ELEMENT_HUMIDITY),
        pressure=_selected_value(selected, ELEMENT_PRESSURE),
        precipitation_10m=_selected_value(selected, ELEMENT_PRECIPITATION_10M),
        wind_speed=_selected_value(selected, ELEMENT_WIND_SPEED),
        wind_gust=_selected_value(selected, ELEMENT_WIND_GUST),
        wind_direction=_selected_value(selected, ELEMENT_WIND_DIRECTION),
        available_elements=tuple(sorted(available_elements)),
    )

    if not has_usable_observation(observation):
        raise ChmiApiDataError("CHMI response does not contain usable observations")

    return observation


def parse_station_metadata(
    payload: Mapping[str, Any],
    station_id: str,
) -> ChmiStationMetadata:
    """Parse CHMI meta1 station metadata for one station."""
    normalized_station_id = station_id.strip()
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
    observation_type: str = "10M",
) -> ChmiStationCapabilities:
    """Parse CHMI meta2 measurable element metadata for one station."""
    values = _extract_values(payload)
    if not values:
        raise ChmiApiDataError("CHMI capability metadata does not contain rows")

    indices = _extract_header_indices(payload)
    normalized_station_id = station_id.strip()
    normalized_observation_type = observation_type.strip().upper()
    supported_elements: set[str] = set()

    for row in values:
        if not _is_row(row):
            continue

        row_station_id = _row_value(row, indices, "WSI", 1)
        if str(row_station_id).strip() != normalized_station_id:
            continue

        row_observation_type = _as_str(_row_value(row, indices, "OBS_TYPE", 0))
        if (
            normalized_observation_type
            and row_observation_type is not None
            and row_observation_type.upper() != normalized_observation_type
        ):
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
    )


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
    selected: Mapping[str, tuple[datetime | None, float]],
    element: str,
) -> float | None:
    item = selected.get(element)
    if item is None:
        return None
    return item[1]


def _latest_observed_at(
    selected: Mapping[str, tuple[datetime | None, float]],
) -> datetime | None:
    timestamps = [
        observed_at for observed_at, _value in selected.values() if observed_at
    ]
    if not timestamps:
        return None
    return max(timestamps)
