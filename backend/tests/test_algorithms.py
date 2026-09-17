"""
Unit tests for the DSA routing algorithms — run against a small graph
built entirely in-memory, independent of the database.
"""
import math
import pytest

from algorithms import Graph, route, dijkstra, a_star, bfs, dfs, bellman_ford, floyd_warshall
from algorithms.priority_queue import OrderPriorityQueue
from algorithms.tsp import optimize_multi_stop, nearest_neighbor, two_opt, _total_distance


def build_test_graph() -> Graph:
    g = Graph()
    g.add_node("Warehouse", 18.5204, 73.8567)
    g.add_node("A", 18.5300, 73.8700)
    g.add_node("B", 18.5400, 73.8800)
    g.add_node("CustomerA", 18.5500, 73.8900)
    g.add_edge("Warehouse", "A", 2.0, 5.0)
    g.add_edge("A", "B", 3.0, 6.0)
    g.add_edge("B", "CustomerA", 1.5, 4.0)
    g.add_edge("Warehouse", "CustomerA", 10.0, 20.0)  # longer direct edge
    return g


class TestShortestPathAlgorithms:
    @pytest.mark.parametrize("algo", ["dijkstra", "a_star", "bellman_ford", "floyd_warshall"])
    def test_finds_optimal_short_path(self, algo):
        """All optimal (weighted) algorithms must find the 15-min path via A->B, not the 20-min direct edge."""
        g = build_test_graph()
        result = route(g, "Warehouse", "CustomerA", algo)
        assert result.found is True
        assert result.path == ["Warehouse", "A", "B", "CustomerA"]
        assert result.travel_time_min == pytest.approx(15.0, abs=0.01)
        assert result.distance_km == pytest.approx(6.5, abs=0.01)

    def test_bfs_finds_fewest_hops_not_necessarily_shortest(self):
        g = build_test_graph()
        result = bfs(g, "Warehouse", "CustomerA")
        assert result.found is True
        # BFS is unweighted — it should prefer the 1-hop direct edge over the 3-hop path
        assert result.path == ["Warehouse", "CustomerA"]

    def test_dfs_finds_a_valid_path(self):
        g = build_test_graph()
        result = dfs(g, "Warehouse", "CustomerA")
        assert result.found is True
        assert result.path[0] == "Warehouse"
        assert result.path[-1] == "CustomerA"

    def test_no_route_between_disconnected_nodes(self):
        g = Graph()
        g.add_node("X", 0, 0)
        g.add_node("Y", 1, 1)
        # no edge added between X and Y
        result = dijkstra(g, "X", "Y")
        assert result.found is False
        assert result.path == []

    def test_route_common_interface_rejects_unknown_algorithm(self):
        g = build_test_graph()
        with pytest.raises(ValueError):
            route(g, "Warehouse", "CustomerA", "not_a_real_algorithm")

    def test_traffic_factor_increases_travel_time(self):
        g = build_test_graph()
        baseline = dijkstra(g, "Warehouse", "CustomerA")
        g.set_traffic_factor("Warehouse", "A", 3.0)  # heavy traffic on first leg
        with_traffic = dijkstra(g, "Warehouse", "CustomerA")
        assert with_traffic.travel_time_min > baseline.travel_time_min


class TestPriorityQueue:
    def test_pops_in_priority_order_not_insertion_order(self):
        pq = OrderPriorityQueue()
        pq.push(order_id=201, priority=3)  # Normal
        pq.push(order_id=202, priority=1)  # Emergency
        pq.push(order_id=203, priority=2)  # High
        assert pq.pop() == 202
        assert pq.pop() == 203
        assert pq.pop() == 201
        assert pq.pop() is None

    def test_equal_priority_is_fifo(self):
        pq = OrderPriorityQueue()
        pq.push(1, priority=2)
        pq.push(2, priority=2)
        pq.push(3, priority=2)
        assert [pq.pop(), pq.pop(), pq.pop()] == [1, 2, 3]

    def test_remove_invalidates_entry(self):
        pq = OrderPriorityQueue()
        pq.push(1, priority=1)
        pq.push(2, priority=2)
        pq.remove(1)
        assert pq.pop() == 2
        assert len(pq) == 0

    def test_peek_all_reflects_valid_entries_only(self):
        pq = OrderPriorityQueue()
        pq.push(1, priority=2)
        pq.push(2, priority=1)
        pq.remove(1)
        entries = pq.peek_all()
        assert len(entries) == 1
        assert entries[0]["order_id"] == 2


class TestTSP:
    def test_nearest_neighbor_visits_all_stops(self):
        coords = [(0, 0), (0, 1), (1, 1), (5, 5)]
        order = nearest_neighbor(coords)
        assert sorted(order) == [0, 1, 2, 3]
        assert order[0] == 0  # starts at warehouse

    def test_two_opt_never_worsens_the_route(self):
        coords = [(0, 0), (0, 5), (5, 5), (5, 0), (2, 2)]
        initial = nearest_neighbor(coords)
        improved = two_opt(initial, coords)
        assert _total_distance(improved, coords) <= _total_distance(initial, coords) + 1e-9

    def test_optimize_multi_stop_returns_full_sequence(self):
        stops = [
            {"name": "CustomerA", "lat": 18.55, "lng": 73.89},
            {"name": "CustomerB", "lat": 18.50, "lng": 73.80},
            {"name": "CustomerC", "lat": 18.56, "lng": 73.91},
        ]
        result = optimize_multi_stop(stops, warehouse=(18.5204, 73.8567))
        assert result["sequence"][0] == "Warehouse"
        assert result["sequence"][-1] == "Warehouse"
        assert result["num_stops"] == 3
        assert result["total_distance_km"] > 0
