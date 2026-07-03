import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "")

# Comma-separated list of allowed CORS origins
# e.g. "http://localhost:5173,https://myapp.pages.dev"
CORS_ORIGINS: list[str] = [
    origin.strip()
    for origin in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
    if origin.strip()
]

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "changeme")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", 60))

ORS_API_KEY = os.getenv("ORS_API_KEY", "")
