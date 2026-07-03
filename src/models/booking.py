import enum
from sqlalchemy import (
    Column, Integer, String, Float, Date,
    Enum, DateTime, ForeignKey, Boolean
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from src.database.db import Base


class BookingType(str, enum.Enum):
    RENTAL     = "RENTAL"
    OUTSTATION = "OUTSTATION"


class BookingStatus(str, enum.Enum):
    PENDING   = "PENDING"
    CONFIRMED = "CONFIRMED"
    CANCELLED = "CANCELLED"
    COMPLETED = "COMPLETED"
    CANCEL_REQUESTED = "CANCEL_REQUESTED"


class Booking(Base):
    __tablename__ = "bookings"

    id           = Column(Integer, primary_key=True, index=True, autoincrement=True)
    booking_id   = Column(String(50), unique=True, index=True, nullable=True) # E.g., BKG-1001
    user_id      = Column(Integer, ForeignKey("users.id"), nullable=False)
    car_id       = Column(Integer, ForeignKey("cars.id"), nullable=False)
    car_number   = Column(String(50), nullable=True)
    booking_type = Column(Enum(BookingType, name="bookingtype", create_type=True), nullable=False)
    status       = Column(Enum(BookingStatus, name="bookingstatus", create_type=True), default=BookingStatus.PENDING)

    # ── Rental fields ────────────────────────────────────────────────────────
    start_date      = Column(Date, nullable=True)
    end_date        = Column(Date, nullable=True)
    num_days        = Column(Integer, nullable=True)
    driver_required = Column(Boolean, default=False)
    driver_charges  = Column(Float, default=0.0)

    # ── Outstation fields ────────────────────────────────────────────────────
    pickup_location = Column(String(200), nullable=True)
    drop_location   = Column(String(200), nullable=True)
    pickup_date     = Column(Date, nullable=True)
    distance_km     = Column(Float, nullable=True)

    # ── Common ───────────────────────────────────────────────────────────────
    car_charges = Column(Float, nullable=True)
    discount = Column(Float, nullable=True)
    total_amount_before_discount = Column(Float, nullable=True)
    total_amount = Column(Float, nullable=False)
    # ── Payment fields ───────────────────────────────────────────────────────
    amount_paid     = Column(Float, nullable=True)
    paid_by         = Column(String(100), nullable=True)
    payment_channel = Column(String(50), nullable=True)
    payment_status  = Column(String(50), nullable=True)

    # ── Rating fields ────────────────────────────────────────────────────────
    is_trip_completed = Column(Boolean, default=False)
    is_rated          = Column(Boolean, default=False)
    rating            = Column(Float, nullable=True)

    # ── Driver Info (Rental/Outstation if applicable) ────────────────────────
    driver_id   = Column(String(50), nullable=True)
    driver_name = Column(String(150), nullable=True)
    driver_phone = Column(String(20), nullable=True)

    # ── Cancellation Fields ──────────────────────────────────────────────────
    cancel_reason = Column(String(500), nullable=True)
    admin_reject_reason = Column(String(500), nullable=True)

    created_at   = Column(DateTime(timezone=True), server_default=func.now())
    updated_at   = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="bookings")
    car  = relationship("Car")
