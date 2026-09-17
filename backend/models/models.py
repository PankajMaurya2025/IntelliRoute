"""
SQLAlchemy ORM models for IntelliRoute.

Tables: users, locations, orders, drivers, vehicles, route_edges,
deliveries, batches, traffic_events, simulation_runs.
"""
import enum
from datetime import datetime

from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime, ForeignKey,
    Enum as SAEnum, Text, Table
)
from sqlalchemy.orm import relationship

from database import Base


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------
class OrderStatus(str, enum.Enum):
    PENDING = "pending"
    ASSIGNED = "assigned"
    PICKED_UP = "picked_up"
    IN_TRANSIT = "in_transit"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class OrderPriority(int, enum.Enum):
    EMERGENCY = 1
    HIGH = 2
    NORMAL = 3
    LOW = 4


class DriverStatus(str, enum.Enum):
    AVAILABLE = "available"
    ASSIGNED = "assigned"
    ON_ROUTE = "on_route"
    OFFLINE = "offline"


class VehicleStatus(str, enum.Enum):
    AVAILABLE = "available"
    ASSIGNED = "assigned"
    ON_ROUTE = "on_route"
    MAINTENANCE = "maintenance"
    OFFLINE = "offline"


class TrafficLevel(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    SEVERE = "severe"


# ---------------------------------------------------------------------------
# Users
# ---------------------------------------------------------------------------
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, default="admin")
    created_at = Column(DateTime, default=datetime.utcnow)


# ---------------------------------------------------------------------------
# Locations (graph nodes used by the routing engine)
# ---------------------------------------------------------------------------
class Location(Base):
    __tablename__ = "locations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    is_warehouse = Column(Boolean, default=False)


# ---------------------------------------------------------------------------
# Route edges (graph edges used by the routing engine)
# ---------------------------------------------------------------------------
class RouteEdge(Base):
    __tablename__ = "route_edges"

    id = Column(Integer, primary_key=True, index=True)
    from_location = Column(String, ForeignKey("locations.name"), nullable=False)
    to_location = Column(String, ForeignKey("locations.name"), nullable=False)
    distance_km = Column(Float, nullable=False)
    base_travel_time_min = Column(Float, nullable=False)
    traffic_factor = Column(Float, default=1.0)  # multiplier applied to travel time


# ---------------------------------------------------------------------------
# Vehicles
# ---------------------------------------------------------------------------
class Vehicle(Base):
    __tablename__ = "vehicles"

    id = Column(Integer, primary_key=True, index=True)
    vehicle_number = Column(String, unique=True, nullable=False)
    vehicle_type = Column(String, default="bike")  # bike, car, van, truck
    capacity_kg = Column(Float, default=20.0)
    status = Column(SAEnum(VehicleStatus), default=VehicleStatus.AVAILABLE)
    fuel_level = Column(Float, default=100.0)
    current_lat = Column(Float, default=0.0)
    current_lng = Column(Float, default=0.0)
    total_deliveries = Column(Integer, default=0)

    driver = relationship("Driver", back_populates="vehicle", uselist=False)


# ---------------------------------------------------------------------------
# Drivers
# ---------------------------------------------------------------------------
class Driver(Base):
    __tablename__ = "drivers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    phone = Column(String, default="")
    status = Column(SAEnum(DriverStatus), default=DriverStatus.AVAILABLE)
    current_lat = Column(Float, default=0.0)
    current_lng = Column(Float, default=0.0)
    vehicle_id = Column(Integer, ForeignKey("vehicles.id"), nullable=True)
    current_order_id = Column(Integer, ForeignKey("orders.id"), nullable=True)
    total_deliveries = Column(Integer, default=0)
    rating = Column(Float, default=5.0)

    vehicle = relationship("Vehicle", back_populates="driver", foreign_keys=[vehicle_id])
    orders = relationship("Order", back_populates="driver", foreign_keys="Order.assigned_driver_id")


# ---------------------------------------------------------------------------
# Orders
# ---------------------------------------------------------------------------
class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    customer_name = Column(String, nullable=False)

    pickup_location = Column(String, nullable=False)
    pickup_lat = Column(Float, nullable=False)
    pickup_lng = Column(Float, nullable=False)

    delivery_location = Column(String, nullable=False)
    delivery_lat = Column(Float, nullable=False)
    delivery_lng = Column(Float, nullable=False)

    priority = Column(Integer, default=OrderPriority.NORMAL.value)
    package_weight_kg = Column(Float, default=1.0)

    status = Column(SAEnum(OrderStatus), default=OrderStatus.PENDING)
    assigned_driver_id = Column(Integer, ForeignKey("drivers.id"), nullable=True)

    distance_km = Column(Float, nullable=True)
    predicted_eta_min = Column(Float, nullable=True)
    traffic_level = Column(SAEnum(TrafficLevel), default=TrafficLevel.LOW)

    batch_id = Column(Integer, ForeignKey("batches.id"), nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    estimated_delivery_time = Column(DateTime, nullable=True)
    actual_delivery_time = Column(DateTime, nullable=True)

    driver = relationship("Driver", back_populates="orders", foreign_keys=[assigned_driver_id])
    batch = relationship("Batch", back_populates="orders")


# ---------------------------------------------------------------------------
# Deliveries (a completed/active fulfillment record tied to an order)
# ---------------------------------------------------------------------------
class Delivery(Base):
    __tablename__ = "deliveries"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False)
    driver_id = Column(Integer, ForeignKey("drivers.id"), nullable=False)
    route_algorithm = Column(String, default="dijkstra")
    path_json = Column(Text, default="[]")  # JSON-encoded list of location names
    distance_km = Column(Float, default=0.0)
    travel_time_min = Column(Float, default=0.0)
    progress_pct = Column(Float, default=0.0)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)


# ---------------------------------------------------------------------------
# Batches (K-Means grouped nearby orders)
# ---------------------------------------------------------------------------
class Batch(Base):
    __tablename__ = "batches"

    id = Column(Integer, primary_key=True, index=True)
    assigned_driver_id = Column(Integer, ForeignKey("drivers.id"), nullable=True)
    total_distance_km = Column(Float, default=0.0)
    estimated_time_min = Column(Float, default=0.0)
    num_orders = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    orders = relationship("Order", back_populates="batch")


# ---------------------------------------------------------------------------
# Traffic events
# ---------------------------------------------------------------------------
class TrafficEvent(Base):
    __tablename__ = "traffic_events"

    id = Column(Integer, primary_key=True, index=True)
    from_location = Column(String, nullable=False)
    to_location = Column(String, nullable=False)
    level = Column(SAEnum(TrafficLevel), default=TrafficLevel.LOW)
    created_at = Column(DateTime, default=datetime.utcnow)


# ---------------------------------------------------------------------------
# Simulation runs
# ---------------------------------------------------------------------------
class SimulationRun(Base):
    __tablename__ = "simulation_runs"

    id = Column(Integer, primary_key=True, index=True)
    status = Column(String, default="stopped")  # running, paused, stopped
    speed_multiplier = Column(Float, default=1.0)
    started_at = Column(DateTime, nullable=True)
    stopped_at = Column(DateTime, nullable=True)
