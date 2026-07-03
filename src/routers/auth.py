from fastapi import APIRouter, Depends, status, Form
from typing import Optional
from sqlalchemy.orm import Session

from src.database.db import get_db
from src.schemas.auth import LoginResponse, MessageResponse
from src.services.auth_service import register_user, login_user
from src.schemas.auth import RegisterRequest, LoginRequest

router = APIRouter()


@router.post(
    "/register",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
)
def register(
    name:     str           = Form(...),
    email:    str           = Form(...),
    phone:    Optional[str] = Form(None),
    password: str           = Form(...),
    db: Session = Depends(get_db),
):
    """
    **POST /auth/register** — multipart/form-data

    Creates a new user account with `role = USER` automatically.
    """
    payload = RegisterRequest(name=name, email=email, phone=phone, password=password)
    register_user(db, payload)
    return {"message": "User registered successfully."}


@router.post(
    "/login",
    response_model=LoginResponse,
    status_code=status.HTTP_200_OK,
    summary="Login for all users (USER & ADMIN)",
)
def login(
    email:    str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    """
    **POST /auth/login** — multipart/form-data

    Returns a JWT access token. Works for both ADMIN and USER.
    """
    payload = LoginRequest(email=email, password=password)
    result  = login_user(db, payload)
    return LoginResponse(
        access_token=result["token"],
        token_type="bearer",
        user=result["user"],
    )
