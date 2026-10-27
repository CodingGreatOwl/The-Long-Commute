from datetime import date
from pathlib import Path

from long_commute.matching import match_zvv_stations
from long_commute.optimization import find_longest_fastest_pair
from long_commute.routing import earliest_arrivals
from long_commute.gtfs import build_connections


SAMPLE_GTFS = Path("/home/runner/work/The-Long-Commute/The-Long-Commute/data/sample/gtfs")
SAMPLE_ZVV = Path("/home/runner/work/The-Long-Commute/The-Long-Commute/data/sample/zvv/zvv_stop_list.csv")


def test_earliest_arrival_includes_waiting_time() -> None:
    connections, transfers = build_connections(SAMPLE_GTFS, date(2026, 1, 5))
    arrivals = earliest_arrivals(connections, transfers, {"A"}, 6 * 3600)
    assert arrivals["C"] == 7 * 3600 + 10 * 60


def test_longest_fastest_pair() -> None:
    stations, report = match_zvv_stations(SAMPLE_GTFS, SAMPLE_ZVV)
    assert not report.ambiguous
    assert not report.unmatched

    best, top = find_longest_fastest_pair(SAMPLE_GTFS, stations, date(2026, 1, 5), top_n=3)

    assert best is not None
    assert best.origin_station_id == "A"
    assert best.destination_station_id == "C"
    assert best.fastest_duration_secs == 70 * 60
    assert len(top) == 3
