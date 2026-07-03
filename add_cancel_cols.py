import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.database.db import engine
from sqlalchemy import text

def add_columns():
    with engine.begin() as conn:
        try:
            conn.execute(text("ALTER TABLE bookings ADD COLUMN cancel_reason VARCHAR(500) DEFAULT NULL"))
            print("Added cancel_reason")
        except Exception as e:
            print(f"Error adding cancel_reason: {e}")
            
        try:
            conn.execute(text("ALTER TABLE bookings ADD COLUMN admin_reject_reason VARCHAR(500) DEFAULT NULL"))
            print("Added admin_reject_reason")
        except Exception as e:
            print(f"Error adding admin_reject_reason: {e}")
            
        try:
            conn.execute(text("ALTER TABLE bookings MODIFY COLUMN status ENUM('PENDING', 'CONFIRMED', 'CANCELLED', 'COMPLETED', 'CANCEL_REQUESTED') DEFAULT 'PENDING'"))
            print("Modified status ENUM")
        except Exception as e:
            print(f"Error modifying status ENUM: {e}")

if __name__ == "__main__":
    add_columns()
