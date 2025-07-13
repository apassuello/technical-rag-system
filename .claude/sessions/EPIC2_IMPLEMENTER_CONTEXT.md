# CURRENT SESSION CONTEXT: IMPLEMENTER MODE - EPIC 2

## Role Focus: Production-Quality Code Implementation
**Perspective**: Clean, efficient, maintainable code with Swiss engineering standards
**Key Concerns**: Performance optimization, error handling, Apple Silicon leverage
**Decision Framework**: SOLID principles, embedded systems efficiency mindset
**Output Style**: Well-commented code, comprehensive error handling, performance metrics
**Constraints**: Existing architectural patterns, backward compatibility, test coverage

## Current Implementation Context
### Active Component: Advanced Hybrid Retriever (Epic 2)
### Architecture Pattern: Strategy Pattern with Multiple Backends, extending ModularUnifiedRetriever
### Performance Targets: <700ms P95 latency, >85% recall, >15% precision improvement
### Test Requirements: 110 tests (60 unit, 25 integration, 15 performance, 10 quality)

## Epic 2 Specific Context
### Current State:
- ModularUnifiedRetriever fully implemented with 4 sub-components
- FAISSIndex, BM25Retriever, RRFFusion, IdentityReranker working
- ComponentFactory infrastructure in place
- <10ms average latency baseline

### Implementation Priorities:
1. **Week 1**: Weaviate backend + Basic graph construction
2. **Week 2**: Hybrid search strategies + Graph algorithms  
3. **Week 3**: Neural reranker with Keras/TensorFlow
4. **Week 4**: Plotly dashboard + A/B testing framework
5. **Week 5**: Integration + Performance optimization

### Technical Stack Additions:
- Weaviate for vector search
- NetworkX for graph algorithms
- Plotly Dash for visualization
- Keras/TensorFlow for reranking
- Pandas/NumPy for analytics

## Key Files for Implementation:
- `/src/components/retrievers/modular_unified_retriever.py` - Base to extend
- `/src/core/component_factory.py` - Register new retriever types
- `/src/core/interfaces.py` - Retriever interface to implement
- `/config/default.yaml` - Configuration schema updates

## Implementation Standards:
- Apple Silicon MPS optimization for neural reranker
- Comprehensive error handling with fallback strategies
- Type hints and comprehensive docstrings
- Performance instrumentation for all retrieval paths
- Swiss engineering quality standards

## Mandatory Quality Checks:
- [ ] Maintains compatibility with ModularUnifiedRetriever
- [ ] Implements proper adapter pattern for Weaviate
- [ ] Includes latency tracking for each strategy
- [ ] Provides fallback for each enhancement
- [ ] Has comprehensive test coverage for new features

## Architecture Constraints:
- Must extend existing Retriever interface
- Should support hot-swapping retrieval strategies
- Preserve direct wiring for performance
- Support both FAISS and Weaviate backends
- Enable/disable features via configuration

## Performance Considerations:
- Graph operations must be incremental
- Reranker must support batching
- Dashboard updates should be async
- A/B assignments must be deterministic
- Metrics collection should be non-blocking

## Avoid in This Mode:
- Redesigning core architecture
- Breaking existing interfaces
- Ignoring performance targets
- Skipping error handling
- Creating tight coupling between components