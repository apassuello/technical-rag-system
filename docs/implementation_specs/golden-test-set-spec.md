# Golden Test Set Generation Specification

**Purpose**: Define comprehensive test queries for RAG system evaluation  
**Format**: JSON structured test cases  
**Target**: 75-100 test cases covering all query types and edge cases  
**Location**: `tests/golden_test_set.json`

## 1. Test Case Structure

Each test case must follow this schema:

```json
{
  "test_id": "TC001",
  "category": "factual_simple",
  "query": "What is RISC-V?",
  "query_metadata": {
    "difficulty": "easy",
    "domain_specific": true,
    "expected_sources": ["riscv-spec.pdf", "riscv-base-instructions.pdf"],
    "key_terms": ["RISC-V", "instruction set", "architecture"]
  },
  "expected_behavior": {
    "should_answer": true,
    "min_documents": 3,
    "max_documents": 10,
    "min_confidence": 0.7,
    "max_confidence": 0.95,
    "must_contain_terms": ["instruction set", "open", "architecture"],
    "must_not_contain": ["ARM", "x86", "Intel"]
  },
  "validation_rules": {
    "semantic_relevance": 0.6,
    "answer_completeness": "high",
    "source_grounding": "required"
  },
  "notes": "Basic factual query that should return high-quality results"
}
```

## 2. Query Categories and Distribution

### 2.1 Technical Queries (40% - 30-40 queries)

**Simple Factual (10 queries)**
```json
{
  "test_id": "TC001",
  "category": "factual_simple", 
  "query": "What is RISC-V?",
  "expected_behavior": {
    "should_answer": true,
    "min_confidence": 0.8
  }
}
```

**Complex Technical (10 queries)**
```json
{
  "test_id": "TC011",
  "category": "technical_complex",
  "query": "How does RISC-V handle memory ordering compared to ARM's memory model?",
  "expected_behavior": {
    "should_answer": true,
    "min_confidence": 0.5,
    "max_confidence": 0.8
  }
}
```

**Implementation Details (10 queries)**
```json
{
  "test_id": "TC021",
  "category": "implementation_specific",
  "query": "What are the encoding details for RV32I ADD instruction?",
  "expected_behavior": {
    "should_answer": true,
    "must_contain_terms": ["opcode", "funct3", "rd", "rs1", "rs2"]
  }
}
```

### 2.2 Edge Cases (30% - 22-30 queries)

**Ambiguous Queries (8 queries)**
```json
{
  "test_id": "TC031",
  "category": "ambiguous",
  "query": "What about extensions?",
  "expected_behavior": {
    "should_answer": true,
    "min_confidence": 0.3,
    "max_confidence": 0.6,
    "notes": "Should attempt answer but with lower confidence"
  }
}
```

**Partial Match Queries (7 queries)**
```json
{
  "test_id": "TC041",
  "category": "partial_match",
  "query": "RISC-V quantum computing applications",
  "expected_behavior": {
    "should_answer": true,
    "max_confidence": 0.5,
    "notes": "RISC-V mentioned but quantum computing likely not in docs"
  }
}
```

**Multi-hop Queries (7 queries)**
```json
{
  "test_id": "TC051",
  "category": "multi_hop",
  "query": "What is the difference between the multiply instruction in RV32M and RV64M extensions?",
  "expected_behavior": {
    "should_answer": true,
    "min_documents": 4,
    "notes": "Requires information from multiple document sections"
  }
}
```

### 2.3 Out-of-Scope Queries (20% - 15-20 queries)

**Completely Irrelevant (10 queries)**
```json
{
  "test_id": "TC061",
  "category": "irrelevant",
  "query": "Where is Paris?",
  "expected_behavior": {
    "should_answer": false,
    "max_documents": 0,
    "max_confidence": 0.3,
    "expected_response_type": "refusal"
  }
}
```

**Domain Mismatch (5 queries)**
```json
{
  "test_id": "TC071",
  "category": "wrong_domain",
  "query": "What is the recipe for chocolate cake?",
  "expected_behavior": {
    "should_answer": false,
    "max_confidence": 0.2
  }
}
```

### 2.4 Stress Test Queries (10% - 7-10 queries)

**Adversarial (5 queries)**
```json
{
  "test_id": "TC081",
  "category": "adversarial",
  "query": "Tell me about RISC-V without using the words instruction, architecture, or processor",
  "expected_behavior": {
    "should_answer": true,
    "min_confidence": 0.4,
    "notes": "Tests robustness to unusual constraints"
  }
}
```

## 3. Query Generation Guidelines

### 3.1 Domain Coverage
Ensure queries cover all major RISC-V topics:
- ISA basics and philosophy
- Instruction formats and encoding
- Extensions (M, A, F, D, C, V)
- Privileged architecture
- Memory model
- Interrupts and exceptions
- Implementation considerations

### 3.2 Linguistic Variety
Include various query formulations:
- Questions: "What is...?", "How does...?", "Why does...?"
- Imperatives: "Explain...", "Describe...", "List..."
- Comparisons: "Difference between...", "Compare..."
- Hypotheticals: "What if...", "Could RISC-V..."

### 3.3 Difficulty Progression
```
Easy: Direct fact retrieval, single document sufficient
Medium: Requires synthesis from 2-3 documents
Hard: Requires inference, multiple document correlation
Expert: Requires deep technical understanding
```

## 4. Claude Code Generation Instructions

### 4.1 Initial Generation Prompt
```
"Generate a golden test set for my RISC-V RAG system following this specification:
- 75 test cases in the specified JSON format
- Cover all categories with proper distribution
- Include RISC-V specific technical queries
- Add edge cases I might not think of
- Ensure variety in query formulation
- Include both positive and negative test cases"
```

### 4.2 Refinement Prompts
```
"Review this test set and:
1. Add 10 more adversarial queries that test edge cases
2. Ensure confidence thresholds are realistic
3. Add queries that test stop word filtering effectiveness
4. Include queries that would have failed before our fixes"
```

### 4.3 Validation Prompt
```
"Analyze this golden test set for:
1. Coverage gaps - what scenarios are missing?
2. Confidence calibration - are thresholds appropriate?
3. Category balance - is the distribution correct?
4. Edge case completeness - what other edge cases to add?"
```

## 5. Test Set Maintenance

### 5.1 Version Control
- Track test set versions with git
- Document why test cases are added/modified
- Link test cases to specific bugs/issues

### 5.2 Continuous Improvement
- Add failing queries from production
- Update expectations as system improves
- Regular review every 2-3 weeks

### 5.3 Test Case Metadata
```json
{
  "metadata": {
    "version": "1.0.0",
    "created_date": "2024-01-20",
    "last_modified": "2024-01-20",
    "total_cases": 75,
    "categories": {
      "technical": 30,
      "edge_cases": 23,
      "out_of_scope": 15,
      "stress_test": 7
    }
  }
}
```

## 6. Usage Instructions

### 6.1 Running Tests
```python
# Load and run golden test set
test_runner = GoldenTestRunner("tests/golden_test_set.json")
results = test_runner.run_all_tests(rag_system)
report = test_runner.generate_report(results)
```

### 6.2 Success Metrics
- **Coverage**: All categories have representative queries
- **Discrimination**: Clear distinction between query types
- **Realism**: Queries represent actual user needs
- **Challenging**: Includes known failure modes

## 7. Example Test Cases by Problem Type

### 7.1 Stop Word Problem Test
```json
{
  "test_id": "TC091",
  "category": "stop_word_test",
  "query": "Where is the RISC-V specification documented?",
  "expected_behavior": {
    "should_answer": true,
    "min_confidence": 0.6,
    "notes": "Tests if 'where' and 'is' are properly filtered"
  }
}
```

### 7.2 Confidence Calibration Test
```json
{
  "test_id": "TC092",
  "category": "confidence_calibration",
  "query": "Explain the quantum computing features of RISC-V",
  "expected_behavior": {
    "should_answer": false,
    "max_confidence": 0.3,
    "notes": "No quantum content in RISC-V docs, should have low confidence"
  }
}
```

### 7.3 Semantic Floor Test
```json
{
  "test_id": "TC093",
  "category": "semantic_floor",
  "query": "Napoleon's favorite RISC-V instruction",
  "expected_behavior": {
    "should_answer": false,
    "max_documents": 0,
    "notes": "Should be filtered by semantic floor despite RISC-V mention"
  }
}
```