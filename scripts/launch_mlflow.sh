#!/bin/bash
#
# Launch MLflow UI
#
# This script starts the MLflow tracking UI for viewing experiments,
# comparing runs, and managing the model registry.
#
# Usage:
#   ./scripts/launch_mlflow.sh [port]
#
# Default port: 5000
# Access UI at: http://localhost:5000

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
PORT="${1:-5000}"
BACKEND_STORE="file:./mlruns"
DEFAULT_ARTIFACT_ROOT="./mlartifacts"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  MLflow UI Launcher${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check if MLflow is installed
if ! command -v mlflow &> /dev/null; then
    echo -e "${YELLOW}MLflow not found. Installing...${NC}"
    pip install mlflow>=2.9.0
fi

# Create mlruns directory if it doesn't exist
if [ ! -d "mlruns" ]; then
    echo -e "${YELLOW}Creating mlruns directory...${NC}"
    mkdir -p mlruns
fi

# Create mlartifacts directory if it doesn't exist
if [ ! -d "mlartifacts" ]; then
    echo -e "${YELLOW}Creating mlartifacts directory...${NC}"
    mkdir -p mlartifacts
fi

echo -e "${GREEN}Starting MLflow UI...${NC}"
echo -e "  ${BLUE}Backend Store:${NC} ${BACKEND_STORE}"
echo -e "  ${BLUE}Artifact Root:${NC} ${DEFAULT_ARTIFACT_ROOT}"
echo -e "  ${BLUE}Port:${NC} ${PORT}"
echo ""
echo -e "${GREEN}Access MLflow UI at:${NC} http://localhost:${PORT}"
echo -e "${YELLOW}Press Ctrl+C to stop${NC}"
echo ""

# Launch MLflow UI
mlflow ui \
    --backend-store-uri "${BACKEND_STORE}" \
    --default-artifact-root "${DEFAULT_ARTIFACT_ROOT}" \
    --port "${PORT}" \
    --host 0.0.0.0
