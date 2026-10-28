from datetime import date
from pathlib import Path

from long_commute.gtfs import active_service_ids


def test_calendar_dates_override(tmp_path: Path) -> None:
    gtfs = tmp_path / "gtfs"
    gtfs.mkdir()
    (gtfs / "calendar.txt").write_text(
        "service_id,monday,tuesday,wednesday,thursday,friday,saturday,sunday,start_date,end_date\n"
        "S1,1,1,1,1,1,1,1,20260101,20261231\n"
        "S2,0,0,0,0,0,0,0,20260101,20261231\n",
        encoding="utf-8",
    )
    (gtfs / "calendar_dates.txt").write_text(
        "service_id,date,exception_type\n"
        "S1,20260105,2\n"
        "S2,20260105,1\n",
        encoding="utf-8",
    )

    services = active_service_ids(gtfs, date(2026, 1, 5))
    assert services == {"S2"}
