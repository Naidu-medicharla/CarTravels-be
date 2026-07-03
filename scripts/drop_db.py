import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from src.database.db import engine, Base
from src.models.user import User
from src.models.car import Car, CarImage
from src.models.booking import Booking

print("Dropping all tables...")
Base.metadata.drop_all(bind=engine)
print("Done.")
