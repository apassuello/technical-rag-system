# Epic 8 Kubernetes Network Architecture

**Version**: 1.0.0
**Date**: September 20, 2025
**Cluster**: Kind (epic8-testing) with 3 nodes
**Status**: Working Implementation

## 🌐 **Network Topology Overview**

### Cluster Architecture
```
┌─────────────────────────────────────────────────────────────────┐
│                    Kind Cluster: epic8-testing                  │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │
│  │ Control Plane   │  │    Worker-1     │  │    Worker-2     │  │
│  │ epic8-testing-  │  │ epic8-testing-  │  │ epic8-testing-  │  │
│  │ control-plane   │  │ worker          │  │ worker2         │  │
│  │                 │  │                 │  │                 │  │
│  │ • API Server    │  │ • API Gateway   │  │ • Generator     │  │
│  │ • etcd          │  │ • Analytics     │  │ • Cache         │  │
│  │ • Scheduler     │  │ • Retriever     │  │ • Query Analyzer│  │
│  │ • CNI (kindnet) │  │                 │  │                 │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### Network Addressing
- **Cluster CIDR**: 10.244.0.0/16 (Pod network)
- **Service CIDR**: 10.96.0.0/12 (Service network)
- **Node IPs**: 172.18.0.0/16 (Docker bridge network)

## 📡 **Service Discovery & DNS**

### Internal DNS Resolution
```
Service FQDN Pattern: [service-name].[namespace].svc.cluster.local

Epic 8 Service FQDNs:
├── api-gateway-service.epic8-dev.svc.cluster.local      → 10.96.xxx.xxx:8080
├── query-analyzer-service.epic8-dev.svc.cluster.local  → 10.96.xxx.xxx:8082
├── generator-service.epic8-dev.svc.cluster.local       → 10.96.xxx.xxx:8081
├── retriever-service.epic8-dev.svc.cluster.local       → 10.96.xxx.xxx:8083
├── cache-service.epic8-dev.svc.cluster.local           → 10.96.xxx.xxx:8084
└── analytics-service.epic8-dev.svc.cluster.local       → 10.96.xxx.xxx:8085
```

### Service Discovery Implementation
```yaml
# Example: API Gateway discovering backend services
apiVersion: v1
kind: Service
metadata:
  name: query-analyzer-service
  namespace: epic8-dev
spec:
  selector:
    app.kubernetes.io/name: query-analyzer
  ports:
    - name: http
      port: 8082
      targetPort: 8082
      protocol: TCP
    - name: metrics
      port: 9090
      targetPort: 9090
      protocol: TCP
```

## 🔀 **Communication Patterns**

### 1. External Client → API Gateway
```
Internet/User → kubectl port-forward → API Gateway Pod
             → NodePort/LoadBalancer → API Gateway Service
             → ClusterIP             → API Gateway Pods
```

### 2. API Gateway → Backend Services (Hub Pattern)
```
API Gateway (Hub)
├── HTTP/REST → Query Analyzer Service  → Port 8082
├── HTTP/REST → Generator Service       → Port 8081
├── HTTP/REST → Retriever Service       → Port 8083
├── HTTP/REST → Cache Service           → Port 8084
└── HTTP/REST → Analytics Service       → Port 8085
```

### 3. Inter-Service Communication
```
Query Processing Pipeline:
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│ API Gateway │───▶│Query Analyzer│───▶│  Retriever  │───▶│ Generator   │
│             │    │             │    │             │    │             │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
       │                                      │                   │
       │           ┌─────────────┐           │                   │
       └──────────▶│   Cache     │◀──────────┴───────────────────┘
                   │             │
                   └─────────────┘
                           │
                   ┌─────────────┐
                   │ Analytics   │
                   │             │
                   └─────────────┘
```

## 🛡️ **Network Security**

### Pod Security Context
```yaml
# All Epic 8 pods run with restricted security context
securityContext:
  runAsNonRoot: true
  runAsUser: 1000
  runAsGroup: 1000
  fsGroup: 1000
  capabilities:
    drop:
      - ALL
  readOnlyRootFilesystem: false  # Writable for logs/cache
  allowPrivilegeEscalation: false
```

### Network Policies (Production Ready)
```yaml
# Example: API Gateway network policy
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: api-gateway-network-policy
  namespace: epic8-dev
spec:
  podSelector:
    matchLabels:
      app.kubernetes.io/name: api-gateway
  policyTypes:
    - Ingress
    - Egress
  ingress:
    - from:
        - namespaceSelector:
            matchLabels:
              name: epic8-dev
      ports:
        - protocol: TCP
          port: 8080
  egress:
    - to:
        - podSelector:
            matchLabels:
              epic8.platform/tier: backend
      ports:
        - protocol: TCP
          port: 8081  # Generator
        - protocol: TCP
          port: 8082  # Query Analyzer
        - protocol: TCP
          port: 8083  # Retriever
        - protocol: TCP
          port: 8084  # Cache
        - protocol: TCP
          port: 8085  # Analytics
```

### Service Mesh Readiness (Istio/Linkerd)
```yaml
# Pod annotations for service mesh injection
metadata:
  annotations:
    sidecar.istio.io/inject: "true"
    linkerd.io/inject: enabled
    prometheus.io/scrape: "true"
    prometheus.io/port: "9090"
    prometheus.io/path: "/metrics"
```

## 🔌 **Port Mapping & Endpoints**

### Service Port Allocation
| Service | HTTP Port | Metrics Port | Health Check | Purpose |
|---------|-----------|--------------|--------------|---------|
| **API Gateway** | 8080 | 9090 | `/health` | External interface, orchestration |
| **Query Analyzer** | 8082 | 9090 | `/health/startup` | ML query complexity analysis |
| **Generator** | 8081 | 9090 | `/health/live` | Multi-model answer generation |
| **Retriever** | 8083 | 9090 | `/health/ready` | Document retrieval & ranking |
| **Cache** | 8084 | 9090 | `/health` | Redis-compatible caching |
| **Analytics** | 8085 | 9090 | `/metrics` | Usage analytics & monitoring |

### Endpoint Details
```bash
# API Gateway Endpoints
/                          # Service overview
/health                    # Health check
/api/v1/status            # Comprehensive status
/api/v1/query             # RAG query processing
/api/v1/batch-query       # Batch processing
/api/v1/models            # Available models
/docs                     # API documentation
/metrics                  # Prometheus metrics

# Backend Service Endpoints
/health/startup           # Startup probe
/health/ready             # Readiness probe
/health/live              # Liveness probe
/api/v1/[service-specific] # Service API
/metrics                  # Prometheus metrics
```

## 📊 **Load Balancing & Traffic Distribution**

### Service Load Balancing
```yaml
# Each service uses round-robin load balancing by default
apiVersion: v1
kind: Service
metadata:
  name: api-gateway-service
spec:
  type: ClusterIP
  sessionAffinity: None  # Round-robin
  selector:
    app.kubernetes.io/name: api-gateway
  ports:
    - port: 8080
      targetPort: 8080
```

### Traffic Distribution Strategies
```
API Gateway (2 replicas):
├── 50% → api-gateway-578898658b-9qhrx (Worker-1: 10.244.1.6)
└── 50% → api-gateway-578898658b-gfrb2 (Worker-2: 10.244.2.6)

Generator (3 replicas in production):
├── 33% → generator-797fdd4645-replica1
├── 33% → generator-797fdd4645-replica2
└── 34% → generator-797fdd4645-replica3
```

### Circuit Breaker Pattern
```
API Gateway → Backend Services:
├── Circuit Breaker Status: CLOSED (healthy)
├── Failure Threshold: 5 consecutive failures
├── Timeout: 8 seconds per request
├── Recovery Time: 60 seconds
└── Fallback: Cached responses or error messages
```

## 🗄️ **Storage Network Integration**

### Persistent Volume Architecture
```
Storage Network:
┌─────────────────────────────────────────────────────────────────┐
│                     Kind Local Storage                          │
├─────────────────────────────────────────────────────────────────┤
│  Storage Classes:                                               │
│  ├── epic8-kind-standard (rancher.io/local-path)               │
│  ├── epic8-kind-fast     (rancher.io/local-path)               │
│  └── epic8-kind-archive  (rancher.io/local-path)               │
│                                                                 │
│  Persistent Volumes:                                            │
│  ├── analytics-data     → /var/local-path-provisioner/         │
│  ├── retriever-cache    → /var/local-path-provisioner/         │
│  ├── epic8-document-data → /var/local-path-provisioner/        │
│  └── logs & cache volumes → /var/local-path-provisioner/       │
└─────────────────────────────────────────────────────────────────┘
```

### Volume Mount Network Paths
```yaml
# Example: Retriever service volume mounts
volumeMounts:
  - name: cache
    mountPath: /app/cache
    subPath: retriever-cache
  - name: logs
    mountPath: /app/logs
    subPath: retriever-logs
  - name: vector-indices
    mountPath: /app/indices
    subPath: vector-indices
```

## 🌍 **Multi-Environment Network Isolation**

### Namespace-Based Isolation
```
Network Isolation Strategy:
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│   epic8-dev     │  │ epic8-staging   │  │  epic8-prod     │
│                 │  │                 │  │                 │
│ • Development   │  │ • Pre-production│  │ • Production    │
│ • Local testing │  │ • Integration   │  │ • Live traffic  │
│ • Kind cluster  │  │ • Cloud cluster │  │ • Cloud cluster │
│ • No isolation  │  │ • Network       │  │ • Full network  │
│                 │  │   policies      │  │   isolation     │
└─────────────────┘  └─────────────────┘  └─────────────────┘
```

### Cross-Namespace Communication (Production)
```yaml
# Allow epic8-prod to access shared services
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: cross-namespace-access
  namespace: epic8-prod
spec:
  podSelector: {}
  policyTypes:
    - Egress
  egress:
    - to:
        - namespaceSelector:
            matchLabels:
              name: monitoring
      ports:
        - protocol: TCP
          port: 9090  # Prometheus
    - to:
        - namespaceSelector:
            matchLabels:
              name: logging
      ports:
        - protocol: TCP
          port: 9200  # Elasticsearch
```

## 🔧 **CNI & Networking Implementation**

### Kind CNI Configuration (kindnet)
```yaml
# Kind cluster networking
apiVersion: kind.x-k8s.io/v1alpha4
kind: Cluster
networking:
  apiServerAddress: "127.0.0.1"
  apiServerPort: 58482
  podSubnet: "10.244.0.0/16"
  serviceSubnet: "10.96.0.0/12"
  dnsDomain: "cluster.local"
nodes:
  - role: control-plane
    extraPortMappings:
      - containerPort: 80
        hostPort: 80
      - containerPort: 443
        hostPort: 443
```

### Production CNI Integration
```yaml
# Cilium CNI (recommended for production)
apiVersion: v1
kind: ConfigMap
metadata:
  name: cilium-config
  namespace: kube-system
data:
  enable-ipv4: "true"
  enable-ipv6: "false"
  cluster-pool-ipv4-cidr: "10.244.0.0/16"
  cluster-pool-ipv4-mask-size: "24"
  enable-hubble: "true"
  hubble-metrics-server: ":9091"
```

## 📈 **Network Monitoring & Observability**

### Built-in Network Metrics
```bash
# API Gateway provides network observability
curl http://localhost:8080/api/v1/status | jq '{
  services: .services[],
  response_times: .services[].response_time,
  circuit_breakers: .circuit_breakers,
  network_health: (.healthy_services / .total_services)
}'
```

### Prometheus Network Metrics
```yaml
# Network metrics exposed by all services
epic8_http_requests_total{method="GET", status="200", service="api-gateway"}
epic8_http_request_duration_seconds{service="api-gateway", endpoint="/api/v1/query"}
epic8_circuit_breaker_state{service="query-analyzer", state="closed"}
epic8_network_connections_active{service="retriever", destination="cache-service"}
```

### Network Troubleshooting Tools
```bash
# Service connectivity testing
kubectl run network-test --image=busybox --rm -it -n epic8-dev -- /bin/sh
# Inside pod:
nslookup api-gateway-service.epic8-dev.svc.cluster.local
wget -qO- http://api-gateway-service:8080/health
nc -zv query-analyzer-service 8082

# Network policy testing
kubectl exec -it deployment/api-gateway -n epic8-dev -- curl generator-service:8081/health

# DNS resolution verification
kubectl exec -it deployment/api-gateway -n epic8-dev -- nslookup kubernetes.default.svc.cluster.local
```

## 🚀 **Performance & Optimization**

### Network Performance Tuning
```yaml
# Optimized service configuration
apiVersion: v1
kind: Service
metadata:
  name: api-gateway-service
  annotations:
    service.alpha.kubernetes.io/tolerate-unready-endpoints: "true"
spec:
  type: ClusterIP
  sessionAffinity: None
  ipFamilyPolicy: SingleStack
  ipFamilies:
    - IPv4
```

### Connection Pooling & Keep-Alive
```python
# Example: API Gateway HTTP client configuration
import httpx

# Optimized HTTP client for inter-service communication
http_client = httpx.AsyncClient(
    timeout=httpx.Timeout(8.0),
    limits=httpx.Limits(
        max_keepalive_connections=20,
        max_connections=100,
        keepalive_expiry=30.0
    ),
    http2=True  # Enable HTTP/2 for better performance
)
```

### Bandwidth & Latency Optimization
```
Network Performance Targets:
├── Intra-cluster latency: <1ms (P95)
├── Service-to-service latency: <5ms (P95)
├── API Gateway response time: <100ms (P95)
├── External client latency: <200ms (P95)
└── Throughput: 1000+ requests/second
```

## 🔒 **Security Implementation**

### mTLS Configuration (Production)
```yaml
# Istio mTLS policy
apiVersion: security.istio.io/v1beta1
kind: PeerAuthentication
metadata:
  name: epic8-mtls
  namespace: epic8-prod
spec:
  mtls:
    mode: STRICT
---
apiVersion: security.istio.io/v1beta1
kind: DestinationRule
metadata:
  name: epic8-destination-rule
  namespace: epic8-prod
spec:
  host: "*.epic8-prod.svc.cluster.local"
  trafficPolicy:
    tls:
      mode: ISTIO_MUTUAL
```

### Network Policy Examples
```yaml
# Deny all traffic by default (production)
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: deny-all
  namespace: epic8-prod
spec:
  podSelector: {}
  policyTypes:
    - Ingress
    - Egress
---
# Allow API Gateway to backend services
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: api-gateway-to-backends
  namespace: epic8-prod
spec:
  podSelector:
    matchLabels:
      app.kubernetes.io/name: api-gateway
  egress:
    - to:
        - podSelector:
            matchLabels:
              epic8.platform/tier: backend
```

## 📋 **Network Validation Checklist**

### Deployment Validation
- [ ] All services have ClusterIP addresses assigned
- [ ] Service selectors match pod labels correctly
- [ ] DNS resolution works for all service FQDNs
- [ ] Port forwarding successful for all services
- [ ] Inter-service communication functional
- [ ] Health check endpoints responding
- [ ] Prometheus metrics endpoints accessible
- [ ] Network policies applied (production)
- [ ] mTLS enabled (production)
- [ ] Load balancing distributing traffic evenly

### Performance Validation
- [ ] Latency within acceptable limits (<5ms intra-cluster)
- [ ] No connection timeouts under normal load
- [ ] Circuit breakers functioning correctly
- [ ] Connection pooling optimized
- [ ] HTTP/2 enabled where applicable
- [ ] DNS caching configured

### Security Validation
- [ ] Network policies block unauthorized traffic
- [ ] mTLS encryption in transit (production)
- [ ] Service accounts have minimal permissions
- [ ] Pod security contexts enforce non-root
- [ ] Network segmentation between environments
- [ ] Monitoring for network anomalies

---

**Network Status**: Epic 8 network architecture is fully functional in Kind with comprehensive service discovery, load balancing, and monitoring. Ready for production deployment with additional security hardening.