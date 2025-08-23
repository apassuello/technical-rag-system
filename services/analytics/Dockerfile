# Analytics Service - Epic 8 Cloud-Native
# Build from project root: docker build -f services/analytics/Dockerfile . --build-arg SERVICE_NAME=analytics

# Stage 1: Dependencies and build environment
FROM python:3.11-slim AS builder

# Set build arguments
ARG BUILDPLATFORM
ARG TARGETPLATFORM

# Install system dependencies for building
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy requirements from service directory (using project root context)
COPY services/analytics/requirements.txt /tmp/requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /tmp/requirements.txt

# Stage 2: Runtime environment
FROM python:3.11-slim

# Set metadata labels
LABEL maintainer="RAG Portfolio Project"
LABEL service="analytics"
LABEL version="1.0.0"
LABEL description="Analytics microservice for Epic 8 RAG platform"

# Create non-root user for security
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONPATH="/app"
ENV PROJECT_ROOT="/app"
ENV ANALYTICS_LOG_LEVEL=INFO
ENV ANALYTICS_ENABLE_COST_TRACKING=true
ENV ANALYTICS_ENABLE_PERFORMANCE_TRACKING=true
ENV ANALYTICS_CIRCUIT_BREAKER_ENABLED=true

# Copy virtual environment from builder stage
COPY --from=builder /opt/venv /opt/venv

# Create app directory and set permissions
WORKDIR /app
RUN mkdir -p /app/logs /app/cache /app/data && \
    chown -R appuser:appuser /app

# Copy Epic 1 components (available due to project root build context)
COPY --chown=appuser:appuser src/ ./src/
COPY --chown=appuser:appuser config/ ./config/

# Copy service-specific application code
COPY --chown=appuser:appuser services/analytics/analytics_app/ ./app/

# Copy service configuration
COPY --chown=appuser:appuser services/analytics/config.yaml ./config.yaml

# Install curl for health checks
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Expose port (8085 for Analytics)
EXPOSE 8085

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8085/health/live || exit 1

# Switch to non-root user
USER appuser

# Default command
CMD ["python", "-m", "uvicorn", "analytics_app.main:app", "--host", "0.0.0.0", "--port", "8085", "--workers", "1"]