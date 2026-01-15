"""FastAPI application entry point."""

import asyncio
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router as api_router
from app.api.websocket import router as ws_router
from app.db.redis import cache
from app.config import settings
from app.db.session import init_db, close_db
from app.db.redis import init_redis, close_redis
from app.etl.scheduler import start_scheduler, stop_scheduler

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """Application lifecycle manager."""
    logger.info("starting_application", app=settings.app_name)
    
    # Initialize database
    await init_db()
    logger.info("database_initialized")
    
    # Initialize Redis
    await init_redis()
    logger.info("redis_initialized")
    
    # Start ETL scheduler
    await start_scheduler()
    logger.info("scheduler_started")
    
    yield
    
    # Cleanup
    logger.info("shutting_down_application")
    await stop_scheduler()
    await close_redis()
    await close_db()
    logger.info("application_stopped")


app = FastAPI(
    title=settings.app_name,
    description="PSP Dashboard Backend API - Aggregates payment data from Vima and PayShack",
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(api_router, prefix="/api/v1")
app.include_router(ws_router, prefix="/ws")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": settings.app_name,
        "version": "0.1.0"
    }


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "PSP Dashboard API",
        "docs": "/api/docs",
        "health": "/health"
    }
