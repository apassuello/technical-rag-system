"""
API Gateway Service - FastAPI Application.

This is the main orchestration service for Epic 8, coordinating all other microservices
to provide a unified RAG query processing pipeline.
"""

import asyncio
import logging
import time
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
from .core.gateway import APIGatewayService
from .schemas.responses import ErrorResponse

# Configure structured logging
logging.basicConfig(level=logging.INFO)
logger = structlog.get_logger(__name__)

# Prometheus metrics
REQUEST_COUNT = Counter('gateway_requests_total', 'Total number of gateway requests', ['method', 'status'])
REQUEST_DURATION = Histogram('gateway_request_duration_seconds', 'Gateway request duration', ['method'])
SERVICE_HEALTH = Gauge('gateway_service_health', 'Gateway service health (1=healthy, 0=unhealthy)')
CONNECTED_SERVICES = Gauge('gateway_connected_services', 'Number of healthy connected services')

# Global gateway service instance
gateway_service: Optional[APIGatewayService] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle - startup and shutdown."""
    global gateway_service
    
    logger.info("Starting API Gateway Service")
    
    try:
        # Initialize gateway service
        settings = get_settings()
        gateway_service = APIGatewayService(settings)
        
        # Initialize all service clients and circuit breakers
        await gateway_service.initialize()
        
        # Set health metrics
        SERVICE_HEALTH.set(1)
        
        logger.info(
            "API Gateway Service started successfully",
            service_endpoints={
                "query-analyzer": settings.get_service_endpoint("query-analyzer").url,
                "generator": settings.get_service_endpoint("generator").url,
                "retriever": settings.get_service_endpoint("retriever").url,
                "cache": settings.get_service_endpoint("cache").url,
                "analytics": settings.get_service_endpoint("analytics").url
            }
        )
        
        yield
        
    except Exception as e:
        logger.error("Failed to start API Gateway Service", error=str(e))
        SERVICE_HEALTH.set(0)
        raise
    
    finally:
        logger.info("Shutting down API Gateway Service")
        
        if gateway_service:
            try:
                await gateway_service.close()
            except Exception as e:
                logger.warning("Error during gateway shutdown", error=str(e))
        
        SERVICE_HEALTH.set(0)


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    
    settings = get_settings()
    
    app = FastAPI(
        title="API Gateway Service",
        description="Epic 8 - Cloud-Native RAG Platform API Gateway",
        version="1.0.0",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json"
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=settings.allowed_methods,
        allow_headers=settings.allowed_headers,
    )
    
    # Add custom middleware for request logging and metrics
    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        """Log requests and update metrics."""
        start_time = time.time()
        method = request.method
        path = request.url.path
        
        # Skip metrics for health checks and metrics endpoint
        skip_metrics = path in ["/health", "/health/live", "/health/ready", "/metrics"]
        
        if not skip_metrics:
            logger.info(
                "Request started",
                method=method,
                path=path,
                client_ip=request.client.host if request.client else "unknown"
            )
        
        try:
            response = await call_next(request)
            
            # Update metrics
            duration = time.time() - start_time
            
            if not skip_metrics:
                REQUEST_COUNT.labels(method=method, status=response.status_code).inc()
                REQUEST_DURATION.labels(method=method).observe(duration)
                
                logger.info(
                    "Request completed",
                    method=method,
                    path=path,
                    status_code=response.status_code,
                    duration=duration
                )
            
            return response
            
        except Exception as e:
            duration = time.time() - start_time
            
            if not skip_metrics:
                REQUEST_COUNT.labels(method=method, status=500).inc()
                REQUEST_DURATION.labels(method=method).observe(duration)
                
                logger.error(
                    "Request failed",
                    method=method,
                    path=path,
                    error=str(e),
                    duration=duration
                )
            
            # Return standardized error response
            return JSONResponse(
                status_code=500,
                content=ErrorResponse(
                    error="InternalServerError",
                    message="An unexpected error occurred",
                    details={"error": str(e)}
                ).model_dump()
            )
    
    # Include API routers
    app.include_router(rest.router, prefix="/api/v1", tags=["Gateway API"])
    
    # Add Prometheus metrics endpoint
    metrics_app = make_asgi_app()
    app.mount("/metrics", metrics_app)
    
    # Global exception handler
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        """Handle uncaught exceptions."""
        logger.error(
            "Uncaught exception",
            path=request.url.path,
            method=request.method,
            error=str(exc),
            error_type=type(exc).__name__
        )
        
        return JSONResponse(
            status_code=500,
            content=ErrorResponse(
                error="InternalServerError",
                message="An unexpected error occurred",
                details={
                    "error": str(exc),
                    "error_type": type(exc).__name__
                },
                suggestions=[
                    "Check service status at /api/v1/status",
                    "Contact support if problem persists"
                ]
            ).model_dump()
        )
    
    return app


def get_gateway_service() -> APIGatewayService:
    """Dependency to get the gateway service instance."""
    if gateway_service is None:
        raise HTTPException(status_code=503, detail="Gateway service not initialized")
    return gateway_service


# Create app instance
app = create_app()


# Health check endpoints at root level
@app.get("/health")
async def root_health_check():
    """Root health check endpoint."""
    return {
        "status": "healthy",
        "service": "api-gateway",
        "version": "1.0.0",
        "timestamp": time.time()
    }


@app.get("/")
async def root():
    """Root endpoint with service information."""
    return {
        "service": "API Gateway",
        "version": "1.0.0",
        "description": "Epic 8 - Cloud-Native RAG Platform API Gateway",
        "endpoints": {
            "docs": "/docs",
            "redoc": "/redoc",
            "health": "/health",
            "status": "/api/v1/status",
            "query": "/api/v1/query",
            "batch_query": "/api/v1/batch-query",
            "models": "/api/v1/models"
        },
        "epic8_compliance": {
            "architecture": "Cloud-Native Microservices",
            "orchestration": "Complete RAG Pipeline",
            "services_connected": 5,
            "features": [
                "Unified Query Processing",
                "Intelligent Model Routing",
                "Cost Optimization",
                "Circuit Breaker Resilience",
                "Comprehensive Analytics"
            ]
        }
    }


if __name__ == "__main__":
    uvicorn.run(
        "gateway_app.main:app",
        host="0.0.0.0",
        port=8080,
        reload=True,
        log_level="info"
    )