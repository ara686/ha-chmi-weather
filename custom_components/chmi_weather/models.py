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
