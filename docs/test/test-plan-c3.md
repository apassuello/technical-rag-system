# Test Plan: Component 3 - Embedder

**Component ID**: C3  
**Version**: 1.0  
**References**: [COMPONENT-3-EMBEDDER.md](./COMPONENT-3-EMBEDDER.md), [MASTER-TEST-STRATEGY.md](./MASTER-TEST-STRATEGY.md)  
**Last Updated**: July 2025

---

## 1. Test Scope

### 1.1 Component Overview

The Embedder transforms text into vector representations for semantic search, utilizing both local models and external APIs. This test plan validates its ability to generate consistent embeddings, optimize batch processing, and maintain cache efficiency according to specifications.

### 1.2 Testing Focus Areas

1. **Embedding Generation**: Quality and consistency of vectors
2. **Batch Processing**: Optimization and GPU utilization
3. **Caching Strategy**: Multi-level cache effectiveness
4. **Model Management**: Local vs API-based models
5. **Hardware Optimization**: GPU/MPS/CPU adaptation

### 1.3 Sub-Components to Test

- Embedding Model (SentenceTransformer direct, OpenAI adapter)
- Batch Processor (Dynamic, Streaming, Fixed-size)
- Embedding Cache (In-memory direct, Redis adapter, Disk adapter)
- Hardware Optimizer

### 1.4 Architecture Compliance Focus

- Validate mixed adapter pattern (local models direct, APIs use adapters)
- Verify hardware optimization strategies
- Ensure multi-level caching hierarchy
- Confirm stateless embedding generation

---

## 2. Test Requirements Traceability

| Requirement | Test Cases | Priority |
|-------------|------------|----------|
| FR1: Generate embeddings from text | C3-FUNC-001 to C3-FUNC-005 | High |
| FR2: Batch process multiple texts efficiently | C3-FUNC-006 to C3-FUNC-010 | High |
| FR3: Cache and retrieve computed embeddings | C3-FUNC-011 to C3-FUNC-015 | High |
| FR4: Support different embedding models | C3-FUNC-016 to C3-FUNC-019 | Medium |
| FR5: Handle various text lengths appropriately | C3-FUNC-020 to C3-FUNC-022 | Medium |

---

## 3. Test Cases

### 3.1 Sub-Component Tests

#### C3-SUB-001: Embedding Model Architecture
**Requirement**: Mixed implementation pattern  
**Priority**: High  
**Type**: Architecture  

**Test Steps**:
1. Verify SentenceTransformer direct implementation
2. Test OpenAI adapter implementation
3. Validate adapter interface consistency
4. Check model loading strategies
5. Test model switching capability

**PASS Criteria**:
- Architecture:
  - Local models use direct implementation
  - API models use adapter pattern
  - Consistent embedding interface
  - Clean model abstraction
- Functional:
  - Both model types produce embeddings
  - Dimension consistency maintained

**FAIL Criteria**:
- Adapter pattern misused for local models
- Direct API calls without adapter
- Inconsistent interfaces
- Model switching failures

---

#### C3-SUB-002: Batch Processor Strategies
**Requirement**: Batch optimization patterns  
**Priority**: High  
**Type**: Performance/Architecture  

**Test Steps**:
1. Test dynamic batch sizing
2. Validate streaming batch processor
3. Test fixed-size batching
4. Compare strategy performance
5. Verify memory management

**PASS Criteria**:
- Functional:
  - All strategies implement base interface
  - Dynamic sizing adapts to memory
  - Streaming handles large datasets
  - Fixed-size maintains consistency
- Performance:
  - 80x+ speedup with batching
  - Memory usage controlled

**FAIL Criteria**:
- Strategy interface violations
- Memory overflow with batching
- No performance improvement
- Incorrect batch processing

---

#### C3-SUB-003: Multi-Level Cache Hierarchy
**Requirement**: Cache architecture validation  
**Priority**: High  
**Type**: Architecture  

**Test Steps**:
1. Test in-memory cache (direct)
2. Test Redis cache adapter
3. Test disk cache adapter
4. Verify cache hierarchy flow
5. Test cache invalidation

**PASS Criteria**:
- Architecture:
  - Memory cache uses direct implementation
  - Redis/Disk use adapter pattern
  - Proper fallback hierarchy
  - Cache consistency maintained
- Performance:
  - Memory cache hit <1ms
  - Redis cache hit <10ms
  - Disk cache hit <50ms

**FAIL Criteria**:
- Adapter pattern misuse
- Cache hierarchy broken
- Inconsistent cache data
- Performance targets missed

---

#### C3-SUB-004: Hardware Optimizer
**Requirement**: Hardware adaptation  
**Priority**: Medium  
**Type**: Performance  

**Test Steps**:
1. Test GPU optimization
2. Test MPS (Apple Silicon) optimization
3. Test CPU fallback
4. Verify automatic hardware detection
5. Test optimization switching

**PASS Criteria**:
- Functional:
  - Correct hardware detected
  - Appropriate optimizations applied
  - Graceful fallback to CPU
  - No crashes on hardware switch
- Performance:
  - GPU utilization >80%
  - MPS acceleration confirmed
  - CPU fallback functional

**FAIL Criteria**:
- Hardware detection failures
- No optimization applied
- Crashes on hardware change
- Poor hardware utilization

---

### 3.2 Functional Tests - Embedding Generation

#### C3-FUNC-001: Basic Embedding Generation
**Requirement**: FR1  
**Priority**: High  
**Type**: Functional  

**Preconditions**:
- SentenceTransformer model loaded
- Valid text input prepared

**Test Steps**:
1. Generate embedding for single text
2. Verify vector dimensions (384)
3. Check vector normalization
4. Validate numeric range
5. Test embedding determinism

**PASS Criteria**:
- Functional:
  - Vector dimension exactly 384
  - Vectors normalized when configured
  - All values in range [-1, 1]
  - Deterministic results (same input → same output)
- Quality:
  - No NaN or Inf values
  - Meaningful embeddings generated

**FAIL Criteria**:
- Incorrect dimensions
- Non-normalized vectors when required
- Values outside expected range
- Non-deterministic results

---

#### C3-FUNC-002: Empty/Invalid Input Handling
**Requirement**: FR1  
**Priority**: High  
**Type**: Functional/Negative  

**Preconditions**:
- Model initialized
- Various invalid inputs prepared

**Test Steps**:
1. Process empty string
2. Process None/null input
3. Process extremely long text
4. Process special characters only
5. Verify appropriate handling

**PASS Criteria**:
- Functional:
  - Empty string returns zero or special embedding
  - None input raises ValueError
  - Text >512 tokens truncated correctly
  - Special characters processed without error
- Resilience:
  - No crashes on edge inputs
  - Clear error messages

**FAIL Criteria**:
- Crashes on empty input
- Silent failures on None
- Incorrect truncation
- Special character errors

---

#### C3-FUNC-003: Model Consistency
**Requirement**: FR1  
**Priority**: High  
**Type**: Functional  

**Preconditions**:
- Multiple text samples
- Model loaded

**Test Steps**:
1. Generate embeddings for similar texts
2. Calculate cosine similarity
3. Generate embeddings for different texts
4. Compare similarity scores
5. Verify semantic relationships preserved

**PASS Criteria**:
- Quality:
  - Similar text similarity >0.8
  - Different text similarity <0.5
  - Semantic relationships preserved
  - Consistency across runs
- Functional:
  - Valid cosine similarity values [-1, 1]
  - No embedding drift over time

**FAIL Criteria**:
- Poor semantic separation
- Inconsistent similarities
- Invalid similarity values
- Embedding quality degradation

---

### 3.3 Functional Tests - Batch Processing

#### C3-FUNC-006: Dynamic Batch Processing
**Requirement**: FR2  
**Priority**: High  
**Type**: Functional  

**Preconditions**:
- GPU/MPS available
- Large text collection prepared

**Test Steps**:
1. Process texts with dynamic batcher
2. Monitor batch size adjustments
3. Verify memory usage optimization
4. Check throughput improvement
5. Validate result correctness

**PASS Criteria**:
- Performance:
  - Batch size dynamically adjusted
  - 80x+ speedup achieved
  - Memory usage stays within limits
  - No out-of-memory errors
- Functional:
  - All embeddings identical to single processing
  - Batch results in correct order

**FAIL Criteria**:
- Fixed batch sizes only
- Speedup <80x
- Memory overflow
- Incorrect embeddings

---

#### C3-FUNC-007: Batch Size Optimization
**Requirement**: FR2  
**Priority**: Medium  
**Type**: Functional  

**Preconditions**:
- Various text lengths
- Performance monitoring enabled

**Test Steps**:
1. Test with uniform text lengths
2. Test with mixed text lengths
3. Measure optimal batch sizes
4. Verify automatic adjustment
5. Check edge cases (1 text, 1000 texts)

**PASS Criteria**:
- Functional:
  - Optimal batch size automatically found
  - Mixed lengths handled without errors
  - Graceful degradation at boundaries
  - Accurate metrics collection
- Performance:
  - Batch efficiency >90%
  - No performance cliff

**FAIL Criteria**:
- Fixed batch sizes only
- Errors with mixed lengths
- Sudden performance drops
- Missing or incorrect metrics

---

### 3.3 Functional Tests - Caching

#### C3-FUNC-011: In-Memory Cache Operations
**Requirement**: FR3  
**Priority**: High  
**Type**: Functional  

**Preconditions**:
- In-memory cache configured
- Test texts prepared

**Test Steps**:
1. Generate embedding (cache miss)
2. Retrieve same embedding (cache hit)
3. Verify cache hit rate tracking
4. Test cache eviction (LRU)
5. Validate cache invalidation

**PASS Criteria**:
- Functional:
  - Cache miss triggers computation
  - Cache hit returns identical embedding
  - Hit rate tracking accurate to 0.1%
  - LRU eviction follows policy
  - Invalidation immediate and complete
- Performance:
  - Cache hit <1ms
  - 100x speedup on hits

**FAIL Criteria**:
- Cache not populated
- Different values on cache hit
- Incorrect hit rate tracking
- Eviction policy violations

---

#### C3-FUNC-012: Redis Cache Adapter
**Requirement**: FR3  
**Priority**: High  
**Type**: Functional  

**Preconditions**:
- Redis instance running
- Redis adapter configured

**Test Steps**:
1. Store embeddings in Redis
2. Retrieve across sessions
3. Test TTL functionality
4. Verify serialization correctness
5. Check distributed access

**Expected Results**:
- Embeddings persist in Redis
- Correct deserialization
- TTL respected
- Multiple clients can access
- No data corruption

---

### 3.4 Performance Tests

#### C3-PERF-001: Embedding Throughput
**Requirement**: QR - >2,500 chars/second  
**Priority**: High  
**Type**: Performance  

**Test Steps**:
1. Prepare texts of various lengths
2. Measure single embedding time
3. Measure batch embedding time
4. Calculate throughput
5. Test with different hardware

**PASS Criteria**:
- Performance:
  - Single embedding: >2,500 chars/second
  - Batch processing: >200,000 chars/second
  - GPU acceleration confirmed
  - Linear scaling to optimal batch
- Quality:
  - Consistent throughput
  - No degradation over time

**FAIL Criteria**:
- Below throughput targets
- No GPU acceleration
- Non-linear scaling
- Performance degradation

---

#### C3-PERF-002: Cache Performance Impact
**Requirement**: QR - >90% cache hit rate  
**Priority**: High  
**Type**: Performance  

**Test Steps**:
1. Process document corpus
2. Reprocess same corpus
3. Measure cache hit rate
4. Compare timing with/without cache
5. Monitor memory usage

**PASS Criteria**:
- Performance:
  - Cache hit rate >90%
  - Speedup >100x on hits
  - Memory usage <1GB for 100K embeddings
  - Key generation <1ms
- Functional:
  - Accurate hit tracking
  - No false cache hits

**FAIL Criteria**:
- Hit rate <90%
- Insufficient speedup
- Excessive memory usage
- Slow key generation

---

### 3.5 Hardware Optimization Tests

#### C3-HW-001: GPU/MPS Acceleration
**Requirement**: Hardware optimization  
**Priority**: High  
**Type**: Functional  

**Preconditions**:
- System with GPU/MPS
- CPU-only fallback available

**Test Steps**:
1. Force GPU/MPS mode
2. Generate embeddings
3. Force CPU mode
4. Compare performance
5. Test automatic detection

**Expected Results**:
- GPU/MPS significantly faster
- Correct results both modes
- Automatic detection works
- Graceful fallback on failure

---

#### C3-HW-002: Memory Management
**Requirement**: Hardware optimization  
**Priority**: Medium  
**Type**: Functional  

**Test Steps**:
1. Monitor GPU memory usage
2. Process increasing batch sizes
3. Detect OOM threshold
4. Verify graceful handling
5. Test memory cleanup

**Expected Results**:
- Memory usage predictable
- OOM prevented proactively
- Batch size reduced before OOM
- Memory properly released

---

### 3.6 Model Adapter Tests

#### C3-ADAPT-001: OpenAI Adapter Validation
**Requirement**: Architecture - Adapter pattern  
**Priority**: High  
**Type**: Compliance  

**Test Steps**:
1. Configure OpenAI adapter
2. Generate embeddings via API
3. Compare with local model format
4. Test error handling
5. Verify cost tracking

**Expected Results**:
- Same interface as local model
- API calls properly formatted
- Errors mapped correctly
- Usage tracked for costs
- Results in standard format

---

## 4. Test Data Requirements

### 4.1 Text Samples

**Basic Test Set**:
- Single words
- Short sentences
- Paragraphs
- Technical documentation
- Multi-language samples
- Special characters

**Performance Test Set**:
- 10K diverse texts
- Various length distributions
- Repeated texts (cache testing)
- Domain-specific corpus

### 4.2 Edge Cases

- Empty strings
- Maximum length texts
- Unicode and emojis
- Malformed text
- Binary data

---

## 5. Test Environment Setup

### 5.1 Hardware Configurations

**GPU Testing**:
- NVIDIA GPU with CUDA
- Apple Silicon with MPS
- Sufficient GPU memory

**CPU Testing**:
- Multi-core CPU
- Memory constraints
- No GPU available

### 5.2 External Services

- Redis instance for cache testing
- Mock OpenAI API endpoint
- Network latency simulation

---

## 6. Risk-Based Test Prioritization

### 6.1 High Priority Tests

1. Basic embedding generation (core functionality)
2. Batch processing efficiency (performance critical)
3. Cache operations (major optimization)
4. Hardware detection (deployment variability)

### 6.2 Medium Priority Tests

1. Multiple model support
2. Edge case handling
3. Cache adapter variations
4. Memory optimization

### 6.3 Low Priority Tests

1. Exotic text formats
2. Extreme batch sizes
3. Cache persistence edge cases

---

## 7. Sub-Component Integration Tests

### 7.1 Model + Batch Processor

- Verify batch processor works with all models
- Test dynamic sizing per model
- Validate memory estimation accuracy
- Check error propagation

### 7.2 Batch Processor + Cache

- Ensure batch results cached properly
- Test partial cache hits in batches
- Verify cache lookup optimization
- Check batch cache invalidation

### 7.3 Cache Hierarchy

- Test memory → Redis → disk flow
- Verify cache promotion/demotion
- Test distributed cache coherence
- Validate TTL propagation

---

## 8. Exit Criteria

### 8.1 Functional Coverage

- All embedding models tested
- Batch processing verified
- Cache layers validated
- Hardware paths tested

### 8.2 Performance Criteria

- Throughput targets achieved
- Cache hit rate >90%
- Batch speedup verified
- Memory usage optimized

### 8.3 Quality Gates

- Zero embedding corruption
- Consistent dimensions
- No memory leaks
- All adapters functional