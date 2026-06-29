"""Data models for CHMI OpenData observations."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime


@dataclass(slots=True, frozen=True)
class ChmiPrecipitationSample:
    """One timestamped CHMI precipitation interval sample."""

    observed_at: datetime
    amount: float


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
    temperature_max_10m: float | None = None
    temperature_min_10m: float | None = None
    apparent_temperature: float | None = None
    wind_speed_avg: float | None = None
    wind_direction_avg: float | None = None
    wind_gust_direction: float | None = None
    precipitation_1h: float | None = None
    precipitation_today: float | None = None
    daily_summary_date: date | None = None
    yesterday_precipitation: float | None = None
    yesterday_temperature_max: float | None = None
    yesterday_temperature_min: float | None = None
    yesterday_wind_gust_max: float | None = None
    month_precipitation_chmi: float | None = None
    precipitation_samples: tuple[ChmiPrecipitationSample, ...] = field(
        default_factory=tuple
    )
    available_elements: tuple[str, ...] = field(default_factory=tuple)
    quality_by_element: dict[str, float | None] = field(default_factory=dict)
    flag_by_element: dict[str, str | None] = field(default_factory=dict)


@dataclass(slots=True, frozen=True)
class ChmiDailySummary:
    """Normalized recent daily station summary from CHMI OpenData."""

    station_id: str
    summary_date: date
    yesterday_precipitation: float | None
    yesterday_temperature_max: float | None
    yesterday_temperature_min: float | None
    yesterday_wind_gust_max: float | None
    month_precipitation_chmi: float | None


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
    supported_elements_by_interval: dict[int, tuple[str, ...]] = field(
        default_factory=dict
    )


@dataclass(slots=True)
class ChmiNearestStation:
    """CHMI station with distance from a requested location."""

    station: ChmiStationMetadata
    distance_km: float
