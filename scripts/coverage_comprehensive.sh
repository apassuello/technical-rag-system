#!/bin/bash
# Comprehensive coverage analysis across all core src/ components
# Combines unit, integration, and Epic-specific tests for complete coverage picture

echo "🧪 Running Comprehensive Coverage Analysis"
echo "=========================================="

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

# Clean previous coverage data
echo "🧹 Cleaning previous coverage data..."
rm -f .coverage*
rm -rf reports/coverage/comprehensive_html

echo ""
echo "📊 Running comprehensive test suite with coverage..."
echo "This includes:"
echo "  - Unit tests (tests/unit/)"
echo "  - Integration tests (tests/integration/)" 
echo "  - Component tests (tests/component/)"
echo "  - Epic 1 tests (integration, smoke, phase2, demos)"
echo "  - Epic 8 tests (unit, integration, api)"
echo "  - Working Epic 2 validation tests"
echo ""

# Run comprehensive test suite with coverage - including ALL working Epic tests
python -m pytest \
    tests/unit/ \
    tests/integration/ \
    tests/component/test_modular_document_processor.py \
    tests/component/test_pdf_parser.py \
    tests/component/test_embeddings.py \
    tests/epic1/integration/ \
    tests/epic1/smoke/ \
    tests/epic1/phase2/ \
    tests/epic1/demos/scripts/ \
    tests/epic8/unit/ \
    tests/epic8/integration/ \
    tests/epic8/api/ \
    --cov=src \
    --cov=services \
    --cov-report=html:reports/coverage/comprehensive_html \
    --cov-report=json:reports/coverage/comprehensive_coverage.json \
    --cov-report=xml:reports/coverage/comprehensive_coverage.xml \
    --cov-report=term-missing \
    --cov-fail-under=50 \
    -v \
    --tb=short \
    --maxfail=50

# Check results
if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Comprehensive coverage analysis completed successfully!"
    echo ""
    echo "📊 Coverage reports generated:"
    echo "  - HTML: reports/coverage/comprehensive_html/index.html"
    echo "  - JSON: reports/coverage/comprehensive_coverage.json"  
    echo "  - XML: reports/coverage/comprehensive_coverage.xml"
    echo ""
    
    # Extract coverage percentage from JSON if available
    if [ -f "reports/coverage/comprehensive_coverage.json" ]; then
        python -c "
import json
try:
    with open('reports/coverage/comprehensive_coverage.json') as f:
        data = json.load(f)
    total_percent = data.get('totals', {}).get('percent_covered', 0)
    print(f'🎯 Overall Coverage: {total_percent:.1f}%')
    
    if total_percent >= 75:
        print('🎉 Excellent coverage level!')
    elif total_percent >= 65:
        print('✅ Good coverage level')
    elif total_percent >= 50:
        print('⚠️  Fair coverage level - room for improvement')
    else:
        print('❌ Low coverage level - needs attention')
except:
    print('📊 Coverage data available in reports')
"
    fi
    
    echo ""
    echo "🌐 View detailed HTML report:"
    echo "  open reports/coverage/comprehensive_html/index.html"
    echo ""
    echo "📈 To compare with previous runs:"
    echo "  python test_runner.py coverage diff baseline_coverage.json reports/coverage/comprehensive_coverage.json"
    
else
    echo ""
    echo "❌ Comprehensive coverage analysis failed"
    echo "Check the output above for details"
    exit 1
fi