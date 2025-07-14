#!/bin/bash
# Weaviate Setup Script for Epic 2 RAG System
# This script sets up the complete Weaviate environment for Epic 2 testing

set -euo pipefail  # Exit on error, undefined vars, pipe failures

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Script configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
WEAVIATE_URL="http://localhost:8080"
OLLAMA_URL="http://localhost:11434"
MAX_WAIT_TIME=180  # Maximum wait time in seconds

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

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Wait for service to be ready
wait_for_service() {
    local url="$1"
    local service_name="$2"
    local max_attempts=$((MAX_WAIT_TIME / 5))
    local attempt=1
    
    log_info "Waiting for $service_name to be ready at $url..."
    
    while [ $attempt -le $max_attempts ]; do
        if curl -s -f "$url" >/dev/null 2>&1; then
            log_success "$service_name is ready!"
            return 0
        fi
        
        echo -n "."
        sleep 5
        ((attempt++))
    done
    
    log_error "$service_name failed to start within $MAX_WAIT_TIME seconds"
    return 1
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check Docker
    if ! command_exists docker; then
        log_error "Docker is not installed. Please install Docker first."
        log_info "Visit: https://docs.docker.com/get-docker/"
        exit 1
    fi
    
    # Check Docker Compose
    if ! command_exists docker-compose && ! docker compose version >/dev/null 2>&1; then
        log_error "Docker Compose is not available. Please install Docker Compose."
        exit 1
    fi
    
    # Determine Docker Compose command
    if docker compose version >/dev/null 2>&1; then
        DOCKER_COMPOSE="docker compose"
    else
        DOCKER_COMPOSE="docker-compose"
    fi
    
    # Check if Docker is running
    if ! docker info >/dev/null 2>&1; then
        log_error "Docker is not running. Please start Docker first."
        exit 1
    fi
    
    log_success "All prerequisites satisfied"
}

# Setup Weaviate
setup_weaviate() {
    log_info "Setting up Weaviate with Epic 2 configuration..."
    
    cd "$PROJECT_ROOT"
    
    # Check if docker-compose.yml exists
    if [ ! -f "docker-compose.yml" ]; then
        log_error "docker-compose.yml not found in project root"
        exit 1
    fi
    
    # Stop existing containers
    log_info "Stopping any existing containers..."
    $DOCKER_COMPOSE down
    
    # Start Weaviate and Ollama
    log_info "Starting Weaviate and Ollama services..."
    $DOCKER_COMPOSE up -d weaviate ollama
    
    # Wait for services to be ready
    wait_for_service "$WEAVIATE_URL/v1/.well-known/ready" "Weaviate"
    wait_for_service "$OLLAMA_URL/api/version" "Ollama"
    
    log_success "Epic 2 services started successfully"
}

# Validate Weaviate installation
validate_weaviate() {
    log_info "Validating Weaviate installation..."
    
    # Test basic connectivity
    local ready_status
    ready_status=$(curl -s "$WEAVIATE_URL/v1/.well-known/ready" | grep -o '"status":"ok"' || echo "")
    
    if [ -z "$ready_status" ]; then
        log_error "Weaviate ready check failed"
        return 1
    fi
    
    # Test live endpoint
    local live_status
    live_status=$(curl -s "$WEAVIATE_URL/v1/.well-known/live" | grep -o '"status":"ok"' || echo "")
    
    if [ -z "$live_status" ]; then
        log_error "Weaviate live check failed"
        return 1
    fi
    
    # Test schema endpoint
    local schema_response
    schema_response=$(curl -s "$WEAVIATE_URL/v1/schema")
    
    if [ -z "$schema_response" ]; then
        log_error "Weaviate schema endpoint failed"
        return 1
    fi
    
    # Test Ollama
    local ollama_version
    ollama_version=$(curl -s "$OLLAMA_URL/api/version" | grep -o '"version"' || echo "")
    
    if [ -z "$ollama_version" ]; then
        log_warning "Ollama validation failed (non-critical for Weaviate testing)"
    else
        log_success "Ollama is responding correctly"
    fi
    
    log_success "Weaviate validation completed successfully"
}

# Test Epic 2 integration
test_epic2_integration() {
    log_info "Testing Epic 2 integration with Weaviate..."
    
    cd "$PROJECT_ROOT"
    
    # Check if Python test script exists
    if [ -f "scripts/test_weaviate_connection.py" ]; then
        log_info "Running Epic 2 integration test..."
        
        if python scripts/test_weaviate_connection.py; then
            log_success "Epic 2 integration test passed"
        else
            log_warning "Epic 2 integration test failed (check Python environment)"
        fi
    else
        log_info "Creating basic Weaviate connection test..."
        
        # Basic Python connectivity test
        python3 -c "
import requests
import sys

try:
    response = requests.get('$WEAVIATE_URL/v1/.well-known/ready', timeout=10)
    if response.status_code == 200 and 'ok' in response.text:
        print('✅ Python → Weaviate connection successful')
        sys.exit(0)
    else:
        print('❌ Weaviate responded but not ready')
        sys.exit(1)
except Exception as e:
    print(f'❌ Python → Weaviate connection failed: {e}')
    sys.exit(1)
" || log_warning "Python connectivity test failed"
    fi
}

# Show service status
show_status() {
    log_info "Epic 2 Service Status:"
    echo ""
    $DOCKER_COMPOSE ps
    echo ""
    
    log_info "Service Health:"
    echo "Weaviate Ready: $(curl -s "$WEAVIATE_URL/v1/.well-known/ready" 2>/dev/null || echo "❌ Failed")"
    echo "Weaviate Live:  $(curl -s "$WEAVIATE_URL/v1/.well-known/live" 2>/dev/null || echo "❌ Failed")"
    echo "Ollama Version: $(curl -s "$OLLAMA_URL/api/version" 2>/dev/null | grep -o '"version":"[^"]*"' || echo "❌ Failed")"
    echo ""
    
    log_info "Access URLs:"
    echo "Weaviate API:    $WEAVIATE_URL"
    echo "Weaviate Schema: $WEAVIATE_URL/v1/schema"
    echo "Ollama API:      $OLLAMA_URL"
    echo ""
}

# Show usage information
show_usage() {
    echo "Usage: $0 [OPTION]"
    echo ""
    echo "Epic 2 Weaviate Setup Script"
    echo ""
    echo "Options:"
    echo "  setup     Set up and start Weaviate + Ollama services"
    echo "  validate  Validate existing Weaviate installation"
    echo "  test      Test Epic 2 integration with Weaviate"
    echo "  status    Show current service status"
    echo "  stop      Stop all Epic 2 services"
    echo "  restart   Restart all Epic 2 services"
    echo "  clean     Stop services and remove volumes (DESTRUCTIVE)"
    echo "  help      Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 setup     # Complete setup and validation"
    echo "  $0 status    # Check service status"
    echo "  $0 clean     # Clean reset (removes all data)"
    echo ""
}

# Stop services
stop_services() {
    log_info "Stopping Epic 2 services..."
    cd "$PROJECT_ROOT"
    $DOCKER_COMPOSE down
    log_success "Services stopped"
}

# Restart services
restart_services() {
    log_info "Restarting Epic 2 services..."
    cd "$PROJECT_ROOT"
    $DOCKER_COMPOSE restart
    
    # Wait for services to be ready
    wait_for_service "$WEAVIATE_URL/v1/.well-known/ready" "Weaviate"
    wait_for_service "$OLLAMA_URL/api/version" "Ollama"
    
    log_success "Services restarted successfully"
}

# Clean installation (DESTRUCTIVE)
clean_installation() {
    log_warning "This will DELETE ALL Weaviate data and Docker volumes!"
    read -p "Are you sure? (y/N): " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        log_info "Performing clean installation..."
        cd "$PROJECT_ROOT"
        $DOCKER_COMPOSE down -v
        docker system prune -f
        log_success "Clean installation completed"
    else
        log_info "Clean installation cancelled"
    fi
}

# Main script logic
main() {
    case "${1:-setup}" in
        "setup")
            check_prerequisites
            setup_weaviate
            validate_weaviate
            test_epic2_integration
            show_status
            log_success "Epic 2 Weaviate setup completed successfully!"
            log_info "Next steps:"
            echo "  1. Run: python epic2_comprehensive_integration_test.py"
            echo "  2. Or:  python epic2_diagnostic_test.py"
            echo "  3. See: docs/WEAVIATE_SETUP.md for more information"
            ;;
        "validate")
            check_prerequisites
            validate_weaviate
            ;;
        "test")
            check_prerequisites
            test_epic2_integration
            ;;
        "status")
            check_prerequisites
            show_status
            ;;
        "stop")
            check_prerequisites
            stop_services
            ;;
        "restart")
            check_prerequisites
            restart_services
            ;;
        "clean")
            check_prerequisites
            clean_installation
            ;;
        "help"|"-h"|"--help")
            show_usage
            ;;
        *)
            log_error "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
}

# Execute main function with all arguments
main "$@"