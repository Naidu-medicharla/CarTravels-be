import enum
from sqlalchemy import (
    Column, Integer, String, Boolean, Enum,
    Float, Text, DateTime, ForeignKey
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from src.database.db import Base


class FuelType(str, enum.Enum):
    PETROL   = "Petrol"
    DIESEL   = "Diesel"
    ELECTRIC = "Electric"
    HYBRID   = "Hybrid"
    CNG      = "CNG"


class TransmissionType(str, enum.Enum):
    AUTOMATIC = "Automatic"
    MANUAL    = "Manual"


class AvailabilityType(str, enum.Enum):
    RENTAL     = "Rental"
    OUTSTATION = "Outstation"
    BOTH       = "Both"


class Car(Base):
    __tablename__ = "cars"

    id            = Column(Integer, primary_key=True, index=True, autoincrement=True)
    car_number    = Column(String(50), unique=True, nullable=False, index=True)
    brand         = Column(String(100), nullable=False, index=True)
    model         = Column(String(100), nullable=False)
    year          = Column(Integer, nullable=False)
    fuel_type     = Column(Enum(FuelType, name="fueltype", create_type=True), nullable=False)
    transmission  = Column(Enum(TransmissionType, name="transmissiontype", create_type=True), nullable=False)
    price_per_day = Column(Float, nullable=False)
    price_per_km  = Column(Float, nullable=True)   # for outstation bookings
    seats         = Column(Integer, nullable=False)
    location      = Column(String(150), nullable=False, index=True)
    description   = Column(Text, nullable=True)
    availability_type = Column(Enum(AvailabilityType, name="availabilitytype", create_type=True), default=AvailabilityType.BOTH)
    available     = Column(Boolean, default=True)
    is_deleted    = Column(Boolean, default=False)   # soft delete flag
    created_at    = Column(DateTime(timezone=True), server_default=func.now())
    updated_at    = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    images = relationship("CarImage", back_populates="car", cascade="all, delete-orphan")
    bookings = relationship("Booking", back_populates="car")

    @property
    def upcoming_bookings(self):
        from datetime import date
        from src.models.booking import BookingStatus
        today = date.today()
        active_statuses = [BookingStatus.PENDING, BookingStatus.CONFIRMED, BookingStatus.CANCEL_REQUESTED]
        
        upcoming = []
        for b in self.bookings:
            if b.status in active_statuses:
                if b.end_date and b.end_date >= today:
                    upcoming.append(b)
                elif b.pickup_date and b.pickup_date >= today:
                    upcoming.append(b)
        return upcoming


class CarImage(Base):
    __tablename__ = "car_images"

    id         = Column(Integer, primary_key=True, autoincrement=True)
    car_id     = Column(Integer, ForeignKey("cars.id", ondelete="CASCADE"), nullable=False)
    image_path = Column(String(500), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    car = relationship("Car", back_populates="images")
