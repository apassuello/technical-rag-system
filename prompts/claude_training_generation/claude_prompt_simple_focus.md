# Claude Training Data Generation Prompt - Simple Complexity Focus


**🎯 Current Focus**: RISC-V Architecture and Development

**Instructions**: If using a specific topic focus, ensure 60-70% of queries relate to that topic, with 30-40% general computing questions for variety.

## System Context

You are an expert in query complexity analysis and machine learning data generation. You will generate high-quality training data for a multi-view ML system that analyzes query complexity across 5 orthogonal dimensions:

1. **Technical Complexity**: Domain-specific terminology, jargon, technical depth
2. **Linguistic Complexity**: Sentence structure, vocabulary, readability  
3. **Task Complexity**: Cognitive load based on Bloom's taxonomy (Knowledge, Comprehension, Application, Analysis, Synthesis, Evaluation)
4. **Semantic Complexity**: Conceptual relationships, abstraction level, implicit knowledge
5. **Computational Complexity**: Algorithm mentions, implementation difficulty, optimization aspects

Your task is to generate **25 training samples focused on SIMPLE complexity** with realistic queries and detailed complexity assessments across all 5 views.

## 🎯 **TOPIC FOCUS FOR THIS BATCH**

**Primary Topic**: RISC-V Architecture and Development

Generate queries related to:
- **RISC-V Basics**: ISA fundamentals, instruction sets, registers
- **RISC-V Development**: Toolchains, compilers, assembly programming  
- **RISC-V Hardware**: Processors, cores, implementations
- **RISC-V Software**: Operating systems, libraries, applications
- **RISC-V Ecosystem**: Tools, simulators, development boards

**Important**: Ensure all RISC-V queries are appropriate for SIMPLE complexity level - focus on basic concepts, introductory questions, and fundamental understanding.

## Critical Requirements

1. **Natural Language**: All queries must sound like genuine user questions - grammatically correct, conversational, and realistic
2. **Score Calibration**: Maintain consistent scoring within the simple range with some boundary samples
3. **Feature Accuracy**: All numerical features must be derivable from the query text
4. **View Correlation**: Views should correlate (0.6-0.9) but not be identical
5. **Detailed Reasoning**: Provide clear explanations for each score

## Target Distribution for This Batch

Generate exactly 25 samples with this distribution:
- **20 samples**: Clearly simple (0.10-0.25 overall complexity)
- **5 samples**: Simple-medium boundary (0.26-0.35 overall complexity)

## Simple Query Characteristics

### Clear Simple (0.10-0.25)
- **Query Length**: 3-10 words typically
- **Vocabulary**: Common, everyday terms
- **Technical Terms**: 0-2 basic technical terms
- **Task Type**: Direct how-to, basic definitions, simple lookups
- **Cognitive Level**: Bloom's 1-2 (Knowledge, Comprehension)
- **Examples**: "How do I create a Python list?", "What is an API?", "How to install npm?"

### Simple-Medium Boundary (0.26-0.35)
- **Query Length**: 8-15 words
- **Vocabulary**: Mix of common and some technical terms
- **Technical Terms**: 2-3 technical terms
- **Task Type**: Basic comparisons, simple troubleshooting
- **Cognitive Level**: Bloom's 2-3 (Comprehension, Application)
- **Examples**: "What's the difference between let and const in JavaScript?", "How do I fix a git merge conflict?"

## JSON Structure for Each Sample

**CRITICAL: Use this EXACT structure to match existing training infrastructure:**

```json
{
  "query_text": "Natural, grammatically correct user question",
  "expected_complexity_score": 0.15,
  "expected_complexity_level": "simple",
  "view_scores": {
    "technical": 0.18,
    "linguistic": 0.12,
    "task": 0.14,
    "semantic": 0.13,
    "computational": 0.17
  },
  "confidence": 0.91,
  "metadata": {
    "domain": "technical",
    "query_type": "definition", 
    "generation_timestamp": "2025-08-07T20:00:00Z",
    "base_score": 0.15,
    "template_used": "none - natural generation"
  }
}
```

**IMPORTANT**: 
- `view_scores` contains ONLY simple float values (0.0-1.0), not complex objects
- Each view name must be exactly: "technical", "linguistic", "task", "semantic", "computational"
- All scores should be in the simple range: 0.10-0.35 for expected_complexity_score
- View scores can vary slightly but should correlate with expected score

## Scoring Guidelines for Simple Complexity

### View Score Ranges for Simple Queries:
- **Technical (0.10-0.35)**: Basic programming concepts, fundamental tools, minimal jargon
- **Linguistic (0.05-0.30)**: Simple sentence structure, common vocabulary, direct questions
- **Task (0.10-0.35)**: Bloom's Level 1-2 (Knowledge, Comprehension), minimal steps
- **Semantic (0.10-0.35)**: Concrete concepts, minimal abstraction, direct relationships  
- **Computational (0.05-0.35)**: Basic operations, no algorithms, simple data structures

### How to Score Each View:
1. **Technical**: Count technical terms, assess domain specificity, evaluate concept depth
2. **Linguistic**: Analyze sentence length, vocabulary complexity, syntactic structure
3. **Task**: Identify Bloom's level, assess cognitive load, count solution steps
4. **Semantic**: Evaluate abstraction level, concept relationships, context dependency
5. **Computational**: Consider algorithms mentioned, implementation difficulty, optimization needs

**Key Principle**: All view scores should correlate (0.6-0.9 correlation) and average to approximately the expected_complexity_score.

## Example Samples for Calibration

### Example 1: Clearly Simple (Score: 0.15)
```json
{
  "query_text": "How do I create a list in Python?",
  "expected_complexity_score": 0.15,
  "expected_complexity_level": "simple",
  "view_scores": {
    "technical": 0.18,
    "linguistic": 0.12,
    "task": 0.14,
    "semantic": 0.13,
    "computational": 0.17
  },
  "confidence": 0.91,
  "metadata": {
    "domain": "technical",
    "query_type": "how-to",
    "generation_timestamp": "2025-08-07T20:00:00Z",
    "base_score": 0.15,
    "template_used": "none - natural generation"
  }
}
```

**Analysis**: Basic Python data structure question. Technical (0.18) - mentions 'list' and 'Python' as fundamental concepts. Linguistic (0.12) - very simple sentence. Task (0.14) - Bloom's Level 1 knowledge recall. Semantic (0.13) - concrete concept. Computational (0.17) - basic data structure operation.

### Example 2: Simple-Medium Boundary (Score: 0.32)
```json
{
  "query_text": "What's the difference between let and const in JavaScript?",
  "expected_complexity_score": 0.32,
  "expected_complexity_level": "simple",
  "view_scores": {
    "technical": 0.35,
    "linguistic": 0.28,
    "task": 0.33,
    "semantic": 0.31,
    "computational": 0.34
  },
  "confidence": 0.88,
  "metadata": {
    "domain": "technical",
    "query_type": "comparison",
    "generation_timestamp": "2025-08-07T20:00:00Z",
    "base_score": 0.32,
    "template_used": "none - natural generation"
  }
}
```

**Analysis**: JavaScript variable declaration comparison. Technical (0.35) - requires understanding scoping rules. Linguistic (0.28) - comparison structure, straightforward vocabulary. Task (0.33) - Bloom's Level 2 comprehension, comparing concepts. Semantic (0.31) - relationship between related concepts. Computational (0.34) - variable scoping implications.

## Domain and Query Type Distribution

Ensure variety across the 25 samples:

### Domains (distribute across samples):
- **Technical** (15 samples): RISC-V programming, toolchains, assembly
- **Academic** (7 samples): RISC-V architecture theory, ISA concepts  
- **General** (3 samples): RISC-V ecosystem, getting started topics

### Query Types (distribute across samples):
- **definition** (10 samples): "What is RISC-V?", "What does X instruction do?"
- **how-to** (8 samples): "How to compile for RISC-V?", "How to use X tool?"
- **comparison** (4 samples): "RISC-V vs ARM", "Difference between RV32 and RV64"
- **troubleshooting** (3 samples): "Why won't my RISC-V code compile?", basic debugging

### RISC-V Topic Areas for Simple Queries:
- Basic ISA concepts (registers, instructions, addressing)
- Getting started with RISC-V development
- Simple toolchain usage (GCC, binutils)
- Basic assembly programming
- RISC-V vs other architectures (simple comparisons)
- Development board basics
- Simulator/emulator introductions

## Validation Checklist

Before outputting each sample, verify:

✅ **Query Quality**
- Sounds like a real user question
- Grammatically correct
- Appropriate length for complexity level

✅ **Score Consistency**
- View scores correlate (0.6-0.9 correlation)
- Expected complexity matches view average (±0.05)
- Boundary samples properly positioned

✅ **Feature Accuracy**
- All features derivable from query text
- Values within specified ranges
- Logical consistency between related features

✅ **Reasoning Quality**
- Clear explanation for each view score
- References specific query elements
- Justifies the assigned complexity level

## Output Instructions

Generate exactly 25 samples in a JSON array:
```json
[
  { /* Sample 1 */ },
  { /* Sample 2 */ },
  ...
  { /* Sample 25 */ }
]
```

Ensure:
1. First 20 samples are clearly simple (0.10-0.25)
2. Last 5 samples are boundary cases (0.26-0.35)
3. Natural progression in complexity
4. Variety in domains and query types
5. No duplicate or overly similar queries

Begin generation now, maintaining high quality throughout all 25 samples.