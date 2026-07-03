"""
notification_service.py

Central helper for creating database-backed notifications.
Call create_notification() from any service or router after a business event commits.
"""
from typing import Optional
from sqlalchemy.orm import Session

from src.models.notification import Notification, NotificationType, NotificationRecipientRole
from src.models.user import User, UserRole
from src.services.notification_pubsub import pubsub
from src.core.events import event_bus


def _notify_all_admins(
    db: Session,
    n_type: NotificationType,
    title: str,
    message: str,
    reference_id: Optional[str] = None,
):
    """Insert one notification row per admin user."""
    admins = db.query(User).filter(User.role == UserRole.ADMIN, User.is_active == True).all()
    admin_notifs = []
    for admin in admins:
        notif = Notification(
            recipient_id   = admin.id,
            recipient_role = NotificationRecipientRole.ADMIN,
            type           = n_type,
            title          = title,
            message        = message,
            reference_id   = reference_id,
        )
        db.add(notif)
        admin_notifs.append(notif)
    # Commit all at once
    db.commit()

    # Dispatch to Pub/Sub instantly
    for notif in admin_notifs:
        db.refresh(notif)
        payload = {
            "id": notif.id,
            "type": notif.type.value,
            "title": notif.title,
            "message": notif.message,
            "reference_id": notif.reference_id,
            "is_read": notif.is_read,
            "created_at": notif.created_at.isoformat() if notif.created_at else None,
        }
        pubsub.notify_user(notif.recipient_id, [payload])


def notify_user(
    db: Session,
    user_id: int,
    n_type: NotificationType,
    title: str,
    message: str,
    reference_id: Optional[str] = None,
):
    """Insert one notification row for a specific user."""
    notif = Notification(
        recipient_id   = user_id,
        recipient_role = NotificationRecipientRole.USER,
        type           = n_type,
        title          = title,
        message        = message,
        reference_id   = reference_id,
    )
    db.add(notif)
    db.commit()
    db.refresh(notif)
    
    payload = {
        "id": notif.id,
        "type": notif.type.value,
        "title": notif.title,
        "message": notif.message,
        "reference_id": notif.reference_id,
        "is_read": notif.is_read,
        "created_at": notif.created_at.isoformat() if notif.created_at else None,
    }
    pubsub.notify_user(user_id, [payload])


# ── Public convenience wrappers (now Event Listeners) ───────────────────────

@event_bus.subscribe("booking-created")
def notify_admins_new_booking(db: Session, booking_id: str, user_name: str, car_number: str):
    _notify_all_admins(
        db,
        NotificationType.NEW_BOOKING,
        title   = "New Booking Received",
        message = f"{user_name} booked car {car_number}.",
        reference_id = str(booking_id),
    )


@event_bus.subscribe("cancellation-requested")
def notify_admins_cancel_request(db: Session, booking_id: str, user_name: str, car_number: str, reason: str):
    _notify_all_admins(
        db,
        NotificationType.CANCEL_REQUEST,
        title   = "Cancellation Request",
        message = f"{user_name} requested cancellation for car {car_number}. Reason: {reason}",
        reference_id = str(booking_id),
    )


@event_bus.subscribe("ticket-created")
def notify_admins_new_ticket(db: Session, ticket_id: int, full_name: str, subject: str):
    _notify_all_admins(
        db,
        NotificationType.NEW_TICKET,
        title   = "New Support Ticket",
        message = f"{full_name} submitted a ticket: '{subject}'",
        reference_id = str(ticket_id),
    )


@event_bus.subscribe("driver-assigned")
def notify_user_driver_assigned(db: Session, user_id: int, booking_id: str, driver_name: str):
    notify_user(
        db,
        user_id      = user_id,
        n_type       = NotificationType.DRIVER_ASSIGNED,
        title        = "Driver Assigned",
        message      = f"Driver {driver_name} has been assigned to your booking {booking_id}.",
        reference_id = str(booking_id),
    )


@event_bus.subscribe("cancellation-approved")
def notify_user_cancellation_approved(db: Session, user_id: int, booking_id: str, car_number: str):
    notify_user(
        db,
        user_id      = user_id,
        n_type       = NotificationType.CANCELLATION_APPROVED,
        title        = "Cancellation Approved",
        message      = f"Your cancellation request for car {car_number} (booking {booking_id}) has been approved.",
        reference_id = str(booking_id),
    )


@event_bus.subscribe("cancellation-rejected")
def notify_user_cancellation_rejected(db: Session, user_id: int, booking_id: str, reason: str):
    notify_user(
        db,
        user_id      = user_id,
        n_type       = NotificationType.CANCELLATION_REJECTED,
        title        = "Cancellation Rejected",
        message      = f"Your cancellation request for booking {booking_id} was rejected. Reason: {reason}",
        reference_id = str(booking_id),
    )


@event_bus.subscribe("ticket-replied")
def notify_user_ticket_reply(db: Session, user_id: int, ticket_id: int, subject: str):
    notify_user(
        db,
        user_id      = user_id,
        n_type       = NotificationType.TICKET_REPLY,
        title        = "Ticket Reply",
        message      = f"Admin has replied to your ticket: '{subject}'",
        reference_id = str(ticket_id),
    )


@event_bus.subscribe("booking-milestone")
def check_and_notify_booking_milestone(db: Session):
    """Notify admins at every 50th confirmed booking."""
    from src.models.booking import Booking, BookingStatus
    total = db.query(Booking).filter(Booking.status == BookingStatus.CONFIRMED).count()
    if total > 0 and total % 50 == 0:
        _notify_all_admins(
            db,
            NotificationType.BOOKING_MILESTONE,
            title   = f"🎉 Booking Milestone: {total} Bookings!",
            message = f"Congratulations! The platform has reached {total} confirmed bookings.",
            reference_id = str(total),
        )


@event_bus.subscribe("booking-confirmed")
def notify_user_booking_confirmed(db: Session, user_id: int, booking_id: str, car_number: str):
    notify_user(
        db,
        user_id      = user_id,
        n_type       = NotificationType.BOOKING_CONFIRMED,
        title        = "Booking Confirmed",
        message      = f"Your booking {booking_id} for car {car_number} has been confirmed.",
        reference_id = str(booking_id),
    )
