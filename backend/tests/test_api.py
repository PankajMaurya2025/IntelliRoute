"""
Integration tests hitting the real FastAPI app + SQLite test database
(seeded automatically via utils.seed on app startup).
"""


class TestAuth:
    def test_login_with_seeded_demo_user_succeeds(self, client):
        resp = client.post("/api/auth/login", json={"email": "admin@intelliroute.com", "password": "Admin@123"})
        assert resp.status_code == 200
        body = resp.json()
        assert "access_token" in body
        assert body["user"]["email"] == "admin@intelliroute.com"

    def test_login_with_wrong_password_fails(self, client):
        resp = client.post("/api/auth/login", json={"email": "admin@intelliroute.com", "password": "wrong"})
        assert resp.status_code == 401

    def test_signup_then_login_new_user(self, client):
        resp = client.post("/api/auth/signup", json={
            "name": "Test User", "email": "test_user_1@example.com", "password": "Str0ngPass!"
        })
        assert resp.status_code == 201
        assert resp.json()["user"]["email"] == "test_user_1@example.com"

        login = client.post("/api/auth/login", json={"email": "test_user_1@example.com", "password": "Str0ngPass!"})
        assert login.status_code == 200

    def test_signup_duplicate_email_rejected(self, client):
        resp = client.post("/api/auth/signup", json={
            "name": "Dup", "email": "admin@intelliroute.com", "password": "whatever123"
        })
        assert resp.status_code == 400

    def test_protected_route_requires_token(self, client):
        resp = client.get("/api/orders")
        assert resp.status_code == 401


class TestOrders:
    def test_seed_created_at_least_ten_orders(self, client, auth_headers):
        resp = client.get("/api/orders", headers=auth_headers)
        assert resp.status_code == 200
        orders = resp.json()
        assert len(orders) >= 10

    def test_create_order_appears_in_priority_queue(self, client, auth_headers):
        payload = {
            "customer_name": "Priority Test Customer",
            "pickup_location": "Warehouse",
            "pickup_lat": 18.5204, "pickup_lng": 73.8567,
            "delivery_location": "Baner",
            "delivery_lat": 18.5590, "delivery_lng": 73.7868,
            "priority": 1,
            "package_weight_kg": 2.0,
        }
        resp = client.post("/api/orders", json=payload, headers=auth_headers)
        assert resp.status_code == 201
        order_id = resp.json()["id"]

        pq_resp = client.get("/api/orders/priority-queue", headers=auth_headers)
        assert pq_resp.status_code == 200
        ids_in_queue = [e["order_id"] for e in pq_resp.json()]
        assert order_id in ids_in_queue

    def test_create_order_rejects_invalid_priority(self, client, auth_headers):
        payload = {
            "customer_name": "Bad Priority",
            "pickup_location": "Warehouse", "pickup_lat": 18.5, "pickup_lng": 73.8,
            "delivery_location": "Baner", "delivery_lat": 18.5, "delivery_lng": 73.7,
            "priority": 9,
        }
        resp = client.post("/api/orders", json=payload, headers=auth_headers)
        assert resp.status_code == 422

    def test_get_nonexistent_order_returns_404(self, client, auth_headers):
        resp = client.get("/api/orders/999999", headers=auth_headers)
        assert resp.status_code == 404

    def test_update_order_status(self, client, auth_headers):
        create_resp = client.post("/api/orders", json={
            "customer_name": "Update Test",
            "pickup_location": "Warehouse", "pickup_lat": 18.52, "pickup_lng": 73.85,
            "delivery_location": "Kothrud", "delivery_lat": 18.5074, "delivery_lng": 73.8077,
            "priority": 3,
        }, headers=auth_headers)
        order_id = create_resp.json()["id"]

        update_resp = client.put(f"/api/orders/{order_id}", json={"status": "cancelled"}, headers=auth_headers)
        assert update_resp.status_code == 200
        assert update_resp.json()["status"] == "cancelled"


class TestDriversAndVehicles:
    def test_seed_created_five_drivers_and_vehicles(self, client, auth_headers):
        drivers = client.get("/api/drivers", headers=auth_headers).json()
        vehicles = client.get("/api/vehicles", headers=auth_headers).json()
        assert len(drivers) == 5
        assert len(vehicles) == 5

    def test_create_vehicle_then_driver(self, client, auth_headers):
        v_resp = client.post("/api/vehicles", json={
            "vehicle_number": "TEST-999", "vehicle_type": "bike", "capacity_kg": 10.0
        }, headers=auth_headers)
        assert v_resp.status_code == 201
        vehicle_id = v_resp.json()["id"]

        d_resp = client.post("/api/drivers", json={
            "name": "Test Driver", "phone": "123", "vehicle_id": vehicle_id,
            "current_lat": 18.52, "current_lng": 73.85,
        }, headers=auth_headers)
        assert d_resp.status_code == 201
        assert d_resp.json()["vehicle_id"] == vehicle_id

    def test_duplicate_vehicle_number_rejected(self, client, auth_headers):
        resp = client.post("/api/vehicles", json={"vehicle_number": "PUN-BK-101"}, headers=auth_headers)
        assert resp.status_code == 400


class TestRoutingEngine:
    def test_optimize_route_dijkstra(self, client, auth_headers):
        resp = client.post("/api/routes/optimize", json={
            "start": "Warehouse", "destination": "Hinjewadi", "algorithm": "dijkstra"
        }, headers=auth_headers)
        assert resp.status_code == 200
        body = resp.json()
        assert body["found"] is True
        assert body["path"][0] == "Warehouse"
        assert body["path"][-1] == "Hinjewadi"
        assert body["distance"] > 0

    def test_optimize_route_all_algorithms_reach_destination(self, client, auth_headers):
        for algo in ["dijkstra", "a_star", "bfs", "dfs", "bellman_ford", "floyd_warshall"]:
            resp = client.post("/api/routes/optimize", json={
                "start": "Warehouse", "destination": "Viman Nagar", "algorithm": algo
            }, headers=auth_headers)
            assert resp.status_code == 200, f"{algo} failed: {resp.text}"
            assert resp.json()["path"][-1] == "Viman Nagar"

    def test_optimize_route_unknown_algorithm_rejected(self, client, auth_headers):
        resp = client.post("/api/routes/optimize", json={
            "start": "Warehouse", "destination": "Baner", "algorithm": "quantum_teleport"
        }, headers=auth_headers)
        assert resp.status_code == 422

    def test_optimize_route_unknown_location_404(self, client, auth_headers):
        resp = client.post("/api/routes/optimize", json={
            "start": "Nonexistent Place", "destination": "Baner", "algorithm": "dijkstra"
        }, headers=auth_headers)
        assert resp.status_code == 404

    def test_list_algorithms_endpoint(self, client, auth_headers):
        resp = client.get("/api/routes/algorithms", headers=auth_headers)
        assert resp.status_code == 200
        algos = resp.json()["algorithms"]
        for expected in ["dijkstra", "a_star", "bfs", "dfs", "bellman_ford", "floyd_warshall"]:
            assert expected in algos
