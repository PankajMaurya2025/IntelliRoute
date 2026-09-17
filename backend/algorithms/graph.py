"""
Graph data structure and pathfinding algorithms for IntelliRoute's
routing engine. All algorithms are implemented from scratch (no
third-party graph libraries) and share a common `route()` interface.
"""
import heapq
import math
from collections import deque
from typing import Dict, List, Optional, Tuple


class Node:
    __slots__ = ("name", "lat", "lng")

    def __init__(self, name: str, lat: float, lng: float):
        self.name = name
        self.lat = lat
        self.lng = lng


class Edge:
    __slots__ = ("to", "distance_km", "base_time_min", "traffic_factor")

    def __init__(self, to: str, distance_km: float, base_time_min: float, traffic_factor: float = 1.0):
        self.to = to
        self.distance_km = distance_km
        self.base_time_min = base_time_min
        self.traffic_factor = traffic_factor

    @property
    def weighted_time_min(self) -> float:
        return self.base_time_min * self.traffic_factor


class Graph:
    """Directed weighted graph representing the road network."""

    def __init__(self):
        self.nodes: Dict[str, Node] = {}
        self.adjacency: Dict[str, List[Edge]] = {}

    def add_node(self, name: str, lat: float, lng: float):
        self.nodes[name] = Node(name, lat, lng)
        self.adjacency.setdefault(name, [])

    def add_edge(self, from_name: str, to_name: str, distance_km: float,
                 base_time_min: float, traffic_factor: float = 1.0, bidirectional: bool = True):
        self.adjacency.setdefault(from_name, []).append(
            Edge(to_name, distance_km, base_time_min, traffic_factor)
        )
        if bidirectional:
            self.adjacency.setdefault(to_name, []).append(
                Edge(from_name, distance_km, base_time_min, traffic_factor)
            )

    def set_traffic_factor(self, from_name: str, to_name: str, factor: float):
        """Update traffic factor on the edge(s) between two nodes (both directions)."""
        for edge in self.adjacency.get(from_name, []):
            if edge.to == to_name:
                edge.traffic_factor = factor
        for edge in self.adjacency.get(to_name, []):
            if edge.to == from_name:
                edge.traffic_factor = factor

    def neighbors(self, name: str) -> List[Edge]:
        return self.adjacency.get(name, [])

    def haversine_km(self, a: str, b: str) -> float:
        """Great-circle distance between two nodes, used as the A* heuristic."""
        n1, n2 = self.nodes[a], self.nodes[b]
        R = 6371.0
        lat1, lat2 = math.radians(n1.lat), math.radians(n2.lat)
        dlat = math.radians(n2.lat - n1.lat)
        dlng = math.radians(n2.lng - n1.lng)
        h = (math.sin(dlat / 2) ** 2 +
             math.cos(lat1) * math.cos(lat2) * math.sin(dlng / 2) ** 2)
        return 2 * R * math.asin(min(1.0, math.sqrt(h)))


class RouteResult:
    def __init__(self, algorithm: str, path: List[str], distance_km: float,
                 travel_time_min: float, nodes_explored: int, found: bool = True):
        self.algorithm = algorithm
        self.path = path
        self.distance_km = round(distance_km, 2)
        self.travel_time_min = round(travel_time_min, 2)
        self.nodes_explored = nodes_explored
        self.found = found

    def to_dict(self):
        return {
            "algorithm": self.algorithm,
            "path": self.path,
            "distance": self.distance_km,
            "travel_time": self.travel_time_min,
            "nodes_explored": self.nodes_explored,
            "found": self.found,
        }


def _reconstruct(prev: Dict[str, Optional[str]], start: str, end: str) -> List[str]:
    if end not in prev and end != start:
        return []
    path = []
    cur = end
    while cur is not None:
        path.append(cur)
        cur = prev.get(cur)
    path.reverse()
    return path if path and path[0] == start else []


def _path_metrics(graph: Graph, path: List[str]) -> Tuple[float, float]:
    dist, time = 0.0, 0.0
    for i in range(len(path) - 1):
        edge = next((e for e in graph.neighbors(path[i]) if e.to == path[i + 1]), None)
        if edge:
            dist += edge.distance_km
            time += edge.weighted_time_min
    return dist, time


# ---------------------------------------------------------------------------
# Dijkstra — real min-heap priority queue implementation
# ---------------------------------------------------------------------------
def dijkstra(graph: Graph, start: str, end: str) -> RouteResult:
    dist = {start: 0.0}
    prev: Dict[str, Optional[str]] = {start: None}
    visited = set()
    heap = [(0.0, start)]
    explored = 0

    while heap:
        d, node = heapq.heappop(heap)
        if node in visited:
            continue
        visited.add(node)
        explored += 1
        if node == end:
            break
        for edge in graph.neighbors(node):
            nd = d + edge.weighted_time_min
            if nd < dist.get(edge.to, math.inf):
                dist[edge.to] = nd
                prev[edge.to] = node
                heapq.heappush(heap, (nd, edge.to))

    path = _reconstruct(prev, start, end)
    if not path:
        return RouteResult("dijkstra", [], 0, 0, explored, found=False)
    d_km, t_min = _path_metrics(graph, path)
    return RouteResult("dijkstra", path, d_km, t_min, explored)


# ---------------------------------------------------------------------------
# A* — Euclidean/haversine heuristic
# ---------------------------------------------------------------------------
def a_star(graph: Graph, start: str, end: str) -> RouteResult:
    g_score = {start: 0.0}
    f_score = {start: graph.haversine_km(start, end)}
    prev: Dict[str, Optional[str]] = {start: None}
    open_set = [(f_score[start], start)]
    visited = set()
    explored = 0

    while open_set:
        _, node = heapq.heappop(open_set)
        if node in visited:
            continue
        visited.add(node)
        explored += 1
        if node == end:
            break
        for edge in graph.neighbors(node):
            tentative_g = g_score[node] + edge.weighted_time_min
            if tentative_g < g_score.get(edge.to, math.inf):
                g_score[edge.to] = tentative_g
                prev[edge.to] = node
                # heuristic approximated in minutes assuming ~40km/h average speed
                h = (graph.haversine_km(edge.to, end) / 40.0) * 60.0
                f_score[edge.to] = tentative_g + h
                heapq.heappush(open_set, (f_score[edge.to], edge.to))

    path = _reconstruct(prev, start, end)
    if not path:
        return RouteResult("a_star", [], 0, 0, explored, found=False)
    d_km, t_min = _path_metrics(graph, path)
    return RouteResult("a_star", path, d_km, t_min, explored)


# ---------------------------------------------------------------------------
# BFS — fewest hops (unweighted)
# ---------------------------------------------------------------------------
def bfs(graph: Graph, start: str, end: str) -> RouteResult:
    prev: Dict[str, Optional[str]] = {start: None}
    visited = {start}
    queue = deque([start])
    explored = 0

    while queue:
        node = queue.popleft()
        explored += 1
        if node == end:
            break
        for edge in graph.neighbors(node):
            if edge.to not in visited:
                visited.add(edge.to)
                prev[edge.to] = node
                queue.append(edge.to)

    path = _reconstruct(prev, start, end)
    if not path:
        return RouteResult("bfs", [], 0, 0, explored, found=False)
    d_km, t_min = _path_metrics(graph, path)
    return RouteResult("bfs", path, d_km, t_min, explored)


# ---------------------------------------------------------------------------
# DFS — depth-first (not guaranteed shortest, but a real traversal)
# ---------------------------------------------------------------------------
def dfs(graph: Graph, start: str, end: str) -> RouteResult:
    visited = set()
    prev: Dict[str, Optional[str]] = {start: None}
    explored = 0
    found_end = False

    def _visit(node: str) -> bool:
        nonlocal explored, found_end
        visited.add(node)
        explored += 1
        if node == end:
            found_end = True
            return True
        for edge in graph.neighbors(node):
            if edge.to not in visited:
                prev[edge.to] = node
                if _visit(edge.to):
                    return True
        return False

    _visit(start)
    if not found_end:
        return RouteResult("dfs", [], 0, 0, explored, found=False)
    path = _reconstruct(prev, start, end)
    d_km, t_min = _path_metrics(graph, path)
    return RouteResult("dfs", path, d_km, t_min, explored)


# ---------------------------------------------------------------------------
# Bellman-Ford — handles negative-ish adjustments safely, O(V*E)
# ---------------------------------------------------------------------------
def bellman_ford(graph: Graph, start: str, end: str) -> RouteResult:
    dist = {n: math.inf for n in graph.nodes}
    dist[start] = 0.0
    prev: Dict[str, Optional[str]] = {start: None}
    explored = 0

    edges = [(u, e.to, e.weighted_time_min) for u in graph.adjacency for e in graph.adjacency[u]]

    for _ in range(len(graph.nodes) - 1):
        updated = False
        for u, v, w in edges:
            explored += 1
            if dist[u] + w < dist[v]:
                dist[v] = dist[u] + w
                prev[v] = u
                updated = True
        if not updated:
            break

    path = _reconstruct(prev, start, end)
    if not path:
        return RouteResult("bellman_ford", [], 0, 0, explored, found=False)
    d_km, t_min = _path_metrics(graph, path)
    return RouteResult("bellman_ford", path, d_km, t_min, explored)


# ---------------------------------------------------------------------------
# Floyd-Warshall — all-pairs shortest paths, returned for one start/end pair
# ---------------------------------------------------------------------------
def floyd_warshall(graph: Graph, start: str, end: str) -> RouteResult:
    names = list(graph.nodes.keys())
    idx = {n: i for i, n in enumerate(names)}
    n = len(names)
    INF = math.inf

    dist = [[INF] * n for _ in range(n)]
    nxt = [[None] * n for _ in range(n)]
    for i in range(n):
        dist[i][i] = 0
        nxt[i][i] = i
    for u in graph.adjacency:
        for e in graph.adjacency[u]:
            i, j = idx[u], idx[e.to]
            if e.weighted_time_min < dist[i][j]:
                dist[i][j] = e.weighted_time_min
                nxt[i][j] = j

    explored = 0
    for k in range(n):
        for i in range(n):
            for j in range(n):
                explored += 1
                if dist[i][k] + dist[k][j] < dist[i][j]:
                    dist[i][j] = dist[i][k] + dist[k][j]
                    nxt[i][j] = nxt[i][k]

    if start not in idx or end not in idx:
        return RouteResult("floyd_warshall", [], 0, 0, explored, found=False)
    i, j = idx[start], idx[end]
    if nxt[i][j] is None:
        return RouteResult("floyd_warshall", [], 0, 0, explored, found=False)

    path_idx = [i]
    while i != j:
        i = nxt[i][j]
        path_idx.append(i)
    path = [names[p] for p in path_idx]
    d_km, t_min = _path_metrics(graph, path)
    return RouteResult("floyd_warshall", path, d_km, t_min, explored)


ALGORITHMS = {
    "dijkstra": dijkstra,
    "a_star": a_star,
    "bfs": bfs,
    "dfs": dfs,
    "bellman_ford": bellman_ford,
    "floyd_warshall": floyd_warshall,
}


def route(graph: Graph, start: str, destination: str, algorithm: str = "dijkstra") -> RouteResult:
    """Common interface: route(start, destination, algorithm)."""
    fn = ALGORITHMS.get(algorithm)
    if fn is None:
        raise ValueError(f"Unknown algorithm '{algorithm}'. Choices: {list(ALGORITHMS)}")
    return fn(graph, start, destination)
