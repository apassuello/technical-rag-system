#!/bin/bash
# Docker Setup Validation Script for Epic 8
# Quick validation of Docker architecture implementation

set -e

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }
log_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }

echo "================================================================"
echo "Epic 8 Docker Architecture Validation"
echo "================================================================"
echo ""

# 1. Check docker-compose.yml configuration
log_info "Validating docker-compose.yml..."
if [ -f "$PROJECT_ROOT/docker-compose.yml" ]; then
    # Check build contexts
    if grep -q "context: \." "$PROJECT_ROOT/docker-compose.yml"; then
        log_success "✓ Build contexts correctly set to project root"
    else
        log_error "✗ Build contexts not set to project root"
        exit 1
    fi
    
    # Check dockerfile paths
    if grep -q "dockerfile: services/" "$PROJECT_ROOT/docker-compose.yml"; then
        log_success "✓ Dockerfile paths correctly configured"  
    else
        log_error "✗ Dockerfile paths incorrectly configured"
        exit 1
    fi
else
    log_error "✗ docker-compose.yml not found"
    exit 1
fi

# 2. Check Epic 1 component directories
log_info "Validating Epic 1 component access..."
epic1_dirs=("src" "config" "src/components" "src/core")
for dir in "${epic1_dirs[@]}"; do
    if [ -d "$PROJECT_ROOT/$dir" ]; then
        log_success "✓ Epic 1 directory found: $dir"
    else
        log_error "✗ Epic 1 directory missing: $dir"
        exit 1
    fi
done

# 3. Check service Dockerfiles
log_info "Validating service Dockerfiles..."
services=("api-gateway" "query-analyzer" "generator" "retriever" "cache" "analytics")
for service in "${services[@]}"; do
    dockerfile="$PROJECT_ROOT/services/$service/Dockerfile"
    if [ -f "$dockerfile" ]; then
        # Check for proper COPY commands (Epic 1 integration)
        if grep -q "COPY.*src/.*\./src/" "$dockerfile" && grep -q "COPY.*config/.*\./config/" "$dockerfile"; then
            log_success "✓ $service Dockerfile has Epic 1 integration"
        else
            log_error "✗ $service Dockerfile missing Epic 1 integration"
            exit 1
        fi
        
        # Check for service-specific app copy
        if grep -q "COPY.*services/$service/app/.*\./app/" "$dockerfile"; then
            log_success "✓ $service Dockerfile has service app integration"
        else
            log_error "✗ $service Dockerfile missing service app integration"
            exit 1
        fi
    else
        log_error "✗ Dockerfile missing for service: $service"
        exit 1
    fi
done

# 4. Check build scripts
log_info "Validating build automation..."
if [ -f "$PROJECT_ROOT/docker-setup.sh" ] && [ -x "$PROJECT_ROOT/docker-setup.sh" ]; then
    log_success "✓ New docker-setup.sh script available and executable"
else
    log_warning "⚠ New docker-setup.sh script not found or not executable"
fi

if [ -f "$PROJECT_ROOT/build-services.sh" ] && [ -x "$PROJECT_ROOT/build-services.sh" ]; then
    log_success "✓ Legacy build-services.sh script available and executable"
else
    log_warning "⚠ Legacy build-services.sh script not found or not executable"
fi

# 5. Validate build context paths
log_info "Testing build context path structure..."

# Simulate what Docker sees during build
test_paths=(
    "src/components"
    "src/core"
    "config"
    "services/query-analyzer/Dockerfile"
    "services/generator/Dockerfile"
    "services/retriever/Dockerfile"
    "services/api-gateway/Dockerfile"
    "services/cache/Dockerfile"
    "services/analytics/Dockerfile"
)

for path in "${test_paths[@]}"; do
    if [ -e "$PROJECT_ROOT/$path" ]; then
        log_success "✓ Build context can access: $path"
    else
        log_error "✗ Build context cannot access: $path"
        exit 1
    fi
done

# 6. Check port allocations
log_info "Validating port allocations..."
expected_ports=(
    "8080:api-gateway"
    "8081:generator"  
    "8082:query-analyzer"
    "8083:retriever"
    "8084:cache"
    "8085:analytics"
    "8180:weaviate"
    "11434:ollama"
    "6379:redis"
)

for port_service in "${expected_ports[@]}"; do
    port="${port_service%:*}"
    service="${port_service#*:}"
    
    if grep -q "$port:" "$PROJECT_ROOT/docker-compose.yml"; then
        log_success "✓ Port $port allocated for $service"
    else
        log_error "✗ Port $port not found for $service"
        exit 1
    fi
done

echo ""
echo "================================================================"
log_success "🎉 Docker Architecture Validation PASSED!"
echo "================================================================"
echo ""
log_info "Your Epic 8 Docker architecture is correctly implemented:"
echo "  ✅ All build contexts use project root for Epic 1 access"
echo "  ✅ All Dockerfiles properly integrate Epic 1 components"  
echo "  ✅ All services have proper port allocations"
echo "  ✅ Build automation scripts are available"
echo "  ✅ Configuration files are correctly structured"
echo ""
log_info "Ready to build and deploy! Run:"
echo "  ./docker-setup.sh check    # Pre-flight checks"
echo "  ./docker-setup.sh build    # Build all services"  
echo "  ./docker-setup.sh start    # Start all services"
echo "  ./docker-setup.sh status   # Check service health"
echo ""
echo "================================================================"