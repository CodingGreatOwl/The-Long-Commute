from __future__ import annotations

from collections import defaultdict, deque
from math import inf

from .models import Connection, Transfer


def _transfers_by_from_stop(transfers: list[Transfer]) -> dict[str, list[tuple[str, int]]]:
    """Index transfers by origin stop for quick relaxation."""
    grouped: dict[str, list[tuple[str, int]]] = defaultdict(list)
    for transfer in transfers:
        grouped[transfer.from_stop_id].append((transfer.to_stop_id, transfer.min_transfer_secs))
    return grouped


def _relax_transfers(arrivals: dict[str, float], start_stop: str, transfer_map: dict[str, list[tuple[str, int]]]) -> None:
    """Propagate improved arrival times through transfer edges."""
    queue = deque([start_stop])
    while queue:
        current = queue.popleft()
        current_arrival = arrivals.get(current, inf)
        for target, transfer_time in transfer_map.get(current, []):
            candidate = current_arrival + transfer_time
            if candidate < arrivals.get(target, inf):
                arrivals[target] = candidate
                queue.append(target)


def earliest_arrivals(
    connections: list[Connection],
    transfers: list[Transfer],
    origin_stop_ids: set[str],
    departure_secs: int,
) -> dict[str, int]:
    """Compute earliest arrivals from origin stops at a departure time."""
    arrivals: dict[str, float] = defaultdict(lambda: inf)
    transfer_map = _transfers_by_from_stop(transfers)

    for origin in origin_stop_ids:
        arrivals[origin] = min(arrivals[origin], departure_secs)
        _relax_transfers(arrivals, origin, transfer_map)

    for connection in connections:
        if connection.departure_secs < departure_secs:
            continue
        source_arrival = arrivals.get(connection.from_stop_id, inf)
        if source_arrival <= connection.departure_secs and connection.arrival_secs < arrivals.get(connection.to_stop_id, inf):
            arrivals[connection.to_stop_id] = connection.arrival_secs
            _relax_transfers(arrivals, connection.to_stop_id, transfer_map)

    return {stop_id: int(arrival) for stop_id, arrival in arrivals.items() if arrival < inf}


def departure_candidates(connections: list[Connection], origin_stop_ids: set[str]) -> list[int]:
    """Return departure times worth evaluating for an origin station."""
    candidates = {0}
    for connection in connections:
        if connection.from_stop_id in origin_stop_ids:
            candidates.add(connection.departure_secs)
    return sorted(candidates)
