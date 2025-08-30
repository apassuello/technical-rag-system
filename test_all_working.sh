#!/bin/bash
# Simple wrapper script for unified test execution
# Provides quick access to common test scenarios

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 RAG Portfolio - Quick Test Runner${NC}"
echo -e "${BLUE}======================================${NC}"

# Check if python script exists
if [ ! -f "run_unified_tests.py" ]; then
    echo -e "${RED}❌ Error: run_unified_tests.py not found${NC}"
    exit 1
fi

# Default command
DEFAULT_CMD="python run_unified_tests.py --level working"

# Parse command line arguments
case "${1:-default}" in
    "basic"|"b")
        echo -e "${YELLOW}📋 Running basic tests (priority 1 only)${NC}"
        python run_unified_tests.py --level basic || true
        ;;
    "working"|"w"|"default")
        echo -e "${YELLOW}📋 Running working tests (priority 1-2)${NC}"
        python run_unified_tests.py --level working || true
        ;;
    "comprehensive"|"c"|"all")
        echo -e "${YELLOW}📋 Running comprehensive tests (all priorities)${NC}"
        python run_unified_tests.py --level comprehensive || true
        ;;
    "epic8"|"e8")
        echo -e "${YELLOW}📋 Running Epic 8 tests only${NC}"
        python run_unified_tests.py --level working --epics epic8 || true
        ;;
    "epic1"|"e1")
        echo -e "${YELLOW}📋 Running Epic 1 tests only${NC}"
        python run_unified_tests.py --level working --epics epic1 || true
        ;;
    "coverage"|"cov")
        echo -e "${YELLOW}📋 Running working tests with coverage analysis${NC}"
        python run_unified_tests.py --level working --save-results test_results_with_coverage.json || true
        echo -e "${GREEN}✅ Opening reports...${NC}"
        # Find the most recent HTML test report
        LATEST_REPORT=$(ls -t test_report_*.html 2>/dev/null | head -1)
        if [ -n "$LATEST_REPORT" ]; then
            open "$LATEST_REPORT" 2>/dev/null || echo "Test report: $LATEST_REPORT"
        fi
        open reports/coverage/html/index.html 2>/dev/null || echo "Coverage report: reports/coverage/html/index.html"
        ;;
    "no-coverage"|"nc")
        echo -e "${YELLOW}📋 Running working tests without coverage${NC}"
        python run_unified_tests.py --level working --no-coverage || true
        ;;
    "quick"|"q")
        echo -e "${YELLOW}📋 Quick smoke test${NC}"
        python run_unified_tests.py --level basic --no-coverage || true
        ;;
    "report"|"r")
        echo -e "${YELLOW}📋 Running working tests with HTML report generation${NC}"
        python run_unified_tests.py --level working --save-results comprehensive_report.json || true
        # Find the most recent HTML test report and open it
        LATEST_REPORT=$(ls -t test_report_*.html 2>/dev/null | head -1)
        if [ -n "$LATEST_REPORT" ]; then
            echo -e "${GREEN}✅ Opening HTML test report: $LATEST_REPORT${NC}"
            open "$LATEST_REPORT" 2>/dev/null || echo "HTML Test report: $LATEST_REPORT"
        else
            echo -e "${RED}❌ No HTML report found${NC}"
        fi
        ;;
    "help"|"h"|"-h"|"--help")
        echo -e "${BLUE}Usage: $0 [OPTION]${NC}"
        echo ""
        echo -e "${GREEN}Test Levels:${NC}"
        echo "  basic, b          - Run basic tests only (fastest)"
        echo "  working, w        - Run working tests (default)"
        echo "  comprehensive, c  - Run all tests including problematic ones"
        echo "  all              - Same as comprehensive"
        echo ""
        echo -e "${GREEN}Epic Filters:${NC}"
        echo "  epic8, e8        - Run Epic 8 tests only"
        echo "  epic1, e1        - Run Epic 1 tests only"
        echo ""
        echo -e "${GREEN}Coverage Options:${NC}"
        echo "  coverage, cov    - Run with coverage + open report"
        echo "  no-coverage, nc  - Run without coverage (faster)"
        echo ""
        echo -e "${GREEN}Quick Options:${NC}"
        echo "  quick, q         - Quick smoke test (no coverage)"
        echo "  report, r        - Generate beautiful HTML test report"
        echo "  help, h          - Show this help"
        echo ""
        echo -e "${GREEN}Examples:${NC}"
        echo "  $0 basic         # Fast basic tests"
        echo "  $0 working       # Standard working tests"
        echo "  $0 epic8         # Epic 8 tests only"
        echo "  $0 report        # Beautiful HTML test report"
        echo "  $0 coverage      # Working tests + coverage report"
        echo "  $0 comprehensive # All tests (may have failures)"
        ;;
    *)
        echo -e "${RED}❌ Unknown option: $1${NC}"
        echo -e "${YELLOW}💡 Use '$0 help' for available options${NC}"
        exit 1
        ;;
esac

echo -e "${GREEN}✅ Test execution completed${NC}"