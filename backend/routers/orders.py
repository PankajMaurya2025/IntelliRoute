from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from models import Order, OrderStatus, User
from schemas.schemas import OrderCreate, OrderUpdate, OrderOut
from utils.auth import get_current_user
from services import dispatch
from services.road_network import get_graph
from algorithms import route as run_route


router = APIRouter(prefix="/api/orders", tags=["orders"])


@router.post("", response_model=OrderOut, status_code=status.HTTP_201_CREATED)
def create_order(
    payload: OrderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # Validate priority
    if payload.priority not in (1, 2, 3, 4):
        raise HTTPException(
            status_code=422,
            detail="priority must be 1 (Emergency)-4 (Low)",
        )

    # Create order as PENDING
    order = Order(
        **payload.model_dump(),
        status=OrderStatus.PENDING,
    )

    db.add(order)
    db.commit()
    db.refresh(order)

    # Calculate route distance if graph locations exist
    try:
        graph = get_graph(db)

        if (
            payload.pickup_location in graph.nodes
            and payload.delivery_location in graph.nodes
        ):
            result = run_route(
                graph,
                payload.pickup_location,
                payload.delivery_location,
                "dijkstra",
            )

            if result.found:
                order.distance_km = result.distance_km
                db.commit()
                db.refresh(order)

    except Exception:
        # Route calculation should not stop order creation
        pass

    # Add order to priority queue
    dispatch.enqueue_order(order)

    # Automatically try to assign the order
    # to the nearest available driver with a suitable vehicle.
    try:
        dispatch.auto_dispatch_next(db)
        db.refresh(order)
    except Exception:
        # If no suitable driver is available,
        # keep the order as PENDING.
        pass

    return order


@router.get("", response_model=List[OrderOut])
def list_orders(
    status_filter: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    q = db.query(Order)

    if status_filter:
        q = q.filter(Order.status == status_filter)

    return q.order_by(Order.created_at.desc()).all()


@router.get("/priority-queue")
def get_priority_queue(
    current_user: User = Depends(get_current_user),
):
    """Returns the REAL backend priority-queue contents."""
    return dispatch.priority_queue.peek_all()


@router.post("/dispatch-next")
def dispatch_next(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Manually dispatch the highest-priority pending order
    if automatic dispatch could not assign it earlier.
    """

    order = dispatch.auto_dispatch_next(db)

    if order is None:
        raise HTTPException(
            status_code=404,
            detail=(
                "No dispatchable order "
                "(empty queue or no available driver)"
            ),
        )

    return {
        "assigned_order_id": order.id,
        "driver_id": order.assigned_driver_id,
    }


@router.get(
    "/{order_id}",
    response_model=OrderOut,
)
def get_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    order = db.query(Order).get(order_id)

    if not order:
        raise HTTPException(
            status_code=404,
            detail="Order not found",
        )

    return order


@router.put(
    "/{order_id}",
    response_model=OrderOut,
)
def update_order(
    order_id: int,
    payload: OrderUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    order = db.query(Order).get(order_id)

    if not order:
        raise HTTPException(
            status_code=404,
            detail="Order not found",
        )

    data = payload.model_dump(exclude_unset=True)

    for field, value in data.items():
        setattr(order, field, value)

    db.commit()
    db.refresh(order)

    return order


@router.delete(
    "/{order_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    order = db.query(Order).get(order_id)

    if not order:
        raise HTTPException(
            status_code=404,
            detail="Order not found",
        )

    # Remove order from priority queue
    dispatch.priority_queue.remove(order.id)

    db.delete(order)
    db.commit()

    return None