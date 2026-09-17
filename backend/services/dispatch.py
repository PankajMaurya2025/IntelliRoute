"""
Dispatch service: wraps the OrderPriorityQueue and implements automatic
driver assignment (nearest available driver with sufficient vehicle
capacity).
"""
import math
from typing import Optional
from sqlalchemy.orm import Session

from algorithms import OrderPriorityQueue
from models import Order, Driver, Vehicle, DriverStatus, VehicleStatus, OrderStatus

# Single shared in-memory priority queue for the process lifetime.
priority_queue = OrderPriorityQueue()


def _haversine_km(lat1, lng1, lat2, lng2) -> float:
    R = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlng = math.radians(lng2 - lng1)
    h = math.sin(dlat / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlng / 2) ** 2
    return 2 * R * math.asin(min(1.0, math.sqrt(h)))


def enqueue_order(order: Order):
    priority_queue.push(order.id, order.priority)


def find_best_driver(db: Session, order: Order) -> Optional[Driver]:
    """Pick the closest available driver whose vehicle can carry the package."""
    candidates = db.query(Driver).filter(Driver.status == DriverStatus.AVAILABLE).all()
    best_driver, best_dist = None, math.inf

    for driver in candidates:
        if driver.vehicle_id:
            vehicle = db.query(Vehicle).get(driver.vehicle_id)
            if vehicle is None or vehicle.status != VehicleStatus.AVAILABLE:
                continue
            if vehicle.capacity_kg < order.package_weight_kg:
                continue
        dist = _haversine_km(driver.current_lat, driver.current_lng, order.pickup_lat, order.pickup_lng)
        if dist < best_dist:
            best_dist = dist
            best_driver = driver

    return best_driver


def assign_order_to_driver(db: Session, order: Order, driver: Driver):
    order.assigned_driver_id = driver.id
    order.status = OrderStatus.ASSIGNED
    driver.status = DriverStatus.ASSIGNED
    driver.current_order_id = order.id
    if driver.vehicle_id:
        vehicle = db.query(Vehicle).get(driver.vehicle_id)
        if vehicle:
            vehicle.status = VehicleStatus.ASSIGNED
    priority_queue.remove(order.id)
    db.commit()


def auto_dispatch_next(db: Session) -> Optional[Order]:
    """Pop the highest-priority pending order and assign it if a driver is free."""
    order_id = None
    for entry in priority_queue.peek_all():
        candidate_order = db.query(Order).get(entry["order_id"])
        if candidate_order and candidate_order.status == OrderStatus.PENDING:
            order_id = entry["order_id"]
            break
    if order_id is None:
        return None

    order = db.query(Order).get(order_id)
    driver = find_best_driver(db, order)
    if driver is None:
        return None

    assign_order_to_driver(db, order, driver)
    return order
