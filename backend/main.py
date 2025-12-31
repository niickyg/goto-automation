"""
Main FastAPI application for GoTo Call Automation System.

This is the entry point that ties together all routers and services.
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from config import get_settings, configure_logging
from database import db_manager
from sqlalchemy import text
import webhooks, calls, actions, kpi, billing

# Configure logging
configure_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.

    Handles startup and shutdown events.
    """
    # Startup
    logger.info("Starting GoTo Call Automation System...")

    # Initialize database
    db_manager.initialize()
    logger.info("Database initialized")

    # Create tables if they don't exist
    db_manager.create_tables()
    logger.info("Database tables verified")

    yield

    # Shutdown
    logger.info("Shutting down GoTo Call Automation System...")
    db_manager.close()
    logger.info("Database connections closed")


# Create FastAPI application
app = FastAPI(
    title="GoTo Call Automation System",
    description="Automated call recording transcription, AI analysis, and notification system for GoTo Connect",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Configure CORS
settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if not settings.is_production() else ["https://yourdomain.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": str(exc) if not settings.is_production() else "An error occurred"
        }
    )


# Health check endpoint
@app.get("/", tags=["health"])
async def root():
    """Root endpoint with API information."""
    return {
        "service": "GoTo Call Automation System",
        "version": "1.0.0",
        "status": "running",
        "docs": "/docs",
        "health": "/health"
    }


@app.get("/health", tags=["health"])
async def health_check():
    """
    Health check endpoint.

    Returns service health status and component availability.
    """
    from datetime import datetime

    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "components": {
            "database": "unknown",
            "api": "healthy"
        }
    }

    # Check database connection
    try:
        session = db_manager.get_session()
        session.execute(text("SELECT 1"))
        session.close()
        health_status["components"]["database"] = "healthy"
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        health_status["components"]["database"] = "unhealthy"
        health_status["status"] = "degraded"

    return health_status


# Include routers
app.include_router(webhooks.router)
app.include_router(calls.router)
app.include_router(actions.router)
app.include_router(kpi.router)
app.include_router(billing.router)


# Middleware for request logging
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all HTTP requests."""
    logger.info(f"{request.method} {request.url.path}")
    response = await call_next(request)
    logger.info(f"{request.method} {request.url.path} - {response.status_code}")
    return response


def main():
    """Run the application."""
    settings = get_settings()

    logger.info(
        f"Starting server on {settings.api_host}:{settings.api_port} "
        f"(env={settings.app_env})"
    )

    uvicorn.run(
        "backend.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=not settings.is_production(),
        log_level=settings.log_level.lower(),
        access_log=True,
    )


if __name__ == "__main__":
    main()
