# Configuration Migration Guide

**Date**: January 21, 2025  
**Change**: Simplified from 24 configurations to 4 core configurations  
**Reason**: Project assessment identified configuration bloat as deployment blocker

## New Configuration Structure

### Core Configurations (4 files)

1. **`basic.yaml`** - Simple RAG without Epic 2 features
   - Uses MockLLMAdapter (no external dependencies)
   - Basic retriever with identity reranking
   - Simple fusion strategy
   - Memory optimized settings
   - **Use for**: Testing, development, CI/CD

2. **`epic2.yaml`** - Full Epic 2 features enabled
   - Uses Ollama LLM (requires local setup)
   - Neural reranking with cross-encoder models
   - Graph-enhanced fusion
   - High-performance settings
   - **Use for**: Production demonstrations, full feature showcasing

3. **`demo.yaml`** - Optimized for demonstrations
   - Uses MockLLMAdapter (reliable for demos)
   - Selective Epic 2 features (neural reranking only)
   - Balanced performance/reliability
   - **Use for**: Portfolio demos, presentations, showcases

4. **`default.yaml`** - Legacy compatibility (preserved)
   - Maintains backward compatibility
   - **Use for**: Existing scripts that reference default config

### Archived Configurations (23 files)

All previous configurations moved to `config/archive/`:
- `advanced_test.yaml`
- `comprehensive_test_graph.yaml`
- `dev.yaml`
- `diagnostic_test_graph.yaml`
- `epic2_hf_api.yaml`
- `epic2_modular.yaml`
- `hf_api_test.yaml`
- `production.yaml`
- `score_aware_test.yaml`
- `test.yaml`
- `test_epic2_*.yaml` (9 files)
- `test_mock*.yaml` (4 files)
- `test_with_mock.yaml`
- `demo_score_aware.yaml`

## Migration Instructions

### For Development
```python
# OLD
config = load_config("config/test_mock_default.yaml")

# NEW
config = load_config("config/basic.yaml")
```

### For Epic 2 Testing
```python
# OLD
config = load_config("config/test_epic2_all_features.yaml")

# NEW
config = load_config("config/epic2.yaml")
```

### For Demos
```python
# OLD
config = load_config("config/demo_score_aware.yaml")

# NEW
config = load_config("config/demo.yaml")
```

## Key Changes

### MockLLMAdapter Integration
- All test/demo configurations now use MockLLMAdapter by default
- No more Ollama dependency for testing
- Reliable, deterministic responses for CI/CD

### Simplified Feature Selection
- **Basic**: No Epic 2 features, maximum reliability
- **Demo**: Neural reranking only, balanced performance
- **Epic2**: All features enabled, requires Ollama

### Performance Optimization
- Memory settings tuned for each use case
- Batch sizes optimized for configuration purpose
- Cache settings appropriate for workload

## Benefits

1. **Reduced Complexity**: 24 → 4 configurations (83% reduction)
2. **Clear Purpose**: Each config has specific use case
3. **No Dependencies**: Basic and demo configs work without Ollama
4. **Easy Selection**: Choose by use case, not technical details
5. **Maintainability**: Only 4 files to maintain vs 24

## Backward Compatibility

- `default.yaml` preserved for existing scripts
- All archived configs available in `config/archive/`
- System behavior unchanged, only configuration organization improved

## Testing

All configurations validated:
```bash
# Test basic configuration
python -c "from src.core.config import load_config; from pathlib import Path; print('✅', load_config(Path('config/basic.yaml')).retriever.type)"

# Test demo configuration  
python -c "from src.core.config import load_config; from pathlib import Path; print('✅', load_config(Path('config/demo.yaml')).retriever.type)"

# Test Epic 2 configuration
python -c "from src.core.config import load_config; from pathlib import Path; print('✅', load_config(Path('config/epic2.yaml')).retriever.type)"
```

## Quick Reference

| Use Case | Configuration | LLM | Epic 2 Features | Dependencies |
|----------|---------------|-----|-----------------|--------------|
| Testing/CI | `basic.yaml` | Mock | None | None |
| Demos | `demo.yaml` | Mock | Neural reranking | None |
| Production | `epic2.yaml` | Ollama | All features | Ollama + models |
| Legacy | `default.yaml` | Ollama | Some features | Ollama |

This migration addresses the key finding from the project assessment: **"The technology is already there - it just needs to be accessible."**