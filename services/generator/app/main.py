"""
Generator Service - FastAPI Application.

This service provides multi-model answer generation capabilities by encapsulating
the Epic1AnswerGenerator with intelligent routing and cost optimization.
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
from .core.generator import GeneratorService
from .schemas.responses import HealthResponse

# Configure structured logging
logging.basicConfig(level=logging.INFO)
logger = structlog.get_logger(__name__)

# Prometheus metrics
MAIN_REQUEST_COUNT = Counter('generator_main_requests_total', 'Total number of generation requests', ['endpoint', 'status'])
MAIN_REQUEST_DURATION = Histogram('generator_main_request_duration_seconds', 'Request duration in seconds', ['endpoint'])
MAIN_MODEL_USAGE = Counter('generator_main_model_usage_total', 'Model usage counts', ['model', 'status'])
MAIN_SERVICE_HEALTH = Gauge('generator_main_service_health', 'Service health status (1=healthy, 0=unhealthy)')

# Global service instance
generator_service: Optional[GeneratorService] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle - startup and shutdown."""
    global generator_service
    
    logger.info("Starting Generator Service")
    
    # Initialize service
    settings = get_settings()
    generator_service = GeneratorService(config=settings.generator_config)
    
    # Initialize health metrics
    MAIN_SERVICE_HEALTH.set(1)
    
    logger.info("Generator Service started successfully")
    
    yield
    
    logger.info("Shutting down Generator Service")
    if generator_service:
        await generator_service.shutdown()
    MAIN_SERVICE_HEALTH.set(0)


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    
    app = FastAPI(
        title="Generator Service",
        description="Multi-model answer generation microservice with intelligent routing",
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


def get_generator_service() -> GeneratorService:
    """Dependency to get the generator service instance."""
    if generator_service is None:
        raise HTTPException(status_code=503, detail="Service not initialized")
    return generator_service


# Create app instance
app = create_app()


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    try:
        if generator_service is None:
            raise HTTPException(status_code=503, detail="Service not initialized")
        
        # Perform basic health checks
        is_healthy = await generator_service.health_check()
        
        return HealthResponse(
            status="healthy" if is_healthy else "unhealthy",
            service="generator",
            version="1.0.0",
            details={
                "generator_initialized": generator_service is not None,
                "components_loaded": is_healthy,
                "models_available": len(await generator_service.get_available_models()) > 0
            }
        )
    except Exception as e:
        logger.error("Health check failed", error=str(e))
        return HealthResponse(
            status="unhealthy",
            service="generator",
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
    if generator_service is None:
        raise HTTPException(status_code=503, detail="Service not ready")
    
    is_ready = await generator_service.health_check()
    if not is_ready:
        raise HTTPException(status_code=503, detail="Service not ready")
    
    return {"status": "ready"}


if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8081,
        reload=True,
        log_level="info"
    )