from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from src.core.config import DATABASE_URL

engine = create_engine(
    DATABASE_URL,
    echo=True,
    pool_pre_ping=True,          # detect stale connections (important for Neon serverless)
    pool_recycle=300,            # recycle connections every 5 minutes
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """FastAPI dependency to get a DB session per request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
