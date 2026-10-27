# The Long Commute

Python project for identifying the **ordered** ZVV station pair whose **fastest available scheduled train journey** is the longest.

## Scope (current milestone)

This repository implements the first end-to-end milestone:

1. Load GTFS timetable files (train-only filtering).
2. Import the official ZVV stop list from a local CSV export.
3. Match ZVV stops to GTFS train stations with a separate reconciliation step.
4. Produce a validated station list plus an ambiguity/unmatched report.
5. Build an initial timetable connection graph.
6. Compute earliest-arrival journeys with waiting and transfer times.
7. Rank ordered station pairs by their minimum scheduled journey duration.

## Data sources

- Swiss GTFS timetable files (`stops.txt`, `routes.txt`, `trips.txt`, `stop_times.txt`, `calendar.txt`, `calendar_dates.txt`, optional `transfers.txt`).
- Official ZVV regional network stop list:
  - https://www.zvv.ch/en/timetable-and-information/zone-map/regional-network.html#accordion-71e76ebb11-item-d108ecd612
  - Export/save locally to CSV; this project does not silently substitute another source.

## Matching policy

- Normalized-name exact matching is attempted first.
- Ambiguous matches are **reported, not auto-resolved**.
- Unmatched records are **reported, not discarded**.
- Manual corrections are supported via JSON overrides.

## Project structure

- `src/long_commute/` — ingestion, matching, routing, optimization, CLI.
- `data/` — data instructions and synthetic sample dataset.
- `tests/` — unit/integration tests against synthetic data.

## Installation

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
```

## Usage

### 1) Match ZVV list to GTFS stations

```bash
long-commute match-stops \
  --gtfs-dir /absolute/path/to/gtfs \
  --zvv-stop-list /absolute/path/to/zvv_stop_list.csv \
  --overrides /absolute/path/to/match_overrides.json \
  --out-stations /absolute/path/to/output/stations.csv \
  --out-report /absolute/path/to/output/match_report.json
```

### 2) Analyze longest fastest ordered pair

```bash
long-commute analyze \
  --gtfs-dir /absolute/path/to/gtfs \
  --stations /absolute/path/to/output/stations.csv \
  --service-date 2026-01-05 \
  --out-json /absolute/path/to/output/results.json \
  --out-csv /absolute/path/to/output/results.csv \
  --top-n 10
```

### 3) One-shot run

```bash
long-commute run \
  --gtfs-dir /absolute/path/to/gtfs \
  --zvv-stop-list /absolute/path/to/zvv_stop_list.csv \
  --overrides /absolute/path/to/match_overrides.json \
  --stations /absolute/path/to/output/stations.csv \
  --match-report /absolute/path/to/output/match_report.json \
  --service-date 2026-01-05 \
  --out-json /absolute/path/to/output/results.json \
  --out-csv /absolute/path/to/output/results.csv
```

## Assumptions and architecture notes

- Train-only filter uses GTFS `route_type` values for rail and rail subcategories.
- Journey computation uses a connection-scan style earliest-arrival pass over scheduled connections.
- Transfer waiting times are included through departure constraints and optional `transfers.txt` edges.
- Current implementation evaluates destination travel-time minima over departure candidates derived from origin departure events.
- Branch-reduction optimizations are intentionally not enabled by default in this milestone; correctness-first baseline is prioritized.

## Reproducibility

Given a fixed GTFS dataset, ZVV list, override file, and service date, outputs are deterministic.

## Tests

```bash
pytest
```

## Sample demo

Synthetic data is provided under:

- `data/sample/gtfs/`
- `data/sample/zvv/zvv_stop_list.csv`

It is intended for tests and CLI smoke-checks only (not real ZVV-wide results).
