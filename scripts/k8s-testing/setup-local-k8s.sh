#!/bin/bash

# Local Kubernetes Testing Environment Setup
# Epic 8 Cloud-Native RAG Platform
#
# This script sets up a local Kubernetes testing environment using Kind or Minikube
# for comprehensive testing of Epic 8 microservices deployment.

set -euo pipefail

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
CLUSTER_NAME="epic8-testing"
KUBERNETES_VERSION="v1.28.0"
INGRESS_ENABLED="true"
MONITORING_ENABLED="true"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
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

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."

    local missing_tools=()

    if ! command_exists docker; then
        missing_tools+=("docker")
    fi

    if ! command_exists kubectl; then
        missing_tools+=("kubectl")
    fi

    if ! command_exists kind && ! command_exists minikube; then
        missing_tools+=("kind or minikube")
    fi

    if ! command_exists helm; then
        log_warning "Helm not found - Helm chart testing will be limited"
    fi

    if [ ${#missing_tools[@]} -ne 0 ]; then
        log_error "Missing required tools: ${missing_tools[*]}"
        log_info "Please install the missing tools and run again"
        log_info ""
        log_info "Installation instructions:"
        log_info "- Docker: https://docs.docker.com/get-docker/"
        log_info "- kubectl: https://kubernetes.io/docs/tasks/tools/"
        log_info "- Kind: https://kind.sigs.k8s.io/docs/user/quick-start/"
        log_info "- Minikube: https://minikube.sigs.k8s.io/docs/start/"
        log_info "- Helm: https://helm.sh/docs/intro/install/"
        exit 1
    fi

    log_success "All prerequisites satisfied"
}

# Detect preferred K8s tool
detect_k8s_tool() {
    if command_exists kind; then
        echo "kind"
    elif command_exists minikube; then
        echo "minikube"
    else
        log_error "Neither Kind nor Minikube found"
        exit 1
    fi
}

# Setup Kind cluster
setup_kind_cluster() {
    log_info "Setting up Kind cluster: ${CLUSTER_NAME}"

    # Create Kind configuration
    cat > "${SCRIPT_DIR}/kind-config.yaml" << EOF
kind: Cluster
apiVersion: kind.x-k8s.io/v1alpha4
name: ${CLUSTER_NAME}
nodes:
- role: control-plane
  kubeadmConfigPatches:
  - |
    kind: InitConfiguration
    nodeRegistration:
      kubeletExtraArgs:
        node-labels: "ingress-ready=true"
  extraPortMappings:
  # API Gateway
  - containerPort: 8080
    hostPort: 8080
    protocol: TCP
  # Query Analyzer
  - containerPort: 8082
    hostPort: 8082
    protocol: TCP
  # Generator
  - containerPort: 8081
    hostPort: 8081
    protocol: TCP
  # Retriever
  - containerPort: 8083
    hostPort: 8083
    protocol: TCP
  # Cache
  - containerPort: 8084
    hostPort: 8084
    protocol: TCP
  # Analytics
  - containerPort: 8085
    hostPort: 8085
    protocol: TCP
  # Ingress Controller
  - containerPort: 80
    hostPort: 80
    protocol: TCP
  - containerPort: 443
    hostPort: 443
    protocol: TCP
- role: worker
  labels:
    node-role: epic8-worker
- role: worker
  labels:
    node-role: epic8-worker
EOF

    # Check if cluster already exists
    if kind get clusters | grep -q "^${CLUSTER_NAME}$"; then
        log_warning "Kind cluster ${CLUSTER_NAME} already exists"
        read -p "Do you want to recreate it? (y/n): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            log_info "Deleting existing cluster..."
            kind delete cluster --name "${CLUSTER_NAME}"
        else
            log_info "Using existing cluster"
            return 0
        fi
    fi

    # Create cluster
    log_info "Creating Kind cluster with Kubernetes ${KUBERNETES_VERSION}..."
    kind create cluster --config="${SCRIPT_DIR}/kind-config.yaml" --image="kindest/node:${KUBERNETES_VERSION}"

    # Wait for cluster to be ready
    log_info "Waiting for cluster to be ready..."
    kubectl wait --for=condition=Ready nodes --all --timeout=300s

    log_success "Kind cluster ${CLUSTER_NAME} created successfully"
}

# Setup Minikube cluster
setup_minikube_cluster() {
    log_info "Setting up Minikube cluster: ${CLUSTER_NAME}"

    # Check if cluster already exists
    if minikube profile list | grep -q "${CLUSTER_NAME}"; then
        log_warning "Minikube cluster ${CLUSTER_NAME} already exists"
        read -p "Do you want to recreate it? (y/n): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            log_info "Deleting existing cluster..."
            minikube delete --profile "${CLUSTER_NAME}"
        else
            log_info "Using existing cluster"
            minikube profile "${CLUSTER_NAME}"
            return 0
        fi
    fi

    # Create cluster
    log_info "Creating Minikube cluster with Kubernetes ${KUBERNETES_VERSION}..."
    minikube start \
        --profile="${CLUSTER_NAME}" \
        --kubernetes-version="${KUBERNETES_VERSION}" \
        --nodes=3 \
        --cpus=4 \
        --memory=8192 \
        --disk-size=20g \
        --driver=docker

    # Set context
    minikube profile "${CLUSTER_NAME}"

    # Wait for cluster to be ready
    log_info "Waiting for cluster to be ready..."
    kubectl wait --for=condition=Ready nodes --all --timeout=300s

    log_success "Minikube cluster ${CLUSTER_NAME} created successfully"
}

# Setup ingress controller
setup_ingress_controller() {
    local k8s_tool="$1"

    if [ "${INGRESS_ENABLED}" != "true" ]; then
        log_info "Ingress controller setup skipped"
        return 0
    fi

    log_info "Setting up ingress controller..."

    if [ "${k8s_tool}" = "kind" ]; then
        # Install NGINX Ingress Controller for Kind
        kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/kind/deploy.yaml

        # Wait for ingress controller to be ready
        log_info "Waiting for ingress controller to be ready..."
        kubectl wait --namespace ingress-nginx \
            --for=condition=ready pod \
            --selector=app.kubernetes.io/component=controller \
            --timeout=300s

    elif [ "${k8s_tool}" = "minikube" ]; then
        # Enable ingress addon for Minikube
        minikube addons enable ingress --profile="${CLUSTER_NAME}"

        # Wait for ingress controller to be ready
        log_info "Waiting for ingress controller to be ready..."
        kubectl wait --namespace ingress-nginx \
            --for=condition=ready pod \
            --selector=app.kubernetes.io/name=ingress-nginx \
            --timeout=300s
    fi

    log_success "Ingress controller setup complete"
}

# Setup monitoring stack (optional)
setup_monitoring() {
    if [ "${MONITORING_ENABLED}" != "true" ]; then
        log_info "Monitoring setup skipped"
        return 0
    fi

    log_info "Setting up monitoring stack..."

    # Create monitoring namespace
    kubectl create namespace monitoring --dry-run=client -o yaml | kubectl apply -f -

    # Add Prometheus Helm repository
    if command_exists helm; then
        helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
        helm repo update

        # Install Prometheus stack
        log_info "Installing Prometheus stack..."
        helm upgrade --install monitoring prometheus-community/kube-prometheus-stack \
            --namespace monitoring \
            --set prometheus.prometheusSpec.serviceMonitorSelectorNilUsesHelmValues=false \
            --set prometheus.prometheusSpec.podMonitorSelectorNilUsesHelmValues=false \
            --set grafana.adminPassword=admin123 \
            --timeout=600s

        log_success "Monitoring stack installed"
        log_info "Grafana admin password: admin123"
        log_info "To access Grafana: kubectl port-forward -n monitoring svc/monitoring-grafana 3000:80"
    else
        log_warning "Helm not found - monitoring stack installation skipped"
    fi
}

# Create Epic 8 namespace and setup
setup_epic8_namespace() {
    log_info "Setting up Epic 8 namespace..."

    # Create namespace
    kubectl create namespace epic8 --dry-run=client -o yaml | kubectl apply -f -

    # Label namespace
    kubectl label namespace epic8 app.kubernetes.io/part-of=epic8-rag-platform --overwrite

    # Create service account
    cat << EOF | kubectl apply -f -
apiVersion: v1
kind: ServiceAccount
metadata:
  name: epic8-service-account
  namespace: epic8
  labels:
    app.kubernetes.io/part-of: epic8-rag-platform
---
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  namespace: epic8
  name: epic8-role
rules:
- apiGroups: [""]
  resources: ["pods", "services", "configmaps", "secrets"]
  verbs: ["get", "list", "watch", "create", "update", "patch", "delete"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: epic8-role-binding
  namespace: epic8
subjects:
- kind: ServiceAccount
  name: epic8-service-account
  namespace: epic8
roleRef:
  kind: Role
  name: epic8-role
  apiGroup: rbac.authorization.k8s.io
EOF

    log_success "Epic 8 namespace setup complete"
}

# Create validation scripts
create_validation_scripts() {
    log_info "Creating validation scripts..."

    # Create validation script directory
    mkdir -p "${SCRIPT_DIR}/validation"

    # Create cluster health check script
    cat > "${SCRIPT_DIR}/validation/check-cluster-health.sh" << 'EOF'
#!/bin/bash

# Cluster Health Check Script
set -euo pipefail

echo "=== Kubernetes Cluster Health Check ==="

# Check cluster info
echo "Cluster info:"
kubectl cluster-info

echo -e "\nNode status:"
kubectl get nodes -o wide

echo -e "\nNamespace status:"
kubectl get namespaces

echo -e "\nSystem pods status:"
kubectl get pods -n kube-system

echo -e "\nIngress controller status:"
kubectl get pods -n ingress-nginx 2>/dev/null || echo "Ingress controller not found"

echo -e "\nMonitoring status:"
kubectl get pods -n monitoring 2>/dev/null || echo "Monitoring not found"

echo -e "\nEpic 8 namespace status:"
kubectl get all -n epic8 2>/dev/null || echo "Epic 8 namespace empty"

echo -e "\n=== Health Check Complete ==="
EOF

    # Create Epic 8 deployment test script
    cat > "${SCRIPT_DIR}/validation/test-epic8-deployment.sh" << 'EOF'
#!/bin/bash

# Epic 8 Deployment Test Script
set -euo pipefail

NAMESPACE="epic8"

echo "=== Epic 8 Deployment Test ==="

# Check if namespace exists
if ! kubectl get namespace "${NAMESPACE}" >/dev/null 2>&1; then
    echo "Error: Namespace ${NAMESPACE} does not exist"
    exit 1
fi

echo "Testing deployments in namespace: ${NAMESPACE}"

# Check deployments
echo -e "\nDeployments:"
kubectl get deployments -n "${NAMESPACE}"

# Check services
echo -e "\nServices:"
kubectl get services -n "${NAMESPACE}"

# Check pods
echo -e "\nPods:"
kubectl get pods -n "${NAMESPACE}"

# Check ingress
echo -e "\nIngress:"
kubectl get ingress -n "${NAMESPACE}" 2>/dev/null || echo "No ingress found"

# Test service connectivity
echo -e "\nTesting service connectivity..."

services=$(kubectl get services -n "${NAMESPACE}" -o jsonpath='{.items[*].metadata.name}')
for service in $services; do
    if [ "$service" != "kubernetes" ]; then
        echo "Testing service: $service"
        kubectl run test-pod-$service --image=curlimages/curl --rm -i --restart=Never -n "${NAMESPACE}" -- \
            curl -s -o /dev/null -w "%{http_code}" "http://$service" || echo "Connection test failed for $service"
    fi
done

echo -e "\n=== Deployment Test Complete ==="
EOF

    # Create port forwarding script
    cat > "${SCRIPT_DIR}/validation/port-forward-services.sh" << 'EOF'
#!/bin/bash

# Port Forwarding Script for Epic 8 Services
set -euo pipefail

NAMESPACE="epic8"

echo "=== Epic 8 Services Port Forwarding ==="

# Function to start port forwarding in background
start_port_forward() {
    local service=$1
    local local_port=$2
    local remote_port=$3

    echo "Starting port forward for $service: localhost:$local_port -> $service:$remote_port"
    kubectl port-forward -n "${NAMESPACE}" "svc/$service" "$local_port:$remote_port" &
    local pid=$!
    echo "$pid" > "/tmp/pf-$service.pid"
}

# Function to stop all port forwards
stop_port_forwards() {
    echo "Stopping all port forwards..."
    for pidfile in /tmp/pf-*.pid; do
        if [ -f "$pidfile" ]; then
            local pid=$(cat "$pidfile")
            kill "$pid" 2>/dev/null || true
            rm "$pidfile"
        fi
    done
}

# Trap to cleanup on exit
trap stop_port_forwards EXIT

# Check if services exist and start port forwarding
services_config=(
    "epic8-api-gateway 8080 8080"
    "epic8-query-analyzer 8082 8082"
    "epic8-generator 8081 8081"
    "epic8-retriever 8083 8083"
    "epic8-cache 8084 8084"
    "epic8-analytics 8085 8085"
)

for config in "${services_config[@]}"; do
    read -r service local_port remote_port <<< "$config"

    if kubectl get service "$service" -n "${NAMESPACE}" >/dev/null 2>&1; then
        start_port_forward "$service" "$local_port" "$remote_port"
    else
        echo "Service $service not found, skipping..."
    fi
done

echo -e "\nPort forwarding started. Access services at:"
echo "- API Gateway: http://localhost:8080"
echo "- Query Analyzer: http://localhost:8082"
echo "- Generator: http://localhost:8081"
echo "- Retriever: http://localhost:8083"
echo "- Cache: http://localhost:8084"
echo "- Analytics: http://localhost:8085"

echo -e "\nPress Ctrl+C to stop all port forwards..."
wait
EOF

    # Make scripts executable
    chmod +x "${SCRIPT_DIR}/validation/"*.sh

    log_success "Validation scripts created"
}

# Main setup function
main() {
    local k8s_tool
    local action="${1:-setup}"

    case "$action" in
        setup)
            log_info "Starting Epic 8 local Kubernetes testing environment setup..."

            check_prerequisites
            k8s_tool=$(detect_k8s_tool)

            log_info "Using Kubernetes tool: ${k8s_tool}"

            if [ "${k8s_tool}" = "kind" ]; then
                setup_kind_cluster
            elif [ "${k8s_tool}" = "minikube" ]; then
                setup_minikube_cluster
            fi

            setup_ingress_controller "${k8s_tool}"
            setup_monitoring
            setup_epic8_namespace
            create_validation_scripts

            log_success "Epic 8 local Kubernetes testing environment setup complete!"
            log_info ""
            log_info "Next steps:"
            log_info "1. Test cluster health: ${SCRIPT_DIR}/validation/check-cluster-health.sh"
            log_info "2. Deploy Epic 8 services: kubectl apply -f k8s/manifests/"
            log_info "3. Test deployments: ${SCRIPT_DIR}/validation/test-epic8-deployment.sh"
            log_info "4. Access services: ${SCRIPT_DIR}/validation/port-forward-services.sh"
            ;;

        cleanup)
            log_info "Cleaning up Epic 8 testing environment..."

            k8s_tool=$(detect_k8s_tool)

            if [ "${k8s_tool}" = "kind" ]; then
                if kind get clusters | grep -q "^${CLUSTER_NAME}$"; then
                    kind delete cluster --name "${CLUSTER_NAME}"
                    log_success "Kind cluster ${CLUSTER_NAME} deleted"
                else
                    log_warning "Kind cluster ${CLUSTER_NAME} not found"
                fi
            elif [ "${k8s_tool}" = "minikube" ]; then
                if minikube profile list | grep -q "${CLUSTER_NAME}"; then
                    minikube delete --profile "${CLUSTER_NAME}"
                    log_success "Minikube cluster ${CLUSTER_NAME} deleted"
                else
                    log_warning "Minikube cluster ${CLUSTER_NAME} not found"
                fi
            fi

            # Clean up configuration files
            rm -f "${SCRIPT_DIR}/kind-config.yaml"
            rm -rf "${SCRIPT_DIR}/validation"

            log_success "Cleanup complete"
            ;;

        status)
            log_info "Checking Epic 8 testing environment status..."

            k8s_tool=$(detect_k8s_tool)

            if [ "${k8s_tool}" = "kind" ]; then
                if kind get clusters | grep -q "^${CLUSTER_NAME}$"; then
                    log_success "Kind cluster ${CLUSTER_NAME} is running"
                    kubectl cluster-info --context "kind-${CLUSTER_NAME}"
                else
                    log_warning "Kind cluster ${CLUSTER_NAME} not found"
                fi
            elif [ "${k8s_tool}" = "minikube" ]; then
                minikube status --profile "${CLUSTER_NAME}" || log_warning "Minikube cluster ${CLUSTER_NAME} not running"
            fi
            ;;

        *)
            echo "Usage: $0 {setup|cleanup|status}"
            echo ""
            echo "Commands:"
            echo "  setup   - Create and configure local Kubernetes testing environment"
            echo "  cleanup - Delete the testing environment and clean up"
            echo "  status  - Check the status of the testing environment"
            exit 1
            ;;
    esac
}

# Run main function with all arguments
main "$@"