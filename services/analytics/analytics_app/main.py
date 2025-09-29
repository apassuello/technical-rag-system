"""
Analytics Service - FastAPI Application.

This module implements the main FastAPI application for the Analytics service,
providing REST endpoints for cost tracking, performance analytics, and usage trends.

Epic 8 Integration:
- Cost tracking with Epic 1 CostTracker integration
- Performance analytics and SLO monitoring  
- Usage pattern analysis and optimization recommendations
- A/B testing framework support
- Real-time and historical analytics
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Optional

import uvicorn
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from prometheus_client import make_asgi_app, Counter, Histogram, Gauge
import structlog

from .api import rest
from .core.config import get_settings
from .core.analytics import AnalyticsService
from .schemas.responses import HealthResponse

# Configure structured logging
logging.basicConfig(level=logging.INFO)
logger = structlog.get_logger(__name__)

# Prometheus metrics
REQUEST_COUNT = Counter('analytics_requests_total', 'Total number of analytics requests', ['endpoint', 'status'])
REQUEST_DURATION = Histogram('analytics_request_duration_seconds', 'Request duration in seconds', ['endpoint'])
COST_TRACKING_TOTAL = Counter('analytics_cost_tracking_total', 'Total cost tracking records', ['provider', 'model'])
SERVICE_HEALTH = Gauge('analytics_service_health', 'Service health status (1=healthy, 0=unhealthy)')

# Global service instance
analytics_service: Optional[AnalyticsService] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle - startup and shutdown."""
    global analytics_service
    
    logger.info("Starting Analytics Service")
    
    # Initialize service
    settings = get_settings()
    analytics_service = AnalyticsService()
    
    # Initialize health metrics
    SERVICE_HEALTH.set(1)
    
    logger.info("Analytics Service started successfully")
    
    yield
    
    logger.info("Shutting down Analytics Service")
    SERVICE_HEALTH.set(0)


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    
    app = FastAPI(
        title="Analytics Service",
        description="Microservice for cost tracking, performance analytics, and usage trends",
        version="1.0.0",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc"
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "https://yourdomain.com",
            "https://api.yourdomain.com",
            "http://localhost:3000",  # For development
        ],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["Content-Type", "Authorization", "X-Request-ID"],
    )
    
    # Include routers
    app.include_router(rest.router, prefix="/api/v1")
    
    # Add Prometheus metrics endpoint
    metrics_app = make_asgi_app()
    app.mount("/metrics", metrics_app)
    
    return app


def get_analytics_service() -> AnalyticsService:
    """Dependency to get the analytics service instance."""
    if analytics_service is None:
        raise HTTPException(status_code=503, detail="Service not initialized")
    return analytics_service


# Create app instance
app = create_app()


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    try:
        if analytics_service is None:
            raise HTTPException(status_code=503, detail="Service not initialized")
        
        # Perform basic health checks
        is_healthy = await analytics_service.health_check()
        
        return HealthResponse(
            status="healthy" if is_healthy else "unhealthy",
            service="analytics",
            version="1.0.0",
            details={
                "service_initialized": analytics_service is not None,
                "cost_tracker_active": is_healthy,
                "metrics_store_active": is_healthy
            }
        )
    except Exception as e:
        logger.error("Health check failed", error=str(e))
        return HealthResponse(
            status="unhealthy",
            service="analytics",
            version="1.0.0",
            details={"error": str(e)}
        )


@app.get("/health/live")
async def liveness_probe():
    """Kubernetes liveness probe."""
    return {"status": "alive"}


@app.get("/health/ready")
async def readiness_probe():
    """Kubernetes readiness probe."""
    if analytics_service is None:
        raise HTTPException(status_code=503, detail="Service not ready")

    is_ready = await analytics_service.health_check()
    if not is_ready:
        raise HTTPException(status_code=503, detail="Service not ready")

    return {"status": "ready"}


@app.get("/health/startup")
async def startup_probe():
    """Kubernetes startup probe."""
    if analytics_service is None:
        raise HTTPException(status_code=503, detail="Service not started")

    return {"status": "started"}


if __name__ == "__main__":
    uvicorn.run(
        "analytics_app.main:app",
        host="0.0.0.0",
        port=8085,  # Analytics service runs on port 8085
        reload=True,
        log_level="info"
    )