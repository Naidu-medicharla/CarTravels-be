from fastapi import APIRouter, Depends, Query
from typing import List, Optional
from sqlalchemy.orm import Session

from src.database.db import get_db
from src.schemas.car import CarOut, CarListOut
from src.services import car_service

router = APIRouter()

# ─────────────────────────────────────────────────────────────────────────────
#  Static routes MUST come before /{car_id}
# ─────────────────────────────────────────────────────────────────────────────

@router.get(
    "/available",
    response_model=List[CarListOut],
    summary="Get All Available Cars",
)
def get_available_cars(db: Session = Depends(get_db)):
    return car_service.get_available_cars(db)


@router.get(
    "/search",
    response_model=List[CarListOut],
    summary="Search Cars",
)
def search_cars(
    brand:        Optional[str] = Query(None),
    location:     Optional[str] = Query(None),
    fuel_type:    Optional[str] = Query(None),
    transmission: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    return car_service.search_cars(db, brand, location, fuel_type, transmission)


# ─────────────────────────────────────────────────────────────────────────────
#  List with full filters & pagination
# ─────────────────────────────────────────────────────────────────────────────

@router.get(
    "",
    response_model=List[CarListOut],
    summary="Get All Cars (with filters & pagination)",
)
def get_all_cars(
    page:         int            = Query(1,    ge=1),
    limit:        int            = Query(10,   ge=1, le=100),
    brand:        Optional[str]  = Query(None),
    fuel_type:    Optional[str]  = Query(None),
    transmission: Optional[str]  = Query(None),
    min_price:    Optional[float]= Query(None, ge=0),
    max_price:    Optional[float]= Query(None, ge=0),
    location:     Optional[str]  = Query(None),
    sort:         Optional[str]  = Query("id"),
    order:        Optional[str]  = Query("asc"),
    db: Session = Depends(get_db),
):
    return car_service.get_cars_public(
        db, page, limit, brand, fuel_type,
        transmission, min_price, max_price, location, sort, order,
    )


# ─────────────────────────────────────────────────────────────────────────────
#  Single car
# ─────────────────────────────────────────────────────────────────────────────

@router.get(
    "/{car_number}",
    response_model=CarOut,
    summary="Get Single Car",
)
def get_car(car_number: str, db: Session = Depends(get_db)):
    return car_service.get_car_public(db, car_number)


@router.get(
    "/{car_number}/availability",
    response_model=List[str],
    summary="Get Blocked Dates for a Car",
)
def get_car_availability(car_number: str, db: Session = Depends(get_db)):
    from src.services import booking_service
    return booking_service.get_blocked_dates_for_car(db, car_number)
