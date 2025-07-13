# Epic 2 Quick Reference Card

## 🎯 Current Focus: Week 1 - Weaviate Backend
**Task 2.1**: Implement Weaviate adapter (25 hours)
**Status**: Starting implementation

## 📁 Key Files to Create
```
src/components/retrievers/backends/
├── __init__.py
├── weaviate_backend.py       # Main adapter implementation
├── weaviate_config.py        # Configuration classes
├── schema/
│   ├── document_schema.py    # Weaviate schema definition
│   └── index_config.py       # Index settings
└── migration/
    ├── faiss_to_weaviate.py  # Migration script
    └── data_validator.py     # Consistency checker
```

## 🔧 Implementation Checklist
- [ ] Create directory structure
- [ ] Implement WeaviateAdapter class (follow OllamaAdapter pattern)
- [ ] Define document schema for Weaviate
- [ ] Implement CRUD operations (index, search, delete, update)
- [ ] Add batch import optimization
- [ ] Create migration script from FAISS
- [ ] Add comprehensive error handling
- [ ] Implement health check and connection management
- [ ] Add performance instrumentation
- [ ] Create unit tests
- [ ] Create integration tests
- [ ] Benchmark vs FAISS

## 🎨 Architecture Pattern
```python
class WeaviateAdapter:
    """Adapter for Weaviate vector database following OllamaAdapter pattern."""
    
    def __init__(self, config: WeaviateConfig):
        # Initialize connection
        # Setup schema
        # Configure batch settings
    
    def index_documents(self, documents: List[Document]) -> None:
        # Batch import with error handling
    
    def search(self, query_vector: np.ndarray, top_k: int) -> List[SearchResult]:
        # Vector search with metadata filtering
    
    def migrate_from_faiss(self, faiss_index: FAISSIndex) -> None:
        # Migration logic with progress tracking
```

## 📊 Success Metrics
- Migration completes without data loss
- Search latency comparable to FAISS (<10ms)
- Batch import >1000 docs/second
- 100% test coverage for adapter
- Graceful error handling for connection issues

## 🔗 Reference Patterns
- `src/components/generators/answer_generator.py:OllamaAdapter` - Adapter pattern
- `src/components/retrievers/modular_unified_retriever.py:FAISSIndex` - Current backend
- `src/core/component_factory.py` - How to register new component types

## ⚡ Performance Considerations
- Use batch operations for import
- Implement connection pooling
- Add caching for frequent queries
- Support async operations where possible
- Monitor memory usage during migration

## 🧪 Test Requirements
- Unit tests for all CRUD operations
- Integration test with real Weaviate instance
- Migration test with sample data
- Performance benchmark suite
- Error handling test scenarios

## 📝 Documentation Needs
- API documentation for WeaviateAdapter
- Migration guide from FAISS
- Configuration examples
- Performance tuning guide
- Troubleshooting section