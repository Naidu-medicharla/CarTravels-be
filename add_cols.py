import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.database.db import engine
from sqlalchemy import text

def add_columns():
    with engine.begin() as conn:
        try:
            conn.execute(text("ALTER TABLE bookings ADD COLUMN rating FLOAT DEFAULT NULL"))
            print("Added rating")
        except Exception as e:
            print(f"Error adding rating: {e}")

if __name__ == "__main__":
    add_columns()
