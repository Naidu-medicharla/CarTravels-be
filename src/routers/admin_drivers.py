from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from typing import List
from datetime import date

from src.database.db import get_db
from src.core.dependencies import require_admin
from src.models.user import User
from src.schemas.driver import DriverCreate, DriverOut, DriverResponse
from src.services import driver_service

router = APIRouter()

@router.post(
    "/drivers",
    response_model=DriverResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new Driver (Admin Only)",
)
def create_driver(
    payload: DriverCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    driver = driver_service.create_driver(db, payload)
    return {"message": "Driver created successfully", "driver_id": driver.driver_id}

@router.get(
    "/drivers",
    response_model=List[DriverOut],
    summary="Get all Drivers (Admin Only)",
)
def get_all_drivers(
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    return driver_service.get_all_drivers(db)

@router.get(
    "/drivers/available",
    response_model=List[DriverOut],
    summary="Get available Drivers for dates (Admin)",
)
def get_available_drivers(
    start_date: date,
    end_date: date,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    return driver_service.get_available_drivers_for_dates(db, start_date, end_date)
