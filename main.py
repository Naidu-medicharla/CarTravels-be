from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from src.core.config import CORS_ORIGINS
from src.routers import (
    auth, admin, admin_cars, admin_bookings,
    cars, bookings, notifications, users,
    admin_drivers, admin_dashboard, tickets,
)
import os

# Import notification_service to register its EventBus subscribers
import src.services.notification_service

app = FastAPI(
    title="CarTravels API",
    description="Car Travel Booking Platform",
    version="1.0.0"
)

# ── CORS ──────────────────────────────────────────────────────────────────────
# Origins are read from CORS_ORIGINS env var (comma-separated).
# Set on Fly.io with: fly secrets set CORS_ORIGINS=https://your-app.pages.dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Static files ───────────────────────────────────────────────────────────────
os.makedirs("uploads/car_images", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(auth.router,             prefix="/auth",             tags=["Authentication"])
app.include_router(admin.router,            prefix="/admin",            tags=["Admin - Users"])
app.include_router(admin_cars.router,       prefix="/admin",            tags=["Admin - Cars"])
app.include_router(admin_bookings.router,   prefix="/admin",            tags=["Admin - Bookings"])
app.include_router(cars.router,             prefix="/cars",             tags=["Cars (Public)"])
app.include_router(bookings.router,         prefix="/bookings",         tags=["Bookings"])
app.include_router(notifications.router,    prefix="/notification",     tags=["Notifications"])
app.include_router(users.router,                                        tags=["Users"])
app.include_router(admin_drivers.router,    prefix="/admin",            tags=["Admin - Drivers"])
app.include_router(admin_dashboard.router,  prefix="/admin/dashboard",  tags=["Admin - Dashboard"])
app.include_router(tickets.router)


# ── Core endpoints ─────────────────────────────────────────────────────────────
@app.get("/")
def root():
    return {"message": "Welcome to CarTravels API 🚗"}


@app.get("/health", tags=["Health"])
def health():
    """Health check endpoint used by Fly.io and Docker to verify the app is running."""
    return {"status": "healthy", "service": "cartravels-api"}
