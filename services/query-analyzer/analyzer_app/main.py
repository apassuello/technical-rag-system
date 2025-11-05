"""
Query Analyzer Service - FastAPI Application.

This module implements the main FastAPI application for the Query Analyzer service,
providing both REST and gRPC endpoints for query analysis functionality.
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
from .core.config import get_settings, get_analyzer_config
from .core.analyzer import QueryAnalyzerService
from .schemas.requests import AnalyzeRequest
from .schemas.responses import AnalyzeResponse, HealthResponse

# Configure structured logging
logging.basicConfig(level=logging.INFO)
logger = structlog.get_logger(__name__)

# Prometheus metrics
REQUEST_COUNT = Counter('query_analyzer_requests_total', 'Total number of analysis requests', ['endpoint', 'status'])
REQUEST_DURATION = Histogram('query_analyzer_request_duration_seconds', 'Request duration in seconds', ['endpoint'])
ANALYSIS_COMPLEXITY = Counter('query_analyzer_complexity_total', 'Queries by complexity level', ['complexity'])
SERVICE_HEALTH = Gauge('query_analyzer_service_health', 'Service health status (1=healthy, 0=unhealthy)')

# Global service instance
analyzer_service: Optional[QueryAnalyzerService] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle - startup and shutdown."""
    global analyzer_service
    
    logger.info("Starting Query Analyzer Service")
    
    # Initialize service
    settings = get_settings()
    analyzer_config = get_analyzer_config()
    analyzer_service = QueryAnalyzerService(config=analyzer_config)
    
    # Initialize health metrics
    SERVICE_HEALTH.set(1)
    
    logger.info("Query Analyzer Service started successfully")
    
    yield
    
    logger.info("Shutting down Query Analyzer Service")
    SERVICE_HEALTH.set(0)


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    
    app = FastAPI(
        title="Query Analyzer Service",
        description="Microservice for query analysis and complexity classification",
        version="1.0.0",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc"
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include routers
    app.include_router(rest.router, prefix="/api/v1")
    
    # Add Prometheus metrics endpoint
    metrics_app = make_asgi_app()
    app.mount("/metrics", metrics_app)
    
    return app


def get_analyzer_service() -> QueryAnalyzerService:
    """Dependency to get the analyzer service instance."""
    if analyzer_service is None:
        raise HTTPException(status_code=503, detail="Service not initialized")
    return analyzer_service


# Create app instance
app = create_app()


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    try:
        if analyzer_service is None:
            raise HTTPException(status_code=503, detail="Service not initialized")
        
        # Perform basic health checks
        is_healthy = await analyzer_service.health_check()
        
        return HealthResponse(
            status="healthy" if is_healthy else "unhealthy",
            service="query-analyzer",
            version="1.0.0",
            details={
                "analyzer_initialized": analyzer_service is not None,
                "components_loaded": is_healthy
            }
        )
    except Exception as e:
        logger.error("Health check failed", error=str(e))
        return HealthResponse(
            status="unhealthy",
            service="query-analyzer",
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
    if analyzer_service is None:
        raise HTTPException(status_code=503, detail="Service not ready")

    is_ready = await analyzer_service.health_check()
    if not is_ready:
        raise HTTPException(status_code=503, detail="Service not ready")

    return {"status": "ready"}


@app.get("/health/startup")
async def startup_probe():
    """Kubernetes startup probe."""
    if analyzer_service is None:
        raise HTTPException(status_code=503, detail="Service not started")
    return {"status": "started"}


if __name__ == "__main__":
    from .core.config import get_settings
    settings = get_settings()
    uvicorn.run(
        "analyzer_app.main:app",
        host=settings.host,
        port=settings.port,
        reload=True,
        log_level="info"
    )