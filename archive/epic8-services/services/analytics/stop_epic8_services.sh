#!/bin/bash
# Epic 8 Service Stop Script
# Stops all Epic 8 microservices

echo "🛑 Stopping Epic 8 Services..."
echo "================================"

# Function to stop a service
stop_service() {
    local service_name=$1
    local pid_file="/tmp/epic8_${service_name}.pid"
    
    if [ -f "${pid_file}" ]; then
        local pid=$(cat "${pid_file}")
        if ps -p $pid > /dev/null 2>&1; then
            echo "Stopping ${service_name} (PID: ${pid})..."
            kill $pid
            rm -f "${pid_file}"
        else
            echo "${service_name} not running (PID file stale)"
            rm -f "${pid_file}"
        fi
    else
        echo "${service_name} PID file not found"
    fi
}

# Kill any remaining uvicorn processes for Epic 8
echo "Stopping any uvicorn processes on Epic 8 ports..."
pkill -f "port 808[0-5]" 2>/dev/null || true

# Stop individual services
stop_service "query-analyzer"
stop_service "generator" 
stop_service "retriever"
stop_service "cache"
stop_service "analytics"
stop_service "api-gateway"

echo ""
echo "✅ All Epic 8 services stopped!"
