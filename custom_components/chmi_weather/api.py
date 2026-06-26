"""Async CHMI OpenData client and parser."""

from __future__ import annotations

import asyncio
import json
from collections.abc import Mapping, Sequence
from datetime import UTC, date, datetime, timedelta
from typing import Any

from .const import (
    CHMI_BASE_URL,
    CHMI_ELEMENT_BY_FIELD,
    ELEMENT_HUMIDITY,
    ELEMENT_PRECIPITATION_10M,
    ELEMENT_PRESSURE,
    ELEMENT_TEMPERATURE,
    ELEMENT_WIND_DIRECTION,
    ELEMENT_WIND_GUST,
    ELEMENT_WIND_SPEED,
    OBSERVATION_VALUE_FIELDS,
)
from .models import ChmiObservation

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
        timeout: int = DEFAULT_TIMEOUT_SECONDS,
    ) -> None:
        """Initialize the client."""
        self._session = session
        self._base_url = base_url.rstrip("/")
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


def _as_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


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
