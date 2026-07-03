from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy.sql import func
from src.database.db import get_db
from src.models.user import User
from src.models.booking import Booking
from src.models.car import Car

router = APIRouter()

@router.get("/{user_email}/profile-details", summary="Get User Profile Details")
def get_user_profile_details(
    user_email: str,
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    # 1. Fetch user by email
    user = db.query(User).filter(User.email == user_email).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    # 2. Fetch all bookings for the user
    bookings = db.query(Booking).filter(Booking.user_id == user.id).all()
    
    total_trips = len(bookings)
    total_spend = sum(b.total_amount for b in bookings if b.total_amount)
    
    # Calculate avg rating from bookings that have a rating
    rated_bookings = [b for b in bookings if b.rating is not None]
    avg_rating = 0.0
    if rated_bookings:
        avg_rating = sum(b.rating for b in rated_bookings) / len(rated_bookings)
        
    # 3. Get recent activity
    # Sort bookings by created_at descending
    recent_bookings = sorted(bookings, key=lambda x: x.created_at, reverse=True)
    recent_activity = []
    
    if recent_bookings:
        b = recent_bookings[0]
        # Fetch car for car name
        car = db.query(Car).filter(Car.id == b.car_id).first()
        car_name = f"{car.brand} {car.model}" if car else "Unknown Car"
        
        # Determine date range string
        if b.booking_type == "RENTAL":
            date_range = f"{b.start_date} to {b.end_date}"
        else:
            date_range = f"{b.pickup_date}"
            
        recent_activity.append({
            "booking_id": b.booking_id,
            "car_name": car_name,
            "date": date_range,
            "amount_paid": b.total_amount
        })
        
    all_bookings_list = []
    for b in recent_bookings:
        # Avoid requerying car if we already know we need it, but doing it in loop is fine for small N
        car = db.query(Car).filter(Car.id == b.car_id).first()
        car_name = f"{car.brand} {car.model}" if car else "Unknown Car"
        
        all_bookings_list.append({
            "id": b.id,
            "booking_id": b.booking_id,
            "car_name": car_name,
            "booking_type": b.booking_type.value if hasattr(b.booking_type, 'value') else b.booking_type,
            "status": b.status.value if hasattr(b.status, 'value') else b.status,
            "start_date": b.start_date,
            "end_date": b.end_date,
            "pickup_date": b.pickup_date,
            "total_amount": b.total_amount,
            "driver_name": b.driver_name,
            "driver_phone": b.driver_phone,
            "cancel_reason": b.cancel_reason,
            "admin_reject_reason": b.admin_reject_reason,
            "is_trip_completed": b.is_trip_completed,
            "is_rated": b.is_rated,
            "rating": b.rating,
            "created_at": b.created_at
        })
        
    return {
        "name": user.name,
        "email": user.email,
        "phone": user.phone,
        "created_at": user.created_at,
        "total_trips": total_trips,
        "total_spend": round(total_spend, 2),
        "avg_rating": round(avg_rating, 2),
        "recent_activity": recent_activity,
        "all_bookings": all_bookings_list
    }
