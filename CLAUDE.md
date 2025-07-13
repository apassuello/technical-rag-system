# RAG Portfolio Development Context - Epic 2

## Project Overview
Building a 3-project RAG portfolio for ML Engineer positions in Swiss tech market.
Currently working on **Project 1: Technical Documentation RAG System - Epic 2: Advanced Hybrid Retriever**.

## Developer Background
- Arthur Passuello, transitioning from Embedded Systems to AI/ML
- 2.5 years medical device firmware experience
- Recent 7-week ML intensive (transformers from scratch, multimodal systems)
- Strong optimization and production mindset from embedded background
- Using M4-Pro Apple Silicon Mac with MPS acceleration

## Current Development Environment
- Python 3.11 in conda environment `rag-portfolio`
- PyTorch with Metal/MPS support
- Key libraries: transformers, sentence-transformers, langchain, faiss-cpu
- **New for Epic 2**: weaviate-client, networkx, plotly, keras/tensorflow
- IDE: Cursor with AI assistant
- Git: SSH-based workflow

## Project 1 Technical Stack
- **Embeddings**: sentence-transformers/all-MiniLM-L6-v2 (local inference)
- **Vector Store**: FAISS (local) + **Weaviate** (Epic 2 addition)
- **LLM**: Ollama with llama3.2:3b model
- **Deployment Target**: Streamlit on HuggingFace Spaces
- **Evaluation**: RAGAS framework
- **Analytics**: Plotly Dash (Epic 2 addition)

## Current Development Status

### System Foundation (Complete)
- **6-Component Architecture**: All components implemented with modular design
- **Validation Score**: 90.2% internal testing metric
- **Performance**: 565K chars/sec processing, <10ms retrieval latency
- **Testing**: 122 test cases with defined acceptance criteria

### Epic 2: Advanced Hybrid Retriever (In Progress)
**Started**: [Current Date]
**Duration**: 4-5 weeks (160-200 hours)
**Current Week**: Week 1 - Weaviate Backend Implementation

#### Epic 2 Objectives
1. **Weaviate Integration**: Alternative vector store with advanced features
2. **Knowledge Graph**: Document relationship analysis with NetworkX
3. **Hybrid Search**: Dense + Sparse + Graph-based retrieval
4. **Neural Reranking**: Cross-encoder with Keras/TensorFlow
5. **Analytics Dashboard**: Real-time Plotly visualization
6. **A/B Testing**: Production-grade experimentation

#### Current Task: Weaviate Backend (Task 2.1)
- Implementing Weaviate adapter following existing patterns
- Creating migration tools from FAISS
- Maintaining backward compatibility
- Target: 25 hours for complete implementation

## Development Philosophy
- **Production-first**: Every component deployment-ready
- **Modular design**: Small, testable, single-purpose functions
- **Swiss market aligned**: Quality, reliability, thorough documentation
- **Optimization mindset**: Leverage embedded systems background
- **Incremental enhancement**: Build on solid foundation

## Architecture Guidelines for Epic 2

### Component Structure
```
src/components/retrievers/
├── advanced_retriever.py      # New main retriever
├── backends/                  # Multi-backend support
│   ├── weaviate_backend.py   # Current implementation focus
│   └── faiss_backend.py      # Existing, to be wrapped
├── graph/                     # Document relationships
├── hybrid/                    # Search strategies
├── reranking/                # Neural models
├── analytics/                 # Dashboard
└── experiments/               # A/B testing
```

### Design Patterns
- **Adapter Pattern**: For Weaviate (external service)
- **Strategy Pattern**: For retrieval backends
- **Factory Pattern**: Integration with ComponentFactory
- **Observer Pattern**: For metrics collection

### Integration Requirements
- Extend ModularUnifiedRetriever, don't replace
- Register in ComponentFactory as "advanced" type
- Support configuration-driven feature toggles
- Maintain <700ms P95 latency target

## Key Implementation Files

### Existing (Reference)
- `src/components/retrievers/modular_unified_retriever.py` - Base implementation
- `src/core/interfaces.py` - Retriever interface
- `src/core/component_factory.py` - Component registration
- `src/components/generators/answer_generator.py` - Adapter pattern example

### New (Epic 2)
- `src/components/retrievers/backends/weaviate_backend.py` - Current focus
- `src/components/retrievers/backends/weaviate_config.py` - Configuration
- `src/components/retrievers/backends/migration/faiss_to_weaviate.py` - Migration tools

## Quality Standards
- **Code**: Type hints, docstrings, error handling
- **Performance**: Instrumentation on all operations
- **Testing**: Unit + Integration + Performance tests
- **Documentation**: API docs + Usage examples
- **Monitoring**: Metrics collection built-in

## Current Session Guidelines
1. Focus on Weaviate backend implementation
2. Follow adapter pattern from OllamaAdapter
3. Ensure backward compatibility
4. Add comprehensive error handling
5. Include migration capabilities
6. Benchmark against FAISS baseline

## Performance Targets (Epic 2)
- Retrieval latency: <500ms P95 (base)
- With reranking: <700ms P95 (total)
- Retrieval recall: >85%
- Precision improvement: >15% with reranking
- Dashboard refresh: <1 second

## Next Steps Queue
1. Complete Weaviate adapter implementation
2. Test migration script with RISC-V documents
3. Benchmark Weaviate vs FAISS performance
4. Begin graph construction module
5. Design hybrid fusion strategies

## Important Notes
- Maintain all existing functionality
- Epic 2 enhances, doesn't replace
- Performance is critical (embedded mindset)
- Quality over speed in implementation
- Document all design decisions

## Session Memory
- Epic 2 started on: [Current Date]
- Last component worked on: Weaviate Backend
- Current blocker: None
- Next milestone: Working Weaviate adapter with migration