# Epic 8 Comprehensive Learning Plan

**Time Required**: 8-10 hours
**Goal**: Deep understanding of microservices architecture through code, docs, and hands-on
**Strategy**: Learn each layer by combining all three approaches (read → examine → experiment)

---

## 🎯 Learning Philosophy

For each layer, you will:
1. **READ** the relevant documentation (understand concepts)
2. **EXAMINE** the actual code (see implementation)
3. **EXPERIMENT** hands-on (validate understanding)

This interleaved approach ensures you understand WHY (docs), HOW (code), and THAT IT WORKS (hands-on).

---

## 📚 Layer 1: The Big Picture (1.5 hours)

### 🔍 Step 1.1: Visual Architecture First (20 min)

**READ**:
```bash
# Read the main architecture document
open docs/epic8/EPIC8_MICROSERVICES_ARCHITECTURE.md
# OR: cat docs/epic8/EPIC8_MICROSERVICES_ARCHITECTURE.md | less

# Read the deployment overview
open docs/deployment/aws-ecs/deployment-plan.md
# Focus on sections:
# - Complete System Architecture
# - Service Communication Flow
# - 3-Tier Model Routing
```

**Key Concepts to Understand**:
- 6 microservices: API Gateway, Query Analyzer, Generator, Retriever, Analytics, Cache
- Why microservices? (scalability, independence, cloud-native)
- How they communicate (HTTP/REST)
- Load balancing (ALB in AWS)

**ACTION**: Draw the architecture on paper as you read:
```
Client
  │
  ▼
Application Load Balancer (ALB)
  │
  ▼
API Gateway ──────┬──────────────────────────┐
                  │                          │
                  ▼                          ▼
         Query Analyzer              Generator
                  │                          │
                  │                          ▼
                  │                      Retriever
                  │                          │
                  └──────────┬───────────────┘
                             ▼
                        Analytics
                             ▼
                        Redis Cache
```

---

### 👀 Step 1.2: Code Tour - Service Structure (30 min)

**EXAMINE**:
```bash
# Look at the service directory structure
ls -la services/

# Expected output:
# - api-gateway/
# - query-analyzer/
# - generator/
# - retriever/
# - analytics/
# - cache/ (Redis - might be external)

# For EACH service, examine structure:
for service in api-gateway query-analyzer generator retriever analytics; do
    echo "=== $service ==="
    ls -la services/$service/
    echo ""
done
```

**Notice the Pattern** - Each service has:
- `main.py` - FastAPI application
- `requirements.txt` - Python dependencies
- `Dockerfile` - Container definition
- `tests/` - Service-specific tests
- Sometimes: `config/`, `schemas/`, `utils/`

**EXAMINE ONE SERVICE IN DETAIL** (start with Analytics - it's simple):
```bash
# Read the entire Analytics service
cat services/analytics/main.py

# What to look for:
# 1. FastAPI app initialization
# 2. Health check endpoint (/health)
# 3. Metrics endpoint (/metrics)
# 4. How it stores data (in-memory? database?)
# 5. CORS configuration
# 6. Error handling
```

**Key Questions to Answer**:
- [ ] What framework are services built with? (FastAPI)
- [ ] What's the purpose of the health check endpoint?
- [ ] How do services import from `src/`?
- [ ] What data does Analytics track?

---

### 🛠️ Step 1.3: Hands-On - Run ONE Service Locally (40 min)

**EXPERIMENT**:

```bash
# Navigate to the simplest service
cd services/analytics

# Install dependencies (in virtual environment)
pip install -r requirements.txt

# Run the service
uvicorn main:app --reload --port 8003
```

**Expected Output**:
```
INFO:     Uvicorn running on http://127.0.0.1:8003
INFO:     Application startup complete.
```

**TEST THE SERVICE** (in another terminal):
```bash
# Test health check
curl http://localhost:8003/health
# Expected: {"status": "healthy", "service": "analytics", ...}

# Test metrics endpoint
curl http://localhost:8003/metrics
# Expected: {"total_queries": 0, "average_latency": 0, ...}

# Check the API documentation (FastAPI auto-generates this)
open http://localhost:8003/docs
# OR: curl http://localhost:8003/docs
```

**EXPERIMENT**:
1. Modify the health check response in `main.py`
2. Restart the service (auto-reload should catch it)
3. Call `/health` again - see your change
4. Change it back

**Stop the service**: `Ctrl+C`

**✅ Checkpoint Questions**:
- [ ] Can you run the Analytics service?
- [ ] Can you call its endpoints?
- [ ] Do you understand what FastAPI does?
- [ ] Can you find the endpoint definitions in `main.py`?

---

## 🔗 Layer 2: Service Communication (2 hours)

### 🔍 Step 2.1: Read How Services Talk (30 min)

**READ**:
```bash
# Read the API Gateway - it's the orchestrator
cat services/api-gateway/main.py | less

# Find and read these sections:
# 1. Import statements (top)
# 2. Service URL configuration (env vars)
# 3. /api/v1/query endpoint (main request handler)
# 4. How it calls query-analyzer
# 5. How it calls generator
# 6. Error handling (try/except blocks)
# 7. Response formatting
```

**Trace ONE Complete Request**:
```
1. POST /api/v1/query receives: {"query": "What is Python?"}
2. API Gateway extracts query text
3. Calls Query Analyzer: POST http://query-analyzer:8001/analyze
   → Response: {"complexity": 2.3, "recommended_model": "ollama"}
4. Calls Generator: POST http://generator:8002/generate
   → Response: {"answer": "...", "model_used": "ollama", "cost": 0.0}
5. Calls Analytics: POST http://analytics:8003/log
   → Response: {"logged": true}
6. Returns to client: {"answer": "...", "metadata": {...}}
```

**Key Concepts**:
- Service discovery via environment variables
- HTTP client (httpx or requests)
- Error handling and fallbacks
- Request/response schemas

---

### 👀 Step 2.2: Examine Service-to-Service Code (30 min)

**EXAMINE**:

```bash
# Look at how API Gateway calls other services
grep -n "query-analyzer" services/api-gateway/main.py
grep -n "generator" services/api-gateway/main.py
grep -n "analytics" services/api-gateway/main.py

# Find the service URL configuration
grep -n "QUERY_ANALYZER_URL" services/api-gateway/main.py
grep -n "GENERATOR_URL" services/api-gateway/main.py

# Look at the actual HTTP calls
# Find the function that calls query-analyzer
# Find the function that calls generator
```

**Example Pattern You'll See**:
```python
# Service URL from environment
QUERY_ANALYZER_URL = os.getenv("QUERY_ANALYZER_URL", "http://localhost:8001")

# HTTP call to another service
async with httpx.AsyncClient() as client:
    response = await client.post(
        f"{QUERY_ANALYZER_URL}/analyze",
        json={"query": query_text}
    )
    analysis = response.json()
```

**COMPARE** with Query Analyzer:
```bash
# Look at what Query Analyzer exposes
cat services/query-analyzer/main.py | grep -A 10 "@app.post"

# Find the /analyze endpoint
# See what it expects as input
# See what it returns as output
```

---

### 🛠️ Step 2.3: Hands-On - Run Multi-Service (1 hour)

**EXPERIMENT**: Run all services locally and watch them communicate.

**Terminal Setup** (you'll need 6 terminals):

**Terminal 1: Query Analyzer**
```bash
cd services/query-analyzer
pip install -r requirements.txt
uvicorn main:app --port 8001 --reload
```

**Terminal 2: Generator**
```bash
cd services/generator
pip install -r requirements.txt
uvicorn main:app --port 8002 --reload
```

**Terminal 3: Retriever**
```bash
cd services/retriever
pip install -r requirements.txt
uvicorn main:app --port 8004 --reload
```

**Terminal 4: Analytics**
```bash
cd services/analytics
pip install -r requirements.txt
uvicorn main:app --port 8003 --reload
```

**Terminal 5: API Gateway**
```bash
cd services/api-gateway
pip install -r requirements.txt

# Set environment variables for service discovery
export QUERY_ANALYZER_URL=http://localhost:8001
export GENERATOR_URL=http://localhost:8002
export RETRIEVER_URL=http://localhost:8004
export ANALYTICS_URL=http://localhost:8003

uvicorn main:app --port 8000 --reload
```

**Terminal 6: Testing**
```bash
# Test the full flow
curl -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What is Python?"}'

# You should see logs in ALL service terminals!
# Watch the request flow through each service
```

**WATCH THE LOGS** - this is the key learning moment:
- Terminal 1 (Query Analyzer): See analysis request
- Terminal 2 (Generator): See generation request
- Terminal 3 (Retriever): See retrieval request
- Terminal 4 (Analytics): See logging request
- Terminal 5 (API Gateway): See orchestration

**EXPERIMENT**:
1. Stop one service (Ctrl+C in its terminal)
2. Make a request - see the error handling
3. Restart the service
4. Make request again - see it work

**MODIFY AND TEST**:
1. In Query Analyzer, change the complexity score
2. Watch how it affects which model Generator uses
3. Change it back

**Stop all services**: Ctrl+C in each terminal

**✅ Checkpoint Questions**:
- [ ] Can you run all 5 services together?
- [ ] Can you trace a request through all services?
- [ ] Do you understand service discovery (env vars)?
- [ ] What happens when one service is down?

---

## 🐳 Layer 3: Containerization (2 hours)

### 🔍 Step 3.1: Read Docker Basics (20 min)

**READ**:
```bash
# Read one Dockerfile to understand the pattern
cat services/api-gateway/Dockerfile

# Read the Docker deployment guide
cat docs/deployment/DOCKER_DEPLOYMENT_GUIDE.md | head -300
```

**Key Dockerfile Concepts**:
```dockerfile
FROM python:3.11-slim          # Base image
WORKDIR /app                    # Working directory
COPY requirements.txt .         # Copy dependency list
RUN pip install -r requirements.txt  # Install dependencies
COPY . .                        # Copy source code
EXPOSE 8000                     # Port to expose
CMD ["uvicorn", "main:app"]     # Command to run
```

**Why Docker?**:
- Consistent environment (works on any machine)
- Isolation (dependencies don't conflict)
- Easy deployment (ship the container)
- Scalability (run multiple instances)

---

### 👀 Step 3.2: Code - Docker Compose (30 min)

**EXAMINE**:
```bash
# Read the Docker Compose file
cat docker-compose.yml | less
```

**What to Look For**:

1. **Service Definitions**:
```yaml
services:
  api-gateway:
    build: ./services/api-gateway
    ports:
      - "8000:8000"
    environment:
      - QUERY_ANALYZER_URL=http://query-analyzer:8001
    depends_on:
      - query-analyzer
      - generator
```

2. **Key Concepts**:
- `build`: Where the Dockerfile is
- `ports`: Port mapping (host:container)
- `environment`: Environment variables
- `depends_on`: Service dependencies
- `networks`: How services communicate
- `volumes`: Persistent data

3. **Service Discovery**:
```yaml
# Services can reach each other by name!
# api-gateway can call: http://query-analyzer:8001
# Docker Compose creates a network with DNS
```

**COMPARE**: Multi-terminal setup vs Docker Compose:
- Manual: 6 terminals, manual env vars, manual startup order
- Docker Compose: 1 command, automatic network, automatic ordering

---

### 🛠️ Step 3.3: Hands-On - Docker Everything (1 hour 10 min)

**EXPERIMENT**:

**Build All Services**:
```bash
cd /home/user/technical-rag-system/project-1-technical-rag

# Build all Docker images (this takes a while)
./docker-setup.sh

# OR manually:
docker-compose build

# Watch the build process - see each service being built
```

**Check What Was Built**:
```bash
# List Docker images
docker images | grep epic8

# Expected output:
# epic8-api-gateway
# epic8-query-analyzer
# epic8-generator
# epic8-retriever
# epic8-analytics
```

**Start Everything**:
```bash
# Start all services
docker-compose up

# Watch the logs - see all services starting
# This is ONE terminal showing ALL service logs (color-coded)
```

**Test the System** (in another terminal):
```bash
# Test health checks
curl http://localhost:8000/health
curl http://localhost:8001/health
curl http://localhost:8002/health
curl http://localhost:8003/health

# Test full query flow
curl -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What is machine learning?"}' | jq .

# Check metrics
curl http://localhost:8003/metrics | jq .
```

**Docker Commands to Know**:
```bash
# View running containers
docker-compose ps

# View logs for one service
docker-compose logs -f api-gateway

# Restart one service
docker-compose restart generator

# Stop all services
docker-compose down

# Stop and remove volumes
docker-compose down -v
```

**EXPERIMENT - Service Failure**:
```bash
# In one terminal: docker-compose up
# In another terminal:

# Stop one service
docker-compose stop generator

# Try making a request - see error handling
curl -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Test"}' | jq .

# Restart the service
docker-compose start generator

# Try again - should work
curl -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Test"}' | jq .
```

**EXPERIMENT - Scaling**:
```bash
# Run multiple instances of a service
docker-compose up --scale generator=3

# Check running containers
docker-compose ps

# Make multiple requests - they'll be load balanced
for i in {1..5}; do
  curl -X POST http://localhost:8000/api/v1/query \
    -H "Content-Type: application/json" \
    -d '{"query": "Test '$i'"}' | jq .model_used
done
```

**Stop Everything**:
```bash
docker-compose down
```

**✅ Checkpoint Questions**:
- [ ] Can you build all Docker images?
- [ ] Can you start all services with one command?
- [ ] Do you understand service discovery in Docker?
- [ ] Can you view logs and restart services?
- [ ] What's the benefit over running services manually?

---

## ☸️ Layer 4: Kubernetes Basics (2.5 hours)

### 🔍 Step 4.1: Read K8s Concepts (45 min)

**READ**:
```bash
# Read the K8s deployment guide
cat k8s/README.md

# Read comparison: ECS vs K8s
cat docs/deployment/aws-ecs/README.md | grep -A 20 "vs Kubernetes"
```

**Key Kubernetes Concepts**:

1. **Pod**: Smallest deployable unit (one or more containers)
2. **Deployment**: Manages desired state (e.g., "run 3 replicas")
3. **Service**: Networking/load balancing (how pods communicate)
4. **ConfigMap**: Non-sensitive configuration
5. **Secret**: Sensitive data (passwords, API keys)
6. **Namespace**: Logical cluster subdivision

**Why Kubernetes?**:
- Auto-scaling (HPA - Horizontal Pod Autoscaler)
- Self-healing (restarts failed pods)
- Rolling updates (zero-downtime deployments)
- Service discovery (built-in DNS)
- Resource management (CPU/memory limits)

**READ ONE COMPLETE EXAMPLE**:
```bash
# API Gateway Deployment
cat k8s/api-gateway-deployment.yaml

# API Gateway Service
cat k8s/api-gateway-service.yaml

# Understand how they connect
```

---

### 👀 Step 4.2: Code - K8s Manifests (45 min)

**EXAMINE**: Look at the pattern across all services.

```bash
# List all K8s manifests
ls -la k8s/

# Expected:
# - *-deployment.yaml (defines pods)
# - *-service.yaml (defines networking)
# - configmap.yaml (configuration)
# - secrets.yaml (sensitive data)
```

**Examine ONE Deployment**:
```bash
cat k8s/api-gateway-deployment.yaml
```

**Key Sections**:
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api-gateway
  labels:
    app: epic8
    component: api-gateway
spec:
  replicas: 2                    # Run 2 instances
  selector:
    matchLabels:
      component: api-gateway
  template:
    metadata:
      labels:
        component: api-gateway
    spec:
      containers:
      - name: api-gateway
        image: epic8-api-gateway:latest
        ports:
        - containerPort: 8000
        env:                     # Environment variables
        - name: QUERY_ANALYZER_URL
          value: "http://query-analyzer:8001"
        resources:               # Resource limits
          requests:
            cpu: "100m"
            memory: "256Mi"
          limits:
            cpu: "500m"
            memory: "512Mi"
        livenessProbe:           # Health checks
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
```

**Examine ONE Service**:
```bash
cat k8s/api-gateway-service.yaml
```

**Key Sections**:
```yaml
apiVersion: v1
kind: Service
metadata:
  name: api-gateway
spec:
  selector:
    component: api-gateway      # Routes to pods with this label
  ports:
  - protocol: TCP
    port: 8000                  # Service port
    targetPort: 8000            # Container port
  type: LoadBalancer            # External access
```

**COMPARE ALL SERVICES**:
```bash
# Notice the pattern - they're all similar
for service in api-gateway query-analyzer generator retriever analytics; do
  echo "=== $service ==="
  head -30 k8s/${service}-deployment.yaml
  echo ""
done
```

**Key Differences from Docker Compose**:
| Feature | Docker Compose | Kubernetes |
|---------|----------------|------------|
| Scaling | Manual | Automatic (HPA) |
| Health Checks | Basic | Liveness + Readiness |
| Load Balancing | Basic | Advanced (Service) |
| Resource Limits | No | Yes (requests/limits) |
| Self-Healing | No | Yes |
| Service Discovery | Docker DNS | K8s DNS |

---

### 🛠️ Step 4.3: Hands-On - Local K8s (1 hour 20 min)

**EXPERIMENT**: Deploy to local Kubernetes cluster.

**Option A: Kind (Kubernetes in Docker)**

**Install Kind** (if not installed):
```bash
# macOS
brew install kind

# Linux
curl -Lo ./kind https://kind.sigs.k8s.io/dl/v0.20.0/kind-linux-amd64
chmod +x ./kind
sudo mv ./kind /usr/local/bin/kind

# Verify
kind version
```

**Create Local Cluster**:
```bash
# Create cluster
kind create cluster --name epic8-dev

# Verify
kubectl cluster-info
kubectl get nodes

# Expected: One control-plane node running
```

**Load Docker Images into Kind**:
```bash
# Build images first (if not already built)
docker-compose build

# Load each image into Kind
for service in api-gateway query-analyzer generator retriever analytics; do
  echo "Loading epic8-${service}..."
  kind load docker-image epic8-${service}:latest --name epic8-dev
done

# This makes your local images available to K8s
```

**Deploy to Kubernetes**:
```bash
# Apply all manifests
kubectl apply -f k8s/

# Watch pods starting
kubectl get pods -w

# Expected output (after a minute):
# NAME                              READY   STATUS    RESTARTS   AGE
# api-gateway-xxx                   1/1     Running   0          30s
# query-analyzer-xxx                1/1     Running   0          30s
# generator-xxx                     1/1     Running   0          30s
# retriever-xxx                     1/1     Running   0          30s
# analytics-xxx                     1/1     Running   0          30s

# Press Ctrl+C to stop watching
```

**Check Services**:
```bash
# List services
kubectl get services

# Expected:
# NAME             TYPE           PORT(S)
# api-gateway      LoadBalancer   8000:XXXXX/TCP
# query-analyzer   ClusterIP      8001/TCP
# generator        ClusterIP      8002/TCP
# ...
```

**Access the System**:
```bash
# Port-forward API Gateway
kubectl port-forward service/api-gateway 8000:8000

# In another terminal, test
curl http://localhost:8000/health

curl -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What is Kubernetes?"}' | jq .
```

**Kubernetes Commands to Know**:
```bash
# View all resources
kubectl get all

# Describe a pod (detailed info)
kubectl describe pod <pod-name>

# View logs
kubectl logs -f deployment/api-gateway

# Exec into a pod (for debugging)
kubectl exec -it <pod-name> -- /bin/bash

# Delete a pod (K8s will recreate it - self-healing!)
kubectl delete pod <api-gateway-pod-name>
kubectl get pods -w  # Watch it recreate
```

**EXPERIMENT - Scaling**:
```bash
# Scale query-analyzer to 3 replicas
kubectl scale deployment query-analyzer --replicas=3

# Watch pods
kubectl get pods

# You should see 3 query-analyzer pods

# Scale back down
kubectl scale deployment query-analyzer --replicas=1
```

**EXPERIMENT - Self-Healing**:
```bash
# Get a pod name
kubectl get pods

# Delete a pod
kubectl delete pod <api-gateway-pod-name>

# Immediately watch pods
kubectl get pods -w

# K8s will automatically create a new pod!
```

**EXPERIMENT - Updates**:
```bash
# Edit deployment
kubectl edit deployment api-gateway

# Change replicas: 2 → 3
# Save and exit

# Watch K8s create the new pod
kubectl get pods -w
```

**View Resource Usage**:
```bash
# Install metrics server (if needed)
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml

# View resource usage
kubectl top nodes
kubectl top pods
```

**Cleanup**:
```bash
# Delete all resources
kubectl delete -f k8s/

# Or delete the entire cluster
kind delete cluster --name epic8-dev
```

**✅ Checkpoint Questions**:
- [ ] Can you create a local K8s cluster?
- [ ] Can you deploy all services to K8s?
- [ ] Do you understand Deployments vs Services?
- [ ] Can you scale a service?
- [ ] Do you understand self-healing?
- [ ] Can you view logs and exec into pods?

---

## ☁️ Layer 5: Cloud Deployment (2 hours)

### 🔍 Step 5.1: Read AWS ECS Architecture (45 min)

**READ**:
```bash
# Read the complete deployment plan
cat docs/deployment/aws-ecs/deployment-plan.md | less

# Focus on these sections:
# 1. Executive Summary
# 2. Architecture Overview
# 3. Cost Analysis
# 4. Infrastructure Setup
# 5. Service Deployment
```

**Key ECS Concepts**:

1. **Fargate**: Serverless compute for containers
   - No EC2 instances to manage
   - Pay only for what you use
   - Auto-scaling built-in

2. **Task Definition**: Like K8s Pod spec
   - Defines container(s)
   - CPU/memory requirements
   - Environment variables

3. **Service**: Like K8s Deployment
   - Maintains desired task count
   - Load balancing
   - Auto-scaling

4. **ALB (Application Load Balancer)**:
   - Routes traffic to services
   - Health checks
   - SSL termination

**Why ECS for $100 Budget?**:
```
Kubernetes (EKS):
- $0.10/hour for control plane = $72/month
- EC2 nodes = $50+/month
- Total: ~$120/month = 7.5 days on $100

ECS Fargate:
- No control plane cost
- Pay per task: ~$3.20/day
- Total: 31 days on $100 ✅
```

**Architecture**:
```
Internet
   │
   ▼
Application Load Balancer (ALB)
   │
   ├─► Target Group: API Gateway
   │   └─► ECS Tasks (api-gateway) [Fargate]
   │
   └─► Internal ALB (optional)
       ├─► Query Analyzer Service
       ├─► Generator Service
       ├─► Retriever Service
       └─► Analytics Service
```

---

### 👀 Step 5.2: Code - Deployment Scripts (45 min)

**EXAMINE**:

```bash
# Read the main deployment script
cat deployment/ecs/deploy.sh | less
```

**Script Structure**:
```bash
# Main functions:
setup()     # Creates AWS infrastructure (VPC, ECS cluster, ALB, etc.)
build()     # Builds Docker images, tags, pushes to ECR
deploy()    # Creates task definitions and services
test()      # Validates deployment
teardown()  # Deletes everything
```

**Examine SETUP phase**:
```bash
# Find the setup function
grep -A 50 "^setup()" deployment/ecs/deploy.sh

# What it does:
# 1. Create VPC (network)
# 2. Create subnets (public/private)
# 3. Create security groups (firewall)
# 4. Create IAM roles (permissions)
# 5. Create ECS cluster
# 6. Create ECR repositories (Docker registry)
# 7. Create ALB and target groups
# 8. Store secrets in AWS Secrets Manager
# 9. Create CloudWatch log groups
```

**Examine BUILD phase**:
```bash
grep -A 30 "^build()" deployment/ecs/deploy.sh

# What it does:
# 1. Build Docker images locally
# 2. Tag with ECR repository URL
# 3. Login to ECR
# 4. Push images to ECR
```

**Examine DEPLOY phase**:
```bash
grep -A 50 "^deploy()" deployment/ecs/deploy.sh

# What it does:
# 1. Register task definitions
# 2. Create ECS services
# 3. Configure service discovery
# 4. Set up auto-scaling
# 5. Configure health checks
```

**Look at Cost Monitoring**:
```bash
cat deployment/ecs/check-costs.sh

# What it does:
# 1. Queries AWS Cost Explorer API
# 2. Shows daily costs
# 3. Projects monthly costs
# 4. Warns if approaching budget
```

**Examine Terraform (Infrastructure as Code)**:
```bash
# List Terraform modules
ls -la terraform/modules/

# Read ECS Fargate module
cat terraform/modules/ecs-fargate/main.tf | head -200

# See how infrastructure is defined as code
```

---

### 🛠️ Step 5.3: Hands-On - Dry Run (30 min)

**EXPERIMENT**: Understand the deployment process without actually deploying.

**Don't Run These** (they cost money), but understand what they do:

```bash
cd deployment/ecs

# Show help
./deploy.sh --help

# Expected output:
# Usage: ./deploy.sh [setup|build|deploy|test|teardown]
# ...
```

**Examine AWS Commands** (what would run):
```bash
# Look at the actual AWS CLI commands
grep "aws " deploy.sh | head -30

# Example commands you'd see:
# aws ec2 create-vpc --cidr-block 10.0.0.0/16
# aws ecs create-cluster --cluster-name epic8-cluster
# aws ecr create-repository --repository-name epic8/api-gateway
# aws ecs register-task-definition --cli-input-json file://task-def.json
# aws ecs create-service --cluster epic8-cluster --service-name api-gateway
```

**Understand the Deployment Flow**:
```bash
# Create a deployment flow diagram
cat > deployment_flow.txt << 'EOF'
Deployment Flow to AWS ECS
==========================

1. SETUP (10-15 min)
   ├─ Create VPC and networking (3 min)
   ├─ Create ECS cluster (2 min)
   ├─ Create ECR repositories (2 min)
   ├─ Create IAM roles (2 min)
   ├─ Create ALB (3 min)
   └─ Store secrets (1 min)

2. BUILD (15-20 min)
   ├─ Build all Docker images (10 min)
   ├─ Tag images for ECR (1 min)
   └─ Push to ECR (5 min)

3. DEPLOY (5-10 min)
   ├─ Register task definitions (2 min)
   ├─ Create ECS services (3 min)
   └─ Wait for healthy (5 min)

4. TEST (2-5 min)
   ├─ Get ALB DNS name
   ├─ Test health checks
   └─ Send test query

Total: 30-40 minutes
EOF

cat deployment_flow.txt
```

**Create Your Pre-Deployment Checklist**:
```bash
cat > AWS_DEPLOYMENT_CHECKLIST.md << 'EOF'
# AWS ECS Deployment Checklist

## Before Deploying

Prerequisites:
- [ ] AWS account with $100 credit
- [ ] AWS CLI installed and configured
- [ ] Docker installed and running
- [ ] All services tested locally (docker-compose up)
- [ ] Budget alerts set up in AWS
- [ ] HuggingFace API token obtained
- [ ] Ollama configured (for local tier)

## Pre-Deployment Validation

Test locally first:
```bash
# 1. Build all images
docker-compose build

# 2. Run locally
docker-compose up

# 3. Test all endpoints
curl http://localhost:8000/health
curl -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Test"}'

# 4. Verify logs look clean
docker-compose logs
```

## Deployment Steps

When ready to deploy:
```bash
cd deployment/ecs

# 1. Setup infrastructure (10-15 min)
./deploy.sh setup

# 2. Build and push images (15-20 min)
./deploy.sh build

# 3. Deploy services (5-10 min)
./deploy.sh deploy

# 4. Test deployment (2-5 min)
./deploy.sh test
```

## Post-Deployment

Monitoring:
- [ ] Check CloudWatch logs
- [ ] Verify all services healthy
- [ ] Run cost check: `./check-costs.sh`
- [ ] Set up daily cost alerts
- [ ] Test all query types (simple/medium/complex)

## Daily Monitoring

Run daily:
```bash
# Check costs
./check-costs.sh

# Check service health
aws ecs describe-services --cluster epic8-cluster

# View logs
aws logs tail /ecs/epic8 --follow
```

## Teardown (When Done)

To avoid ongoing charges:
```bash
# Delete all resources
./deploy.sh teardown

# Verify everything deleted
aws ecs list-clusters
aws ec2 describe-vpcs --filters "Name=tag:Project,Values=epic8"

# Check final costs
./check-costs.sh
```

## Cost Expectations

Daily: $3.20
- ECS Fargate: $2.48
- ALB: $0.62
- Data transfer: $0.10

30 days: $96.00 (within $100 budget)

## Troubleshooting

If services fail to start:
1. Check CloudWatch logs
2. Verify security groups
3. Check IAM role permissions
4. Validate task definitions
5. Check ECR image availability

Common issues:
- "Task failed to start": Check memory/CPU limits
- "Health check failed": Check service ports
- "Cannot pull image": Check ECR permissions
EOF

cat AWS_DEPLOYMENT_CHECKLIST.md
```

**✅ Checkpoint Questions**:
- [ ] Do you understand the ECS architecture?
- [ ] Can you explain why ECS is cheaper than EKS?
- [ ] Do you understand the deployment phases?
- [ ] Have you created a deployment checklist?
- [ ] Do you know how to monitor costs?

---

## 🎯 Layer 6: Putting It All Together (1 hour)

### Step 6.1: Create Your Own Summary (30 min)

**ACTION**: Write your understanding in your own words.

```bash
cat > MY_EPIC8_UNDERSTANDING.md << 'EOF'
# My Epic 8 Understanding

**Date**: $(date +%Y-%m-%d)

## What Problem Does Epic 8 Solve?

[Write in your own words - why microservices? why cloud?]

## Architecture Explanation (For Interviews)

"Epic 8 is a cloud-native microservices architecture that decomposes the RAG system into 6 independent services..."

[Your explanation here]

## The 6 Services

1. **API Gateway** (Port 8000)
   - What: [Your description]
   - Why: [Why separate?]
   - Key code: services/api-gateway/main.py

2. **Query Analyzer** (Port 8001)
   - What: [Your description]
   - Why: [Why separate?]
   - Connects to: Epic 1 complexity classifier

3. **Generator** (Port 8002)
   - What: [Your description]
   - Why: [Why separate?]
   - Connects to: Epic 1 multi-model routing

4. **Retriever** (Port 8004)
   - What: [Your description]
   - Why: [Why separate?]
   - Connects to: Epic 2 advanced retrieval

5. **Analytics** (Port 8003)
   - What: [Your description]
   - Why: [Why separate?]
   - Stores: Metrics, costs, performance data

6. **Cache** (Redis)
   - What: [Your description]
   - Why: [Why separate?]
   - Benefit: Speed + cost reduction

## How They Communicate

[Your explanation of HTTP/REST, service discovery, etc.]

## Deployment Options (and when to use each)

| Option | Use When | Cost | Complexity |
|--------|----------|------|------------|
| Docker Compose | Development, testing | FREE | Low |
| Kind (local K8s) | Learning K8s, testing | FREE | Medium |
| AWS ECS Fargate | Production, demos | $3.20/day | Low |
| AWS EKS | Enterprise, full K8s | $120+/month | High |

## Why Microservices?

Benefits:
1. [Your point]
2. [Your point]
3. [Your point]

Trade-offs:
1. [Your point]
2. [Your point]

## Cost Optimization Strategy

"The key insight is using ECS Fargate instead of Kubernetes..."

[Your explanation of the $3.20/day architecture]

## My Demo Flow (5-10 minutes)

1. **Introduction** (1 min)
   - "I built a cloud-native RAG platform..."
   - [Your opening]

2. **Architecture Diagram** (2 min)
   - Show the 6 services
   - Explain communication flow

3. **Live Demo** (5 min)
   - docker-compose up
   - Show request flowing through services
   - Demonstrate scaling

4. **Cloud Deployment** (2 min)
   - Show AWS ECS architecture
   - Explain cost optimization
   - Show IaC (deployment scripts)

## Key Files I Need to Know

**For Demo**:
- docker-compose.yml
- services/*/main.py
- deployment/ecs/deploy.sh

**For Deep Dive**:
- k8s/*.yaml
- terraform/modules/
- docs/deployment/aws-ecs/deployment-plan.md

## Questions I Can Answer

- [x] What are the 6 services?
- [x] How do they communicate?
- [x] Why microservices vs monolith?
- [x] How does deployment work?
- [x] Why is ECS cheaper than EKS?
- [x] How do you scale services?
- [x] What happens if one service fails?
- [x] How do you monitor in production?

## Questions I Still Have

- [ ] [Your questions]

## Next Steps

- [ ] Practice the demo
- [ ] Create architecture diagrams
- [ ] Test actual AWS deployment (when ready)
- [ ] Add to portfolio
EOF
```

Now **fill it out** with your own words!

---

### Step 6.2: Create Your Demo Script (30 min)

```bash
cat > my_epic8_demo.sh << 'DEMO'
#!/bin/bash
# My Epic 8 Demo - 5-10 minute demo script

set -e  # Exit on error

echo "═══════════════════════════════════════════════════════════"
echo "  Epic 8: Cloud-Native Multi-Model RAG Platform"
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "Demonstrating: Microservices architecture with intelligent"
echo "model routing and cost-optimized cloud deployment"
echo ""
echo "Press Enter to continue..."
read

# Part 1: Show architecture
echo ""
echo "━━━ Part 1: Architecture Overview ━━━"
echo ""
echo "6 Independent Microservices:"
echo "  1. API Gateway      - Request routing and orchestration"
echo "  2. Query Analyzer   - Epic 1 complexity classification"
echo "  3. Generator        - Epic 1 multi-model answer generation"
echo "  4. Retriever        - Epic 2 advanced retrieval"
echo "  5. Analytics        - Metrics and cost tracking"
echo "  6. Cache (Redis)    - Performance optimization"
echo ""
echo "Press Enter to start services..."
read

# Part 2: Start services
echo ""
echo "━━━ Part 2: Starting Services (Docker Compose) ━━━"
echo ""
docker-compose up -d
echo ""
echo "Waiting for services to be ready..."
sleep 10

# Part 3: Health checks
echo ""
echo "━━━ Part 3: Verifying All Services Healthy ━━━"
echo ""
for port in 8000 8001 8002 8003 8004; do
    SERVICE=$(curl -s http://localhost:${port}/health | jq -r '.service')
    STATUS=$(curl -s http://localhost:${port}/health | jq -r '.status')
    echo "  ✓ Port $port: $SERVICE ($STATUS)"
done
echo ""
echo "Press Enter to send queries..."
read

# Part 4: Simple query
echo ""
echo "━━━ Part 4: Testing Simple Query (Should Use Ollama - FREE) ━━━"
echo ""
echo "Query: 'What is Python?'"
echo ""
RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What is Python?"}')

echo "$RESPONSE" | jq '{
  model: .metadata.model_used,
  cost: .metadata.cost,
  answer_preview: .answer[:200]
}'

echo ""
echo "Expected: model = ollama/llama3.2, cost = $0.000"
echo ""
echo "Press Enter to send complex query..."
read

# Part 5: Complex query
echo ""
echo "━━━ Part 5: Testing Complex Query (Should Use GPT-OSS) ━━━"
echo ""
echo "Query: 'Comprehensive analysis of distributed systems...'"
echo ""
RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Provide a comprehensive analysis of distributed consensus protocols including Raft and Paxos, with implications for CAP theorem"}')

echo "$RESPONSE" | jq '{
  model: .metadata.model_used,
  cost: .metadata.cost,
  answer_preview: .answer[:200]
}'

echo ""
echo "Expected: model = gpt-oss-20b or mistral, cost > $0.001"
echo ""
echo "Press Enter to view metrics..."
read

# Part 6: Metrics
echo ""
echo "━━━ Part 6: System Metrics ━━━"
echo ""
curl -s http://localhost:8003/metrics | jq '{
  total_queries: .total_queries,
  average_latency: .average_latency,
  model_distribution: .model_distribution,
  total_cost: .total_cost
}'

echo ""
echo "Press Enter to show scaling..."
read

# Part 7: Scaling demo
echo ""
echo "━━━ Part 7: Demonstrating Scaling ━━━"
echo ""
echo "Scaling generator service to 3 instances..."
docker-compose up -d --scale generator=3
sleep 5

echo ""
docker-compose ps | grep generator
echo ""
echo "3 generator instances now running for load balancing"
echo ""
echo "Press Enter to view deployment options..."
read

# Part 8: Cloud deployment
echo ""
echo "━━━ Part 8: Cloud Deployment Options ━━━"
echo ""
echo "Local (Docker Compose):"
echo "  Cost: FREE"
echo "  Use: Development, testing"
echo ""
echo "AWS ECS Fargate (RECOMMENDED):"
echo "  Cost: $3.20/day = 31 days on $100 budget"
echo "  Use: Production demos, portfolio"
echo "  Deploy: ./deployment/ecs/deploy.sh setup && build && deploy"
echo ""
echo "AWS EKS (Full Kubernetes):"
echo "  Cost: $120+/month"
echo "  Use: Enterprise production"
echo ""
echo "Press Enter to finish..."
read

# Cleanup
echo ""
echo "━━━ Demo Complete! ━━━"
echo ""
echo "Stopping services..."
docker-compose down

echo ""
echo "═══════════════════════════════════════════════════════════"
echo "  Key Achievements:"
echo "  • 6-service microservices architecture"
echo "  • Independent scaling and deployment"
echo "  • 88% cost reduction vs GPU approach"
echo "  • Production-ready with IaC"
echo "═══════════════════════════════════════════════════════════"
DEMO

chmod +x my_epic8_demo.sh
```

**Test Your Demo**:
```bash
./my_epic8_demo.sh
```

---

## 📊 Final Validation

After completing all layers, test yourself:

### Comprehension Check

**Architecture** (can you answer these?):
- [ ] What are the 6 microservices and what does each do?
- [ ] Why separate Query Analyzer from Generator?
- [ ] How do services discover each other?
- [ ] What's the benefit of microservices vs monolith?

**Communication** (can you explain?):
- [ ] How does a request flow through all services?
- [ ] What happens if one service crashes?
- [ ] How is service discovery different in Docker vs K8s?
- [ ] What's the role of the API Gateway?

**Deployment** (do you understand?):
- [ ] What's the difference between Docker Compose, K8s, and ECS?
- [ ] Why is ECS Fargate recommended for $100 budget?
- [ ] What are the deployment phases?
- [ ] How do you scale a service in each environment?

**Operations** (can you do it?):
- [ ] Run all services locally with Docker Compose
- [ ] Deploy to local K8s (Kind)
- [ ] View logs from a specific service
- [ ] Scale a service up and down
- [ ] Debug a failing service
- [ ] Monitor costs in AWS

### Hands-On Validation

**Run these commands confidently**:
```bash
# Local development
docker-compose up
docker-compose logs -f api-gateway
docker-compose scale generator=3
docker-compose down

# Kubernetes
kubectl apply -f k8s/
kubectl get pods
kubectl logs -f deployment/api-gateway
kubectl scale deployment query-analyzer --replicas=3
kubectl delete -f k8s/

# AWS (when ready)
cd deployment/ecs
./deploy.sh setup
./deploy.sh build
./deploy.sh deploy
./check-costs.sh
./deploy.sh teardown
```

---

## 🎓 Learning Complete!

You now understand:
- ✅ Microservices architecture (why and how)
- ✅ Service communication patterns
- ✅ Docker and containerization
- ✅ Kubernetes fundamentals
- ✅ AWS ECS deployment
- ✅ Cost optimization strategies
- ✅ How to demo the system

**Portfolio-Ready Artifacts**:
1. Working demo script (`my_epic8_demo.sh`)
2. Personal understanding doc (`MY_EPIC8_UNDERSTANDING.md`)
3. Deployment checklist (`AWS_DEPLOYMENT_CHECKLIST.md`)
4. Hands-on experience (you've run it all)

**Interview-Ready**:
- You can explain the architecture
- You can demo it live
- You can discuss trade-offs
- You can answer deep technical questions

---

## 📖 Quick Reference

**Services & Ports**:
- API Gateway: 8000
- Query Analyzer: 8001
- Generator: 8002
- Analytics: 8003
- Retriever: 8004
- Redis: 6379

**Key Commands**:
```bash
# Local development
docker-compose up -d              # Start all services
docker-compose ps                 # Check status
docker-compose logs -f <service>  # View logs
docker-compose down               # Stop all

# Kubernetes
kubectl get pods                  # List pods
kubectl logs -f <pod>             # View logs
kubectl scale deployment <name>   # Scale service
kubectl describe pod <pod>        # Debug info

# AWS
./deploy.sh [setup|build|deploy]  # Deploy to AWS
./check-costs.sh                  # Monitor costs
```

**Key Files**:
- `docker-compose.yml` - Local orchestration
- `services/*/main.py` - Service implementations
- `k8s/*.yaml` - Kubernetes manifests
- `deployment/ecs/deploy.sh` - AWS automation
- `docs/deployment/aws-ecs/deployment-plan.md` - Complete guide

---

**Next Steps**: Run your demo, add to portfolio, prepare for interviews! 🚀
