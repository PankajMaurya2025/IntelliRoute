"""
Simulation tests, split into:

1. Pure engine unit tests (simulation/engine.py) — no DB, no FastAPI.
2. REST control-endpoint integration tests — DB-backed.
3. A WebSocket smoke test using FastAPI's TestClient.websocket_connect,
   which exercises the real ASGI WebSocket path (not a mock).
"""
import pytest


class TestSimulationEngineUnit:
    def test_leg_advances_and_interpolates_position(self):
        from simulation.engine import SimulationEngine, DriverLeg

        waypoints = [(18.5204, 73.8567), (18.5300, 73.8700), (18.5590, 73.7868)]
        leg = DriverLeg(leg_id="t1", driver_id=1, order_id=1, driver_name="Test Driver",
                         waypoints=waypoints, speed_kmph=60.0)
        assert leg.total_km > 0

        engine = SimulationEngine()
        engine.add_leg(leg)
        engine.start()

        engine.tick(dt_seconds=10)
        assert leg.traveled_km > 0
        assert 0 < leg.progress_pct() < 100
        assert leg.status == "running"

    def test_leg_completes_when_distance_covered(self):
        from simulation.engine import SimulationEngine, DriverLeg

        waypoints = [(18.5204, 73.8567), (18.5590, 73.7868)]
        leg = DriverLeg(leg_id="t2", driver_id=1, order_id=2, driver_name="Test Driver",
                         waypoints=waypoints, speed_kmph=200.0)  # fast, to finish quickly
        engine = SimulationEngine()
        engine.add_leg(leg)
        engine.start()

        completed = []
        for _ in range(50):
            completed += engine.tick(dt_seconds=10)
            if leg.status == "completed":
                break

        assert leg.status == "completed"
        assert abs(leg.progress_pct() - 100.0) < 0.01
        assert any(c["leg_id"] == "t2" for c in completed)

    def test_paused_engine_does_not_advance(self):
        from simulation.engine import SimulationEngine, DriverLeg

        leg = DriverLeg(leg_id="t3", driver_id=1, order_id=3, driver_name="Test Driver",
                         waypoints=[(0, 0), (1, 1)], speed_kmph=50.0)
        engine = SimulationEngine()
        engine.add_leg(leg)
        engine.start()
        engine.pause()

        completed = engine.tick(dt_seconds=10)
        assert completed == []
        assert leg.traveled_km == 0

    def test_reset_clears_all_legs(self):
        from simulation.engine import SimulationEngine, DriverLeg

        engine = SimulationEngine()
        engine.add_leg(DriverLeg(leg_id="t4", driver_id=1, order_id=4, driver_name="X",
                                  waypoints=[(0, 0), (1, 1)]))
        engine.start()
        engine.reset()
        assert len(engine.legs) == 0
        assert engine.status == "stopped"


class TestSimulationAPI:
    def _create_and_assign_order(self, client, auth_headers):
        create_resp = client.post("/api/orders", json={
            "customer_name": "Simulation Test Customer",
            "pickup_location": "Warehouse", "pickup_lat": 18.5204, "pickup_lng": 73.8567,
            "delivery_location": "Baner", "delivery_lat": 18.5590, "delivery_lng": 73.7868,
            "priority": 1,
        }, headers=auth_headers)
        assert create_resp.status_code == 201, create_resp.text
        order_id = create_resp.json()["id"]

        dispatch_resp = client.post("/api/orders/dispatch-next", headers=auth_headers)
        # dispatch-next dispatches whatever is highest priority in the queue, which
        # given priority=1 (Emergency) above should be our order, but fall back to
        # manual assignment if some other emergency order beat it to the front.
        if dispatch_resp.status_code == 200 and dispatch_resp.json()["assigned_order_id"] == order_id:
            return order_id

        drivers = client.get("/api/drivers", headers=auth_headers).json()
        available = next((d for d in drivers if d["status"] == "available"), None)
        if available:
            client.put(f"/api/orders/{order_id}", json={
                "status": "assigned", "assigned_driver_id": available["id"],
            }, headers=auth_headers)
        return order_id

    def test_full_start_pause_resume_stop_reset_cycle(self, client, auth_headers):
        client.post("/api/simulation/reset", headers=auth_headers)
        self._create_and_assign_order(client, auth_headers)

        start_resp = client.post("/api/simulation/start", headers=auth_headers)
        assert start_resp.status_code == 200, start_resp.text
        assert start_resp.json()["status"] == "running"
        assert start_resp.json()["active_legs"] >= 1

        state = client.get("/api/simulation/state", headers=auth_headers).json()
        assert state["status"] == "running"

        pause_resp = client.post("/api/simulation/pause", headers=auth_headers)
        assert pause_resp.json()["status"] == "paused"

        resume_resp = client.post("/api/simulation/resume", headers=auth_headers)
        assert resume_resp.status_code == 200
        assert resume_resp.json()["status"] == "running"

        stop_resp = client.post("/api/simulation/stop", headers=auth_headers)
        assert stop_resp.json()["status"] == "stopped"

        reset_resp = client.post("/api/simulation/reset", headers=auth_headers)
        assert reset_resp.json()["active_legs"] == 0

    def test_resume_without_active_simulation_returns_400(self, client, auth_headers):
        client.post("/api/simulation/reset", headers=auth_headers)
        resp = client.post("/api/simulation/resume", headers=auth_headers)
        assert resp.status_code == 400

    def test_simulation_endpoints_require_auth(self, client):
        assert client.get("/api/simulation/state").status_code == 401
        assert client.post("/api/simulation/start").status_code == 401


class TestSimulationWebSocket:
    def test_websocket_sends_initial_state_on_connect(self, client):
        with client.websocket_connect("/ws/simulation") as ws:
            data = ws.receive_json()
            assert "status" in data
            assert "active_legs" in data
            assert "completed_legs" in data
