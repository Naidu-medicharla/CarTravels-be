from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from src.models.driver import Driver
from src.schemas.driver import DriverCreate

def create_driver(db: Session, driver_data: DriverCreate):
    # Check if driver with same mobile number exists
    existing_driver = db.query(Driver).filter(Driver.mobile_number == driver_data.mobile_number).first()
    if existing_driver:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A driver with this mobile number already exists."
        )

    new_driver = Driver(
        driver_name=driver_data.driver_name,
        mobile_number=driver_data.mobile_number
    )
    db.add(new_driver)
    db.commit()
    db.refresh(new_driver)
    return new_driver

def get_all_drivers(db: Session):
    return db.query(Driver).all()

def get_driver_by_id(db: Session, driver_id: str):
    driver = db.query(Driver).filter(Driver.driver_id == driver_id).first()
    if not driver:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Driver not found"
        )
    return driver

def get_available_drivers_for_dates(db: Session, start_date, end_date):
    from src.models.booking import Booking, BookingStatus
    from sqlalchemy import or_
    
    # Get all drivers
    all_drivers = db.query(Driver).all()
    
    # Find bookings that overlap with [start_date, end_date] and are not cancelled/completed/rejected
    overlapping_bookings = db.query(Booking).filter(
        Booking.status.in_([BookingStatus.PENDING, BookingStatus.CONFIRMED, BookingStatus.CANCEL_REQUESTED]),
        Booking.driver_id.isnot(None),
        Booking.start_date <= end_date,
        Booking.end_date >= start_date
    ).all()
    
    busy_driver_ids = {b.driver_id for b in overlapping_bookings}
    
    available_drivers = [d for d in all_drivers if d.driver_id not in busy_driver_ids]
    return available_drivers
