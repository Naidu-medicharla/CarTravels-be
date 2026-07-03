"""
Run this script ONCE to:
  1. Create the `car_travels` database (if not exists).
  2. Create all tables from the SQLAlchemy models.
  3. Insert the default ADMIN user.

Usage (inside your venv):
    python scripts/init_db.py
"""

import sys
import os

# Allow imports from project root
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from src.database.db import engine, SessionLocal, Base
from src.models.user import User, UserRole          # registers User model
from src.models.car import Car, CarImage            # registers Car & CarImage models
from src.models.booking import Booking              # registers Booking model
from src.core.security import hash_password

ADMIN_NAME     = "Bunny"
ADMIN_EMAIL    = "naidumedicharla830@gmail.com"
ADMIN_PASSWORD = "Bunnynaidu@830"


def init():
    print("📦 Creating tables...")
    Base.metadata.create_all(bind=engine)
    print("✅ Tables created.")

    db = SessionLocal()
    try:
        existing_admin = db.query(User).filter(User.email == ADMIN_EMAIL).first()
        if existing_admin:
            print("ℹ️  Admin user already exists — skipping seed.")
            return

        admin = User(
            name="Bunny",
            email="naidumedicharla830@gmail.com",
            password_hash=hash_password(ADMIN_PASSWORD),
            role=UserRole.ADMIN,
            is_active=True,
        )
        db.add(admin)
        db.commit()
        print("🎉 Admin user created successfully!")
        print(f"   Name    : {ADMIN_NAME}")
        print(f"   Email   : {ADMIN_EMAIL}")
        print(f"   Password: {ADMIN_PASSWORD}  (hashed in DB)")
        print(f"   Role    : ADMIN")
    finally:
        db.close()


if __name__ == "__main__":
    init()
