# Load Epic 1 Multi-Model Context

**Usage**: `/epic1-context [component]`
**Examples**:
- `/epic1-context` - Load full Epic 1 context
- `/epic1-context analyzer` - Focus on query analyzer
- `/epic1-context adapters` - Focus on LLM adapters
- `/epic1-context routing` - Focus on routing engine

## Instructions

Load Epic 1 multi-model answer generator context and prepare for implementation.

## Context Loading

**Epic 1 Base Context**:
- Epic 1 specification from docs/epics/epic-1-multi-model-generator.md
- Current AnswerGenerator implementation
- Existing adapter patterns from llm_adapters/
- Configuration patterns from config/

**Component-Specific Context**:
- **analyzer**: Query classification, feature extraction, complexity scoring
- **adapters**: OpenAI/Mistral integration, cost tracking, error handling
- **routing**: Strategy pattern, model selection, fallback chains
- **integration**: AnswerGenerator enhancement, configuration schema

## Output Format

**📚 EPIC 1 CONTEXT LOADED - [Component Focus]**

**Epic Overview**:
- **Goal**: Multi-model answer generation with 40%+ cost reduction
- **Approach**: Intelligent routing based on query complexity
- **Timeline**: 1-2 weeks for complete implementation

**Current System State**:
- AnswerGenerator: Single-model with Ollama
- Adapters: Base + Ollama + HuggingFace + Mock
- Epic 2 Status: Complete with all features operational

**Implementation Plan**:
- Phase 1: Query Complexity Analyzer
- Phase 2: Multi-Model Adapters
- Phase 3: Routing Engine
- Phase 4: Integration & Testing

**Ready for**: [Specific implementation tasks based on component focus]