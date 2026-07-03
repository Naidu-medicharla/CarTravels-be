from datetime import date, timedelta
from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import and_

from src.models.booking import Booking, BookingType, BookingStatus
from src.models.car import Car
from src.schemas.booking import (
    RentalBookingRequest, OutstationBookingRequest,
    RentalPreviewResponse, OutstationPreviewResponse,
    RentalConfirmRequest, AssignDriverRequest,
)
from src.services.distance_service import get_road_distance_km
from src.models.driver import Driver
import random


# ── Helpers ───────────────────────────────────────────────────────────────────

def _get_active_car(db: Session, car_number: str) -> Car:
    car = db.query(Car).filter(
        Car.car_number == car_number,
        Car.is_deleted.is_not(True),
        Car.available == True,
    ).first()
    if not car:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Car not found or not available.",
        )
    return car


def _check_rental_availability(db: Session, car_id: int, start: date, end: date):
    """Raise 409 if car is already booked (CONFIRMED) in the requested date range."""
    conflict = db.query(Booking).filter(
        Booking.car_id      == car_id,
        Booking.booking_type == BookingType.RENTAL,
        Booking.status.in_([BookingStatus.CONFIRMED, BookingStatus.PENDING, BookingStatus.CANCEL_REQUESTED]),
        Booking.start_date  <= end,
        Booking.end_date    >= start,
    ).first()
    if conflict:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Car is already booked from {conflict.start_date} to {conflict.end_date}.",
        )


def _check_outstation_availability(db: Session, car_id: int, pickup_date: date):
    """Raise 409 if car is already booked (CONFIRMED) on the pickup date."""
    conflict = db.query(Booking).filter(
        Booking.car_id       == car_id,
        Booking.booking_type == BookingType.OUTSTATION,
        Booking.status.in_([BookingStatus.CONFIRMED, BookingStatus.PENDING, BookingStatus.CANCEL_REQUESTED]),
        Booking.pickup_date  == pickup_date,
    ).first()
    if conflict:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Car is already booked for an outstation trip on {pickup_date}.",
        )


# ── Preview (before booking) ──────────────────────────────────────────────────

def preview_rental(db: Session, car_number: str, start_date: date, end_date: date, driver_required: bool = False) -> RentalPreviewResponse:
    if end_date < start_date:
        raise HTTPException(status_code=400, detail="end_date cannot be before start_date.")
    car      = _get_active_car(db, car_number)
    num_days = (end_date - start_date).days + 1
    car_price = round(num_days * car.price_per_day, 2)
    driver_charges = num_days * 800.0 if driver_required else 0.0
    return RentalPreviewResponse(
        car_number    = car_number,
        num_days      = num_days,
        car_price     = car_price,
        driver_charges= driver_charges,
        total_amount  = car_price + driver_charges,
    )


def preview_outstation(db: Session, car_number: str, pickup: str, drop: str) -> OutstationPreviewResponse:
    car = _get_active_car(db, car_number)
    if not car.price_per_km:
        raise HTTPException(
            status_code=400,
            detail="This car does not support outstation bookings (price_per_km not set).",
        )
    distance_km = get_road_distance_km(pickup, drop)
    return OutstationPreviewResponse(
        car_number      = car_number,
        pickup_location = pickup,
        drop_location   = drop,
        distance_km     = distance_km,
        price_per_km    = car.price_per_km,
        total_amount    = round(distance_km * car.price_per_km, 2),
    )


# ── Create Bookings ───────────────────────────────────────────────────────────

def create_rental_booking(db: Session, user_id: int, payload: RentalBookingRequest) -> Booking:
    if payload.end_date < payload.start_date:
        raise HTTPException(status_code=400, detail="end_date cannot be before start_date.")

    car      = _get_active_car(db, payload.car_number)
    num_days = (payload.end_date - payload.start_date).days + 1
    _check_rental_availability(db, car.id, payload.start_date, payload.end_date)

    car_price = round(num_days * car.price_per_day, 2)
    driver_charges = num_days * 800.0 if payload.driver_required else 0.0

    booking = Booking(
        user_id         = user_id,
        car_id          = car.id,
        car_number      = car.car_number,
        booking_type    = BookingType.RENTAL,
        status          = BookingStatus.PENDING,
        start_date      = payload.start_date,
        end_date        = payload.end_date,
        num_days        = num_days,
        driver_required = payload.driver_required,
        driver_charges  = driver_charges,
        total_amount    = car_price + driver_charges,
    )
    db.add(booking)
    db.commit()
    db.refresh(booking)

    # Notify admins of new booking
    try:
        from src.core.events import event_bus
        user = db.query(__import__('src.models.user', fromlist=['User']).User).filter_by(id=user_id).first()
        event_bus.publish("booking-created", db=db, booking_id=booking.id, user_name=user.name if user else f"User#{user_id}", car_number=car.car_number)
    except Exception:
        pass

    return booking


def confirm_rental_booking(db: Session, user_id: int, car_number: str, payload: RentalConfirmRequest) -> Booking:
    if payload.end_date < payload.start_date:
        raise HTTPException(status_code=400, detail="end_date cannot be before start_date.")

    car = _get_active_car(db, car_number)
    num_days = (payload.end_date - payload.start_date).days + 1
    _check_rental_availability(db, car.id, payload.start_date, payload.end_date)

    import uuid
    booking_id = f"BKG-{str(uuid.uuid4())[:8].upper()}"

    assigned_driver_id = None
    assigned_driver_name = None
    assigned_driver_phone = None

    if payload.driver_required:
        all_drivers = db.query(Driver).all()
        
        # Check for bookings overlapping with this rental period
        busy_bookings = db.query(Booking).filter(
            Booking.driver_id.is_not(None),
            Booking.status.in_([BookingStatus.CONFIRMED, BookingStatus.PENDING, BookingStatus.CANCEL_REQUESTED]),
            Booking.start_date <= payload.end_date,
            Booking.end_date >= payload.start_date,
            Booking.booking_type == BookingType.RENTAL
        ).all()
        
        busy_driver_ids = {b.driver_id for b in busy_bookings if b.driver_id}
        available_drivers = [d for d in all_drivers if d.driver_id not in busy_driver_ids]
        
        if available_drivers:
            chosen_driver = random.choice(available_drivers)
            assigned_driver_id = chosen_driver.driver_id
            assigned_driver_name = chosen_driver.driver_name
            assigned_driver_phone = chosen_driver.mobile_number

    booking = Booking(
        booking_id      = booking_id,
        user_id         = user_id,
        car_id          = car.id,
        car_number      = car.car_number,
        booking_type    = BookingType.RENTAL,
        status          = BookingStatus.CONFIRMED,
        start_date      = payload.start_date,
        end_date        = payload.end_date,
        num_days        = num_days,
        driver_required = payload.driver_required,
        driver_id       = assigned_driver_id,
        driver_name     = assigned_driver_name,
        driver_phone    = assigned_driver_phone,
        car_charges     = payload.car_charges,
        driver_charges  = payload.driver_charges,
        discount        = payload.discount,
        total_amount_before_discount = payload.total_amount_before_discount,
        total_amount    = payload.total_amount,
        amount_paid     = payload.amount_paid,
        paid_by         = payload.paid_by,
        payment_channel = payload.payment_channel,
        payment_status  = payload.payment_status,
    )
    db.add(booking)
    db.commit()
    db.refresh(booking)

    # Notify admins of new confirmed booking + milestone check
    try:
        from src.core.events import event_bus
        user = db.query(__import__('src.models.user', fromlist=['User']).User).filter_by(id=user_id).first()
        event_bus.publish("booking-created", db=db, booking_id=booking.booking_id or booking.id, user_name=user.name if user else f"User#{user_id}", car_number=car.car_number)
        event_bus.publish("booking-milestone", db=db)
    except Exception:
        pass

    return booking


def get_blocked_dates_for_car(db: Session, car_number: str) -> List[str]:
    bookings = db.query(Booking).filter(
        Booking.car_number == car_number,
        Booking.status == BookingStatus.CONFIRMED
    ).all()

    blocked_dates = set()
    for b in bookings:
        if b.booking_type == BookingType.RENTAL and b.start_date and b.end_date:
            curr = b.start_date
            while curr <= b.end_date:
                blocked_dates.add(curr.strftime("%Y-%m-%d"))
                curr += timedelta(days=1)
        elif b.booking_type == BookingType.OUTSTATION and b.pickup_date:
            blocked_dates.add(b.pickup_date.strftime("%Y-%m-%d"))
            
    return sorted(list(blocked_dates))


def create_outstation_booking(db: Session, user_id: int, payload: OutstationBookingRequest) -> Booking:
    car = _get_active_car(db, payload.car_number)
    if not car.price_per_km:
        raise HTTPException(
            status_code=400,
            detail="This car does not support outstation bookings (price_per_km not set).",
        )

    _check_outstation_availability(db, car.id, payload.pickup_date)
    distance_km = get_road_distance_km(payload.pickup_location, payload.drop_location)

    booking = Booking(
        user_id         = user_id,
        car_id          = car.id,
        booking_type    = BookingType.OUTSTATION,
        status          = BookingStatus.PENDING,
        pickup_location = payload.pickup_location,
        drop_location   = payload.drop_location,
        pickup_date     = payload.pickup_date,
        distance_km     = distance_km,
        total_amount    = round(distance_km * car.price_per_km, 2),
    )
    db.add(booking)
    db.commit()
    db.refresh(booking)

    # Notify admins of new outstation booking
    try:
        from src.core.events import event_bus
        user = db.query(__import__('src.models.user', fromlist=['User']).User).filter_by(id=user_id).first()
        event_bus.publish("booking-created", db=db, booking_id=booking.id, user_name=user.name if user else f"User#{user_id}", car_number=car.car_number)
    except Exception:
        pass

    return booking


# ── User actions ──────────────────────────────────────────────────────────────

def request_cancel_booking(db: Session, booking_id: int, user_id: int, reason: str) -> Booking:
    booking = db.query(Booking).filter(
        Booking.id      == booking_id,
        Booking.user_id == user_id,
    ).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found.")
    if booking.status == BookingStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Cannot cancel a completed booking.")
    if booking.status in [BookingStatus.CANCELLED, BookingStatus.CANCEL_REQUESTED]:
        raise HTTPException(status_code=400, detail="Booking is already cancelled or cancel requested.")
    
    booking.status = BookingStatus.CANCEL_REQUESTED
    booking.cancel_reason = reason
    db.commit()
    db.refresh(booking)

    # Notify admins of cancel request
    try:
        from src.core.events import event_bus
        user = db.query(__import__('src.models.user', fromlist=['User']).User).filter_by(id=user_id).first()
        event_bus.publish("cancellation-requested",
            db=db,
            booking_id  = booking.booking_id or str(booking.id),
            user_name   = user.name if user else f"User#{user_id}",
            car_number  = booking.car_number or "",
            reason      = reason,
        )
    except Exception:
        pass

    return booking


def get_my_bookings(db: Session, user_id: int) -> List[Booking]:
    return db.query(Booking).filter(Booking.user_id == user_id).all()


def get_pending_notifications(db: Session, user_id: int):
    today = date.today()
    bookings_to_check = db.query(Booking).filter(
        Booking.user_id == user_id,
        Booking.status.in_([BookingStatus.CONFIRMED, BookingStatus.COMPLETED]),
        Booking.is_trip_completed == False
    ).all()
    
    dirty = False
    for b in bookings_to_check:
        if b.booking_type == BookingType.RENTAL and b.end_date and b.end_date < today:
            b.is_trip_completed = True
            dirty = True
        elif b.booking_type == BookingType.OUTSTATION and b.pickup_date and b.pickup_date < today:
            b.is_trip_completed = True
            dirty = True
            
    if dirty:
        db.commit()
        
    unrated_bookings = db.query(Booking).filter(
        Booking.user_id == user_id,
        Booking.is_trip_completed == True,
        Booking.is_rated == False
    ).all()
    
    notifications = []
    for b in unrated_bookings:
        notifications.append({
            "booking_id": b.id,
            "car_number": b.car_number,
            "rating_needed": True,
            "message": f"Your trip with car {b.car_number} is completed. Please rate your experience."
        })
        
    return notifications


def get_booking_by_id(db: Session, booking_id: int, user_id: int) -> Booking:
    booking = db.query(Booking).filter(
        Booking.id      == booking_id,
        Booking.user_id == user_id,
    ).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found.")
    return booking


# ── Admin actions ─────────────────────────────────────────────────────────────

def admin_get_all_bookings(
    db: Session,
    booking_type: Optional[str] = None,
    booking_status: Optional[str] = None,
) -> List[Booking]:
    query = db.query(Booking)
    if booking_type:
        query = query.filter(Booking.booking_type == booking_type.upper())
    if booking_status:
        query = query.filter(Booking.status == booking_status.upper())
    return query.all()


def admin_get_booking(db: Session, booking_id: int) -> Booking:
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found.")
    return booking


def admin_update_status(db: Session, booking_id: int, new_status: BookingStatus) -> Booking:
    booking = admin_get_booking(db, booking_id)
    booking.status = new_status
    db.commit()
    db.refresh(booking)
    return booking


def admin_reject_cancel_request(db: Session, booking_id: int, reason: str) -> Booking:
    booking = admin_get_booking(db, booking_id)
    if booking.status != BookingStatus.CANCEL_REQUESTED:
        raise HTTPException(status_code=400, detail="Booking is not in CANCEL_REQUESTED status.")
    
    booking.status = BookingStatus.CONFIRMED
    booking.admin_reject_reason = reason
    db.commit()
    db.refresh(booking)
    return booking

def admin_assign_driver(db: Session, booking_id: int, payload: AssignDriverRequest) -> Booking:
    booking = db.query(Booking).filter(Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found"
        )
    
    from src.models.driver import Driver
    driver = db.query(Driver).filter(Driver.driver_id == payload.driver_id).first()
    
    if payload.driver_id != "TEMP":
        from src.services.driver_service import get_available_drivers_for_dates
        start = booking.start_date if booking.booking_type == BookingType.RENTAL else booking.pickup_date
        end = booking.end_date if booking.booking_type == BookingType.RENTAL else booking.pickup_date
        
        available = get_available_drivers_for_dates(db, start, end)
        if not any(d.driver_id == payload.driver_id for d in available):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Driver is already assigned to another booking during these dates."
            )
            
    booking.driver_id = payload.driver_id
    booking.driver_name = payload.driver_name
    booking.driver_phone = driver.mobile_number if driver else payload.driver_phone
    
    db.commit()
    db.refresh(booking)
    return booking
