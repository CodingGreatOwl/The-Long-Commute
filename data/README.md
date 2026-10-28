# Data directory

- `sample/` contains a tiny synthetic GTFS-like dataset for tests and demos.
- Put full GTFS-CH files in `data/gtfs-ch/` (ignored by git).
- Save the official ZVV regional network stop list as CSV (for example `data/raw/zvv_stop_list.csv`) with columns:
  - `zvv_id`
  - `station_name`
- Optional manual corrections file (JSON):

```json
{
  "matches": {
    "Zurich HB": "8503000"
  }
}
```

The pipeline never auto-resolves ambiguous matches; unresolved records stay in the report.
