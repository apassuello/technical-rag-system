# Epic 1, 2 & 8 Quick Reference Card

**Keep this handy for quick lookups!**

---

## 🎯 The Three Epics

| Epic | What It Does | Key Achievement | Time to Learn |
|------|-------------|-----------------|---------------|
| **Epic 1** | Multi-model intelligence | 99.5% accuracy, <$0.001/query | 1-2 hours (refresh) |
| **Epic 2** | Advanced retrieval | 48.7% MRR improvement | 1-2 hours (refresh) |
| **Epic 8** | Cloud microservices | $3.20/day deployment | 8-10 hours (learn) |

---

## 📘 Epic 1: Multi-Model Intelligence

### What It Does
Query complexity classifier → Adaptive model routing → Cost optimization

### The Flow
```
Query → Analyze Complexity → Route to Model
        (5D analysis)        • Simple → Ollama (FREE)
        99.5% accuracy       • Medium → Mistral ($)
                            • Complex → GPT-OSS ($$)
```

### Key Files
- `src/components/generators/epic1_answer_generator.py`
- `src/components/analyzers/`
- `models/epic1/` (trained classifiers)

### Quick Test
```bash
python << 'EOF'
from src.core.platform_orchestrator import PlatformOrchestrator
orch = PlatformOrchestrator('config/default.yaml')
result = orch.process_query('What is Python?')
print(f"Model: {result.get('model_used')}, Cost: ${result.get('cost')}")
EOF
```

---

## 📗 Epic 2: Advanced Retrieval

### What It Does
Multi-strategy retrieval: Vector + BM25 → Fusion → Reranking

### The Flow
```
Query → Parallel Retrieval → Fusion → Rerank → Top Results
        • FAISS (semantic)     RRF     Neural    48.7% MRR
        • BM25 (keyword)              Cross-Encoder  improvement
```

### Key Files
- `src/components/retrievers/modular_unified_retriever.py`
- `src/components/retrievers/fusion_strategies/`
- `src/components/retrievers/rerankers/`

### Quick Test
```bash
pytest tests/epic2_validation/test_epic2_quality_validation_new.py -v
```

---

## 📙 Epic 8: Cloud Microservices

### What It Does
6-service microservices architecture with cloud deployment

### The Services
```
1. API Gateway (8000)      - Orchestration
2. Query Analyzer (8001)   - Epic 1 complexity
3. Generator (8002)        - Epic 1 multi-model
4. Retriever (8004)        - Epic 2 retrieval
5. Analytics (8003)        - Metrics tracking
6. Cache (6379)           - Redis performance
```

### Key Files
- `docker-compose.yml` - Local orchestration
- `services/*/main.py` - Service implementations
- `k8s/*.yaml` - Kubernetes deployment
- `deployment/ecs/deploy.sh` - AWS automation

### Quick Start
```bash
# Local development
docker-compose up -d
curl http://localhost:8000/health

# Test query
curl -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What is Python?"}'

# Stop
docker-compose down
```

---

## ⚡ Common Commands

### Epic 1 & 2 (Refresh)
```bash
# Run refresher
cat EPIC1_EPIC2_REFRESHER.md

# Quick test Epic 1
pytest tests/epic1/integration/test_epic1_end_to_end.py -v

# Quick test Epic 2
pytest tests/epic2_validation/test_epic2_performance_validation_new.py -v
```

### Epic 8 (Learn)
```bash
# Follow learning plan
cat EPIC8_LEARNING_PLAN.md

# Run demo
./my_epic8_demo.sh

# Start services
docker-compose up -d

# View logs
docker-compose logs -f api-gateway

# Stop services
docker-compose down
```

---

## 🐳 Docker Compose Quick Reference

```bash
# Start all services
docker-compose up -d

# View status
docker-compose ps

# View logs (all)
docker-compose logs -f

# View logs (one service)
docker-compose logs -f api-gateway

# Restart one service
docker-compose restart generator

# Scale a service
docker-compose up -d --scale generator=3

# Stop all
docker-compose down

# Stop and remove volumes
docker-compose down -v

# Rebuild images
docker-compose build
docker-compose up -d --build
```

---

## ☸️ Kubernetes Quick Reference

```bash
# Create local cluster (Kind)
kind create cluster --name epic8-dev

# Load images
kind load docker-image epic8-api-gateway:latest --name epic8-dev

# Deploy
kubectl apply -f k8s/

# Check status
kubectl get pods
kubectl get services

# View logs
kubectl logs -f deployment/api-gateway

# Scale
kubectl scale deployment query-analyzer --replicas=3

# Port forward
kubectl port-forward service/api-gateway 8000:8000

# Describe (debug)
kubectl describe pod <pod-name>

# Exec into pod
kubectl exec -it <pod-name> -- /bin/bash

# Delete
kubectl delete -f k8s/

# Delete cluster
kind delete cluster --name epic8-dev
```

---

## ☁️ AWS ECS Quick Reference

```bash
cd deployment/ecs

# Deploy to AWS (costs money!)
./deploy.sh setup     # Creates infrastructure
./deploy.sh build     # Builds and pushes images
./deploy.sh deploy    # Creates services
./deploy.sh test      # Validates deployment

# Monitor costs
./check-costs.sh

# Teardown (important!)
./deploy.sh teardown  # Deletes everything
```

---

## 📊 Service Ports

| Service | Port | URL |
|---------|------|-----|
| API Gateway | 8000 | http://localhost:8000 |
| Query Analyzer | 8001 | http://localhost:8001 |
| Generator | 8002 | http://localhost:8002 |
| Analytics | 8003 | http://localhost:8003 |
| Retriever | 8004 | http://localhost:8004 |
| Redis | 6379 | redis://localhost:6379 |

---

## 🧪 Quick Tests

### Health Check All Services
```bash
for port in 8000 8001 8002 8003 8004; do
  curl -s http://localhost:${port}/health | jq .
done
```

### Test Simple Query (Ollama)
```bash
curl -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What is Python?"}' | jq .
```

### Test Complex Query (GPT-OSS)
```bash
curl -X POST http://localhost:8000/api/v1/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Comprehensive analysis of distributed systems"}' | jq .
```

### View Metrics
```bash
curl -s http://localhost:8003/metrics | jq .
```

---

## 🎓 Learning Paths

### Already Know Epic 1 & 2?
→ Start with: `EPIC1_EPIC2_REFRESHER.md` (2-3 hours)

### New to Epic 8?
→ Start with: `EPIC8_LEARNING_PLAN.md` (8-10 hours)
→ Layer by layer: Big Picture → Communication → Docker → K8s → AWS

### Want to Demo?
→ Run: `./my_epic8_demo.sh`
→ Fill out: `MY_EPIC8_UNDERSTANDING_TEMPLATE.md`

---

## 💰 Cost Comparison

| Deployment | Daily Cost | 30-Day Cost | $100 Runtime |
|------------|-----------|-------------|--------------|
| Docker Compose (local) | $0 | $0 | ∞ |
| AWS ECS Fargate | $3.20 | $96 | 31 days ✅ |
| AWS EKS | $13.35 | $400+ | 7.5 days |
| GPU Always-On | $26 | $780+ | 3.8 days |

**Winner**: ECS Fargate (31 days on $100 budget)

---

## 🎯 Portfolio Talking Points

### Epic 1
"Built ML-based query classifier with 99.5% accuracy, enabling intelligent model routing that achieves <$0.001 per query"

### Epic 2
"Implemented multi-strategy retrieval with 48.7% MRR improvement through vector+BM25 fusion and neural reranking"

### Epic 8
"Architected cloud-native microservices deployment with 88% cost reduction, achieving 31 days runtime on $100 budget"

---

## 📁 Key Documentation

### Epic 1 & 2
- `EPIC1_EPIC2_REFRESHER.md` - Refresh guide
- `docs/epic1/architecture/EPIC1_SYSTEM_ARCHITECTURE.md`
- `docs/architecture/components/component-4-retriever.md`

### Epic 8
- `EPIC8_LEARNING_PLAN.md` - Complete learning plan
- `MY_EPIC8_UNDERSTANDING_TEMPLATE.md` - Personal notes template
- `docs/epic8/EPIC8_MICROSERVICES_ARCHITECTURE.md`
- `docs/deployment/aws-ecs/deployment-plan.md`

### Demos
- `my_epic8_demo.sh` - Automated demo script
- `docs/demos/epic8/README.md` - Demo guide

---

## 🆘 Quick Troubleshooting

### Services Won't Start
```bash
# Check if ports are in use
lsof -i :8000
lsof -i :8001

# Kill processes using ports
kill -9 $(lsof -t -i:8000)

# Restart Docker
docker-compose down
docker-compose up -d
```

### Can't Connect to Service
```bash
# Check service status
docker-compose ps

# Check logs
docker-compose logs service-name

# Restart service
docker-compose restart service-name
```

### Images Won't Build
```bash
# Clean Docker
docker system prune -a

# Rebuild from scratch
docker-compose build --no-cache
```

---

## ✅ Quick Checklist

### Before Demos:
- [ ] All dependencies installed (`pip install -r requirements.txt`)
- [ ] Docker running
- [ ] Services start successfully (`docker-compose up -d`)
- [ ] All health checks pass
- [ ] Test queries work
- [ ] Demo script runs end-to-end (`./my_epic8_demo.sh`)

### Before AWS Deployment:
- [ ] Tested locally with Docker Compose
- [ ] AWS CLI configured
- [ ] Budget alerts set up
- [ ] API keys ready (HuggingFace, etc.)
- [ ] Read deployment checklist (`AWS_DEPLOYMENT_CHECKLIST.md`)

---

**Last Updated**: Auto-generated
**Quick Start**: Run `./my_epic8_demo.sh`
**Full Learning**: Follow `EPIC8_LEARNING_PLAN.md`
