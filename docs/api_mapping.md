# API Mapping Reference: BasicRAG → RAGPipeline

This document provides a comprehensive mapping of all BasicRAG APIs to their RAGPipeline equivalents, ensuring smooth migration with full compatibility.

## Quick Reference Table

| BasicRAG | RAGPipeline | Compatibility | Notes |
|----------|-------------|---------------|-------|
| `BasicRAG()` | `RAGPipeline(config_path)` | ✅ Compatible | Requires config file |
| `index_document(path)` | `index_document(path)` | ✅ Identical | Same interface |
| `query(text)` | `query(text, k=5)` | ✅ Compatible | Optional k parameter |
| `hybrid_query(text, top_k=5)` | `query(text, k=5)` | ✅ Compatible | Hybrid is default |
| `enhanced_hybrid_query(text)` | `query(text, k=5)` | ⚠️ Deprecated | Features integrated |
| `get_stats()` | `get_pipeline_info()` | ✅ Enhanced | More detailed info |
| `clear_index()` | `clear_index()` | ✅ Identical | Same interface |

## Detailed API Mapping

### 1. Initialization

#### BasicRAG
```python
from src.basic_rag import BasicRAG

# Simple initialization
rag = BasicRAG()
```

#### RAGPipeline
```python
from src.core.pipeline import RAGPipeline
from pathlib import Path

# Configuration-based initialization
rag = RAGPipeline("config/default.yaml")
# or
rag = RAGPipeline(Path("config/default.yaml"))

# Using different configurations
dev_rag = RAGPipeline("config/dev.yaml")
prod_rag = RAGPipeline("config/production.yaml")
```

**Migration Pattern:**
```python
# Before
rag = BasicRAG()

# After  
rag = RAGPipeline("config/default.yaml")
```

### 2. Document Indexing

#### BasicRAG
```python
# Index a single document
chunks_count = rag.index_document("document.pdf")
print(f"Indexed {chunks_count} chunks")

# Multiple documents (if supported)
for doc_path in document_paths:
    rag.index_document(doc_path)
```

#### RAGPipeline
```python
# Index a single document (identical interface)
chunks_count = rag.index_document("document.pdf")
print(f"Indexed {chunks_count} chunks")

# Index with Path object
from pathlib import Path
chunks_count = rag.index_document(Path("document.pdf"))

# Multiple documents
for doc_path in document_paths:
    rag.index_document(doc_path)
```

**Migration Pattern:**
```python
# No changes needed - identical interface
chunks_count = rag.index_document("document.pdf")
```

### 3. Querying

#### BasicRAG Query Methods
```python
# Basic query
results = rag.query("What is RISC-V?")
# Returns: List[Dict] with chunks

# Hybrid query (recommended)
results = rag.hybrid_query("What is RISC-V?", top_k=5)
# Returns: List[Dict] with chunks and scores

# Enhanced hybrid query (deprecated)
results = rag.enhanced_hybrid_query("What is RISC-V?")
# Returns: List[Dict] with enhanced features
```

#### RAGPipeline Query Methods
```python
# Unified query interface (hybrid by default)
answer = rag.query("What is RISC-V?", k=5)
# Returns: Answer object with structured data

# Access answer components
print(answer.text)           # Generated answer
print(answer.sources)        # Source documents
print(answer.confidence)     # Confidence score
print(answer.metadata)       # Additional metadata

# Access source documents
for doc in answer.sources:
    print(doc.content)       # Document content
    print(doc.metadata)      # Document metadata
```

**Migration Patterns:**

#### Pattern 1: Basic Query
```python
# Before
results = rag.query("What is RISC-V?")
for result in results:
    print(result['text'])

# After
answer = rag.query("What is RISC-V?")
for doc in answer.sources:
    print(doc.content)
# Or use the generated answer
print(answer.text)
```

#### Pattern 2: Hybrid Query
```python
# Before
results = rag.hybrid_query("What is RISC-V?", top_k=5)
for result in results:
    print(f"Score: {result['score']}, Text: {result['text']}")

# After
answer = rag.query("What is RISC-V?", k=5)
print(f"Answer: {answer.text}")
print(f"Confidence: {answer.confidence}")
for i, doc in enumerate(answer.sources):
    print(f"Source {i+1}: {doc.content[:100]}...")
```

#### Pattern 3: Enhanced Hybrid Query
```python
# Before (deprecated)
results = rag.enhanced_hybrid_query("What is RISC-V?")

# After (enhanced features are integrated by default)
answer = rag.query("What is RISC-V?", k=5)
```

### 4. Return Value Structures

#### BasicRAG Return Format
```python
# Query results format
results = [
    {
        'text': 'chunk content...',
        'score': 0.85,
        'metadata': {
            'source': 'document.pdf',
            'page': 1,
            'chunk_id': 0
        }
    },
    # ... more chunks
]
```

#### RAGPipeline Return Format
```python
# Answer object structure
answer = Answer(
    text="Generated answer text...",
    sources=[
        Document(
            content="chunk content...",
            metadata={
                'source': 'document.pdf',
                'page': 1,
                'chunk_id': 0
            }
        ),
        # ... more documents
    ],
    confidence=0.85,
    metadata={
        'model_used': 'deepset/roberta-base-squad2',
        'generation_time': 1.23,
        'retrieval_method': 'hybrid'
    }
)
```

**Conversion Patterns:**

#### Extract Chunks Like BasicRAG
```python
# To get BasicRAG-like chunk list from RAGPipeline
answer = rag.query("query")

# Convert to BasicRAG format
basic_rag_format = []
for doc in answer.sources:
    basic_rag_format.append({
        'text': doc.content,
        'score': 1.0,  # RAGPipeline uses confidence instead
        'metadata': doc.metadata
    })
```

#### Use Enhanced Answer Format
```python
# Take advantage of RAGPipeline's enhanced format
answer = rag.query("query")

# Generated answer (not available in BasicRAG)
print(f"Answer: {answer.text}")

# Confidence score
print(f"Confidence: {answer.confidence}")

# Rich metadata
print(f"Model: {answer.metadata.get('model_used')}")
print(f"Generation time: {answer.metadata.get('generation_time')}s")

# Source diversity
sources = set(doc.metadata.get('source') for doc in answer.sources)
print(f"Sources: {sources}")
```

### 5. System Information and Statistics

#### BasicRAG
```python
# Get basic statistics
stats = rag.get_stats()
# Returns basic index information

# Limited component access
# No direct access to internal components
```

#### RAGPipeline
```python
# Get comprehensive pipeline information
info = rag.get_pipeline_info()
print(info)  # Detailed configuration and component info

# Access individual components
processor = rag.get_component("processor")
embedder = rag.get_component("embedder")
vector_store = rag.get_component("vector_store")
retriever = rag.get_component("retriever")
generator = rag.get_component("generator")

# Component-specific information
if vector_store and hasattr(vector_store, 'get_index_info'):
    index_info = vector_store.get_index_info()
    print(f"Index size: {index_info.get('total_vectors', 0)} vectors")
```

**Migration Pattern:**
```python
# Before
stats = rag.get_stats()

# After (enhanced information)
info = rag.get_pipeline_info()
# Plus individual component access for detailed stats
```

### 6. Index Management

#### BasicRAG
```python
# Clear index
rag.clear_index()

# Save/load index (if supported)
rag.save_index("index.faiss")
rag.load_index("index.faiss")
```

#### RAGPipeline
```python
# Clear index (identical interface)
rag.clear_index()

# Index persistence through vector store component
vector_store = rag.get_component("vector_store")
if hasattr(vector_store, 'save'):
    vector_store.save("index.faiss")
if hasattr(vector_store, 'load'):
    vector_store.load("index.faiss")
```

**Migration Pattern:**
```python
# Clear index - no changes needed
rag.clear_index()

# For save/load operations
# Before
rag.save_index("index.faiss")

# After
vector_store = rag.get_component("vector_store")
if hasattr(vector_store, 'save'):
    vector_store.save("index.faiss")
```

## Advanced Migration Patterns

### 1. Configuration-Based Customization

#### BasicRAG (Limited Customization)
```python
# BasicRAG had limited customization options
rag = BasicRAG()
# Configuration was hardcoded
```

#### RAGPipeline (Full Customization)
```python
# Create custom configurations for different use cases
research_rag = RAGPipeline("config/research.yaml")   # Large chunks, detailed analysis
production_rag = RAGPipeline("config/production.yaml") # Optimized for speed
testing_rag = RAGPipeline("config/test.yaml")        # Fast, minimal resources

# Runtime configuration selection
import os
env = os.getenv("RAG_ENV", "default")
rag = RAGPipeline(f"config/{env}.yaml")
```

### 2. Error Handling Migration

#### BasicRAG Error Handling
```python
try:
    results = rag.hybrid_query("query")
    if not results:
        print("No results found")
except Exception as e:
    print(f"Query failed: {e}")
```

#### RAGPipeline Error Handling
```python
try:
    answer = rag.query("query")
    if answer.confidence < 0.5:
        print("Low confidence answer")
    if not answer.sources:
        print("No sources found")
except Exception as e:
    print(f"Query failed: {e}")
    # Enhanced error information available
    print(f"Error details: {getattr(e, 'details', 'N/A')}")
```

### 3. Batch Processing Migration

#### BasicRAG Batch Processing
```python
# Process multiple queries
results = []
for query in queries:
    result = rag.hybrid_query(query)
    results.append(result)
```

#### RAGPipeline Batch Processing
```python
# Process multiple queries (same pattern, enhanced results)
answers = []
for query in queries:
    answer = rag.query(query)
    answers.append(answer)

# Enhanced batch processing with monitoring
import time
answers = []
for i, query in enumerate(queries):
    start_time = time.time()
    answer = rag.query(query)
    processing_time = time.time() - start_time
    
    answers.append({
        'query': query,
        'answer': answer,
        'processing_time': processing_time,
        'confidence': answer.confidence
    })
    
    print(f"Query {i+1}/{len(queries)}: {processing_time:.2f}s, confidence: {answer.confidence:.3f}")
```

### 4. Component Customization

#### BasicRAG (No Component Access)
```python
# BasicRAG didn't allow component customization
rag = BasicRAG()
# All components were internal and fixed
```

#### RAGPipeline (Full Component Access)
```python
# Access and customize individual components
rag = RAGPipeline("config/default.yaml")

# Customize retriever behavior
retriever = rag.get_component("retriever")
if hasattr(retriever, 'set_weights'):
    retriever.set_weights(dense_weight=0.8, sparse_weight=0.2)

# Customize answer generator
generator = rag.get_component("generator")
if hasattr(generator, 'set_temperature'):
    generator.set_temperature(0.2)  # More focused answers

# Monitor embedder performance
embedder = rag.get_component("embedder")
if hasattr(embedder, 'get_embedding_stats'):
    stats = embedder.get_embedding_stats()
    print(f"Embedding speed: {stats.get('tokens_per_second', 'N/A')}")
```

## Migration Testing Patterns

### 1. Compatibility Testing

```python
def test_migration_compatibility():
    """Test that migration preserves functionality."""
    # Initialize both systems
    old_rag = BasicRAG()
    new_rag = RAGPipeline("config/default.yaml")
    
    # Index same document
    test_doc = "test_document.pdf"
    old_chunks = old_rag.index_document(test_doc)
    new_chunks = new_rag.index_document(test_doc)
    
    # Test query compatibility
    query = "What is the main topic?"
    old_results = old_rag.hybrid_query(query, top_k=5)
    new_answer = new_rag.query(query, k=5)
    
    # Verify compatibility
    assert len(new_answer.sources) == len(old_results)
    assert new_answer.confidence > 0.0
    assert len(new_answer.text) > 0
```

### 2. Performance Testing

```python
def test_migration_performance():
    """Test that migration doesn't degrade performance."""
    import time
    
    # Test old system
    old_rag = BasicRAG()
    old_rag.index_document("test_document.pdf")
    
    start_time = time.time()
    old_results = old_rag.hybrid_query("test query")
    old_time = time.time() - start_time
    
    # Test new system
    new_rag = RAGPipeline("config/default.yaml")
    new_rag.index_document("test_document.pdf")
    
    start_time = time.time()
    new_answer = new_rag.query("test query")
    new_time = time.time() - start_time
    
    # Performance should be similar or better
    assert new_time <= old_time * 1.5  # Allow 50% variance
    print(f"Old: {old_time:.3f}s, New: {new_time:.3f}s")
```

## Common Migration Gotchas

### 1. Return Type Changes

❌ **Wrong**: Expecting list of chunks
```python
# This will fail with RAGPipeline
answer = rag.query("query")
for chunk in answer:  # ❌ answer is not iterable
    print(chunk['text'])
```

✅ **Correct**: Use Answer object
```python
answer = rag.query("query")
for doc in answer.sources:  # ✅ iterate over sources
    print(doc.content)
```

### 2. Configuration Requirements

❌ **Wrong**: No configuration file
```python
# This will fail with RAGPipeline
rag = RAGPipeline()  # ❌ config_path required
```

✅ **Correct**: Provide configuration
```python
rag = RAGPipeline("config/default.yaml")  # ✅ config required
```

### 3. Method Parameter Changes

❌ **Wrong**: Old parameter names
```python
# This might not work as expected
results = rag.hybrid_query(query, k=5)  # ❌ use top_k for BasicRAG
```

✅ **Correct**: Unified interface
```python
answer = rag.query(query, k=5)  # ✅ works for RAGPipeline
```

### 4. Import Statement Updates

❌ **Wrong**: Old imports
```python
from src.basic_rag import BasicRAG  # ❌ old import
```

✅ **Correct**: New imports
```python
from src.core.pipeline import RAGPipeline  # ✅ new import
```

## Migration Checklist by Feature

### Core Functionality
- [ ] ✅ Document indexing works
- [ ] ✅ Query processing works  
- [ ] ✅ Results are equivalent
- [ ] ✅ Performance is acceptable

### API Compatibility
- [ ] ✅ All method calls updated
- [ ] ✅ Return value handling updated
- [ ] ✅ Error handling adapted
- [ ] ✅ Import statements updated

### Configuration
- [ ] ✅ Configuration files created
- [ ] ✅ Environment-specific configs
- [ ] ✅ Configuration validation
- [ ] ✅ Environment variables set

### Testing
- [ ] ✅ Unit tests updated
- [ ] ✅ Integration tests passing
- [ ] ✅ Performance tests passing
- [ ] ✅ Comparison validation complete

### Production Readiness
- [ ] ✅ Monitoring configured
- [ ] ✅ Logging updated
- [ ] ✅ Error alerting setup
- [ ] ✅ Rollback procedure tested

## Conclusion

This API mapping provides complete coverage for migrating from BasicRAG to RAGPipeline. The new system maintains full compatibility while providing enhanced functionality, better performance, and improved maintainability.

Key migration principles:
1. **Backward Compatibility**: Core functionality is preserved
2. **Enhanced Features**: New capabilities are additive, not breaking
3. **Configuration-Driven**: Flexibility through external configuration
4. **Component Access**: Full visibility into system components
5. **Better Monitoring**: Enhanced observability and debugging

Use this reference alongside the [Migration Guide](migration_guide.md) for a complete migration experience.