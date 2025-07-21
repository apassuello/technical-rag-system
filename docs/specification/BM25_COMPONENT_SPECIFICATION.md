# BM25 Sparse Retrieval Component Specification

**Component**: BM25Retriever (Sparse Retrieval Sub-component)  
**Version**: 2.0  
**Domain**: RISC-V Technical Documentation RAG System  
**Status**: Production Ready  
**Architecture**: Direct Implementation Pattern

## 1. Component Role & Purpose

### Primary Role
The BM25Retriever serves as the **lexical matching engine** within the ModularUnifiedRetriever, providing keyword-based document retrieval for RISC-V technical documentation queries.

### Core Responsibilities
- **Lexical Matching**: Find documents containing query terms using BM25 ranking
- **Technical Term Handling**: Preserve RISC-V-specific terminology (RV32I, CSR, etc.)
- **Score Normalization**: Provide [0,1] normalized scores for fusion with semantic retrieval
- **Performance Optimization**: Maintain <10ms search latency for production use

### Domain Context
- **Specialized Corpus**: All documents are RISC-V related (specifications, papers, tutorials)
- **Technical Vocabulary**: Rich domain-specific terminology (ISA, extensions, instructions)
- **Query Patterns**: Mix of high-level concepts ("vector operations") and specific terms ("RV32I ADD")

## 2. Expected Behavior

### 2.1 Query Processing Behavior

#### High-Level Technical Queries
```
Query: "vector instruction set"
Expected: Returns documents about RISC-V vector extension (V-ext)
Rationale: "vector" + "instruction" are discriminative technical terms
```

#### Specific Technical Queries  
```
Query: "RV32I base integer instructions"
Expected: Returns base ISA specification documents
Rationale: "RV32I", "base", "integer" are highly specific technical terms
```

#### Architectural Queries
```
Query: "privilege levels supervisor mode"
Expected: Returns privileged architecture specification
Rationale: "privilege", "supervisor", "mode" are architectural concepts
```

#### Out-of-Domain Queries
```
Query: "Napoleon's favorite instruction"
Expected: Returns empty results (score = 0.0 for all documents)
Rationale: "Napoleon" has no technical relevance in RISC-V corpus
```

### 2.2 Scoring Behavior

#### Domain-Specific Scoring Characteristics
- **"RISC-V" term**: Low discriminative power (appears in ~90% of documents)
- **Technical terms**: High discriminative power ("vector", "privilege", "compressed")
- **Instruction names**: Very high discriminative power ("ADD", "LW", "FENCE")
- **Extension codes**: Maximum discriminative power ("RV32I", "RV64G", "Zicsr")

#### Score Distribution Expectations
- **Relevant queries**: 1-5 documents with scores >0.1 after normalization
- **Highly specific queries**: 1-2 documents with scores >0.8 after normalization  
- **Irrelevant queries**: All documents score 0.0 (BM25 handles this naturally)

### 2.3 Performance Characteristics
- **Search Latency**: <10ms for 95th percentile queries
- **Index Size**: Efficient for 1K-10K document corpus
- **Memory Usage**: <500MB for typical RISC-V documentation corpus

## 3. Functional Requirements

### 3.1 Core Functionality (MUST HAVE)

#### FR1: BM25 Lexical Matching
- **Implementation**: Use rank_bm25 library with standard parameters (k1=1.2, b=0.75)
- **Input**: Preprocessed query tokens
- **Output**: BM25 relevance scores for all indexed documents
- **Validation**: Verify score calculation matches BM25 formula

#### FR2: Technical Term Preservation
- **Hyphenated Terms**: Preserve "RISC-V", "RV32I-based", "floating-point"
- **Alphanumeric Codes**: Preserve "RV32I", "Zicsr", "F-ext", "CSR0x300"
- **Case Sensitivity**: Handle "ADD" vs "add" appropriately for instruction names
- **Validation**: Technical terms remain intact through preprocessing

#### FR3: Basic Stopword Filtering
- **Scope**: Remove only linguistic noise words ("the", "is", "and", "or", "but")
- **Preserve**: All technical and domain-specific terms
- **Configuration**: Use "english_common" stopword set (100-120 words)
- **Validation**: No technical terms filtered incorrectly

#### FR4: Score Normalization
- **Range**: Convert BM25 scores to [0,1] range for fusion compatibility
- **Method**: Min-max normalization across result set
- **Negative Scores**: Handle rank_bm25 library negative score bug by shifting
- **Validation**: All output scores in [0,1] range

#### FR5: Performance Optimization
- **Indexing**: Support batch document indexing with progress monitoring
- **Caching**: Cache preprocessed tokens for repeated documents
- **Memory**: Efficient memory usage for large document collections
- **Validation**: Meet latency and memory requirements

### 3.2 Configuration Requirements (MUST HAVE)

#### CR1: BM25 Parameters
```yaml
k1: 1.2                    # Term frequency saturation (standard)
b: 0.75                    # Document length normalization (standard)
```

#### CR2: Preprocessing Parameters
```yaml
lowercase: true            # Convert to lowercase for matching
preserve_technical_terms: true  # Keep hyphenated/alphanumeric terms
filter_stop_words: true    # Enable linguistic stopword filtering
stop_word_sets: ["english_common"]  # Use standard linguistic stopwords only
min_word_length: 2         # Filter very short tokens
```

#### CR3: Performance Parameters
```yaml
min_score: 0.0            # Minimum normalized score threshold
debug_stop_words: false   # Enable/disable preprocessing debug logs
```

### 3.3 Integration Requirements (MUST HAVE)

#### IR1: ModularUnifiedRetriever Integration
- **Interface**: Implement SparseRetriever base class
- **Document Format**: Accept src.core.interfaces.Document objects
- **Result Format**: Return List[Tuple[int, float]] (doc_index, normalized_score)
- **Error Handling**: Graceful failure with informative error messages

#### IR2: ComponentFactory Integration
- **Registration**: Available via ComponentFactory.create_retriever()
- **Configuration**: Support Epic 2 configuration hierarchy
- **Logging**: Enhanced logging with sub-component identification
- **Initialization**: Fast component creation (<100ms)

## 4. Validation & Test Strategy

### 4.1 Unit Test Requirements

#### UT1: Technical Term Preservation Tests
```python
def test_technical_term_preservation():
    """Verify RISC-V technical terms are preserved during preprocessing."""
    test_cases = [
        ("RV32I base instructions", ["rv32i", "base", "instructions"]),
        ("RISC-V vector extension", ["risc-v", "vector", "extension"]),
        ("floating-point operations", ["floating-point", "operations"]),
        ("CSR0x300 machine mode", ["csr0x300", "machine", "mode"])
    ]
    # Validate each case preserves technical terms
```

#### UT2: Stopword Filtering Tests
```python
def test_stopword_filtering():
    """Verify only linguistic stopwords are filtered."""
    test_cases = [
        ("The RISC-V ISA is modular", ["risc-v", "isa", "modular"]),
        ("Vector operations are efficient", ["vector", "operations", "efficient"]),
        ("Instructions and extensions", ["instructions", "extensions"])
    ]
    # Validate "the", "is", "are", "and" removed but technical terms preserved
```

#### UT3: Domain-Specific Scoring Tests
```python
def test_domain_scoring():
    """Test scoring behavior with realistic RISC-V corpus."""
    corpus = load_riscv_test_documents()  # 6 RISC-V focused documents
    queries = [
        ("vector instructions", "should_match_vector_docs"),
        ("base integer operations", "should_match_base_isa_docs"),
        ("privilege architecture", "should_match_privileged_docs"),
        ("napoleon paris france", "should_return_empty")
    ]
    # Validate appropriate document ranking and zero scores for irrelevant queries
```

### 4.2 Integration Test Requirements

#### IT1: Real Corpus Testing
- **Corpus**: Use data/test/ RISC-V documents (6 documents, ~12MB)
- **Queries**: Test 20+ realistic RISC-V queries from specification domains
- **Validation**: Verify ranking quality and performance benchmarks

#### IT2: Epic 2 Configuration Testing
- **Config**: Test with config/advanced_test.yaml Epic 2 configuration
- **Integration**: Verify BM25 works within ModularUnifiedRetriever
- **Fusion**: Confirm scores integrate properly with vector and graph retrieval

#### IT3: Performance Benchmarking
- **Latency**: Measure search latency with realistic query workload
- **Memory**: Monitor memory usage during indexing and search
- **Throughput**: Test concurrent query handling capability

### 4.3 Quality Metrics & Acceptance Criteria

#### QM1: Functional Quality
- **Technical Term Preservation**: 100% of RISC-V terms preserved correctly
- **Stopword Filtering**: 0% false positives (no technical terms filtered)
- **Score Range**: 100% of output scores in [0,1] range
- **Error Handling**: Graceful failure for all invalid inputs

#### QM2: Performance Quality
- **Search Latency**: <10ms for 95th percentile (realistic RISC-V queries)
- **Indexing Speed**: >1000 documents/second for batch indexing
- **Memory Efficiency**: <500MB total memory for 10K document corpus
- **Throughput**: >100 queries/second sustained load

#### QM3: Integration Quality
- **ComponentFactory**: 100% compatibility with factory pattern
- **Configuration**: Support all Epic 2 BM25 configuration parameters
- **Logging**: Comprehensive debug information when enabled
- **Reliability**: 99.9% uptime under normal query load

## 5. Implementation Guidelines

### 5.1 Architecture Compliance
- **Pattern**: Direct Implementation (not adapter) - BM25 is internal algorithm
- **Dependencies**: rank_bm25 library, numpy for score processing
- **Interfaces**: Implement SparseRetriever base class
- **Error Handling**: Comprehensive validation with actionable error messages

### 5.2 Code Quality Standards
- **Type Hints**: Complete type annotations for all public methods
- **Documentation**: Comprehensive docstrings with examples
- **Testing**: Unit test coverage >95% for all public methods
- **Performance**: Profiling and optimization for production workloads

### 5.3 RISC-V Domain Considerations
- **Vocabulary**: Handle evolving RISC-V terminology and extension names
- **Standards**: Follow RISC-V International naming conventions
- **Extensibility**: Support for new instruction sets and extensions
- **Accuracy**: Precise technical term matching for specification queries

## 6. Test Cases for Validation

### 6.1 Core RISC-V Query Test Set
```python
RISCV_CORE_QUERIES = [
    # High-level architectural queries
    ("vector instruction set architecture", "vector extension documents"),
    ("base integer instruction set", "RV32I/RV64I specification"),
    ("privileged architecture specification", "privileged mode documents"),
    ("compressed instruction extension", "C-extension documents"),
    
    # Specific technical queries
    ("RV32I ADD instruction encoding", "base instruction encoding"),
    ("vector register file organization", "vector register specification"),
    ("machine mode privilege level", "privileged architecture"),
    ("CSR register access instructions", "control status register docs"),
    
    # Implementation queries
    ("vector intrinsic functions", "vector intrinsic specification"),
    ("debug specification interface", "debug module specification"),
    ("ABI calling convention", "application binary interface"),
    ("SBI system binary interface", "supervisor binary interface"),
    
    # Out-of-domain queries (should return empty)
    ("napoleon bonaparte france", "empty_results"),
    ("machine learning neural networks", "empty_results"),
    ("javascript web development", "empty_results"),
    ("database sql queries", "empty_results")
]
```

### 6.2 Technical Term Preservation Test Set
```python
TECHNICAL_TERMS_TEST = [
    # RISC-V specific terms
    "RISC-V", "RV32I", "RV64G", "RV128",
    
    # Extension names
    "Zicsr", "Zifencei", "Zam", "Ztso",
    
    # Instruction names
    "ADD", "SUB", "LW", "SW", "FENCE", "ECALL",
    
    # Register names
    "x0", "x1", "ra", "sp", "gp", "tp",
    
    # Hyphenated terms
    "floating-point", "out-of-order", "cache-coherent",
    
    # Alphanumeric codes
    "CSR0x300", "0x12345678", "F-ext", "V-ext"
]
```

## 7. Success Criteria

### 7.1 Functional Success
- ✅ All RISC-V core queries return appropriate documents
- ✅ Technical terms preserved through preprocessing pipeline
- ✅ Out-of-domain queries return empty results naturally
- ✅ Score normalization produces [0,1] range consistently

### 7.2 Performance Success
- ✅ Search latency <10ms for 95th percentile realistic queries
- ✅ Memory usage <500MB for realistic RISC-V corpus
- ✅ Integration with Epic 2 configuration seamless
- ✅ Zero regression in ModularUnifiedRetriever performance

### 7.3 Quality Success
- ✅ 100% test coverage for core functionality
- ✅ Comprehensive documentation with examples
- ✅ Production-ready error handling and logging
- ✅ Architectural compliance with direct implementation pattern

This specification defines the BM25 component as a **specialized lexical matching engine** for RISC-V technical documentation, focusing on domain-appropriate behavior rather than generic search optimization.