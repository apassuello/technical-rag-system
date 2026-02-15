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
LLAMA_PID=""

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

start_llama_server() {
    echo "Starting llama-server (native)..."

    # Check llama-server is on PATH
    if ! which llama-server > /dev/null 2>&1; then
        echo "ERROR: llama-server not found on PATH. Install llama.cpp first."
        exit 1
    fi

    # Resolve model path from env or default
    LLAMA_MODEL="${LLAMA_MODEL:-$HOME/.cache/llama-models/qwen2.5-1.5b-instruct-q4_k_m.gguf}"
    if [ ! -f "$LLAMA_MODEL" ]; then
        echo "ERROR: GGUF model not found at $LLAMA_MODEL"
        echo "  Set LLAMA_MODEL env var to the correct path."
        exit 1
    fi

    # Log file — timestamped, kept in /tmp so it survives the run
    LLAMA_LOG="/tmp/llama-server-$(date +%Y%m%d-%H%M%S).log"

    # Start llama-server in background, redirect all output to log file
    llama-server \
        --model "$LLAMA_MODEL" \
        --port 11434 \
        --n-gpu-layers -1 \
        --ctx-size 4096 \
        > "$LLAMA_LOG" 2>&1 &
    LLAMA_PID=$!

    # Poll /health until ready (up to 60s, 2s intervals)
    for i in $(seq 1 30); do
        if curl -sf http://localhost:11434/health > /dev/null 2>&1; then
            echo "  llama-server ready (model: $(basename "$LLAMA_MODEL"))"
            echo "  log: $LLAMA_LOG"
            return
        fi
        if ! kill -0 "$LLAMA_PID" 2>/dev/null; then
            echo "ERROR: llama-server exited early. Check log: $LLAMA_LOG"
            tail -20 "$LLAMA_LOG"
            exit 1
        fi
        [ "$i" -eq 30 ] && echo "  WARNING: llama-server not ready after 60s (log: $LLAMA_LOG)"
        sleep 2
    done
}

cleanup() {
    if [ -n "$LLAMA_PID" ]; then
        echo "Stopping llama-server (PID $LLAMA_PID)..."
        kill $LLAMA_PID 2>/dev/null
        wait $LLAMA_PID 2>/dev/null
        echo "  log preserved: ${LLAMA_LOG:-/tmp/llama-server-*.log}"
    fi
    if [ "$WEAVIATE_STARTED" = true ]; then
        echo "Stopping Weaviate..."
        docker compose stop weaviate 2>/dev/null && docker compose rm -f weaviate 2>/dev/null
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
    if curl -sf http://localhost:11434/health > /dev/null 2>&1; then
        echo "llama-server already running"
    else
        start_llama_server
    fi

    if curl -sf http://localhost:8180/v1/.well-known/ready > /dev/null 2>&1; then
        echo "Weaviate already running"
    else
        start_weaviate
    fi
fi

# ---------------------------------------------------------------------------
# Build pytest args
# ---------------------------------------------------------------------------
COV_THRESHOLD=70

# Exclude markers for services with known issues (weaviate v3→v4, spacy model)
MARKER_EXCLUDE="not requires_weaviate and not requires_spacy"

PYTEST_ARGS=(
    "${TESTPATHS[@]}"
    --override-ini="addopts=--strict-markers --strict-config --tb=short"
    -m "$MARKER_EXCLUDE"
    -rfEsx
)

if [ "$NO_COV" = false ]; then
    PYTEST_ARGS+=(
        --cov=src
        --cov-report=html:htmlcov
    )
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
    count=$(pytest "$tier" --collect-only -q 2>/dev/null | tail -1 | grep -o '[0-9]\+' | head -1 || echo "0")
    echo "  $(basename "$tier"): ${count:-0} tests"
done
total=$(pytest "${TESTPATHS[@]}" --collect-only -q 2>/dev/null | tail -1 | grep -o '[0-9]\+' | head -1 || echo "0")
echo "  total: ${total:-0} tests"
echo ""

# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------
echo "=== Running: ${TESTPATHS[*]} ==="
set +e
pytest "${PYTEST_ARGS[@]}" 2>&1 | tee /tmp/pytest-output.log
PYTEST_EXIT=${PIPESTATUS[0]}
set -e

# ---------------------------------------------------------------------------
# Coverage summary (compact: file, stmts, miss, cover%)
# ---------------------------------------------------------------------------
if [ "$NO_COV" = false ] && [ -f .coverage ]; then
    echo ""
    echo "=== Coverage (files < 100%) ==="
    coverage report --skip-covered --include="src/*" 2>/dev/null \
        | awk '
            /^Name /    { printf "  %-70s %5s %5s %6s\n", "File", "Stmts", "Miss", "Cover"; next }
            /^-/        { next }
            /^TOTAL/    { printf "  %-70s %5s %5s %6s\n", "TOTAL", $2, $3, $NF; next }
            NF >= 4     { printf "  %-70s %5s %5s %6s\n", $1, $2, $3, $NF }
        '
    echo ""

    # Extract total percentage and compare to threshold
    COV_TOTAL=$(coverage report --include="src/*" 2>/dev/null | awk '/^TOTAL/ { print $NF }' | tr -d '%')
    if [ -n "$COV_TOTAL" ]; then
        if [ "$(echo "$COV_TOTAL < $COV_THRESHOLD" | bc -l 2>/dev/null || echo 0)" = "1" ]; then
            echo "WARNING: Coverage ${COV_TOTAL}% is below threshold ${COV_THRESHOLD}%"
        else
            echo "Coverage: ${COV_TOTAL}% (threshold: ${COV_THRESHOLD}%)"
        fi
    fi
    echo "HTML report: htmlcov/index.html"
fi

exit $PYTEST_EXIT
