from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import User, Batch, Order
from schemas.schemas import BatchCreateRequest, BatchOut, BatchDetailOut
from utils.auth import get_current_user
from services.batching import create_batches

router = APIRouter(prefix="/api/batches", tags=["batching"])


@router.post("/create", response_model=List[BatchOut])
def create_order_batches(payload: BatchCreateRequest, db: Session = Depends(get_db),
                          current_user: User = Depends(get_current_user)):
    if payload.orders_per_batch < 1:
        raise HTTPException(status_code=422, detail="orders_per_batch must be at least 1")

    try:
        batches = create_batches(db, orders_per_batch=payload.orders_per_batch)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Batching failed: {e}")

    if not batches:
        raise HTTPException(status_code=404, detail="No unbatched pending orders available to batch (need at least 2)")
    return batches


@router.get("", response_model=List[BatchOut])
def list_batches(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(Batch).order_by(Batch.created_at.desc()).all()


@router.get("/{batch_id}", response_model=BatchDetailOut)
def get_batch(batch_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    batch = db.query(Batch).get(batch_id)
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")
    order_ids = [o.id for o in db.query(Order).filter(Order.batch_id == batch_id).all()]
    return BatchDetailOut(
        id=batch.id,
        assigned_driver_id=batch.assigned_driver_id,
        total_distance_km=batch.total_distance_km,
        estimated_time_min=batch.estimated_time_min,
        num_orders=batch.num_orders,
        created_at=batch.created_at,
        order_ids=order_ids,
    )
