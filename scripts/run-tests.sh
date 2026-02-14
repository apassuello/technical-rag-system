#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
cd "$PROJECT_ROOT"

# ---------------------------------------------------------------------------
# Flags
# ---------------------------------------------------------------------------
RUN_UNIT=false
RUN_INTEGRATION=false
RUN_VALIDATION=false
NO_COV=false
FAIL_FAST=false

usage() {
    cat <<EOF
Usage: $0 [FLAGS]

Flags:
  --unit            Run unit tests only (tests/unit/)
  --integration     Run integration tests (tests/integration/)
  --validation      Run validation tests (tests/validation/)
  --full            Run all 3 tiers
  --no-cov          Disable coverage collection
  --fail-fast        Stop on first failure (-x)

Examples:
  $0 --unit                     # Fast unit tests (<30s)
  $0 --unit --no-cov            # Unit tests without coverage
  $0 --unit --integration       # Unit + integration
  $0 --full                     # All tiers with coverage
  $0 --full --no-cov            # All tiers without coverage
EOF
    exit 1
}

if [ $# -eq 0 ]; then
    usage
fi

while [ $# -gt 0 ]; do
    case "$1" in
        --unit)         RUN_UNIT=true ;;
        --integration)  RUN_INTEGRATION=true ;;
        --validation)   RUN_VALIDATION=true ;;
        --full)         RUN_UNIT=true; RUN_INTEGRATION=true; RUN_VALIDATION=true ;;
        --no-cov)       NO_COV=true ;;
        --fail-fast)    FAIL_FAST=true ;;
        -h|--help)      usage ;;
        *)              echo "Unknown flag: $1"; usage ;;
    esac
    shift
done

# ---------------------------------------------------------------------------
# Service management (only for integration / validation)
# ---------------------------------------------------------------------------
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
    local models
    models=$(curl -sf http://localhost:11434/api/tags | grep -o '"name":"[^"]*"' | cut -d'"' -f4 || echo "")

    if ! echo "$models" | grep -q "llama3.2:3b"; then
        echo "  Pulling llama3.2:3b..."
        docker compose exec ollama ollama pull llama3.2:3b
    else
        echo "  llama3.2:3b already available"
    fi

    if ! echo "$models" | grep -q "tinyllama"; then
        echo "  Pulling tinyllama..."
        docker compose exec ollama ollama pull tinyllama
    else
        echo "  tinyllama already available"
    fi
}

cleanup() {
    if [ "$WEAVIATE_STARTED" = true ] || [ "$OLLAMA_STARTED" = true ]; then
        echo "Stopping services..."
        docker compose down
    fi
}
trap cleanup EXIT

# ---------------------------------------------------------------------------
# Build test paths
# ---------------------------------------------------------------------------
TESTPATHS=()
[ "$RUN_UNIT" = true ]        && TESTPATHS+=(tests/unit)
[ "$RUN_INTEGRATION" = true ] && TESTPATHS+=(tests/integration)
[ "$RUN_VALIDATION" = true ]  && TESTPATHS+=(tests/validation)

if [ ${#TESTPATHS[@]} -eq 0 ]; then
    echo "ERROR: No tier selected. Use --unit, --integration, --validation, or --full."
    exit 1
fi

# Start services only when integration or validation is selected
if [ "$RUN_INTEGRATION" = true ] || [ "$RUN_VALIDATION" = true ]; then
    if curl -sf http://localhost:11434/api/tags > /dev/null 2>&1; then
        echo "Ollama already running"
    else
        start_ollama
    fi
    pull_ollama_models

    if curl -sf http://localhost:8180/v1/.well-known/ready > /dev/null 2>&1; then
        echo "Weaviate already running"
    else
        start_weaviate
    fi
fi

# ---------------------------------------------------------------------------
# Build pytest args
# ---------------------------------------------------------------------------
PYTEST_ARGS=(
    "${TESTPATHS[@]}"
    --override-ini="addopts=--strict-markers --strict-config --tb=short"
    -q
)

if [ "$NO_COV" = false ]; then
    PYTEST_ARGS+=(--cov=src --cov-report=term-missing --cov-fail-under=70)
fi

if [ "$FAIL_FAST" = true ]; then
    PYTEST_ARGS+=(-x)
fi

# ---------------------------------------------------------------------------
# Show collection summary per tier
# ---------------------------------------------------------------------------
echo ""
echo "=== Test collection ==="
for tier in "${TESTPATHS[@]}"; do
    count=$(pytest "$tier" --collect-only -q 2>/dev/null | tail -1 | grep -o '[0-9]\+' | head -1)
    echo "  $(basename "$tier"): ${count:-0} tests"
done
total=$(pytest "${TESTPATHS[@]}" --collect-only -q 2>/dev/null | tail -1 | grep -o '[0-9]\+' | head -1)
echo "  total: ${total:-0} tests"
echo ""

# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------
echo "=== Running: ${TESTPATHS[*]} ==="
pytest "${PYTEST_ARGS[@]}"
