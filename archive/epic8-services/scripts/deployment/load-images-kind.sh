#!/bin/bash
# Epic 8 Kind Image Loading Script
# Loads all Epic 8 Docker images into Kind cluster

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
KIND_CLUSTER_NAME="epic8-testing"
IMAGES=(
    "epic8/api-gateway:latest"
    "epic8/query-analyzer:latest"
    "epic8/generator:latest"
    "epic8/retriever:latest"
    "epic8/cache:latest"
    "epic8/analytics:latest"
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

# Check if Kind cluster exists
check_cluster() {
    log_info "Checking Kind cluster: $KIND_CLUSTER_NAME"

    if ! kind get clusters | grep -q "^$KIND_CLUSTER_NAME$"; then
        log_error "Kind cluster '$KIND_CLUSTER_NAME' not found"
        log_info "Available clusters:"
        kind get clusters | sed 's/^/  - /'
        return 1
    fi

    log_success "Kind cluster '$KIND_CLUSTER_NAME' found"
}

# Check if images exist locally
check_images() {
    log_info "Checking if Docker images exist locally..."

    local missing_images=()

    for image in "${IMAGES[@]}"; do
        if docker images -q "$image" | grep -q .; then
            log_success "Image found: $image"
        else
            log_error "Image missing: $image"
            missing_images+=("$image")
        fi
    done

    if [ ${#missing_images[@]} -gt 0 ]; then
        log_error "Missing ${#missing_images[@]} images. Please build them first:"
        for image in "${missing_images[@]}"; do
            echo "  - $image"
        done
        log_info "Run: ./scripts/deployment/build-services.sh build"
        return 1
    fi

    log_success "All images found locally"
}

# Load single image into Kind
load_image() {
    local image="$1"

    log_info "Loading image: $image"

    if kind load docker-image "$image" --name "$KIND_CLUSTER_NAME"; then
        log_success "Loaded $image into Kind cluster"
        return 0
    else
        log_error "Failed to load $image into Kind cluster"
        return 1
    fi
}

# Load all images
load_all_images() {
    log_info "Loading all Epic 8 images into Kind cluster..."

    local failed_images=()
    local successful_images=()

    for image in "${IMAGES[@]}"; do
        echo ""
        log_info "=================================================="
        log_info "Loading: $image"
        log_info "=================================================="

        if load_image "$image"; then
            successful_images+=("$image")
        else
            failed_images+=("$image")
        fi
    done

    # Summary
    echo ""
    log_info "=================================================="
    log_info "IMAGE LOADING SUMMARY"
    log_info "=================================================="

    if [ ${#successful_images[@]} -gt 0 ]; then
        log_success "Successfully loaded ${#successful_images[@]} images:"
        for image in "${successful_images[@]}"; do
            echo "  ✓ $image"
        done
    fi

    if [ ${#failed_images[@]} -gt 0 ]; then
        log_error "Failed to load ${#failed_images[@]} images:"
        for image in "${failed_images[@]}"; do
            echo "  ✗ $image"
        done
        echo ""
        log_error "Image loading completed with errors"
        return 1
    else
        echo ""
        log_success "All images loaded successfully!"
        return 0
    fi
}

# Verify images in cluster
verify_images() {
    log_info "Verifying images are available in Kind cluster..."

    # Get cluster node name
    local node_name
    node_name=$(kubectl get nodes -o jsonpath='{.items[0].metadata.name}')

    if [ -z "$node_name" ]; then
        log_error "Could not find cluster node"
        return 1
    fi

    log_info "Checking images on node: $node_name"

    # Check images in cluster
    local missing_in_cluster=()

    for image in "${IMAGES[@]}"; do
        # Use docker exec to check if image exists in kind node
        if docker exec "$KIND_CLUSTER_NAME-control-plane" crictl images | grep -q "${image##*/}"; then
            log_success "Image available in cluster: $image"
        else
            log_warning "Image not found in cluster: $image"
            missing_in_cluster+=("$image")
        fi
    done

    if [ ${#missing_in_cluster[@]} -gt 0 ]; then
        log_warning "Some images may not be available in cluster"
        return 1
    else
        log_success "All images verified in cluster"
        return 0
    fi
}

# Show status
show_status() {
    log_info "Epic 8 Image Status in Kind Cluster:"
    echo ""

    printf "%-25s %-15s %-20s\n" "IMAGE" "LOCAL" "IN CLUSTER"
    echo "=============================================================="

    for image in "${IMAGES[@]}"; do
        # Check local
        if docker images -q "$image" | grep -q .; then
            local_status="✓ Built"
        else
            local_status="✗ Missing"
        fi

        # Check in cluster (simplified check)
        if docker exec "$KIND_CLUSTER_NAME-control-plane" crictl images 2>/dev/null | grep -q "${image##*/}" 2>/dev/null; then
            cluster_status="✓ Loaded"
        else
            cluster_status="✗ Not loaded"
        fi

        printf "%-25s %-15s %-20s\n" "${image#epic8/}" "$local_status" "$cluster_status"
    done
}

# Help function
show_help() {
    cat << EOF
Epic 8 Kind Image Loading Script

USAGE:
    $0 [COMMAND]

COMMANDS:
    load       Load all Epic 8 images into Kind cluster
    verify     Verify images are available in Kind cluster
    status     Show image status (local vs cluster)
    help       Show this help message

EXAMPLES:
    $0 load                # Load all images into Kind
    $0 verify              # Verify images in cluster
    $0 status              # Show image status

PREREQUISITES:
    - Kind cluster '$KIND_CLUSTER_NAME' must be running
    - All Epic 8 Docker images must be built locally
    - kubectl must be configured for the Kind cluster

NOTES:
    - Images are loaded from local Docker into Kind cluster
    - Use 'build-services.sh build' to build images first
    - Use 'kubectl get pods' to check if pods start after loading

EOF
}

# Main execution
main() {
    case "${1:-load}" in
        "load")
            if ! check_cluster; then
                exit 1
            fi

            if ! check_images; then
                exit 1
            fi

            if load_all_images; then
                log_success "All images loaded into Kind cluster"

                echo ""
                log_info "Next steps:"
                echo "  1. Restart failed pods: kubectl delete pods --all -n epic8-dev"
                echo "  2. Check pod status: kubectl get pods -n epic8-dev"
                echo "  3. Check logs: kubectl logs -f deployment/api-gateway -n epic8-dev"
            else
                log_error "Some images failed to load"
                exit 1
            fi
            ;;
        "verify")
            if ! check_cluster; then
                exit 1
            fi
            verify_images
            ;;
        "status")
            if ! check_cluster; then
                exit 1
            fi
            show_status
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