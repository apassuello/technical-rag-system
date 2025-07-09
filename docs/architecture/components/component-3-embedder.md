# Component 3: Embedder

**Component ID**: C3  
**Version**: 1.0  
**References**: [MASTER-ARCHITECTURE.md](./MASTER-ARCHITECTURE.md)  
**Related Components**: [C2-Document Processor](./COMPONENT-2-DOCUMENT-PROCESSOR.md), [C4-Retriever](./COMPONENT-4-RETRIEVER.md)

---

## 1. Component Overview

### 1.1 Purpose & Responsibility

The Embedder transforms **text into vector representations** for semantic search:
- Generate high-quality embeddings from text chunks
- Optimize batch processing for efficiency
- Cache embeddings to avoid recomputation
- Support multiple embedding models

### 1.2 Position in System

**Pipeline Position**: Between Document Processor and Retriever
- **Input**: Text chunks from Document Processor
- **Output**: Vector embeddings to Retriever

### 1.3 Key Design Decisions

1. **Model Agnostic**: Support both local and API-based models
2. **Batch Optimization**: Dynamic batching for GPU efficiency
3. **Multi-level Caching**: Memory → Redis → Disk

---

## 2. Requirements

### 2.1 Functional Requirements

**Core Capabilities**:
- FR1: Generate embeddings from text
- FR2: Batch process multiple texts efficiently
- FR3: Cache and retrieve computed embeddings
- FR4: Support different embedding models
- FR5: Handle various text lengths appropriately

**Interface Contracts**: See [Embedder Interface](./rag-interface-reference.md#2-main-component-interfaces)

**Behavioral Specifications**:
- Must maintain consistent dimensions across all embeddings
- Must handle empty/invalid text gracefully
- Must optimize for available hardware (GPU/MPS/CPU)

### 2.2 Quality Requirements

**Performance**:
- Throughput: >2,500 chars/second
- Batch efficiency: 80x+ speedup with batching
- Cache hit rate: >90% for repeated content

**Reliability**:
- Deterministic embeddings for same input
- Graceful fallback if GPU unavailable
- Handle model loading failures

**Scalability**:
- Process batches up to 128 texts
- Support models from 384 to 1536 dimensions
- Horizontal scaling via distributed cache

---

## 3. Architecture Design

### 3.1 Internal Structure

```
Embedder
├── Embedding Model (sub-component)
├── Batch Processor (sub-component)
├── Embedding Cache (sub-component)
└── Hardware Optimizer
```

### 3.2 Sub-Components

**Embedding Model**:
- **Purpose**: Core embedding generation
- **Implementation**: Mixed (Direct for local, Adapter for APIs)
- **Decision**: External APIs need format conversion
- **Variants**: SentenceTransformer (direct), OpenAI (adapter)

**Batch Processor**:
- **Purpose**: Optimize embedding generation throughput
- **Implementation**: Direct implementation
- **Decision**: Pure optimization logic, no external deps
- **Variants**: Dynamic, Streaming, Fixed-size

**Embedding Cache**:
- **Purpose**: Avoid recomputing embeddings
- **Implementation**: Adapter for external stores
- **Decision**: Different storage backends need adaptation
- **Variants**: In-memory (direct), Redis (adapter), Disk (adapter)

### 3.3 Adapter vs Direct

**Uses Adapters For**:
- External embedding APIs (OpenAI, Cohere)
- Distributed cache backends (Redis)
- Persistent storage (Disk cache)

**Direct Implementation For**:
- Local embedding models (Sentence Transformers)
- Batch processing logic
- In-memory caching

### 3.4 State Management

**Stateless Embedding**:
- No state between embedding calls
- Model loaded once at initialization
- Cache is external state

---

## 4. Interfaces

### 4.1 Provided Interfaces

See [Embedder Sub-component Interfaces](./rag-interface-reference.md#32-embedding-sub-components)

**Main Interface**:
- `embed(texts) -> np.ndarray`
- `embed_query(query) -> List[float]`
- `get_dimension() -> int`
- `batch_embed(texts, batch_size) -> np.ndarray`

### 4.2 Required Interfaces

- Document chunks from Document Processor
- Hardware detection for optimization
- Cache storage backends

### 4.3 Events Published

- Embedding batch completed
- Cache hit/miss statistics
- Model loading status

---

## 5. Design Rationale

### Architectural Decisions

**AD1: Separate Model from Processing**
- **Decision**: Model as sub-component
- **Rationale**: Switch models without changing logic
- **Trade-off**: Extra abstraction layer

**AD2: Multi-level Caching**
- **Decision**: Memory → Redis → Disk hierarchy
- **Rationale**: Balance speed vs capacity
- **Trade-off**: Complex cache management

**AD3: Hardware Optimization**
- **Decision**: Automatic GPU/MPS detection
- **Rationale**: Best performance on available hardware
- **Trade-off**: Platform-specific code paths

### Alternatives Considered

1. **Single Embedding Model**: Too limiting for production
2. **No Caching**: Wastes computation on repeated text
3. **Fixed Batch Sizes**: Suboptimal for varying loads

---

## 6. Implementation Guidelines

### Current Implementation Notes

- sentence-transformers/all-MiniLM-L6-v2 as default
- MPS acceleration on Apple Silicon
- 87.9x speedup with batch processing

### Best Practices

1. **Always batch** when processing multiple texts
2. **Warm up cache** with common queries
3. **Monitor GPU memory** to prevent OOM
4. **Validate dimensions** match expected values

### Common Pitfalls

- Don't embed texts longer than model's max length
- Don't assume GPU always available
- Don't cache without considering memory limits
- Don't mix embeddings from different models

### Performance Considerations

- Optimal batch size depends on GPU memory
- Cache eviction strategy affects hit rate
- Model loading time impacts cold starts
- Normalize embeddings for cosine similarity

---

## 7. Configuration

### Configuration Schema

```yaml
embedder:
  model:
    type: "sentence_transformer"  # or "openai", "custom"
    config:
      model_name: "all-MiniLM-L6-v2"
      device: "mps"  # or "cuda", "cpu"
      normalize: true
      
  batch_processor:
    type: "dynamic"  # or "fixed", "streaming"
    config:
      initial_batch_size: 32
      max_batch_size: 128
      optimize_for_memory: true
      
  cache:
    type: "redis"  # or "memory", "disk"
    config:
      ttl_seconds: 3600
      max_entries: 100000
      eviction_policy: "lru"
```

---

## 8. Operations

### Health Checks

- Model loaded successfully
- GPU/MPS available and functional
- Cache backend connected
- Test embedding generation

### Metrics Exposed

- `embedder_texts_processed_total`
- `embedder_batch_size_histogram`
- `embedder_cache_hit_rate`
- `embedder_processing_time_seconds`
- `embedder_model_memory_bytes`

### Logging Strategy

- DEBUG: Batch composition and timing
- INFO: Model loading and cache statistics
- WARN: Fallback to CPU, cache misses
- ERROR: Model failures, OOM errors

### Troubleshooting Guide

| Symptom | Likely Cause | Resolution |
|---------|--------------|------------|
| Slow embedding | CPU fallback | Check GPU availability |
| OOM errors | Large batches | Reduce batch size |
| Inconsistent results | Different models | Verify model consistency |
| Low cache hits | Poor key strategy | Improve text normalization |

---

## 9. Future Enhancements

### Planned Features

1. **Multi-modal Embeddings**: Image + text embeddings
2. **Fine-tuned Models**: Domain-specific embeddings
3. **Quantized Models**: Reduced memory usage
4. **Cross-lingual**: Multilingual embedding support

### Extension Points

- Custom embedding models
- Alternative caching strategies
- Specialized batch processors
- Hardware accelerators (TPU)

### Known Limitations

- English-optimized models
- Fixed embedding dimensions
- No incremental embedding updates
- Limited to text input only