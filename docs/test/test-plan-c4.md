# Test Plan: Component 4 - Retriever

**Component ID**: C4  
**Version**: 1.0  
**References**: [COMPONENT-4-RETRIEVER.md](./COMPONENT-4-RETRIEVER.md), [MASTER-TEST-STRATEGY.md](./MASTER-TEST-STRATEGY.md)  
**Last Updated**: July 2025

---

## 1. Test Scope

### 1.1 Component Overview

The Retriever implements hybrid search capabilities combining vector similarity and keyword matching to find relevant documents. This test plan validates its ability to store, search, fuse results, and rerank documents according to architectural specifications.

### 1.2 Testing Focus Areas

1. **Vector Search**: Dense retrieval accuracy and performance
2. **Sparse Search**: Keyword-based retrieval effectiveness
3. **Hybrid Fusion**: Result combination strategies
4. **Reranking**: Relevance improvement validation
5. **Index Management**: Storage, updates, and deletion

### 1.3 Sub-Components to Test

- Vector Index (FAISS direct, Pinecone adapter)
- Sparse Retriever (BM25 direct, Elasticsearch adapter)
- Fusion Strategy (RRF, Weighted, ML-based)
- Reranker (Cross-encoder, ColBERT, LLM-based)
- Metadata Store

### 1.4 Architecture Compliance Focus

- Validate unified retriever pattern
- Verify adapter usage for cloud services
- Ensure direct implementation for algorithms
- Confirm pluggable fusion and reranking strategies

---

## 2. Test Requirements Traceability

| Requirement | Test Cases | Priority |
|-------------|------------|----------|
| FR1: Store and index document embeddings | C4-FUNC-001 to C4-FUNC-005 | High |
| FR2: Perform vector similarity search | C4-FUNC-006 to C4-FUNC-010 | High |
| FR3: Execute keyword-based search | C4-FUNC-011 to C4-FUNC-015 | High |
| FR4: Fuse multiple retrieval signals | C4-FUNC-016 to C4-FUNC-020 | High |
| FR5: Rerank results for relevance | C4-FUNC-021 to C4-FUNC-025 | Medium |

---

## 3. Test Cases

### 3.1 Sub-Component Tests

#### C4-SUB-001: Vector Index Architecture
**Requirement**: Index implementation patterns  
**Priority**: High  
**Type**: Architecture  

**Test Steps**:
1. Verify FAISS direct implementation
2. Test Pinecone adapter implementation
3. Validate consistent index interface
4. Check index switching capability
5. Test error handling patterns

**PASS Criteria**:
- Architecture:
  - FAISS uses direct implementation
  - Pinecone uses adapter pattern
  - Consistent IndexInterface
  - Clean abstraction layer
- Functional:
  - Both indices work correctly
  - Seamless switching possible

**FAIL Criteria**:
- Pattern violations
- Inconsistent interfaces
- Switching causes errors
- Abstraction leakage

---

#### C4-SUB-002: Sparse Retriever Patterns
**Requirement**: Sparse search implementations  
**Priority**: High  
**Type**: Architecture  

**Test Steps**:
1. Test BM25 direct implementation
2. Verify Elasticsearch adapter
3. Check tokenization consistency
4. Validate scoring normalization
5. Test configuration handling

**PASS Criteria**:
- Architecture:
  - BM25 directly implemented
  - Elasticsearch via adapter
  - Consistent scoring interface
  - Pluggable tokenizers
- Performance:
  - BM25 <5ms for 10K docs
  - Linear scaling

**FAIL Criteria**:
- Adapter misuse
- Inconsistent scoring
- Poor performance
- Configuration errors

---

#### C4-SUB-003: Fusion Strategy Validation
**Requirement**: Result fusion patterns  
**Priority**: High  
**Type**: Functional  

**Test Steps**:
1. Test RRF fusion algorithm
2. Validate weighted fusion
3. Test ML-based fusion
4. Compare fusion effectiveness
5. Verify score normalization

**PASS Criteria**:
- Functional:
  - All strategies implement FusionInterface
  - RRF produces stable rankings
  - Weighted fusion respects weights
  - Scores properly normalized [0,1]
- Quality:
  - Fusion improves results
  - No result loss

**FAIL Criteria**:
- Interface violations
- Unstable rankings
- Score range violations
- Result degradation

---

#### C4-SUB-004: Reranker Components
**Requirement**: Reranking architecture  
**Priority**: Medium  
**Type**: Architecture  

**Test Steps**:
1. Test cross-encoder reranker
2. Validate ColBERT reranker
3. Test LLM-based reranker
4. Verify reranker chaining
5. Test performance impact

**PASS Criteria**:
- Architecture:
  - All rerankers implement RerankerInterface
  - Model-based rerankers use adapters
  - Clean abstraction maintained
  - Chainable rerankers work
- Performance:
  - Reranking <50ms for 100 docs
  - Quality improvement measurable

**FAIL Criteria**:
- Interface inconsistency
- Adapter pattern violations
- Performance regression
- Quality degradation

---

### 3.2 Functional Tests - Indexing

#### C4-FUNC-001: Document Indexing
**Requirement**: FR1  
**Priority**: High  
**Type**: Functional  

**Preconditions**:
- Retriever initialized
- Documents with embeddings prepared

**Test Steps**:
1. Index single document
2. Index batch of documents
3. Verify index size updates
4. Check metadata storage
5. Confirm immediate searchability

**PASS Criteria**:
- Functional:
  - All documents indexed without errors
  - Index size = number of documents
  - 100% metadata preservation
  - Search finds indexed docs immediately
- Performance:
  - Indexing rate >10K docs/second
  - Batch indexing 10x faster

**FAIL Criteria**:
- Indexing failures
- Incorrect index size
- Lost metadata
- Search delay after indexing

---

#### C4-FUNC-002: Duplicate Document Handling
**Requirement**: FR1  
**Priority**: Medium  
**Type**: Functional  

**Preconditions**:
- Documents with same ID
- Existing indexed documents

**Test Steps**:
1. Index document A with ID=1
2. Index document B with ID=1
3. Search for content from A
4. Search for content from B
5. Verify replacement behavior

**PASS Criteria**:
- Functional:
  - Duplicate ID replaces existing
  - Index size remains constant
  - Latest content searchable
  - Metadata fully updated
- Quality:
  - No orphaned embeddings
  - Consistent state maintained

**FAIL Criteria**:
- Duplicate entries created
- Old content still found
- Metadata inconsistency
- Index corruption

---

#### C4-FUNC-003: Index Persistence
**Requirement**: FR1  
**Priority**: High  
**Type**: Functional  

**Preconditions**:
- Documents indexed
- Persistence enabled

**Test Steps**:
1. Index documents
2. Save index to disk
3. Create new retriever instance
4. Load saved index
5. Verify search functionality

**PASS Criteria**:
- Functional:
  - Index saves to specified path
  - Loading restores 100% of data
  - Search results identical after reload
  - Metadata intact
- Performance:
  - Save time <1s per 100K docs
  - Load time <2s per 100K docs

**FAIL Criteria**:
- Save failures
- Data loss on reload
- Search differences
- Slow save/load

---

### 3.3 Functional Tests - Vector Search

#### C4-FUNC-006: Basic Vector Search
**Requirement**: FR2  
**Priority**: High  
**Type**: Functional  

**Preconditions**:
- Documents indexed with embeddings
- Query embedding generated

**Test Steps**:
1. Search with exact match query
2. Search with similar query
3. Search with unrelated query
4. Verify result ordering
5. Check score ranges

**PASS Criteria**:
- Functional:
  - Exact match score = 1.0
  - Similar content score >0.8
  - Unrelated content score <0.3
  - All scores in [0, 1] range
- Quality:
  - Monotonic score ordering
  - Meaningful score differences

**FAIL Criteria**:
- Incorrect scoring
- Score range violations
- Poor discrimination
- Unstable rankings

---

#### C4-FUNC-007: Vector Search with k Parameter
**Requirement**: FR2  
**Priority**: High  
**Type**: Functional  

**Preconditions**:
- At least 20 documents indexed
- Query prepared

**Test Steps**:
1. Search with k=1
2. Search with k=5
3. Search with k=10
4. Search with k=100
5. Verify result counts

**Expected Results**:
- Returns exactly k results (or all if less)
- Results ordered by score
- Same top results for different k
- No duplicates

---

### 3.4 Functional Tests - Sparse Search

#### C4-FUNC-011: BM25 Keyword Search
**Requirement**: FR3  
**Priority**: High  
**Type**: Functional  

**Preconditions**:
- Documents indexed for BM25
- Keyword queries prepared

**Test Steps**:
1. Search single keyword
2. Search multiple keywords
3. Search exact phrase
4. Search with stop words
5. Verify technical term handling

**Expected Results**:
- Keyword matches found
- Multi-term queries work
- Exact phrases matched
- Stop words handled properly
- Technical terms preserved

---

#### C4-FUNC-012: Sparse Search Edge Cases
**Requirement**: FR3  
**Priority**: Medium  
**Type**: Functional  

**Preconditions**:
- Special content indexed
- Edge case queries

**Test Steps**:
1. Search with special characters
2. Search with numbers only
3. Search with very long query
4. Search with typos
5. Search non-existent terms

**Expected Results**:
- Special chars handled gracefully
- Numbers searchable
- Long queries truncated safely
- No results for non-existent
- No crashes or errors

---

### 3.5 Functional Tests - Fusion

#### C4-FUNC-016: RRF Fusion Strategy
**Requirement**: FR4  
**Priority**: High  
**Type**: Functional  

**Preconditions**:
- Both vector and sparse results available
- RRF fusion configured

**Test Steps**:
1. Get vector search results
2. Get sparse search results
3. Apply RRF fusion
4. Verify score calculation
5. Check result ordering

**PASS Criteria**:
- Functional:
  - All unique results included
  - RRF formula: 1/(k+rank) applied
  - Higher combined scores = better rank
  - Zero duplicate documents
  - Scores normalized to [0, 1]
- Quality:
  - Fusion improves relevance
  - Stable across runs

**FAIL Criteria**:
- Missing results
- Formula errors
- Duplicates present
- Score range violations

---

#### C4-FUNC-017: Weighted Fusion
**Requirement**: FR4  
**Priority**: Medium  
**Type**: Functional  

**Preconditions**:
- Fusion weights configured
- Multiple search results

**Test Steps**:
1. Set dense weight = 0.7
2. Set sparse weight = 0.3
3. Execute fusion
4. Verify weight application
5. Test different weight combinations

**PASS Criteria**:
- Functional:
  - score = 0.7*dense + 0.3*sparse
  - Dense bias visible in results
  - Linear combination verified
  - Weights sum to 1.0
  - Configuration works correctly
- Quality:
  - Smooth weight effects
  - No weight dominance bugs

**FAIL Criteria**:
- Weight math incorrect
- Non-linear effects
- Weights don't sum to 1.0
- Configuration ignored

---

### 3.6 Performance Tests

#### C4-PERF-001: Search Latency
**Requirement**: QR - <10ms average  
**Priority**: High  
**Type**: Performance  

**Test Steps**:
1. Index 10K documents
2. Prepare 100 test queries
3. Measure search time per query
4. Calculate percentiles
5. Test with different k values

**Expected Results**:
- Average latency <10ms
- p95 latency <20ms
- p99 latency <50ms
- Linear scaling with k

---

#### C4-PERF-002: Indexing Throughput
**Requirement**: QR - >10K docs/second  
**Priority**: High  
**Type**: Performance  

**Test Steps**:
1. Prepare 100K documents
2. Measure batch indexing time
3. Calculate documents/second
4. Monitor memory usage
5. Check index quality

**Expected Results**:
- Throughput >10K docs/sec
- Stable memory usage
- No quality degradation
- Linear scaling

---

#### C4-PERF-003: Reranking Performance
**Requirement**: QR - <50ms for 100 docs  
**Priority**: Medium  
**Type**: Performance  

**Test Steps**:
1. Retrieve 100 documents
2. Apply cross-encoder reranking
3. Measure reranking time
4. Test different rerankers
5. Profile bottlenecks

**Expected Results**:
- Reranking <50ms
- Quality improvement measurable
- Batch processing efficient
- GPU acceleration works

---

### 3.7 Adapter Pattern Tests

#### C4-ADAPT-001: Pinecone Adapter
**Requirement**: Architecture - Adapter pattern  
**Priority**: High  
**Type**: Compliance  

**Test Steps**:
1. Configure Pinecone adapter
2. Test all CRUD operations
3. Verify API translation
4. Check error handling
5. Monitor API calls

**Expected Results**:
- Same interface as FAISS
- API calls correct
- Errors mapped properly
- Latency acceptable
- Cost tracking enabled

---

### 3.8 Resilience Tests

#### C4-RESIL-001: Index Corruption Recovery
**Requirement**: Reliability  
**Priority**: High  
**Type**: Resilience  

**Test Steps**:
1. Corrupt index file partially
2. Attempt to load index
3. Verify error detection
4. Test recovery procedure
5. Validate index integrity

**Expected Results**:
- Corruption detected
- Clear error message
- Recovery possible
- Partial data salvageable
- Integrity checks work

---

## 4. Test Data Requirements

### 4.1 Document Collections

**Small Collection** (1K docs):
- Diverse topics
- Various lengths
- Quality labels for evaluation

**Medium Collection** (10K docs):
- Performance testing
- Real-world distribution
- Known relevant pairs

**Large Collection** (100K+ docs):
- Scalability testing
- Index optimization
- Stress testing

### 4.2 Query Sets

**Functional Queries**:
- Exact match queries
- Semantic variations
- Multi-term queries
- Edge cases

**Performance Queries**:
- 1000 diverse queries
- Different complexity levels
- Relevance judgments

---

## 5. Test Environment Setup

### 5.1 Index Configurations

**Local Testing**:
- FAISS with different index types
- BM25 with custom tokenization
- In-memory operation

**Cloud Testing**:
- Pinecone sandbox
- Elasticsearch cluster
- Network latency simulation

### 5.2 Evaluation Metrics

- Precision@k
- Recall@k
- Mean Reciprocal Rank
- NDCG@k

---

## 6. Risk-Based Test Prioritization

### 6.1 High Priority Tests

1. Basic search functionality (core feature)
2. Hybrid search fusion (key differentiator)
3. Index persistence (data integrity)
4. Search performance (user experience)

### 6.2 Medium Priority Tests

1. Reranking effectiveness
2. Advanced fusion strategies
3. Metadata filtering
4. Batch operations

### 6.3 Low Priority Tests

1. Exotic query types
2. Extreme scale limits
3. Alternative index types

---

## 7. Sub-Component Integration Tests

### 7.1 Vector + Sparse Integration

- Verify independent operation
- Test result alignment
- Check score normalization
- Validate parallel execution

### 7.2 Fusion + Reranking Pipeline

- Test end-to-end flow
- Verify no data loss
- Check performance impact
- Validate quality improvement

### 7.3 Index + Metadata Coordination

- Ensure consistency
- Test atomic updates
- Verify transaction semantics
- Check referential integrity

---

## 8. Exit Criteria

### 8.1 Functional Coverage

- All search types tested
- All fusion strategies verified
- Reranking validated
- Index operations complete

### 8.2 Performance Criteria

- Latency targets met
- Throughput verified
- Scalability demonstrated
- Resource usage acceptable

### 8.3 Quality Gates

- Search accuracy >90%
- Zero data loss bugs
- No index corruption
- All adapters functional