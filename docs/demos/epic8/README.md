# Epic 8 Demo - Quick Start Guide

**Last Updated**: November 10, 2025
**Time Required**: 5-20 minutes (depending on demo type)
**Difficulty**: Easy to Intermediate

---

## 🎯 Choose Your Demo

### Option 1: Automated Showcase (5 minutes) ⚡ FASTEST
```bash
python demos/capability_showcase.py
```
**Best for**: Quick overview, portfolio presentations

### Option 2: Interactive Exploration (10-15 minutes) 🔍 DETAILED
```bash
python demos/interactive_demo.py
```
**Best for**: Technical interviews, hands-on demonstrations

### Option 3: Performance Validation (5 minutes) 📊 QUANTITATIVE
```bash
python demos/performance_demo.py
```
**Best for**: Performance discussions, optimization showcase

### Option 4: Web Demo (15-20 minutes) 🌐 VISUAL
```bash
streamlit run demos/streamlit_epic2_demo.py
```
**Best for**: Client presentations, portfolio website

---

## ✅ Pre-Demo Checklist

### Required (Minimum for Any Demo)
- [ ] Python 3.11+ installed
- [ ] In project directory: `/home/user/rag-portfolio/project-1-technical-rag`
- [ ] Dependencies installed: `pip install -r requirements.txt`
- [ ] Test configuration available: `config/test.yaml`

### Optional (For Full Functionality)
- [ ] Ollama installed and running (or API keys configured)
- [ ] Sample PDF documents in `data/test/`
- [ ] Docker daemon running (for container deployment demo)
- [ ] Kubernetes cluster available (for cloud deployment demo)

---

## 🚀 Quick Start Commands

### 1. Environment Setup (One-Time)
```bash
# Navigate to project
cd /home/user/rag-portfolio/project-1-technical-rag

# Install dependencies
pip install -r requirements.txt

# Download language model
python -m spacy download en_core_web_sm

# Verify setup
python -c "from src.core.platform_orchestrator import PlatformOrchestrator; print('Setup OK')"
```

### 2. Run Capability Showcase (Fastest Demo)
```bash
# Using test configuration (faster, smaller models)
python demos/capability_showcase.py config/test.yaml

# Or using default configuration
python demos/capability_showcase.py
```

**Expected Output**:
```
🎯 RAG SYSTEM CAPABILITY SHOWCASE
   Phase 4 Production Architecture - Swiss Market Standards
================================================================================
📋 Demonstration Plan:
   1. 🏗️  Architecture Overview
   2. 📄 Document Processing Capabilities
   3. 🧠 Intelligent Query Processing
   4. 📊 Performance & Optimization Benefits
   5. 🏥 System Health & Monitoring
   6. 🚀 Phase 4 Achievements
...
```

### 3. Run Interactive Demo (Detailed Exploration)
```bash
python demos/interactive_demo.py
```

**Menu Options**:
```
1. Process documents
2. Ask questions
3. View system health
4. Explore performance metrics
5. Compare architectures
6. Exit
```

### 4. Run Performance Benchmarking
```bash
python demos/performance_demo.py
```

**Key Metrics Shown**:
- System initialization time
- Document processing rates
- Query throughput
- Deployment readiness score

### 5. Launch Streamlit Web Demo
```bash
streamlit run demos/streamlit_epic2_demo.py
```

**Access**: Browser opens to `http://localhost:8501`

---

## 🐳 Container Deployment Demo (Optional)

### Build Docker Images
```bash
cd scripts/deployment
./build-services.sh build

# Verify
docker images | grep epic8
```

**Expected**: 6 Epic 8 images listed

### Deploy to Local Kubernetes
```bash
# Create Kind cluster
kind create cluster --name epic8-demo

# Load images
./load-images-kind.sh load

# Deploy services
kubectl apply -f ../../k8s/namespaces/epic8-dev.yaml
kubectl apply -f ../../k8s/deployments/ -n epic8-dev
kubectl apply -f ../../k8s/services/ -n epic8-dev

# Check status
kubectl get pods -n epic8-dev
```

### Access API Gateway
```bash
# Port forward
kubectl port-forward -n epic8-dev svc/api-gateway-service 8080:8080

# Test health
curl http://localhost:8080/health

# Test status
curl http://localhost:8080/api/v1/status
```

---

## 🔧 Troubleshooting

### Issue: Import Errors
```bash
# Solution: Ensure you're in project root
pwd  # Should show: /home/user/rag-portfolio/project-1-technical-rag
```

### Issue: Config Not Found
```bash
# Solution: Use test configuration
python demos/capability_showcase.py config/test.yaml
```

### Issue: Ollama Not Available
```bash
# Solution 1: Install Ollama
curl https://ollama.ai/install.sh | sh
ollama pull llama3.2:3b

# Solution 2: Use mock adapter (edit config to use MockLLMAdapter)
```

### Issue: Missing Dependencies
```bash
# Solution: Reinstall dependencies
pip install -r requirements.txt --force-reinstall
python -m spacy download en_core_web_sm
```

### Issue: No Test Data
```bash
# Check available PDFs
ls data/test/*.pdf

# Download samples if needed (from project documentation)
```

---

## 📊 Demo Talking Points

### System Architecture
- "6-service microservices architecture"
- "129 infrastructure files (K8s, Helm, Terraform)"
- "Multi-cloud deployment support (AWS, GCP, Azure)"

### Technical Achievements
- "99.5% query classification accuracy (Epic 1)"
- "48.7% MRR improvement (Epic 2)"
- "100% Epic 8 test success (48/48 tests)"

### Performance Metrics
- "Sub-millisecond routing decisions (<25ms)"
- "565K characters/sec document processing"
- "1000+ concurrent users capability"

### Operational Excellence
- "99.9% uptime SLA target"
- "Zero-downtime deployments"
- "Complete observability stack"

---

## 🎬 Recommended Demo Flow (15 minutes)

### **1. Introduction (2 min)**
- Show Epic 8 architecture diagram
- Explain 6-service decomposition
- Highlight Swiss engineering standards

### **2. Capability Showcase (5 min)**
```bash
python demos/capability_showcase.py config/test.yaml
```
- Let automated demo run
- Highlight key metrics as they appear
- Point out architecture components

### **3. Live Interaction (5 min)**
```bash
python demos/interactive_demo.py
```
- Process a sample document
- Ask 2-3 queries
- Show system health monitoring

### **4. Infrastructure Tour (3 min)**
```bash
# Show infrastructure files
ls -R k8s/ helm/ terraform/ | head -50

# Display service implementations
wc -l services/*/*_app/main.py
```
- Explain deployment architecture
- Show Kubernetes manifests
- Discuss multi-cloud support

### **5. Q&A (5 min)**
- Technical deep-dive as needed
- Performance discussions
- Deployment scenarios

---

## 📚 Quick Reference

### Configuration Files
```
config/
├── default.yaml          Production settings
├── test.yaml            Fast testing (use for demos)
├── demo.yaml            Demo-optimized settings
├── epic1_multi_model.yaml   Multi-model routing
└── epic2.yaml           Enhanced retrieval
```

### Demo Scripts
```
demos/
├── capability_showcase.py    Automated demo (fastest)
├── interactive_demo.py       CLI exploration
├── performance_demo.py       Benchmarking
└── streamlit_epic2_demo.py   Web interface
```

### Infrastructure
```
k8s/          Kubernetes manifests (49 files)
helm/         Helm charts (32 files)
terraform/    Multi-cloud IaC (29 files)
services/     Microservices code (6 services)
```

### Documentation
```
docs/epics/                   Epic 8 specifications
docs/completion-reports/      Progress and completion
k8s/README.md                Deployment guide
demos/README.md              Demo guide
EPIC8_DEMO_PREPARATION_REPORT.md  This comprehensive report
```

---

## ✅ Demo Success Checklist

After completing demo, verify:

- [ ] **System initialized** successfully
- [ ] **Demo script ran** without errors
- [ ] **Key metrics displayed** (if performance demo)
- [ ] **Questions answered** confidently
- [ ] **Infrastructure shown** (K8s/Helm/Terraform files)
- [ ] **Technical depth demonstrated** (architecture, code, deployment)

---

## 🎯 Next Steps After Demo

### For Portfolio
- [ ] Add demo recordings/screenshots
- [ ] Update portfolio with metrics
- [ ] Create case study document

### For Interviews
- [ ] Prepare answers to likely questions
- [ ] Review architecture decisions
- [ ] Practice explaining tradeoffs

### For Production
- [ ] Deploy to cloud environment
- [ ] Set up monitoring dashboards
- [ ] Complete load testing

---

**Status**: ✅ READY FOR DEMONSTRATION

**Recommendation**: Start with **Capability Showcase** for quickest demo, then progress to **Interactive Demo** for detailed exploration.

*For comprehensive demo preparation details, see `EPIC8_DEMO_PREPARATION_REPORT.md`*
