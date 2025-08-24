#!/bin/bash
# Epic-specific coverage analysis
# Analyzes coverage for specific Epic test suites

EPIC_NUMBER=${1:-1}

echo "🧪 Running Epic $EPIC_NUMBER Coverage Analysis"
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

case $EPIC_NUMBER in
    1)
        echo "🔍 Running Epic 1 tests with coverage..."
        echo "Tests: Multi-model routing, cost tracking, ML infrastructure, query analysis"
        echo "Includes: integration, smoke, phase2, demos, and related unit tests"
        
        python -m pytest \
            tests/epic1/integration/ \
            tests/epic1/smoke/ \
            tests/epic1/phase2/ \
            tests/epic1/demos/scripts/ \
            tests/epic1/ml_infrastructure/unit/ \
            tests/unit/test_technical_term_manager.py \
            tests/unit/test_syntactic_parser.py \
            tests/unit/test_feature_extractor.py \
            tests/unit/test_complexity_classifier.py \
            tests/unit/test_model_recommender.py \
            --cov=src \
            --cov-report=html:reports/coverage/epic1_html \
            --cov-report=json:reports/coverage/epic1_coverage.json \
            --cov-report=xml:reports/coverage/epic1_coverage.xml \
            --cov-report=term-missing \
            --cov-fail-under=40 \
            -v \
            --tb=short \
            --maxfail=30
        ;;
    8)
        echo "🔍 Running Epic 8 tests with coverage..."
        echo "Tests: Cloud-native microservices, API gateway, services"
        echo "Includes: unit, integration, api, performance tests"
        
        python -m pytest \
            tests/epic8/unit/ \
            tests/epic8/integration/ \
            tests/epic8/api/ \
            tests/epic8/performance/ \
            --cov=services \
            --cov=src \
            --cov-report=html:reports/coverage/epic8_html \
            --cov-report=json:reports/coverage/epic8_coverage.json \
            --cov-report=xml:reports/coverage/epic8_coverage.xml \
            --cov-report=term-missing \
            --cov-fail-under=40 \
            -v \
            --tb=short \
            --maxfail=30
        ;;
    *)
        echo "❌ Unknown Epic number: $EPIC_NUMBER"
        echo "Available Epics: 1, 8"
        echo ""
        echo "Usage:"
        echo "  $0 1    # Run Epic 1 coverage"
        echo "  $0 8    # Run Epic 8 coverage"
        exit 1
        ;;
esac

# Check results
if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Epic $EPIC_NUMBER coverage analysis completed successfully!"
    echo "📊 Coverage reports generated:"
    echo "  - HTML: reports/coverage/epic${EPIC_NUMBER}_html/index.html"
    echo "  - JSON: reports/coverage/epic${EPIC_NUMBER}_coverage.json"
    echo "  - XML: reports/coverage/epic${EPIC_NUMBER}_coverage.xml"
    echo ""
    echo "🌐 Open HTML report:"
    echo "  open reports/coverage/epic${EPIC_NUMBER}_html/index.html"
else
    echo ""
    echo "❌ Epic $EPIC_NUMBER coverage analysis failed"
    exit 1
fi