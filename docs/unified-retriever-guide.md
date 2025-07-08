# UnifiedRetriever Component Guide

**Component**: UnifiedRetriever  
**Phase**: 2 - Component Consolidation  
**Status**: ✅ Production Ready  
**Location**: `src/components/retrievers/unified_retriever.py`

---

## Overview

The UnifiedRetriever consolidates the functionality of FAISSVectorStore and HybridRetriever into a single, efficient component. It provides both dense semantic search (FAISS) and sparse keyword matching (BM25) with Reciprocal Rank Fusion, eliminating abstraction layers for improved performance.

### Key Features

- **🔄 Unified Architecture**: Single component for vector storage + hybrid search
- **⚡ High Performance**: Sub-second search on 1000+ document corpus
- **🎯 Hybrid Search**: Dense semantic + sparse BM25 with RRF fusion
- **🔧 Multiple FAISS Indexes**: Support for IndexFlatIP, IndexFlatL2, IndexIVFFlat
- **🍎 Apple Silicon Optimized**: MPS acceleration for embeddings
- **📊 Comprehensive Monitoring**: Built-in stats and health reporting

---

## Quick Start

### Basic Usage

```python
from src.components.retrievers.unified_retriever import UnifiedRetriever
from src.components.embedders.sentence_transformer_embedder import SentenceTransformerEmbedder
from src.core.interfaces import Document

# Initialize embedder
embedder = SentenceTransformerEmbedder(
    model_name="sentence-transformers/all-MiniLM-L6-v2",
    use_mps=True
)

# Create unified retriever
retriever = UnifiedRetriever(
    embedder=embedder,
    dense_weight=0.7,
    embedding_dim=384,
    index_type="IndexFlatIP"
)

# Index documents
documents = [
    Document(
        content="RISC-V is an open standard instruction set architecture.",
        metadata={"source": "riscv_intro.pdf", "page": 1},
        embedding=embedder.embed(["RISC-V is an open standard..."])[0]
    )
]

retriever.index_documents(documents)

# Search
results = retriever.retrieve("What is RISC-V?", k=5)
for result in results:
    print(f"Score: {result.score:.3f} - {result.document.content[:100]}")
```

### Configuration-Based Usage

**Unified Configuration** (`config.yaml`):
```yaml
retriever:
  type: "unified"
  config:
    dense_weight: 0.7
    embedding_dim: 384
    index_type: "IndexFlatIP"
    normalize_embeddings: true
    metric: "cosine"
    embedding_model: "sentence-transformers/multi-qa-MiniLM-L6-cos-v1"
    use_mps: true
    bm25_k1: 1.2
    bm25_b: 0.75
    rrf_k: 10
```

**Platform Orchestrator Usage**:
```python
from src.core.platform_orchestrator import PlatformOrchestrator

# Automatic unified retriever creation
orchestrator = PlatformOrchestrator("config.yaml")
orchestrator.process_document(Path("document.pdf"))
answer = orchestrator.process_query("Your question here")
```

---

## API Reference

### Constructor

```python
UnifiedRetriever(
    embedder: Embedder,
    dense_weight: float = 0.7,
    embedding_dim: int = 384,
    index_type: str = "IndexFlatIP",
    normalize_embeddings: bool = True,
    metric: str = "cosine",
    embedding_model: str = "sentence-transformers/multi-qa-MiniLM-L6-cos-v1",
    use_mps: bool = True,
    bm25_k1: float = 1.2,
    bm25_b: float = 0.75,
    rrf_k: int = 10
)
```

**Parameters**:
- `embedder`: Embedder instance for query encoding
- `dense_weight`: Weight for semantic similarity in fusion (0.0-1.0)
- `embedding_dim`: Dimension of embeddings (e.g., 384, 768)
- `index_type`: FAISS index type ("IndexFlatIP", "IndexFlatL2", "IndexIVFFlat")
- `normalize_embeddings`: Whether to normalize embeddings for cosine similarity
- `metric`: Distance metric ("cosine" or "euclidean")
- `embedding_model`: Sentence transformer model name for hybrid search
- `use_mps`: Use Apple Silicon MPS acceleration
- `bm25_k1`: BM25 term frequency saturation parameter
- `bm25_b`: BM25 document length normalization parameter
- `rrf_k`: Reciprocal Rank Fusion constant

### Core Methods

#### `index_documents(documents: List[Document]) -> None`

Index documents for both dense and sparse retrieval.

```python
documents = [
    Document(
        content="Your document content here",
        metadata={"source": "file.pdf", "page": 1},
        embedding=[0.1, 0.2, 0.3, 0.4]  # Pre-computed embedding
    )
]

retriever.index_documents(documents)
```

**Requirements**:
- All documents must have embeddings
- Embedding dimensions must match `embedding_dim`
- Documents list cannot be empty

#### `retrieve(query: str, k: int = 5) -> List[RetrievalResult]`

Retrieve relevant documents using hybrid search.

```python
results = retriever.retrieve("What is RISC-V?", k=10)

for result in results:
    print(f"Score: {result.score:.3f}")
    print(f"Method: {result.retrieval_method}")
    print(f"Content: {result.document.content}")
    print(f"Metadata: {result.document.metadata}")
```

**Returns**: List of `RetrievalResult` objects sorted by relevance score (descending)

#### `get_retrieval_stats() -> Dict[str, Any]`

Get comprehensive retrieval statistics.

```python
stats = retriever.get_retrieval_stats()
print(f"Indexed documents: {stats['indexed_documents']}")
print(f"Dense weight: {stats['dense_weight']}")
print(f"FAISS vectors: {stats['faiss_total_vectors']}")
print(f"Architecture: {stats['component_type']}")
```

#### `get_configuration() -> Dict[str, Any]`

Get current configuration parameters.

```python
config = retriever.get_configuration()
print(f"Embedding dimension: {config['embedding_dim']}")
print(f"Index type: {config['index_type']}")
print(f"BM25 parameters: k1={config['bm25_k1']}, b={config['bm25_b']}")
```

#### `clear_index() -> None`

Clear all indexed documents and reset the retriever.

```python
retriever.clear_index()
assert retriever.get_document_count() == 0
```

### Utility Methods

#### `get_document_count() -> int`
Returns the number of indexed documents.

#### `supports_batch_queries() -> bool`
Returns `False` (batch queries not currently supported).

#### `get_faiss_info() -> Dict[str, Any]`
Returns FAISS-specific index information.

---

## Configuration Options

### FAISS Index Types

**IndexFlatIP** (Default):
```python
retriever = UnifiedRetriever(
    embedder=embedder,
    index_type="IndexFlatIP",
    normalize_embeddings=True,  # Required for cosine similarity
    metric="cosine"
)
```
- Best for: Cosine similarity with normalized embeddings
- Performance: Exact search, slower on large datasets
- Memory: Higher memory usage

**IndexFlatL2**:
```python
retriever = UnifiedRetriever(
    embedder=embedder,
    index_type="IndexFlatL2",
    normalize_embeddings=False,
    metric="euclidean"
)
```
- Best for: Euclidean distance metrics
- Performance: Exact search, slower on large datasets
- Memory: Higher memory usage

**IndexIVFFlat**:
```python
retriever = UnifiedRetriever(
    embedder=embedder,
    index_type="IndexIVFFlat",
    normalize_embeddings=True
)
```
- Best for: Large datasets (>10k documents)
- Performance: Approximate search, faster on large datasets
- Memory: Lower memory usage
- Note: Requires training phase during indexing

### Hybrid Search Tuning

**Dense-Heavy Configuration** (Better for semantic similarity):
```python
retriever = UnifiedRetriever(
    embedder=embedder,
    dense_weight=0.8,  # 80% dense, 20% sparse
    rrf_k=5           # Lower RRF constant
)
```

**Sparse-Heavy Configuration** (Better for keyword matching):
```python
retriever = UnifiedRetriever(
    embedder=embedder,
    dense_weight=0.4,  # 40% dense, 60% sparse
    bm25_k1=1.5,      # Higher term frequency saturation
    bm25_b=0.9,       # Higher length normalization
    rrf_k=20          # Higher RRF constant
)
```

**Balanced Configuration** (Recommended default):
```python
retriever = UnifiedRetriever(
    embedder=embedder,
    dense_weight=0.7,  # 70% dense, 30% sparse
    bm25_k1=1.2,      # Standard BM25 parameters
    bm25_b=0.75,
    rrf_k=10          # Moderate RRF fusion
)
```

---

## Performance Guidelines

### Optimization Tips

1. **Embedding Dimension**: Use smaller dimensions (384) for faster indexing, larger (768) for better quality
2. **Index Type Selection**: 
   - Use `IndexFlatIP` for <1k documents
   - Use `IndexIVFFlat` for >10k documents
3. **Dense Weight Tuning**: Start with 0.7, adjust based on query patterns
4. **Apple Silicon**: Enable `use_mps=True` for 2-3x embedding speedup
5. **Memory Management**: Call `clear_index()` when switching document sets

### Performance Benchmarks

| Documents | Indexing Time | Memory Usage | Query Time |
|-----------|---------------|--------------|------------|
| 50 | 2.5s | <100MB | <0.1s |
| 500 | 15s | <300MB | <0.2s |
| 5000 | 120s | <800MB | <0.5s |

**System**: M4-Pro Apple Silicon, 32GB RAM

### Troubleshooting Performance

**Slow Indexing**:
- Check `use_mps=True` for Apple Silicon
- Reduce `embedding_dim` if quality allows
- Use `IndexIVFFlat` for large datasets

**High Memory Usage**:
- Use `IndexIVFFlat` instead of `IndexFlatIP`
- Reduce batch size in document processing
- Call `clear_index()` between document sets

**Poor Search Quality**:
- Increase `dense_weight` for semantic queries
- Decrease `dense_weight` for keyword queries
- Tune `rrf_k` parameter (lower = more emphasis on top results)

---

## Error Handling

### Common Errors

**Missing Embeddings**:
```python
# ❌ Error: Document without embedding
doc = Document("content", metadata={"source": "file.pdf"})
retriever.index_documents([doc])  # ValueError: Document 0 is missing embedding

# ✅ Correct: Document with embedding
doc.embedding = embedder.embed([doc.content])[0]
retriever.index_documents([doc])
```

**Wrong Embedding Dimension**:
```python
# ❌ Error: Wrong dimension
retriever = UnifiedRetriever(embedder=embedder, embedding_dim=384)
doc = Document("content", embedding=[0.1, 0.2])  # Only 2 dimensions
retriever.index_documents([doc])  # ValueError: embedding dimension 2 doesn't match expected 384

# ✅ Correct: Matching dimension
doc.embedding = [0.1] * 384  # 384 dimensions
retriever.index_documents([doc])
```

**Query Before Indexing**:
```python
# ❌ Error: Query without documents
retriever = UnifiedRetriever(embedder=embedder)
retriever.retrieve("query")  # RuntimeError: No documents have been indexed

# ✅ Correct: Index first, then query
retriever.index_documents(documents)
results = retriever.retrieve("query")
```

### Error Recovery

```python
try:
    retriever.index_documents(documents)
except ValueError as e:
    if "missing embedding" in str(e):
        # Generate missing embeddings
        for doc in documents:
            if doc.embedding is None:
                doc.embedding = embedder.embed([doc.content])[0]
        retriever.index_documents(documents)
    else:
        raise

try:
    results = retriever.retrieve(query, k=10)
except RuntimeError as e:
    if "No documents" in str(e):
        print("Warning: No documents indexed yet")
        results = []
    else:
        raise
```

---

## Migration from Legacy Components

### From FAISSVectorStore + HybridRetriever

**Old Architecture**:
```python
# Legacy: Separate components
vector_store = FAISSVectorStore(embedding_dim=384)
hybrid_retriever = HybridRetriever(
    vector_store=vector_store,
    embedder=embedder,
    dense_weight=0.7
)

# Index documents
vector_store.add(documents)
hybrid_retriever.index_documents(documents)

# Search
results = hybrid_retriever.retrieve(query, k=5)
```

**New Architecture**:
```python
# Unified: Single component
unified_retriever = UnifiedRetriever(
    embedder=embedder,
    dense_weight=0.7,
    embedding_dim=384
)

# Index documents (single call)
unified_retriever.index_documents(documents)

# Search (same API)
results = unified_retriever.retrieve(query, k=5)
```

### Configuration Migration

**Legacy Config**:
```yaml
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
```

**Unified Config**:
```yaml
retriever:
  type: "unified"
  config:
    embedding_dim: 384      # From vector_store
    index_type: "IndexFlatIP"  # From vector_store  
    dense_weight: 0.7       # From retriever
    rrf_k: 10              # From retriever
```

### Benefits of Migration

1. **Simplified Codebase**: Remove dual component management
2. **Better Performance**: Eliminate abstraction layer overhead
3. **Easier Configuration**: Single component configuration
4. **Reduced Memory**: No duplicate document storage
5. **Enhanced Monitoring**: Unified stats and health reporting

---

## Advanced Usage

### Custom Embedder Integration

```python
class CustomEmbedder(Embedder):
    def embed(self, texts: List[str]) -> List[List[float]]:
        # Your custom embedding logic
        return embeddings
    
    def embedding_dim(self) -> int:
        return 512

# Use with unified retriever
retriever = UnifiedRetriever(
    embedder=CustomEmbedder(),
    embedding_dim=512,  # Match custom embedder
    dense_weight=0.8
)
```

### Batch Document Processing

```python
def process_documents_in_batches(retriever, all_documents, batch_size=100):
    """Process large document collections in batches."""
    
    for i in range(0, len(all_documents), batch_size):
        batch = all_documents[i:i + batch_size]
        
        try:
            retriever.index_documents(batch)
            print(f"Processed batch {i//batch_size + 1}: {len(batch)} documents")
        except Exception as e:
            print(f"Error in batch {i//batch_size + 1}: {e}")
            continue
    
    print(f"Total documents indexed: {retriever.get_document_count()}")
```

### Health Monitoring Integration

```python
def monitor_retriever_health(retriever):
    """Monitor retriever health and performance."""
    
    stats = retriever.get_retrieval_stats()
    faiss_info = retriever.get_faiss_info()
    
    health_report = {
        "status": "healthy" if stats["indexed_documents"] > 0 else "warning",
        "documents": stats["indexed_documents"],
        "faiss_vectors": faiss_info["total_vectors"],
        "memory_mb": faiss_info.get("index_size_bytes", 0) / (1024*1024),
        "architecture": stats["component_type"]
    }
    
    return health_report
```

### Query Analysis and Debugging

```python
def analyze_query_results(retriever, query, k=10):
    """Analyze query results for debugging."""
    
    results = retriever.retrieve(query, k=k)
    
    analysis = {
        "query": query,
        "total_results": len(results),
        "score_range": (results[0].score, results[-1].score) if results else (0, 0),
        "retrieval_method": results[0].retrieval_method if results else "none",
        "top_sources": [r.document.metadata.get("source", "unknown") for r in results[:3]]
    }
    
    return analysis
```

---

## Best Practices

### 1. Configuration Management

- Use environment-specific configs for different deployments
- Validate embedding dimensions match your embedder
- Test different dense_weight values with your data
- Monitor performance metrics in production

### 2. Document Preparation

- Ensure all documents have embeddings before indexing
- Use consistent metadata schemas across documents
- Implement proper error handling for malformed documents
- Consider document chunking for large texts

### 3. Performance Optimization

- Use Apple Silicon MPS acceleration when available
- Choose appropriate FAISS index type for your dataset size
- Implement batch processing for large document collections
- Monitor memory usage and implement cleanup strategies

### 4. Production Deployment

- Implement comprehensive health monitoring
- Use structured logging for debugging
- Set up performance alerts for indexing time
- Regular testing with representative queries

### 5. Quality Assurance

- Validate search results quality with test queries
- Monitor retrieval metrics and user feedback
- Implement A/B testing for configuration changes
- Regular performance benchmarking

---

## Support and Troubleshooting

### Common Issues

1. **Import Errors**: Ensure all dependencies are installed (`faiss-cpu`, `transformers`, `torch`)
2. **Memory Issues**: Use smaller batch sizes or IndexIVFFlat for large datasets
3. **Poor Results**: Tune dense_weight and RRF parameters for your use case
4. **Slow Performance**: Enable MPS acceleration and use appropriate index type

### Debug Tools

```python
# Enable debug logging
import logging
logging.getLogger('src.components.retrievers.unified_retriever').setLevel(logging.DEBUG)

# Check system health
health = retriever.get_retrieval_stats()
print(f"System health: {health}")

# Validate configuration
config = retriever.get_configuration()
print(f"Current config: {config}")
```

### Performance Profiling

```python
import time

def profile_retriever_performance(retriever, queries, k=5):
    """Profile retriever query performance."""
    
    times = []
    for query in queries:
        start = time.time()
        results = retriever.retrieve(query, k=k)
        end = time.time()
        times.append(end - start)
    
    avg_time = sum(times) / len(times)
    print(f"Average query time: {avg_time:.3f}s")
    print(f"Queries per second: {1/avg_time:.1f}")
    
    return times
```

For additional support, check:
- Test suite: `tests/unit/test_unified_retriever.py`
- Integration examples: `tests/unit/test_platform_orchestrator_phase2.py`
- Performance benchmarks: `docs/phase2-detailed-design.md`