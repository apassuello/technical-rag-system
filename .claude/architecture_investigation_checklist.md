# Architecture Investigation Checklist

## Files to Read First (In Order)

### 1. Configuration Analysis
- [ ] `config/advanced_test.yaml` - Current Epic 2 configuration structure
- [ ] `config/default.yaml` - Basic configuration for comparison
- [ ] Compare configuration differences and understand structure

### 2. Component Factory Analysis  
- [ ] `src/core/component_factory.py` - Lines 74-80 (`_RETRIEVERS` registry)
- [ ] Find `create_retriever` method implementation
- [ ] Understand how retriever types are mapped to classes

### 3. ModularUnifiedRetriever Architecture
- [ ] `src/components/retrievers/modular_unified_retriever.py` - Lines 89-92 (sub-component init)
- [ ] Lines 126-149 (sub-component creation methods)
- [ ] Lines 54-73 (configuration example in docstring)
- [ ] Understand exact sub-component structure and configuration format

### 4. AdvancedRetriever Analysis
- [ ] `src/components/retrievers/advanced_retriever.py` - Class definition and purpose
- [ ] Lines 30-80 (class docstring and constructor)
- [ ] Understand relationship to ModularUnifiedRetriever
- [ ] Determine if it should exist in runtime or just config

### 5. Epic 2 Sub-Components
- [ ] `src/components/retrievers/fusion/graph_enhanced_fusion.py` - Epic 2 fusion
- [ ] `src/components/retrievers/rerankers/neural_reranker.py` - Epic 2 reranker
- [ ] Verify these are properly integrated in ModularUnifiedRetriever

## Configuration Structure to Understand

### Current Advanced Test Config Pattern
```yaml
retriever:
  type: "advanced"  # WRONG - creates separate component
  config:
    # Advanced features configuration
```

### Required ModularUnified Config Pattern  
```yaml
retriever:
  type: "modular_unified"  # CORRECT - uses standard component
  config:
    vector_index:
      type: "faiss"  # or "weaviate"
    sparse:
      type: "bm25"
    fusion:
      type: "graph_enhanced_rrf"  # Epic 2 enhancement
    reranker:
      type: "neural"              # Epic 2 enhancement
```

## Key Questions to Answer

1. **Configuration Format**: What is the exact configuration structure ModularUnifiedRetriever expects?

2. **Sub-Component Mapping**: How do configuration types map to sub-component classes?
   - `fusion.type: "graph_enhanced_rrf"` → `GraphEnhancedRRFFusion`
   - `reranker.type: "neural"` → `NeuralReranker`

3. **Component Factory**: How should ComponentFactory handle Epic 2 configuration?
   - Should `"advanced"` type be removed entirely?
   - Should it be an alias for `"modular_unified"` with specific config?

4. **AdvancedRetriever Role**: What should happen to the AdvancedRetriever class?
   - Delete it entirely?
   - Convert to configuration builder/helper?
   - Keep as documentation reference?

## Testing Strategy

### Before Changes
```bash
python3 -c "
from src.core.platform_orchestrator import PlatformOrchestrator
po = PlatformOrchestrator('config/advanced_test.yaml')
print(f'Current: {type(po._components[\"retriever\"]).__name__}')
"
```

### After Changes (Expected)
```bash
python3 -c "
from src.core.platform_orchestrator import PlatformOrchestrator
po = PlatformOrchestrator('config/advanced_test.yaml')
retriever = po._components['retriever']
print(f'Component: {type(retriever).__name__}')
print(f'Fusion: {type(retriever.fusion_strategy).__name__}')
print(f'Reranker: {type(retriever.reranker).__name__}')
"
```

Expected output:
```
Component: ModularUnifiedRetriever
Fusion: GraphEnhancedRRFFusion
Reranker: NeuralReranker
```

## Implementation Plan
1. Understand current configuration structure
2. Design proper ModularUnifiedRetriever configuration for Epic 2
3. Update config files
4. Fix ComponentFactory if needed
5. Handle AdvancedRetriever class appropriately
6. Test and validate changes