from __future__ import annotations

from dataclasses import dataclass
from datetime import date


TRAIN_ROUTE_TYPES = {2, *range(100, 118)}


@dataclass(frozen=True)
class Stop:
    stop_id: str
    stop_name: str
    stop_lat: float | None
    stop_lon: float | None
    location_type: int
    parent_station: str | None


@dataclass(frozen=True)
class Route:
    route_id: str
    route_type: int


@dataclass(frozen=True)
class Trip:
    trip_id: str
    route_id: str
    service_id: str


@dataclass(frozen=True)
class StopTime:
    trip_id: str
    arrival_secs: int
    departure_secs: int
    stop_id: str
    stop_sequence: int


@dataclass(frozen=True)
class Connection:
    from_stop_id: str
    to_stop_id: str
    departure_secs: int
    arrival_secs: int
    trip_id: str


@dataclass(frozen=True)
class Transfer:
    from_stop_id: str
    to_stop_id: str
    min_transfer_secs: int


@dataclass(frozen=True)
class StationMatch:
    station_id: str
    station_name: str
    stop_ids: tuple[str, ...]


@dataclass(frozen=True)
class PairResult:
    origin_station_id: str
    origin_station_name: str
    destination_station_id: str
    destination_station_name: str
    fastest_duration_secs: int
    best_departure_secs: int
    best_arrival_secs: int
    service_date: date
