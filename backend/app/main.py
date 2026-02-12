"""
Stock Exchange Prediction API - Main Application Entry Point

This module configures the FastAPI application with security middleware,
routers, and proper error handling for production deployment.
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import uuid
import time

from db.session import engine, Base
from db import models
from common.config import settings
from common.logging import get_logger
from app.middleware.rate_limit import RateLimitMiddleware
from app.routers import auth, users, billing, analysis

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup and shutdown events."""
    # Startup
    logger.info("Starting Stock Exchange Prediction API", extra={
        "event": "startup",
        "env": settings.ENV,
        "debug": settings.DEBUG
    })

    # Only auto-create tables in development (use Alembic migrations in prod)
    if settings.ENV in ("dev", "development", "test"):
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created/verified (dev mode)")
    else:
        logger.info("Skipping auto table creation (production mode)")
    
    yield
    
    # Shutdown
    logger.info("Shutting down application", extra={"event": "shutdown"})


# Create FastAPI application
app = FastAPI(
    title="Stock Exchange Prediction API",
    description="API for stock analysis and prediction services",
    version="1.0.0",
    lifespan=lifespan,
    # Disable docs in production
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    openapi_url="/openapi.json" if settings.DEBUG else None,
)


# =============================================================================
# CORS Middleware
# =============================================================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID", "X-RateLimit-Limit", "X-RateLimit-Remaining"],
)


# =============================================================================
# Rate Limiting Middleware
# =============================================================================
app.add_middleware(RateLimitMiddleware)


# =============================================================================
# Request ID & Logging Middleware
# =============================================================================
@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):
    """Add request ID, log requests, and track timing."""
    # Generate unique request ID
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    
    # Track request timing
    start_time = time.time()
    
    # Log incoming request
    logger.info(
        f"Request started: {request.method} {request.url.path}",
        extra={
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "event": "request_start"
        }
    )
    
    try:
        response = await call_next(request)
        
        # Calculate duration
        duration_ms = (time.time() - start_time) * 1000
        
        # Add request ID to response headers
        response.headers["X-Request-ID"] = request_id
        
        # Log completed request
        logger.info(
            f"Request completed: {request.method} {request.url.path} -> {response.status_code}",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": round(duration_ms, 2),
                "event": "request_complete"
            }
        )
        
        return response
        
    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        logger.exception(
            f"Request failed: {request.method} {request.url.path}",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "duration_ms": round(duration_ms, 2),
                "event": "request_error"
            }
        )
        raise


# =============================================================================
# Security Headers Middleware
# =============================================================================
@app.middleware("http")
async def security_headers_middleware(request: Request, call_next):
    """Add security headers to all responses."""
    response = await call_next(request)
    
    # Prevent MIME type sniffing
    response.headers["X-Content-Type-Options"] = "nosniff"
    
    # Prevent clickjacking
    response.headers["X-Frame-Options"] = "DENY"
    
    # XSS protection (legacy browsers)
    response.headers["X-XSS-Protection"] = "1; mode=block"
    
    # Enforce HTTPS (enable in production with proper SSL)
    if settings.ENV == "production":
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    
    # Referrer policy
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    
    # Content Security Policy (adjust as needed for your frontend)
    response.headers["Content-Security-Policy"] = "default-src 'self'"
    
    return response


# =============================================================================
# Global Exception Handler
# =============================================================================
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Handle unhandled exceptions gracefully.
    
    In production, hide internal error details. In debug mode, show them.
    """
    request_id = getattr(request.state, "request_id", "unknown")
    
    logger.exception(
        f"Unhandled exception: {type(exc).__name__}: {str(exc)}",
        extra={
            "request_id": request_id,
            "path": request.url.path,
            "method": request.method,
            "event": "unhandled_exception"
        }
    )
    
    if settings.DEBUG:
        return JSONResponse(
            status_code=500,
            content={
                "detail": str(exc),
                "type": type(exc).__name__,
                "request_id": request_id
            }
        )
    
    return JSONResponse(
        status_code=500,
        content={
            "detail": "An internal error occurred. Please try again later.",
            "request_id": request_id
        }
    )


# =============================================================================
# Health Check Endpoints
# =============================================================================
@app.get("/health", tags=["health"])
def health_check():
    """
    Health check endpoint for load balancers and container orchestration.
    """
    return {"status": "healthy", "service": "stock-api"}


@app.get("/health/ready", tags=["health"])
def readiness_check():
    """
    Readiness check - verifies database connectivity.
    """
    try:
        from db.session import SessionLocal
        db = SessionLocal()
        db.execute("SELECT 1")
        db.close()
        return {"status": "ready", "database": "connected"}
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={"status": "not ready", "database": "disconnected"}
        )


# =============================================================================
# Root Endpoint
# =============================================================================
@app.get("/", tags=["root"])
def root():
    """API root - returns basic service info."""
    return {
        "service": "Stock Exchange Prediction API",
        "version": "1.0.0",
        "status": "operational"
    }


@app.get("/home", tags=["root"])
def welcome_message():
    """Legacy welcome endpoint."""
    return {"message": "Welcome to the Stock Exchange Prediction API"}


# =============================================================================
# Register API Routers
# =============================================================================
app.include_router(auth.router, prefix="/auth", tags=["authentication"])
app.include_router(users.router, prefix="/users", tags=["users"])
app.include_router(billing.router, prefix="/billing", tags=["billing"])
app.include_router(analysis.router, prefix="/analysis", tags=["analysis"])
