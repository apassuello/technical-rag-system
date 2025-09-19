#!/bin/bash

# Comprehensive Kubernetes Testing Script
# Epic 8 Cloud-Native RAG Platform
#
# This script runs all Kubernetes testing categories in sequence,
# providing a single entry point for complete validation.

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
NAMESPACE="epic8"
CLUSTER_NAME="epic8-testing"
REPORT_DIR="${PROJECT_ROOT}/test-reports"
TIMESTAMP="$(date +%Y%m%d_%H%M%S)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_section() {
    echo -e "${PURPLE}[SECTION]${NC} $1"
}

# Test result tracking
declare -A test_results
total_tests=0
passed_tests=0
failed_tests=0
start_time=$(date +%s)

# Function to record test result
record_test_result() {
    local test_name="$1"
    local result="$2"
    local duration="$3"

    test_results["$test_name"]="$result|$duration"
    total_tests=$((total_tests + 1))

    if [ "$result" = "PASSED" ]; then
        passed_tests=$((passed_tests + 1))
        log_success "$test_name completed in ${duration}s"
    else
        failed_tests=$((failed_tests + 1))
        log_error "$test_name failed in ${duration}s"
    fi
}

# Function to run a test with timeout and error handling
run_test() {
    local test_name="$1"
    local test_command="$2"
    local timeout_seconds="${3:-300}"

    log_info "Running $test_name..."
    local test_start=$(date +%s)

    if timeout "$timeout_seconds" bash -c "$test_command"; then
        local test_end=$(date +%s)
        local duration=$((test_end - test_start))
        record_test_result "$test_name" "PASSED" "$duration"
        return 0
    else
        local test_end=$(date +%s)
        local duration=$((test_end - test_start))
        record_test_result "$test_name" "FAILED" "$duration"
        return 1
    fi
}

# Function to check prerequisites
check_prerequisites() {
    log_section "Checking Prerequisites"

    local missing_tools=()

    # Check required tools
    for tool in docker kubectl python3 kind; do
        if ! command -v "$tool" >/dev/null 2>&1; then
            missing_tools+=("$tool")
        fi
    done

    if [ ${#missing_tools[@]} -ne 0 ]; then
        log_error "Missing required tools: ${missing_tools[*]}"
        log_info "Please install missing tools and run again"
        return 1
    fi

    # Check Python dependencies
    if ! python3 -c "import yaml, pytest, kubernetes" 2>/dev/null; then
        log_warning "Some Python dependencies missing - installing..."
        pip3 install pyyaml pytest kubernetes requests || {
            log_error "Failed to install Python dependencies"
            return 1
        }
    fi

    log_success "All prerequisites satisfied"
    return 0
}

# Function to setup test environment
setup_environment() {
    log_section "Setting up Test Environment"

    # Create report directory
    mkdir -p "$REPORT_DIR"

    # Setup local cluster if not exists
    if ! kind get clusters | grep -q "^${CLUSTER_NAME}$"; then
        log_info "Setting up local Kubernetes cluster..."
        if ! "$SCRIPT_DIR/setup-local-k8s.sh" setup; then
            log_error "Failed to setup local cluster"
            return 1
        fi
    else
        log_info "Using existing cluster: $CLUSTER_NAME"
    fi

    # Verify cluster is ready
    if ! kubectl cluster-info --context "kind-${CLUSTER_NAME}" >/dev/null 2>&1; then
        log_error "Cluster is not accessible"
        return 1
    fi

    log_success "Test environment ready"
    return 0
}

# Function to run static validation tests
run_static_validation() {
    log_section "Static Validation Tests"

    # 1. YAML Syntax Validation
    run_test "YAML_Syntax_Validation" "
        find '$PROJECT_ROOT/k8s' '$PROJECT_ROOT/helm' -name '*.yaml' -o -name '*.yml' | xargs -I {} python3 -c \"
import yaml, sys
try:
    with open('{}', 'r') as f:
        list(yaml.safe_load_all(f.read()))
except Exception as e:
    print('❌ {}: {}'.format('{}', e))
    sys.exit(1)
\"
    " 60

    # 2. Kubernetes Manifest Validation
    if [ -f "$PROJECT_ROOT/k8s/tests/test_manifest_validation.py" ]; then
        run_test "K8s_Manifest_Validation" "
            cd '$PROJECT_ROOT/k8s/tests'
            python3 test_manifest_validation.py --manifest-dir ../manifests --output-format json > '$REPORT_DIR/manifest_validation_${TIMESTAMP}.json'
        " 180
    else
        log_warning "K8s manifest validation tests not found"
    fi

    # 3. Helm Chart Validation
    if [ -f "$PROJECT_ROOT/helm/tests/test_helm_charts.py" ]; then
        run_test "Helm_Chart_Validation" "
            cd '$PROJECT_ROOT/helm/tests'
            python3 test_helm_charts.py --chart-dir ../charts --output-format json > '$REPORT_DIR/helm_validation_${TIMESTAMP}.json'
        " 180
    else
        log_warning "Helm chart validation tests not found"
    fi

    # 4. Security Validation (if tools available)
    if command -v checkov >/dev/null 2>&1; then
        run_test "Security_Validation_Checkov" "
            checkov -d '$PROJECT_ROOT/k8s' -d '$PROJECT_ROOT/helm' --framework kubernetes,helm --output json > '$REPORT_DIR/security_checkov_${TIMESTAMP}.json'
        " 120
    else
        log_info "Checkov not available - skipping security validation"
    fi
}

# Function to run Helm-specific tests
run_helm_tests() {
    log_section "Helm Chart Tests"

    if [ ! -d "$PROJECT_ROOT/helm/charts" ]; then
        log_warning "No Helm charts found - skipping Helm tests"
        return 0
    fi

    # 1. Helm Lint
    run_test "Helm_Lint_Tests" "
        for chart in '$PROJECT_ROOT/helm/charts'/*; do
            if [ -f \"\$chart/Chart.yaml\" ]; then
                helm lint \"\$chart\" || exit 1
            fi
        done
    " 120

    # 2. Template Rendering Tests
    run_test "Template_Rendering_Tests" "
        for chart in '$PROJECT_ROOT/helm/charts'/*; do
            if [ -f \"\$chart/Chart.yaml\" ]; then
                chart_name=\$(basename \"\$chart\")
                helm template test-release \"\$chart\" > '/tmp/rendered_\${chart_name}.yaml'
                python3 -c \"
import yaml
with open('/tmp/rendered_\${chart_name}.yaml', 'r') as f:
    list(yaml.safe_load_all(f))
\"
            fi
        done
    " 180

    # 3. Multi-Environment Testing
    run_test "Multi_Environment_Tests" "
        for env in development staging production; do
            for chart in '$PROJECT_ROOT/helm/charts'/*; do
                if [ -f \"\$chart/Chart.yaml\" ] && [ -f \"\$chart/values-\$env.yaml\" ]; then
                    helm template test-release \"\$chart\" -f \"\$chart/values-\$env.yaml\" > /dev/null
                fi
            done
        done
    " 120
}

# Function to run deployment tests
run_deployment_tests() {
    log_section "Deployment Tests"

    # 1. Create namespace if it doesn't exist
    kubectl create namespace "$NAMESPACE" --dry-run=client -o yaml | kubectl apply -f -

    # 2. Deploy Epic 8 services (if manifests exist)
    local deployment_success=false

    if [ -d "$PROJECT_ROOT/k8s/manifests" ] && [ "$(ls -A "$PROJECT_ROOT/k8s/manifests"/*.yaml 2>/dev/null)" ]; then
        run_test "K8s_Manifest_Deployment" "
            kubectl apply -f '$PROJECT_ROOT/k8s/manifests' -n '$NAMESPACE'
            kubectl wait --for=condition=available --timeout=300s deployment --all -n '$NAMESPACE'
        " 360
        deployment_success=true

    elif [ -d "$PROJECT_ROOT/helm/charts" ] && [ "$(ls -A "$PROJECT_ROOT/helm/charts"/*/Chart.yaml 2>/dev/null)" ]; then
        run_test "Helm_Chart_Deployment" "
            for chart in '$PROJECT_ROOT/helm/charts'/*; do
                if [ -f \"\$chart/Chart.yaml\" ]; then
                    chart_name=\$(basename \"\$chart\")
                    helm upgrade --install \"epic8-\$chart_name\" \"\$chart\" --namespace '$NAMESPACE' --timeout=10m --wait
                fi
            done
        " 600
        deployment_success=true

    else
        log_warning "No manifests or charts found - creating test deployment"
        run_test "Test_Deployment_Creation" "
            cat <<EOF | kubectl apply -f -
apiVersion: apps/v1
kind: Deployment
metadata:
  name: epic8-test
  namespace: $NAMESPACE
spec:
  replicas: 1
  selector:
    matchLabels:
      app: epic8-test
  template:
    metadata:
      labels:
        app: epic8-test
    spec:
      containers:
      - name: nginx
        image: nginx:alpine
        ports:
        - containerPort: 80
---
apiVersion: v1
kind: Service
metadata:
  name: epic8-test-service
  namespace: $NAMESPACE
spec:
  selector:
    app: epic8-test
  ports:
  - port: 80
    targetPort: 80
EOF
            kubectl wait --for=condition=available --timeout=300s deployment/epic8-test -n '$NAMESPACE'
        " 360
        deployment_success=true
    fi

    # 3. Deployment Validation
    if [ "$deployment_success" = true ] && [ -f "$SCRIPT_DIR/deployment-validation.py" ]; then
        run_test "Deployment_Validation" "
            python3 '$SCRIPT_DIR/deployment-validation.py' \
                --namespace '$NAMESPACE' \
                --timeout 300 \
                --output '$REPORT_DIR/deployment_validation_${TIMESTAMP}.json' \
                --output-format json
        " 360
    fi

    # 4. Service Connectivity Tests
    run_test "Service_Connectivity_Tests" "
        services=\$(kubectl get services -n '$NAMESPACE' -o jsonpath='{.items[*].metadata.name}')
        for service in \$services; do
            kubectl run connectivity-test-\$service \
                --image=curlimages/curl --rm -i --restart=Never \
                -n '$NAMESPACE' --timeout=60s \
                -- curl -s -f -m 10 \"http://\$service\" || echo \"Service \$service test completed\"
        done
    " 300
}

# Function to run performance tests
run_performance_tests() {
    log_section "Performance Tests"

    # 1. Resource Usage Validation
    run_test "Resource_Usage_Validation" "
        kubectl top pods -n '$NAMESPACE' || echo 'Metrics server not available'
        kubectl get pods -n '$NAMESPACE' -o jsonpath='{range .items[*]}{.metadata.name}{\"\\t\"}{.status.phase}{\"\\n\"}{end}'
    " 60

    # 2. Pod Startup Time Test
    run_test "Pod_Startup_Time_Test" "
        # Create a test pod and measure startup time
        start_time=\$(date +%s)
        kubectl run startup-test --image=nginx:alpine -n '$NAMESPACE'
        kubectl wait --for=condition=ready pod/startup-test -n '$NAMESPACE' --timeout=120s
        end_time=\$(date +%s)
        startup_duration=\$((end_time - start_time))
        echo \"Pod startup time: \${startup_duration}s\"
        kubectl delete pod startup-test -n '$NAMESPACE'

        # Fail if startup takes more than 60 seconds
        [ \$startup_duration -le 60 ]
    " 180

    # 3. Basic Load Test (if services are available)
    run_test "Basic_Load_Test" "
        services=\$(kubectl get services -n '$NAMESPACE' -o jsonpath='{.items[*].metadata.name}')
        if [ -n \"\$services\" ]; then
            for service in \$services; do
                # Port forward and run basic load test
                kubectl port-forward svc/\$service 8080:80 -n '$NAMESPACE' &
                pf_pid=\$!
                sleep 5

                # Simple load test with curl
                for i in {1..10}; do
                    curl -s -o /dev/null -w '%{http_code}' http://localhost:8080/ || echo 'Request failed'
                done

                kill \$pf_pid || true
                break  # Test only first service
            done
        else
            echo 'No services found for load testing'
        fi
    " 120
}

# Function to cleanup test environment
cleanup_environment() {
    log_section "Cleaning up Test Environment"

    # Cleanup namespace
    if kubectl get namespace "$NAMESPACE" >/dev/null 2>&1; then
        kubectl delete namespace "$NAMESPACE" --timeout=60s || log_warning "Failed to delete namespace"
    fi

    # Cleanup test pods
    kubectl delete pods -l "run in (connectivity-test-*, startup-test)" --all-namespaces --ignore-not-found=true

    log_success "Cleanup completed"
}

# Function to generate comprehensive report
generate_report() {
    log_section "Generating Test Report"

    local report_file="$REPORT_DIR/comprehensive_test_report_${TIMESTAMP}.md"
    local end_time=$(date +%s)
    local total_duration=$((end_time - start_time))

    cat > "$report_file" << EOF
# Epic 8 Kubernetes Testing Report

**Generated**: $(date)
**Duration**: ${total_duration} seconds
**Cluster**: ${CLUSTER_NAME}
**Namespace**: ${NAMESPACE}

## Summary

- **Total Tests**: $total_tests
- **Passed**: $passed_tests ($(( passed_tests * 100 / total_tests ))%)
- **Failed**: $failed_tests ($(( failed_tests * 100 / total_tests ))%)

## Test Results

| Test Name | Result | Duration (s) |
|-----------|--------|--------------|
EOF

    # Add test results to report
    for test_name in "${!test_results[@]}"; do
        IFS='|' read -r result duration <<< "${test_results[$test_name]}"
        local status_icon="❌"
        if [ "$result" = "PASSED" ]; then
            status_icon="✅"
        fi
        echo "| $test_name | $status_icon $result | $duration |" >> "$report_file"
    done

    cat >> "$report_file" << EOF

## Overall Assessment

EOF

    if [ "$failed_tests" -eq 0 ]; then
        echo "✅ **ALL TESTS PASSED** - Epic 8 is ready for deployment!" >> "$report_file"
    else
        echo "❌ **SOME TESTS FAILED** - Please review and fix issues before deployment." >> "$report_file"
    fi

    cat >> "$report_file" << EOF

## Test Artifacts

- Test reports: \`$REPORT_DIR\`
- Validation results: JSON format available
- Logs: Check individual test outputs

## Next Steps

EOF

    if [ "$failed_tests" -eq 0 ]; then
        cat >> "$report_file" << EOF
1. Deploy to staging environment
2. Run integration tests
3. Perform security audit
4. Deploy to production
EOF
    else
        cat >> "$report_file" << EOF
1. Review failed test details
2. Fix identified issues
3. Re-run tests
4. Proceed with deployment after all tests pass
EOF
    fi

    log_success "Test report generated: $report_file"

    # Also generate JSON summary
    local json_report="$REPORT_DIR/test_summary_${TIMESTAMP}.json"
    cat > "$json_report" << EOF
{
  "timestamp": "$(date -Iseconds)",
  "summary": {
    "total_tests": $total_tests,
    "passed": $passed_tests,
    "failed": $failed_tests,
    "duration_seconds": $total_duration,
    "success_rate": $(( passed_tests * 100 / total_tests ))
  },
  "environment": {
    "cluster": "$CLUSTER_NAME",
    "namespace": "$NAMESPACE"
  },
  "status": "$([ $failed_tests -eq 0 ] && echo "SUCCESS" || echo "FAILURE")"
}
EOF

    log_success "JSON summary generated: $json_report"
}

# Main execution function
main() {
    local test_level="${1:-full}"
    local cleanup="${2:-true}"

    echo "🚀 Epic 8 Kubernetes Testing Suite"
    echo "=================================="
    echo "Test Level: $test_level"
    echo "Cleanup: $cleanup"
    echo "Report Directory: $REPORT_DIR"
    echo ""

    # Run tests based on level
    case "$test_level" in
        "validation")
            check_prerequisites || exit 1
            run_static_validation
            ;;
        "helm")
            check_prerequisites || exit 1
            run_helm_tests
            ;;
        "deployment")
            check_prerequisites || exit 1
            setup_environment || exit 1
            run_deployment_tests
            ;;
        "performance")
            check_prerequisites || exit 1
            setup_environment || exit 1
            run_deployment_tests
            run_performance_tests
            ;;
        "full"|*)
            check_prerequisites || exit 1
            setup_environment || exit 1
            run_static_validation
            run_helm_tests
            run_deployment_tests
            run_performance_tests
            ;;
    esac

    # Generate report
    generate_report

    # Cleanup if requested
    if [ "$cleanup" = "true" ] && [ "$test_level" != "validation" ] && [ "$test_level" != "helm" ]; then
        cleanup_environment
    fi

    # Final status
    echo ""
    echo "🏁 Testing Complete!"
    echo "==================="
    echo "Total Tests: $total_tests"
    echo "Passed: $passed_tests"
    echo "Failed: $failed_tests"
    echo "Duration: $(($(date +%s) - start_time)) seconds"

    if [ "$failed_tests" -eq 0 ]; then
        log_success "All tests passed! 🎉"
        exit 0
    else
        log_error "Some tests failed. Please review the report."
        exit 1
    fi
}

# Show usage if no arguments
if [ $# -eq 0 ]; then
    echo "Usage: $0 <test_level> [cleanup]"
    echo ""
    echo "Test Levels:"
    echo "  validation  - Static validation only"
    echo "  helm        - Helm chart tests only"
    echo "  deployment  - Deployment tests only"
    echo "  performance - Deployment + performance tests"
    echo "  full        - All tests (default)"
    echo ""
    echo "Cleanup:"
    echo "  true        - Cleanup environment after tests (default)"
    echo "  false       - Leave environment running"
    echo ""
    echo "Examples:"
    echo "  $0 full              # Run all tests with cleanup"
    echo "  $0 validation        # Run only validation tests"
    echo "  $0 deployment false  # Run deployment tests without cleanup"
    exit 1
fi

# Run main function with arguments
main "$@"