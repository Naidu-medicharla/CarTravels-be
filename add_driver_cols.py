import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.database.db import engine
from sqlalchemy import text

def add_columns():
    with engine.begin() as conn:
        try:
            conn.execute(text("ALTER TABLE bookings ADD COLUMN driver_id VARCHAR(50) DEFAULT NULL"))
            print("Added driver_id")
        except Exception as e:
            print(f"Error adding driver_id: {e}")
            
        try:
            conn.execute(text("ALTER TABLE bookings ADD COLUMN driver_name VARCHAR(150) DEFAULT NULL"))
            print("Added driver_name")
        except Exception as e:
            print(f"Error adding driver_name: {e}")
            
        try:
            conn.execute(text("ALTER TABLE bookings ADD COLUMN driver_phone VARCHAR(20) DEFAULT NULL"))
            print("Added driver_phone")
        except Exception as e:
            print(f"Error adding driver_phone: {e}")

if __name__ == "__main__":
    add_columns()
