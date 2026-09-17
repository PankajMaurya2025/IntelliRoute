"""
Wires the pure-Python SimulationEngine (simulation/engine.py) into FastAPI:
REST endpoints to build legs from the DB and control playback, plus a
WebSocket endpoint that broadcasts engine state once per tick.

NOTE on auth: the REST control endpoints (/api/simulation/*) require a
JWT like every other endpoint in this app. The WebSocket endpoint
(/ws/simulation) intentionally does NOT require auth — validating JWTs
over a WebSocket handshake needs a different mechanism (query-param
token) than the header-based OAuth2PasswordBearer used elsewhere, and
adding that is out of scope for Phase 2. This is a deliberate simplification,
not an oversight: don't expose this deployment publicly without adding it.
"""
import asyncio
from datetime import datetime
from typing import Optional, Set

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from database import get_db, SessionLocal
from models import User, Order, Driver, Vehicle, OrderStatus, DriverStatus, VehicleStatus
from schemas.schemas import SimulationControlResponse
from utils.auth import get_current_user
from services.road_network import get_graph
from algorithms import route as run_route
from simulation.engine import SimulationEngine, DriverLeg

router = APIRouter(tags=["simulation"])

engine = SimulationEngine()
TICK_SECONDS = 1.0
_loop_task: Optional[asyncio.Task] = None


class ConnectionManager:
    def __init__(self):
        self.active: Set[WebSocket] = set()

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.active.add(ws)

    def disconnect(self, ws: WebSocket):
        self.active.discard(ws)

    async def broadcast(self, message: dict):
        dead = []
        for ws in self.active:
            try:
                await ws.send_json(message)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws)


manager = ConnectionManager()


def _build_legs_for_active_orders(db: Session):
    """Finds ASSIGNED/PICKED_UP orders with a driver, resolves a graph route
    pickup->delivery via Dijkstra, and turns each into a DriverLeg."""
    graph = get_graph(db)
    orders = db.query(Order).filter(Order.status.in_([OrderStatus.ASSIGNED, OrderStatus.PICKED_UP])).all()

    legs = []
    for order in orders:
        if not order.assigned_driver_id:
            continue
        driver = db.query(Driver).get(order.assigned_driver_id)
        if not driver:
            continue
        if order.pickup_location not in graph.nodes or order.delivery_location not in graph.nodes:
            continue

        result = run_route(graph, order.pickup_location, order.delivery_location, "dijkstra")
        if not result.found:
            continue
        waypoints = [(graph.nodes[name].lat, graph.nodes[name].lng) for name in result.path]

        speed = 25.0
        if driver.vehicle_id:
            vehicle = db.query(Vehicle).get(driver.vehicle_id)
            if vehicle:
                speed = {"bike": 32.0, "car": 28.0, "van": 20.0, "truck": 18.0}.get(vehicle.vehicle_type, 25.0)

        leg = DriverLeg(
            leg_id=f"order-{order.id}", driver_id=driver.id, order_id=order.id,
            driver_name=driver.name, waypoints=waypoints, speed_kmph=speed,
        )
        legs.append((leg, order, driver))
    return legs


def _ensure_loop_running():
    global _loop_task
    if _loop_task is None or _loop_task.done():
        _loop_task = asyncio.create_task(_simulation_loop())


async def _simulation_loop():
    while engine.status in ("running", "paused"):
        if engine.status == "running":
            completed = engine.tick(TICK_SECONDS)
            if completed:
                _finalize_completed_legs(completed)
            await manager.broadcast(engine.get_state())
        await asyncio.sleep(TICK_SECONDS)


def _finalize_completed_legs(completed: list):
    """Opens its own DB session (this runs outside any request context) to
    mark completed deliveries: order -> DELIVERED, driver/vehicle -> AVAILABLE."""
    db = SessionLocal()
    try:
        for leg_state in completed:
            order = db.query(Order).get(leg_state["order_id"])
            driver = db.query(Driver).get(leg_state["driver_id"])
            if order:
                order.status = OrderStatus.DELIVERED
                order.actual_delivery_time = datetime.utcnow()
            if driver:
                driver.status = DriverStatus.AVAILABLE
                driver.current_order_id = None
                driver.total_deliveries = (driver.total_deliveries or 0) + 1
                if driver.vehicle_id:
                    vehicle = db.query(Vehicle).get(driver.vehicle_id)
                    if vehicle:
                        vehicle.status = VehicleStatus.AVAILABLE
                        vehicle.total_deliveries = (vehicle.total_deliveries or 0) + 1
        db.commit()
    finally:
        db.close()


# ---------------------------------------------------------------------------
# REST controls
# ---------------------------------------------------------------------------
@router.post("/api/simulation/start", response_model=SimulationControlResponse)
async def start_simulation(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    # NOTE: this endpoint is `async def` (unlike the other REST endpoints in this
    # app) specifically so `_ensure_loop_running()` -> `asyncio.create_task()`
    # executes on the real event loop. FastAPI runs plain `def` endpoints in a
    # worker thread pool, where there is no running loop to attach a task to —
    # calling create_task() from there raises "no running event loop". The DB
    # calls below are still sync/blocking; for this app's scale that's an
    # acceptable, deliberate trade-off rather than an oversight.
    legs = _build_legs_for_active_orders(db)
    if not legs:
        raise HTTPException(
            status_code=404,
            detail="No assigned/picked-up orders with a resolvable route to simulate. Assign some orders first.",
        )

    engine.clear()
    for leg, order, driver in legs:
        engine.add_leg(leg)
        order.status = OrderStatus.IN_TRANSIT
        driver.status = DriverStatus.ON_ROUTE
        if driver.vehicle_id:
            vehicle = db.query(Vehicle).get(driver.vehicle_id)
            if vehicle:
                vehicle.status = VehicleStatus.ON_ROUTE
    db.commit()

    engine.start()
    _ensure_loop_running()
    return SimulationControlResponse(
        status=engine.status, active_legs=len(engine.legs),
        message=f"Simulation started with {len(legs)} active deliveries",
    )


@router.post("/api/simulation/pause", response_model=SimulationControlResponse)
def pause_simulation(current_user: User = Depends(get_current_user)):
    engine.pause()
    return SimulationControlResponse(status=engine.status, active_legs=len(engine.legs), message="Simulation paused")


@router.post("/api/simulation/resume", response_model=SimulationControlResponse)
async def resume_simulation(current_user: User = Depends(get_current_user)):
    # async def for the same reason as start_simulation() above.
    if not engine.legs:
        raise HTTPException(status_code=400, detail="No simulation in progress to resume")
    engine.resume()
    _ensure_loop_running()
    return SimulationControlResponse(status=engine.status, active_legs=len(engine.legs), message="Simulation resumed")


@router.post("/api/simulation/stop", response_model=SimulationControlResponse)
def stop_simulation(current_user: User = Depends(get_current_user)):
    engine.stop()
    return SimulationControlResponse(status=engine.status, active_legs=len(engine.legs), message="Simulation stopped")


@router.post("/api/simulation/reset", response_model=SimulationControlResponse)
def reset_simulation(current_user: User = Depends(get_current_user)):
    engine.reset()
    return SimulationControlResponse(status=engine.status, active_legs=0, message="Simulation reset")


@router.get("/api/simulation/state")
def get_simulation_state(current_user: User = Depends(get_current_user)):
    return engine.get_state()


# ---------------------------------------------------------------------------
# WebSocket — live position/progress/ETA stream
# ---------------------------------------------------------------------------
@router.websocket("/ws/simulation")
async def simulation_ws(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        await websocket.send_json(engine.get_state())
        while True:
            # Blocks until the client sends something or disconnects; the app
            # doesn't require inbound messages, this just detects disconnects.
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
