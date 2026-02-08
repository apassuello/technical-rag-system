# Vector Index Quick Start Guide

## Prerequisites

Ensure dependencies are installed:

```bash
pip install -r requirements.txt
```

## Building Indices

### Step 1: Check Current Status

```bash
python scripts/check_indices_status.py
```

Expected output if indices don't exist:
```
================================================================================
VECTOR INDEX STATUS CHECK
================================================================================
Checking: /home/user/technical-rag-system/project-1-technical-rag/data/indices

❌ Indices directory does not exist

To create indices, run:
    python scripts/build_indices.py
================================================================================
```

### Step 2: Build Indices

```bash
python scripts/build_indices.py
```

This will:
- Discover 22 PDF documents in `data/test/` (39MB total)
- Process each PDF and extract text chunks
- Generate embeddings using `multi-qa-MiniLM-L6-cos-v1` (384 dimensions)
- Build FAISS index with cosine similarity (IndexFlatIP)
- Save to `data/indices/`

Expected output:
```
================================================================================
VECTOR INDEX BUILD
================================================================================
Discovering documents in data/test...
Found 22 documents

Processing 22 documents...
[1/22] riscv-v-spec-1.0.pdf
  → Generated 45 chunks
  → Generated 45 embeddings (dim=384)
[2/22] EECS-2011-62.pdf
  → Generated 32 chunks
  → Generated 32 embeddings (dim=384)
...

Building FAISS index (150+ documents)...
Saving index to disk...
  → FAISS index: data/indices/faiss_index.bin
  → Documents: data/indices/documents.pkl

================================================================================
BUILD COMPLETE
================================================================================
Documents processed: 22
Total chunks: 150+
Embedding dimension: 384
Index location: data/indices
Index size: ~2-5 MB
================================================================================
```

### Step 3: Verify Indices

```bash
python scripts/verify_indices.py
```

Expected output:
```
================================================================================
VECTOR INDEX VERIFICATION
================================================================================
Checking index files...
  metadata: ✓ (0.01 MB)
  documents: ✓ (5.23 MB)
  faiss_index: ✓ (2.15 MB)

Verifying metadata...
  created_at: ✓
  updated_at: ✓
  document_count: ✓ (150)
  embedding_dim: ✓ (384)

Testing search functionality...
  Query 1: 2.34ms, top match: idx=0, dist=0.9876
  Query 2: 1.89ms, top match: idx=12, dist=0.9543
  ...

================================================================================
VERIFICATION SUMMARY
================================================================================
Files exist: ✓
Metadata valid: ✓
Documents valid: ✓
Index valid: ✓
Search works: ✓

Overall Status: PASSED
================================================================================
```

## Common Commands

```bash
# Check status (lightweight, no dependencies)
python scripts/check_indices_status.py

# Build indices from scratch
python scripts/build_indices.py

# Rebuild (overwrite existing)
python scripts/build_indices.py --rebuild

# Incremental update (only new/modified files)
python scripts/build_indices.py --incremental

# Verify indices
python scripts/verify_indices.py

# Verify with benchmarks
python scripts/verify_indices.py --benchmark

# Generate verification report
python scripts/verify_indices.py --report
```

## Integration with RAG System

Once indices are built, the retriever can load them:

```python
from pathlib import Path
import pickle

# Load documents from index
indices_dir = Path("data/indices")
with open(indices_dir / "documents.pkl", 'rb') as f:
    documents = pickle.load(f)

# Initialize retriever
retriever.initialize_index(documents)
```

## Troubleshooting

### Dependencies Missing

**Error**: `ModuleNotFoundError: No module named 'pydantic'`

**Solution**:
```bash
pip install -r requirements.txt
```

### Build Fails with Memory Error

**Solution**: Reduce batch size in `config/default.yaml`:
```yaml
embedder:
  config:
    batch_processor:
      config:
        initial_batch_size: 32  # Reduce from 64
```

### Verification Fails

**Solution**: Rebuild indices:
```bash
python scripts/build_indices.py --rebuild
```

## File Locations

```
data/
├── indices/                          # Index storage (created by build script)
│   ├── faiss_index.bin              # FAISS vector index
│   ├── documents.pkl                # Document objects with embeddings
│   ├── index_metadata.json          # Index statistics and metadata
│   └── verification_report.json    # Verification results (if --report used)
└── test/                            # Source documents
    ├── *.pdf                        # PDF documents (22 files, 39MB)
    ├── *.txt                        # Text documents
    └── *.md                         # Markdown documents
```

## Next Steps

1. **Build indices**: `python scripts/build_indices.py`
2. **Verify**: `python scripts/verify_indices.py`
3. **Integrate**: Load documents in retriever
4. **Test**: Run RAG system end-to-end

For detailed documentation, see:
- **Full Guide**: `docs/INDEX_MANAGEMENT_GUIDE.md`
- **Configuration**: `config/indices.yaml`
- **Scripts**: `scripts/build_indices.py`, `scripts/verify_indices.py`
