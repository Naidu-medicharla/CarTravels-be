from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import date, datetime, timedelta
import locale

from src.models.booking import Booking, BookingStatus, BookingType
from src.models.car import Car
from src.models.user import User

def format_currency(amount: float) -> str:
    # A simple formatter for INR if locale isn't strictly configured
    s = str(int(amount))
    if len(s) > 3:
        last_three = s[-3:]
        other = s[:-3]
        other_chunks = []
        while other:
            other_chunks.insert(0, other[-2:])
            other = other[:-2]
        formatted = ",".join(other_chunks) + "," + last_three
        return f"₹{formatted}"
    return f"₹{s}"


def time_ago(dt: datetime) -> str:
    now = datetime.now(dt.tzinfo)
    diff = now - dt
    if diff.days > 0:
        return f"{diff.days} days ago"
    hours = diff.seconds // 3600
    if hours > 0:
        return f"{hours} hrs ago"
    minutes = (diff.seconds % 3600) // 60
    if minutes > 0:
        return f"{minutes} mins ago"
    return "Just now"


def get_dashboard_details(db: Session) -> dict:
    today = date.today()
    yesterday = today - timedelta(days=1)
    first_of_month = today.replace(day=1)
    
    # 1. KPIs
    # Total bookings today (created today)
    today_bookings_count = db.query(Booking).filter(
        func.date(Booking.created_at) == today
    ).count()
    
    # Today revenue (CONFIRMED/COMPLETED created today)
    today_revenue_val = db.query(func.sum(Booking.total_amount)).filter(
        func.date(Booking.created_at) == today,
        Booking.status.in_([BookingStatus.CONFIRMED, BookingStatus.COMPLETED])
    ).scalar() or 0.0
    
    # Available cars
    available_cars = db.query(Car).filter(Car.available == True).count()
    
    # Under maintenance cars
    under_maintenance = db.query(Car).filter(Car.available == False).count()
    
    # 2. Today Schedule (based on start_date or pickup_date)
    # RENTAL starts today, OUTSTATION pickup today
    scheduled_bookings = db.query(Booking, User, Car).join(
        User, Booking.user_id == User.id
    ).join(
        Car, Booking.car_id == Car.id
    ).filter(
        ( (Booking.booking_type == BookingType.RENTAL) & (Booking.start_date == today) ) |
        ( (Booking.booking_type == BookingType.OUTSTATION) & (func.date(Booking.pickup_date) == today) )
    ).all()
    
    today_schedule_list = []
    for b, u, c in scheduled_bookings:
        if b.booking_type == BookingType.RENTAL:
            time_str = "All Day"
            title = "Rental"
            pickup = "Store"
            destination = "Return to Store"
        else:
            time_str = b.pickup_date.strftime("%I:%M %p") if b.pickup_date else "N/A"
            title = "Outstation"
            pickup = b.pickup_location or "N/A"
            destination = b.drop_location or "N/A"
            
        today_schedule_list.append({
            "id": f"BKG-{b.id}",
            "time": time_str,
            "title": title,
            "customer": u.name,
            "phone": u.phone,
            "vehicle": f"{c.brand} {c.model}",
            "plate": c.car_number,
            "driver": b.driver_name or "Not Assigned",
            "pickup": pickup,
            "destination": destination,
            "status": b.status.value if hasattr(b.status, 'value') else b.status,
            "payment": "Paid" if b.status in [BookingStatus.CONFIRMED, BookingStatus.COMPLETED] else "Pending"
        })
        
    # 3. Recent Bookings (last 3)
    recent = db.query(Booking, User, Car).join(
        User, Booking.user_id == User.id
    ).join(
        Car, Booking.car_id == Car.id
    ).order_by(Booking.created_at.desc()).limit(3).all()
    
    recent_bookings_list = []
    for b, u, c in recent:
        recent_bookings_list.append({
            "customer": u.name,
            "vehicle": f"{c.brand} {c.model}",
            "time": time_ago(b.created_at) if b.created_at else "Unknown",
            "status": b.status.value if hasattr(b.status, 'value') else b.status
        })
        
    # 4. Revenue Summary
    yesterday_revenue_val = db.query(func.sum(Booking.total_amount)).filter(
        func.date(Booking.created_at) == yesterday,
        Booking.status.in_([BookingStatus.CONFIRMED, BookingStatus.COMPLETED])
    ).scalar() or 0.0
    
    this_month_revenue_val = db.query(func.sum(Booking.total_amount)).filter(
        func.date(Booking.created_at) >= first_of_month,
        func.date(Booking.created_at) <= today,
        Booking.status.in_([BookingStatus.CONFIRMED, BookingStatus.COMPLETED])
    ).scalar() or 0.0
    
    return {
        "kpis": {
            "today_bookings": today_bookings_count,
            "today_revenue": format_currency(today_revenue_val),
            "available_cars": available_cars,
            "under_maintenance": under_maintenance
        },
        "today_schedule": today_schedule_list,
        "recent_bookings": recent_bookings_list,
        "revenue_summary": {
            "today": format_currency(today_revenue_val),
            "yesterday": format_currency(yesterday_revenue_val),
            "this_month": format_currency(this_month_revenue_val)
        }
    }
