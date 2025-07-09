# Configuration System Phase 3 - Factory-Based Validation

**Component**: Configuration System  
**Phase**: 3 - Direct Wiring Implementation  
**Status**: ✅ Enhanced  
**Location**: `src/core/config.py`

---

## Overview

The Phase 3 configuration system enhances the existing Pydantic-based validation with ComponentFactory integration, providing comprehensive validation of component types and architecture consistency. It maintains full backward compatibility while adding enhanced error reporting and factory-based validation.

### Key Enhancements

- **🏭 Factory Integration**: ComponentFactory validation for all component types
- **🏗️ Architecture Validation**: Automatic consistency checking for legacy vs unified architectures
- **📊 Enhanced Errors**: Detailed validation errors with actionable guidance
- **🔄 Backward Compatibility**: All existing configurations continue to work
- **⚡ Performance**: Optimized validation with lazy factory import

---

## Configuration Architecture

### Component Validation Flow
```
YAML Configuration
    ↓
Pydantic Schema Validation
    ↓
ComponentFactory Type Validation
    ↓
Architecture Consistency Validation
    ↓
Validated PipelineConfig
```

### Validation Layers
1. **Schema Validation**: Pydantic ensures correct structure and types
2. **Component Validation**: ComponentFactory validates component types exist
3. **Architecture Validation**: Ensures configuration consistency (legacy vs unified)
4. **Environment Overrides**: Apply runtime configuration overrides

---

## Configuration Structure

### PipelineConfig Schema
```python
class PipelineConfig(BaseModel):
    """Complete pipeline configuration with factory validation."""
    
    document_processor: ComponentConfig      # Required
    embedder: ComponentConfig               # Required
    vector_store: Optional[ComponentConfig] # Optional (unified architecture)
    retriever: ComponentConfig              # Required
    answer_generator: ComponentConfig       # Required
    global_settings: Dict[str, Any]         # Optional
```

### ComponentConfig Schema
```python
class ComponentConfig(BaseModel):
    """Individual component configuration."""
    
    type: str                    # Component type (validated by factory)
    config: Dict[str, Any]       # Component-specific parameters
```

### Validation Enhancements
```python
@model_validator(mode='after')
def validate_component_types(self):
    """Validate component types using ComponentFactory."""
    # Factory validation ensures all component types exist
    errors = ComponentFactory.validate_configuration(config_dict)
    if errors:
        raise ValueError("Component validation failed: ...")

@model_validator(mode='after')  
def validate_architecture_consistency(self):
    """Validate architecture consistency (legacy vs unified)."""
    # Ensure unified architecture doesn't have vector_store
    # Ensure legacy architecture has required vector_store
```

---

## Supported Architectures

### 1. Unified Architecture (Phase 2+ Recommended)

#### Configuration Structure
```yaml
document_processor:
  type: "hybrid_pdf"
  config: { ... }

embedder:
  type: "sentence_transformer"
  config: { ... }

# No vector_store section - unified retriever handles storage
retriever:
  type: "unified"
  config:
    embedding_dim: 384
    index_type: "IndexFlatIP"
    dense_weight: 0.7
    # ... other unified retriever parameters

answer_generator:
  type: "adaptive"
  config: { ... }
```

#### Validation Rules
- ✅ `retriever.type` must be `"unified"`
- ✅ `vector_store` section must be absent or `null`
- ✅ `retriever.config` must include vector storage parameters
- ✅ All component types must be supported by ComponentFactory

### 2. Legacy Architecture (Phase 1 Compatibility)

#### Configuration Structure
```yaml
document_processor:
  type: "hybrid_pdf"
  config: { ... }

embedder:
  type: "sentence_transformer"
  config: { ... }

# vector_store section required for legacy architecture
vector_store:
  type: "faiss"
  config:
    embedding_dim: 384
    index_type: "IndexFlatIP"

retriever:
  type: "hybrid"
  config:
    dense_weight: 0.7
    # ... other hybrid retriever parameters

answer_generator:
  type: "adaptive"
  config: { ... }
```

#### Validation Rules
- ✅ `retriever.type` must be `"hybrid"`
- ✅ `vector_store` section must be present and configured
- ✅ `vector_store.type` must be supported by ComponentFactory
- ✅ All component types must be supported by ComponentFactory

---

## Component Type Mapping

### Supported Component Types
The configuration system validates against ComponentFactory mappings:

```python
# Document Processors
"hybrid_pdf"      → HybridPDFProcessor
"pdf_processor"   → HybridPDFProcessor (alias)

# Embedders  
"sentence_transformer"  → SentenceTransformerEmbedder
"sentence_transformers" → SentenceTransformerEmbedder (alias)

# Vector Stores (legacy architecture only)
"faiss"          → FAISSVectorStore

# Retrievers
"hybrid"         → HybridRetriever (legacy)
"unified"        → UnifiedRetriever (unified)

# Answer Generators
"adaptive"       → AdaptiveAnswerGenerator
"adaptive_generator" → AdaptiveAnswerGenerator (alias)
```

### Type Validation
```python
# Configuration validation checks component types
config = PipelineConfig(**yaml_data)
# Automatically validates:
# - All component types exist in ComponentFactory
# - Architecture consistency (unified vs legacy)
# - Required parameters present
```

---

## Configuration Examples

### Example 1: Unified Architecture
```yaml
# config/examples/phase3_unified_example.yaml
document_processor:
  type: "hybrid_pdf"
  config:
    chunk_size: 1000
    chunk_overlap: 200
    enable_toc_navigation: true

embedder:
  type: "sentence_transformer"
  config:
    model_name: "sentence-transformers/all-MiniLM-L6-v2"
    use_mps: true

# No vector_store needed
retriever:
  type: "unified"
  config:
    embedding_dim: 384
    index_type: "IndexFlatIP"
    dense_weight: 0.7
    rrf_k: 10

answer_generator:
  type: "adaptive"
  config:
    model_type: "local"
    max_length: 512

global_settings:
  platform: "phase3_unified"
  use_mps: true
```

### Example 2: Legacy Architecture
```yaml
# config/examples/phase3_legacy_example.yaml
document_processor:
  type: "hybrid_pdf"
  config:
    chunk_size: 1000
    chunk_overlap: 200

embedder:
  type: "sentence_transformer"  
  config:
    model_name: "sentence-transformers/all-MiniLM-L6-v2"
    use_mps: true

vector_store:
  type: "faiss"
  config:
    embedding_dim: 384
    index_type: "IndexFlatIP"

retriever:
  type: "hybrid"
  config:
    dense_weight: 0.7
    rrf_k: 10

answer_generator:
  type: "adaptive"
  config:
    model_type: "local"
    max_length: 512

global_settings:
  platform: "phase3_legacy"
```

---

## Validation Error Handling

### Enhanced Error Messages

#### Component Type Validation
```python
# Invalid component type
document_processor:
  type: "unknown_processor"

# Error message:
ValueError: Component validation failed:
  - Unknown document_processor type 'unknown_processor'. 
    Available processors: ['hybrid_pdf', 'pdf_processor']
```

#### Architecture Consistency Validation
```python
# Unified retriever with vector_store (invalid)
retriever:
  type: "unified"
vector_store:
  type: "faiss"

# Error message:
ValueError: Unified retriever architecture detected, but vector_store is configured. 
For unified architecture, remove the vector_store section - 
the retriever handles vector storage internally.
```

```python
# Legacy retriever without vector_store (invalid)
retriever:
  type: "hybrid"
# vector_store: missing

# Error message:
ValueError: Legacy hybrid retriever architecture detected, but vector_store is missing. 
For legacy architecture, configure a vector_store section, 
or switch to 'unified' retriever type.
```

### Error Recovery Patterns
```python
def load_config_safely(config_path: Path) -> Optional[PipelineConfig]:
    """Load configuration with error recovery."""
    
    try:
        config_manager = ConfigManager(config_path)
        config = config_manager.load()
        return config
    except ValueError as e:
        if "Component validation failed" in str(e):
            print("Configuration has invalid component types:")
            print(str(e))
            print("\nAvailable components:")
            from src.core.component_factory import ComponentFactory
            available = ComponentFactory.get_available_components()
            for comp_type, types in available.items():
                print(f"  {comp_type}: {types}")
        elif "architecture detected" in str(e):
            print("Configuration has architecture inconsistency:")
            print(str(e))
        else:
            print(f"Configuration error: {e}")
        return None
    except Exception as e:
        print(f"Failed to load configuration: {e}")
        return None

# Usage
config = load_config_safely(Path("config.yaml"))
if config is None:
    print("Please fix configuration errors and try again")
```

---

## Environment Variable Overrides

### Override Syntax
Environment variables use the prefix `RAG_` with double underscores for nesting:

```bash
# Override embedder model
export RAG_EMBEDDER__CONFIG__MODEL_NAME="sentence-transformers/multi-qa-MiniLM-L6-cos-v1"

# Override retriever dense weight
export RAG_RETRIEVER__CONFIG__DENSE_WEIGHT="0.8"

# Override global setting
export RAG_GLOBAL_SETTINGS__USE_MPS="false"

# Override answer generator type
export RAG_ANSWER_GENERATOR__TYPE="adaptive"
```

### Environment Override Examples
```python
# Base configuration
config = {
    "embedder": {
        "type": "sentence_transformer",
        "config": {"model_name": "all-MiniLM-L6-v2", "use_mps": True}
    }
}

# With environment variables:
# RAG_EMBEDDER__CONFIG__MODEL_NAME="multi-qa-MiniLM-L6-cos-v1"
# RAG_EMBEDDER__CONFIG__USE_MPS="false"

# Results in:
config = {
    "embedder": {
        "type": "sentence_transformer", 
        "config": {"model_name": "multi-qa-MiniLM-L6-cos-v1", "use_mps": False}
    }
}
```

### Complex Value Overrides
```bash
# JSON values for complex configurations
export RAG_RETRIEVER__CONFIG='{"dense_weight": 0.8, "rrf_k": 15}'

# Boolean values
export RAG_GLOBAL_SETTINGS__USE_MPS="true"

# Numeric values
export RAG_DOCUMENT_PROCESSOR__CONFIG__CHUNK_SIZE="1500"
```

---

## Configuration Manager API

### Basic Usage
```python
from src.core.config import ConfigManager, PipelineConfig

# Load from file
config_manager = ConfigManager(Path("config.yaml"))
config = config_manager.load()

# Access components
processor_config = config.document_processor
embedder_config = config.embedder
retriever_config = config.retriever

# Get specific component configuration
processor_config = config_manager.get_component_config("document_processor")
```

### Advanced Usage
```python
# Environment-specific configuration
config_manager = ConfigManager(env="production")
config = config_manager.load()  # Loads config/production.yaml

# Save configuration
config_manager.save(Path("output_config.yaml"))

# Lazy loading
config = config_manager.config  # Loads on first access

# Raw configuration access
raw_config = config_manager._raw_config
```

### Validation Methods
```python
# Validate configuration before use
def validate_config(config_path: Path) -> List[str]:
    """Validate configuration and return errors."""
    
    try:
        config_manager = ConfigManager(config_path)
        config = config_manager.load()
        return []  # No errors
    except ValueError as e:
        return [str(e)]
    except Exception as e:
        return [f"Configuration load error: {e}"]

# Usage
errors = validate_config(Path("config.yaml"))
if errors:
    for error in errors:
        print(f"Error: {error}")
else:
    print("Configuration is valid")
```

---

## Configuration Best Practices

### 1. Component Configuration
```yaml
# Good: Specific, well-documented parameters
document_processor:
  type: "hybrid_pdf"
  config:
    chunk_size: 1000      # Optimal for technical docs
    chunk_overlap: 200    # 20% overlap for context
    enable_toc_navigation: true  # Extract TOC structure

# Avoid: Minimal configuration without context
document_processor:
  type: "hybrid_pdf"
  config: {}
```

### 2. Architecture Selection
```yaml
# Unified architecture (recommended for new deployments)
retriever:
  type: "unified"
  config:
    embedding_dim: 384
    index_type: "IndexFlatIP"
    dense_weight: 0.7

# Legacy architecture (for backward compatibility)
vector_store:
  type: "faiss"
  config: {embedding_dim: 384}
retriever:
  type: "hybrid"
  config: {dense_weight: 0.7}
```

### 3. Environment Management
```yaml
# Development
global_settings:
  log_level: "DEBUG"
  use_mps: true
  timeout_seconds: 60

# Production  
global_settings:
  log_level: "INFO"
  use_mps: true
  timeout_seconds: 300
  max_workers: 8
```

### 4. Performance Optimization
```yaml
# Apple Silicon optimization
embedder:
  config:
    use_mps: true
    batch_size: 32

retriever:
  config:
    index_type: "IndexFlatIP"  # Fast for <1k docs
    # index_type: "IndexIVFFlat"  # Use for >10k docs

global_settings:
  use_mps: true
  mps_fallback: true
```

---

## Migration Guide

### From Phase 2 to Phase 3
```yaml
# Phase 2 configuration works unchanged in Phase 3
# Factory validation is added automatically

# Phase 2 unified config
retriever:
  type: "unified"
  config: {dense_weight: 0.7, embedding_dim: 384}

# Phase 3 unified config (same, with validation)
retriever:
  type: "unified"
  config: {dense_weight: 0.7, embedding_dim: 384}
# Now validated by ComponentFactory
```

### From Legacy to Unified
```yaml
# Before: Legacy architecture
vector_store:
  type: "faiss"
  config: {embedding_dim: 384, index_type: "IndexFlatIP"}
retriever:
  type: "hybrid"
  config: {dense_weight: 0.7}

# After: Unified architecture
# Remove vector_store section
retriever:
  type: "unified"
  config:
    embedding_dim: 384      # From vector_store.config
    index_type: "IndexFlatIP"  # From vector_store.config  
    dense_weight: 0.7       # From retriever.config
```

### Validation Migration
```python
# Phase 2: Manual validation
config = PipelineConfig(**yaml_data)
# Limited validation

# Phase 3: Automatic factory validation
config = PipelineConfig(**yaml_data)
# Comprehensive validation:
# - Component types exist in factory
# - Architecture consistency
# - Enhanced error messages
```

---

## Testing Configuration

### Configuration Testing
```python
import pytest
import yaml
from pathlib import Path
from src.core.config import ConfigManager, PipelineConfig

class TestConfigurationSystem:
    """Test configuration system with factory validation."""
    
    def test_unified_config_validation(self):
        """Test unified architecture configuration validation."""
        
        unified_config = {
            "document_processor": {"type": "hybrid_pdf", "config": {"chunk_size": 1000}},
            "embedder": {"type": "sentence_transformer", "config": {"use_mps": True}},
            "retriever": {"type": "unified", "config": {"embedding_dim": 384}},
            "answer_generator": {"type": "adaptive", "config": {"model_type": "local"}}
        }
        
        # Should validate successfully
        config = PipelineConfig(**unified_config)
        assert config.retriever.type == "unified"
        assert config.vector_store is None
    
    def test_legacy_config_validation(self):
        """Test legacy architecture configuration validation."""
        
        legacy_config = {
            "document_processor": {"type": "hybrid_pdf", "config": {"chunk_size": 1000}},
            "embedder": {"type": "sentence_transformer", "config": {"use_mps": True}},
            "vector_store": {"type": "faiss", "config": {"embedding_dim": 384}},
            "retriever": {"type": "hybrid", "config": {"dense_weight": 0.7}},
            "answer_generator": {"type": "adaptive", "config": {"model_type": "local"}}
        }
        
        # Should validate successfully
        config = PipelineConfig(**legacy_config)
        assert config.retriever.type == "hybrid"
        assert config.vector_store is not None
    
    def test_invalid_component_type(self):
        """Test validation of invalid component types."""
        
        invalid_config = {
            "document_processor": {"type": "unknown_processor", "config": {}},
            "embedder": {"type": "sentence_transformer", "config": {}},
            "retriever": {"type": "unified", "config": {}},
            "answer_generator": {"type": "adaptive", "config": {}}
        }
        
        with pytest.raises(ValueError, match="Component validation failed"):
            PipelineConfig(**invalid_config)
    
    def test_architecture_inconsistency(self):
        """Test architecture consistency validation."""
        
        # Unified retriever with vector_store (invalid)
        inconsistent_config = {
            "document_processor": {"type": "hybrid_pdf", "config": {}},
            "embedder": {"type": "sentence_transformer", "config": {}},
            "vector_store": {"type": "faiss", "config": {"embedding_dim": 384}},
            "retriever": {"type": "unified", "config": {"embedding_dim": 384}},
            "answer_generator": {"type": "adaptive", "config": {}}
        }
        
        with pytest.raises(ValueError, match="Unified retriever architecture detected.*vector_store"):
            PipelineConfig(**inconsistent_config)
    
    def test_config_manager_integration(self, tmp_path):
        """Test ConfigManager with factory validation."""
        
        config_file = tmp_path / "test_config.yaml"
        config_data = {
            "document_processor": {"type": "hybrid_pdf", "config": {"chunk_size": 1000}},
            "embedder": {"type": "sentence_transformer", "config": {"use_mps": False}},
            "retriever": {"type": "unified", "config": {"embedding_dim": 384}},
            "answer_generator": {"type": "adaptive", "config": {"model_type": "local"}}
        }
        
        with open(config_file, 'w') as f:
            yaml.dump(config_data, f)
        
        # Load and validate
        config_manager = ConfigManager(config_file)
        config = config_manager.load()
        
        assert config.document_processor.type == "hybrid_pdf"
        assert config.retriever.type == "unified"
        assert config.vector_store is None
```

---

## Troubleshooting

### Common Configuration Issues

1. **Invalid Component Type**
```yaml
# Problem: Unknown component type
document_processor:
  type: "pdf_reader"  # Not supported

# Solution: Use supported type
document_processor:
  type: "hybrid_pdf"  # Supported by factory
```

2. **Architecture Mismatch**
```yaml
# Problem: Unified retriever with vector_store
retriever:
  type: "unified"
vector_store:
  type: "faiss"

# Solution: Remove vector_store for unified
retriever:
  type: "unified"
  config: {embedding_dim: 384}
```

3. **Missing Required Configuration**
```yaml
# Problem: Legacy retriever without vector_store
retriever:
  type: "hybrid"

# Solution: Add vector_store for legacy
vector_store:
  type: "faiss"
  config: {embedding_dim: 384}
retriever:
  type: "hybrid"
```

### Debug Tools
```python
# Validate configuration with detailed errors
from src.core.component_factory import ComponentFactory

def debug_config(config_dict):
    """Debug configuration issues."""
    
    print("Available components:")
    available = ComponentFactory.get_available_components()
    for comp_type, types in available.items():
        print(f"  {comp_type}: {types}")
    
    print("\nValidating configuration...")
    errors = ComponentFactory.validate_configuration(config_dict)
    
    if errors:
        print("Validation errors:")
        for error in errors:
            print(f"  - {error}")
    else:
        print("Configuration is valid")
```

For additional configuration examples and troubleshooting, see:
- Example configurations: `config/examples/`
- Factory documentation: `docs/component-factory-guide.md`
- Migration guide: `docs/component-migration-guide.md`