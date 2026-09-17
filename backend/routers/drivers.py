from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from database import get_db
from models import Driver, User
from schemas.schemas import DriverCreate, DriverUpdate, DriverOut
from utils.auth import get_current_user

router = APIRouter(prefix="/api/drivers", tags=["drivers"])


@router.get("", response_model=List[DriverOut])
def list_drivers(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return db.query(Driver).all()


@router.post("", response_model=DriverOut, status_code=status.HTTP_201_CREATED)
def create_driver(payload: DriverCreate, db: Session = Depends(get_db),
                   current_user: User = Depends(get_current_user)):
    driver = Driver(**payload.model_dump())
    db.add(driver)
    db.commit()
    db.refresh(driver)
    return driver


@router.put("/{driver_id}", response_model=DriverOut)
def update_driver(driver_id: int, payload: DriverUpdate, db: Session = Depends(get_db),
                   current_user: User = Depends(get_current_user)):
    driver = db.query(Driver).get(driver_id)
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")
    data = payload.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(driver, field, value)
    db.commit()
    db.refresh(driver)
    return driver
