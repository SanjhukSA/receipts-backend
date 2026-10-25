"""FastAPI application entry point."""

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import Base, engine
from app.routers import analytics, receipts


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Args:
        app: FastAPI application instance.
    Return:
        Async generator yielding control during application runtime.
    Creates database tables and ensures the uploads directory exists on startup.
    """
    Base.metadata.create_all(bind=engine)
    os.makedirs(settings.upload_dir, exist_ok=True)
    yield


app = FastAPI(
    title="Receipts Backend",
    description="Receipt scanning, expense tracking, and analytics API",
    version="2.0.0",
    lifespan=lifespan,
)

origins = [o.strip() for o in settings.allowed_origins.split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(receipts.router)
app.include_router(analytics.router)


@app.get("/health", tags=["health"])
def health():
    """
    Args:
        None.
    Return:
        Dictionary indicating service health status.
    Returns a simple status check response.
    """
    return {"status": "ok"}