# Epic 8 Cloud-Native Multi-Model RAG Platform - Kubernetes Manifests

## Overview

This directory contains comprehensive Kubernetes manifests for deploying the Epic 8 Cloud-Native Multi-Model RAG Platform following enterprise best practices and Swiss engineering standards. The platform targets 99.9% uptime SLA with production-ready security, scalability, and operational excellence.

## Architecture

### 6-Service Microservices Architecture

1. **API Gateway** (2 replicas) - Entry point with external load balancer
2. **Query Analyzer** (2 replicas) - ML-based query complexity analysis
3. **Generator** (3 replicas) - Multi-model answer generation with Epic 1 integration
4. **Retriever** (2 replicas) - Epic 2 ModularUnifiedRetriever integration
5. **Cache** (1 replica) - Redis-backed caching layer
6. **Analytics** (1 replica) - Performance monitoring and cost tracking

### Resource Specifications

| Service | CPU Request | Memory Request | CPU Limit | Memory Limit | Replicas |
|---------|-------------|----------------|-----------|--------------|----------|
| API Gateway | 500m | 1Gi | 1 | 2Gi | 2 |
| Query Analyzer | 750m | 1.5Gi | 1.5 | 3Gi | 2 |
| Generator | 1 | 2Gi | 2 | 4Gi | 3 |
| Retriever | 500m | 1Gi | 1 | 2Gi | 2 |
| Cache | 250m | 512Mi | 500m | 1Gi | 1 |
| Analytics | 250m | 512Mi | 500m | 1Gi | 1 |

## Directory Structure

```
k8s/
├── namespaces/              # Multi-environment namespace configuration
│   ├── epic8-dev.yaml      # Development environment with resource quotas
│   ├── epic8-staging.yaml  # Staging environment (production-like)
│   └── epic8-prod.yaml     # Production environment with strict limits
├── deployments/             # Service deployment manifests
│   ├── api-gateway-deployment.yaml     # External-facing gateway
│   ├── query-analyzer-deployment.yaml  # ML-based query analysis
│   ├── generator-deployment.yaml       # Multi-model generation
│   ├── retriever-deployment.yaml       # Document retrieval service
│   ├── cache-deployment.yaml           # Redis caching layer
│   └── analytics-deployment.yaml       # Performance & cost tracking
├── services/                # Service discovery and communication
│   ├── api-gateway-service.yaml        # External + internal services
│   ├── query-analyzer-service.yaml     # Internal ClusterIP
│   ├── generator-service.yaml          # Internal ClusterIP
│   ├── retriever-service.yaml          # Internal ClusterIP
│   ├── cache-service.yaml              # Internal ClusterIP with session affinity
│   └── analytics-service.yaml          # Internal ClusterIP
├── configmaps/              # Configuration management
│   ├── epic8-common-config.yaml        # Shared platform configuration
│   └── service-configs.yaml            # Service-specific configurations
├── secrets/                 # Secret management
│   └── epic8-secrets.yaml              # Common secrets, LLM API keys, monitoring
├── rbac/                    # Role-based access control
│   ├── service-accounts.yaml           # Service accounts for all services
│   ├── roles.yaml                      # Roles with least-privilege access
│   └── rolebindings.yaml               # Role bindings and cluster access
├── storage/                 # Persistent storage configuration
│   ├── storage-class.yaml              # Multi-tier storage classes
│   └── persistent-volumes.yaml         # PVCs for logs, cache, models, data
├── network-policies/        # Network security segmentation
│   └── epic8-network-policies.yaml     # Comprehensive network isolation
└── tests/                   # Existing test infrastructure (preserved)
    └── [existing test files]
```

## Enterprise Features

### Security Implementation

- **Pod Security Standards**: Restricted security contexts, non-root users
- **Network Policies**: Default deny-all with selective service communication
- **RBAC**: Least-privilege access with service-specific roles
- **Secret Management**: Encrypted secrets with rotation capability
- **TLS**: mTLS ready with service mesh integration
- **Container Security**: Read-only filesystems, dropped capabilities

### High Availability & Resilience

- **Pod Disruption Budgets**: Ensure minimum availability during updates
- **Anti-Affinity Rules**: Spread replicas across nodes
- **Rolling Updates**: Zero-downtime deployments with surge control
- **Health Checks**: Comprehensive liveness, readiness, and startup probes
- **Resource Management**: Proper requests/limits for optimal scheduling
- **Multi-Zone Deployment**: Topology spread constraints

### Observability & Monitoring

- **Prometheus Integration**: Metrics endpoints on all services
- **Grafana Ready**: Dashboard-ready with persistent storage
- **Structured Logging**: JSON format with centralized collection
- **Distributed Tracing**: Jaeger-ready with correlation IDs
- **Custom Metrics**: Business metrics for cost and performance tracking

### Storage Architecture

- **Multi-Tier Storage**: Fast SSD for models/cache, standard for logs
- **Persistent Volumes**: Dedicated storage for each service component
- **Shared Document Data**: ReadWriteMany for document sharing
- **Multi-Cloud Support**: Storage classes for AWS, GCP, Azure
- **Backup Ready**: Retain policy for critical data

## Deployment Instructions

### Prerequisites

- Kubernetes cluster 1.28+
- Storage provisioner (AWS EBS, GCP PD, Azure Disk)
- Ingress controller (for external access)
- Prometheus operator (optional, for enhanced monitoring)

### Quick Deployment

```bash
# 1. Create namespace and base resources
kubectl apply -f namespaces/epic8-prod.yaml
kubectl apply -f storage/storage-class.yaml
kubectl apply -f storage/persistent-volumes.yaml

# 2. Apply RBAC and security
kubectl apply -f rbac/ -n epic8-prod

# 3. Apply configuration and secrets
kubectl apply -f configmaps/ -n epic8-prod
kubectl apply -f secrets/ -n epic8-prod

# 4. Deploy services
kubectl apply -f deployments/ -n epic8-prod
kubectl apply -f services/ -n epic8-prod

# 5. Apply network policies
kubectl apply -f network-policies/ -n epic8-prod

# 6. Verify deployment
kubectl get pods -n epic8-prod
kubectl get services -n epic8-prod
```

### Environment-Specific Deployment

```bash
# Development environment
kubectl apply -f namespaces/epic8-dev.yaml
kubectl apply -f . -n epic8-dev

# Staging environment
kubectl apply -f namespaces/epic8-staging.yaml
kubectl apply -f . -n epic8-staging

# Production environment
kubectl apply -f namespaces/epic8-prod.yaml
kubectl apply -f . -n epic8-prod
```

## Configuration Management

### Common Configuration

The `epic8-common-config` ConfigMap contains shared settings:
- Logging configuration (JSON format, INFO level)
- Metrics and monitoring settings
- Security and TLS configuration
- Performance and rate limiting settings
- Feature flags for platform capabilities

### Service-Specific Configuration

Each service has dedicated configuration in `service-configs.yaml`:
- **Query Analyzer**: ML model settings, complexity thresholds
- **Generator**: Model selection strategy, cost tracking precision
- **Retriever**: Retrieval methods, vector database settings
- **Cache**: Redis configuration, cache strategies
- **Analytics**: Cost tracking, performance monitoring, SLA targets

### Secret Management

Secrets are organized by function:
- **epic8-secrets**: Common platform secrets (DB, Redis, JWT, encryption)
- **llm-api-keys**: LLM provider API keys (OpenAI, Mistral, Anthropic, etc.)
- **monitoring-secrets**: Observability stack credentials

## Network Security

### Network Policies

- **Default Deny**: All traffic denied by default
- **Service Segmentation**: Selective communication between tiers
- **External Access**: Only API Gateway accepts external traffic
- **Monitoring Access**: Prometheus can scrape all service metrics
- **Cross-Namespace**: Monitoring stack can access multiple environments

### Service Communication Flow

```
External → API Gateway → Backend Services (Query Analyzer, Generator, Retriever)
                     ↓
              Data Services (Cache, Analytics)
                     ↓
              External APIs (LLMs, Vector DBs)
```

## Storage Management

### Storage Tiers

- **epic8-fast-ssd**: High-performance storage for models, vector indices, cache
- **epic8-standard**: Standard storage for logs and temporary data
- **epic8-archive**: Cold storage for long-term data retention

### Persistent Volume Claims

- Service logs: 5-10Gi standard storage
- Model storage: 20-50Gi fast SSD
- Vector indices: 100Gi fast SSD
- Shared documents: 200Gi standard (ReadWriteMany)
- Analytics data: 50Gi fast SSD
- Monitoring data: 100Gi fast SSD (Prometheus)

## Resource Requirements

### Minimum Cluster Requirements

- **Nodes**: 3+ nodes for high availability
- **CPU**: 16+ cores total (8 cores requested, 16 cores limit)
- **Memory**: 32Gi+ total (16Gi requested, 32Gi limit)
- **Storage**: 500Gi+ for persistent volumes
- **Network**: CNI with NetworkPolicy support

### Production Scaling

The manifests are designed for horizontal scaling:
- **API Gateway**: Scale to 5+ replicas for high traffic
- **Generator**: Scale to 10+ replicas for high generation load
- **Query Analyzer**: Scale to 5+ replicas for complex analysis
- **Storage**: Auto-expansion enabled for all PVCs

## Multi-Cloud Compatibility

### AWS EKS

- Storage: EBS GP3 with encryption
- Load Balancer: Network Load Balancer annotations
- IAM: Service accounts ready for IRSA

### Google GKE

- Storage: Persistent Disk SSD
- Load Balancer: GCP load balancer integration
- Workload Identity: Service account annotations ready

### Azure AKS

- Storage: Azure Disk Premium SSD
- Load Balancer: Azure load balancer integration
- AAD Pod Identity: Service principal ready

## Monitoring Integration

### Prometheus Metrics

All services expose metrics on port 9090:
- **Business Metrics**: Cost per query, response time, accuracy
- **Technical Metrics**: CPU, memory, request rates, error rates
- **Custom Metrics**: Query complexity, model selection, cache hit rates

### Grafana Dashboards

Ready for dashboard creation:
- **Service Overview**: Health, performance, resource utilization
- **Business Dashboard**: Cost tracking, SLA monitoring, user analytics
- **Technical Dashboard**: Infrastructure metrics, error tracking

## Operational Procedures

### Health Monitoring

```bash
# Check all service health
kubectl get pods -n epic8-prod
kubectl describe pod <pod-name> -n epic8-prod

# Check service endpoints
kubectl get endpoints -n epic8-prod

# Check resource usage
kubectl top pods -n epic8-prod
kubectl top nodes
```

### Log Management

```bash
# View service logs
kubectl logs -f deployment/api-gateway -n epic8-prod
kubectl logs -f deployment/generator -n epic8-prod

# View all Epic 8 logs
kubectl logs -l epic8.platform/version=v1 -n epic8-prod
```

### Configuration Updates

```bash
# Update common configuration
kubectl edit configmap epic8-common-config -n epic8-prod

# Update service-specific configuration
kubectl edit configmap query-analyzer-config -n epic8-prod

# Restart deployments to pick up changes
kubectl rollout restart deployment/query-analyzer -n epic8-prod
```

### Secret Rotation

```bash
# Update API keys
kubectl edit secret llm-api-keys -n epic8-prod

# Update database credentials
kubectl edit secret epic8-secrets -n epic8-prod

# Force deployment restart
kubectl rollout restart deployment/generator -n epic8-prod
```

## Testing Integration

The existing test infrastructure in `k8s/tests/` is preserved and compatible with these manifests. Tests can validate:
- Deployment success and pod readiness
- Service connectivity and endpoints
- Configuration loading and secret mounting
- Network policy enforcement
- Resource allocation and limits

## Swiss Engineering Standards

These manifests implement Swiss engineering principles:
- **Reliability**: 99.9% uptime through redundancy and health checks
- **Efficiency**: >70% resource utilization through proper sizing
- **Security**: Defense in depth with multiple security layers
- **Quality**: Enterprise-grade configuration with comprehensive testing
- **Precision**: Exact resource specifications and quantified SLAs

## Next Steps

1. **Deploy to staging environment** for validation
2. **Configure monitoring stack** (Prometheus, Grafana, Jaeger)
3. **Set up CI/CD pipelines** for automated deployment
4. **Implement service mesh** (Istio/Linkerd) for enhanced observability
5. **Configure auto-scaling** (HPA/VPA) based on workload patterns
6. **Set up backup procedures** for persistent data
7. **Implement disaster recovery** across multiple regions

This Kubernetes deployment provides a solid foundation for the Epic 8 Cloud-Native Multi-Model RAG Platform with enterprise-grade reliability, security, and operational excellence.