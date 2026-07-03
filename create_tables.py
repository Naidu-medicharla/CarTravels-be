import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.database.db import engine
from src.models import *
from src.models.driver import Driver
from src.database.db import Base

def create_tables():
    print("Creating tables...")
    Base.metadata.create_all(bind=engine)
    print("Tables created successfully.")

if __name__ == "__main__":
    create_tables()
