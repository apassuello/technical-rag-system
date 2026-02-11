#!/bin/bash
# Epic 8 Service Build Script
# Builds all Docker services with project-root context

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration - Navigate to project root (2 levels up from scripts/deployment/)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
BUILD_CONTEXT="$PROJECT_ROOT"

# Epic 8 Services
SERVICES=(
    "api-gateway:8080"
    "query-analyzer:8082"
    "generator:8081"
    "retriever:8083"
    "cache:8084"
    "analytics:8085"
)

# Functions
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

# Build single service
build_service() {
    local service_name="$1"
    local dockerfile_path="services/$service_name/Dockerfile"
    local image_tag="epic8/$service_name:latest"
    
    log_info "Building service: $service_name"
    log_info "  - Dockerfile: $dockerfile_path"
    log_info "  - Build context: $BUILD_CONTEXT"
    log_info "  - Image tag: $image_tag"
    
    if [ ! -f "$BUILD_CONTEXT/$dockerfile_path" ]; then
        log_error "Dockerfile not found: $dockerfile_path"
        return 1
    fi
    
    # Build the service
    if docker build \
        --file "$dockerfile_path" \
        --tag "$image_tag" \
        --build-arg SERVICE_NAME="$service_name" \
        "$BUILD_CONTEXT"; then
        log_success "Built $service_name successfully"
        return 0
    else
        log_error "Failed to build $service_name"
        return 1
    fi
}

# Test build context
test_build_context() {
    log_info "Testing build context access..."
    
    # Check if Epic 1 src directory exists
    if [ -d "$BUILD_CONTEXT/src" ]; then
        log_success "Epic 1 src directory found: $BUILD_CONTEXT/src"
    else
        log_error "Epic 1 src directory not found: $BUILD_CONTEXT/src"
        return 1
    fi
    
    # Check if config directory exists  
    if [ -d "$BUILD_CONTEXT/config" ]; then
        log_success "Config directory found: $BUILD_CONTEXT/config"
    else
        log_error "Config directory not found: $BUILD_CONTEXT/config"
        return 1
    fi
    
    # Check if service directories exist
    for service_port in "${SERVICES[@]}"; do
        service_name="${service_port%:*}"
        if [ -d "$BUILD_CONTEXT/services/$service_name" ]; then
            log_success "Service directory found: services/$service_name"
        else
            log_error "Service directory not found: services/$service_name"
            return 1
        fi
    done
    
    log_success "Build context test passed"
}

# Build all services
build_all() {
    log_info "Building all Epic 8 services..."
    
    local failed_services=()
    local successful_services=()
    
    for service_port in "${SERVICES[@]}"; do
        service_name="${service_port%:*}"
        
        echo ""
        log_info "=================================================="
        log_info "Building service: $service_name"
        log_info "=================================================="
        
        if build_service "$service_name"; then
            successful_services+=("$service_name")
        else
            failed_services+=("$service_name")
        fi
    done
    
    # Summary
    echo ""
    log_info "=================================================="
    log_info "BUILD SUMMARY"
    log_info "=================================================="
    
    if [ ${#successful_services[@]} -gt 0 ]; then
        log_success "Successfully built ${#successful_services[@]} services:"
        for service in "${successful_services[@]}"; do
            echo "  ✓ $service"
        done
    fi
    
    if [ ${#failed_services[@]} -gt 0 ]; then
        log_error "Failed to build ${#failed_services[@]} services:"
        for service in "${failed_services[@]}"; do
            echo "  ✗ $service"
        done
        echo ""
        log_error "Build completed with errors"
        return 1
    else
        echo ""
        log_success "All services built successfully!"
        return 0
    fi
}

# Clean Docker images
clean() {
    log_info "Cleaning Epic 8 Docker images..."
    
    # Remove Epic 8 service images
    docker images -q epic8/* | xargs -r docker rmi -f 2>/dev/null || true
    
    # Remove dangling images
    docker image prune -f
    
    log_success "Cleanup completed"
}

# Show service status
status() {
    log_info "Epic 8 Service Status:"
    echo ""
    
    printf "%-15s %-20s %-10s %-20s\n" "SERVICE" "IMAGE" "PORT" "STATUS"
    echo "=================================================================="
    
    for service_port in "${SERVICES[@]}"; do
        service_name="${service_port%:*}"
        port="${service_port#*:}"
        image_tag="epic8/$service_name:latest"
        
        # Check if image exists
        if docker images -q "$image_tag" | grep -q .; then
            image_status="✓ Built"
        else
            image_status="✗ Not built"
        fi
        
        # Check if container is running
        if docker ps -q -f name="epic8_$service_name" | grep -q .; then
            container_status="🟢 Running"
        elif docker ps -a -q -f name="epic8_$service_name" | grep -q .; then
            container_status="🔴 Stopped"
        else
            container_status="⚪ Not created"
        fi
        
        printf "%-15s %-20s %-10s %-20s\n" "$service_name" "$image_status" "$port" "$container_status"
    done
}

# Help function
show_help() {
    cat << EOF
Epic 8 Service Build Script

USAGE:
    $0 [COMMAND] [OPTIONS]

COMMANDS:
    build [SERVICE]     Build all services or specific service
    test               Test build context access
    clean              Clean Docker images and dangling resources
    status             Show service build and runtime status
    help               Show this help message

SERVICE OPTIONS:
    api-gateway        API Gateway service (port 8080)
    query-analyzer     Query Analyzer service (port 8082)  
    generator          Generator service (port 8081)
    retriever          Retriever service (port 8083)
    cache              Cache service (port 8084)
    analytics          Analytics service (port 8085)

EXAMPLES:
    $0 build                    # Build all services
    $0 build query-analyzer     # Build only query-analyzer service
    $0 test                     # Test build context
    $0 clean                    # Clean Docker images
    $0 status                   # Show service status

NOTES:
    - All builds use project root as build context
    - Epic 1 components (src/, config/) are available to all services
    - Services are tagged as epic8/SERVICE_NAME:latest
    - Use docker-compose.yml for orchestration after building

EOF
}

# Main execution
main() {
    cd "$PROJECT_ROOT"
    
    case "${1:-help}" in
        "build")
            if [ -n "$2" ]; then
                # Build specific service
                if build_service "$2"; then
                    log_success "Service $2 built successfully"
                else
                    log_error "Failed to build service $2"
                    exit 1
                fi
            else
                # Build all services
                if ! test_build_context; then
                    log_error "Build context test failed"
                    exit 1
                fi
                
                if build_all; then
                    log_success "All services built successfully"
                else
                    log_error "Some services failed to build"
                    exit 1
                fi
            fi
            ;;
        "test")
            test_build_context
            ;;
        "clean")
            clean
            ;;
        "status")
            status
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