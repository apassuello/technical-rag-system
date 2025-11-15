# Vector Index Management Guide

## Overview

This guide explains how to build, verify, and manage FAISS vector indices for the RAG system.

## Quick Start

```bash
# Install dependencies (if not already installed)
pip install -r requirements.txt

# Build indices from sample documents
python scripts/build_indices.py

# Verify indices
python scripts/verify_indices.py

# Rebuild indices (overwrite existing)
python scripts/build_indices.py --rebuild

# Incremental update (only new/modified documents)
python scripts/build_indices.py --incremental
```

## Index Building

### Basic Usage

The `build_indices.py` script processes documents and creates searchable FAISS indices.

```bash
# Build with default settings
python scripts/build_indices.py

# Build from specific directory
python scripts/build_indices.py --data-dir /path/to/documents

# Save indices to specific location
python scripts/build_indices.py --indices-dir /path/to/indices

# Use custom configuration
python scripts/build_indices.py --config config/custom.yaml

# Enable verbose logging
python scripts/build_indices.py --verbose
```

### Build Modes

#### Full Build (Default)
Processes all documents in the data directory and creates complete indices.

```bash
python scripts/build_indices.py
```

#### Rebuild Mode
Overwrites existing indices, useful after configuration changes.

```bash
python scripts/build_indices.py --rebuild
```

#### Incremental Mode
Only processes new or modified documents, preserving existing index data.

```bash
python scripts/build_indices.py --incremental
```

### What Gets Created

The build process creates three files in `data/indices/`:

1. **faiss_index.bin** - FAISS binary index file
   - Contains vector representations of document chunks
   - Optimized for fast similarity search
   - Size: ~1-10MB per 1000 documents

2. **documents.pkl** - Pickled document objects
   - Original text chunks with metadata
   - Embeddings attached to each document
   - Required for retrieving actual content

3. **index_metadata.json** - Index metadata and statistics
   ```json
   {
     "created_at": "2025-11-15T10:00:00",
     "updated_at": "2025-11-15T10:00:00",
     "document_count": 150,
     "embedding_model": "sentence-transformers/multi-qa-MiniLM-L6-cos-v1",
     "embedding_dim": 384,
     "file_hashes": {...},
     "index_type": "faiss"
   }
   ```

### Build Process

The build process follows these steps:

1. **Document Discovery** - Finds all PDF, TXT, and MD files
2. **Document Processing** - Extracts text and chunks documents
3. **Embedding Generation** - Creates vector embeddings for each chunk
4. **Index Building** - Constructs FAISS index from embeddings
5. **Persistence** - Saves index, documents, and metadata

### Performance

Typical performance on M4-Pro Apple Silicon:

- **Processing**: ~1-2 documents/second
- **Embedding**: ~50-100 chunks/second (batch size 64)
- **Index Building**: <1 second for 1000 vectors
- **Total Time**: ~2-5 minutes for 20-30 documents (depending on size)

## Index Verification

### Basic Usage

The `verify_indices.py` script validates index integrity and functionality.

```bash
# Verify default indices
python scripts/verify_indices.py

# Verify specific indices
python scripts/verify_indices.py --indices-dir /path/to/indices

# Run performance benchmarks
python scripts/verify_indices.py --benchmark

# Generate detailed report
python scripts/verify_indices.py --report
```

### Verification Checks

The verifier performs the following checks:

1. **File Existence**
   - Confirms all required files exist
   - Reports file sizes

2. **Metadata Validation**
   - Checks required fields present
   - Validates data types and ranges
   - Confirms document count > 0

3. **Document Integrity**
   - Loads pickled documents
   - Verifies document structure
   - Checks embeddings present

4. **Index Structure**
   - Loads FAISS index
   - Verifies dimension matches metadata
   - Confirms index is trained

5. **Search Functionality**
   - Performs test searches
   - Measures search latency
   - Validates results returned

### Verification Status

The verifier reports one of three statuses:

- **PASSED** - All checks successful ✓
- **PARTIAL** - Some checks failed ⚠️
- **FAILED** - Critical checks failed ✗

### Performance Benchmarks

With `--benchmark` flag, the verifier runs extended tests:

- 10 test queries (vs 5 in standard mode)
- Latency percentiles (P50, P95, P99)
- Search performance statistics

Example output:
```
Search performance:
  - avg: 2.34ms
  - min: 1.12ms
  - max: 4.56ms
```

### Verification Report

With `--report` flag, generates `verification_report.json`:

```json
{
  "timestamp": "2025-11-15T10:30:00",
  "indices_dir": "data/indices",
  "checks": {
    "file_metadata_exists": true,
    "file_metadata_size_mb": 0.01,
    "file_documents_exists": true,
    "file_documents_size_mb": 5.23,
    "file_faiss_index_exists": true,
    "file_faiss_index_size_mb": 2.15,
    "metadata_document_count": true,
    "metadata_document_count_value": 150,
    "documents_count": 150,
    "index_ntotal": 150,
    "index_dimension": 384,
    "search_avg_time_ms": 2.34,
    "search_works": true
  },
  "overall_status": "PASSED"
}
```

## Index Configuration

### Configuration File

See `config/indices.yaml` for complete configuration options:

```yaml
indices:
  storage_dir: "data/indices"
  types:
    - name: "main"
      type: "faiss"

documents:
  sources:
    - path: "data/test"
      recursive: true

embeddings:
  model: "sentence-transformers/multi-qa-MiniLM-L6-cos-v1"
  dimension: 384
  batch_size: 64

build:
  index_type: "IndexFlatIP"
  metric: "cosine"
  incremental:
    enabled: true
    hash_algorithm: "sha256"
```

### Index Types

Supported FAISS index types:

- **IndexFlatIP** (default) - Exact search with inner product (cosine similarity)
- **IndexFlatL2** - Exact search with L2 distance (Euclidean)
- **IndexIVFFlat** - Approximate search with inverted file index (faster, less accurate)
- **IndexHNSWFlat** - Approximate search with HNSW graph (very fast, good accuracy)

### Embedding Models

Recommended models:

- `sentence-transformers/multi-qa-MiniLM-L6-cos-v1` (384d) - Balanced, good for Q&A
- `sentence-transformers/all-MiniLM-L6-v2` (384d) - General purpose
- `sentence-transformers/all-mpnet-base-v2` (768d) - Higher quality, slower

## Integration with Retriever

### Loading Indices in Code

The retriever automatically loads indices if they exist:

```python
from src.core.component_factory import ComponentFactory
from src.config_loader import load_config

# Load configuration
config = load_config("config/default.yaml")

# Create retriever
factory = ComponentFactory()
retriever = factory.create_retriever(
    "modular_unified",
    config=config.retriever.config,
    embedder=embedder
)

# Load documents from index
from pathlib import Path
import pickle

indices_dir = Path("data/indices")
with open(indices_dir / "documents.pkl", 'rb') as f:
    documents = pickle.load(f)

# Initialize retriever with documents
retriever.initialize_index(documents)
```

### Automatic Index Loading

For seamless integration, modify the retriever to auto-load:

```python
def initialize_index(self, documents: Optional[List[Document]] = None):
    """Initialize with documents or load from saved index."""
    if documents is None:
        # Try to load from saved index
        indices_dir = Path("data/indices")
        if (indices_dir / "documents.pkl").exists():
            with open(indices_dir / "documents.pkl", 'rb') as f:
                documents = pickle.load(f)
            logger.info(f"Loaded {len(documents)} documents from index")

    # Proceed with normal initialization
    ...
```

## Maintenance

### Index Lifecycle

1. **Initial Build** - Create indices from scratch
   ```bash
   python scripts/build_indices.py
   ```

2. **Periodic Updates** - Add new documents incrementally
   ```bash
   python scripts/build_indices.py --incremental
   ```

3. **Configuration Changes** - Rebuild with new settings
   ```bash
   python scripts/build_indices.py --rebuild --config config/new.yaml
   ```

4. **Verification** - Regular health checks
   ```bash
   python scripts/verify_indices.py --report
   ```

### Backup Strategy

Recommended backup approach:

```bash
# Create backup
cp -r data/indices data/indices.backup.$(date +%Y%m%d)

# Keep last 5 backups
ls -t data/indices.backup.* | tail -n +6 | xargs rm -rf
```

### Index Optimization

For large document collections (>10,000 documents):

1. Use approximate indices (IndexIVFFlat, IndexHNSWFlat)
2. Increase batch sizes for embedding
3. Enable parallel processing (future enhancement)
4. Consider index sharding for very large collections

### Troubleshooting

#### Index Build Fails

**Problem**: Build script fails with memory error

**Solution**:
- Reduce batch size in config
- Process documents in smaller batches
- Increase system memory
- Use simpler index type (IndexFlatIP)

#### Search Returns No Results

**Problem**: Queries return empty results

**Solution**:
- Verify embeddings are normalized (`normalize_embeddings: true`)
- Check distance metric matches (cosine vs euclidean)
- Ensure query uses same embedding model
- Verify index was properly trained (for IVF indices)

#### Incremental Update Not Working

**Problem**: Modified documents not detected

**Solution**:
- Check file hashes in metadata
- Force rebuild with `--rebuild`
- Verify file permissions
- Check metadata.json is writable

## Performance Tuning

### Batch Size Optimization

For embedding generation:

- **Small datasets (<1000 docs)**: batch_size=32
- **Medium datasets (1000-10000 docs)**: batch_size=64
- **Large datasets (>10000 docs)**: batch_size=128-256

### Memory Management

Monitor memory usage:

```python
import psutil
process = psutil.Process()
memory_mb = process.memory_info().rss / 1024 / 1024
print(f"Memory usage: {memory_mb:.2f} MB")
```

Reduce memory footprint:
- Use smaller embedding models
- Process documents in batches
- Clear caches between batches
- Use memory-mapped FAISS indices

### Search Performance

Optimize search latency:

1. **Index Type**: Use approximate indices for large datasets
2. **Normalization**: Pre-normalize embeddings
3. **Batch Queries**: Search multiple queries at once
4. **Caching**: Cache frequent queries
5. **Quantization**: Use product quantization for large indices

## Advanced Usage

### Custom Document Processing

Override document processor:

```python
class CustomIndexBuilder(IndexBuilder):
    def process_document(self, file_path: Path) -> List[Document]:
        # Custom processing logic
        ...
```

### Multiple Index Types

Build separate indices for different document types:

```bash
# Index PDFs
python scripts/build_indices.py \
  --data-dir data/pdfs \
  --indices-dir data/indices/pdfs

# Index markdown
python scripts/build_indices.py \
  --data-dir data/markdown \
  --indices-dir data/indices/markdown
```

### Monitoring Integration

Add monitoring hooks:

```python
# In build_indices.py
from prometheus_client import Counter, Gauge

docs_processed = Counter('documents_processed_total', 'Documents processed')
index_size = Gauge('index_size_bytes', 'Index size in bytes')

# Update during build
docs_processed.inc()
index_size.set(self.index_path.stat().st_size)
```

## References

- [FAISS Documentation](https://github.com/facebookresearch/faiss)
- [Sentence Transformers](https://www.sbert.net/)
- [RAG System Architecture](/docs/architecture/)
- [Configuration Guide](/config/indices.yaml)

## Support

For issues or questions:
1. Check verification report: `python scripts/verify_indices.py --report`
2. Review logs in `logs/index_building.log`
3. Consult troubleshooting section above
4. Contact: arthur.passuello@example.com
