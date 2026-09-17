from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, ConfigDict


# ---------------- Auth ----------------
class UserSignup(BaseModel):
    name: str
    email: EmailStr
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    email: str
    role: str


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


# ---------------- Orders ----------------
class OrderCreate(BaseModel):
    customer_name: str
    pickup_location: str
    pickup_lat: float
    pickup_lng: float
    delivery_location: str
    delivery_lat: float
    delivery_lng: float
    priority: int = 3
    package_weight_kg: float = 1.0


class OrderUpdate(BaseModel):
    status: Optional[str] = None
    assigned_driver_id: Optional[int] = None
    priority: Optional[int] = None


class OrderOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    customer_name: str
    pickup_location: str
    pickup_lat: float
    pickup_lng: float
    delivery_location: str
    delivery_lat: float
    delivery_lng: float
    priority: int
    package_weight_kg: float
    status: str
    assigned_driver_id: Optional[int]
    distance_km: Optional[float]
    predicted_eta_min: Optional[float]
    traffic_level: str
    batch_id: Optional[int]
    created_at: datetime
    estimated_delivery_time: Optional[datetime]
    actual_delivery_time: Optional[datetime]


# ---------------- Drivers / Vehicles ----------------
class DriverCreate(BaseModel):
    name: str
    phone: str = ""
    vehicle_id: Optional[int] = None
    current_lat: float = 0.0
    current_lng: float = 0.0


class DriverUpdate(BaseModel):
    status: Optional[str] = None
    current_lat: Optional[float] = None
    current_lng: Optional[float] = None
    vehicle_id: Optional[int] = None


class DriverOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    phone: str
    status: str
    current_lat: float
    current_lng: float
    vehicle_id: Optional[int]
    current_order_id: Optional[int]
    total_deliveries: int
    rating: float


class VehicleCreate(BaseModel):
    vehicle_number: str
    vehicle_type: str = "bike"
    capacity_kg: float = 20.0


class VehicleUpdate(BaseModel):
    status: Optional[str] = None
    fuel_level: Optional[float] = None
    current_lat: Optional[float] = None
    current_lng: Optional[float] = None


class VehicleOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    vehicle_number: str
    vehicle_type: str
    capacity_kg: float
    status: str
    fuel_level: float
    current_lat: float
    current_lng: float
    total_deliveries: int


# ---------------- Routing ----------------
class RouteRequest(BaseModel):
    start: str
    destination: str
    algorithm: str = "dijkstra"


class RouteResponse(BaseModel):
    algorithm: str
    path: List[str]
    distance: float
    travel_time: float
    nodes_explored: int
    found: bool


# ---------------- ML ----------------
class ETARequest(BaseModel):
    distance_km: float
    traffic_level: str = "low"
    num_stops: int = 1
    priority: int = 3
    package_weight_kg: float = 1.0
    hour_of_day: int = 12
    day_of_week: int = 1


class ETAResponse(BaseModel):
    predicted_eta_minutes: float


class TrainModelResponse(BaseModel):
    trained: bool
    mae_minutes: float
    r2_score: float
    num_train_samples: int
    num_test_samples: int
    feature_importances: dict


# ---------------- Batching ----------------
class BatchCreateRequest(BaseModel):
    orders_per_batch: int = 4


class BatchOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    assigned_driver_id: Optional[int]
    total_distance_km: float
    estimated_time_min: float
    num_orders: int
    created_at: datetime


class BatchDetailOut(BatchOut):
    order_ids: List[int]


# ---------------- Simulation ----------------
class SimulationControlResponse(BaseModel):
    status: str
    active_legs: int
    message: str


# ---------------- Analytics ----------------
class PriorityBreakdown(BaseModel):
    emergency: int
    high: int
    normal: int
    low: int


class AnalyticsSummary(BaseModel):
    total_orders: int
    pending_orders: int
    active_deliveries: int
    delivered_orders: int
    cancelled_orders: int
    total_drivers: int
    available_drivers: int
    driver_utilization_pct: float
    total_vehicles: int
    available_vehicles: int
    vehicle_utilization_pct: float
    average_eta_min: float
    total_distance_km: float
    priority_breakdown: PriorityBreakdown
