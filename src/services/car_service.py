import os
import shutil
from typing import List, Optional
from fastapi import HTTPException, UploadFile, status
from sqlalchemy.orm import Session
from sqlalchemy import or_

from src.models.car import Car, CarImage, FuelType, TransmissionType
from src.schemas.car import (
    CarCreate, CarUpdate, CarPartialUpdate,
    AvailabilityUpdate, BulkAvailabilityUpdate
)

UPLOAD_DIR = "uploads/car_images"


# ── Helpers ───────────────────────────────────────────────────────────────────

def _get_car_or_404(db: Session, car_number: str, include_deleted: bool = False) -> Car:
    query = db.query(Car).filter(Car.car_number == car_number)
    if not include_deleted:
        query = query.filter(Car.is_deleted.is_not(True))
    car = query.first()
    if not car:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Car not found.")
    return car


# ── Admin Services ────────────────────────────────────────────────────────────

def create_car(db: Session, payload: CarCreate) -> Car:
    car = Car(**payload.model_dump())
    db.add(car)
    db.commit()
    db.refresh(car)
    return car


def update_car(db: Session, car_number: str, payload: CarUpdate) -> Car:
    car = _get_car_or_404(db, car_number)
    for field, value in payload.model_dump().items():
        setattr(car, field, value)
    db.commit()
    db.refresh(car)
    return car


def partial_update_car(db: Session, car_number: str, payload: CarPartialUpdate) -> Car:
    car = _get_car_or_404(db, car_number)
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(car, field, value)
    db.commit()
    db.refresh(car)
    return car


def delete_car(db: Session, car_number: str) -> None:
    car = _get_car_or_404(db, car_number, include_deleted=True)
    db.delete(car)
    db.commit()


def update_availability(db: Session, car_number: str, payload: AvailabilityUpdate) -> Car:
    car = _get_car_or_404(db, car_number)
    car.available = payload.available
    db.commit()
    db.refresh(car)
    return car


def soft_delete_car(db: Session, car_number: str) -> Car:
    car = _get_car_or_404(db, car_number)
    car.is_deleted = True
    car.available  = False
    db.commit()
    db.refresh(car)
    return car


def restore_car(db: Session, car_number: str) -> Car:
    car = _get_car_or_404(db, car_number, include_deleted=True)
    car.is_deleted = False
    car.available  = True
    db.commit()
    db.refresh(car)
    return car


def upload_car_images(db: Session, car_number: str, files: List[UploadFile]) -> List[str]:
    car = _get_car_or_404(db, car_number)

    save_dir = os.path.join(UPLOAD_DIR, car_number)
    os.makedirs(save_dir, exist_ok=True)

    saved_paths = []
    for file in files:
        file_path = os.path.join(save_dir, file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        img = CarImage(car_id=car.id, image_path=file_path.replace("\\", "/"))
        db.add(img)
        saved_paths.append(file_path)

    db.commit()
    return saved_paths


def get_all_cars_admin(db: Session) -> List[Car]:
    """Admin: returns ALL cars including soft-deleted."""
    from sqlalchemy.orm import joinedload
    return db.query(Car).options(joinedload(Car.bookings)).all()


def get_car_admin(db: Session, car_number: str) -> Car:
    return _get_car_or_404(db, car_number, include_deleted=True)


def bulk_create_cars(db: Session, cars_data: List[CarCreate]) -> List[Car]:
    cars = [Car(**c.model_dump()) for c in cars_data]
    db.add_all(cars)
    db.commit()
    for car in cars:
        db.refresh(car)
    return cars


def bulk_delete_cars(db: Session, car_numbers: List[str]) -> int:
    deleted = db.query(Car).filter(Car.car_number.in_(car_numbers)).delete(synchronize_session=False)
    db.commit()
    return deleted


def bulk_update_availability(db: Session, payload: BulkAvailabilityUpdate) -> int:
    updated = (
        db.query(Car)
        .filter(Car.car_number.in_(payload.car_numbers))
        .update({"available": payload.available}, synchronize_session=False)
    )
    db.commit()
    return updated


# ── User/Public Services ──────────────────────────────────────────────────────

def get_cars_public(
    db: Session,
    page: int = 1,
    limit: int = 10,
    brand: Optional[str] = None,
    fuel_type: Optional[str] = None,
    transmission: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    location: Optional[str] = None,
    sort: Optional[str] = "id",
    order: Optional[str] = "asc",
) -> List[Car]:
    query = db.query(Car).filter(Car.is_deleted.is_not(True), Car.available == True)

    if brand:
        query = query.filter(Car.brand.ilike(f"%{brand}%"))
    if fuel_type:
        query = query.filter(Car.fuel_type == fuel_type)
    if transmission:
        query = query.filter(Car.transmission == transmission)
    if min_price is not None:
        query = query.filter(Car.price_per_day >= min_price)
    if max_price is not None:
        query = query.filter(Car.price_per_day <= max_price)
    if location:
        query = query.filter(Car.location.ilike(f"%{location}%"))

    sort_column = getattr(Car, sort, Car.id)
    if order == "desc":
        query = query.order_by(sort_column.desc())
    else:
        query = query.order_by(sort_column.asc())

    offset = (page - 1) * limit
    return query.offset(offset).limit(limit).all()


def get_car_public(db: Session, car_number: str) -> Car:
    return _get_car_or_404(db, car_number)


def search_cars(
    db: Session,
    brand: Optional[str] = None,
    location: Optional[str] = None,
    fuel_type: Optional[str] = None,
    transmission: Optional[str] = None,
) -> List[Car]:
    query = db.query(Car).filter(Car.is_deleted.is_not(True), Car.available == True)
    if brand:
        query = query.filter(Car.brand.ilike(f"%{brand}%"))
    if location:
        query = query.filter(Car.location.ilike(f"%{location}%"))
    if fuel_type:
        query = query.filter(Car.fuel_type == fuel_type)
    if transmission:
        query = query.filter(Car.transmission == transmission)
    return query.all()


def get_available_cars(db: Session) -> List[Car]:
    return db.query(Car).filter(Car.is_deleted.is_not(True), Car.available == True).all()
