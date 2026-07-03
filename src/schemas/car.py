from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date
from src.models.car import FuelType, TransmissionType, AvailabilityType


# ── Shared base ──────────────────────────────────────────────────────────────

class CarBase(BaseModel):
    car_number:    str
    brand:         str
    model:         str
    year:          int = Field(..., ge=1990, le=2100)
    fuel_type:     FuelType
    transmission:  TransmissionType
    price_per_day: float = Field(..., gt=0)
    price_per_km:  Optional[float] = None   # for outstation bookings
    seats:         int   = Field(..., ge=1, le=20)
    location:      str
    description:   Optional[str] = None
    availability_type: AvailabilityType = AvailabilityType.BOTH
    available:     bool = True


# ── Request schemas ───────────────────────────────────────────────────────────

class CarCreate(CarBase):
    pass


class CarUpdate(CarBase):
    """PUT — all fields required."""
    pass


class CarPartialUpdate(BaseModel):
    """PATCH — only send the fields you want to change."""
    car_number:    Optional[str]              = None
    brand:         Optional[str]              = None
    model:         Optional[str]              = None
    year:          Optional[int]              = None
    fuel_type:     Optional[FuelType]         = None
    transmission:  Optional[TransmissionType] = None
    price_per_day: Optional[float]            = None
    price_per_km:  Optional[float]            = None
    seats:         Optional[int]              = None
    location:      Optional[str]              = None
    description:   Optional[str]             = None
    availability_type: Optional[AvailabilityType] = None
    available:     Optional[bool]             = None


class AvailabilityUpdate(BaseModel):
    available: bool


class BulkCarCreate(BaseModel):
    cars: List[CarCreate]


class BulkDeleteRequest(BaseModel):
    car_numbers: List[str]


class BulkAvailabilityUpdate(BaseModel):
    car_numbers: List[str]
    available: bool


# ── Response schemas ──────────────────────────────────────────────────────────

class CarImageOut(BaseModel):
    id:         int
    image_path: str
    model_config = {"from_attributes": True}


class UpcomingBooking(BaseModel):
    booking_id: Optional[str] = None
    booking_type: str
    status: str
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    pickup_date: Optional[date] = None
    model_config = {"from_attributes": True}

class CarOut(CarBase):
    """Full car detail — used in admin endpoints."""
    id:         int
    is_deleted: Optional[bool] = False
    images:     List[CarImageOut] = []
    upcoming_bookings: List[UpcomingBooking] = []
    model_config = {"from_attributes": True}


class CarListOut(BaseModel):
    """Slim card — used in list/search endpoints."""
    id:           int
    brand:        str
    model:        str
    year:         int
    fuel_type:    FuelType
    transmission: TransmissionType
    price_per_day: float
    seats:        int
    location:     str
    available:    bool
    model_config = {"from_attributes": True}


class CarCreateResponse(BaseModel):
    message: str
    car_id:  int


class MessageResponse(BaseModel):
    message: str


class BulkCreateResponse(BaseModel):
    message:  str
    car_numbers:  List[str]
    created:  int
