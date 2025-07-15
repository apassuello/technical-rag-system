# Key Files Reference - Epic 2 System

## Core System Files

### Configuration Files
- `config/default.yaml` - Basic configuration (ModularUnifiedRetriever)
- `config/advanced_test.yaml` - Epic 2 configuration (AdvancedRetriever)

### System Architecture
- `src/core/platform_orchestrator.py` - System initialization and orchestration
- `src/core/component_factory.py` - Component creation with "enhanced_modular_unified" type
- `src/core/interfaces.py` - Component interfaces and contracts

### Epic 2 Implementation
- `src/components/retrievers/advanced_retriever.py` - Main Epic 2 AdvancedRetriever
- `src/components/retrievers/modular_unified_retriever.py` - Base modular retriever
- `src/components/retrievers/rerankers/neural_reranker.py` - Neural reranking implementation
- `src/components/retrievers/fusion/graph_enhanced_fusion.py` - Graph-enhanced fusion

### Validation & Testing
- `final_epic2_proof.py` - Epic 2 vs basic component differentiation proof
- `run_comprehensive_tests.py` - Complete system validation
- `tests/diagnostic/run_all_diagnostics.py` - System health diagnostics

### Documentation
- `CLAUDE.md` - Main project context (Epic 2 current status)
- `EPIC_2_ARCHITECTURE_FIX_COMPLETE_REPORT.md` - Complete implementation report
- `EPIC_2_LIVE_DEMO_PREPARATION.md` - Demo implementation guide

## Key Directories

### Epic 2 Components
- `src/components/retrievers/` - All retriever implementations
- `src/components/retrievers/rerankers/` - Neural reranking components
- `src/components/retrievers/fusion/` - Enhanced fusion strategies
- `src/components/retrievers/graph/` - Graph analysis components
- `src/components/retrievers/analytics/` - Analytics framework

### Testing & Validation
- `tests/epic2_validation/` - Epic 2 specific tests
- `tests/diagnostic/` - System diagnostic tests
- `tests/comprehensive_integration_test.py` - End-to-end validation

### Data & Samples
- `data/test/` - Sample RISC-V documents for testing
- `validation_results/` - Test results and performance metrics

## Quick Reference Commands

### System Validation
```bash
# Validate Epic 2 working
python final_epic2_proof.py

# Run comprehensive tests (basic)
python run_comprehensive_tests.py

# Run comprehensive tests (Epic 2)
python run_comprehensive_tests.py config/advanced_test.yaml

# Run diagnostic tests
python -m diagnostic.run_all_diagnostics
```

### System Initialization
```python
# Basic system
from src.core.platform_orchestrator import PlatformOrchestrator
basic_system = PlatformOrchestrator(Path("config/default.yaml"))

# Epic 2 system  
epic2_system = PlatformOrchestrator(Path("config/advanced_test.yaml"))
```