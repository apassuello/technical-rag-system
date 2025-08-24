#!/bin/bash
# Epic 8 Docker Setup and Management Script
# Complete Docker environment setup with user guidance

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BUILD_CONTEXT="$PROJECT_ROOT"

# Epic 8 Services Configuration
SERVICES=(
    "api-gateway:8080"
    "query-analyzer:8082"
    "generator:8081"
    "retriever:8083"
    "cache:8084"
    "analytics:8085"
)

# Supporting Services
SUPPORT_SERVICES=(
    "weaviate:8180"
    "ollama:11434"
    "redis:6379"
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

log_header() {
    echo -e "${PURPLE}[EPIC8]${NC} $1"
}

# Check Docker installation and permissions
check_docker() {
    log_info "Checking Docker installation..."
    
    # Check if Docker is installed
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed. Please install Docker first:"
        echo "  - macOS: https://docs.docker.com/desktop/mac/install/"
        echo "  - Linux: https://docs.docker.com/engine/install/"
        echo "  - Windows: https://docs.docker.com/desktop/windows/install/"
        return 1
    fi
    
    # Check if Docker daemon is running
    if ! docker info &> /dev/null; then
        log_error "Docker daemon is not running. Please start Docker:"
        echo "  - macOS/Windows: Start Docker Desktop application"
        echo "  - Linux: sudo systemctl start docker"
        return 1
    fi
    
    # Check if user has Docker permissions (no sudo needed)
    if docker ps &> /dev/null; then
        log_success "Docker is properly configured (no sudo required)"
    else
        log_warning "Docker may require sudo. Consider adding user to docker group:"
        echo "  sudo usermod -aG docker \$USER"
        echo "  Then logout/login or restart your session"
        log_info "Continuing with current permissions..."
    fi
    
    # Check Docker Compose
    if docker compose version &> /dev/null || docker-compose --version &> /dev/null; then
        log_success "Docker Compose is available"
    else
        log_error "Docker Compose is not available. Install Docker Compose:"
        echo "  - Included with Docker Desktop"
        echo "  - Linux: https://docs.docker.com/compose/install/"
        return 1
    fi
    
    return 0
}

# Validate Epic 1 components availability
validate_epic1_components() {
    log_info "Validating Epic 1 component availability..."
    
    local required_dirs=(
        "src/components"
        "src/core"
        "config"
    )
    
    local missing_dirs=()
    
    for dir in "${required_dirs[@]}"; do
        if [ -d "$BUILD_CONTEXT/$dir" ]; then
            log_success "Found Epic 1 directory: $dir"
        else
            missing_dirs+=("$dir")
            log_error "Missing Epic 1 directory: $dir"
        fi
    done
    
    if [ ${#missing_dirs[@]} -gt 0 ]; then
        log_error "Epic 1 components are not complete. Cannot proceed with Epic 8 build."
        return 1
    fi
    
    # Check specific Epic 1 components
    local epic1_components=(
        "src/components/answer_generators/epic1_answer_generator.py"
        "src/components/query_processors/epic1_query_analyzer.py"
        "src/core/component_factory.py"
    )
    
    for component in "${epic1_components[@]}"; do
        if [ -f "$BUILD_CONTEXT/$component" ]; then
            log_success "Found Epic 1 component: $(basename "$component")"
        else
            log_warning "Optional Epic 1 component not found: $component"
        fi
    done
    
    return 0
}

# Pre-flight checks
preflight_checks() {
    log_header "Running Pre-flight Checks"
    echo ""
    
    # Check Docker
    if ! check_docker; then
        return 1
    fi
    echo ""
    
    # Validate Epic 1 components
    if ! validate_epic1_components; then
        return 1
    fi
    echo ""
    
    # Check service directories
    log_info "Checking service directories..."
    for service_port in "${SERVICES[@]}"; do
        service_name="${service_port%:*}"
        service_dir="$BUILD_CONTEXT/services/$service_name"
        dockerfile="$service_dir/Dockerfile"
        
        if [ -d "$service_dir" ]; then
            if [ -f "$dockerfile" ]; then
                log_success "Service ready: $service_name (with Dockerfile)"
            else
                log_error "Missing Dockerfile: $dockerfile"
                return 1
            fi
        else
            log_error "Missing service directory: services/$service_name"
            return 1
        fi
    done
    
    log_success "All pre-flight checks passed!"
    return 0
}

# Build services with user-friendly output
build_services() {
    local target_services=("$@")
    
    # If no specific services provided, build all
    if [ ${#target_services[@]} -eq 0 ]; then
        log_header "Building All Epic 8 Services"
        target_services=()
        for service_port in "${SERVICES[@]}"; do
            target_services+=("${service_port%:*}")
        done
    else
        log_header "Building Selected Services: ${target_services[*]}"
    fi
    
    echo ""
    
    local failed_services=()
    local successful_services=()
    local total_start_time=$(date +%s)
    
    for service_name in "${target_services[@]}"; do
        local service_start_time=$(date +%s)
        
        echo ""
        log_info "=================================================="
        log_info "Building: $service_name"
        log_info "=================================================="
        
        local dockerfile_path="services/$service_name/Dockerfile"
        local image_tag="epic8/$service_name:latest"
        
        log_info "Configuration:"
        log_info "  - Service: $service_name"
        log_info "  - Dockerfile: $dockerfile_path"
        log_info "  - Build context: $BUILD_CONTEXT"
        log_info "  - Image tag: $image_tag"
        echo ""
        
        # Show what Docker command would be run
        log_info "Docker command:"
        echo "  docker build \\"
        echo "    --file $dockerfile_path \\"
        echo "    --tag $image_tag \\"
        echo "    --build-arg SERVICE_NAME=$service_name \\"
        echo "    $BUILD_CONTEXT"
        echo ""
        
        log_info "Starting build..."
        
        # Build the service
        if docker build \
            --file "$dockerfile_path" \
            --tag "$image_tag" \
            --build-arg SERVICE_NAME="$service_name" \
            "$BUILD_CONTEXT"; then
            
            local service_end_time=$(date +%s)
            local service_duration=$((service_end_time - service_start_time))
            
            successful_services+=("$service_name")
            log_success "Built $service_name successfully (${service_duration}s)"
        else
            failed_services+=("$service_name")
            log_error "Failed to build $service_name"
        fi
    done
    
    # Build Summary
    local total_end_time=$(date +%s)
    local total_duration=$((total_end_time - total_start_time))
    
    echo ""
    log_header "BUILD SUMMARY"
    echo "=================================================="
    log_info "Total build time: ${total_duration}s"
    echo ""
    
    if [ ${#successful_services[@]} -gt 0 ]; then
        log_success "Successfully built ${#successful_services[@]} services:"
        for service in "${successful_services[@]}"; do
            echo "  ✓ $service"
        done
        echo ""
    fi
    
    if [ ${#failed_services[@]} -gt 0 ]; then
        log_error "Failed to build ${#failed_services[@]} services:"
        for service in "${failed_services[@]}"; do
            echo "  ✗ $service"
        done
        echo ""
        
        log_error "Build completed with errors!"
        log_info "To debug failed builds, check the output above or run:"
        for service in "${failed_services[@]}"; do
            echo "  ./docker-setup.sh build $service"
        done
        
        return 1
    else
        log_success "All services built successfully!"
        echo ""
        log_info "Next steps:"
        echo "  1. Start services: ./docker-setup.sh start"
        echo "  2. Check status: ./docker-setup.sh status"
        echo "  3. View logs: ./docker-setup.sh logs [service-name]"
        return 0
    fi
}

# Start services using docker-compose
start_services() {
    local services=("$@")
    
    log_header "Starting Epic 8 Services"
    echo ""
    
    if [ ${#services[@]} -eq 0 ]; then
        log_info "Starting all services with docker-compose..."
        echo ""
        log_info "Docker Compose command:"
        echo "  docker-compose up -d"
        echo ""
        
        if docker-compose up -d; then
            log_success "All services started successfully!"
        else
            log_error "Failed to start services"
            return 1
        fi
    else
        log_info "Starting specific services: ${services[*]}"
        echo ""
        log_info "Docker Compose command:"
        echo "  docker-compose up -d ${services[*]}"
        echo ""
        
        if docker-compose up -d "${services[@]}"; then
            log_success "Selected services started successfully!"
        else
            log_error "Failed to start selected services"
            return 1
        fi
    fi
    
    echo ""
    log_info "Service endpoints:"
    echo "  - API Gateway: http://localhost:8080"
    echo "  - Query Analyzer: http://localhost:8082"
    echo "  - Generator: http://localhost:8081"
    echo "  - Retriever: http://localhost:8083"
    echo "  - Cache: http://localhost:8084"
    echo "  - Analytics: http://localhost:8085"
    echo ""
    echo "  - Weaviate: http://localhost:8180"
    echo "  - Ollama: http://localhost:11434"
    echo "  - Redis: localhost:6379"
}

# Show comprehensive status
show_status() {
    log_header "Epic 8 Platform Status"
    echo ""
    
    # Docker Images Status
    log_info "Docker Images:"
    printf "%-15s %-25s %-15s %-20s\n" "SERVICE" "IMAGE" "TAG" "SIZE"
    echo "==========================================================================="
    
    for service_port in "${SERVICES[@]}"; do
        service_name="${service_port%:*}"
        image_tag="epic8/$service_name"
        
        if docker images --format "table {{.Repository}}:{{.Tag}}\t{{.Size}}" "$image_tag" 2>/dev/null | tail -n +2 | grep -q .; then
            size=$(docker images --format "{{.Size}}" "$image_tag:latest" 2>/dev/null | head -n 1)
            printf "%-15s %-25s %-15s %-20s\n" "$service_name" "$image_tag" "latest" "${size:-unknown}"
        else
            printf "%-15s %-25s %-15s %-20s\n" "$service_name" "$image_tag" "latest" "❌ Not built"
        fi
    done
    
    echo ""
    
    # Container Status
    log_info "Container Status:"
    printf "%-20s %-15s %-10s %-15s %-20s\n" "CONTAINER" "SERVICE" "PORT" "STATUS" "HEALTH"
    echo "===================================================================================="
    
    # Epic 8 Services
    for service_port in "${SERVICES[@]}"; do
        service_name="${service_port%:*}"
        port="${service_port#*:}"
        container_name="epic8_$service_name"
        
        # Get container status
        if docker ps -f name="$container_name" --format "{{.Status}}" | grep -q "Up"; then
            status="🟢 Running"
        elif docker ps -a -f name="$container_name" --format "{{.Status}}" | grep -q .; then
            status="🔴 Stopped"
        else
            status="⚪ Not created"
        fi
        
        # Get health status
        health=$(docker inspect --format='{{.State.Health.Status}}' "$container_name" 2>/dev/null || echo "no-healthcheck")
        case $health in
            "healthy") health_status="✅ Healthy" ;;
            "unhealthy") health_status="❌ Unhealthy" ;;
            "starting") health_status="⏳ Starting" ;;
            *) health_status="➖ No check" ;;
        esac
        
        printf "%-20s %-15s %-10s %-15s %-20s\n" "$container_name" "$service_name" "$port" "$status" "$health_status"
    done
    
    # Supporting Services
    for service_port in "${SUPPORT_SERVICES[@]}"; do
        service_name="${service_port%:*}"
        port="${service_port#*:}"
        container_name="epic8_$service_name"
        
        if docker ps -f name="$container_name" --format "{{.Status}}" | grep -q "Up"; then
            status="🟢 Running"
        elif docker ps -a -f name="$container_name" --format "{{.Status}}" | grep -q .; then
            status="🔴 Stopped"
        else
            status="⚪ Not created"
        fi
        
        # Get health status for supporting services
        health=$(docker inspect --format='{{.State.Health.Status}}' "$container_name" 2>/dev/null || echo "no-healthcheck")
        case $health in
            "healthy") health_status="✅ Healthy" ;;
            "unhealthy") health_status="❌ Unhealthy" ;;
            "starting") health_status="⏳ Starting" ;;
            *) health_status="➖ No check" ;;
        esac
        
        printf "%-20s %-15s %-10s %-15s %-20s\n" "$container_name" "$service_name" "$port" "$status" "$health_status"
    done
}

# Show logs for specific service
show_logs() {
    local service_name="$1"
    local follow="${2:-false}"
    
    if [ -z "$service_name" ]; then
        log_error "Please specify a service name"
        echo "Available services: api-gateway, query-analyzer, generator, retriever, cache, analytics"
        return 1
    fi
    
    log_info "Showing logs for: $service_name"
    echo ""
    
    if [ "$follow" = "true" ]; then
        log_info "Following logs (Press Ctrl+C to stop)..."
        echo ""
        docker-compose logs -f "$service_name"
    else
        docker-compose logs --tail=50 "$service_name"
    fi
}

# Stop services
stop_services() {
    local services=("$@")
    
    log_header "Stopping Epic 8 Services"
    echo ""
    
    if [ ${#services[@]} -eq 0 ]; then
        log_info "Stopping all services..."
        docker-compose down
    else
        log_info "Stopping specific services: ${services[*]}"
        docker-compose stop "${services[@]}"
    fi
    
    log_success "Services stopped"
}

# Clean up Docker resources
cleanup() {
    log_header "Cleaning Up Epic 8 Docker Resources"
    echo ""
    
    log_warning "This will remove all Epic 8 containers, images, and volumes!"
    read -p "Are you sure? (y/N): " -n 1 -r
    echo ""
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        log_info "Stopping and removing containers..."
        docker-compose down -v
        
        log_info "Removing Epic 8 images..."
        docker images -q epic8/* | xargs -r docker rmi -f 2>/dev/null || true
        
        log_info "Removing dangling images..."
        docker image prune -f
        
        log_info "Removing unused volumes..."
        docker volume prune -f
        
        log_success "Cleanup completed"
    else
        log_info "Cleanup cancelled"
    fi
}

# Show help
show_help() {
    cat << EOF
Epic 8 Docker Setup and Management Script

USAGE:
    $0 [COMMAND] [OPTIONS]

COMMANDS:
    check              Run pre-flight checks (Docker, Epic 1 components)
    build [SERVICES]   Build Docker images for all or specific services
    start [SERVICES]   Start services using docker-compose
    stop [SERVICES]    Stop running services
    status             Show comprehensive status of images and containers
    logs SERVICE [-f]  Show logs for a service (use -f to follow)
    cleanup            Remove all Epic 8 Docker resources
    help               Show this help message

SERVICES:
    api-gateway        API Gateway service (port 8080)
    query-analyzer     Query Analyzer service (port 8082)
    generator          Generator service (port 8081)
    retriever          Retriever service (port 8083)
    cache              Cache service (port 8084)
    analytics          Analytics service (port 8085)

EXAMPLES:
    # Complete setup workflow
    $0 check                    # Check prerequisites
    $0 build                    # Build all services
    $0 start                    # Start all services
    $0 status                   # Check status

    # Service-specific operations
    $0 build query-analyzer generator    # Build specific services
    $0 start api-gateway                 # Start only API gateway
    $0 logs query-analyzer -f            # Follow logs for query-analyzer
    $0 stop cache analytics              # Stop specific services

    # Maintenance
    $0 cleanup                  # Clean up all resources

SERVICE ENDPOINTS:
    - API Gateway: http://localhost:8080
    - Query Analyzer: http://localhost:8082
    - Generator: http://localhost:8081
    - Retriever: http://localhost:8083
    - Cache: http://localhost:8084
    - Analytics: http://localhost:8085
    - Weaviate: http://localhost:8180
    - Ollama: http://localhost:11434
    - Redis: localhost:6379

NOTES:
    - All services are built with Epic 1 component integration
    - Build context uses project root for Epic 1 access
    - Services are tagged as epic8/SERVICE_NAME:latest
    - Health checks are configured for all services
    - Use docker-compose.yml for advanced orchestration

TROUBLESHOOTING:
    - If Docker requires sudo, add user to docker group
    - If builds fail, check Epic 1 components are present
    - If services don't start, check port availability
    - Use 'logs' command to debug service issues

EOF
}

# Main execution
main() {
    cd "$PROJECT_ROOT"
    
    case "${1:-help}" in
        "check"|"preflight")
            preflight_checks
            ;;
        "build")
            shift
            if ! preflight_checks; then
                log_error "Pre-flight checks failed. Cannot proceed with build."
                exit 1
            fi
            echo ""
            build_services "$@"
            ;;
        "start"|"up")
            shift
            start_services "$@"
            ;;
        "stop"|"down")
            shift
            stop_services "$@"
            ;;
        "status"|"ps")
            show_status
            ;;
        "logs")
            if [ "$3" = "-f" ]; then
                show_logs "$2" true
            else
                show_logs "$2"
            fi
            ;;
        "cleanup"|"clean")
            cleanup
            ;;
        "help"|"--help"|"-h"|"")
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