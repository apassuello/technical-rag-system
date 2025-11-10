# Deployment Documentation

Complete deployment guides for Epic 8 RAG Platform across multiple environments.

---

## 📋 Available Deployment Options

### 1. [AWS ECS Fargate](./aws-ecs/) - **RECOMMENDED FOR $100 BUDGET**

**Best for**: Cost-optimized production deployment with $100 AWS credit

- **Cost**: $3.20/day (~31 days runtime)
- **Setup Time**: 30-40 minutes
- **Complexity**: Low (serverless, no K8s)
- **Features**:
  - 3-tier intelligent model routing
  - Zero GPU costs
  - Automated deployment scripts
  - Complete monitoring setup

📚 **Documentation**:
- [Quick Start Guide](./aws-ecs/README.md) - Get started in 30 minutes
- [Detailed Deployment Plan](./aws-ecs/deployment-plan.md) - Complete implementation guide with 11 diagrams

🚀 **Quick Deploy**:
```bash
cd deployment/ecs
./deploy.sh setup && ./deploy.sh build && ./deploy.sh deploy
```

---

### 2. [AWS EKS (Kubernetes)](./aws-eks/)

**Best for**: Production-grade deployment with full Kubernetes features

- **Cost**: $250-400/month (dev), $1,200-2,000/month (prod)
- **Setup Time**: 4-8 hours
- **Complexity**: High (full Kubernetes management)
- **Features**:
  - Multi-AZ high availability
  - Auto-scaling (HPA, VPA, Cluster Autoscaler)
  - GPU node groups for self-hosted models
  - Enterprise monitoring (Prometheus + Grafana)

📚 **Documentation**:
- [EKS Deployment Plan](./aws-eks/deployment-plan.md) - Complete Terraform + Helm setup

⚠️ **Note**: Requires more AWS budget and Kubernetes expertise

---

### 3. [Local Development (Docker)](./local/)

**Best for**: Local testing and development

- **Cost**: FREE
- **Setup Time**: 10 minutes
- **Complexity**: Very Low
- **Features**:
  - Docker Compose setup
  - Hot reload for development
  - Easy debugging

📚 **Documentation**:
- [Docker Deployment Guide](./DOCKER_DEPLOYMENT_GUIDE.md)
- [Docker Implementation Complete](./DOCKER_IMPLEMENTATION_COMPLETE.md)
- [Docker Quick Reference](./DOCKER_QUICK_REFERENCE.md)

🚀 **Quick Start**:
```bash
# Build all services
./docker-setup.sh

# Validate Epic 8 deployment
./validate-epic8-build.sh

# Start services
docker-compose up
```

---

## 🎯 Decision Matrix

| Criteria | ECS Fargate | EKS | Local Docker |
|----------|-------------|-----|--------------|
| **Budget** | $100 (31 days) | $250+ per month | FREE |
| **Setup Time** | 30-40 min | 4-8 hours | 10 min |
| **Production Ready** | ✅ Yes | ✅ Yes | ❌ No |
| **Scalability** | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐ |
| **Complexity** | Low | High | Very Low |
| **Kubernetes** | ❌ No | ✅ Yes | ❌ No |
| **Auto-scaling** | ✅ Yes | ✅ Advanced | ❌ No |
| **Monitoring** | ✅ CloudWatch | ✅ Prometheus | ❌ Basic |

---

## 📂 Deployment Scripts & Configuration

**Automation Scripts**:
- **ECS**: [`/deployment/ecs/`](../../deployment/ecs/)
  - `deploy.sh` - Main deployment automation (setup, build, deploy, teardown)
  - `check-costs.sh` - Cost monitoring and budget tracking
- **Docker**: Project root
  - `docker-setup.sh` - Build all Docker images
  - `validate-epic8-build.sh` - Validate Epic 8 services
  - `docker-compose.yml` - Local development stack

**Configuration Files**:
- [`/config/`](../../config/)
  - `epic1_ecs_deployment.yaml` - 3-tier model routing for ECS
  - Other environment-specific configs

---

## 📖 Related Documentation

- **Integration Guides**:
  - [GPT-OSS Integration](../integration/gpt-oss/) - OpenAI's open-source model setup
- **Demo Guides**:
  - [Epic 8 Demo](../demos/epic8/) - Demo preparation and execution guides
- **Architecture**:
  - [Architecture Documentation](../architecture/) - System design and components
  - [Epics](../epics/) - Feature specifications

---

## 🆘 Need Help?

**For AWS ECS Deployment**:
1. **Quick Start**: Go to [AWS ECS Quick Start](./aws-ecs/README.md)
2. **Detailed Guide**: See [ECS Deployment Plan](./aws-ecs/deployment-plan.md)
3. **Troubleshooting**: Check deployment-plan.md Troubleshooting section
4. **Cost Questions**: Run [`./deployment/ecs/check-costs.sh`](../../deployment/ecs/check-costs.sh)

**For Local Development**:
1. Follow [Docker Deployment Guide](./DOCKER_DEPLOYMENT_GUIDE.md)
2. Check [Docker Quick Reference](./DOCKER_QUICK_REFERENCE.md) for commands

---

## 💡 Recommendation

**For your $100 AWS credit**: Start with **AWS ECS Fargate** deployment
- Provides production-ready deployment
- Best cost optimization ($3.20/day = 31 days)
- Includes 3-tier intelligent model routing
- Complete monitoring and automation
- Professional documentation with 11 diagrams

**For local development**: Use Docker Compose
- FREE and fast setup
- Perfect for testing changes
- Hot reload during development
