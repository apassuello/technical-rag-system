# Weaviate Setup Guide for Epic 2 RAG System

This guide provides complete setup instructions for Weaviate, the vector database used in Epic 2's Advanced Hybrid Retriever system.

## Overview

Epic 2 extends the RAG system with advanced retrieval capabilities including:
- **Multi-backend support**: FAISS (local) + Weaviate (cloud-ready)
- **Hybrid search**: Dense + sparse + graph retrieval
- **Neural reranking**: Cross-encoder model optimization
- **Hot-swapping**: Dynamic backend switching for production

## Prerequisites

### System Requirements
- **Docker**: Version 20.10+ with Docker Compose
- **Memory**: Minimum 4GB RAM (8GB+ recommended)
- **Storage**: 10GB+ free space for Weaviate data
- **Python**: 3.11+ with Epic 2 dependencies

### Epic 2 Dependencies
```bash
# Core Epic 2 libraries (should already be installed)
pip install weaviate-client>=3.24.0
pip install networkx>=3.1
pip install plotly>=5.17.0
pip install dash>=2.14.0
```

## Quick Start (5 Minutes)

### 1. Start Weaviate Server
```bash
# From project root directory
cd /path/to/project-1-technical-rag

# Start Weaviate and Ollama services
docker-compose up -d

# Verify services are running
docker-compose ps
```

Expected output:
```
NAME           COMMAND                  SERVICE    STATUS     PORTS
rag_ollama     "/bin/ollama serve"      ollama     Up         0.0.0.0:11434->11434/tcp
rag_weaviate   "/bin/weaviate"          weaviate   Up         0.0.0.0:8080->8080/tcp, 0.0.0.0:50051->50051/tcp
```

### 2. Validate Weaviate Connection
```bash
# Quick health check
curl http://localhost:8080/v1/.well-known/ready

# Expected response: {"status":"ok"}
```

### 3. Run Epic 2 Tests
```bash
# Test Epic 2 configuration with Weaviate
python epic2_comprehensive_integration_test.py

# Expected: All Epic 2 components operational with Weaviate backend
```

## Detailed Setup

### Docker Compose Configuration

The `docker-compose.yml` provides a complete Epic 2 environment:

```yaml
services:
  weaviate:
    image: semitechnologies/weaviate:1.23.7
    ports:
      - "8080:8080"    # REST API
      - "50051:50051"  # gRPC API
    environment:
      AUTHENTICATION_ANONYMOUS_ACCESS_ENABLED: 'true'
      DEFAULT_VECTORIZER_MODULE: 'none'  # We use custom embeddings
      PERSISTENCE_DATA_PATH: '/var/lib/weaviate'
```

**Key Features**:
- **Anonymous access**: Enabled for development/testing
- **Custom embeddings**: Uses sentence-transformers (not Weaviate's built-in)
- **Persistent storage**: Data survives container restarts
- **Health checks**: Automatic restart on failure

### Environment-Specific Setup

#### Development Environment
```bash
# Standard development setup
docker-compose up -d

# View real-time logs
docker-compose logs -f weaviate
```

#### Testing Environment
```bash
# Clean testing environment (reset data)
docker-compose down -v
docker-compose up -d

# Faster startup for CI/CD
docker-compose up -d --wait
```

#### Production Environment
```bash
# Use production-ready configuration
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Enable authentication and SSL
# (requires additional configuration)
```

## Configuration Integration

### Epic 2 Configuration Files

Update your Epic 2 config files to use Weaviate:

#### For Comprehensive Testing (`config/epic2_comprehensive_test.yaml`)
```yaml
retriever:
  type: "advanced"
  config:
    backends:
      primary_backend: "weaviate"  # Use Weaviate as primary
      fallback_backend: "faiss"   # FAISS fallback
      weaviate:
        connection:
          url: "http://localhost:8080"
          timeout: 30
        schema:
          class_name: "TechnicalDocument"
```

#### For Diagnostic Testing (`config/epic2_diagnostic_test.yaml`)
```yaml
retriever:
  type: "advanced"
  config:
    backends:
      primary_backend: "faiss"     # FAISS for speed
      fallback_backend: "weaviate" # Weaviate fallback
      enable_hot_swap: true        # Test backend switching
```

### Backend Switching Example
```python
# Switch to Weaviate during runtime
retriever.switch_to_backend("weaviate")

# Switch back to FAISS
retriever.switch_to_backend("faiss")

# Auto-failover (configured)
# System automatically switches on errors
```

## Validation and Testing

### Health Checks

```bash
# 1. Docker container health
docker-compose ps
docker health-check rag_weaviate

# 2. Weaviate API health
curl http://localhost:8080/v1/.well-known/ready
curl http://localhost:8080/v1/.well-known/live

# 3. Schema validation
curl http://localhost:8080/v1/schema
```

### Connection Testing Script

Create `scripts/test_weaviate_connection.py`:

```python
#!/usr/bin/env python3
"""Test Weaviate connection and Epic 2 integration."""

import weaviate
import sys
from pathlib import Path

def test_weaviate_connection():
    """Test basic Weaviate connectivity."""
    try:
        client = weaviate.Client("http://localhost:8080")
        
        # Test connection
        assert client.is_ready(), "Weaviate is not ready"
        print("✅ Weaviate connection successful")
        
        # Test schema access
        schema = client.schema.get()
        print(f"✅ Schema accessible: {len(schema.get('classes', []))} classes")
        
        return True
        
    except Exception as e:
        print(f"❌ Weaviate connection failed: {e}")
        return False

def test_epic2_integration():
    """Test Epic 2 Advanced Retriever with Weaviate."""
    sys.path.append(str(Path(__file__).parent.parent))
    
    try:
        from src.core.platform_orchestrator import PlatformOrchestrator
        
        # Test with Epic 2 configuration
        po = PlatformOrchestrator("config/epic2_comprehensive_test.yaml")
        retriever = po._components.get('retriever')
        
        # Verify Advanced Retriever
        assert type(retriever).__name__ == "AdvancedRetriever"
        print(f"✅ Epic 2 retriever created: {type(retriever).__name__}")
        
        # Test backend switching
        retriever.switch_to_backend("weaviate")
        print(f"✅ Switched to Weaviate: {retriever.active_backend_name}")
        
        retriever.switch_to_backend("faiss")
        print(f"✅ Switched to FAISS: {retriever.active_backend_name}")
        
        return True
        
    except Exception as e:
        print(f"❌ Epic 2 integration failed: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing Weaviate + Epic 2 Integration")
    print("="*50)
    
    weaviate_ok = test_weaviate_connection()
    epic2_ok = test_epic2_integration()
    
    if weaviate_ok and epic2_ok:
        print("\n🎉 All tests passed! Epic 2 + Weaviate ready.")
        sys.exit(0)
    else:
        print("\n💥 Some tests failed. Check configuration.")
        sys.exit(1)
```

### Performance Validation

```bash
# Test Epic 2 performance with Weaviate
python -c "
import time
from src.core.platform_orchestrator import PlatformOrchestrator

po = PlatformOrchestrator('config/epic2_comprehensive_test.yaml')

# Benchmark retrieval latency
start = time.time()
results = po.process_query('What is RISC-V instruction set architecture?')
latency = time.time() - start

print(f'Epic 2 + Weaviate latency: {latency*1000:.1f}ms')
print(f'Target: <700ms P95 (✅ if <700ms)')
"
```

## Troubleshooting

### Common Issues

#### 1. "Connection refused" Error
```bash
# Check if Docker is running
docker --version
docker-compose --version

# Check if Weaviate container is running
docker-compose ps
docker-compose logs weaviate
```

**Solution**: Start Docker and Weaviate:
```bash
docker-compose up -d
```

#### 2. "Port 8080 already in use"
```bash
# Check what's using port 8080
lsof -i :8080
```

**Solutions**:
```bash
# Option 1: Kill conflicting process
sudo kill -9 <PID>

# Option 2: Change Weaviate port in docker-compose.yml
ports:
  - "8081:8080"  # Use port 8081 instead

# Update config files to use new port
url: "http://localhost:8081"
```

#### 3. "Schema not found" Error
```bash
# Reset Weaviate schema and data
docker-compose down -v
docker-compose up -d

# Wait for Weaviate to be ready
sleep 30
curl http://localhost:8080/v1/.well-known/ready
```

#### 4. Epic 2 Configuration Validation Errors
```python
# Check configuration loading
from src.core.platform_orchestrator import PlatformOrchestrator

try:
    po = PlatformOrchestrator("config/epic2_comprehensive_test.yaml")
    print("✅ Configuration valid")
except Exception as e:
    print(f"❌ Configuration error: {e}")
```

### Performance Issues

#### Slow Startup
- **Cause**: Weaviate initialization on first run
- **Solution**: Wait 60-90 seconds for complete startup
- **Verification**: Check health endpoint repeatedly

#### High Memory Usage
```bash
# Monitor Docker memory usage
docker stats rag_weaviate

# Limit Weaviate memory (if needed)
# Add to docker-compose.yml:
deploy:
  resources:
    limits:
      memory: 2G
```

#### Slow Queries
- **Cause**: Cold start, no indexes
- **Solution**: Run warmup queries after startup
- **Optimization**: Use FAISS for speed-critical paths

### Logs and Debugging

```bash
# View Weaviate logs
docker-compose logs -f weaviate

# View all service logs
docker-compose logs -f

# Debug Epic 2 integration
python epic2_diagnostic_test.py --verbose

# Check Weaviate metrics
curl http://localhost:8080/v1/nodes
```

## Production Deployment

### Security Configuration

For production deployment, enable authentication:

```yaml
# docker-compose.prod.yml
environment:
  AUTHENTICATION_ANONYMOUS_ACCESS_ENABLED: 'false'
  AUTHENTICATION_APIKEY_ENABLED: 'true'
  AUTHENTICATION_APIKEY_ALLOWED_KEYS: 'your-secure-api-key'
  AUTHENTICATION_APIKEY_USERS: 'admin'
```

Update Epic 2 configuration:
```yaml
weaviate:
  connection:
    url: "http://your-weaviate-server:8080"
    api_key: "your-secure-api-key"
```

### Monitoring and Alerting

- **Health checks**: Built into docker-compose.yml
- **Metrics**: Use Prometheus + Grafana (optional)
- **Logging**: Centralized logging with ELK stack
- **Alerts**: Monitor disk space, memory, response times

## Next Steps

1. **Run Epic 2 Tests**: Validate complete integration
2. **Performance Tuning**: Optimize for your workload
3. **Production Deployment**: Enable security and monitoring
4. **Advanced Features**: Explore neural reranking and graph retrieval

For Epic 2-specific testing procedures, see `docs/EPIC2_TESTING_GUIDE.md`.

---

**Epic 2 Status**: With Weaviate properly configured, you have a production-ready advanced hybrid retriever system with multi-backend support, neural reranking, and graph-enhanced retrieval capabilities.