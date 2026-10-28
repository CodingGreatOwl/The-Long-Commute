from __future__ import annotations

import csv
from collections import defaultdict
from datetime import date, datetime
from pathlib import Path

from .models import Connection, Route, Stop, StopTime, Transfer, Trip, TRAIN_ROUTE_TYPES
from .timeutil import hhmmss_to_secs


def _read_csv(path: Path) -> list[dict[str, str]]:
    """Read a UTF-8 CSV file into a list of row dictionaries."""
    with path.open("r", encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def load_stops(gtfs_dir: Path) -> dict[str, Stop]:
    """Load GTFS stops keyed by stop_id."""
    rows = _read_csv(gtfs_dir / "stops.txt")
    stops: dict[str, Stop] = {}
    for row in rows:
        stops[row["stop_id"]] = Stop(
            stop_id=row["stop_id"],
            stop_name=row["stop_name"],
            stop_lat=float(row["stop_lat"]) if row.get("stop_lat") else None,
            stop_lon=float(row["stop_lon"]) if row.get("stop_lon") else None,
            location_type=int(row.get("location_type") or 0),
            parent_station=row.get("parent_station") or None,
        )
    return stops


def load_routes(gtfs_dir: Path) -> dict[str, Route]:
    """Load GTFS routes keyed by route_id."""
    rows = _read_csv(gtfs_dir / "routes.txt")
    return {
        row["route_id"]: Route(route_id=row["route_id"], route_type=int(row["route_type"]))
        for row in rows
    }


def load_trips(gtfs_dir: Path) -> dict[str, Trip]:
    """Load GTFS trips keyed by trip_id."""
    rows = _read_csv(gtfs_dir / "trips.txt")
    return {
        row["trip_id"]: Trip(trip_id=row["trip_id"], route_id=row["route_id"], service_id=row["service_id"])
        for row in rows
    }


def load_stop_times(gtfs_dir: Path) -> dict[str, list[StopTime]]:
    """Load and sequence stop times for each trip."""
    rows = _read_csv(gtfs_dir / "stop_times.txt")
    grouped: dict[str, list[StopTime]] = defaultdict(list)
    for row in rows:
        grouped[row["trip_id"]].append(
            StopTime(
                trip_id=row["trip_id"],
                arrival_secs=hhmmss_to_secs(row["arrival_time"]),
                departure_secs=hhmmss_to_secs(row["departure_time"]),
                stop_id=row["stop_id"],
                stop_sequence=int(row["stop_sequence"]),
            )
        )
    for stop_times in grouped.values():
        stop_times.sort(key=lambda st: st.stop_sequence)
    return grouped


def load_transfers(gtfs_dir: Path) -> list[Transfer]:
    """Load transfer rules from transfers.txt when present."""
    path = gtfs_dir / "transfers.txt"
    if not path.exists():
        return []
    rows = _read_csv(path)
    transfers: list[Transfer] = []
    for row in rows:
        if not row.get("from_stop_id") or not row.get("to_stop_id"):
            continue
        transfers.append(
            Transfer(
                from_stop_id=row["from_stop_id"],
                to_stop_id=row["to_stop_id"],
                min_transfer_secs=int(row.get("min_transfer_time") or 0),
            )
        )
    return transfers


def _parse_yyyymmdd(value: str) -> date:
    """Parse a GTFS YYYYMMDD calendar field into a date."""
    return datetime.strptime(value, "%Y%m%d").date()


def active_service_ids(gtfs_dir: Path, service_date: date) -> set[str]:
    """Return service_ids active on a specific date, including exceptions."""
    services: set[str] = set()
    calendar_path = gtfs_dir / "calendar.txt"
    if calendar_path.exists():
        weekday_name = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"][
            service_date.weekday()
        ]
        for row in _read_csv(calendar_path):
            if row.get(weekday_name) != "1":
                continue
            if _parse_yyyymmdd(row["start_date"]) <= service_date <= _parse_yyyymmdd(row["end_date"]):
                services.add(row["service_id"])

    calendar_dates_path = gtfs_dir / "calendar_dates.txt"
    if calendar_dates_path.exists():
        for row in _read_csv(calendar_dates_path):
            if _parse_yyyymmdd(row["date"]) != service_date:
                continue
            if row.get("exception_type") == "1":
                services.add(row["service_id"])
            elif row.get("exception_type") == "2":
                services.discard(row["service_id"])

    return services


def train_trip_ids(gtfs_dir: Path) -> set[str]:
    """Return trip_ids whose routes are classified as train/rail services."""
    routes = load_routes(gtfs_dir)
    trips = load_trips(gtfs_dir)
    return {
        trip.trip_id
        for trip in trips.values()
        if routes.get(trip.route_id) and routes[trip.route_id].route_type in TRAIN_ROUTE_TYPES
    }


def build_connections(gtfs_dir: Path, service_date: date) -> tuple[list[Connection], list[Transfer]]:
    """Build train connections and transfers for a given service date."""
    trips = load_trips(gtfs_dir)
    stop_times = load_stop_times(gtfs_dir)
    active_services = active_service_ids(gtfs_dir, service_date)
    allowed_trips = train_trip_ids(gtfs_dir)

    connections: list[Connection] = []
    for trip_id in allowed_trips:
        trip = trips.get(trip_id)
        if not trip or trip.service_id not in active_services:
            continue
        sequence = stop_times.get(trip_id, [])
        for current, nxt in zip(sequence, sequence[1:]):
            depart = current.departure_secs
            arrive = nxt.arrival_secs
            if arrive < depart:
                arrive += 24 * 3600
            connections.append(
                Connection(
                    from_stop_id=current.stop_id,
                    to_stop_id=nxt.stop_id,
                    departure_secs=depart,
                    arrival_secs=arrive,
                    trip_id=trip_id,
                )
            )

    connections.sort(key=lambda c: c.departure_secs)
    return connections, load_transfers(gtfs_dir)
