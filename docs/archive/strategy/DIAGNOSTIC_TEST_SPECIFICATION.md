# Comprehensive Diagnostic Test Specification

**Date**: January 8, 2025  
**Purpose**: Systematic diagnosis of RAG system quality issues discovered in Phase 5 demo validation  
**Scope**: End-to-end pipeline analysis from document processing to answer generation  

## Executive Summary

The Phase 5 demo validation revealed **critical answer quality failures** that make the system unsuitable for portfolio demonstration. This specification defines a comprehensive diagnostic testing strategy to identify and analyze every component, interface, and data transformation point in the RAG pipeline.

**Critical Issues Identified:**
- Answer quality: Nonsensical responses ("Editors" for "Who am I?")
- Confidence scoring: All answers at 0.100 (10%)
- Source attribution: "Page unknown from unknown" errors
- Architecture mismatch: Claims Phase 4 but shows legacy
- Cache performance: 0% hit rate despite heavy usage

## System Architecture Analysis

### Current Phase 4 Architecture
```
Document → PDF Processor → Document Objects → Embedder → Vector Store
                                          ↓
Query → Platform Orchestrator → Retriever → Answer Generator → Answer Object
                                          ↓
                        Query Processor → Health Monitoring
```

### Component Interfaces to Validate
1. **Document Processing Interface**: `Path → List[Document]`
2. **Embedding Interface**: `List[str] → List[List[float]]`
3. **Vector Storage Interface**: `List[Document] → None` (indexing)
4. **Retrieval Interface**: `str → List[RetrievalResult]`
5. **Generation Interface**: `str + List[RetrievalResult] → Answer`
6. **Health Monitoring Interface**: `None → Dict[str, Any]`

## Detailed Test Specification

### Test Suite 1: Document Processing Validation

#### Test 1.1: PDF Metadata Extraction
**Objective**: Diagnose "Page unknown from unknown" source attribution errors

**Test Cases:**
```python
# Input: Single PDF with known structure
pdf_path = "data/test/riscv-card.pdf"

# Expected Outputs:
document.metadata = {
    'source': 'data/test/riscv-card.pdf',
    'page': <actual_page_number>,
    'section': <section_if_available>,
    'chunk_id': <sequential_id>
}

# Validation Points:
1. metadata['source'] != 'unknown'
2. metadata['page'] != 'unknown' 
3. All required fields present
4. Page numbers are integers or valid strings
```

**Data Collection:**
- Raw PDF structure analysis
- Metadata extraction at each processing step
- Document object field validation
- Comparison with expected vs actual metadata

#### Test 1.2: Content Chunking Quality
**Objective**: Validate chunk content quality and boundaries

**Test Cases:**
```python
# Input: Technical document with known structure
# Expected: Coherent chunks with proper boundaries

# Validation Points:
1. Chunks contain complete sentences
2. Technical terms not split across chunks
3. Chunk overlap preserves context
4. Chunk size within specified limits
5. No empty or malformed chunks
```

**Data Collection:**
- Chunk content analysis
- Boundary detection validation
- Overlap quality assessment
- Content coherence scoring

#### Test 1.3: Document Object Validation
**Objective**: Ensure Document objects conform to interface specification

**Test Cases:**
```python
# For each Document object:
assert isinstance(doc.content, str)
assert len(doc.content) > 0
assert isinstance(doc.metadata, dict)
assert 'source' in doc.metadata
assert doc.embedding is None or isinstance(doc.embedding, list)
```

### Test Suite 2: Embedding and Vector Storage Validation

#### Test 2.1: Embedding Generation Quality
**Objective**: Validate embedding model performance and consistency

**Test Cases:**
```python
# Input: Known text samples
test_texts = [
    "RISC-V is an instruction set architecture",
    "ARM processors are widely used",
    "Machine learning requires data"
]

# Validation Points:
1. Embeddings have correct dimensionality (384 for MiniLM)
2. Similar texts have high cosine similarity
3. Different topics have low cosine similarity
4. Embeddings are normalized if expected
5. No NaN or infinite values
```

**Data Collection:**
- Embedding dimensionality verification
- Similarity matrix analysis
- Embedding distribution statistics
- Model consistency validation

#### Test 2.2: Vector Store Indexing Validation
**Objective**: Ensure proper document indexing and storage

**Test Cases:**
```python
# Process documents and validate storage
documents = processor.process(pdf_path)
vector_store.add(documents)

# Validation Points:
1. All documents indexed successfully
2. Vector store size matches document count
3. Stored embeddings match generated embeddings
4. Document metadata preserved in storage
5. Index structure integrity
```

### Test Suite 3: Retrieval System Validation

#### Test 3.1: Dense Retrieval Quality
**Objective**: Validate semantic similarity retrieval

**Test Cases:**
```python
# Known query-answer pairs from documents
test_cases = [
    {
        'query': 'What is RISC-V?',
        'expected_topics': ['instruction set', 'architecture', 'RISC'],
        'expected_sources': ['riscv-card.pdf', 'unpriv-isa-asciidoc.pdf']
    }
]

# Validation Points:
1. Retrieved chunks contain expected topics
2. Similarity scores are reasonable (>0.3 for relevant)
3. Most relevant chunks ranked highest
4. Source documents match expectations
```

#### Test 3.2: Sparse Retrieval (BM25) Quality
**Objective**: Validate keyword-based retrieval

**Test Cases:**
```python
# Keyword-specific queries
queries = [
    'RISC-V instruction set',  # Should find exact matches
    'vector extension',        # Should find technical terms
    'memory operations'        # Should find related content
]

# Validation Points:
1. Exact keyword matches ranked highly
2. Term frequency scoring working
3. Document frequency normalization applied
4. No irrelevant chunks in top results
```

#### Test 3.3: Hybrid Fusion Validation
**Objective**: Validate Reciprocal Rank Fusion (RRF) implementation

**Test Cases:**
```python
# Compare dense vs sparse vs hybrid results
query = "What are atomic memory operations?"

dense_results = dense_retriever.retrieve(query, k=10)
sparse_results = sparse_retriever.retrieve(query, k=10)
hybrid_results = hybrid_retriever.retrieve(query, k=10)

# Validation Points:
1. Hybrid combines both result sets
2. RRF scoring formula applied correctly
3. Final ranking balances semantic + keyword relevance
4. No duplicate chunks in final results
5. Fusion weights applied as configured
```

### Test Suite 4: Answer Generation Deep Analysis

#### Test 4.1: Model Selection and Configuration
**Objective**: Validate answer generation model setup

**Test Cases:**
```python
# Inspect actual model being used
generator = answer_generator

# Validation Points:
1. Model type (extractive vs generative)
2. Model configuration parameters
3. Temperature, max_length settings
4. Tokenizer configuration
5. Model loading success
```

**Critical Analysis:**
- **Current Issue**: Squad2 is extractive QA model, not generative
- **Expected**: Should use generative model (T5, BART, GPT) or implement post-processing

#### Test 4.2: Context Preparation Analysis
**Objective**: Validate context formatting for answer generation

**Test Cases:**
```python
# Trace context preparation pipeline
query = "What is RISC-V?"
retrieved_chunks = retriever.retrieve(query, k=5)
formatted_context = generator._prepare_context(query, retrieved_chunks)

# Validation Points:
1. Context format matches model expectations
2. Chunk content properly formatted
3. Source attribution included
4. Context length within model limits
5. Special tokens handled correctly
```

#### Test 4.3: Model Inference Analysis
**Objective**: Deep dive into model prediction process

**Test Cases:**
```python
# Detailed inference tracing
inputs = tokenizer(formatted_input, return_tensors="pt")
with torch.no_grad():
    outputs = model(**inputs)
    
# Validation Points:
1. Input tokenization correct
2. Model forward pass successful
3. Output format analysis (logits, scores)
4. Post-processing steps
5. Confidence calculation method
```

#### Test 4.4: Confidence Scoring Deep Analysis
**Objective**: Understand confidence calculation mechanism

**Test Cases:**
```python
# Trace confidence calculation
answer_obj = generator.generate(query, context)

# Validation Points:
1. Where confidence is calculated
2. Confidence calculation method
3. Confidence range validation (0-1)
4. Confidence vs model uncertainty correlation
5. Confidence vs answer quality correlation
```

**Critical Investigation:**
- **Issue**: All answers show 0.100 confidence
- **Root Cause Analysis Required**: 
  - Is confidence hardcoded?
  - Is calculation method broken?
  - Is model uncertainty not propagated?

### Test Suite 5: Source Attribution and Metadata Analysis

#### Test 5.1: Citation Generation Analysis
**Objective**: Diagnose source attribution failures

**Test Cases:**
```python
# Trace citation creation process
answer = generator.generate(query, retrieved_chunks)

# Validation Points:
1. Citation extraction from retrieved chunks
2. Source metadata propagation
3. Page number preservation
4. Citation formatting
5. Citation-answer alignment
```

#### Test 5.2: Metadata Preservation Chain
**Objective**: Track metadata through entire pipeline

**Test Cases:**
```python
# End-to-end metadata tracking
pdf_path → pdf_processor → documents → embedder → vector_store → retriever → generator

# Validation at each stage:
1. PDF: Original file metadata
2. Documents: Extracted metadata
3. Vector Store: Stored metadata
4. Retrieval: Retrieved metadata
5. Answer: Citation metadata
```

### Test Suite 6: System Health and Architecture Validation

#### Test 6.1: Architecture Detection Validation
**Objective**: Diagnose architecture display mismatch

**Test Cases:**
```python
# Validate architecture detection logic
health = orchestrator.get_system_health()

# Validation Points:
1. Configuration file analysis
2. Component type detection
3. Architecture classification logic
4. Health reporting accuracy
```

#### Test 6.2: Component Factory Analysis
**Objective**: Diagnose cache performance issues

**Test Cases:**
```python
# Trace component creation and caching
factory_stats = ComponentFactory.get_performance_metrics()

# Validation Points:
1. Component creation tracking
2. Cache hit/miss counting
3. Cache key generation
4. Cache storage mechanism
5. Metrics aggregation
```

### Test Suite 7: End-to-End Quality Validation

#### Test 7.1: Known Good Cases
**Objective**: Test with questions that should work well

**Test Cases:**
```python
good_cases = [
    {
        'query': 'What is RISC-V?',
        'expected_answer_contains': ['instruction set', 'architecture', 'open'],
        'min_answer_length': 50,
        'min_confidence': 0.3,
        'expected_sources': ['riscv']
    }
]
```

#### Test 7.2: Known Bad Cases
**Objective**: Test with questions that should be refused

**Test Cases:**
```python
bad_cases = [
    {
        'query': 'Where is Paris?',
        'expected_behavior': 'refuse',
        'expected_answer_contains': ['cannot answer', 'not found', 'no information']
    },
    {
        'query': 'Who am I?',
        'expected_behavior': 'refuse'
    }
]
```

#### Test 7.3: Confidence Calibration Validation
**Objective**: Validate confidence vs answer quality correlation

**Test Cases:**
```python
# Test confidence across quality spectrum
queries_by_quality = {
    'high_quality': ["What is RISC-V?", "What are the main RISC-V extensions?"],
    'medium_quality': ["How does RISC-V compare to x86?"],
    'low_quality': ["What is the weather today?"],
    'impossible': ["Where is Paris?"]
}

# Expected confidence ranges:
# high_quality: >0.7
# medium_quality: 0.3-0.7
# low_quality: 0.1-0.3
# impossible: <0.1 (should refuse)
```

## Data Collection Strategy

### 1. Raw Data Capture
For each test, capture:
- Input data (queries, documents, configurations)
- Intermediate outputs at each pipeline stage
- Final outputs (answers, metadata, metrics)
- Timing information
- Error messages and stack traces

### 2. Structured Analysis
Create analysis templates:
```python
@dataclass
class DiagnosticResult:
    test_name: str
    component: str
    input_data: Any
    expected_output: Any
    actual_output: Any
    validation_results: Dict[str, bool]
    issues_found: List[str]
    recommendations: List[str]
    raw_data: Dict[str, Any]
```

### 3. Comparison Analysis
- Expected vs Actual outputs
- Current vs Previous behavior (if baseline available)
- Component A vs Component B (dense vs sparse retrieval)
- Configuration A vs Configuration B (legacy vs unified)

## Implementation Strategy

### Phase 1: Infrastructure Setup (30 minutes)
1. **Create diagnostic test framework**
   - Base test classes with data capture
   - Result aggregation and reporting
   - Error handling and logging

2. **Update imports and dependencies**
   - Adapt old test imports to Phase 4 architecture
   - Ensure compatibility with current interfaces
   - Set up test data paths

### Phase 2: Component-Level Diagnostics (2 hours)
1. **Document Processing Tests** (30 min)
   - PDF metadata extraction validation
   - Chunk quality analysis
   - Document object compliance

2. **Embedding and Storage Tests** (30 min)
   - Embedding generation validation
   - Vector store indexing verification
   - Similarity calculation accuracy

3. **Retrieval System Tests** (45 min)
   - Dense retrieval quality
   - Sparse retrieval quality
   - Hybrid fusion analysis

4. **Answer Generation Deep Dive** (45 min)
   - Model configuration analysis
   - Context preparation validation
   - Inference process tracing
   - Confidence calculation diagnosis

### Phase 3: Integration and Quality Tests (1 hour)
1. **End-to-End Pipeline Tests** (30 min)
   - Known good cases validation
   - Known bad cases validation
   - Edge case handling

2. **System Health Validation** (30 min)
   - Architecture detection verification
   - Component factory analysis
   - Performance metrics validation

### Phase 4: Analysis and Reporting (30 minutes)
1. **Issue Prioritization**
   - Critical vs non-critical issues
   - Root cause identification
   - Fix complexity assessment

2. **Comprehensive Report Generation**
   - Detailed findings per component
   - Data flow analysis
   - Recommended fixes with implementation order

## Quality Gates

### Pass Criteria for Each Test
1. **Data Integrity**: All data transformations preserve required information
2. **Interface Compliance**: All components meet interface specifications
3. **Performance Baseline**: Components perform within expected parameters
4. **Error Handling**: Graceful handling of edge cases and invalid inputs

### Failure Analysis Protocol
For each failed test:
1. **Root Cause Analysis**: Trace issue to specific component/code
2. **Impact Assessment**: How does this affect end-user experience?
3. **Fix Complexity**: How difficult is this to fix?
4. **Workaround Options**: Can we mitigate while fixing?

## Expected Outcomes

### Issue Classification
- **Critical**: Breaks core functionality (answer quality, confidence)
- **High**: Affects user experience (source attribution, metadata)
- **Medium**: Performance or display issues (cache, architecture display)
- **Low**: Cosmetic or non-functional issues

### Detailed Fix Roadmap
- Prioritized list of issues with specific solutions
- Code changes required for each fix
- Testing strategy for validation
- Rollback plan if fixes introduce new issues

### Validation Strategy
- Updated test suite for continuous validation
- Performance benchmarks for regression detection
- Quality metrics for ongoing monitoring

This comprehensive diagnostic approach will ensure we understand exactly what's broken, why it's broken, and how to fix it systematically without introducing new issues.