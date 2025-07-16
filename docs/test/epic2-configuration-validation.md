# Epic 2 Configuration Validation
## YAML-Driven Feature Testing Procedures

**Version**: 1.0  
**References**: [Epic 2 Integration Test Plan](./epic2-integration-test-plan.md), [EPIC2_TESTING_GUIDE.md](../EPIC2_TESTING_GUIDE.md)  
**Last Updated**: July 2025

---

## 1. Executive Summary

This document provides comprehensive procedures for validating Epic 2 Advanced Hybrid Retriever configurations that enable enhanced sub-components within ModularUnifiedRetriever. Configuration validation ensures that YAML-driven feature activation works correctly and produces the expected sub-component instantiation.

### 1.1 Configuration Validation Philosophy

Epic 2 configuration validation focuses on **YAML-driven feature activation** rather than traditional component configuration, emphasizing:
- **Sub-Component Selection**: Correct sub-component instantiation based on configuration
- **Feature Activation**: YAML parameters properly enable Epic 2 features
- **Configuration Consistency**: Valid configuration produces expected behavior
- **Error Handling**: Invalid configurations handled gracefully

### 1.2 Validation Scope

**Configuration Files Tested**:
- `test_epic2_base.yaml` - Basic configuration (no Epic 2 features)
- `test_epic2_neural_enabled.yaml` - Neural reranking sub-component only
- `test_epic2_graph_enabled.yaml` - Graph enhancement sub-component only
- `test_epic2_all_features.yaml` - All Epic 2 sub-components enabled

**Validation Categories**:
- Configuration parsing and schema validation
- Sub-component instantiation verification
- Feature activation confirmation
- Error handling and fallback behavior

---

## 2. Configuration Architecture Overview

### 2.1 Epic 2 Configuration Structure

Epic 2 configurations extend ModularUnifiedRetriever through enhanced sub-component selection:

```yaml
retriever:
  type: "modular_unified"
  config:
    # Sub-component selection drives Epic 2 feature activation
    reranker:
      type: "neural"      # Epic 2: NeuralReranker
      # type: "identity"   # Basic: IdentityReranker
    
    fusion:
      type: "graph_enhanced_rrf"  # Epic 2: GraphEnhancedRRFFusion
      # type: "rrf"               # Basic: RRFFusion
    
    vector_index:
      type: "faiss"       # Basic: FAISSIndex
      # type: "weaviate"   # Epic 2: WeaviateIndex (optional)
```

### 2.2 Sub-Component Configuration Mapping

| Configuration Value | Sub-Component Class | Epic 2 Feature |
|---------------------|---------------------|----------------|
| `reranker.type: "neural"` | NeuralReranker | Neural reranking |
| `reranker.type: "identity"` | IdentityReranker | Basic reranking |
| `fusion.type: "graph_enhanced_rrf"` | GraphEnhancedRRFFusion | Graph enhancement |
| `fusion.type: "rrf"` | RRFFusion | Basic fusion |
| `vector_index.type: "weaviate"` | WeaviateIndex | Multi-backend |
| `vector_index.type: "faiss"` | FAISSIndex | Single backend |

### 2.3 Configuration Validation Levels

**Level 1: Schema Validation**
- YAML syntax correctness
- Required fields presence
- Data type validation
- Value range validation

**Level 2: Semantic Validation**
- Configuration consistency
- Feature dependency validation
- Resource availability checks
- Compatibility verification

**Level 3: Runtime Validation**
- Sub-component instantiation
- Feature activation confirmation
- Integration testing
- Performance validation

---

## 3. Configuration Test Files

### 3.1 Base Configuration (No Epic 2 Features)

#### File: `config/test_epic2_base.yaml`

```yaml
# Base configuration - no Epic 2 features enabled
retriever:
  type: "modular_unified"
  config:
    vector_index:
      type: "faiss"
      config:
        index_type: "IndexFlatIP"
        normalize_embeddings: true
        metric: "cosine"
    
    sparse:
      type: "bm25"
      config:
        k1: 1.2
        b: 0.75
    
    fusion:
      type: "rrf"              # Basic fusion - no graph enhancement
      config:
        k: 60
        weights:
          dense: 0.7
          sparse: 0.3
    
    reranker:
      type: "identity"         # Basic reranker - no neural reranking
      config: {}
```

**Expected Sub-Components**:
- Reranker: `IdentityReranker`
- Fusion: `RRFFusion`
- Vector Index: `FAISSIndex`
- **Epic 2 Features**: None

#### Validation Tests:
```python
def test_base_configuration():
    """Test basic configuration loads without Epic 2 features."""
    config = load_config("test_epic2_base.yaml")
    retriever = ComponentFactory.create_retriever(config.retriever)
    
    assert isinstance(retriever.reranker, IdentityReranker)
    assert isinstance(retriever.fusion_strategy, RRFFusion)
    assert isinstance(retriever.vector_index, FAISSIndex)
```

### 3.2 Neural Reranking Configuration

#### File: `config/test_epic2_neural_enabled.yaml`

```yaml
# Neural reranking only - Epic 2 neural sub-component
retriever:
  type: "modular_unified"
  config:
    vector_index:
      type: "faiss"
      config:
        index_type: "IndexFlatIP"
        normalize_embeddings: true
    
    sparse:
      type: "bm25"
      config:
        k1: 1.2
        b: 0.75
    
    fusion:
      type: "rrf"              # Basic fusion
      config:
        k: 60
        weights:
          dense: 0.7
          sparse: 0.3
    
    reranker:
      type: "neural"           # Epic 2: Neural reranking enabled
      config:
        enabled: true
        model_name: "cross-encoder/ms-marco-MiniLM-L6-v2"
        device: "auto"
        batch_size: 32
        max_length: 512
        max_candidates: 100
```

**Expected Sub-Components**:
- Reranker: `NeuralReranker`
- Fusion: `RRFFusion`
- Vector Index: `FAISSIndex`
- **Epic 2 Features**: Neural reranking

#### Validation Tests:
```python
def test_neural_reranking_configuration():
    """Test neural reranking configuration enables Epic 2 feature."""
    config = load_config("test_epic2_neural_enabled.yaml")
    retriever = ComponentFactory.create_retriever(config.retriever)
    
    assert isinstance(retriever.reranker, NeuralReranker)
    assert retriever.reranker.is_enabled()
    assert retriever.reranker.model_name == "cross-encoder/ms-marco-MiniLM-L6-v2"
    assert isinstance(retriever.fusion_strategy, RRFFusion)
```

### 3.3 Graph Enhancement Configuration

#### File: `config/test_epic2_graph_enabled.yaml`

```yaml
# Graph enhancement only - Epic 2 graph sub-component
retriever:
  type: "modular_unified"
  config:
    vector_index:
      type: "faiss"
      config:
        index_type: "IndexFlatIP"
        normalize_embeddings: true
    
    sparse:
      type: "bm25"
      config:
        k1: 1.2
        b: 0.75
    
    fusion:
      type: "graph_enhanced_rrf"  # Epic 2: Graph enhancement enabled
      config:
        k: 60
        weights:
          dense: 0.4
          sparse: 0.3
          graph: 0.3          # Graph signal weight
        graph_enabled: true
        similarity_threshold: 0.65
        max_connections_per_document: 15
        use_pagerank: true
        pagerank_damping: 0.85
    
    reranker:
      type: "identity"         # Basic reranker
      config: {}
```

**Expected Sub-Components**:
- Reranker: `IdentityReranker`
- Fusion: `GraphEnhancedRRFFusion`
- Vector Index: `FAISSIndex`
- **Epic 2 Features**: Graph enhancement

#### Validation Tests:
```python
def test_graph_enhancement_configuration():
    """Test graph enhancement configuration enables Epic 2 feature."""
    config = load_config("test_epic2_graph_enabled.yaml")
    retriever = ComponentFactory.create_retriever(config.retriever)
    
    assert isinstance(retriever.reranker, IdentityReranker)
    assert isinstance(retriever.fusion_strategy, GraphEnhancedRRFFusion)
    assert retriever.fusion_strategy.graph_enabled
    assert retriever.fusion_strategy.similarity_threshold == 0.65
```

### 3.4 Complete Epic 2 Configuration

#### File: `config/test_epic2_all_features.yaml`

```yaml
# All Epic 2 features enabled - complete configuration
retriever:
  type: "modular_unified"
  config:
    vector_index:
      type: "faiss"
      config:
        index_type: "IndexFlatIP"
        normalize_embeddings: true
    
    sparse:
      type: "bm25"
      config:
        k1: 1.2
        b: 0.75
    
    fusion:
      type: "graph_enhanced_rrf"  # Epic 2: Graph enhancement
      config:
        k: 60
        weights:
          dense: 0.4
          sparse: 0.3
          graph: 0.3
        graph_enabled: true
        similarity_threshold: 0.65
        max_connections_per_document: 15
        use_pagerank: true
        pagerank_damping: 0.85
    
    reranker:
      type: "neural"           # Epic 2: Neural reranking
      config:
        enabled: true
        model_name: "cross-encoder/ms-marco-MiniLM-L6-v2"
        device: "auto"
        batch_size: 32
        max_length: 512
        max_candidates: 100
        models:
          default_model:
            name: "cross-encoder/ms-marco-MiniLM-L6-v2"
            device: "auto"
            batch_size: 32
            max_length: 512
        default_model: "default_model"
```

**Expected Sub-Components**:
- Reranker: `NeuralReranker`
- Fusion: `GraphEnhancedRRFFusion`
- Vector Index: `FAISSIndex`
- **Epic 2 Features**: Neural reranking + Graph enhancement

#### Validation Tests:
```python
def test_complete_epic2_configuration():
    """Test complete Epic 2 configuration enables all features."""
    config = load_config("test_epic2_all_features.yaml")
    retriever = ComponentFactory.create_retriever(config.retriever)
    
    assert isinstance(retriever.reranker, NeuralReranker)
    assert retriever.reranker.is_enabled()
    assert isinstance(retriever.fusion_strategy, GraphEnhancedRRFFusion)
    assert retriever.fusion_strategy.graph_enabled
    assert isinstance(retriever.vector_index, FAISSIndex)
```

---

## 4. Validation Test Procedures

### 4.1 Configuration Parsing Validation

#### 4.1.1 Schema Validation Tests

**Test Category**: Configuration Schema Compliance

```python
def test_configuration_schema_validation():
    """Test all Epic 2 configurations comply with schema."""
    config_files = [
        "test_epic2_base.yaml",
        "test_epic2_neural_enabled.yaml", 
        "test_epic2_graph_enabled.yaml",
        "test_epic2_all_features.yaml"
    ]
    
    for config_file in config_files:
        config = load_config(config_file)
        assert config.retriever.type == "modular_unified"
        assert "vector_index" in config.retriever.config
        assert "sparse" in config.retriever.config
        assert "fusion" in config.retriever.config
        assert "reranker" in config.retriever.config
```

#### 4.1.2 Configuration Parsing Tests

**Test Category**: YAML Parsing Correctness

```python
def test_yaml_parsing_correctness():
    """Test YAML files parse correctly without errors."""
    config_files = [
        "test_epic2_base.yaml",
        "test_epic2_neural_enabled.yaml",
        "test_epic2_graph_enabled.yaml", 
        "test_epic2_all_features.yaml"
    ]
    
    for config_file in config_files:
        try:
            config = load_config(config_file)
            assert config is not None
            assert hasattr(config, 'retriever')
        except Exception as e:
            pytest.fail(f"Configuration {config_file} failed to parse: {e}")
```

### 4.2 Sub-Component Instantiation Validation

#### 4.2.1 Sub-Component Type Validation

**Test Category**: Correct Sub-Component Creation

```python
def test_subcomponent_instantiation():
    """Test configurations create expected sub-components."""
    
    # Test base configuration
    config = load_config("test_epic2_base.yaml")
    retriever = ComponentFactory.create_retriever(config.retriever)
    assert type(retriever.reranker).__name__ == "IdentityReranker"
    assert type(retriever.fusion_strategy).__name__ == "RRFFusion"
    
    # Test neural configuration
    config = load_config("test_epic2_neural_enabled.yaml")
    retriever = ComponentFactory.create_retriever(config.retriever)
    assert type(retriever.reranker).__name__ == "NeuralReranker"
    assert type(retriever.fusion_strategy).__name__ == "RRFFusion"
    
    # Test graph configuration
    config = load_config("test_epic2_graph_enabled.yaml")
    retriever = ComponentFactory.create_retriever(config.retriever)
    assert type(retriever.reranker).__name__ == "IdentityReranker"
    assert type(retriever.fusion_strategy).__name__ == "GraphEnhancedRRFFusion"
    
    # Test complete configuration
    config = load_config("test_epic2_all_features.yaml")
    retriever = ComponentFactory.create_retriever(config.retriever)
    assert type(retriever.reranker).__name__ == "NeuralReranker"
    assert type(retriever.fusion_strategy).__name__ == "GraphEnhancedRRFFusion"
```

#### 4.2.2 Configuration Parameter Validation

**Test Category**: Configuration Parameter Propagation

```python
def test_configuration_parameter_propagation():
    """Test configuration parameters propagate to sub-components."""
    
    # Test neural reranking parameters
    config = load_config("test_epic2_neural_enabled.yaml")
    retriever = ComponentFactory.create_retriever(config.retriever)
    neural_reranker = retriever.reranker
    
    assert neural_reranker.model_name == "cross-encoder/ms-marco-MiniLM-L6-v2"
    assert neural_reranker.batch_size == 32
    assert neural_reranker.max_candidates == 100
    
    # Test graph enhancement parameters
    config = load_config("test_epic2_graph_enabled.yaml")
    retriever = ComponentFactory.create_retriever(config.retriever)
    graph_fusion = retriever.fusion_strategy
    
    assert graph_fusion.similarity_threshold == 0.65
    assert graph_fusion.max_connections_per_document == 15
    assert graph_fusion.use_pagerank == True
```

### 4.3 Feature Activation Validation

#### 4.3.1 Feature Enable/Disable Tests

**Test Category**: Feature Activation Control

```python
def test_feature_activation_control():
    """Test Epic 2 features activate/deactivate correctly."""
    
    # Test neural reranking activation
    config = load_config("test_epic2_neural_enabled.yaml")
    retriever = ComponentFactory.create_retriever(config.retriever)
    assert retriever.reranker.is_enabled()
    
    # Test graph enhancement activation
    config = load_config("test_epic2_graph_enabled.yaml")
    retriever = ComponentFactory.create_retriever(config.retriever)
    assert retriever.fusion_strategy.graph_enabled
    
    # Test base configuration (no features)
    config = load_config("test_epic2_base.yaml")
    retriever = ComponentFactory.create_retriever(config.retriever)
    assert not hasattr(retriever.reranker, 'is_enabled') or not retriever.reranker.is_enabled()
    assert not hasattr(retriever.fusion_strategy, 'graph_enabled') or not retriever.fusion_strategy.graph_enabled
```

#### 4.3.2 Feature Combination Tests

**Test Category**: Multiple Feature Activation

```python
def test_multiple_feature_activation():
    """Test multiple Epic 2 features can be activated simultaneously."""
    
    config = load_config("test_epic2_all_features.yaml")
    retriever = ComponentFactory.create_retriever(config.retriever)
    
    # Verify both features are active
    assert isinstance(retriever.reranker, NeuralReranker)
    assert retriever.reranker.is_enabled()
    assert isinstance(retriever.fusion_strategy, GraphEnhancedRRFFusion)
    assert retriever.fusion_strategy.graph_enabled
    
    # Verify no conflicts between features
    assert retriever.reranker.model_name == "cross-encoder/ms-marco-MiniLM-L6-v2"
    assert retriever.fusion_strategy.similarity_threshold == 0.65
```

### 4.4 Error Handling Validation

#### 4.4.1 Invalid Configuration Tests

**Test Category**: Configuration Error Handling

```python
def test_invalid_configuration_handling():
    """Test invalid configurations handled gracefully."""
    
    # Test invalid reranker type
    invalid_config = {
        "retriever": {
            "type": "modular_unified",
            "config": {
                "reranker": {"type": "invalid_type"},
                "fusion": {"type": "rrf"},
                "vector_index": {"type": "faiss"}
            }
        }
    }
    
    with pytest.raises(ValueError, match="Invalid reranker type"):
        ComponentFactory.create_retriever(invalid_config["retriever"])
    
    # Test missing required parameters
    invalid_config = {
        "retriever": {
            "type": "modular_unified",
            "config": {
                "reranker": {"type": "neural"},  # Missing required config
                "fusion": {"type": "rrf"},
                "vector_index": {"type": "faiss"}
            }
        }
    }
    
    with pytest.raises(ValueError, match="Missing required configuration"):
        ComponentFactory.create_retriever(invalid_config["retriever"])
```

#### 4.4.2 Configuration Validation Tests

**Test Category**: Configuration Consistency

```python
def test_configuration_consistency():
    """Test configuration consistency validation."""
    
    # Test conflicting parameters
    invalid_config = {
        "retriever": {
            "type": "modular_unified",
            "config": {
                "reranker": {
                    "type": "neural",
                    "config": {"enabled": False}  # Conflicting with neural type
                },
                "fusion": {"type": "rrf"},
                "vector_index": {"type": "faiss"}
            }
        }
    }
    
    with pytest.raises(ValueError, match="Configuration conflict"):
        ComponentFactory.create_retriever(invalid_config["retriever"])
```

---

## 5. Automated Configuration Validation

### 5.1 Continuous Integration Tests

#### 5.1.1 Configuration Test Suite

**Test Execution Framework**:
```python
class Epic2ConfigurationTestSuite:
    """Comprehensive Epic 2 configuration validation suite."""
    
    def __init__(self):
        self.config_files = [
            "test_epic2_base.yaml",
            "test_epic2_neural_enabled.yaml",
            "test_epic2_graph_enabled.yaml",
            "test_epic2_all_features.yaml"
        ]
        self.test_results = {}
    
    def run_all_tests(self):
        """Run all configuration validation tests."""
        for config_file in self.config_files:
            self.test_results[config_file] = self._validate_configuration(config_file)
        return self.test_results
    
    def _validate_configuration(self, config_file):
        """Validate individual configuration file."""
        results = {
            "schema_valid": False,
            "parsing_valid": False,
            "instantiation_valid": False,
            "features_valid": False,
            "errors": []
        }
        
        try:
            # Schema validation
            config = load_config(config_file)
            results["schema_valid"] = True
            
            # Parsing validation
            retriever = ComponentFactory.create_retriever(config.retriever)
            results["parsing_valid"] = True
            
            # Instantiation validation
            self._validate_subcomponents(retriever, config_file)
            results["instantiation_valid"] = True
            
            # Feature validation
            self._validate_features(retriever, config_file)
            results["features_valid"] = True
            
        except Exception as e:
            results["errors"].append(str(e))
        
        return results
```

#### 5.1.2 CI Pipeline Integration

**GitHub Actions Configuration**:
```yaml
name: Epic 2 Configuration Validation
on: [push, pull_request]

jobs:
  config-validation:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        pip install pytest
    
    - name: Run configuration validation tests
      run: |
        python -m pytest tests/test_epic2_configuration_validation.py -v
        python scripts/validate_all_epic2_configs.py
```

### 5.2 Configuration Validation Scripts

#### 5.2.1 Validation Script

**File**: `scripts/validate_all_epic2_configs.py`

```python
#!/usr/bin/env python3
"""
Epic 2 Configuration Validation Script

Validates all Epic 2 configuration files for correctness,
consistency, and feature activation.
"""

import sys
from pathlib import Path
from typing import Dict, List, Any

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.config import load_config
from src.core.component_factory import ComponentFactory
from src.components.retrievers.rerankers.neural_reranker import NeuralReranker
from src.components.retrievers.rerankers.identity_reranker import IdentityReranker
from src.components.retrievers.fusion.graph_enhanced_rrf_fusion import GraphEnhancedRRFFusion
from src.components.retrievers.fusion.rrf_fusion import RRFFusion

def validate_epic2_configurations():
    """Validate all Epic 2 configuration files."""
    
    config_files = [
        "test_epic2_base.yaml",
        "test_epic2_neural_enabled.yaml",
        "test_epic2_graph_enabled.yaml",
        "test_epic2_all_features.yaml"
    ]
    
    results = {}
    
    for config_file in config_files:
        print(f"\n🔍 Validating {config_file}...")
        results[config_file] = validate_configuration(config_file)
    
    # Print summary
    print("\n" + "="*60)
    print("EPIC 2 CONFIGURATION VALIDATION SUMMARY")
    print("="*60)
    
    total_configs = len(config_files)
    valid_configs = sum(1 for r in results.values() if r["valid"])
    
    print(f"Total configurations: {total_configs}")
    print(f"Valid configurations: {valid_configs}")
    print(f"Success rate: {valid_configs/total_configs*100:.1f}%")
    
    if valid_configs == total_configs:
        print("✅ All Epic 2 configurations are valid!")
        return True
    else:
        print("❌ Some Epic 2 configurations are invalid!")
        return False

def validate_configuration(config_file: str) -> Dict[str, Any]:
    """Validate individual configuration file."""
    result = {
        "valid": False,
        "errors": [],
        "warnings": [],
        "features": []
    }
    
    try:
        # Load configuration
        config_path = Path(f"config/{config_file}")
        config = load_config(config_path)
        
        # Create retriever
        retriever = ComponentFactory.create_retriever(config.retriever)
        
        # Validate sub-components
        reranker_type = type(retriever.reranker).__name__
        fusion_type = type(retriever.fusion_strategy).__name__
        
        print(f"  📋 Reranker: {reranker_type}")
        print(f"  📋 Fusion: {fusion_type}")
        
        # Detect Epic 2 features
        features = []
        if isinstance(retriever.reranker, NeuralReranker):
            features.append("neural_reranking")
            print(f"  🧠 Neural reranking enabled")
        
        if isinstance(retriever.fusion_strategy, GraphEnhancedRRFFusion):
            features.append("graph_enhancement")
            print(f"  🕸️  Graph enhancement enabled")
        
        if not features:
            print(f"  📝 Basic configuration (no Epic 2 features)")
        
        result["features"] = features
        result["valid"] = True
        print(f"  ✅ Configuration valid")
        
    except Exception as e:
        result["errors"].append(str(e))
        print(f"  ❌ Configuration invalid: {e}")
    
    return result

if __name__ == "__main__":
    success = validate_epic2_configurations()
    sys.exit(0 if success else 1)
```

#### 5.2.2 Quick Validation Script

**File**: `scripts/quick_config_check.py`

```python
#!/usr/bin/env python3
"""
Quick Epic 2 Configuration Check

Performs rapid validation of Epic 2 configuration files.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.config import load_config
from src.core.component_factory import ComponentFactory

def quick_config_check():
    """Perform quick validation of Epic 2 configurations."""
    
    configs = {
        "Base": "test_epic2_base.yaml",
        "Neural": "test_epic2_neural_enabled.yaml", 
        "Graph": "test_epic2_graph_enabled.yaml",
        "Complete": "test_epic2_all_features.yaml"
    }
    
    print("🚀 Epic 2 Configuration Quick Check")
    print("="*40)
    
    for name, config_file in configs.items():
        try:
            config = load_config(f"config/{config_file}")
            retriever = ComponentFactory.create_retriever(config.retriever)
            
            reranker = type(retriever.reranker).__name__
            fusion = type(retriever.fusion_strategy).__name__
            
            print(f"{name:>10}: ✅ {reranker} + {fusion}")
            
        except Exception as e:
            print(f"{name:>10}: ❌ {e}")
    
    print("\n🎯 Quick check complete!")

if __name__ == "__main__":
    quick_config_check()
```

---

## 6. Configuration Troubleshooting Guide

### 6.1 Common Configuration Issues

#### 6.1.1 Neural Reranking Configuration Issues

**Issue**: "Neural reranking model not found"
```yaml
# Problem configuration
reranker:
  type: "neural"
  config:
    model_name: "invalid-model-name"  # Invalid model
```

**Solution**:
```yaml
# Correct configuration
reranker:
  type: "neural"
  config:
    enabled: true
    model_name: "cross-encoder/ms-marco-MiniLM-L6-v2"  # Valid model
    device: "auto"
    batch_size: 32
    max_candidates: 100
```

**Validation Test**:
```python
def test_neural_model_validation():
    """Test neural reranking model validation."""
    config = load_config("test_epic2_neural_enabled.yaml")
    retriever = ComponentFactory.create_retriever(config.retriever)
    
    # Verify model can be loaded
    assert retriever.reranker.model_name == "cross-encoder/ms-marco-MiniLM-L6-v2"
    assert retriever.reranker.is_enabled()
```

#### 6.1.2 Graph Enhancement Configuration Issues

**Issue**: "Graph configuration invalid"
```yaml
# Problem configuration
fusion:
  type: "graph_enhanced_rrf"
  config:
    graph_enabled: false  # Contradictory setting
```

**Solution**:
```yaml
# Correct configuration
fusion:
  type: "graph_enhanced_rrf"
  config:
    k: 60
    weights:
      dense: 0.4
      sparse: 0.3
      graph: 0.3
    graph_enabled: true
    similarity_threshold: 0.65
    max_connections_per_document: 15
```

**Validation Test**:
```python
def test_graph_configuration_validation():
    """Test graph enhancement configuration validation."""
    config = load_config("test_epic2_graph_enabled.yaml")
    retriever = ComponentFactory.create_retriever(config.retriever)
    
    # Verify graph configuration
    assert retriever.fusion_strategy.graph_enabled
    assert retriever.fusion_strategy.similarity_threshold == 0.65
```

### 6.2 Configuration Debugging

#### 6.2.1 Configuration Inspection Tools

**Debug Script**: `scripts/inspect_config.py`

```python
#!/usr/bin/env python3
"""
Configuration Inspection Tool

Provides detailed inspection of Epic 2 configuration files.
"""

import sys
from pathlib import Path
import json

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.config import load_config
from src.core.component_factory import ComponentFactory

def inspect_configuration(config_file: str):
    """Inspect Epic 2 configuration in detail."""
    
    print(f"🔍 Inspecting {config_file}")
    print("="*50)
    
    try:
        # Load configuration
        config = load_config(f"config/{config_file}")
        
        # Print raw configuration
        print("📋 Raw Configuration:")
        print(json.dumps(config.retriever.dict(), indent=2))
        print()
        
        # Create retriever
        retriever = ComponentFactory.create_retriever(config.retriever)
        
        # Inspect sub-components
        print("🔧 Sub-Components:")
        print(f"  Reranker: {type(retriever.reranker).__name__}")
        print(f"  Fusion: {type(retriever.fusion_strategy).__name__}")
        print(f"  Vector Index: {type(retriever.vector_index).__name__}")
        print()
        
        # Inspect feature activation
        print("⚡ Feature Activation:")
        
        # Neural reranking
        if hasattr(retriever.reranker, 'is_enabled'):
            enabled = retriever.reranker.is_enabled()
            print(f"  Neural Reranking: {'✅' if enabled else '❌'}")
            if enabled:
                print(f"    Model: {retriever.reranker.model_name}")
                print(f"    Batch Size: {retriever.reranker.batch_size}")
        else:
            print(f"  Neural Reranking: ❌")
        
        # Graph enhancement
        if hasattr(retriever.fusion_strategy, 'graph_enabled'):
            enabled = retriever.fusion_strategy.graph_enabled
            print(f"  Graph Enhancement: {'✅' if enabled else '❌'}")
            if enabled:
                print(f"    Threshold: {retriever.fusion_strategy.similarity_threshold}")
                print(f"    Max Connections: {retriever.fusion_strategy.max_connections_per_document}")
        else:
            print(f"  Graph Enhancement: ❌")
        
    except Exception as e:
        print(f"❌ Error inspecting configuration: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        inspect_configuration(sys.argv[1])
    else:
        print("Usage: python inspect_config.py <config_file>")
        print("Example: python inspect_config.py test_epic2_all_features.yaml")
```

#### 6.2.2 Configuration Comparison Tool

**Comparison Script**: `scripts/compare_configs.py`

```python
#!/usr/bin/env python3
"""
Configuration Comparison Tool

Compares different Epic 2 configurations side-by-side.
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.config import load_config
from src.core.component_factory import ComponentFactory

def compare_configurations(config1: str, config2: str):
    """Compare two Epic 2 configurations."""
    
    print(f"🔍 Comparing {config1} vs {config2}")
    print("="*60)
    
    try:
        # Load configurations
        cfg1 = load_config(f"config/{config1}")
        cfg2 = load_config(f"config/{config2}")
        
        # Create retrievers
        ret1 = ComponentFactory.create_retriever(cfg1.retriever)
        ret2 = ComponentFactory.create_retriever(cfg2.retriever)
        
        # Compare sub-components
        print("🔧 Sub-Component Comparison:")
        
        reranker1 = type(ret1.reranker).__name__
        reranker2 = type(ret2.reranker).__name__
        print(f"  Reranker: {reranker1} vs {reranker2}")
        
        fusion1 = type(ret1.fusion_strategy).__name__
        fusion2 = type(ret2.fusion_strategy).__name__
        print(f"  Fusion: {fusion1} vs {fusion2}")
        
        # Compare features
        print("\n⚡ Feature Comparison:")
        
        # Neural reranking
        neural1 = hasattr(ret1.reranker, 'is_enabled') and ret1.reranker.is_enabled()
        neural2 = hasattr(ret2.reranker, 'is_enabled') and ret2.reranker.is_enabled()
        print(f"  Neural: {'✅' if neural1 else '❌'} vs {'✅' if neural2 else '❌'}")
        
        # Graph enhancement
        graph1 = hasattr(ret1.fusion_strategy, 'graph_enabled') and ret1.fusion_strategy.graph_enabled
        graph2 = hasattr(ret2.fusion_strategy, 'graph_enabled') and ret2.fusion_strategy.graph_enabled
        print(f"  Graph: {'✅' if graph1 else '❌'} vs {'✅' if graph2 else '❌'}")
        
        # Summary
        print(f"\n📊 Summary:")
        print(f"  {config1}: {reranker1} + {fusion1}")
        print(f"  {config2}: {reranker2} + {fusion2}")
        
    except Exception as e:
        print(f"❌ Error comparing configurations: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 2:
        compare_configurations(sys.argv[1], sys.argv[2])
    else:
        print("Usage: python compare_configs.py <config1> <config2>")
        print("Example: python compare_configs.py test_epic2_base.yaml test_epic2_all_features.yaml")
```

---

## 7. Configuration Best Practices

### 7.1 Configuration Design Principles

#### 7.1.1 Clarity and Consistency

**Principle**: Configuration should be self-documenting and consistent
```yaml
# Good: Clear sub-component configuration
reranker:
  type: "neural"           # Clear type specification
  config:
    enabled: true          # Explicit activation
    model_name: "cross-encoder/ms-marco-MiniLM-L6-v2"  # Full model name
    device: "auto"         # Clear device specification
    batch_size: 32         # Explicit batch size
    max_candidates: 100    # Clear limits

# Bad: Unclear or inconsistent configuration
reranker:
  type: "neural"
  config:
    model: "MiniLM"        # Ambiguous model name
    enabled: 1             # Inconsistent boolean representation
```

#### 7.1.2 Modularity and Reusability

**Principle**: Configuration should be modular and reusable
```yaml
# Good: Modular configuration with clear sections
retriever:
  type: "modular_unified"
  config:
    # Vector index configuration
    vector_index: &vector_config
      type: "faiss"
      config:
        index_type: "IndexFlatIP"
        normalize_embeddings: true
    
    # Reusable sparse configuration
    sparse: &sparse_config
      type: "bm25"
      config:
        k1: 1.2
        b: 0.75
    
    # Epic 2 specific configuration
    reranker:
      type: "neural"
      config:
        enabled: true
        model_name: "cross-encoder/ms-marco-MiniLM-L6-v2"
```

### 7.2 Configuration Testing Best Practices

#### 7.2.1 Comprehensive Test Coverage

**Practice**: Test all configuration combinations
```python
def test_all_configuration_combinations():
    """Test all valid configuration combinations."""
    
    reranker_types = ["identity", "neural"]
    fusion_types = ["rrf", "graph_enhanced_rrf"]
    
    for reranker_type in reranker_types:
        for fusion_type in fusion_types:
            config = create_test_config(reranker_type, fusion_type)
            retriever = ComponentFactory.create_retriever(config)
            
            # Validate configuration
            assert retriever is not None
            assert type(retriever.reranker).__name__.lower().startswith(reranker_type)
            assert type(retriever.fusion_strategy).__name__.lower().startswith(fusion_type.replace("_", ""))
```

#### 7.2.2 Error Condition Testing

**Practice**: Test all error conditions
```python
def test_configuration_error_conditions():
    """Test configuration error conditions."""
    
    error_conditions = [
        {"reranker": {"type": "invalid"}},
        {"fusion": {"type": "invalid"}},
        {"reranker": {"type": "neural", "config": {}}},  # Missing config
        {"fusion": {"type": "graph_enhanced_rrf", "config": {"graph_enabled": False}}}  # Inconsistent
    ]
    
    for error_config in error_conditions:
        with pytest.raises(ValueError):
            ComponentFactory.create_retriever(error_config)
```

---

## 8. Configuration Maintenance

### 8.1 Configuration Version Control

#### 8.1.1 Configuration Versioning

**Practice**: Version configuration files and track changes
```yaml
# config/test_epic2_all_features.yaml
# Version: 1.0
# Last Updated: 2025-07-16
# Changes: Added neural reranking batch size optimization

retriever:
  type: "modular_unified"
  config:
    # Configuration version for tracking
    version: "1.0"
    
    # Sub-component configurations
    reranker:
      type: "neural"
      config:
        enabled: true
        model_name: "cross-encoder/ms-marco-MiniLM-L6-v2"
        batch_size: 32  # Updated from 16 for better performance
```

#### 8.1.2 Configuration Migration

**Practice**: Provide migration tools for configuration updates
```python
def migrate_configuration_v1_to_v2(config_path: str):
    """Migrate configuration from v1 to v2 format."""
    
    config = load_config(config_path)
    
    # Migration logic
    if config.retriever.config.get("version", "1.0") == "1.0":
        # Update batch size
        if config.retriever.config.reranker.type == "neural":
            config.retriever.config.reranker.config.batch_size = 32
        
        # Update version
        config.retriever.config.version = "2.0"
        
        # Save updated configuration
        save_config(config, config_path)
```

### 8.2 Configuration Documentation

#### 8.2.1 Configuration Schema Documentation

**Practice**: Document configuration schema and options
```yaml
# Configuration Schema Documentation
retriever:
  type: "modular_unified"  # Required: Always use modular_unified for Epic 2
  config:
    # Neural Reranking Configuration
    reranker:
      type: "neural" | "identity"  # Required: Sub-component type
      config:
        enabled: boolean           # Required for neural: Feature activation
        model_name: string         # Required for neural: HuggingFace model name
        device: "auto" | "cpu" | "cuda"  # Optional: Device selection
        batch_size: integer        # Optional: Batch size (default: 32)
        max_candidates: integer    # Optional: Max candidates (default: 100)
    
    # Graph Enhancement Configuration
    fusion:
      type: "rrf" | "graph_enhanced_rrf"  # Required: Fusion strategy
      config:
        k: integer                 # Required: RRF parameter
        weights:
          dense: float            # Required: Dense weight
          sparse: float           # Required: Sparse weight
          graph: float            # Required for graph: Graph weight
        graph_enabled: boolean     # Required for graph: Feature activation
        similarity_threshold: float # Optional: Graph similarity threshold
```

#### 8.2.2 Configuration Examples

**Practice**: Provide comprehensive configuration examples
```yaml
# Example 1: High Performance Configuration
retriever:
  type: "modular_unified"
  config:
    reranker:
      type: "neural"
      config:
        enabled: true
        model_name: "cross-encoder/ms-marco-MiniLM-L6-v2"
        batch_size: 16  # Smaller batch for lower latency
        max_candidates: 50  # Fewer candidates for speed
    
    fusion:
      type: "rrf"  # Basic fusion for performance
      config:
        k: 60
        weights:
          dense: 0.7
          sparse: 0.3

# Example 2: High Quality Configuration
retriever:
  type: "modular_unified"
  config:
    reranker:
      type: "neural"
      config:
        enabled: true
        model_name: "cross-encoder/ms-marco-MiniLM-L6-v2"
        batch_size: 32  # Larger batch for better throughput
        max_candidates: 100  # More candidates for quality
    
    fusion:
      type: "graph_enhanced_rrf"  # Advanced fusion for quality
      config:
        k: 60
        weights:
          dense: 0.4
          sparse: 0.3
          graph: 0.3
        graph_enabled: true
        similarity_threshold: 0.65
        max_connections_per_document: 15
```

---

## 9. Conclusion

This Epic 2 Configuration Validation document provides comprehensive procedures for validating YAML-driven Epic 2 feature activation within ModularUnifiedRetriever. The validation approach ensures that configuration changes produce the expected sub-component behavior while maintaining system stability and performance.

**Key Validation Principles**:
- Configuration-driven sub-component selection
- Comprehensive test coverage for all configuration combinations
- Automated validation with CI/CD integration
- Clear error handling and debugging procedures

**Production Readiness**:
- All Epic 2 configurations validated and tested
- Automated validation ensures configuration consistency
- Clear troubleshooting and debugging procedures
- Comprehensive documentation for maintenance and extension

The validation framework provides confidence that Epic 2 configurations will work correctly in production environments while maintaining the flexibility to adapt to future requirements.

---

## References

- [Epic 2 Integration Test Plan](./epic2-integration-test-plan.md) - Comprehensive testing framework
- [EPIC2_TESTING_GUIDE.md](../EPIC2_TESTING_GUIDE.md) - Testing procedures
- [Epic 2 Performance Benchmarks](./epic2-performance-benchmarks.md) - Performance targets
- [Master Test Strategy](./master-test-strategy.md) - Overall testing approach