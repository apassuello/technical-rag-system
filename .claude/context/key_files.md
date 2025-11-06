# Key Files Reference - Epic 8 Transition Ready

## Core System Files

### Configuration Files
- `config/default.yaml` - Current system configuration with Epic 1 multi-model routing
- `config/epic1_config.yaml` - Epic 1 production configuration (if exists)

### System Architecture
- `src/core/platform_orchestrator.py` - System initialization and orchestration
- `src/core/component_factory.py` - Component creation and factory patterns

### Epic 1 Foundation (Production-Ready)
- `src/components/generators/epic1_answer_generator.py` - Multi-model routing system
- `src/components/generators/routing/adaptive_router.py` - Intelligent routing with 95.1% success rate
- `src/components/generators/routing/routing_strategies.py` - Cost/quality optimization strategies
- `src/components/generators/routing/model_registry.py` - Dynamic model provisioning

### Test Infrastructure (Unified System)
- `test_runner.py` - Unified test execution with JSON diagnostics
- `tests/runner/` - Complete test framework (discovery, execution, reporting)
- `tests/epic1/phase2/` - Epic 1 validation tests (95.1% success rate)

### Epic 8 Planning Documents
- `docs/epics/epic8-specification.md` - Complete Epic 8 requirements and architecture
- `docs/epics/epic8-implementation-guidelines.md` - Detailed implementation guidelines
- `docs/epics/epic8-test-specification.md` - Comprehensive test specifications

### Documentation
- `CLAUDE.md` - Main project context (Epic 8 transition focus)
- `docs/epic1/EPIC1_PRODUCTION_STATUS.md` - Single source of truth for Epic 1
- `docs/epic1/lessons-learned/EPIC1_LESSONS_LEARNED.md` - Implementation insights

## Key Directories

### Epic 1 Components (Available for Epic 8 Extraction)
- `src/components/generators/` - Multi-model routing system
- `src/components/generators/routing/` - Intelligent routing components
- `src/components/processors/` - Document processing pipeline
- `src/components/retrievers/` - Retrieval system with Epic 2 enhancements
- `src/components/embedders/` - Embedding generation system

### Testing & Validation
- `tests/runner/` - Unified test execution framework
- `tests/epic1/phase2/` - Epic 1 production validation
- `tests/epic1/demos/` - Demo scripts and validation

### Epic 8 Target Architecture Directories (To Be Created)
- `epic8/` - Epic 8 microservices implementation
- `k8s/` - Kubernetes manifests and Helm charts
- `docker/` - Container definitions and multi-stage builds
- `monitoring/` - Observability stack configuration

## Quick Reference Commands

### Current System Validation
```bash
# Epic 1 system validation
python test_runner.py epic1 all

# Smoke tests
python test_runner.py epic1 smoke

# Integration tests  
python test_runner.py epic1 integration
```

### System Initialization
```python
# Current Epic 1 system
from src.core.platform_orchestrator import PlatformOrchestrator
system = PlatformOrchestrator(Path("config/default.yaml"))

# Epic 1 multi-model system
epic1_system = PlatformOrchestrator(Path("config/epic1_config.yaml"))
```

### Epic 8 Planning References
```bash
# Review Epic 8 specifications
cat docs/epics/epic8-specification.md
cat docs/epics/epic8-implementation-guidelines.md
cat docs/epics/epic8-test-specification.md

# Epic 1 foundation status
cat docs/epic1/EPIC1_PRODUCTION_STATUS.md
```

## Epic 8 Transition Status

### Ready for Epic 8
- ✅ Epic 1 foundation complete (95.1% success rate)
- ✅ Multi-model routing system operational
- ✅ Comprehensive test framework implemented
- ✅ Documentation consolidated and current

### Next Steps
- Begin Phase 1: Multi-Model Enhancement (service extraction)
- Create Epic 8 directory structure
- Start Docker containerization planning
- Design Kubernetes deployment strategy