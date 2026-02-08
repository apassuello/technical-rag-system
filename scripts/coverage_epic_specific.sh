#!/bin/bash
# Epic-specific coverage analysis
# Analyzes coverage for specific Epic test suites

EPIC_NUMBER=${1:-8}

echo "🧪 Running Epic $EPIC_NUMBER Coverage Analysis"
echo "============================================="

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

case $EPIC_NUMBER in
    1)
        echo "🔍 Running Epic 1 tests with src/ coverage..."
        echo "Tests: Multi-model routing, cost tracking, ML infrastructure, query analysis"
        
        pytest tests/epic1/ tests/unit/test_epic* \
            --cov=src \
            --cov-config=.coveragerc \
            --cov-report=html:reports/coverage/epic1_html \
            --cov-report=json:reports/coverage/epic1_coverage.json \
            --cov-report=xml:reports/coverage/epic1_coverage.xml \
            --cov-report=term-missing \
            --tb=no -q
        ;;
    8)
        echo "🔍 Running Epic 8 tests with services/ coverage..."
        echo "Tests: Cloud-native microservices, API gateway, services"
        
        pytest tests/epic8/ \
            --cov=services \
            --cov-config=.coveragerc \
            --cov-report=html:reports/coverage/epic8_html \
            --cov-report=json:reports/coverage/epic8_coverage.json \
            --cov-report=xml:reports/coverage/epic8_coverage.xml \
            --cov-report=term-missing \
            --tb=no -q
        ;;
    *)
        echo "❌ Unknown Epic number: $EPIC_NUMBER"
        echo "Available Epics: 1, 8"
        echo ""
        echo "Usage:"
        echo "  $0 1    # Run Epic 1 coverage (src/)"
        echo "  $0 8    # Run Epic 8 coverage (services/)"
        exit 1
        ;;
esac

echo ""
echo "✅ Epic $EPIC_NUMBER coverage analysis completed!"
echo "📊 Coverage reports generated:"
echo "  - HTML: reports/coverage/epic${EPIC_NUMBER}_html/index.html"
echo "  - JSON: reports/coverage/epic${EPIC_NUMBER}_coverage.json"
echo "  - XML: reports/coverage/epic${EPIC_NUMBER}_coverage.xml"
echo ""
echo "🌐 Open HTML report:"
echo "  open reports/coverage/epic${EPIC_NUMBER}_html/index.html"