import asyncio
import json
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse
from typing import List
from sqlalchemy.orm import Session

from src.database.db import get_db, SessionLocal
from src.core.dependencies import get_current_user
from src.models.user import User
from src.models.notification import Notification
from src.schemas.notification import NotificationOut, UnreadCountOut

router = APIRouter()


# ── SSE Stream ────────────────────────────────────────────────────────────────

@router.get("/stream", summary="SSE stream for real-time notifications")
async def notification_stream(
    request: Request,
    current_user: User = Depends(get_current_user),
):
    """
    Server-Sent Events endpoint using Pub/Sub.
    - Opens one persistent connection per user.
    - Pushes new notifications instantly when they are created.
    - Uses 0 database queries while idle.
    """
    from src.services.notification_pubsub import pubsub
    
    user_id = current_user.id

    async def event_generator():
        q = pubsub.connect(user_id)
        try:
            while True:
                # Check if the client has disconnected
                if await request.is_disconnected():
                    break
                
                try:
                    # Wait for a new notification instantly, or timeout after 30s to send a heartbeat
                    payload = await asyncio.wait_for(q.get(), timeout=30.0)
                    yield f"data: {json.dumps(payload)}\n\n"
                except asyncio.TimeoutError:
                    # Heartbeat — keeps connection alive through proxies/Render
                    yield ": heartbeat\n\n"
        except asyncio.CancelledError:
            # Client disconnected gracefully
            pass
        finally:
            pubsub.disconnect(user_id, q)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control":    "no-cache",
            "Connection":       "keep-alive",
            "X-Accel-Buffering": "no",   # disables Nginx/Render proxy buffering
        },
    )


# ── REST endpoints (kept for backward compatibility) ──────────────────────────

@router.get("", response_model=List[NotificationOut], summary="Get my unread notifications")
def get_my_notifications(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return (
        db.query(Notification)
        .filter(Notification.recipient_id == current_user.id, Notification.is_read == False)
        .order_by(Notification.created_at.desc())
        .all()
    )


@router.get("/count", response_model=UnreadCountOut, summary="Get unread notification count")
def get_notification_count(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    count = (
        db.query(Notification)
        .filter(Notification.recipient_id == current_user.id, Notification.is_read == False)
        .count()
    )
    return {"unread_count": count}


@router.patch("/{notification_id}/read", response_model=NotificationOut, summary="Mark notification as read")
def mark_notification_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    notif = db.query(Notification).filter(
        Notification.id == notification_id,
        Notification.recipient_id == current_user.id,
    ).first()
    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found.")
    notif.is_read = True
    db.commit()
    db.refresh(notif)
    return notif


@router.patch("/read-all", summary="Mark all notifications as read")
def mark_all_notifications_read(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    db.query(Notification).filter(
        Notification.recipient_id == current_user.id,
        Notification.is_read == False,
    ).update({"is_read": True})
    db.commit()
    return {"message": "All notifications marked as read."}
