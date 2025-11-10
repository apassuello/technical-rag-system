#!/bin/bash
# RAG Portfolio Test Runner Shell Script
# Convenient wrapper for the Python test runner with common use cases.

# Navigate to project directory
cd "$(dirname "$0")"

# Activate conda environment if available
if command -v conda &> /dev/null; then
    if conda info --envs | grep -q "rag-portfolio"; then
        echo "🔄 Activating rag-portfolio environment..."
        source $(conda info --base)/etc/profile.d/conda.sh
        conda activate rag-portfolio
    fi
fi

# Check if Python test runner exists
if [[ ! -f "test_runner.py" ]]; then
    echo "❌ test_runner.py not found. Run from project root directory."
    exit 1
fi

# Display banner
echo "🧪 RAG Portfolio Test Runner"
echo "============================="

# Handle special cases for convenience
case "${1:-help}" in
    "help"|"-h"|"--help")
        echo ""
        echo "Common usage patterns:"
        echo ""
        echo "  ./run_tests.sh epic1 all           # Run all Epic 1 tests"
        echo "  ./run_tests.sh epic1 unit          # Run Epic 1 unit tests"
        echo "  ./run_tests.sh epic1 integration   # Run Epic 1 integration tests"
        echo "  ./run_tests.sh epic1 phase2        # Run Epic 1 Phase 2 tests"
        echo "  ./run_tests.sh smoke               # Run smoke tests"
        echo "  ./run_tests.sh list                # List available test suites"
        echo ""
        echo "Coverage commands:"
        echo "  ./run_tests.sh coverage unit       # Unit test coverage"
        echo "  ./run_tests.sh coverage integration # Integration test coverage"
        echo "  ./run_tests.sh coverage comprehensive # Full coverage analysis"
        echo "  ./run_tests.sh coverage epic1      # Epic 1 specific coverage"
        echo ""
        echo "For all options:"
        python test_runner.py --help
        exit 0
        ;;
    "quick"|"q")
        echo "🚀 Running quick smoke tests..."
        python test_runner.py smoke
        exit $?
        ;;
    "epic1-quick")
        echo "🚀 Running Epic 1 smoke tests..."
        python test_runner.py epic1 unit
        exit $?
        ;;
    "epic1-full"|"epic1")
        echo "🚀 Running full Epic 1 test suite..."
        python test_runner.py epic1 all
        exit $?
        ;;
    "coverage")
        # Handle coverage commands
        case "${2:-help}" in
            "unit")
                echo "📊 Running unit test coverage analysis..."
                ./scripts/coverage_unit_tests.sh
                exit $?
                ;;
            "integration")
                echo "📊 Running integration test coverage analysis..."
                ./scripts/coverage_integration_tests.sh
                exit $?
                ;;
            "comprehensive"|"full")
                echo "📊 Running comprehensive coverage analysis..."
                ./scripts/coverage_comprehensive.sh
                exit $?
                ;;
            "epic1")
                echo "📊 Running Epic 1 coverage analysis..."
                ./scripts/coverage_epic_specific.sh 1
                exit $?
                ;;
            "epic8")
                echo "📊 Running Epic 8 coverage analysis..."
                ./scripts/coverage_epic_specific.sh 8
                exit $?
                ;;
            *)
                echo "❌ Unknown coverage command: ${2:-help}"
                echo ""
                echo "Available coverage commands:"
                echo "  unit         - Unit test coverage"
                echo "  integration  - Integration test coverage"
                echo "  comprehensive - Full coverage analysis"
                echo "  epic1        - Epic 1 specific coverage"
                echo "  epic8        - Epic 8 specific coverage"
                exit 1
                ;;
        esac
        ;;
    *)
        # Pass all arguments to Python test runner
        python test_runner.py "$@"
        exit $?
        ;;
esac