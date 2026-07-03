from pydantic import BaseModel
from typing import Optional, List
from datetime import date, datetime
from src.models.booking import BookingType, BookingStatus


# ── Request Schemas ───────────────────────────────────────────────────────────

class RentalBookingRequest(BaseModel):
    car_number:      str
    start_date:      date   # YYYY-MM-DD
    end_date:        date   # YYYY-MM-DD
    driver_required: bool = False


class RentalConfirmRequest(BaseModel):
    start_date:      date
    end_date:        date
    driver_required: bool
    car_charges:     float
    driver_charges:  float
    discount:        float
    total_amount_before_discount: float
    total_amount:    float
    amount_paid:     float
    paid_by:         str
    payment_channel: str
    payment_status:  str


class OutstationBookingRequest(BaseModel):
    car_number:      str
    pickup_location: str   # city name e.g. "Hyderabad"
    drop_location:   str   # city name e.g. "Bangalore"
    pickup_date:     date  # YYYY-MM-DD


# ── Preview Schemas (before confirming) ──────────────────────────────────────

class RentalPreviewResponse(BaseModel):
    car_number:     str
    num_days:       int
    car_price:      float
    driver_charges: float
    total_amount:   float


class OutstationPreviewResponse(BaseModel):
    car_number:      str
    pickup_location: str
    drop_location:   str
    distance_km:     float
    price_per_km:    float
    total_amount:    float


# ── Car summary embedded in booking response ─────────────────────────────────

class CarSummary(BaseModel):
    car_number: str
    brand: str
    model: str
    model_config = {"from_attributes": True}


class UserSummary(BaseModel):
    id:   int
    name: str
    model_config = {"from_attributes": True}


# ── Booking Response ─────────────────────────────────────────────────────────

class AssignDriverRequest(BaseModel):
    driver_id: str
    driver_name: str
    driver_phone: Optional[str] = None

class BookingOut(BaseModel):
    id:           int
    booking_id:   Optional[str] = None
    booking_type: BookingType
    status:       BookingStatus
    car_charges:  Optional[float] = None
    discount:     Optional[float] = None
    total_amount_before_discount: Optional[float] = None
    total_amount: float
    amount_paid:  Optional[float] = None
    paid_by:      Optional[str] = None
    payment_channel: Optional[str] = None
    payment_status: Optional[str] = None

    # Rental
    start_date:      Optional[date] = None
    end_date:        Optional[date] = None
    num_days:        Optional[int]  = None
    driver_required: Optional[bool] = None
    driver_charges:  Optional[float] = None

    # Outstation
    pickup_location: Optional[str]   = None
    drop_location:   Optional[str]   = None
    pickup_date:     Optional[date]  = None
    distance_km:     Optional[float] = None

    # Driver Info
    driver_id:    Optional[str] = None
    driver_name:  Optional[str] = None
    driver_phone: Optional[str] = None

    # Cancellation
    cancel_reason: Optional[str] = None
    admin_reject_reason: Optional[str] = None

    # Trip state
    is_trip_completed: Optional[bool] = False
    is_rated: Optional[bool] = False
    rating: Optional[float] = None

    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    car:  Optional[CarSummary]  = None
    user: Optional[UserSummary] = None

    model_config = {"from_attributes": True}


class CancelRequestRequest(BaseModel):
    reason: str


class RejectCancelRequest(BaseModel):
    reason: str


class MessageResponse(BaseModel):
    message: str
