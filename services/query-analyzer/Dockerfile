# Multi-stage Docker build for Query Analyzer Service
# Stage 1: Dependencies and build environment
FROM python:3.11-slim as builder

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

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

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
ENV QUERY_ANALYZER_CONFIG_FILE="/app/config.yaml"

# Copy virtual environment from builder stage
COPY --from=builder /opt/venv /opt/venv

# Create app directory and set permissions
WORKDIR /app
RUN mkdir -p /app/logs /app/cache && \
    chown -R appuser:appuser /app

# Copy application code
COPY --chown=appuser:appuser . .

# Copy the main project src directory (needed for Epic1QueryAnalyzer imports)
# Note: This is a temporary solution - in production we'd package components properly
COPY --chown=appuser:appuser ../../src /app/src

# Expose ports
EXPOSE 8080 50051

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8080/health/live || exit 1

# Switch to non-root user
USER appuser

# Default command
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "1"]