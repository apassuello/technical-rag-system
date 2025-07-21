# Retrieval Quality Test Plan

**Version**: 1.0  
**Date**: January 2025  
**Status**: Implementation Ready  
**Purpose**: Define comprehensive quality-focused tests for RAG retrieval components

---

## 📋 Executive Summary

This test plan addresses the critical gap in current testing: validating retrieval **quality** rather than implementation **mechanics**. Current tests verify that components execute without errors but fail to validate that they retrieve relevant documents with appropriate scores.

### Key Testing Principles

1. **Mathematical Correctness**: Algorithms produce correct scores according to formulas
2. **Semantic Validity**: Embeddings capture meaningful relationships
3. **Relevance Improvement**: Advanced features actually improve retrieval quality
4. **Score Interpretability**: Scores have consistent meaning across components
5. **Failure Mode Testing**: System handles edge cases appropriately

---

## 🎯 Test Categories

### 1. Scoring Algorithm Validation

#### 1.1 BM25 Scoring Tests

**Purpose**: Verify BM25 implements the correct mathematical formula and produces interpretable scores.

**Test Cases**:

```python
def test_bm25_formula_correctness():
    """Verify BM25 score calculation matches expected formula."""
    # Given: Document with known term frequencies
    doc = Document(content="RISC-V RISC-V processor architecture")
    query = "RISC-V"
    
    # Calculate expected score manually
    tf = 2  # "RISC-V" appears twice
    doc_length = 4  # 4 terms
    avg_doc_length = 10  # corpus average
    idf = 2.0  # inverse document frequency
    k1, b = 1.2, 0.75
    
    expected_score = idf * (tf * (k1 + 1)) / (tf + k1 * (1 - b + b * doc_length / avg_doc_length))
    actual_score = bm25.score(query, doc)
    
    assert abs(actual_score - expected_score) < 0.001

def test_bm25_relevance_filtering():
    """Verify BM25 filters irrelevant queries."""
    technical_doc = Document(content="RISC-V implements a 32-bit instruction set architecture")
    
    # Technical query should score high
    assert bm25.score("RISC-V architecture", technical_doc) > 0.7
    
    # Irrelevant query should score low
    assert bm25.score("French cooking recipes", technical_doc) < 0.3
    
    # Partially relevant should be moderate
    assert 0.3 < bm25.score("computer architecture", technical_doc) < 0.7

def test_bm25_term_saturation():
    """Verify diminishing returns for repeated terms."""
    doc = Document(content="RISC-V processor design")
    
    score_1x = bm25.score("RISC-V", doc)
    score_2x = bm25.score("RISC-V RISC-V", doc)
    score_3x = bm25.score("RISC-V RISC-V RISC-V", doc)
    
    # Scores should increase but with diminishing returns
    assert score_2x > score_1x
    assert score_3x > score_2x
    assert (score_2x - score_1x) > (score_3x - score_2x)

def test_bm25_document_length_normalization():
    """Verify document length normalization works correctly."""
    short_doc = Document(content="RISC-V architecture")
    long_doc = Document(content="RISC-V architecture is an open instruction set architecture based on established reduced instruction set computer principles")
    
    # Both have same term frequency ratio for "RISC-V"
    short_score = bm25.score("RISC-V", short_doc)
    long_score = bm25.score("RISC-V", long_doc)
    
    # Scores should be similar (within 20%)
    assert abs(short_score - long_score) / max(short_score, long_score) < 0.2
```

#### 1.2 Vector Similarity Tests

**Purpose**: Verify embeddings capture semantic relationships with appropriate similarity ranges.

**Test Cases**:

```python
def test_semantic_similarity_ranges():
    """Verify similarity scores fall in expected ranges."""
    embedder = create_embedder()
    
    # Highly related concepts
    emb1 = embedder.embed("RISC-V instruction set architecture")
    emb2 = embedder.embed("RISC V ISA specification")
    similarity_high = cosine_similarity(emb1, emb2)
    assert similarity_high > 0.8
    
    # Unrelated concepts
    emb3 = embedder.embed("French cuisine recipes")
    similarity_low = cosine_similarity(emb1, emb3)
    assert similarity_low < 0.3
    
    # Clear separation
    assert similarity_high - similarity_low > 0.5

def test_synonym_detection():
    """Verify synonyms have high similarity."""
    test_pairs = [
        ("CPU", "processor", 0.7),
        ("RAM", "memory", 0.7),
        ("ISA", "instruction set architecture", 0.8),
        ("pipeline", "pipelining", 0.7)
    ]
    
    for term1, term2, min_similarity in test_pairs:
        emb1 = embedder.embed(term1)
        emb2 = embedder.embed(term2)
        similarity = cosine_similarity(emb1, emb2)
        assert similarity > min_similarity, f"{term1} vs {term2}: {similarity}"

def test_concept_hierarchy():
    """Verify hierarchical relationships are captured."""
    # Parent concept
    computer = embedder.embed("computer architecture")
    
    # Child concepts
    cpu = embedder.embed("CPU design")
    memory = embedder.embed("memory hierarchy")
    io = embedder.embed("I/O systems")
    
    # Children should be moderately similar to parent
    assert 0.5 < cosine_similarity(computer, cpu) < 0.8
    assert 0.5 < cosine_similarity(computer, memory) < 0.8
    
    # Siblings should be somewhat similar
    assert 0.4 < cosine_similarity(cpu, memory) < 0.7
```

### 2. Fusion Algorithm Validation

**Purpose**: Verify fusion algorithms correctly combine scores from multiple sources.

**Test Cases**:

```python
def test_rrf_formula():
    """Verify RRF implements correct reciprocal rank fusion formula."""
    # Dense results: [(doc1, rank0), (doc2, rank1), (doc3, rank2)]
    # Sparse results: [(doc2, rank0), (doc1, rank1), (doc4, rank2)]
    
    k = 60
    dense_weight = 0.7
    sparse_weight = 0.3
    
    # Expected RRF scores
    doc1_score = dense_weight * (1/(k+1)) + sparse_weight * (1/(k+2))  # ranks 0,1
    doc2_score = dense_weight * (1/(k+2)) + sparse_weight * (1/(k+1))  # ranks 1,0
    doc3_score = dense_weight * (1/(k+3)) + sparse_weight * 0          # rank 2, not in sparse
    doc4_score = dense_weight * 0 + sparse_weight * (1/(k+3))          # not in dense, rank 2
    
    fused_results = rrf_fusion(dense_results, sparse_results, k=k, 
                               dense_weight=dense_weight, sparse_weight=sparse_weight)
    
    # Verify scores match formula
    assert abs(fused_results["doc1"] - doc1_score) < 0.0001
    assert abs(fused_results["doc2"] - doc2_score) < 0.0001
    
    # Verify ranking order
    assert fused_results["doc2"] > fused_results["doc1"]  # doc2 has better combined rank

def test_weight_impact():
    """Verify fusion weights actually affect results."""
    dense_results = [("doc1", 0.9), ("doc2", 0.8), ("doc3", 0.7)]
    sparse_results = [("doc3", 0.95), ("doc4", 0.85), ("doc5", 0.75)]
    
    # Dense-heavy fusion
    fusion_dense = weighted_fusion(dense_results, sparse_results, 
                                  dense_weight=0.9, sparse_weight=0.1)
    
    # Sparse-heavy fusion
    fusion_sparse = weighted_fusion(dense_results, sparse_results,
                                   dense_weight=0.1, sparse_weight=0.9)
    
    # Top results should differ based on weights
    assert fusion_dense[0][0] in ["doc1", "doc2"]  # Dense top docs
    assert fusion_sparse[0][0] in ["doc3", "doc4"]  # Sparse top docs

def test_score_normalization():
    """Verify fusion produces normalized scores."""
    results = fusion_strategy.fuse(dense_results, sparse_results)
    
    scores = [score for _, score in results]
    
    # All scores in valid range
    assert all(0 <= score <= 1 for score in scores)
    
    # Scores properly ordered
    assert scores == sorted(scores, reverse=True)
    
    # No score inflation
    assert max(scores) <= 1.0
```

### 3. Reranking Quality Validation

**Purpose**: Verify reranking improves relevance, not just shuffles results.

**Test Cases**:

```python
def test_neural_reranking_improvement():
    """Verify neural reranking moves relevant documents up."""
    query = "RISC-V pipeline hazard detection"
    
    # Initial results (fusion output)
    initial_results = [
        Document(id="generic_pipeline.pdf", content="Generic pipeline design..."),
        Document(id="riscv_hazards.pdf", content="RISC-V pipeline hazard detection..."),
        Document(id="arm_pipeline.pdf", content="ARM pipeline architecture...")
    ]
    
    reranked = neural_reranker.rerank(query, initial_results)
    
    # Most relevant document should move to top
    assert reranked[0].id == "riscv_hazards.pdf"
    
    # Verify score indicates high relevance
    assert reranked[0].score > 0.9

def test_cross_encoder_scoring():
    """Verify cross-encoder produces calibrated scores."""
    cross_encoder = create_neural_reranker()
    
    # High relevance pair
    score_high = cross_encoder.score(
        "RISC-V vector instructions",
        "RISC-V V extension provides vector processing capabilities..."
    )
    assert score_high > 0.8
    
    # Low relevance pair
    score_low = cross_encoder.score(
        "RISC-V vector instructions",
        "Python programming tutorial for beginners..."
    )
    assert score_low < 0.2
    
    # Moderate relevance
    score_moderate = cross_encoder.score(
        "RISC-V vector instructions",
        "SIMD processing in modern processors..."
    )
    assert 0.4 < score_moderate < 0.7

def test_reranking_stability():
    """Verify reranking maintains relative order of similar documents."""
    query = "memory hierarchy"
    
    similar_docs = [
        Document(content="Cache memory hierarchy levels..."),
        Document(content="Memory hierarchy and cache design..."),
        Document(content="Understanding memory hierarchies...")
    ]
    
    # Run reranking multiple times
    results = []
    for _ in range(5):
        reranked = neural_reranker.rerank(query, similar_docs.copy())
        results.append([doc.id for doc in reranked])
    
    # Results should be consistent
    assert all(r == results[0] for r in results)
```

### 4. End-to-End Retrieval Quality

**Purpose**: Validate complete pipeline produces high-quality results.

**Test Cases**:

```python
def test_precision_at_k():
    """Measure precision@k for various queries."""
    test_queries = [
        {
            "query": "RISC-V vector extension",
            "relevant_docs": ["riscv_v_spec.pdf", "riscv_vector_programming.pdf"],
            "k": 5,
            "min_precision": 0.4  # At least 2/5 relevant
        },
        {
            "query": "branch prediction algorithms",
            "relevant_docs": ["branch_prediction.pdf", "cpu_optimization.pdf"],
            "k": 10,
            "min_precision": 0.3  # At least 3/10 relevant
        }
    ]
    
    for test_case in test_queries:
        results = rag_system.retrieve(test_case["query"], k=test_case["k"])
        retrieved_ids = [r.document.id for r in results]
        
        relevant_retrieved = len(set(retrieved_ids) & set(test_case["relevant_docs"]))
        precision = relevant_retrieved / test_case["k"]
        
        assert precision >= test_case["min_precision"]
        
        # Top result should always be relevant
        assert results[0].document.id in test_case["relevant_docs"]

def test_irrelevant_query_handling():
    """Verify system handles off-topic queries appropriately."""
    irrelevant_queries = [
        "French cooking recipes",
        "Tourist attractions in Paris",
        "How to train a dog"
    ]
    
    for query in irrelevant_queries:
        results = rag_system.retrieve(query, k=5)
        
        # Either return empty or all low scores
        if results:
            assert all(r.score < 0.3 for r in results)
            # Should indicate low confidence
            assert results[0].metadata.get("confidence", 0) < 0.5

def test_score_distribution():
    """Verify score distributions are meaningful."""
    results = rag_system.retrieve("RISC-V instruction encoding", k=10)
    
    scores = [r.score for r in results]
    
    # Scores should decrease
    assert scores == sorted(scores, reverse=True)
    
    # Should have meaningful gaps
    if len(scores) >= 5:
        top_scores = scores[:3]
        bottom_scores = scores[-3:]
        
        # Clear separation between top and bottom
        assert min(top_scores) > max(bottom_scores) + 0.1
```

### 5. Comparative Quality Tests

**Purpose**: Validate Epic 2 improvements over baseline.

**Test Cases**:

```python
def test_epic2_score_improvement():
    """Verify Epic 2 provides significant score improvements."""
    test_queries = [
        "RISC-V pipeline architecture",
        "vector processing instructions",
        "memory coherency protocols"
    ]
    
    for query in test_queries:
        basic_results = basic_rag.retrieve(query, k=5)
        epic2_results = epic2_rag.retrieve(query, k=5)
        
        # Top result should have higher score
        if basic_results and epic2_results:
            improvement = epic2_results[0].score / basic_results[0].score
            assert improvement > 5  # At least 5x improvement
            
            # In some cases, verify 60x improvement
            if "pipeline" in query:
                assert improvement > 50

def test_ranking_quality_improvement():
    """Verify Epic 2 improves ranking quality metrics."""
    golden_test_set = load_golden_test_set()
    
    for test_case in golden_test_set:
        query = test_case["query"]
        relevant_docs = test_case["relevant_docs"]
        
        # Get results from both systems
        basic_results = basic_rag.retrieve(query, k=10)
        epic2_results = epic2_rag.retrieve(query, k=10)
        
        # Calculate nDCG for both
        basic_ndcg = calculate_ndcg(basic_results, relevant_docs)
        epic2_ndcg = calculate_ndcg(epic2_results, relevant_docs)
        
        # Epic 2 should improve nDCG by at least 15%
        assert epic2_ndcg > basic_ndcg * 1.15

def test_component_ablation():
    """Test individual Epic 2 component contributions."""
    query = "RISC-V vector processing"
    
    # Test configurations
    configs = {
        "basic": basic_rag,
        "neural_only": rag_with_neural_reranking,
        "graph_only": rag_with_graph_fusion,
        "full_epic2": epic2_rag
    }
    
    results = {}
    for name, system in configs.items():
        res = system.retrieve(query, k=5)
        results[name] = res[0].score if res else 0
    
    # Each component should contribute
    assert results["neural_only"] > results["basic"]
    assert results["graph_only"] > results["basic"]
    assert results["full_epic2"] > results["neural_only"]
    assert results["full_epic2"] > results["graph_only"]
```

---

## 🧪 Golden Test Set

### Purpose
Provide regression detection and consistent quality benchmarking.

### Structure

```yaml
golden_test_set:
  - id: "technical_query_1"
    query: "RISC-V vector extension implementation"
    relevant_documents:
      - doc_id: "riscv_v_spec.pdf"
        relevance: 1.0
      - doc_id: "riscv_vector_examples.pdf"
        relevance: 0.9
      - doc_id: "simd_comparison.pdf"
        relevance: 0.6
    irrelevant_documents:
      - "arm_neon_guide.pdf"
      - "x86_avx_manual.pdf"
    expected_metrics:
      precision_at_5: 0.6
      precision_at_10: 0.5
      top_result: "riscv_v_spec.pdf"
      min_top_score: 0.8
      
  - id: "ambiguous_query_1"
    query: "pipeline"
    relevant_documents:
      - doc_id: "cpu_pipeline.pdf"
        relevance: 0.7
      - doc_id: "riscv_pipeline.pdf"
        relevance: 0.7
    expected_behavior: "Should return both CPU and RISC-V pipeline docs"
    
  - id: "irrelevant_query_1"
    query: "French cuisine recipes"
    relevant_documents: []
    expected_behavior: "No results or all scores < 0.3"
    max_score: 0.3
```

---

## 📊 Quality Metrics

### Core Metrics

1. **Precision@K**: Percentage of relevant documents in top K results
2. **nDCG**: Normalized Discounted Cumulative Gain
3. **MRR**: Mean Reciprocal Rank of first relevant result
4. **Score Separation**: Gap between relevant and irrelevant scores
5. **Ranking Stability**: Consistency across multiple runs

### Quality Targets

- Precision@5: >0.8 (Epic 2), >0.6 (Basic)
- Precision@10: >0.7 (Epic 2), >0.5 (Basic)
- MRR: >0.9 (Epic 2), >0.7 (Basic)
- Score Separation: >0.3 between relevant/irrelevant
- Ranking Stability: 100% for identical queries

---

## 🚨 Failure Mode Tests

### Edge Cases

```python
def test_empty_query():
    """Verify empty query handling."""
    results = rag_system.retrieve("", k=5)
    assert len(results) == 0 or all(r.score < 0.1 for r in results)

def test_very_long_query():
    """Verify long query handling."""
    long_query = "RISC-V " * 1000  # Very long query
    results = rag_system.retrieve(long_query, k=5)
    # Should truncate and still work
    assert len(results) > 0

def test_special_characters():
    """Verify special character handling."""
    queries = ["RISC-V++", "C# programming", "what?!?", "///\\\\\\"]
    for query in queries:
        # Should not crash
        results = rag_system.retrieve(query, k=5)
        assert isinstance(results, list)

def test_unicode_queries():
    """Verify Unicode handling."""
    queries = ["RISC-V 架构", "RISC-V 🚀", "Ω(n log n)"]
    for query in queries:
        results = rag_system.retrieve(query, k=5)
        assert isinstance(results, list)
```

---

## 🔧 Implementation Guidelines

### Test Structure

```python
# tests/quality/base_quality_test.py
class BaseQualityTest:
    """Base class for quality-focused tests."""
    
    def setup_golden_data(self):
        """Load golden test set."""
        pass
    
    def calculate_metrics(self, results, relevant_docs):
        """Calculate quality metrics."""
        pass
    
    def assert_quality_improvement(self, basic_results, epic2_results):
        """Verify Epic 2 improves over basic."""
        pass
```

### Test Organization

```
tests/quality/
├── __init__.py
├── base_quality_test.py          # Base test utilities
├── test_bm25_scoring.py          # BM25 algorithm tests
├── test_vector_similarity.py     # Embedding quality tests
├── test_fusion_algorithms.py     # Fusion correctness tests
├── test_neural_reranking.py      # Reranking quality tests
├── test_retrieval_precision.py   # End-to-end quality tests
├── test_epic2_improvements.py    # Comparative tests
├── golden_test_set.yaml         # Golden test data
└── metrics.py                   # Quality metric calculations
```

---

## ✅ Success Criteria

1. All scoring algorithms pass mathematical validation
2. Semantic similarities fall within expected ranges
3. Fusion algorithms implement correct formulas
4. Neural reranking demonstrably improves relevance
5. End-to-end precision meets targets
6. Epic 2 shows statistically significant improvements
7. Edge cases handled gracefully
8. Golden test set provides stable benchmarks

This comprehensive test plan ensures the RAG system is validated for actual retrieval quality, not just mechanical functionality.