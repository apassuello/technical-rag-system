#!/bin/bash
# Coverage analysis for integration tests
# Focuses on component interaction coverage

echo "🧪 Running Integration Test Coverage Analysis"
echo "============================================="

# Navigate to project directory
cd "$(dirname "$0")/.."

# Activate conda environment if available
if command -v conda &> /dev/null; then
    if conda info --envs | grep -q "rag-portfolio"; then
        echo "🔄 Activating rag-portfolio environment..."
        source $(conda info --base)/etc/profile.d/conda.sh
        conda activate rag-portfolio
    fi
fi

# Create coverage directory
mkdir -p reports/coverage

# Run integration tests with coverage
echo "🔍 Running integration tests with coverage..."
echo "Includes: core integration, Epic 1 integration, Epic 8 integration"
python -m pytest \
    tests/integration/ \
    tests/epic1/integration/ \
    tests/epic8/integration/ \
    tests/component/test_modular_document_processor.py \
    --cov=src \
    --cov=services \
    --cov-append \
    --cov-report=html:reports/coverage/integration_html \
    --cov-report=json:reports/coverage/integration_coverage.json \
    --cov-report=xml:reports/coverage/integration_coverage.xml \
    --cov-report=term-missing \
    --cov-fail-under=40 \
    -v \
    --tb=short \
    --maxfail=20

# Check if tests passed
if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Integration tests completed successfully!"
    echo "📊 Coverage reports generated:"
    echo "  - HTML: reports/coverage/integration_html/index.html"
    echo "  - JSON: reports/coverage/integration_coverage.json"
    echo "  - XML: reports/coverage/integration_coverage.xml"
    echo ""
    echo "🌐 Open HTML report:"
    echo "  open reports/coverage/integration_html/index.html"
else
    echo ""
    echo "❌ Integration tests failed or coverage threshold not met"
    exit 1
fi