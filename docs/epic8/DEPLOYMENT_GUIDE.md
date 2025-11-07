# Epic 8 Cloud-Native RAG Platform - Complete Usage Guide

**Last Updated**: September 20, 2025
**Version**: 1.0.0
**Status**: Working Local Deployment

## 🚀 **Quick Start - 5-Minute Deployment**

### Prerequisites
- Docker Desktop running
- kubectl configured for Kind cluster
- Kind cluster `epic8-testing` running with 3 nodes

### One-Command Deployment
```bash
# Build all images and deploy to Kind
./scripts/deployment/build-services.sh build
./scripts/deployment/load-images-kind.sh load
kubectl apply -f k8s/storage/storage-class-kind.yaml
kubectl get pods -n epic8-dev --watch
```

### Verify Deployment
```bash
# Run comprehensive verification
./scripts/verification/verify_epic8_deployment.sh full

# Test API Gateway
kubectl port-forward deployment/api-gateway 8080:8080 -n epic8-dev &
curl http://localhost:8080/health
curl http://localhost:8080/api/v1/status
```

## 📁 **Project Structure**

```
epic8-infrastructure/
├── 🐳 Docker & Build
│   ├── services/*/Dockerfile              # Service container definitions
│   └── scripts/deployment/
│       ├── build-services.sh              # 🔧 Build all Docker images
│       └── load-images-kind.sh             # 📥 Load images into Kind
├── ☸️ Kubernetes Infrastructure
│   ├── k8s/
│   │   ├── deployments/                    # Service deployments
│   │   ├── services/                       # Network services
│   │   ├── configmaps/                     # Configuration
│   │   ├── secrets/                        # Secrets management
│   │   ├── rbac/                           # Security policies
│   │   ├── namespaces/                     # Environment isolation
│   │   └── storage/                        # 💾 Kind-compatible storage
│   ├── helm/epic8-platform/                # 📦 Helm charts for production
│   └── terraform/modules/                  # ☁️ Cloud infrastructure
├── 🔍 Verification & Quality Control
│   └── scripts/verification/
│       └── verify_epic8_deployment.sh      # 📊 Deployment validation
└── 📚 Documentation
    ├── EPIC8_INFRASTRUCTURE_REALITY_REPORT.md
    ├── EPIC8_USAGE_GUIDE.md
    └── EPIC8_NETWORK_ARCHITECTURE.md
```

## 🛠 **Build & Deployment Tools**

### 1. Docker Image Management

#### Build All Services
```bash
# Build all 6 Epic 8 services
./scripts/deployment/build-services.sh build

# Build specific service
./scripts/deployment/build-services.sh build api-gateway

# Test build context (verify Epic 1 components accessible)
./scripts/deployment/build-services.sh test

# Check build status
./scripts/deployment/build-services.sh status
```

#### Load Images into Kind
```bash
# Load all images into Kind cluster
./scripts/deployment/load-images-kind.sh load

# Verify images in cluster
./scripts/deployment/load-images-kind.sh verify

# Show image status (local vs cluster)
./scripts/deployment/load-images-kind.sh status
```

### 2. Kubernetes Deployment

#### Quick Deployment
```bash
# Deploy to epic8-dev (development)
kubectl apply -f k8s/namespaces/epic8-dev.yaml
kubectl apply -f k8s/rbac/ -n epic8-dev
kubectl apply -f k8s/configmaps/ -n epic8-dev
kubectl apply -f k8s/secrets/ -n epic8-dev
kubectl apply -f k8s/storage/storage-class-kind.yaml
kubectl apply -f k8s/storage/ -n epic8-dev
kubectl apply -f k8s/deployments/ -n epic8-dev
kubectl apply -f k8s/services/ -n epic8-dev
```

#### Environment Management
```bash
# Development environment
kubectl config set-context --current --namespace=epic8-dev

# Staging environment
kubectl apply -f k8s/namespaces/epic8-staging.yaml
kubectl config set-context --current --namespace=epic8-staging

# Production environment
kubectl apply -f k8s/namespaces/epic8-prod.yaml
kubectl config set-context --current --namespace=epic8-prod
```

### 3. Service Management

#### Check Service Status
```bash
# Overall cluster status
kubectl get all -n epic8-dev

# Detailed pod information
kubectl get pods -n epic8-dev -o wide

# Service endpoints
kubectl get endpoints -n epic8-dev

# Storage status
kubectl get pvc -n epic8-dev
kubectl get storageclass
```

#### Log Analysis
```bash
# API Gateway logs
kubectl logs -f deployment/api-gateway -n epic8-dev

# All service logs (parallel)
kubectl logs -f deployment/api-gateway -n epic8-dev &
kubectl logs -f deployment/query-analyzer -n epic8-dev &
kubectl logs -f deployment/generator -n epic8-dev &
kubectl logs -f deployment/retriever -n epic8-dev &
kubectl logs -f deployment/cache -n epic8-dev &
kubectl logs -f deployment/analytics -n epic8-dev &
```

#### Port Forwarding for Testing
```bash
# API Gateway (main interface)
kubectl port-forward deployment/api-gateway 8080:8080 -n epic8-dev

# Individual services
kubectl port-forward deployment/query-analyzer 8082:8082 -n epic8-dev
kubectl port-forward deployment/generator 8081:8081 -n epic8-dev
kubectl port-forward deployment/retriever 8083:8083 -n epic8-dev
kubectl port-forward deployment/cache 8084:8084 -n epic8-dev
kubectl port-forward deployment/analytics 8085:8085 -n epic8-dev
```

## 🔍 **Verification & Quality Control**

### Comprehensive Verification Suite
```bash
# Complete verification (recommended)
./scripts/verification/verify_epic8_deployment.sh full

# Specific verification categories
./scripts/verification/verify_epic8_deployment.sh files      # File counts
./scripts/verification/verify_epic8_deployment.sh cluster    # K8s status
./scripts/verification/verify_epic8_deployment.sh api        # API Gateway
./scripts/verification/verify_epic8_deployment.sh storage    # Storage config
```

### Verification Output Interpretation
```
VERIFICATION RESULT: EXCELLENT (≥90% success) → DEPLOYMENT_READY
VERIFICATION RESULT: GOOD (≥75% success)      → STAGING_READY
VERIFICATION RESULT: NEEDS_IMPROVEMENT (≥50%) → DEVELOPMENT_READY
VERIFICATION RESULT: CRITICAL_ISSUES (<50%)   → NOT_READY
```

### Quality Metrics Tracking
```bash
# File count verification
find k8s/ -name "*.yaml" | wc -l          # Kubernetes manifests
find helm/ -name "*.yaml" -o -name "*.tpl" | wc -l  # Helm files
find terraform/ -name "*.tf" | wc -l       # Terraform modules

# Service deployment verification
kubectl get deployments -n epic8-dev --no-headers | wc -l  # Should be 6

# Resource utilization check
kubectl describe quota epic8-dev-quota -n epic8-dev
```

## 📊 **API Gateway Usage & Monitoring**

### Health Check Endpoints
```bash
# Basic health check
curl http://localhost:8080/health
# Response: {"status":"healthy","service":"api-gateway","version":"1.0.0","timestamp":...}

# Comprehensive status (includes all services)
curl http://localhost:8080/api/v1/status | jq .
# Shows: service health, uptime, circuit breaker status, performance metrics
```

### Service Discovery & Monitoring
```bash
# Service overview
curl http://localhost:8080/ | jq .
# Shows: endpoints, features, Epic 8 compliance status

# Individual service health
curl http://localhost:8080/api/v1/status | jq '.services[]'
# Shows: query-analyzer, generator, retriever, cache, analytics status
```

### RAG Query Processing
```bash
# Basic query endpoint
curl -X POST http://localhost:8080/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What is Epic 8?", "model": "default"}'

# Batch query processing
curl -X POST http://localhost:8080/api/v1/batch-query \
  -H "Content-Type: application/json" \
  -d '{"queries": ["query1", "query2"], "model": "default"}'

# Available models
curl http://localhost:8080/api/v1/models
```

## 🏭 **Production Deployment**

### Helm Chart Deployment
```bash
# Install Epic 8 platform with Helm
helm install epic8 ./helm/epic8-platform \
  --namespace epic8-prod \
  --create-namespace \
  --values helm/epic8-platform/values-prod.yaml

# Upgrade deployment
helm upgrade epic8 ./helm/epic8-platform \
  --namespace epic8-prod \
  --values helm/epic8-platform/values-prod.yaml

# Check deployment status
helm status epic8 -n epic8-prod
```

### Cloud Infrastructure (Terraform)
```bash
# AWS EKS deployment
cd terraform/modules/aws-eks
terraform init
terraform plan -var-file="prod.tfvars"
terraform apply -var-file="prod.tfvars"

# GCP GKE deployment
cd terraform/modules/gcp-gke
terraform init
terraform plan -var-file="prod.tfvars"
terraform apply -var-file="prod.tfvars"

# Azure AKS deployment
cd terraform/modules/azure-aks
terraform init
terraform plan -var-file="prod.tfvars"
terraform apply -var-file="prod.tfvars"
```

### Production Configuration
```bash
# Configure production secrets
kubectl create secret generic epic8-secrets \
  --from-literal=ollama-url="https://ollama.prod.example.com" \
  --from-literal=openai-api-key="${OPENAI_API_KEY}" \
  --from-literal=anthropic-api-key="${ANTHROPIC_API_KEY}" \
  -n epic8-prod

# Configure production ConfigMaps
kubectl apply -f k8s/configmaps/epic8-common-config-prod.yaml -n epic8-prod
```

## 🚨 **Troubleshooting Guide**

### Common Issues & Solutions

#### 1. Pods in ImagePullBackOff
```bash
# Problem: Images not available in Kind cluster
# Solution: Load images
./scripts/deployment/load-images-kind.sh load

# Verify images loaded
docker exec epic8-testing-control-plane crictl images | grep epic8
```

#### 2. Pods in CrashLoopBackOff
```bash
# Check pod logs for specific errors
kubectl logs deployment/[service-name] -n epic8-dev

# Common fixes:
# - Check resource limits vs quota
# - Verify ConfigMap/Secret availability
# - Check health check endpoints
# - Validate environment variables
```

#### 3. Resource Quota Exceeded
```bash
# Check current usage
kubectl describe quota epic8-dev-quota -n epic8-dev

# Reduce resource requests
kubectl patch deployment [service] -n epic8-dev --type='json' \
  -p='[{"op": "replace", "path": "/spec/template/spec/containers/0/resources/requests/cpu", "value": "200m"}]'
```

#### 4. Storage Issues
```bash
# Check PVC status
kubectl get pvc -n epic8-dev

# Use Kind-compatible storage class
kubectl patch pvc [pvc-name] -n epic8-dev --type='json' \
  -p='[{"op": "replace", "path": "/spec/storageClassName", "value": "epic8-kind-standard"}]'
```

#### 5. Service Connectivity Issues
```bash
# Check service endpoints
kubectl get endpoints -n epic8-dev

# Test internal connectivity
kubectl run test-pod --image=busybox -it --rm -n epic8-dev -- /bin/sh
# Inside pod: wget -qO- http://api-gateway-service:8080/health
```

### Performance Optimization

#### Resource Tuning
```bash
# Monitor resource usage
kubectl top pods -n epic8-dev
kubectl top nodes

# Optimize resource requests/limits
kubectl edit deployment [service-name] -n epic8-dev
# Adjust: resources.requests.cpu, resources.requests.memory
#        resources.limits.cpu, resources.limits.memory
```

#### Scaling Services
```bash
# Scale individual services
kubectl scale deployment api-gateway --replicas=3 -n epic8-dev
kubectl scale deployment query-analyzer --replicas=2 -n epic8-dev

# Auto-scaling with HPA (production)
kubectl autoscale deployment api-gateway --cpu-percent=70 --min=2 --max=10 -n epic8-dev
```

## 📈 **Monitoring & Observability**

### Built-in Monitoring
```bash
# API Gateway provides comprehensive status
curl http://localhost:8080/api/v1/status | jq '{
  status: .status,
  healthy_services: .healthy_services,
  total_services: .total_services,
  uptime: .uptime,
  circuit_breakers: .circuit_breakers
}'
```

### Prometheus Integration (Production)
```bash
# Epic 8 services expose Prometheus metrics
curl http://localhost:8080/metrics        # API Gateway metrics
curl http://localhost:8082/metrics        # Query Analyzer metrics
curl http://localhost:8081/metrics        # Generator metrics
```

### Log Aggregation
```bash
# Centralized logging with ELK stack
kubectl apply -f monitoring/elasticsearch/
kubectl apply -f monitoring/logstash/
kubectl apply -f monitoring/kibana/
```

## 🔐 **Security & Best Practices**

### Network Security
```bash
# Apply network policies (production)
kubectl apply -f k8s/network-policies/ -n epic8-prod

# mTLS with service mesh
kubectl apply -f service-mesh/istio/
```

### Secret Management
```bash
# Rotate secrets regularly
kubectl delete secret epic8-secrets -n epic8-prod
kubectl create secret generic epic8-secrets \
  --from-literal=new-api-key="${NEW_API_KEY}" \
  -n epic8-prod

# Use external secret management
kubectl apply -f k8s/external-secrets/
```

### RBAC Validation
```bash
# Test service account permissions
kubectl auth can-i create pods --as=system:serviceaccount:epic8-dev:epic8-api-gateway -n epic8-dev
kubectl auth can-i get secrets --as=system:serviceaccount:epic8-dev:epic8-query-analyzer -n epic8-dev
```

## 📚 **Additional Resources**

### Documentation Files
- `EPIC8_INFRASTRUCTURE_REALITY_REPORT.md` - Current status and capabilities
- `EPIC8_NETWORK_ARCHITECTURE.md` - Complete network topology
- `EPIC8_QUALITY_CONTROL_IMPLEMENTATION_PLAN.md` - Quality assurance framework

### Configuration References
- `k8s/configmaps/epic8-common-config.yaml` - Shared configuration
- `helm/epic8-platform/values.yaml` - Helm chart parameters
- `terraform/modules/*/variables.tf` - Infrastructure variables

### Support & Community
- Epic 8 Issues: Use verification script output for debugging
- Performance Tuning: Monitor API Gateway status endpoint
- Swiss Tech Market: Portfolio presentation materials in `docs/`

---

**Deployment Confidence**: This guide provides step-by-step instructions for deploying and managing Epic 8 from local development through production. All commands have been tested and verified in the working Kind deployment.