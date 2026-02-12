#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

MODE="${1:---full}"
WEAVIATE_STARTED=false

start_weaviate() {
    echo "Starting Weaviate via Docker..."
    docker compose up -d weaviate
    WEAVIATE_STARTED=true
    for i in $(seq 1 30); do
        if curl -sf http://localhost:8180/v1/.well-known/ready > /dev/null 2>&1; then
            echo "  Weaviate ready"
            return
        fi
        [ "$i" -eq 30 ] && echo "  WARNING: Weaviate not ready after 30s"
        sleep 1
    done
}

cleanup() {
    if [ "$WEAVIATE_STARTED" = true ]; then
        echo "Stopping Weaviate..."
        docker compose down
    fi
}
trap cleanup EXIT

case "$MODE" in
    --quick)
        echo "=== Quick: unit + component, no ML, no coverage ==="
        pytest tests/unit tests/component tests/api \
            -m "not requires_ml and not requires_ollama" \
            --override-ini="addopts=--strict-config --tb=short" -x -q
        ;;
    --local)
        echo "=== Local: everything without external services, with coverage ==="
        pytest tests/ \
            -m "not requires_ollama and not requires_weaviate" \
            --cov=src --cov-report=term-missing --cov-report=html --tb=short -q
        ;;
    --full)
        start_weaviate
        echo "=== Full: all tests, with coverage ==="
        echo "Expects: Ollama running (ollama serve)"
        pytest tests/ \
            --cov=src --cov-report=term-missing --cov-report=html --tb=short -q
        ;;
    *)
        echo "Usage: $0 [--quick|--local|--full]"
        echo ""
        echo "  --quick   Unit + component, no ML deps, no coverage (fast feedback)"
        echo "  --local   All tests except Ollama/Weaviate, with coverage"
        echo "  --full    All tests with coverage (needs Ollama, starts Weaviate via Docker)"
        exit 1
        ;;
esac
