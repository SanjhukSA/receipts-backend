"""Shared FastAPI dependencies — DB session."""

from typing import Generator

from app.database import SessionLocal


def get_db() -> Generator:
    """
    Args:
        None.
    Return:
        Generator yielding an active SQLAlchemy Session.
    Provides a database session for a request and closes it upon completion.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()