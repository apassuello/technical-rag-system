# Epic 2 Demo Debugging Session Bootstrap

## Session Startup Protocol

### Step 1: System Status Validation
```bash
# Verify Epic 2 system operational status
python final_epic2_proof.py

# Check architecture compliance
python -c "
from src.core.platform_orchestrator import PlatformOrchestrator
from pathlib import Path

basic = PlatformOrchestrator(Path('config/default.yaml'))
epic2 = PlatformOrchestrator(Path('config/advanced_test.yaml'))

print('Basic Architecture:', basic._determine_system_architecture())
print('Epic 2 Architecture:', epic2._determine_system_architecture())
print('Epic 2 Retriever:', type(epic2.retriever).__name__)
"

# Test demo system integration
python -c "
from demo.utils.system_integration import get_system_manager
import time

print('Testing demo system integration...')
start = time.time()
manager = get_system_manager()
print(f'System manager created in {time.time() - start:.2f}s')
print('Manager type:', type(manager))

# Test cache status
cache_info = manager.get_cache_info()
print('Cache status:', cache_info['cache_valid'])
print('Cache size:', cache_info.get('cache_size_mb', 'N/A'), 'MB')
"
```

### Step 2: Performance Baseline Establishment
```bash
# Memory usage baseline
python -c "
import psutil
import os
print('System memory usage baseline:')
print(f'Available memory: {psutil.virtual_memory().available / 1024 / 1024:.1f}MB')
print(f'Process memory: {psutil.Process(os.getpid()).memory_info().rss / 1024 / 1024:.1f}MB')
"

# Document processing performance test
python -c "
from demo.utils.system_integration import get_system_manager
import time
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)

print('Testing document processing performance...')
manager = get_system_manager()

# Test initialization time
start = time.time()
success = manager.initialize_system()
init_time = time.time() - start

print(f'System initialization: {init_time:.2f}s')
print(f'Documents processed: {manager.documents_processed}')
print(f'Initialization success: {success}')
"
```

### Step 3: Answer Quality Baseline
```bash
# Test answer quality with sample queries
python -c "
from demo.utils.system_integration import get_system_manager
import time

manager = get_system_manager()
if not manager.is_initialized:
    print('Initializing system...')
    manager.initialize_system()

# Test queries for quality assessment
test_queries = [
    'What is RISC-V instruction set architecture?',
    'Explain RISC-V memory management',
    'How does RISC-V handle interrupts?'
]

print('Testing answer quality baseline...')
for query in test_queries:
    start = time.time()
    result = manager.query(query)
    response_time = time.time() - start
    
    print(f'Query: {query}')
    print(f'Response time: {response_time:.2f}s')
    print(f'Answer length: {len(result.get(\"answer\", \"\"))} chars')
    print(f'Confidence: {result.get(\"confidence\", \"N/A\")}')
    print(f'Sources: {len(result.get(\"sources\", []))}')
    print('---')
"
```

## Current System State Summary

### Epic 2 Architecture Status
- **Basic System**: ModularUnifiedRetriever with "modular" architecture
- **Epic 2 System**: AdvancedRetriever with "modular" architecture
- **Architecture Compliance**: 100% modular design maintained
- **Component Factory**: "enhanced_modular_unified" type registered

### Performance Characteristics
- **Initialization**: Currently slow (document parsing + vector DB building)
- **Caching**: Knowledge cache implemented for performance improvement
- **Memory Usage**: Monitor for HuggingFace Spaces <2GB requirement
- **Query Response**: Target <2s for typical queries

### Quality Standards
- **Answer Relevance**: Target >90% for Swiss tech market
- **Technical Sophistication**: Demonstrate Epic 2 neural reranking and graph enhancement
- **Professional Quality**: Portfolio-ready presentation standards
- **Error Handling**: Graceful failure management and recovery

## Debugging Session Objectives

### Primary Issues to Address
1. **Slow Initialization**: Document parsing and vector DB building optimization
2. **Answer Quality**: Improve relevance and professional quality
3. **HuggingFace Deployment**: Assess migration effort and API integration
4. **Performance Monitoring**: Real-time metrics and optimization

### Success Criteria
- [ ] Initialization time <10s (measure current baseline)
- [ ] Answer quality >90% relevance (measurable improvement)
- [ ] HuggingFace deployment plan with effort estimation
- [ ] API integration strategy with cost analysis
- [ ] Swiss engineering quality standards maintained

### Key Files to Focus On
- `streamlit_epic2_demo.py` - Main demo application
- `demo/utils/system_integration.py` - System initialization and caching
- `demo/utils/parallel_processor.py` - Document processing pipeline
- `demo/utils/knowledge_cache.py` - Caching optimization
- `config/advanced_test.yaml` - Epic 2 configuration
- `src/components/retrievers/advanced_retriever.py` - Core retrieval system

## Session Quality Gates

### 30-Minute Checkpoint Protocol
1. **Performance Metrics**: Quantified improvements with before/after comparison
2. **Swiss Engineering Standards**: Quality and precision validation
3. **Architecture Compliance**: Modular design and adapter pattern maintenance
4. **Portfolio Readiness**: Swiss tech market suitability assessment

### Session Handoff Requirements
- Performance improvements documented with metrics
- Quality enhancements validated with test results
- Deployment assessment with migration plan
- Next session preparation with clear objectives

## Context Integration Commands

### Apply Context Template
```bash
# Set session context for debugging
cp .claude/context-templates/OPTIMIZER_MODE_EPIC2_DEMO.md .claude/claude.md

# Start Claude Code session with context
claude code
```

### Validation Commands
```bash
# Verify context understanding
# "Read the current CLAUDE.md and confirm you understand:
# 1. Epic 2 demo debugging session focus and optimization targets
# 2. Swiss engineering standards for performance and quality
# 3. HuggingFace deployment requirements and assessment criteria
# 4. Specific performance metrics and quality gates"

# Load session bootstrap
# "Execute the commands in .claude/session-templates/EPIC2_DEMO_DEBUG_BOOTSTRAP.md
# to establish system baseline and performance metrics"
```

This bootstrap template provides structured context for effective Epic 2 demo debugging following Swiss engineering standards.