"""Data models for CHMI OpenData observations."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass(slots=True)
class ChmiObservation:
    """Normalized current observation for a CHMI weather station."""

    station_id: str
    observed_at: datetime | None
    temperature: float | None
    humidity: float | None
    pressure: float | None
    precipitation_10m: float | None
    wind_speed: float | None
    wind_gust: float | None
    wind_direction: float | None
    available_elements: tuple[str, ...] = field(default_factory=tuple)


@dataclass(slots=True)
class ChmiStationMetadata:
    """Normalized CHMI OpenData station metadata."""

    station_id: str
    gh_id: str | None
    full_name: str
    latitude: float
    longitude: float
    elevation: float | None
    begin_date: datetime | None


@dataclass(slots=True)
class ChmiStationCapabilities:
    """Normalized measurable elements for one CHMI OpenData station."""

    station_id: str
    supported_elements: tuple[str, ...]
    observation_type: str
    observation_interval_minutes: int


@dataclass(slots=True)
class ChmiNearestStation:
    """CHMI station with distance from a requested location."""

    station: ChmiStationMetadata
    distance_km: float
