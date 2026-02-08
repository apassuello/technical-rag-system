#!/bin/bash
# Core system (src/) coverage analysis with unit tests

echo "🧪 Core System (src/) Coverage Analysis"
echo "====================================="

# Navigate to project directory
cd "$(dirname "$0")/.."

# Set proper Python path
export PYTHONPATH="$PWD"

# Activate conda environment if available
if command -v conda &> /dev/null; then
    if conda info --envs | grep -q "technical-rag-system"; then
        echo "🔄 Activating technical-rag-system environment..."
        source $(conda info --base)/etc/profile.d/conda.sh
        conda activate technical-rag-system
    fi
fi

# Create coverage directory
mkdir -p reports/coverage

# Clean previous coverage data
echo "🧹 Cleaning previous coverage data..."
coverage erase

# Run unit tests with src/ coverage measurement
echo "🔍 Running unit tests with src/ coverage..."
pytest --cov=src tests/unit/ \
    --cov-config=.coveragerc \
    --cov-report=html:reports/coverage/src_html \
    --cov-report=json:reports/coverage/src_coverage.json \
    --cov-report=xml:reports/coverage/src_coverage.xml \
    --cov-report=term-missing \
    --tb=no -q

echo ""
echo "✅ Core system coverage analysis complete!"
echo "📊 Coverage reports generated:"
echo "  - HTML: reports/coverage/src_html/index.html" 
echo "  - JSON: reports/coverage/src_coverage.json"
echo "  - XML: reports/coverage/src_coverage.xml"
echo ""
echo "🌐 Open HTML report:"
echo "  open reports/coverage/src_html/index.html"