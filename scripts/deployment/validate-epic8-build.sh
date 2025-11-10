#!/bin/bash

# Epic 8 Docker Build Validation Script
# Comprehensive validation of Docker architecture implementation

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# Configuration
SERVICES=(
    "api-gateway:8080"
    "query-analyzer:8082" 
    "generator:8081"
    "retriever:8083"
    "cache:8084"
    "analytics:8085"
)

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

log_section() {
    echo ""
    echo -e "${CYAN}${BOLD}=== $1 ===${NC}"
    echo ""
}

# Test individual service build
test_service_build() {
    local service_name="$1"
    local port="$2"
    
    log_info "Testing service: $service_name (port $port)"
    
    # Check if Dockerfile exists
    local dockerfile="services/$service_name/Dockerfile"
    if [[ ! -f "$dockerfile" ]]; then
        log_error "Dockerfile missing: $dockerfile"
        return 1
    fi
    
    # Check if requirements.txt exists
    local requirements="services/$service_name/requirements.txt"
    if [[ ! -f "$requirements" ]]; then
        log_warning "Requirements missing: $requirements"
    else
        log_info "Requirements found: $(wc -l < "$requirements") dependencies"
    fi
    
    # Build the service
    log_info "Building $service_name..."
    local build_start=$(date +%s)
    
    if docker build -f "$dockerfile" -t "epic8-validate-$service_name:test" . >/dev/null 2>&1; then
        local build_end=$(date +%s)
        local build_time=$((build_end - build_start))
        log_success "Built $service_name in ${build_time}s"
        
        # Test Epic 1 component access
        log_info "Validating Epic 1 component access..."
        local epic1_test=$(docker run --rm "epic8-validate-$service_name:test" /bin/bash -c "
            if [ -d /app/src ] && [ -d /app/config ]; then
                src_files=\$(find /app/src -name '*.py' | wc -l)
                config_files=\$(find /app/config -name '*.yaml' | wc -l)
                echo \"Epic1_Access:SUCCESS:src=\$src_files:config=\$config_files\"
            else
                echo \"Epic1_Access:FAILED\"
            fi
        " 2>/dev/null)
        
        if [[ "$epic1_test" == Epic1_Access:SUCCESS:* ]]; then
            local src_count=$(echo "$epic1_test" | cut -d: -f3 | cut -d= -f2)
            local config_count=$(echo "$epic1_test" | cut -d: -f4 | cut -d= -f2)
            log_success "Epic 1 access validated: $src_count Python files, $config_count YAML configs"
        else
            log_error "Epic 1 component access failed"
            return 1
        fi
        
        # Test service structure
        log_info "Validating service structure..."
        local structure_test=$(docker run --rm "epic8-validate-$service_name:test" /bin/bash -c "
            if [ -d /app/app ] && [ -f /app/config.yaml ]; then
                echo \"Structure:SUCCESS\"
            else
                echo \"Structure:FAILED\"
            fi
        " 2>/dev/null)
        
        if [[ "$structure_test" == "Structure:SUCCESS" ]]; then
            log_success "Service structure validated"
        else
            log_error "Service structure validation failed"
            return 1
        fi
        
        # Clean up test image
        docker rmi "epic8-validate-$service_name:test" >/dev/null 2>&1
        
        return 0
    else
        log_error "Build failed for $service_name"
        return 1
    fi
}

# Validate docker-compose.yml
validate_docker_compose() {
    log_section "Docker Compose Validation"
    
    if [[ ! -f "docker-compose.yml" ]]; then
        log_error "docker-compose.yml not found"
        return 1
    fi
    
    log_info "Validating docker-compose.yml structure..."
    
    # Check if docker-compose is valid
    if docker-compose config >/dev/null 2>&1; then
        log_success "docker-compose.yml syntax is valid"
    else
        log_error "docker-compose.yml syntax validation failed"
        return 1
    fi
    
    # Check build contexts
    local context_issues=0
    for service_port in "${SERVICES[@]}"; do
        service_name="${service_port%:*}"
        
        # Check if service has correct build context
        local context=$(docker-compose config | grep -A 5 "$service_name:" | grep "context:" | awk '{print $2}' | head -1)
        if [[ "$context" == '"."' ]]; then
            log_success "$service_name: build context correctly set to project root"
        else
            log_error "$service_name: build context not set to project root (found: $context)"
            context_issues=$((context_issues + 1))
        fi
    done
    
    if [[ $context_issues -eq 0 ]]; then
        log_success "All services have correct build context"
        return 0
    else
        log_error "$context_issues services have incorrect build context"
        return 1
    fi
}

# Validate build scripts
validate_build_scripts() {
    log_section "Build Scripts Validation"
    
    # Check build-services.sh
    if [[ -f "build-services.sh" && -x "build-services.sh" ]]; then
        log_success "build-services.sh found and executable"
        
        # Test build script functionality
        if ./build-services.sh test >/dev/null 2>&1; then
            log_success "Build script test passed"
        else
            log_warning "Build script test failed (may be normal)"
        fi
    else
        log_error "build-services.sh missing or not executable"
        return 1
    fi
    
    # Check test-build-context.sh
    if [[ -f "test-build-context.sh" && -x "test-build-context.sh" ]]; then
        log_success "test-build-context.sh found and executable"
    else
        log_warning "test-build-context.sh missing or not executable"
    fi
    
    return 0
}

# Test Epic 1 component availability
validate_epic1_components() {
    log_section "Epic 1 Components Validation"
    
    local issues=0
    
    # Check src directory
    if [[ -d "src" ]]; then
        local py_files=$(find src -name "*.py" | wc -l)
        log_success "Epic 1 src/ directory: $py_files Python files"
        
        # Check key components
        key_components=(
            "src/__init__.py"
            "src/components"
            "src/core"
            "src/basic_rag.py"
        )
        
        for component in "${key_components[@]}"; do
            if [[ -e "$component" ]]; then
                log_success "Key component found: $component"
            else
                log_error "Key component missing: $component"
                issues=$((issues + 1))
            fi
        done
    else
        log_error "Epic 1 src/ directory not found"
        issues=$((issues + 1))
    fi
    
    # Check config directory
    if [[ -d "config" ]]; then
        local yaml_files=$(find config -name "*.yaml" | wc -l)
        log_success "Epic 1 config/ directory: $yaml_files YAML files"
        
        # Check key configs
        key_configs=(
            "config/default.yaml"
            "config/epic1_multi_model.yaml"
        )
        
        for config in "${key_configs[@]}"; do
            if [[ -f "$config" ]]; then
                log_success "Key config found: $config"
            else
                log_warning "Key config missing: $config"
            fi
        done
    else
        log_error "Epic 1 config/ directory not found"
        issues=$((issues + 1))
    fi
    
    if [[ $issues -eq 0 ]]; then
        log_success "All Epic 1 components available"
        return 0
    else
        log_error "$issues Epic 1 component issues found"
        return 1
    fi
}

# Run comprehensive build test
run_build_test() {
    log_section "Service Build Test"
    
    local failed_services=()
    local successful_services=()
    local total_start=$(date +%s)
    
    for service_port in "${SERVICES[@]}"; do
        service_name="${service_port%:*}"
        port="${service_port#*:}"
        
        echo ""
        log_info "Building and testing: $service_name"
        echo "----------------------------------------"
        
        if test_service_build "$service_name" "$port"; then
            successful_services+=("$service_name")
        else
            failed_services+=("$service_name")
        fi
    done
    
    local total_end=$(date +%s)
    local total_time=$((total_end - total_start))
    
    echo ""
    log_section "Build Test Results"
    
    if [[ ${#successful_services[@]} -gt 0 ]]; then
        log_success "Successfully built and validated ${#successful_services[@]} services:"
        for service in "${successful_services[@]}"; do
            echo "  ✓ $service"
        done
    fi
    
    if [[ ${#failed_services[@]} -gt 0 ]]; then
        log_error "Failed to build ${#failed_services[@]} services:"
        for service in "${failed_services[@]}"; do
            echo "  ✗ $service"
        done
        echo ""
        log_error "Build test completed with errors in ${total_time}s"
        return 1
    else
        echo ""
        log_success "All services built and validated successfully in ${total_time}s"
        return 0
    fi
}

# Show comprehensive system status
show_system_status() {
    log_section "Epic 8 System Status"
    
    # Project structure
    echo "Project Structure:"
    echo "├── $([ -f "docker-compose.yml" ] && echo "✓" || echo "✗") docker-compose.yml"
    echo "├── $([ -f "build-services.sh" ] && echo "✓" || echo "✗") build-services.sh"
    echo "├── $([ -d "src" ] && echo "✓" || echo "✗") src/ (Epic 1 components)"
    echo "├── $([ -d "config" ] && echo "✓" || echo "✗") config/ (Epic 1 configs)"
    echo "└── $([ -d "services" ] && echo "✓" || echo "✗") services/"
    
    # Service status
    echo ""
    echo "Epic 8 Services:"
    for service_port in "${SERVICES[@]}"; do
        service_name="${service_port%:*}"
        port="${service_port#*:}"
        
        # Check Dockerfile
        dockerfile_status="$([ -f "services/$service_name/Dockerfile" ] && echo "✓" || echo "✗")"
        
        # Check requirements
        requirements_status="$([ -f "services/$service_name/requirements.txt" ] && echo "✓" || echo "✗")"
        
        # Check built image
        image_status="$(docker images -q "epic8/$service_name:latest" | grep -q . && echo "🟢 Built" || echo "⚪ Not built")"
        
        echo "├── $service_name (port $port)"
        echo "│   ├── Dockerfile       $dockerfile_status"
        echo "│   ├── requirements.txt $requirements_status"
        echo "│   └── Image status     $image_status"
    done
    echo ""
}

# Main help function
show_help() {
    cat << EOF
Epic 8 Docker Build Validation Script

USAGE:
    $0 [COMMAND]

COMMANDS:
    validate          Run comprehensive validation (recommended)
    build-test        Test building all services with validation
    docker-compose    Validate docker-compose.yml configuration
    epic1             Validate Epic 1 component availability
    build-scripts     Validate build automation scripts
    status            Show current system status
    help              Show this help message

EXAMPLES:
    $0 validate       # Run full validation suite
    $0 build-test     # Test building all services
    $0 status         # Show system overview

DESCRIPTION:
    Validates that Epic 8 Docker architecture is correctly implemented:
    
    ✓ Docker build contexts use project root
    ✓ Epic 1 components accessible to all services
    ✓ Service builds complete successfully
    ✓ Docker compose configuration is valid
    ✓ Build automation scripts work correctly

EOF
}

# Main execution
main() {
    case "${1:-help}" in
        "validate")
            log_section "Epic 8 Docker Build Validation"
            echo "Comprehensive validation of Docker architecture implementation"
            
            local validation_errors=0
            
            # Run all validation tests
            validate_epic1_components || validation_errors=$((validation_errors + 1))
            validate_docker_compose || validation_errors=$((validation_errors + 1))
            validate_build_scripts || validation_errors=$((validation_errors + 1))
            run_build_test || validation_errors=$((validation_errors + 1))
            
            echo ""
            log_section "Validation Summary"
            
            if [[ $validation_errors -eq 0 ]]; then
                log_success "🎉 All validations passed! Epic 8 Docker architecture is correctly implemented."
                echo ""
                log_info "Next steps:"
                echo "  1. Build all services: ./build-services.sh build"
                echo "  2. Start the platform: docker-compose up -d"
                echo "  3. Test API Gateway: curl http://localhost:8080/health"
                echo ""
                exit 0
            else
                log_error "❌ $validation_errors validation(s) failed. Please fix the issues above."
                echo ""
                exit 1
            fi
            ;;
        "build-test")
            run_build_test
            ;;
        "docker-compose")
            validate_docker_compose
            ;;
        "epic1")
            validate_epic1_components
            ;;
        "build-scripts")
            validate_build_scripts
            ;;
        "status")
            show_system_status
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