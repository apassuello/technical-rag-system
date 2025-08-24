#!/bin/bash
# Coverage analysis for unit tests
# Focuses on core component coverage in src/

echo "🧪 Running Unit Test Coverage Analysis"
echo "====================================="

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

# Run unit tests with coverage
echo "🔍 Running unit tests with coverage..."
python -m pytest tests/unit/ \
    --cov=src \
    --cov-report=html:reports/coverage/unit_html \
    --cov-report=json:reports/coverage/unit_coverage.json \
    --cov-report=xml:reports/coverage/unit_coverage.xml \
    --cov-report=term-missing \
    --cov-fail-under=60 \
    -v

# Check if tests passed
if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Unit tests completed successfully!"
    echo "📊 Coverage reports generated:"
    echo "  - HTML: reports/coverage/unit_html/index.html"
    echo "  - JSON: reports/coverage/unit_coverage.json"
    echo "  - XML: reports/coverage/unit_coverage.xml"
    echo ""
    echo "🌐 Open HTML report:"
    echo "  open reports/coverage/unit_html/index.html"
else
    echo ""
    echo "❌ Unit tests failed or coverage threshold not met"
    exit 1
fi