from fastapi import APIRouter, Depends, Query, status
from typing import List, Optional
from datetime import date
from sqlalchemy.orm import Session

from src.database.db import get_db
from src.core.dependencies import get_current_user
from src.models.user import User
from src.schemas.booking import (
    RentalBookingRequest, OutstationBookingRequest,
    RentalPreviewResponse, OutstationPreviewResponse,
    BookingOut, MessageResponse, RentalConfirmRequest,
    CancelRequestRequest
)
from src.services import booking_service

router = APIRouter()


# ── Previews (check price before booking) ────────────────────────────────────

@router.get(
    "/rental/preview",
    response_model=RentalPreviewResponse,
    summary="Preview Rental Amount",
)
def preview_rental(
    car_number: str  = Query(...),
    start_date: date = Query(..., description="YYYY-MM-DD"),
    end_date:   date = Query(..., description="YYYY-MM-DD"),
    driver_required: bool = Query(False, description="True if driver is needed"),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """
    Preview the cost of a rental booking before confirming.
    Returns num_days and total_amount.
    """
    return booking_service.preview_rental(db, car_number, start_date, end_date, driver_required)


@router.get(
    "/outstation/preview",
    response_model=OutstationPreviewResponse,
    summary="Preview Outstation Amount",
)
def preview_outstation(
    car_number: str = Query(...),
    pickup:  str = Query(..., description="Pickup city name e.g. Hyderabad"),
    drop:    str = Query(..., description="Drop city name e.g. Bangalore"),
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """
    Preview the cost of an outstation booking.
    Calls OpenRouteService to get real road distance, then calculates amount.
    """
    return booking_service.preview_outstation(db, car_number, pickup, drop)


# ── Create Bookings ───────────────────────────────────────────────────────────

@router.post(
    "/rental",
    response_model=BookingOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create Rental Booking",
)
def create_rental(
    payload: RentalBookingRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Book a car for N days.
    Amount = num_days × price_per_day (calculated by backend).
    """
    return booking_service.create_rental_booking(db, current_user.id, payload)


@router.post(
    "/rental/confirm",
    response_model=BookingOut,
    status_code=status.HTTP_201_CREATED,
    summary="Confirm Rental Booking",
)
def confirm_rental(
    payload: RentalConfirmRequest,
    car_number: str = Query(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Directly create a CONFIRMED booking with payment details.
    """
    return booking_service.confirm_rental_booking(db, current_user.id, car_number, payload)


@router.post(
    "/outstation",
    response_model=BookingOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create Outstation Booking",
)
def create_outstation(
    payload: OutstationBookingRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Book a car for an outstation trip.
    Amount = road_distance_km × price_per_km (calculated by backend via ORS API).
    """
    return booking_service.create_outstation_booking(db, current_user.id, payload)


# ── User Booking Management ───────────────────────────────────────────────────

@router.get(
    "/my",
    response_model=List[BookingOut],
    summary="My Bookings",
)
def my_bookings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Returns all bookings for the currently logged-in user."""
    return booking_service.get_my_bookings(db, current_user.id)


@router.get(
    "/{booking_id}",
    response_model=BookingOut,
    summary="Get Single Booking",
)
def get_booking(
    booking_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return booking_service.get_booking_by_id(db, booking_id, current_user.id)


@router.post(
    "/{booking_id}/request-cancel",
    response_model=BookingOut,
    summary="Request Booking Cancellation",
)
def request_cancel_booking(
    booking_id: int,
    payload: CancelRequestRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return booking_service.request_cancel_booking(db, booking_id, current_user.id, payload.reason)
