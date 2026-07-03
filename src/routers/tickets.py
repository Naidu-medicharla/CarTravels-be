from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from src.database.db import get_db
from src.models.ticket import Ticket, TicketStatus
from src.models.user import User
from src.schemas.ticket import TicketCreate, TicketOut, AdminReplyRequest
from src.core.dependencies import get_current_user_optional, get_current_user, require_admin
from src.core.events import event_bus

router = APIRouter(prefix="/tickets", tags=["Tickets"])


@router.post("", response_model=TicketOut, status_code=status.HTTP_201_CREATED, summary="Create a support ticket")
def create_ticket(
    payload: TicketCreate,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
):
    ticket = Ticket(
        **payload.model_dump(),
        user_id=current_user.id if current_user else None
    )
    db.add(ticket)
    db.commit()
    db.refresh(ticket)

    # Notify all admins
    try:
        event_bus.publish("ticket-created",
            db=db,
            ticket_id = ticket.ticket_id,
            full_name = ticket.full_name,
            subject   = ticket.subject,
        )
    except Exception:
        pass

    return ticket


@router.get("/my", response_model=List[TicketOut], summary="Get my tickets")
def get_my_tickets(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    tickets = db.query(Ticket).filter(Ticket.user_id == current_user.id).order_by(Ticket.created_at.desc()).all()
    return tickets


@router.get("/admin", response_model=List[TicketOut], summary="Get all tickets (Admin)")
def get_all_tickets_admin(
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    tickets = db.query(Ticket).order_by(Ticket.created_at.desc()).all()
    return tickets


@router.patch("/admin/{ticket_id}/reply", response_model=TicketOut, summary="Reply to ticket (Admin)")
def reply_to_ticket(
    ticket_id: int,
    payload: AdminReplyRequest,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
):
    ticket = db.query(Ticket).filter(Ticket.ticket_id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    ticket.admin_reply = payload.admin_reply
    if payload.mark_resolved:
        ticket.status = TicketStatus.RESOLVED

    db.commit()
    db.refresh(ticket)

    # Notify the user who submitted the ticket (if they were logged in)
    if ticket.user_id:
        try:
            event_bus.publish("ticket-replied",
                db=db,
                user_id   = ticket.user_id,
                ticket_id = ticket.ticket_id,
                subject   = ticket.subject,
            )
        except Exception:
            pass

    return ticket

