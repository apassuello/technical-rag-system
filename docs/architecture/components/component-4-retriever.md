# Component 4: Retriever

**Component ID**: C4  
**Version**: 1.0  
**References**: [MASTER-ARCHITECTURE.md](./MASTER-ARCHITECTURE.md)  
**Related Components**: [C3-Embedder](./COMPONENT-3-EMBEDDER.md), [C5-Answer Generator](./COMPONENT-5-ANSWER-GENERATOR.md), [C6-Query Processor](./COMPONENT-6-QUERY-PROCESSOR.md)

---

## 1. Component Overview

### 1.1 Purpose & Responsibility

The Retriever implements **hybrid search capabilities** to find relevant documents:
- Dense retrieval using vector similarity
- Sparse retrieval using keyword matching
- Fusion strategies combining multiple signals
- Reranking for improved relevance

### 1.2 Position in System

**Central Search Component**: Used by Query Processor
- **Input**: Query embeddings and text
- **Output**: Ranked relevant documents

### 1.3 Key Design Decisions

1. **Unified Retriever**: Combines vector store and search logic
2. **Hybrid by Default**: Dense + sparse for best quality
3. **Pluggable Components**: Different indices and strategies

---

## 2. Requirements

### 2.1 Functional Requirements

**Core Capabilities**:
- FR1: Store and index document embeddings
- FR2: Perform vector similarity search
- FR3: Execute keyword-based search
- FR4: Fuse multiple retrieval signals
- FR5: Rerank results for relevance

**Interface Contracts**: See [Retriever Interface](./rag-interface-reference.md#2-main-component-interfaces)

**Behavioral Specifications**:
- Must return results sorted by relevance
- Must handle queries with no matches
- Must support incremental indexing

### 2.2 Quality Requirements

**Performance**:
- Retrieval latency: <10ms average
- Indexing throughput: >10K docs/second
- Reranking: <50ms for 100 documents

**Reliability**:
- 100% retrieval success rate
- No data loss during indexing
- Consistent ranking results

**Scalability**:
- Support 10M+ documents
- Handle 1000+ QPS
- Efficient memory usage

---

## 3. Architecture Design

### 3.1 Internal Structure

```
Unified Retriever
├── Vector Index (sub-component)
├── Sparse Retriever (sub-component)
├── Fusion Strategy (sub-component)
├── Reranker (sub-component)
└── Metadata Store
```

### 3.2 Sub-Components

**Vector Index**:
- **Purpose**: Store and search embeddings
- **Implementation**: Mixed (Direct for FAISS, Adapter for cloud)
- **Decision**: Cloud services need API adaptation
- **Variants**: FAISS (direct), Pinecone (adapter), Weaviate (adapter)

**Sparse Retriever**:
- **Purpose**: Keyword-based search
- **Implementation**: Mixed approach
- **Decision**: Elasticsearch needs adapter, BM25 is direct
- **Variants**: BM25 (direct), Elasticsearch (adapter)

**Fusion Strategy**:
- **Purpose**: Combine retrieval signals
- **Implementation**: Direct implementation
- **Decision**: Pure algorithms, no external deps
- **Variants**: RRF, Weighted, ML-based

**Reranker**:
- **Purpose**: Improve result relevance
- **Implementation**: Direct implementation
- **Decision**: Model inference, minimal adaptation
- **Variants**: Cross-encoder, ColBERT, LLM-based

### 3.3 Adapter vs Direct

**Uses Adapters For**:
- Cloud vector databases (Pinecone, Weaviate)
- Elasticsearch integration
- External ranking services

**Direct Implementation For**:
- Local indices (FAISS, Annoy)
- Fusion algorithms
- Reranking models

### 3.4 State Management

**Persistent State**:
- Vector index (memory-mapped or remote)
- Document metadata
- Sparse index structures

**Runtime State**:
- Query cache for repeated searches
- Reranker model in memory

---

## 4. Interfaces

### 4.1 Provided Interfaces

See [Retriever Sub-component Interfaces](./rag-interface-reference.md#33-retrieval-sub-components)

**Main Interface**:
- `retrieve(query, k) -> List[RetrievalResult]`
- `index_documents(documents) -> None`
- `delete_documents(doc_ids) -> int`
- `get_stats() -> Dict`

### 4.2 Required Interfaces

- Embeddings from Embedder component
- Query analysis from Query Processor

### 4.3 Events Published

- Documents indexed/deleted
- Search completed with statistics
- Index optimization performed

---

## 5. Design Rationale

### Architectural Decisions

**AD1: Unified Retriever Pattern**
- **Decision**: Combine vector store and retriever
- **Rationale**: Reduces complexity, better performance
- **Trade-off**: Less flexibility for swapping stores

**AD2: Hybrid Search Default**
- **Decision**: Always use dense + sparse
- **Rationale**: Best retrieval quality
- **Trade-off**: Higher computational cost

**AD3: Reranking Stage**
- **Decision**: Separate reranking step
- **Rationale**: Improve precision without recall loss
- **Trade-off**: Additional latency

### Alternatives Considered

1. **Separate Vector/Keyword Systems**: Too complex to coordinate
2. **Dense-only Retrieval**: Misses exact matches
3. **No Reranking**: Lower quality results

---

## 6. Implementation Guidelines

### Current Implementation Notes

- FAISS with IndexFlatIP for exact search
- BM25 with custom tokenization
- RRF fusion with k=60
- Cross-encoder reranking

### Best Practices

1. **Index in batches** for efficiency
2. **Tune fusion weights** per domain
3. **Monitor index size** and optimize
4. **Use appropriate index type** for scale

### Common Pitfalls

- Don't forget to normalize vectors
- Don't ignore sparse retrieval value
- Don't rerank too many documents
- Don't mix embeddings from different models

### Performance Considerations

- Choose approximate indices for scale
- Implement result caching
- Parallelize dense/sparse retrieval
- Optimize reranker batch size

---

## 7. Configuration

### Configuration Schema

```yaml
retriever:
  vector_index:
    type: "faiss"  # or "hnsw", "pinecone"
    config:
      index_type: "IndexFlatIP"
      dimension: 384
      metric: "cosine"
      
  sparse_retriever:
    type: "bm25"  # or "elasticsearch"
    config:
      k1: 1.2
      b: 0.75
      tokenizer: "technical"
      
  fusion:
    type: "rrf"  # or "weighted", "learned"
    config:
      k: 60
      weights:
        dense: 0.7
        sparse: 0.3
        
  reranker:
    type: "cross_encoder"  # or "colbert", "none"
    config:
      model: "cross-encoder/ms-marco-MiniLM-L-6-v2"
      batch_size: 32
      top_k: 10
```

---

## 8. Operations

### Health Checks

- Vector index loaded and queryable
- Sparse index initialized
- Reranker model available
- Test retrieval on sample query

### Metrics Exposed

- `retriever_documents_indexed_total`
- `retriever_searches_total`
- `retriever_latency_seconds{phase="dense|sparse|fusion|rerank"}`
- `retriever_index_size_bytes`
- `retriever_cache_hit_rate`

### Logging Strategy

- DEBUG: Retrieval scores and fusion weights
- INFO: Search summary and statistics
- WARN: Slow queries, low scores
- ERROR: Index corruption, search failures

### Troubleshooting Guide

| Symptom | Likely Cause | Resolution |
|---------|--------------|------------|
| Poor results | Wrong fusion weights | Tune weights for domain |
| Slow search | Large index | Use approximate search |
| Missing results | Indexing issues | Verify index integrity |
| High memory | Index in RAM | Use memory-mapped index |

---

## 9. Future Enhancements

### Planned Features

1. **Learned Fusion**: ML model for weight optimization
2. **Query Expansion**: Automatic query enhancement
3. **Personalization**: User-specific ranking
4. **Multi-field Search**: Metadata filtering

### Extension Points

- Custom index implementations
- Alternative fusion strategies
- Domain-specific rerankers
- Query preprocessors

### Known Limitations

- English-only sparse retrieval
- Fixed embedding dimensions
- No real-time index updates
- Limited metadata filtering