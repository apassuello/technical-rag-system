# Initial Prompt for Epic 2 Implementation

## Context Gathering Instructions

Before starting implementation, please:

1. **Read the context files**:
   - `.claude/sessions/EPIC2_IMPLEMENTER_CONTEXT.md` - Session-specific context
   - `docs/epics/epic-2-hybrid-retriever.md` - Full epic description
   - `CLAUDE.md` - Project overview and standards

2. **Analyze current implementation**:
   - `src/components/retrievers/modular_unified_retriever.py` - Current retriever to extend
   - `src/core/interfaces.py` - Retriever interface definition
   - `src/core/component_factory.py` - How to register new components
   - `config/default.yaml` - Current configuration structure

3. **Review relevant patterns**:
   - How ModularDocumentProcessor implements sub-components
   - How OllamaAdapter implements external service integration
   - How ComponentFactory handles component creation

## Initial Task Request

I need to start implementing Epic 2: Advanced Hybrid Retriever with Visual Analytics. This epic will transform our basic retriever into a sophisticated multi-strategy system with real-time analytics.

**Please begin by**:

1. Creating the initial directory structure for the advanced retriever components
2. Implementing the Weaviate backend adapter (Task 2.1) following our adapter pattern
3. Setting up the configuration schema for the new retriever
4. Creating migration scripts from FAISS to Weaviate

**Key Requirements**:
- Maintain backward compatibility with ModularUnifiedRetriever
- Follow the adapter pattern for Weaviate (external service)
- Support both FAISS and Weaviate backends simultaneously
- Include comprehensive error handling and fallback mechanisms
- Add performance instrumentation from the start

**Success Criteria for this session**:
- Weaviate adapter fully implemented and tested
- Migration script working for our test documents
- Configuration properly integrated
- Basic performance benchmarks comparing FAISS vs Weaviate

Please start by analyzing the current retriever implementation and proposing the structure for the Weaviate backend integration.