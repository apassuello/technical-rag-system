#!/usr/bin/env bash
set -euo pipefail

# setup.sh — one-command project setup
# Creates venv, installs deps, runs smoke tests.
# Safe to re-run (idempotent). No sudo, no system changes.

VENV_DIR=".venv"
MIN_PYTHON="3.11"

# --- Colors (disabled if not a terminal) ---
if [ -t 1 ]; then
  GREEN='\033[0;32m'; RED='\033[0;31m'; YELLOW='\033[1;33m'; NC='\033[0m'
else
  GREEN=''; RED=''; YELLOW=''; NC=''
fi

info()  { echo -e "${GREEN}[+]${NC} $*"; }
warn()  { echo -e "${YELLOW}[!]${NC} $*"; }
fail()  { echo -e "${RED}[x]${NC} $*"; exit 1; }

# --- Find Python ≥3.11 ---
find_python() {
  for cmd in python3.11 python3 python; do
    if command -v "$cmd" &>/dev/null; then
      local ver
      ver=$("$cmd" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
      if "$cmd" -c "import sys; exit(0 if sys.version_info >= (3,11) else 1)" 2>/dev/null; then
        PYTHON="$cmd"
        info "Found $PYTHON ($ver)"
        return 0
      fi
    fi
  done

  echo ""
  fail "Python >= $MIN_PYTHON required. Install with:
    macOS:  brew install python@3.11
    Ubuntu: sudo apt install python3.11 python3.11-venv
    Other:  https://www.python.org/downloads/"
}

# --- Create or reuse venv ---
setup_venv() {
  if [ -d "$VENV_DIR" ]; then
    info "Reusing existing $VENV_DIR"
  else
    info "Creating virtual environment in $VENV_DIR"
    "$PYTHON" -m venv "$VENV_DIR"
  fi

  # shellcheck disable=SC1091
  source "$VENV_DIR/bin/activate"
  info "Activated $VENV_DIR ($(python --version))"
}

# --- Install dependencies ---
install_deps() {
  info "Upgrading pip"
  pip install --upgrade pip -q

  info "Installing dependencies (this may take a few minutes)"
  if pip install -r requirements.txt -q; then
    info "Dependencies installed"
  else
    echo ""
    warn "pip install failed. If PyTorch is the issue, try CPU-only:"
    warn "  pip install torch --index-url https://download.pytorch.org/whl/cpu"
    warn "Then re-run: pip install -r requirements.txt"
    exit 1
  fi
}

# --- Verify core imports ---
verify_imports() {
  info "Verifying core imports"
  python -c "
from src.core.platform_orchestrator import PlatformOrchestrator
from src.core.component_factory import ComponentFactory
from src.core.interfaces import Document, RetrievalResult
print('  All core imports OK')
"
}

# --- Run smoke tests ---
run_smoke_tests() {
  info "Running smoke tests (failures here are informational)"
  set +e
  python -m pytest tests/unit \
    -m "not requires_ml and not requires_ollama and not requires_postgres and not requires_redis and not integration" \
    --override-ini="addopts=--strict-markers --strict-config --tb=short" \
    -x -q 2>&1
  local rc=$?
  set -e

  if [ $rc -eq 0 ]; then
    info "Smoke tests passed"
  else
    warn "Some tests failed (exit $rc) — this is expected if optional services are unavailable"
  fi
}

# --- Summary ---
print_summary() {
  echo ""
  echo "========================================="
  info "Setup complete"
  echo "========================================="
  echo ""
  echo "  Activate:   source $VENV_DIR/bin/activate"
  echo "  Tests:      pytest tests/unit -m 'not requires_ml and not requires_ollama' -x -q"
  echo "  App:        streamlit run app.py   # requires Ollama for real LLM answers"
  echo ""
}

# --- Main ---
find_python
setup_venv
install_deps
verify_imports
run_smoke_tests
print_summary
