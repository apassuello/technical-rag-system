# Initial Prompt: Fix Epic 2 Architecture Violation

## Task Overview
Fix a critical architecture violation in the Epic 2 RAG system where the implementation incorrectly creates `AdvancedRetriever` as a separate component type instead of using the standard `ModularUnifiedRetriever` with enhanced sub-components.

## Context Summary
The user identified that regardless of configuration (basic or Epic 2), the system should ALWAYS use `ModularUnifiedRetriever` as the main component. Epic 2 features should be achieved through enhanced sub-components within the ModularUnifiedRetriever architecture, not by creating a separate component type.

## Current Problem
```bash
# Epic 2 configuration currently creates:
🏭 ComponentFactory created: AdvancedRetriever (type=retriever_advanced, ...)
  └─ Sub-components: GraphEnhancedRRFFusion, NeuralReranker
```

## Required Solution
```bash
# Epic 2 configuration should create:
🏭 ComponentFactory created: ModularUnifiedRetriever (type=retriever_modular_unified, ...)
  └─ Sub-components: GraphEnhancedRRFFusion, NeuralReranker
```

## Immediate Actions Needed

1. **Fix Configuration Architecture**:
   - Change `config/advanced_test.yaml` from `type: "advanced"` to `type: "modular_unified"`
   - Configure Epic 2 sub-components within the modular_unified structure

2. **Fix Component Factory**:
   - Remove or reposition `"advanced"` from ComponentFactory registry
   - Ensure Epic 2 creates `ModularUnifiedRetriever` with enhanced sub-components

3. **Handle AdvancedRetriever Class**:
   - Determine if it should be removed, converted to config helper, or kept as reference

## Key Files to Examine First
1. `config/advanced_test.yaml` - Epic 2 configuration file
2. `src/core/component_factory.py` - Component registry and creation logic
3. `src/components/retrievers/modular_unified_retriever.py` - Target architecture (lines 126-149)
4. `src/components/retrievers/advanced_retriever.py` - Problematic separate component

## Architecture Reference
ModularUnifiedRetriever has 4 sub-component slots:
- `vector_index`: FAISSIndex | WeaviateIndex
- `sparse_retriever`: BM25Retriever  
- `fusion_strategy`: RRFFusion | **GraphEnhancedRRFFusion** (Epic 2)
- `reranker`: IdentityReranker | **NeuralReranker** (Epic 2)

## Validation
After fixes, run:
```bash
python3 tests/run_comprehensive_tests.py --epic2
```
Should show `ModularUnifiedRetriever` created with Epic 2 sub-components.

## Success Criteria
- ✅ Both basic and Epic 2 configs create `ModularUnifiedRetriever`
- ✅ Epic 2 config uses `GraphEnhancedRRFFusion` + `NeuralReranker` sub-components
- ✅ Basic config uses `RRFFusion` + `IdentityReranker` sub-components
- ✅ No `AdvancedRetriever` appears in component creation logs

Please start by examining the current configuration structure and component factory logic to understand how to properly implement Epic 2 features within the standard ModularUnifiedRetriever architecture.