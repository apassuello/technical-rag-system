# Critical RAG System Fixes

**Status**: BLOCKING ISSUES - Must fix before LLM integration
**Priority**: P0 (System unusable for Q&A without these fixes)

## 🚨 Critical Issues Confirmed

### Issue 1: RRF Score Normalization Broken
**Problem**: Hybrid scores 37x lower than semantic (0.016 vs 0.59)
**Impact**: LLM has no confidence in retrieved context
**Root Cause**: RRF formula produces tiny scores, not normalized to [0,1]

### Issue 2: Chunking Strategy Fails 
**Problem**: 80% fragment rate, 501 char average (too small)
**Impact**: Context is broken sentences, incomplete explanations
**Root Cause**: Fixed 500-char chunks break semantic boundaries

### Issue 3: Poor Source Diversity
**Problem**: 60% of queries use only 1/5 available sources  
**Impact**: Missing relevant information from other documents
**Root Cause**: Ranking doesn't encourage source diversity

### Issue 4: Context Quality Insufficient for Q&A
**Problem**: Retrieved snippets are fragments, not explanations
**Impact**: LLM cannot generate meaningful answers
**Root Cause**: Combination of chunking + scoring issues

## 🔧 Required Fixes

### Fix 1: RRF Score Normalization (2-3 hours)
**File**: `shared_utils/retrieval/hybrid_search.py`

```python
def reciprocal_rank_fusion(dense_results, sparse_results, dense_weight=0.7, k=60):
    # Current (BROKEN):
    # score = 1.0 / (rank + k)  # Results in ~0.016
    
    # Fix (NORMALIZE):
    combined_scores = {}
    
    # Normalize dense scores to [0,1] if needed
    if dense_results:
        max_dense = max(score for _, score in dense_results)
        dense_norm = [(idx, score/max_dense) for idx, score in dense_results]
    
    # Calculate RRF with proper weighting
    for rank, (idx, score) in enumerate(dense_norm):
        rrf_score = dense_weight * score + (1-dense_weight) * (1.0/(rank + k))
        combined_scores[idx] = rrf_score
    
    # Ensure final scores are in [0,1] range
    max_final = max(combined_scores.values())
    return [(idx, score/max_final) for idx, score in combined_scores.items()]
```

### Fix 2: Improved Chunking Strategy (2-3 hours)
**File**: `shared_utils/document_processing/chunker.py`

```python
def chunk_technical_text(text: str, chunk_size: int = 1200, overlap: int = 200):
    # Current: Fixed 500 chars (BROKEN)
    # Fix: Larger chunks with sentence boundaries
    
    sentences = split_into_sentences(text)
    chunks = []
    current_chunk = ""
    
    for sentence in sentences:
        if len(current_chunk + sentence) <= chunk_size:
            current_chunk += sentence + " "
        else:
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = sentence + " "
    
    # Add overlap between chunks
    return add_overlap_between_chunks(chunks, overlap)
```

### Fix 3: Source Diversity Enhancement (1-2 hours)
**File**: `shared_utils/retrieval/hybrid_search.py`

```python
def enhance_source_diversity(results, max_per_source=2):
    """Ensure diverse sources in top results"""
    source_counts = {}
    diverse_results = []
    
    for result in results:
        source = result['source']
        if source_counts.get(source, 0) < max_per_source:
            diverse_results.append(result)
            source_counts[source] = source_counts.get(source, 0) + 1
        
        if len(diverse_results) >= 5:  # top_k
            break
    
    return diverse_results
```

### Fix 4: Better Embedding Model (30 minutes)
**File**: `shared_utils/embeddings/generator.py`

```python
# Current: all-MiniLM-L6-v2 (general domain)
# Fix: Use better model for technical Q&A
MODEL_NAME = "sentence-transformers/all-mpnet-base-v2"  # Higher quality
# Or: "sentence-transformers/multi-qa-mpnet-base-dot-v1"  # Optimized for Q&A
```

## 🎯 Implementation Priority

### Phase 1: Core Fixes (4-5 hours)
1. **Fix RRF normalization** - Restore meaningful confidence scores
2. **Improve chunking** - Larger, sentence-aware chunks  
3. **Update embedding model** - Better semantic understanding

### Phase 2: Quality Enhancements (2-3 hours)  
4. **Add source diversity** - Ensure comprehensive coverage
5. **Context validation** - Filter low-quality chunks
6. **Re-run evaluation** - Verify fixes work

## 🧪 Validation Plan

### Test Queries for Validation:
```python
test_queries = [
    "How do I configure CPU registers in RISC-V?",
    "What are FDA software validation requirements?", 
    "Explain RISC-V instruction format encoding",
    "What is the RTOS interrupt handling process?"
]
```

### Success Criteria:
- ✅ Hybrid scores in [0.3, 1.0] range (meaningful confidence)
- ✅ Average chunk size >800 characters  
- ✅ Fragment rate <20%
- ✅ Source diversity: ≥3 sources for multi-document queries
- ✅ Retrieved context can answer questions completely

## 🚫 What NOT to Do

❌ **Don't add LLM integration yet** - Fix retrieval first
❌ **Don't optimize query enhancement** - Core retrieval broken  
❌ **Don't tune hyperparameters** - Fundamental bugs need fixing
❌ **Don't add more features** - Fix existing functionality

## ⏰ Timeline

- **Day 1**: Fix RRF normalization + chunking strategy
- **Day 2**: Implement source diversity + better embeddings  
- **Day 3**: Validate fixes + re-run evaluation
- **Day 4**: Ready for LLM integration

## 🎯 Expected Impact

**Before Fixes**:
```
Query: "How do I configure RISC-V registers?"
Context: "register is a function of the source register(s). For most"
LLM: "I don't have enough context to answer your question."
```

**After Fixes**:
```  
Query: "How do I configure RISC-V registers?"
Context: "RISC-V defines 32 integer registers (x0-x31) where x0 is hardwired 
to zero. Register configuration follows the calling convention: x1 serves as 
return address, x2 as stack pointer, x5-x7 as temporaries..."
LLM: "To configure RISC-V registers, you need to understand the standard 
calling convention..."
```

---

**CRITICAL**: These fixes are MANDATORY before any LLM integration. 
The current system would produce poor Q&A responses that frustrate users.