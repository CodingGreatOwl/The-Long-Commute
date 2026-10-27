from pathlib import Path

from long_commute.matching import match_zvv_stations


def test_matching_reports_ambiguous_and_override(tmp_path: Path) -> None:
    gtfs = tmp_path / "gtfs"
    gtfs.mkdir()
    (gtfs / "stops.txt").write_text(
        "stop_id,stop_name,stop_lat,stop_lon,location_type,parent_station\n"
        "S1,Zurich HB,0,0,1,\n"
        "S2,Zurich HB,0,0,1,\n"
        "S3,Uster,0,0,1,\n",
        encoding="utf-8",
    )
    (gtfs / "routes.txt").write_text("route_id,route_short_name,route_long_name,route_type\nR1,R1,R1,2\n", encoding="utf-8")
    (gtfs / "trips.txt").write_text("route_id,service_id,trip_id\nR1,S1,T1\n", encoding="utf-8")
    (gtfs / "stop_times.txt").write_text(
        "trip_id,arrival_time,departure_time,stop_id,stop_sequence\n"
        "T1,06:00:00,06:00:00,S1,1\n"
        "T1,06:05:00,06:05:00,S3,2\n",
        encoding="utf-8",
    )
    (gtfs / "calendar.txt").write_text(
        "service_id,monday,tuesday,wednesday,thursday,friday,saturday,sunday,start_date,end_date\n"
        "S1,1,1,1,1,1,1,1,20260101,20261231\n",
        encoding="utf-8",
    )
    (gtfs / "calendar_dates.txt").write_text("service_id,date,exception_type\n", encoding="utf-8")

    zvv = tmp_path / "zvv.csv"
    zvv.write_text("zvv_id,station_name\n1,Zurich HB\n2,Uster\n", encoding="utf-8")

    overrides = tmp_path / "overrides.json"
    overrides.write_text('{"matches":{"Zurich HB":"S1"}}', encoding="utf-8")

    stations, report = match_zvv_stations(gtfs, zvv, overrides)

    assert {s.station_id for s in stations} == {"S1", "S3"}
    assert not report.ambiguous
    assert not report.unmatched
