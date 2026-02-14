#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

MODE="${1:---full}"
WEAVIATE_STARTED=false
OLLAMA_STARTED=false

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

start_ollama() {
    echo "Starting Ollama via Docker..."
    docker compose up -d ollama
    OLLAMA_STARTED=true
    for i in $(seq 1 30); do
        if curl -sf http://localhost:11434/api/tags > /dev/null 2>&1; then
            echo "  Ollama ready"
            return
        fi
        [ "$i" -eq 30 ] && echo "  WARNING: Ollama not ready after 30s"
        sleep 1
    done
}

pull_ollama_models() {
    echo "Ensuring Ollama models are available..."

    # Get list of currently pulled models
    local models
    models=$(curl -sf http://localhost:11434/api/tags | grep -o '"name":"[^"]*"' | cut -d'"' -f4 || echo "")

    # Pull llama3.2:3b if not present
    if ! echo "$models" | grep -q "llama3.2:3b"; then
        echo "  Pulling llama3.2:3b..."
        docker exec rag-portfolio-extract-ollama-1 ollama pull llama3.2:3b
    else
        echo "  ✓ llama3.2:3b already available"
    fi

    # Pull tinyllama if not present
    if ! echo "$models" | grep -q "tinyllama"; then
        echo "  Pulling tinyllama..."
        docker exec rag-portfolio-extract-ollama-1 ollama pull tinyllama
    else
        echo "  ✓ tinyllama already available"
    fi
}

cleanup() {
    if [ "$WEAVIATE_STARTED" = true ] || [ "$OLLAMA_STARTED" = true ]; then
        echo "Stopping services..."
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
        start_ollama
        pull_ollama_models

        echo "=== Full: all tests, with coverage ==="
        echo "Using config: test-ollama.yaml (Ollama-only)"
        pytest tests/ \
            --cov=src --cov-report=term-missing --cov-report=html --tb=short -q
        ;;
    *)
        echo "Usage: $0 [--quick|--local|--full]"
        echo ""
        echo "  --quick   Unit + component, no ML deps, no coverage (fast feedback)"
        echo "  --local   All tests except Ollama/Weaviate, with coverage"
        echo "  --full    All tests with coverage (starts Ollama + Weaviate via Docker)"
        exit 1
        ;;
esac
