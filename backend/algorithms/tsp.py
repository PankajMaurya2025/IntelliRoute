"""
Multi-stop route optimization for a driver carrying several orders.
Greedy nearest-neighbor construction + optional 2-opt local improvement.
Operates on straight-line (haversine) distance between stops, which is
appropriate for sequencing decisions even though actual travel uses the
road graph.
"""
import math
from typing import List, Tuple, Dict


def _haversine(a: Tuple[float, float], b: Tuple[float, float]) -> float:
    R = 6371.0
    lat1, lat2 = math.radians(a[0]), math.radians(b[0])
    dlat = math.radians(b[0] - a[0])
    dlng = math.radians(b[1] - a[1])
    h = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlng / 2) ** 2
    return 2 * R * math.asin(min(1.0, math.sqrt(h)))


def _total_distance(order: List[int], coords: List[Tuple[float, float]]) -> float:
    return sum(_haversine(coords[order[i]], coords[order[i + 1]]) for i in range(len(order) - 1))


def nearest_neighbor(coords: List[Tuple[float, float]]) -> List[int]:
    """coords[0] is assumed to be the warehouse/start. Returns a visiting order of indices."""
    n = len(coords)
    unvisited = set(range(1, n))
    route = [0]
    current = 0
    while unvisited:
        nxt = min(unvisited, key=lambda i: _haversine(coords[current], coords[i]))
        route.append(nxt)
        unvisited.remove(nxt)
        current = nxt
    return route


def two_opt(route: List[int], coords: List[Tuple[float, float]], max_iterations: int = 200) -> List[int]:
    """Classic 2-opt: repeatedly reverse segments if it shortens the tour."""
    best = route[:]
    improved = True
    iterations = 0
    while improved and iterations < max_iterations:
        improved = False
        iterations += 1
        for i in range(1, len(best) - 1):
            for j in range(i + 1, len(best)):
                if j - i == 1:
                    continue
                new_route = best[:i] + best[i:j][::-1] + best[j:]
                if _total_distance(new_route, coords) < _total_distance(best, coords):
                    best = new_route
                    improved = True
    return best


def optimize_multi_stop(stops: List[Dict], warehouse: Tuple[float, float], use_2opt: bool = True) -> Dict:
    """
    stops: list of dicts each with 'name', 'lat', 'lng' (e.g., order delivery points)
    warehouse: (lat, lng) of the start/end depot
    Returns the optimized visiting sequence (warehouse -> stops -> warehouse) with total distance.
    """
    coords = [warehouse] + [(s["lat"], s["lng"]) for s in stops]
    names = ["Warehouse"] + [s["name"] for s in stops]

    order = nearest_neighbor(coords)
    if use_2opt and len(coords) > 3:
        order = two_opt(order, coords)

    # Return to warehouse at the end
    full_order = order + [0]
    total_km = _total_distance(full_order, coords)

    return {
        "sequence": [names[i] for i in full_order],
        "total_distance_km": round(total_km, 2),
        "num_stops": len(stops),
    }
