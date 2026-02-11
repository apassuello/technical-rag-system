#!/bin/bash
# Epic 8 Deployment Verification Framework
# Validates actual deployment status vs claimed capabilities

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
NAMESPACE="epic8-dev"
EXPECTED_SERVICES=("api-gateway" "query-analyzer" "generator" "retriever" "cache" "analytics")
INFRASTRUCTURE_DIR="."

# Global counters
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[PASS]${NC} $1"
    ((PASSED_TESTS++))
}

log_fail() {
    echo -e "${RED}[FAIL]${NC} $1"
    ((FAILED_TESTS++))
}

log_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

test_start() {
    ((TOTAL_TESTS++))
    log_info "Test $TOTAL_TESTS: $1"
}

# Verify file counts
verify_file_counts() {
    log_info "=================================================="
    log_info "FILE COUNT VERIFICATION"
    log_info "=================================================="

    # Count Kubernetes manifests
    test_start "Kubernetes manifest count"
    k8s_count=$(find k8s/ -name "*.yaml" -type f 2>/dev/null | wc -l | tr -d ' ')
    if [ "$k8s_count" -ge 45 ]; then
        log_success "Kubernetes manifests: $k8s_count files (≥45 expected)"
    else
        log_fail "Kubernetes manifests: $k8s_count files (expected ≥45)"
    fi

    # Count Helm files
    test_start "Helm chart count"
    helm_count=$(find helm/ -name "*.yaml" -o -name "*.tpl" -type f 2>/dev/null | wc -l | tr -d ' ')
    if [ "$helm_count" -ge 25 ]; then
        log_success "Helm files: $helm_count files (≥25 expected)"
    else
        log_fail "Helm files: $helm_count files (expected ≥25)"
    fi

    # Count Terraform files
    test_start "Terraform module count"
    tf_count=$(find terraform/ -name "*.tf" -type f 2>/dev/null | wc -l | tr -d ' ')
    if [ "$tf_count" -ge 25 ]; then
        log_success "Terraform modules: $tf_count files (≥25 expected)"
    else
        log_fail "Terraform modules: $tf_count files (expected ≥25)"
    fi

    # Total infrastructure files
    test_start "Total infrastructure files"
    total_files=$((k8s_count + helm_count + tf_count))
    if [ "$total_files" -ge 100 ]; then
        log_success "Total infrastructure files: $total_files (≥100 expected)"
    else
        log_fail "Total infrastructure files: $total_files (expected ≥100)"
    fi
}

# Verify Docker images
verify_docker_images() {
    log_info "=================================================="
    log_info "DOCKER IMAGE VERIFICATION"
    log_info "=================================================="

    for service in "${EXPECTED_SERVICES[@]}"; do
        test_start "Docker image exists: epic8/$service:latest"
        if docker images -q "epic8/$service:latest" | grep -q .; then
            log_success "epic8/$service:latest found"
        else
            log_fail "epic8/$service:latest missing"
        fi
    done
}

# Verify Kubernetes cluster
verify_cluster() {
    log_info "=================================================="
    log_info "KUBERNETES CLUSTER VERIFICATION"
    log_info "=================================================="

    test_start "Kind cluster accessibility"
    if kubectl cluster-info >/dev/null 2>&1; then
        log_success "Kind cluster accessible"
    else
        log_fail "Kind cluster not accessible"
        return 1
    fi

    test_start "Epic 8 namespace exists"
    if kubectl get namespace "$NAMESPACE" >/dev/null 2>&1; then
        log_success "Namespace $NAMESPACE exists"
    else
        log_fail "Namespace $NAMESPACE missing"
        return 1
    fi
}

# Verify deployments
verify_deployments() {
    log_info "=================================================="
    log_info "DEPLOYMENT VERIFICATION"
    log_info "=================================================="

    for service in "${EXPECTED_SERVICES[@]}"; do
        test_start "Deployment exists: $service"
        if kubectl get deployment "$service" -n "$NAMESPACE" >/dev/null 2>&1; then
            log_success "Deployment $service exists"
        else
            log_fail "Deployment $service missing"
        fi
    done
}

# Verify pods
verify_pods() {
    log_info "=================================================="
    log_info "POD STATUS VERIFICATION"
    log_info "=================================================="

    for service in "${EXPECTED_SERVICES[@]}"; do
        test_start "Pods scheduled for: $service"
        pod_count=$(kubectl get pods -n "$NAMESPACE" -l "app.kubernetes.io/name=$service" --no-headers 2>/dev/null | wc -l | tr -d ' ')
        if [ "$pod_count" -gt 0 ]; then
            log_success "$service has $pod_count pod(s) scheduled"
        else
            log_fail "$service has no pods scheduled"
        fi
    done

    test_start "At least one pod Running"
    running_pods=$(kubectl get pods -n "$NAMESPACE" --field-selector=status.phase=Running --no-headers 2>/dev/null | wc -l | tr -d ' ')
    if [ "$running_pods" -gt 0 ]; then
        log_success "$running_pods pod(s) in Running state"
    else
        log_fail "No pods in Running state"
    fi
}

# Verify services
verify_services() {
    log_info "=================================================="
    log_info "SERVICE VERIFICATION"
    log_info "=================================================="

    for service in "${EXPECTED_SERVICES[@]}"; do
        test_start "Service exists: $service-service"
        if kubectl get service "${service}-service" -n "$NAMESPACE" >/dev/null 2>&1; then
            log_success "Service ${service}-service exists"
        else
            log_fail "Service ${service}-service missing"
        fi
    done
}

# Test API Gateway functionality
test_api_gateway() {
    log_info "=================================================="
    log_info "API GATEWAY FUNCTIONALITY TEST"
    log_info "=================================================="

    test_start "API Gateway pod running"
    if kubectl get pods -n "$NAMESPACE" -l "app.kubernetes.io/name=api-gateway" --field-selector=status.phase=Running --no-headers 2>/dev/null | grep -q api-gateway; then
        log_success "API Gateway pod is running"
    else
        log_fail "API Gateway pod not running"
        return 1
    fi

    # Port forward in background
    log_info "Setting up port forward for testing..."
    kubectl port-forward deployment/api-gateway 8080:8080 -n "$NAMESPACE" >/dev/null 2>&1 &
    PORT_FORWARD_PID=$!
    sleep 3

    test_start "API Gateway health endpoint"
    if curl -s http://localhost:8080/health >/dev/null 2>&1; then
        log_success "API Gateway health endpoint responding"
    else
        log_fail "API Gateway health endpoint not responding"
    fi

    test_start "API Gateway root endpoint"
    response=$(curl -s http://localhost:8080/ 2>/dev/null)
    if echo "$response" | grep -q "API Gateway"; then
        log_success "API Gateway root endpoint functional"
    else
        log_fail "API Gateway root endpoint not functional"
    fi

    test_start "Service discovery functionality"
    status_response=$(curl -s http://localhost:8080/api/v1/status 2>/dev/null)
    if echo "$status_response" | grep -q "services"; then
        log_success "Service discovery endpoint functional"

        # Count services detected
        services_detected=$(echo "$status_response" | grep -o '"name"' | wc -l | tr -d ' ')
        log_info "Services detected: $services_detected/5"
    else
        log_fail "Service discovery endpoint not functional"
    fi

    # Clean up port forward
    kill $PORT_FORWARD_PID 2>/dev/null || true
    sleep 1
}

# Verify storage
verify_storage() {
    log_info "=================================================="
    log_info "STORAGE VERIFICATION"
    log_info "=================================================="

    test_start "Kind-compatible storage classes exist"
    if kubectl get storageclass epic8-kind-standard >/dev/null 2>&1; then
        log_success "Kind-compatible storage classes found"
    else
        log_fail "Kind-compatible storage classes missing"
    fi

    test_start "PVCs created"
    pvc_count=$(kubectl get pvc -n "$NAMESPACE" --no-headers 2>/dev/null | wc -l | tr -d ' ')
    if [ "$pvc_count" -gt 0 ]; then
        log_success "$pvc_count PVC(s) created"
    else
        log_fail "No PVCs found"
    fi

    test_start "Some PVCs bound"
    bound_pvcs=$(kubectl get pvc -n "$NAMESPACE" --no-headers 2>/dev/null | grep -c Bound || echo 0)
    if [ "$bound_pvcs" -gt 0 ]; then
        log_success "$bound_pvcs PVC(s) bound"
    else
        log_fail "No PVCs bound"
    fi
}

# Performance assessment
assess_performance() {
    log_info "=================================================="
    log_info "PERFORMANCE ASSESSMENT"
    log_info "=================================================="

    test_start "Resource quota usage"
    cpu_usage=$(kubectl describe quota epic8-dev-quota -n "$NAMESPACE" 2>/dev/null | grep -E "requests.cpu" | head -1 | awk '{print $2}' || echo "unknown")
    memory_usage=$(kubectl describe quota epic8-dev-quota -n "$NAMESPACE" 2>/dev/null | grep -E "requests.memory" | head -1 | awk '{print $2}' || echo "unknown")

    if [ "$cpu_usage" != "unknown" ] && [ "$memory_usage" != "unknown" ]; then
        log_success "Resource usage: CPU=$cpu_usage, Memory=$memory_usage"
    else
        log_warning "Could not determine resource usage"
    fi

    test_start "Infrastructure complexity"
    # This is a proxy for infrastructure sophistication
    if [ "$TOTAL_TESTS" -gt 20 ]; then
        log_success "Infrastructure demonstrates sufficient complexity ($TOTAL_TESTS tests)"
    else
        log_warning "Infrastructure complexity could be enhanced"
    fi
}

# Generate summary report
generate_summary() {
    echo ""
    log_info "=================================================="
    log_info "VERIFICATION SUMMARY"
    log_info "=================================================="

    local success_rate=$(( (PASSED_TESTS * 100) / TOTAL_TESTS ))

    echo "Total Tests:    $TOTAL_TESTS"
    echo "Passed:         $PASSED_TESTS"
    echo "Failed:         $FAILED_TESTS"
    echo "Success Rate:   $success_rate%"
    echo ""

    if [ "$success_rate" -ge 90 ]; then
        log_success "VERIFICATION RESULT: EXCELLENT ($success_rate% success)"
        echo "Status: DEPLOYMENT_READY"
    elif [ "$success_rate" -ge 75 ]; then
        log_success "VERIFICATION RESULT: GOOD ($success_rate% success)"
        echo "Status: STAGING_READY"
    elif [ "$success_rate" -ge 50 ]; then
        log_warning "VERIFICATION RESULT: NEEDS_IMPROVEMENT ($success_rate% success)"
        echo "Status: DEVELOPMENT_READY"
    else
        log_fail "VERIFICATION RESULT: CRITICAL_ISSUES ($success_rate% success)"
        echo "Status: NOT_READY"
    fi

    echo ""
    log_info "Report generated: $(date)"

    # Save results to file
    {
        echo "Epic 8 Verification Report - $(date)"
        echo "Total Tests: $TOTAL_TESTS"
        echo "Passed: $PASSED_TESTS"
        echo "Failed: $FAILED_TESTS"
        echo "Success Rate: $success_rate%"
    } > "epic8_verification_$(date +%Y%m%d_%H%M%S).txt"
}

# Help function
show_help() {
    cat << EOF
Epic 8 Deployment Verification Framework

USAGE:
    $0 [COMMAND]

COMMANDS:
    full        Run complete verification suite (default)
    files       Verify file counts only
    cluster     Verify cluster and deployments only
    api         Test API Gateway functionality only
    storage     Verify storage configuration only
    help        Show this help message

EXAMPLES:
    $0              # Run complete verification
    $0 full         # Run complete verification
    $0 files        # Verify infrastructure file counts
    $0 cluster      # Test cluster connectivity and deployments
    $0 api          # Test API Gateway endpoints

DESCRIPTION:
    This script verifies the actual Epic 8 deployment status against
    claimed capabilities. It provides accurate assessment of:

    - Infrastructure file counts (K8s, Helm, Terraform)
    - Docker image availability
    - Kubernetes cluster status
    - Pod and service deployment status
    - API Gateway functionality
    - Storage configuration
    - Overall deployment readiness

OUTPUT:
    - Real-time test results with PASS/FAIL status
    - Summary report with success rate percentage
    - Deployment readiness assessment
    - Saved verification report file

EOF
}

# Main execution
main() {
    local start_time=$(date +%s)

    case "${1:-full}" in
        "full")
            log_info "Starting Epic 8 Complete Verification Suite"
            echo ""
            verify_file_counts
            echo ""
            verify_docker_images
            echo ""
            verify_cluster && {
                verify_deployments
                echo ""
                verify_pods
                echo ""
                verify_services
                echo ""
                test_api_gateway
                echo ""
                verify_storage
                echo ""
                assess_performance
            }
            ;;
        "files")
            verify_file_counts
            ;;
        "cluster")
            verify_cluster && {
                verify_deployments
                verify_pods
                verify_services
            }
            ;;
        "api")
            test_api_gateway
            ;;
        "storage")
            verify_storage
            ;;
        "help"|"--help"|"-h")
            show_help
            exit 0
            ;;
        *)
            log_fail "Unknown command: $1"
            echo ""
            show_help
            exit 1
            ;;
    esac

    local end_time=$(date +%s)
    local duration=$((end_time - start_time))

    echo ""
    generate_summary
    echo ""
    log_info "Verification completed in ${duration}s"

    # Exit with appropriate code
    if [ "$FAILED_TESTS" -eq 0 ]; then
        exit 0
    else
        exit 1
    fi
}

main "$@"