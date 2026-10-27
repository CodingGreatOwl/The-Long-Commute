from __future__ import annotations

import csv
import json
from dataclasses import asdict
from datetime import date
from math import inf
from pathlib import Path

from .gtfs import build_connections
from .models import PairResult, StationMatch
from .routing import departure_candidates, earliest_arrivals


def _station_stop_set(station: StationMatch) -> set[str]:
    return set(station.stop_ids)


def _best_duration_between(
    origin: StationMatch,
    destination: StationMatch,
    connections,
    transfers,
) -> tuple[int, int, int] | None:
    origin_stops = _station_stop_set(origin)
    destination_stops = _station_stop_set(destination)

    best_duration = inf
    best_departure = -1
    best_arrival = -1

    for departure in departure_candidates(connections, origin_stops):
        arrivals = earliest_arrivals(connections, transfers, origin_stops, departure)
        arrival = min((arrivals.get(stop_id, inf) for stop_id in destination_stops), default=inf)
        if arrival == inf:
            continue
        duration = arrival - departure
        if duration < best_duration:
            best_duration = duration
            best_departure = departure
            best_arrival = int(arrival)

    if best_duration == inf:
        return None
    return int(best_duration), best_departure, best_arrival


def find_longest_fastest_pair(
    gtfs_dir: Path,
    stations: list[StationMatch],
    service_date: date,
    top_n: int = 5,
) -> tuple[PairResult | None, list[PairResult]]:
    connections, transfers = build_connections(gtfs_dir, service_date)
    if not connections:
        return None, []

    results: list[PairResult] = []
    for origin in stations:
        for destination in stations:
            if origin.station_id == destination.station_id:
                continue
            best = _best_duration_between(origin, destination, connections, transfers)
            if not best:
                continue
            duration, dep, arr = best
            results.append(
                PairResult(
                    origin_station_id=origin.station_id,
                    origin_station_name=origin.station_name,
                    destination_station_id=destination.station_id,
                    destination_station_name=destination.station_name,
                    fastest_duration_secs=duration,
                    best_departure_secs=dep,
                    best_arrival_secs=arr,
                    service_date=service_date,
                )
            )

    if not results:
        return None, []

    ranked = sorted(results, key=lambda r: r.fastest_duration_secs, reverse=True)
    return ranked[0], ranked[:top_n]


def write_results_json(path: Path, best: PairResult | None, top_results: list[PairResult]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "best": asdict(best) if best else None,
        "top_candidates": [asdict(item) for item in top_results],
    }
    if payload["best"]:
        payload["best"]["service_date"] = payload["best"]["service_date"].isoformat()
    for item in payload["top_candidates"]:
        item["service_date"] = item["service_date"].isoformat()

    with path.open("w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2)


def write_results_csv(path: Path, top_results: list[PairResult]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=[
                "origin_station_id",
                "origin_station_name",
                "destination_station_id",
                "destination_station_name",
                "fastest_duration_secs",
                "best_departure_secs",
                "best_arrival_secs",
                "service_date",
            ],
        )
        writer.writeheader()
        for item in top_results:
            row = asdict(item)
            row["service_date"] = row["service_date"].isoformat()
            writer.writerow(row)


def load_station_matches(stations_path: Path) -> list[StationMatch]:
    stations: list[StationMatch] = []
    with stations_path.open("r", encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            stations.append(
                StationMatch(
                    station_id=row["station_id"],
                    station_name=row["station_name"],
                    stop_ids=tuple(item for item in row["stop_ids"].split("|") if item),
                )
            )
    return stations
