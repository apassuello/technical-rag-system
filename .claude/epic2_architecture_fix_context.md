# Epic 2 Architecture Fix - Session Context

## Critical Issue Identified
**Architecture Violation**: Epic 2 implementation incorrectly creates `AdvancedRetriever` as a separate component type instead of using `ModularUnifiedRetriever` with enhanced sub-components.

## Current Incorrect Implementation
```yaml
# config/advanced_test.yaml (WRONG)
retriever:
  type: "advanced"  # Creates AdvancedRetriever
```
**Result**: `ComponentFactory created: AdvancedRetriever`

## Correct Architecture Required
```yaml
# config/advanced_test.yaml (CORRECT)
retriever:
  type: "modular_unified"  # Always use ModularUnifiedRetriever
  config:
    fusion:
      type: "graph_enhanced_rrf"  # Epic 2 enhancement
    reranker:
      type: "neural"              # Epic 2 enhancement
```
**Result**: `ComponentFactory created: ModularUnifiedRetriever` with Epic 2 sub-components

## ModularUnifiedRetriever Sub-Component Architecture

The `ModularUnifiedRetriever` has exactly 4 sub-component slots:

1. **`vector_index`**: `FAISSIndex` | `WeaviateIndex` (Epic 2 adds Weaviate)
2. **`sparse_retriever`**: `BM25Retriever` (unchanged)
3. **`fusion_strategy`**: `RRFFusion` | `GraphEnhancedRRFFusion` (Epic 2 enhancement)
4. **`reranker`**: `IdentityReranker` | `NeuralReranker` (Epic 2 enhancement)

## Epic 2 Sub-Component Mapping
- **Basic**: `ModularUnifiedRetriever` + `RRFFusion` + `IdentityReranker`
- **Epic 2**: `ModularUnifiedRetriever` + `GraphEnhancedRRFFusion` + `NeuralReranker`

## Files That Need Changes

### 1. Configuration Files
- `config/advanced_test.yaml` - Change `type: "advanced"` to `type: "modular_unified"`
- Configure Epic 2 sub-components within modular_unified config structure

### 2. Component Factory
- `src/core/component_factory.py` - Remove or reposition `"advanced"` from `_RETRIEVERS` registry
- Ensure only `ModularUnifiedRetriever` is created for all retriever configurations

### 3. AdvancedRetriever Class
- `src/components/retrievers/advanced_retriever.py` - Determine if this should be:
  - Removed entirely, OR
  - Converted to a configuration helper/builder, OR
  - Kept as documentation/reference

### 4. Test Files (Recently Fixed)
- Tests were correctly updated to use configuration-based component creation
- Should work correctly once config files are fixed

## Implementation Strategy

1. **Phase 1**: Fix configuration to use `modular_unified` type
2. **Phase 2**: Configure Epic 2 sub-components properly
3. **Phase 3**: Remove `AdvancedRetriever` from runtime component creation
4. **Phase 4**: Test Epic 2 features work via `ModularUnifiedRetriever`

## Validation Criteria
- **All configurations** create `ModularUnifiedRetriever` as main component
- **Basic config** uses basic sub-components (`RRFFusion`, `IdentityReranker`)
- **Epic 2 config** uses enhanced sub-components (`GraphEnhancedRRFFusion`, `NeuralReranker`)
- **Component logs** show `ModularUnifiedRetriever` with different sub-component types

## Key Architecture References
- `src/components/retrievers/modular_unified_retriever.py` lines 89-92 (sub-component initialization)
- `src/components/retrievers/modular_unified_retriever.py` lines 126-149 (sub-component creation methods)
- Epic 2 sub-components are already implemented and available in ModularUnifiedRetriever

## Previous Session Work
- Fixed test infrastructure to use configuration-based component creation
- Epic 2 sub-components (`GraphEnhancedRRFFusion`, `NeuralReranker`) are implemented
- Test framework correctly passes configuration to all test classes

## Next Session Goal
Fix the fundamental architecture violation by ensuring Epic 2 features are delivered through proper sub-component configuration within the standard `ModularUnifiedRetriever` architecture.