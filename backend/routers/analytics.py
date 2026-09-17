from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from database import get_db
from models import User, Order, Driver, Vehicle, OrderStatus, DriverStatus, VehicleStatus
from schemas.schemas import AnalyticsSummary, PriorityBreakdown
from utils.auth import get_current_user

router = APIRouter(prefix="/api/analytics", tags=["analytics"])

ACTIVE_STATUSES = [OrderStatus.ASSIGNED, OrderStatus.PICKED_UP, OrderStatus.IN_TRANSIT]


@router.get("/summary", response_model=AnalyticsSummary)
def analytics_summary(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    total_orders = db.query(func.count(Order.id)).scalar() or 0
    pending_orders = db.query(func.count(Order.id)).filter(Order.status == OrderStatus.PENDING).scalar() or 0
    active_deliveries = db.query(func.count(Order.id)).filter(Order.status.in_(ACTIVE_STATUSES)).scalar() or 0
    delivered_orders = db.query(func.count(Order.id)).filter(Order.status == OrderStatus.DELIVERED).scalar() or 0
    cancelled_orders = db.query(func.count(Order.id)).filter(Order.status == OrderStatus.CANCELLED).scalar() or 0

    total_drivers = db.query(func.count(Driver.id)).scalar() or 0
    available_drivers = db.query(func.count(Driver.id)).filter(Driver.status == DriverStatus.AVAILABLE).scalar() or 0
    driver_utilization_pct = round(((total_drivers - available_drivers) / total_drivers) * 100, 1) if total_drivers else 0.0

    total_vehicles = db.query(func.count(Vehicle.id)).scalar() or 0
    available_vehicles = db.query(func.count(Vehicle.id)).filter(Vehicle.status == VehicleStatus.AVAILABLE).scalar() or 0
    vehicle_utilization_pct = round(((total_vehicles - available_vehicles) / total_vehicles) * 100, 1) if total_vehicles else 0.0

    avg_eta = db.query(func.avg(Order.predicted_eta_min)).filter(Order.predicted_eta_min.isnot(None)).scalar()
    total_distance = db.query(func.sum(Order.distance_km)).filter(Order.distance_km.isnot(None)).scalar()

    priority_counts = {p: 0 for p in (1, 2, 3, 4)}
    rows = db.query(Order.priority, func.count(Order.id)).group_by(Order.priority).all()
    for priority, count in rows:
        priority_counts[priority] = count

    return AnalyticsSummary(
        total_orders=total_orders,
        pending_orders=pending_orders,
        active_deliveries=active_deliveries,
        delivered_orders=delivered_orders,
        cancelled_orders=cancelled_orders,
        total_drivers=total_drivers,
        available_drivers=available_drivers,
        driver_utilization_pct=driver_utilization_pct,
        total_vehicles=total_vehicles,
        available_vehicles=available_vehicles,
        vehicle_utilization_pct=vehicle_utilization_pct,
        average_eta_min=round(float(avg_eta), 2) if avg_eta is not None else 0.0,
        total_distance_km=round(float(total_distance), 2) if total_distance is not None else 0.0,
        priority_breakdown=PriorityBreakdown(
            emergency=priority_counts[1],
            high=priority_counts[2],
            normal=priority_counts[3],
            low=priority_counts[4],
        ),
    )
