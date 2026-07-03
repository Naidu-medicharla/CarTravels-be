from fastapi import APIRouter, Depends, Query, status
from typing import List, Optional
from sqlalchemy.orm import Session

from src.database.db import get_db
from src.core.dependencies import require_admin
from src.models.user import User
from src.models.booking import BookingStatus
from src.schemas.booking import BookingOut, MessageResponse, RejectCancelRequest, AssignDriverRequest
from src.services import booking_service
from src.core.events import event_bus

router = APIRouter()


@router.get(
    "/bookings",
    response_model=List[BookingOut],
    summary="Get All Bookings (Admin)",
)
def get_all_bookings(
    type:   Optional[str] = Query(None, description="RENTAL or OUTSTATION"),
    status: Optional[str] = Query(None, description="PENDING, CONFIRMED, CANCELLED, COMPLETED"),
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    return booking_service.admin_get_all_bookings(db, type, status)


@router.get(
    "/bookings/{booking_id}",
    response_model=BookingOut,
    summary="Get Single Booking (Admin)",
)
def get_booking(
    booking_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    return booking_service.admin_get_booking(db, booking_id)


@router.patch(
    "/bookings/{booking_id}/confirm",
    response_model=BookingOut,
    summary="Confirm Booking (Admin)",
)
def confirm_booking(
    booking_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    booking = booking_service.admin_update_status(db, booking_id, BookingStatus.CONFIRMED)
    try:
        event_bus.publish("booking-confirmed",
            db=db,
            user_id    = booking.user_id,
            booking_id = booking.booking_id or str(booking.id),
            car_number = booking.car_number or "",
        )
    except Exception:
        pass
    return booking


@router.post(
    "/bookings/{booking_id}/approve-cancel",
    response_model=BookingOut,
    summary="Approve Cancel Request (Admin)",
)
def approve_cancel_booking(
    booking_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    booking = booking_service.admin_update_status(db, booking_id, BookingStatus.CANCELLED)
    try:
        event_bus.publish("cancellation-approved",
            db=db,
            user_id    = booking.user_id,
            booking_id = booking.booking_id or str(booking.id),
            car_number = booking.car_number or "",
        )
    except Exception:
        pass
    return booking


@router.post(
    "/bookings/{booking_id}/reject-cancel",
    response_model=BookingOut,
    summary="Reject Cancel Request (Admin)",
)
def reject_cancel_booking(
    booking_id: int,
    payload: RejectCancelRequest,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    booking = booking_service.admin_reject_cancel_request(db, booking_id, payload.reason)
    try:
        event_bus.publish("cancellation-rejected",
            db=db,
            user_id    = booking.user_id,
            booking_id = booking.booking_id or str(booking.id),
            reason     = payload.reason,
        )
    except Exception:
        pass
    return booking


@router.post(
    "/bookings/{booking_id}/assign-driver",
    response_model=BookingOut,
    summary="Assign Driver to Booking (Admin)",
)
def assign_driver_to_booking(
    booking_id: int,
    payload: AssignDriverRequest,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    booking = booking_service.admin_assign_driver(db, booking_id, payload)
    try:
        event_bus.publish("driver-assigned",
            db=db,
            user_id    = booking.user_id,
            booking_id = booking.booking_id or str(booking.id),
            driver_name = payload.driver_name,
        )
    except Exception:
        pass
    return booking


@router.patch(
    "/bookings/{booking_id}/complete",
    response_model=BookingOut,
    summary="Mark Booking as Completed (Admin)",
)
def complete_booking(
    booking_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    return booking_service.admin_update_status(db, booking_id, BookingStatus.COMPLETED)

