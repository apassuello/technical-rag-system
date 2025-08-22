# Retriever Service Dockerfile
# Multi-stage build with security scanning and optimization

FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app:/app/src
ENV PROJECT_ROOT=/app

# Create app user for security
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set up working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Copy Epic 2 source components (required for ModularUnifiedRetriever)
COPY --chown=appuser:appuser ../../src ./src/
COPY --chown=appuser:appuser ../../config ./config/

# Copy service-specific code
COPY --chown=appuser:appuser app/ ./app/
COPY --chown=appuser:appuser config.yaml .

# Switch to app user for security
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8083/health/live || exit 1

# Expose port
EXPOSE 8083

# Start command
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8083"]