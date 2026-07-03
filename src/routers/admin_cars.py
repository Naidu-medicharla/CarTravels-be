
from fastapi import APIRouter, Depends, status, UploadFile, File, Form
from typing import List, Optional
from sqlalchemy.orm import Session

from src.database.db import get_db
from src.core.dependencies import require_admin, get_current_user
from src.models.user import User
from src.models.car import FuelType, TransmissionType, AvailabilityType
from src.schemas.car import (
    CarCreate, CarUpdate, CarPartialUpdate, CarOut, CarListOut,
    CarCreateResponse, MessageResponse, AvailabilityUpdate,
    BulkCarCreate, BulkCreateResponse, BulkDeleteRequest, BulkAvailabilityUpdate,
)
from src.services import car_service

router = APIRouter()


# ─────────────────────────────────────────────────────────────────────────────
#  BULK routes (JSON — arrays can't be sent via form-data)
#  Must be declared BEFORE /{car_id} routes
# ─────────────────────────────────────────────────────────────────────────────

@router.post(
    "/cars/bulk",
    response_model=BulkCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Bulk Add Cars (JSON body)",
)
def bulk_add_cars(
    payload: BulkCarCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    cars = car_service.bulk_create_cars(db, payload.cars)
    return BulkCreateResponse(
        message=f"{len(cars)} cars created successfully.",
        car_ids=[c.id for c in cars],
        created=len(cars),
    )


@router.delete(
    "/cars/bulk",
    response_model=MessageResponse,
    summary="Bulk Delete Cars (JSON body)",
)
def bulk_delete_cars(
    payload: BulkDeleteRequest,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    count = car_service.bulk_delete_cars(db, payload.car_ids)
    return {"message": f"{count} car(s) deleted successfully."}


@router.patch(
    "/cars/bulk/availability",
    response_model=MessageResponse,
    summary="Bulk Update Availability (JSON body)",
)
def bulk_update_availability(
    payload: BulkAvailabilityUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    count = car_service.bulk_update_availability(db, payload)
    return {"message": f"Availability updated for {count} car(s)."}


# ─────────────────────────────────────────────────────────────────────────────
#  Standard CRUD — form-data
# ─────────────────────────────────────────────────────────────────────────────

@router.get(
    "/all/cars",
    response_model=List[CarOut],
    summary="Get All Cars (Admin & Users — includes unavailable & soft-deleted)",
)
def get_all_cars(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    return car_service.get_all_cars_admin(db)


@router.post(
    "/cars",
    response_model=CarCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Car",
)
def create_car(
    car_number:    str              = Form(...),
    brand:         str              = Form(...),
    model:         str              = Form(...),
    year:          int              = Form(...),
    fuel_type:     FuelType         = Form(...),
    transmission:  TransmissionType = Form(...),
    price_per_day: float            = Form(...),
    price_per_km:  Optional[float]  = Form(None),
    seats:         int              = Form(...),
    location:      str              = Form(...),
    description:   Optional[str]   = Form(None),
    availability_type: AvailabilityType = Form(AvailabilityType.BOTH),
    available:     bool             = Form(True),
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    payload = CarCreate(
        car_number=car_number, brand=brand, model=model, year=year, fuel_type=fuel_type,
        transmission=transmission, price_per_day=price_per_day,
        price_per_km=price_per_km,
        seats=seats, location=location, description=description, 
        availability_type=availability_type, available=available,
    )
    car = car_service.create_car(db, payload)
    return {"message": "Car Created Successfully", "car_id": car.id}


@router.get(
    "/cars/{car_number}",
    response_model=CarOut,
    summary="Get One Car (Admin)",
)
def get_car(
    car_number: str,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    return car_service.get_car_admin(db, car_number)


@router.put(
    "/cars/{car_number}",
    response_model=CarOut,
    summary="Full Update Car",
)
def update_car(
    car_number:    str,
    brand:         str              = Form(...),
    model:         str              = Form(...),
    year:          int              = Form(...),
    fuel_type:     FuelType         = Form(...),
    transmission:  TransmissionType = Form(...),
    price_per_day: float            = Form(...),
    price_per_km:  Optional[float]  = Form(None),
    seats:         int              = Form(...),
    location:      str              = Form(...),
    description:   Optional[str]   = Form(None),
    availability_type: AvailabilityType = Form(AvailabilityType.BOTH),
    available:     bool             = Form(True),
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    payload = CarUpdate(
        car_number=car_number, brand=brand, model=model, year=year, fuel_type=fuel_type,
        transmission=transmission, price_per_day=price_per_day,
        price_per_km=price_per_km,
        seats=seats, location=location, description=description, 
        availability_type=availability_type, available=available,
    )
    return car_service.update_car(db, car_number, payload)


@router.patch(
    "/cars/{car_number}",
    response_model=CarOut,
    summary="Partial Update Car (only send fields you want to change)",
)
def partial_update_car(
    car_number:    str,
    brand:         Optional[str]              = Form(None),
    model:         Optional[str]              = Form(None),
    year:          Optional[int]              = Form(None),
    fuel_type:     Optional[FuelType]         = Form(None),
    transmission:  Optional[TransmissionType] = Form(None),
    price_per_day: Optional[float]            = Form(None),
    price_per_km:  Optional[float]            = Form(None),
    seats:         Optional[int]              = Form(None),
    location:      Optional[str]              = Form(None),
    description:   Optional[str]             = Form(None),
    availability_type: Optional[AvailabilityType] = Form(None),
    available:     Optional[bool]             = Form(None),
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    payload = CarPartialUpdate(
        car_number=car_number, brand=brand, model=model, year=year, fuel_type=fuel_type,
        transmission=transmission, price_per_day=price_per_day,
        price_per_km=price_per_km,
        seats=seats, location=location, description=description, 
        availability_type=availability_type, available=available,
    )
    return car_service.partial_update_car(db, car_number, payload)


@router.delete(
    "/cars/{car_number}",
    response_model=MessageResponse,
    summary="Hard Delete Car",
)
def delete_car(
    car_number: str,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    car_service.delete_car(db, car_number)
    return {"message": "Car Deleted Successfully"}


@router.patch(
    "/cars/{car_number}/availability",
    response_model=MessageResponse,
    summary="Change Car Availability",
)
def change_availability(
    car_number: str,
    available: bool = Form(...),
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    payload = AvailabilityUpdate(available=available)
    car_service.update_availability(db, car_number, payload)
    return {"message": "Availability Updated"}


@router.patch(
    "/change-car-status/{car_number}/available",
    response_model=MessageResponse,
    summary="Make Car Available",
)
def make_car_available(
    car_number: str,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    payload = AvailabilityUpdate(available=True)
    car_service.update_availability(db, car_number, payload)
    return {"message": "Car is now available."}


@router.patch(
    "/change-car-status/{car_number}/unavailable",
    response_model=MessageResponse,
    summary="Make Car Unavailable",
)
def make_car_unavailable(
    car_number: str,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    payload = AvailabilityUpdate(available=False)
    car_service.update_availability(db, car_number, payload)
    return {"message": "Car is now unavailable."}


@router.patch(
    "/cars/{car_number}/disable",
    response_model=MessageResponse,
    summary="Soft Delete (Disable) Car",
)
def disable_car(
    car_number: str,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    car_service.soft_delete_car(db, car_number)
    return {"message": "Car disabled successfully."}


@router.patch(
    "/cars/{car_number}/enable",
    response_model=MessageResponse,
    summary="Restore (Enable) Car",
)
def enable_car(
    car_number: str,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    car_service.restore_car(db, car_number)
    return {"message": "Car enabled successfully."}


@router.post(
    "/cars/{car_number}/images",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload Car Images",
)
def upload_images(
    car_number: str,
    images: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    paths = car_service.upload_car_images(db, car_number, images)
    return {"message": f"{len(paths)} image(s) uploaded successfully."}
