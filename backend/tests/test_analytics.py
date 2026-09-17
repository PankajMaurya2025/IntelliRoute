"""
Analytics endpoint tests — all require the DB-backed `client`/`auth_headers`
fixtures since they aggregate real seeded data.
"""


class TestAnalyticsSummary:
    def test_summary_endpoint_returns_expected_shape(self, client, auth_headers):
        resp = client.get("/api/analytics/summary", headers=auth_headers)
        assert resp.status_code == 200
        body = resp.json()

        expected_keys = {
            "total_orders", "pending_orders", "active_deliveries", "delivered_orders",
            "cancelled_orders", "total_drivers", "available_drivers", "driver_utilization_pct",
            "total_vehicles", "available_vehicles", "vehicle_utilization_pct",
            "average_eta_min", "total_distance_km", "priority_breakdown",
        }
        assert expected_keys.issubset(body.keys())

    def test_total_orders_matches_order_count(self, client, auth_headers):
        summary = client.get("/api/analytics/summary", headers=auth_headers).json()
        orders = client.get("/api/orders", headers=auth_headers).json()
        assert summary["total_orders"] >= len(orders) or summary["total_orders"] == len(orders)
        # (>= because pagination isn't implemented on GET /api/orders in Phase 1/2;
        #  both should currently return the full set, so equality is the real expectation)
        assert summary["total_orders"] == len(orders)

    def test_priority_breakdown_sums_to_total_orders(self, client, auth_headers):
        summary = client.get("/api/analytics/summary", headers=auth_headers).json()
        breakdown = summary["priority_breakdown"]
        total_from_breakdown = sum(breakdown.values())
        assert total_from_breakdown == summary["total_orders"]

    def test_driver_utilization_is_a_valid_percentage(self, client, auth_headers):
        summary = client.get("/api/analytics/summary", headers=auth_headers).json()
        assert 0.0 <= summary["driver_utilization_pct"] <= 100.0
        assert 0.0 <= summary["vehicle_utilization_pct"] <= 100.0

    def test_status_counts_do_not_exceed_total_orders(self, client, auth_headers):
        summary = client.get("/api/analytics/summary", headers=auth_headers).json()
        status_sum = (
            summary["pending_orders"] + summary["active_deliveries"]
            + summary["delivered_orders"] + summary["cancelled_orders"]
        )
        assert status_sum == summary["total_orders"]

    def test_summary_requires_auth(self, client):
        resp = client.get("/api/analytics/summary")
        assert resp.status_code == 401
