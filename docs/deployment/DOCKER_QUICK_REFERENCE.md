# Epic 8 Docker Quick Reference Card

## 🚀 Quick Start Commands

### 1. Validate Setup
```bash
./validate-docker-setup.sh    # Validate Docker architecture
```

### 2. Complete Deployment (Recommended)
```bash
./docker-setup.sh check       # Pre-flight checks
./docker-setup.sh build       # Build all services  
./docker-setup.sh start       # Start all services
./docker-setup.sh status      # Check health
```

### 3. Manual Docker Commands (Advanced)
```bash
# Build individual services (from project root)
docker build -f services/query-analyzer/Dockerfile -t epic8/query-analyzer:latest .
docker build -f services/generator/Dockerfile -t epic8/generator:latest .

# Start with Docker Compose
docker-compose up -d
docker-compose logs -f query-analyzer
```

## 📋 Service Reference

| Service | Port | Health Check | Purpose |
|---------|------|--------------|---------|
| **api-gateway** | 8080 | `curl localhost:8080/health` | Request routing |
| **query-analyzer** | 8082 | `curl localhost:8082/health/live` | Query analysis |
| **generator** | 8081 | `curl localhost:8081/health/live` | Answer generation |
| **retriever** | 8083 | `curl localhost:8083/health/live` | Document retrieval |
| **cache** | 8084 | `curl localhost:8084/health/live` | Response caching |
| **analytics** | 8085 | `curl localhost:8085/health/live` | Metrics & monitoring |

## 🔧 Troubleshooting Commands

```bash
# Check container status
./docker-setup.sh status

# View service logs
./docker-setup.sh logs query-analyzer
./docker-setup.sh logs generator -f    # Follow logs

# Stop specific services
./docker-setup.sh stop cache analytics

# Clean up everything
./docker-setup.sh cleanup
```

## ✅ Architecture Validation Checklist

- [ ] **Docker installed**: `docker --version`
- [ ] **Docker Compose available**: `docker-compose --version`
- [ ] **No sudo required**: `docker ps` works without sudo
- [ ] **Epic 1 components present**: `ls src/components/`
- [ ] **All Dockerfiles exist**: `ls services/*/Dockerfile`
- [ ] **Validation passes**: `./validate-docker-setup.sh`

## 🏗️ Build Context Architecture

**Key Implementation**: All services use **project root (`.`) as build context**

```yaml
# docker-compose.yml
services:
  service-name:
    build:
      context: .  # ✅ Project root context
      dockerfile: services/service-name/Dockerfile
```

```dockerfile  
# services/*/Dockerfile
# Copy Epic 1 components (available due to project root build context)
COPY --chown=appuser:appuser src/ ./src/
COPY --chown=appuser:appuser config/ ./config/

# Copy service-specific application code
COPY --chown=appuser:appuser services/SERVICE_NAME/app/ ./app/
```

## 🚨 Common Issues & Quick Fixes

| Issue | Quick Fix |
|-------|-----------|
| `permission denied` for Docker | `sudo usermod -aG docker $USER` then logout/login |
| Port already in use | `lsof -i :8080` to find process, kill or change port |
| Build fails with "COPY failed" | Verify running from project root directory |
| Service won't start | Check logs: `./docker-setup.sh logs SERVICE_NAME` |
| Epic 1 components not found | Verify `src/` and `config/` directories exist |

## 📁 File Structure Summary

```
project-1-technical-rag/           # ← Build from here (project root)
├── docker-compose.yml             # ✅ Orchestration config
├── docker-setup.sh               # ✅ New management script
├── validate-docker-setup.sh      # ✅ Architecture validation
├── build-services.sh             # ✅ Legacy build script
├── src/                           # ✅ Epic 1 components (accessible to all services)
├── config/                        # ✅ Epic 1 config (accessible to all services)
└── services/                      # ✅ Service implementations
    ├── api-gateway/Dockerfile     # ✅ Multi-stage build with Epic 1 access
    ├── query-analyzer/Dockerfile  # ✅ Multi-stage build with Epic 1 access
    ├── generator/Dockerfile       # ✅ Multi-stage build with Epic 1 access
    ├── retriever/Dockerfile       # ✅ Multi-stage build with Epic 1 access
    ├── cache/Dockerfile           # ✅ Multi-stage build with Epic 1 access
    └── analytics/Dockerfile       # ✅ Multi-stage build with Epic 1 access
```

## 🎯 Next Steps After Deployment

1. **Verify Epic 1 Integration**:
   ```bash
   docker exec -it epic8_generator python -c "from src.components.answer_generators.epic1_answer_generator import Epic1AnswerGenerator; print('Epic1 OK')"
   ```

2. **Test End-to-End**:
   ```bash
   curl -X POST http://localhost:8080/query \
        -H "Content-Type: application/json" \
        -d '{"query": "test query", "max_results": 5}'
   ```

3. **Monitor Health**:
   ```bash
   watch './docker-setup.sh status'
   ```

## 🏆 Success Criteria

✅ **Architecture Implemented**: All services can access Epic 1 components  
✅ **Build Context Fixed**: Project root context enables Epic 1 integration  
✅ **Automation Ready**: Comprehensive management scripts provided  
✅ **Health Monitoring**: All services have health checks  
✅ **Port Management**: No conflicts, all services properly allocated  

**Status**: **READY FOR DEPLOYMENT** 🚀

---
*Epic 8 Cloud-Native Multi-Model RAG Platform - Docker Architecture Complete*