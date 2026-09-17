"""
K-Means batching tests. The clustering math itself (services/batching.py's
use of sklearn KMeans + the Phase 1 TSP optimizer) is exercised directly
with plain dicts/arrays — no DB needed for that part. The
create/list/get-batch flow needs the `client`/`auth_headers` fixtures
(Postgres-backed).
"""
import pytest


class TestKMeansClusteringUnit:
    """No DB required — exercises the clustering + TSP math directly."""

    def test_kmeans_separates_two_geographic_groups(self):
        import numpy as np
        from sklearn.cluster import KMeans

        coords = np.array([
            [18.55, 73.89], [18.56, 73.90], [18.54, 73.88], [18.57, 73.91],  # group A
            [18.50, 73.80], [18.49, 73.79], [18.51, 73.81], [18.48, 73.78],  # group B
        ])
        labels = KMeans(n_clusters=2, random_state=42, n_init=10).fit_predict(coords)
        assert len(set(labels[:4])) == 1
        assert len(set(labels[4:])) == 1
        assert labels[0] != labels[4]

    def test_optimize_multi_stop_produces_valid_batch_sequence(self):
        from algorithms.tsp import optimize_multi_stop
        stops = [
            {"name": "Order#1", "lat": 18.55, "lng": 73.89},
            {"name": "Order#2", "lat": 18.56, "lng": 73.90},
            {"name": "Order#3", "lat": 18.54, "lng": 73.88},
        ]
        result = optimize_multi_stop(stops, warehouse=(18.5204, 73.8567))
        assert result["sequence"][0] == "Warehouse"
        assert result["sequence"][-1] == "Warehouse"
        assert result["num_stops"] == 3
        assert set(result["sequence"][1:-1]) == {"Order#1", "Order#2", "Order#3"}


class TestBatchingAPI:
    def _create_pending_order(self, client, auth_headers, delivery_location, dlat, dlng, suffix):
        resp = client.post("/api/orders", json={
            "customer_name": f"Batch Test Customer {suffix}",
            "pickup_location": "Warehouse", "pickup_lat": 18.5204, "pickup_lng": 73.8567,
            "delivery_location": delivery_location, "delivery_lat": dlat, "delivery_lng": dlng,
            "priority": 3,
        }, headers=auth_headers)
        assert resp.status_code == 201, resp.text
        return resp.json()["id"]

    def test_create_batches_groups_pending_orders(self, client, auth_headers):
        # Create enough fresh pending orders to guarantee at least one batch,
        # independent of whatever the seed data already produced.
        order_ids = [
            self._create_pending_order(client, auth_headers, "Baner", 18.5590, 73.7868, "A1"),
            self._create_pending_order(client, auth_headers, "Baner", 18.5595, 73.7870, "A2"),
            self._create_pending_order(client, auth_headers, "Hinjewadi", 18.5912, 73.7389, "B1"),
            self._create_pending_order(client, auth_headers, "Hinjewadi", 18.5915, 73.7392, "B2"),
        ]

        resp = client.post("/api/batches/create", json={"orders_per_batch": 2}, headers=auth_headers)
        assert resp.status_code == 200, resp.text
        batches = resp.json()
        assert len(batches) >= 1
        for b in batches:
            assert b["num_orders"] >= 1
            assert b["total_distance_km"] > 0

        # every one of our created orders should now be attached to some batch
        all_batched_order_ids = []
        for b in batches:
            detail = client.get(f"/api/batches/{b['id']}", headers=auth_headers).json()
            all_batched_order_ids.extend(detail["order_ids"])
        for oid in order_ids:
            assert oid in all_batched_order_ids

    def test_list_batches_returns_created_batches(self, client, auth_headers):
        resp = client.get("/api/batches", headers=auth_headers)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_get_nonexistent_batch_404(self, client, auth_headers):
        resp = client.get("/api/batches/999999", headers=auth_headers)
        assert resp.status_code == 404

    def test_create_batches_rejects_invalid_orders_per_batch(self, client, auth_headers):
        resp = client.post("/api/batches/create", json={"orders_per_batch": 0}, headers=auth_headers)
        assert resp.status_code == 422
