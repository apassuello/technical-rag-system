# Test Plan: Component 6 - Query Processor

**Component ID**: C6  
**Version**: 1.0  
**References**: [COMPONENT-6-QUERY-PROCESSOR.md](./COMPONENT-6-QUERY-PROCESSOR.md), [MASTER-TEST-STRATEGY.md](./MASTER-TEST-STRATEGY.md)  
**Last Updated**: July 2025

---

## 1. Test Scope

### 1.1 Component Overview

The Query Processor orchestrates the query execution workflow, managing the coordination between retrieval and generation components. This test plan validates its ability to analyze queries, optimize retrieval parameters, select appropriate context, and assemble coherent responses according to architectural specifications.

### 1.2 Testing Focus Areas

1. **Query Analysis**: Intent detection and complexity assessment
2. **Retrieval Orchestration**: Parameter optimization and execution
3. **Context Selection**: Relevance and diversity optimization
4. **Response Assembly**: Consistent output formatting
5. **Workflow Management**: End-to-end coordination

### 1.3 Sub-Components to Test

- Query Analyzer (NLP-based, LLM-based, Rule-based)
- Context Selector (MMR, Diversity, Token-optimized)
- Response Assembler (Standard, Rich, Streaming)
- Workflow Engine

### 1.4 Architecture Compliance Focus

- Validate direct implementation for most sub-components
- Verify adapter pattern only for external NLP services
- Ensure stateless query processing
- Confirm workflow orchestration patterns

---

## 2. Test Requirements Traceability

| Requirement | Test Cases | Priority |
|-------------|------------|----------|
| FR1: Analyze query intent and complexity | C6-FUNC-001 to C6-FUNC-005 | High |
| FR2: Execute retrieval with appropriate parameters | C6-FUNC-006 to C6-FUNC-010 | High |
| FR3: Select best context within token limits | C6-FUNC-011 to C6-FUNC-015 | High |
| FR4: Coordinate answer generation | C6-FUNC-016 to C6-FUNC-018 | High |
| FR5: Assemble responses with metadata | C6-FUNC-019 to C6-FUNC-022 | Medium |

---

## 3. Test Cases

### 3.1 Sub-Component Tests

#### C6-SUB-001: Query Analyzer Implementations
**Requirement**: Analyzer pattern validation  
**Priority**: High  
**Type**: Architecture  

**Test Steps**:
1. Test NLP-based analyzer (direct)
2. Verify LLM-based analyzer (adapter)
3. Test rule-based analyzer (direct)
4. Compare analyzer effectiveness
5. Validate interface consistency

**PASS Criteria**:
- Architecture:
  - NLP/Rule analyzers directly implemented
  - LLM analyzer uses adapter if external
  - Consistent QueryAnalysis interface
  - Pluggable analyzer selection
- Functional:
  - All analyzers produce valid output
  - Appropriate analyzer selected

**FAIL Criteria**:
- Pattern violations
- Inconsistent interfaces
- Analyzer selection errors
- Poor analysis quality

---

#### C6-SUB-002: Context Selector Strategies
**Requirement**: Selection algorithm validation  
**Priority**: High  
**Type**: Functional  

**Test Steps**:
1. Test MMR diversity selection
2. Validate diversity-based selection
3. Test token-optimized selection
4. Compare selection quality
5. Verify token limit compliance

**PASS Criteria**:
- Functional:
  - MMR reduces redundancy >30%
  - Diversity increases coverage
  - Token limits never exceeded
  - All strategies implement interface
- Quality:
  - Selected context relevant
  - Good topic coverage

**FAIL Criteria**:
- Redundant selections
- Token limit violations
- Poor relevance
- Interface violations

---

#### C6-SUB-003: Response Assembler Formats
**Requirement**: Output format consistency  
**Priority**: Medium  
**Type**: Functional  

**Test Steps**:
1. Test standard format assembler
2. Validate rich format assembler
3. Test streaming assembler
4. Verify format consistency
5. Check metadata inclusion

**PASS Criteria**:
- Functional:
  - Each format correctly structured
  - Metadata consistently included
  - Streaming works properly
  - Format switching seamless
- Quality:
  - Clean, readable output
  - All required fields present

**FAIL Criteria**:
- Format inconsistencies
- Missing metadata
- Streaming failures
- Switching breaks output

---

#### C6-SUB-004: Workflow Engine Orchestration
**Requirement**: Workflow coordination  
**Priority**: High  
**Type**: Integration  

**Test Steps**:
1. Test sequential workflow
2. Validate parallel operations
3. Test error handling flows
4. Verify state management
5. Check timing coordination

**PASS Criteria**:
- Functional:
  - Workflows execute correctly
  - Parallel ops where possible
  - Errors handled gracefully
  - Stateless operation
- Performance:
  - Minimal orchestration overhead
  - Efficient parallelization

**FAIL Criteria**:
- Workflow failures
- State leakage
- Poor error handling
- Performance overhead

---

### 3.2 Functional Tests - Query Analysis

#### C6-FUNC-001: Basic Query Analysis
**Requirement**: FR1  
**Priority**: High  
**Type**: Functional  

**Preconditions**:
- Query analyzer initialized
- Various query types prepared

**Test Steps**:
1. Analyze simple factual query
2. Extract intent classification
3. Determine complexity level
4. Identify key entities
5. Check analysis metadata

**PASS Criteria**:
- Functional:
  - Intent classification accuracy >90%
  - Complexity = "simple" for factual queries
  - Entity extraction precision >85%
  - Complete metadata object
- Performance:
  - Analysis time <50ms
  - Consistent timing

**FAIL Criteria**:
- Intent misclassification
- Wrong complexity assessment
- Poor entity extraction
- Analysis time >50ms

---

#### C6-FUNC-002: Complex Query Analysis
**Requirement**: FR1  
**Priority**: High  
**Type**: Functional  

**Preconditions**:
- Multi-part technical queries
- NLP analyzer configured

**Test Steps**:
1. Analyze compound query
2. Identify multiple intents
3. Assess complexity as "complex"
4. Extract technical terms
5. Determine retrieval strategy

**PASS Criteria**:
- Functional:
  - All query parts identified
  - Complexity = "complex" correct
  - 100% technical term preservation
  - Valid strategy recommendations
  - Rich analysis metadata
- Quality:
  - Actionable insights provided
  - Accurate decomposition

**FAIL Criteria**:
- Missed query components
- Incorrect complexity
- Lost technical terms
- Invalid strategies

---

#### C6-FUNC-003: Entity Extraction
**Requirement**: FR1  
**Priority**: Medium  
**Type**: Functional  

**Preconditions**:
- Queries with named entities
- Entity recognition enabled

**Test Steps**:
1. Process query with product names
2. Process query with technical specs
3. Extract version numbers
4. Identify acronyms
5. Validate extraction accuracy

**PASS Criteria**:
- Functional:
  - Product name extraction >95%
  - Technical spec extraction >90%
  - Version number extraction 100%
  - Acronym recognition >85%
- Quality:
  - No false positives
  - Context preserved

**FAIL Criteria**:
- Missing key entities
- High false positive rate
- Version extraction errors
- Poor acronym detection

---

### 3.3 Functional Tests - Retrieval Orchestration

#### C6-FUNC-006: Dynamic k Selection
**Requirement**: FR2  
**Priority**: High  
**Type**: Functional  

**Preconditions**:
- Query complexity analyzed
- Retriever available

**Test Steps**:
1. Simple query → small k
2. Complex query → large k
3. Verify k adjustment logic
4. Execute retrieval
5. Check result count

**PASS Criteria**:
- Functional:
  - k dynamically adjusted
  - Simple queries: k ∈ [3,5]
  - Complex queries: k ∈ [10,15]
  - Retrieval completes successfully
  - Result count = k (or less)
- Logic:
  - Clear adjustment rules
  - Consistent behavior

**FAIL Criteria**:
- Fixed k value
- Out of range k
- Retrieval failures
- Wrong result count

---

#### C6-FUNC-007: Retrieval Parameter Optimization
**Requirement**: FR2  
**Priority**: Medium  
**Type**: Functional  

**Preconditions**:
- Various query types
- Parameter options available

**Test Steps**:
1. Keyword query → sparse weight boost
2. Semantic query → dense weight boost
3. Technical query → hybrid balanced
4. Verify weight adjustments
5. Check retrieval quality

**PASS Criteria**:
- Functional:
  - Query-dependent weight adjustment
  - Keyword queries: sparse weight >0.5
  - Semantic queries: dense weight >0.7
  - Technical queries: balanced (±0.1)
  - Overall relevance improvement >10%
- Logic:
  - Clear adjustment rules
  - Predictable behavior

**FAIL Criteria**:
- Fixed weights used
- Inappropriate weight selection
- No relevance improvement
- Unpredictable adjustments

---

### 3.3 Functional Tests - Context Selection

#### C6-FUNC-011: MMR Context Selection
**Requirement**: FR3  
**Priority**: High  
**Type**: Functional  

**Preconditions**:
- Retrieved documents available
- MMR selector configured

**Test Steps**:
1. Retrieve 10 documents
2. Apply MMR selection for 5
3. Verify diversity score
4. Check relevance preservation
5. Validate token limits

**PASS Criteria**:
- Functional:
  - Exactly 5 documents selected
  - Diversity score >0.8
  - Relevance score >0.85
  - Token count <max_tokens
  - Selection reasoning available
- Quality:
  - MMR algorithm correctly applied
  - Good diversity/relevance tradeoff

**FAIL Criteria**:
- Wrong document count
- Low diversity score
- Poor relevance
- Token limit exceeded

---

#### C6-FUNC-012: Token Limit Management
**Requirement**: FR3  
**Priority**: High  
**Type**: Functional  

**Preconditions**:
- Documents of various lengths
- Token counter configured

**Test Steps**:
1. Set max tokens = 2048
2. Select from long documents
3. Verify token counting
4. Check truncation logic
5. Validate final count

**Expected Results**:
- Tokens accurately counted
- Selection within limit
- Smart truncation applied
- Most relevant retained
- Exactly ≤2048 tokens

---

#### C6-FUNC-013: Context Ordering
**Requirement**: FR3  
**Priority**: Medium  
**Type**: Functional  

**Preconditions**:
- Selected documents
- Ordering strategy configured

**Test Steps**:
1. Order by relevance
2. Order by diversity
3. Order by recency
4. Test custom ordering
5. Verify impact on generation

**Expected Results**:
- Ordering strategies work
- Most relevant first
- Diversity considered
- Metadata preserved
- Generation improved

---

### 3.4 Functional Tests - Response Assembly

#### C6-FUNC-019: Standard Response Assembly
**Requirement**: FR5  
**Priority**: Medium  
**Type**: Functional  

**Preconditions**:
- Answer from generator
- Retrieved documents
- Standard assembler

**Test Steps**:
1. Receive raw answer
2. Add source citations
3. Include confidence score
4. Add query metadata
5. Format final response

**Expected Results**:
- Complete response object
- Citations formatted
- Confidence included
- Metadata attached
- Consistent structure

---

#### C6-FUNC-020: Rich Response Assembly
**Requirement**: FR5  
**Priority**: Medium  
**Type**: Functional  

**Preconditions**:
- Rich assembler configured
- Additional metadata available

**Test Steps**:
1. Include retrieval scores
2. Add timing information
3. Include strategy used
4. Format with sections
5. Add debug information

**Expected Results**:
- Enhanced response
- All metrics included
- Clear sections
- Debug data available
- Professional format

---

### 3.5 Performance Tests

#### C6-PERF-001: Query Analysis Overhead
**Requirement**: QR - <50ms  
**Priority**: High  
**Type**: Performance  

**Test Steps**:
1. Measure analysis time
2. Test various complexities
3. Profile NLP operations
4. Check caching impact
5. Calculate percentiles

**Expected Results**:
- Average <50ms
- p95 <100ms
- Caching effective
- No memory leaks
- Linear complexity

---

#### C6-PERF-002: Context Selection Performance
**Requirement**: QR - <100ms  
**Priority**: High  
**Type**: Performance  

**Test Steps**:
1. Time selection algorithms
2. Vary document counts
3. Test different strategies
4. Measure memory usage
5. Profile bottlenecks

**Expected Results**:
- Selection <100ms
- Scales with doc count
- MMR efficient
- Memory stable
- No quadratic behavior

---

#### C6-PERF-003: End-to-End Overhead
**Requirement**: QR - <200ms total  
**Priority**: High  
**Type**: Performance  

**Test Steps**:
1. Mock retriever/generator
2. Measure processor overhead
3. Test complete workflow
4. Identify bottlenecks
5. Optimize critical path

**Expected Results**:
- Total overhead <200ms
- Analysis: ~50ms
- Selection: ~100ms
- Assembly: ~50ms
- No hidden delays

---

### 3.6 Workflow Integration Tests

#### C6-WORK-001: Complete Query Flow
**Requirement**: Workflow orchestration  
**Priority**: High  
**Type**: Integration  

**Test Steps**:
1. Submit user query
2. Verify analysis executed
3. Check retrieval called
4. Confirm selection applied
5. Validate generation invoked

**Expected Results**:
- All steps executed
- Correct order maintained
- Data flows properly
- No steps skipped
- Results assembled

---

#### C6-WORK-002: Error Propagation
**Requirement**: Error handling  
**Priority**: High  
**Type**: Negative  

**Test Steps**:
1. Simulate retrieval failure
2. Verify error caught
3. Check fallback attempted
4. Validate error response
5. Ensure cleanup done

**Expected Results**:
- Errors handled gracefully
- Fallbacks work
- Clear error messages
- Partial results possible
- System stable

---

## 4. Test Data Requirements

### 4.1 Query Types

**Analysis Testing**:
- Simple factual queries
- Complex technical queries
- Multi-intent queries
- Ambiguous queries
- Edge cases

**Performance Testing**:
- 1000 diverse queries
- Various complexity levels
- Different domains
- Stress test queries

### 4.2 Context Documents

**Selection Testing**:
- Redundant documents
- Diverse topics
- Various lengths
- Quality variations
- Edge cases

---

## 5. Test Environment Setup

### 5.1 Component Mocking

**For Isolation**:
- Mock Retriever
- Mock Answer Generator
- Controllable responses
- Error injection

### 5.2 Analysis Tools

- spaCy models loaded
- NLP pipelines ready
- Performance profilers
- Memory monitors

---

## 6. Risk-Based Test Prioritization

### 6.1 High Priority Tests

1. Query analysis accuracy (determines quality)
2. Context selection logic (affects answers)
3. Workflow coordination (core function)
4. Error handling (system stability)

### 6.2 Medium Priority Tests

1. Performance optimization
2. Advanced analysis features
3. Response formatting
4. Metadata handling

### 6.3 Low Priority Tests

1. Alternative analyzers
2. Custom strategies
3. Debug features
4. Edge cases

---

## 7. Sub-Component Integration Tests

### 7.1 Analyzer + Workflow Engine

- Query analysis drives workflow
- Complexity affects parameters
- Entity extraction used
- Strategy selection works

### 7.2 Context Selector + Token Counter

- Accurate token counting
- Selection respects limits
- Truncation logic correct
- Buffer management works

### 7.3 Workflow + Response Assembler

- All data available
- Metadata preserved
- Timing recorded
- Format consistent

---

## 8. Exit Criteria

### 8.1 Functional Coverage

- All sub-components tested
- Workflow paths verified
- Error scenarios covered
- Integration validated

### 8.2 Performance Criteria

- Analysis <50ms
- Selection <100ms
- Total overhead <200ms
- Memory usage stable

### 8.3 Quality Gates

- Query analysis accuracy >95%
- Context selection optimal
- Zero workflow failures
- All strategies functional