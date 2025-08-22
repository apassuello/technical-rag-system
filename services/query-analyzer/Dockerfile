# Query Analyzer Service - Epic 8 Cloud-Native
# Build from project root: docker build -f services/query-analyzer/Dockerfile . --build-arg SERVICE_NAME=query-analyzer

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
COPY services/query-analyzer/requirements.txt /tmp/requirements.txt

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r /tmp/requirements.txt

# Download spaCy model (needed for Epic1QueryAnalyzer)
RUN python -m spacy download en_core_web_sm

# Stage 2: Runtime environment
FROM python:3.11-slim

# Set metadata labels
LABEL maintainer="RAG Portfolio Project"
LABEL service="query-analyzer"
LABEL version="1.0.0"
LABEL description="Query Analyzer microservice for Epic 8 RAG platform"

# Create non-root user for security
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PATH="/opt/venv/bin:$PATH"
ENV PYTHONPATH="/app"
ENV QUERY_ANALYZER_CONFIG_FILE="/app/config.yaml"

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
COPY --chown=appuser:appuser services/query-analyzer/app/ ./app/

# Copy service configuration
COPY --chown=appuser:appuser services/query-analyzer/config.yaml ./config.yaml

# Install curl for health checks
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

# Expose ports (8082 to avoid conflict with Weaviate on 8080)
EXPOSE 8082 50051

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8082/health/live || exit 1

# Switch to non-root user
USER appuser

# Default command
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8082", "--workers", "1"]