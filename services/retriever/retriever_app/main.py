"""
Retriever Service - FastAPI Application.

This service provides document retrieval capabilities by encapsulating
Epic 2's ModularUnifiedRetriever with comprehensive error handling,
circuit breakers, and performance monitoring.
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import Optional

import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import make_asgi_app, Counter, Histogram, Gauge
import structlog

from .api import rest
from .core.config import get_settings
from .core.retriever import RetrieverService
from .schemas.responses import HealthResponse, ErrorResponse

# Configure structured logging
logging.basicConfig(level=logging.INFO)
logger = structlog.get_logger(__name__)

# Prometheus metrics
MAIN_REQUEST_COUNT = Counter('retriever_main_requests_total', 'Total number of retrieval requests', ['endpoint', 'status'])
MAIN_REQUEST_DURATION = Histogram('retriever_main_request_duration_seconds', 'Request duration in seconds', ['endpoint'])
MAIN_SERVICE_HEALTH = Gauge('retriever_main_service_health', 'Service health status (1=healthy, 0=unhealthy)')

# Global service instance
retriever_service: Optional[RetrieverService] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle - startup and shutdown."""
    global retriever_service
    
    logger.info("Starting Retriever Service")
    
    # Initialize service
    settings = get_settings()
    retriever_service = RetrieverService(
        config={
            'retriever_config': settings.retriever_config,
            'embedder_config': settings.embedder_config,
            'performance': settings.performance,
            'monitoring': settings.monitoring,
            'development': settings.development
        }
    )
    
    # Set global service instance for the API endpoints
    rest.retriever_service = retriever_service
    
    # Initialize health metrics
    MAIN_SERVICE_HEALTH.set(1)
    
    logger.info("Retriever Service started successfully")
    
    yield
    
    logger.info("Shutting down Retriever Service")
    if retriever_service:
        await retriever_service.shutdown()
    MAIN_SERVICE_HEALTH.set(0)


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    
    settings = get_settings()
    
    app = FastAPI(
        title="Retriever Service",
        description="Document retrieval microservice powered by Epic 2's ModularUnifiedRetriever",
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
    
    # Add global exception handler
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        """Handle unexpected exceptions globally."""
        logger.error(
            "Unhandled exception",
            error=str(exc),
            path=request.url.path,
            method=request.method
        )
        
        # Update error metrics
        MAIN_REQUEST_COUNT.labels(endpoint="global_error", status="error").inc()
        
        return JSONResponse(
            status_code=500,
            content=ErrorResponse(
                error="Internal server error",
                error_code="INTERNAL_ERROR",
                details={
                    "path": request.url.path,
                    "method": request.method
                },
                metadata={
                    "service_version": "1.0.0",
                    "timestamp": "2025-08-22T10:30:00Z"
                }
            ).dict()
        )
    
    return app


def get_retriever_service() -> RetrieverService:
    """Dependency to get the retriever service instance."""
    if retriever_service is None:
        raise HTTPException(status_code=503, detail="Service not initialized")
    return retriever_service


# Create app instance
app = create_app()


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    try:
        if retriever_service is None:
            raise HTTPException(status_code=503, detail="Service not initialized")
        
        # Perform basic health checks
        is_healthy = await retriever_service.health_check()
        status_info = await retriever_service.get_retriever_status()
        
        return HealthResponse(
            status="healthy" if is_healthy else "unhealthy",
            service="retriever",
            version="1.0.0",
            details={
                "retriever_initialized": retriever_service is not None,
                "components_loaded": is_healthy,
                "documents_indexed": status_info.get("documents", {}).get("indexed_count", 0),
                "epic2_retriever": status_info.get("retriever_type", "Unknown"),
                "vector_index_type": status_info.get("configuration", {}).get("vector_index_type", "Unknown"),
                "sparse_type": status_info.get("configuration", {}).get("sparse_type", "Unknown")
            },
            checks=[
                {
                    "name": "retriever_initialization",
                    "status": "healthy" if retriever_service is not None else "unhealthy",
                    "details": "Retriever service instance"
                },
                {
                    "name": "epic2_components",
                    "status": "healthy" if is_healthy else "unhealthy",
                    "details": "Epic 2 ModularUnifiedRetriever components"
                },
                {
                    "name": "document_index",
                    "status": "healthy" if status_info.get("documents", {}).get("indexed_count", 0) >= 0 else "unhealthy",
                    "documents": status_info.get("documents", {}).get("indexed_count", 0)
                }
            ]
        )
    except Exception as e:
        logger.error("Health check failed", error=str(e))
        return HealthResponse(
            status="unhealthy",
            service="retriever",
            version="1.0.0",
            details={"error": str(e)},
            checks=[
                {
                    "name": "health_check_error",
                    "status": "unhealthy",
                    "error": str(e)
                }
            ]
        )


@app.get("/health/live")
async def liveness_probe():
    """Kubernetes liveness probe."""
    return {"status": "alive"}


@app.get("/health/ready")
async def readiness_probe():
    """Kubernetes readiness probe."""
    if retriever_service is None:
        raise HTTPException(status_code=503, detail="Service not ready")
    
    is_ready = await retriever_service.health_check()
    if not is_ready:
        raise HTTPException(status_code=503, detail="Service not ready")
    
    return {"status": "ready"}


@app.get("/")
async def root():
    """Root endpoint with service information."""
    return {
        "service": "retriever-service",
        "version": "1.0.0",
        "description": "Document retrieval microservice powered by Epic 2's ModularUnifiedRetriever",
        "docs": "/docs",
        "health": "/health",
        "metrics": "/metrics",
        "api": "/api/v1"
    }


if __name__ == "__main__":
    settings = get_settings()
    uvicorn.run(
        "retriever_app.main:app",
        host=settings.service.host,
        port=settings.service.port,
        reload=settings.service.debug,
        log_level="info"
    )