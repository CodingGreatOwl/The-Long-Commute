from __future__ import annotations

import csv
import json
import re
import unicodedata
from dataclasses import dataclass
from pathlib import Path

from .gtfs import load_stops, train_trip_ids, load_stop_times
from .models import StationMatch, Stop


@dataclass(frozen=True)
class MatchReport:
    matched: list[dict[str, str]]
    ambiguous: list[dict[str, object]]
    unmatched: list[dict[str, str]]


def normalize_name(name: str) -> str:
    text = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode("ascii")
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _train_stop_ids(gtfs_dir: Path) -> set[str]:
    trip_ids = train_trip_ids(gtfs_dir)
    stop_times = load_stop_times(gtfs_dir)
    train_stops: set[str] = set()
    for trip_id in trip_ids:
        for st in stop_times.get(trip_id, []):
            train_stops.add(st.stop_id)
    return train_stops


def _station_groups(stops: dict[str, Stop], allowed_stop_ids: set[str]) -> dict[str, StationMatch]:
    grouped: dict[str, list[str]] = {}
    names: dict[str, str] = {}
    for stop in stops.values():
        if stop.stop_id not in allowed_stop_ids:
            continue
        station_id = stop.parent_station or stop.stop_id
        grouped.setdefault(station_id, []).append(stop.stop_id)
        names.setdefault(station_id, stops[station_id].stop_name if station_id in stops else stop.stop_name)

    return {
        station_id: StationMatch(station_id=station_id, station_name=names[station_id], stop_ids=tuple(sorted(stop_ids)))
        for station_id, stop_ids in grouped.items()
    }


def _load_overrides(overrides_path: Path | None) -> dict[str, str]:
    if not overrides_path:
        return {}
    with overrides_path.open("r", encoding="utf-8") as fh:
        data = json.load(fh)
    return {normalize_name(k): v for k, v in data.get("matches", {}).items()}


def load_zvv_stop_list(zvv_stop_list_path: Path) -> list[dict[str, str]]:
    with zvv_stop_list_path.open("r", encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def match_zvv_stations(
    gtfs_dir: Path,
    zvv_stop_list_path: Path,
    overrides_path: Path | None = None,
) -> tuple[list[StationMatch], MatchReport]:
    stops = load_stops(gtfs_dir)
    train_stops = _train_stop_ids(gtfs_dir)
    stations = _station_groups(stops, train_stops)
    by_name: dict[str, list[StationMatch]] = {}
    for station in stations.values():
        by_name.setdefault(normalize_name(station.station_name), []).append(station)

    overrides = _load_overrides(overrides_path)
    zvv_rows = load_zvv_stop_list(zvv_stop_list_path)

    matched: list[StationMatch] = []
    report_matched: list[dict[str, str]] = []
    report_ambiguous: list[dict[str, object]] = []
    report_unmatched: list[dict[str, str]] = []

    for row in zvv_rows:
        source_name = (row.get("station_name") or "").strip()
        source_id = (row.get("zvv_id") or "").strip()
        key = normalize_name(source_name)

        if key in overrides:
            station_id = overrides[key]
            station = stations.get(station_id)
            if station:
                matched.append(station)
                report_matched.append({"zvv_id": source_id, "station_name": source_name, "matched_station_id": station_id, "method": "override"})
                continue

        candidates = by_name.get(key, [])
        if len(candidates) == 1:
            station = candidates[0]
            matched.append(station)
            report_matched.append(
                {
                    "zvv_id": source_id,
                    "station_name": source_name,
                    "matched_station_id": station.station_id,
                    "method": "name_exact",
                }
            )
        elif len(candidates) > 1:
            report_ambiguous.append(
                {
                    "zvv_id": source_id,
                    "station_name": source_name,
                    "candidate_station_ids": [c.station_id for c in candidates],
                }
            )
        else:
            report_unmatched.append({"zvv_id": source_id, "station_name": source_name})

    unique = {station.station_id: station for station in matched}
    return sorted(unique.values(), key=lambda s: s.station_name), MatchReport(report_matched, report_ambiguous, report_unmatched)


def write_match_outputs(stations: list[StationMatch], report: MatchReport, stations_path: Path, report_path: Path) -> None:
    stations_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)

    with stations_path.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=["station_id", "station_name", "stop_ids"])
        writer.writeheader()
        for station in stations:
            writer.writerow(
                {
                    "station_id": station.station_id,
                    "station_name": station.station_name,
                    "stop_ids": "|".join(station.stop_ids),
                }
            )

    with report_path.open("w", encoding="utf-8") as fh:
        json.dump(
            {
                "matched": report.matched,
                "ambiguous": report.ambiguous,
                "unmatched": report.unmatched,
            },
            fh,
            indent=2,
        )
