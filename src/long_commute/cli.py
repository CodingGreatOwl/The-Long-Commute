from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path

from .matching import match_zvv_stations, write_match_outputs
from .optimization import find_longest_fastest_pair, load_station_matches, write_results_csv, write_results_json


def _parse_date(value: str):
    """Parse a CLI service date argument in YYYY-MM-DD format."""
    return datetime.strptime(value, "%Y-%m-%d").date()


def main() -> None:
    """Run the command-line interface for matching and analysis workflows."""
    parser = argparse.ArgumentParser(description="Find the longest fastest train journey within ZVV stations")
    subparsers = parser.add_subparsers(dest="command", required=True)

    match_parser = subparsers.add_parser("match-stops", help="Match official ZVV stops to GTFS train stations")
    match_parser.add_argument("--gtfs-dir", type=Path, required=True)
    match_parser.add_argument("--zvv-stop-list", type=Path, required=True)
    match_parser.add_argument("--overrides", type=Path)
    match_parser.add_argument("--out-stations", type=Path, required=True)
    match_parser.add_argument("--out-report", type=Path, required=True)

    analyze_parser = subparsers.add_parser("analyze", help="Compute the longest fastest ordered station pair")
    analyze_parser.add_argument("--gtfs-dir", type=Path, required=True)
    analyze_parser.add_argument("--stations", type=Path, required=True)
    analyze_parser.add_argument("--service-date", type=_parse_date, required=True)
    analyze_parser.add_argument("--out-json", type=Path, required=True)
    analyze_parser.add_argument("--out-csv", type=Path, required=True)
    analyze_parser.add_argument("--top-n", type=int, default=5)

    run_parser = subparsers.add_parser("run", help="Run matching and analysis in one command")
    run_parser.add_argument("--gtfs-dir", type=Path, required=True)
    run_parser.add_argument("--zvv-stop-list", type=Path, required=True)
    run_parser.add_argument("--overrides", type=Path)
    run_parser.add_argument("--stations", type=Path, required=True)
    run_parser.add_argument("--match-report", type=Path, required=True)
    run_parser.add_argument("--service-date", type=_parse_date, required=True)
    run_parser.add_argument("--out-json", type=Path, required=True)
    run_parser.add_argument("--out-csv", type=Path, required=True)
    run_parser.add_argument("--top-n", type=int, default=5)

    args = parser.parse_args()

    if args.command in {"match-stops", "run"}:
        stations, report = match_zvv_stations(args.gtfs_dir, args.zvv_stop_list, getattr(args, "overrides", None))
        write_match_outputs(stations, report, args.out_stations if args.command == "match-stops" else args.stations, args.out_report if args.command == "match-stops" else args.match_report)
        if args.command == "match-stops":
            return

    stations = load_station_matches(args.stations)
    best, top_results = find_longest_fastest_pair(args.gtfs_dir, stations, args.service_date, top_n=args.top_n)
    write_results_json(args.out_json, best, top_results)
    write_results_csv(args.out_csv, top_results)


if __name__ == "__main__":
    main()
