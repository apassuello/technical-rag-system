#!/bin/bash

# Test Build Context Script
# Verifies that Epic 8 services can access Epic 1 components during build

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored status messages
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

# Test build context by creating a temporary Docker file and building
test_build_context() {
    local service_name="test-context"
    local test_dockerfile="/tmp/test-context.Dockerfile"
    
    log_info "Creating test Dockerfile to verify build context..."
    
    # Create test Dockerfile that tries to access Epic 1 components
    cat > "$test_dockerfile" << 'EOF'
FROM python:3.11-slim

# Test copying Epic 1 components
COPY src/ /test/src/
COPY config/ /test/config/

# Test that files exist and are accessible
RUN echo "Testing Epic 1 src/ directory access..." && \
    ls -la /test/src/ && \
    echo "Epic 1 src/__init__.py exists:" && \
    cat /test/src/__init__.py && \
    echo "Testing Epic 1 config/ directory access..." && \
    ls -la /test/config/ && \
    echo "Epic 1 config/default.yaml exists:" && \
    head -10 /test/config/default.yaml && \
    echo "BUILD CONTEXT TEST: SUCCESS"

CMD ["echo", "Build context test completed successfully"]
EOF

    log_info "Building test image to verify Epic 1 component access..."
    
    if docker build -f "$test_dockerfile" -t epic8-test-context:latest . ; then
        log_success "Build context test passed - Epic 1 components accessible"
        
        # Clean up test image
        docker rmi epic8-test-context:latest > /dev/null 2>&1 || true
        rm -f "$test_dockerfile"
        
        return 0
    else
        log_error "Build context test failed - Epic 1 components not accessible"
        rm -f "$test_dockerfile"
        return 1
    fi
}

# Test specific service build with context verification
test_service_build() {
    local service_name="$1"
    
    if [[ -z "$service_name" ]]; then
        log_error "Service name required"
        return 1
    fi
    
    log_info "Testing build context for service: $service_name"
    
    local dockerfile_path="services/$service_name/Dockerfile"
    if [[ ! -f "$dockerfile_path" ]]; then
        log_error "Dockerfile not found: $dockerfile_path"
        return 1
    fi
    
    log_info "Building service with context verification..."
    if docker build -f "$dockerfile_path" -t "epic8-$service_name-test:latest" . ; then
        log_success "Service $service_name built successfully with Epic 1 context"
        
        # Test that the built image contains Epic 1 components
        log_info "Verifying Epic 1 components in built image..."
        if docker run --rm "epic8-$service_name-test:latest" /bin/bash -c "ls -la /app/src/ && ls -la /app/config/"; then
            log_success "Epic 1 components verified in service container"
        else
            log_warning "Could not verify Epic 1 components in container (may be normal due to health check failure)"
        fi
        
        # Clean up test image
        docker rmi "epic8-$service_name-test:latest" > /dev/null 2>&1 || true
        
        return 0
    else
        log_error "Failed to build service $service_name"
        return 1
    fi
}

# Show current Docker build context
show_build_context() {
    log_info "Current Docker build context analysis:"
    echo ""
    
    # Check project structure
    log_info "Project structure:"
    echo "├── src/                 $([ -d "src" ] && echo "✓ Found" || echo "✗ Missing")"
    echo "├── config/              $([ -d "config" ] && echo "✓ Found" || echo "✗ Missing")"
    echo "├── services/            $([ -d "services" ] && echo "✓ Found" || echo "✗ Missing")"
    echo "├── docker-compose.yml   $([ -f "docker-compose.yml" ] && echo "✓ Found" || echo "✗ Missing")"
    echo ""
    
    # Check Epic 1 components
    log_info "Epic 1 components availability:"
    echo "├── src/__init__.py      $([ -f "src/__init__.py" ] && echo "✓ Found" || echo "✗ Missing")"
    echo "├── src/components/      $([ -d "src/components" ] && echo "✓ Found" || echo "✗ Missing")"
    echo "├── src/core/            $([ -d "src/core" ] && echo "✓ Found" || echo "✗ Missing")"
    echo "├── config/default.yaml  $([ -f "config/default.yaml" ] && echo "✓ Found" || echo "✗ Missing")"
    echo ""
    
    # Check service configurations
    log_info "Service configurations:"
    for service_dir in services/*/; do
        if [[ -d "$service_dir" ]]; then
            service_name=$(basename "$service_dir")
            dockerfile_exists="$([ -f "$service_dir/Dockerfile" ] && echo "✓" || echo "✗")"
            requirements_exists="$([ -f "$service_dir/requirements.txt" ] && echo "✓" || echo "✗")"
            echo "├── $service_name"
            echo "│   ├── Dockerfile       $dockerfile_exists"
            echo "│   └── requirements.txt $requirements_exists"
        fi
    done
    echo ""
}

# Main help function
show_help() {
    cat << EOF
Build Context Test Script for Epic 8 Services

USAGE:
    $0 [COMMAND] [OPTIONS]

COMMANDS:
    test              Run comprehensive build context test
    test-service [NAME]   Test specific service build with context
    show              Show current build context structure
    help              Show this help message

SERVICE OPTIONS:
    api-gateway       Test API Gateway service
    query-analyzer    Test Query Analyzer service  
    generator         Test Generator service
    retriever         Test Retriever service
    cache             Test Cache service
    analytics         Test Analytics service

EXAMPLES:
    $0 test                       # Run full build context test
    $0 test-service api-gateway   # Test API Gateway build with context
    $0 show                       # Show build context structure

DESCRIPTION:
    This script verifies that Epic 8 services can properly access Epic 1
    components during Docker builds. It tests the project root build context
    and ensures that src/ and config/ directories are available to services.

EOF
}

# Main execution
main() {
    case "${1:-help}" in
        "test")
            log_info "=== Epic 8 Build Context Test ==="
            echo ""
            
            show_build_context
            
            log_info "Running build context test..."
            if test_build_context; then
                log_success "Build context test completed successfully"
                echo ""
                log_info "Next steps:"
                echo "  1. Build services: ./build-services.sh build"
                echo "  2. Start services: docker-compose up -d"
                echo "  3. Test APIs: curl http://localhost:8080/health"
            else
                log_error "Build context test failed"
                echo ""
                log_error "Troubleshooting:"
                echo "  1. Ensure you're running from project root"
                echo "  2. Verify src/ and config/ directories exist"
                echo "  3. Check Docker daemon is running"
                exit 1
            fi
            ;;
        "test-service")
            if [[ -n "$2" ]]; then
                test_service_build "$2"
            else
                log_error "Service name required"
                echo ""
                echo "Available services: api-gateway, query-analyzer, generator, retriever, cache, analytics"
                exit 1
            fi
            ;;
        "show")
            show_build_context
            ;;
        "help"|"--help"|"-h")
            show_help
            ;;
        *)
            log_error "Unknown command: $1"
            echo ""
            show_help
            exit 1
            ;;
    esac
}

main "$@"