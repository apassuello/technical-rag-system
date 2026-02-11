#!/bin/bash
# Epic 8 Service Startup Script
# Starts all Epic 8 microservices in background processes

set -e

PROJECT_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
PYTHONPATH_SETTING="PYTHONPATH=${PROJECT_ROOT}"

echo "🚀 Starting Epic 8 Services..."
echo "Project Root: ${PROJECT_ROOT}"
echo "================================"

# Function to start a service
start_service() {
    local service_name=$1
    local port=$2
    local service_dir="${PROJECT_ROOT}/services/${service_name}"
    
    echo "Starting ${service_name} on port ${port}..."
    
    cd "${service_dir}"
    ${PYTHONPATH_SETTING} python -m uvicorn app.main:app --host 0.0.0.0 --port ${port} --reload &
    local pid=$!
    echo "  -> ${service_name} started (PID: ${pid})"
    
    # Store PID for later reference
    echo $pid > "/tmp/epic8_${service_name}.pid"
}

# Start all services
start_service "query-analyzer" 8082
start_service "generator" 8081
start_service "retriever" 8083
start_service "cache" 8084
start_service "analytics" 8085
start_service "api-gateway" 8080

echo ""
echo "✅ All services started!"
echo ""
echo "Service URLs:"
echo "  - Query Analyzer: http://localhost:8082"
echo "  - Generator:      http://localhost:8081" 
echo "  - Retriever:      http://localhost:8083"
echo "  - Cache:          http://localhost:8084"
echo "  - Analytics:      http://localhost:8085"
echo "  - API Gateway:    http://localhost:8080"
echo ""
echo "🔍 Run validation: python epic8_comprehensive_validator.py"
echo "🛑 Stop services:  ./stop_epic8_services.sh"
echo ""
echo "Services are starting... wait 10 seconds before validation."
