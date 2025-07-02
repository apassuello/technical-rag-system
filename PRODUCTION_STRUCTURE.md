# Production RAG System Structure

## 🎯 Final Production-Ready Structure

After cleanup, your repository will have this clean, focused structure:

```
rag-portfolio/
├── project-1-technical-rag/
│   ├── src/
│   │   ├── __init__.py
│   │   └── basic_rag.py                    # 🔥 MAIN RAG SYSTEM
│   ├── tests/
│   │   ├── test_basic_rag.py               # Core RAG tests
│   │   ├── test_chunker.py                 # Chunking tests
│   │   ├── test_embeddings.py              # Embedding tests
│   │   ├── test_hybrid_retrieval.py        # Hybrid search tests
│   │   ├── test_integration.py             # End-to-end tests
│   │   ├── test_pdf_parser.py              # PDF parsing tests
│   │   └── test_query_enhancer.py          # Query enhancement tests
│   ├── data/test/
│   │   └── riscv-base-instructions.pdf     # Test document
│   ├── production_demo.py                  # 🚀 SINGLE COMPREHENSIVE DEMO
│   └── README.md
├── shared_utils/
│   ├── __init__.py
│   ├── document_processing/
│   │   ├── __init__.py
│   │   ├── pdf_parser.py                   # PDF text extraction
│   │   ├── chunker.py                      # Basic chunking
│   │   ├── hybrid_parser.py                # 🔥 PRODUCTION PARSER
│   │   ├── toc_guided_parser.py            # TOC parsing (used by hybrid)
│   │   └── pdfplumber_parser.py            # PDFPlumber extraction (used by hybrid)
│   ├── embeddings/
│   │   ├── __init__.py
│   │   └── generator.py                    # Embedding generation
│   ├── retrieval/
│   │   ├── __init__.py
│   │   ├── hybrid_search.py                # 🔥 HYBRID RETRIEVAL
│   │   └── vocabulary_index.py             # Technical vocabulary
│   └── query_processing/
│       ├── __init__.py
│       └── query_enhancer.py               # Query enhancement
└── CLAUDE.md                               # Project documentation
```

## 🔥 Key Production Components

### 1. **Core RAG System** - `src/basic_rag.py`
- Combines all components into production-ready system
- Hybrid search with dense + sparse retrieval
- Structure-preserving parsing with trash filtering
- Query enhancement with vocabulary awareness

### 2. **Production Parser** - `shared_utils/document_processing/hybrid_parser.py`
- TOC-guided navigation for document structure
- PDFPlumber precision extraction
- Aggressive trash filtering while preserving technical content
- Optimal 800-2000 character chunks with 0% fragments

### 3. **Hybrid Retrieval** - `shared_utils/retrieval/hybrid_search.py`
- Dense semantic search (FAISS)
- Sparse keyword search (BM25)
- Reciprocal Rank Fusion with configurable k parameter
- Optimal 70% dense, 30% sparse weighting

## 🧪 Testing Strategy

### Essential Test Coverage:
1. **Unit Tests**: Each component individually tested
2. **Integration Tests**: End-to-end pipeline validation
3. **Performance Tests**: Speed and quality benchmarks
4. **Real-world Validation**: RISC-V technical documentation

### Test Commands:
```bash
# Run all tests
python -m pytest tests/ -v

# Run specific test categories
python -m pytest tests/test_basic_rag.py -v
python -m pytest tests/test_integration.py -v

# Run production demo
python production_demo.py
```

## 📊 Cleanup Impact

### Before Cleanup:
- **55 Python files** (many experimental/debug)
- **29 debug/analysis scripts**
- **8 experimental parsers**
- **10 demo files**
- **Complex, confusing structure**

### After Cleanup:
- **18 Python files** (production-focused)
- **11 core implementation files**
- **7 essential test files**
- **1 comprehensive demonstration**
- **Clean, maintainable structure**

### Benefits:
- **67% file reduction** while maintaining all functionality
- **Clear separation** between production code and tests
- **Single source of truth** for each component
- **Easy to understand** and maintain
- **Production deployment ready**

## 🚀 Usage After Cleanup

### Quick Start:
```python
from src.basic_rag import BasicRAG

# Initialize production RAG system
rag = BasicRAG()

# Index document with hybrid parser
rag.index_document("path/to/document.pdf")

# Query with hybrid retrieval (RECOMMENDED)
result = rag.hybrid_query("Your question here")

# Enhanced query with vocabulary awareness (OPTIONAL)
result = rag.enhanced_hybrid_query("Your question here")
```

### Best Practices:
1. **Use `hybrid_query()`** for production (best performance + quality)
2. **Use `hybrid_parser.py`** for document processing (production parser)
3. **Run `production_demo.py`** to validate system performance
4. **Check `tests/`** for comprehensive testing examples

This structure gives you a **production-ready RAG system** that's clean, efficient, and easy to maintain!