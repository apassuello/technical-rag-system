#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

MODE="${1:---full}"
DOCKER_STARTED=false

cleanup() {
    if [ "$DOCKER_STARTED" = true ]; then
        echo "Tearing down Docker services..."
        docker compose down
    fi
}
trap cleanup EXIT

start_docker() {
    echo "Starting Docker services (Weaviate, Redis)..."
    docker compose up -d
    echo "Waiting for services to be healthy..."
    for i in $(seq 1 30); do
        if curl -sf http://localhost:8180/v1/.well-known/ready > /dev/null 2>&1; then
            echo "  Weaviate ready"
            break
        fi
        [ "$i" -eq 30 ] && echo "  WARNING: Weaviate not ready after 30s"
        sleep 1
    done
    for i in $(seq 1 10); do
        if redis-cli -p 6379 ping > /dev/null 2>&1; then
            echo "  Redis ready"
            break
        fi
        [ "$i" -eq 10 ] && echo "  WARNING: Redis not ready after 10s"
        sleep 1
    done
    DOCKER_STARTED=true
}

check_ollama() {
    if curl -sf http://localhost:11434/api/tags > /dev/null 2>&1; then
        echo "Ollama is running"
        return 0
    else
        echo "WARNING: Ollama not running. Tests requiring Ollama will be skipped."
        echo "  Start with: ollama serve"
        return 1
    fi
}

case "$MODE" in
    --ci)
        echo "=== CI Mode: no external services ==="
        pytest tests/ \
            -m "not requires_ollama and not requires_weaviate and not requires_redis and not integration" \
            --cov=src --cov-report=term-missing --tb=short -q
        ;;
    --quick)
        echo "=== Quick Mode: unit + component only ==="
        pytest tests/unit tests/component tests/api \
            -m "not requires_ml and not requires_ollama" \
            --override-ini="addopts=--strict-config --tb=short" -x -q
        ;;
    --coverage)
        start_docker
        check_ollama || true
        echo "=== Full Suite with Coverage ==="
        pytest tests/ --cov=src --cov-report=term-missing --cov-report=html --tb=short -q
        ;;
    --full|*)
        start_docker
        check_ollama || true
        echo "=== Full Suite ==="
        pytest tests/ --tb=short -q
        ;;
esac
