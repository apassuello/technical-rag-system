# Claude Training Data Generation Prompt - Simple Complexity Focus


## System Context

You are an expert in query complexity analysis and machine learning data generation. You will generate high-quality training data for a multi-view ML system that analyzes query complexity across 5 orthogonal dimensions:

1. **Technical Complexity**: Domain-specific terminology, jargon, technical depth
2. **Linguistic Complexity**: Sentence structure, vocabulary, readability  
3. **Task Complexity**: Cognitive load based on Bloom's taxonomy (Knowledge, Comprehension, Application, Analysis, Synthesis, Evaluation)
4. **Semantic Complexity**: Conceptual relationships, abstraction level, implicit knowledge
5. **Computational Complexity**: Algorithm mentions, implementation difficulty, optimization aspects

Your task is to generate **50 training samples focused on SIMPLE complexity** with realistic queries and detailed complexity assessments across all 5 views.

## Critical Requirements

1. **Natural Language**: All queries must sound like genuine user questions - grammatically correct, conversational, and realistic
2. **Score Calibration**: Maintain consistent scoring within the simple range with some boundary samples
3. **Feature Accuracy**: All numerical features must be derivable from the query text
4. **View Correlation**: Views should correlate (0.6-0.9) but not be identical
5. **Detailed Reasoning**: Provide clear explanations for each score

## Target Distribution for This Batch

Generate exactly 50 samples with this distribution:
- **40 samples**: Clearly simple (0.10-0.25 overall complexity)
- **10 samples**: Simple-medium boundary (0.26-0.35 overall complexity)

## Simple Query Guidelines

Generate **naturally diverse queries** that represent genuine beginner and basic-level questions. Focus on authentic user needs rather than following templates.

### Complexity Indicators for Simple Queries:
- **Technical Complexity**: Basic programming concepts, common tools, fundamental terminology
- **Cognitive Demand**: Recall, understanding, basic application (Bloom's levels 1-3)
- **User Context**: Beginners, students, developers learning new concepts
- **Answer Scope**: Direct answers, single-step solutions, straightforward explanations

### Encourage Natural Diversity:
- **Various Question Styles**: Mix direct questions, how-to requests, definition seeking, basic troubleshooting
- **Different Domains**: Web development, programming languages, tools, databases, basic concepts
- **Authentic Language**: Use natural phrasing that real users would actually type
- **Avoid Repetitive Patterns**: Each query should feel unique and genuine

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

### Domains (distribute naturally across samples):
- **Technical** (30 samples): Programming, system administration, development tools
- **Academic** (12 samples): Computer science concepts, algorithms, theory
- **General** (8 samples): Computing basics, getting started topics

### Query Types (distribute naturally across samples):
- **definition**: "What is X?", "What does Y mean?"
- **how-to**: "How to do X?", "How to use Y?"  
- **comparison**: "X vs Y", "Difference between A and B"
- **troubleshooting**: "Why won't X work?", basic debugging

### Computer Architecture & Systems Topic Areas for Simple Queries:
- Basic computer architecture (CPU, memory, I/O)
- Assembly language fundamentals
- Operating system basics
- Computer organization concepts
- Hardware/software interfaces
- System programming fundamentals
- Development tools and environments

## Quality Focus

**Primary Goal**: Generate authentic, diverse queries that genuinely represent simple complexity level

✅ **Natural Language Priority**
- Each query should sound like something a real person would actually ask
- Avoid formulaic or template-like phrasing
- Use conversational, natural language

✅ **Authentic Complexity**
- Ensure queries truly match the simple complexity range (0.10-0.35)
- Focus on beginner-level questions and basic concepts
- View scores should naturally correlate around the target complexity

✅ **Maximum Diversity**
- No two queries should be similar or follow the same pattern
- Vary question structure, domain, and approach naturally
- Think like different users with different backgrounds and needs

## Output Instructions

**Generate 50 unique, authentic simple queries as a JSON array.**

**Key Requirements**:
- 40 samples in 0.10-0.25 range (clearly simple)
- 10 samples in 0.26-0.35 range (simple-medium boundary) 
- Each query must be genuinely different and natural
- Focus on authentic user questions, not artificial examples
- Maintain proper complexity scoring for the simple level

**Creative Freedom**: You have complete freedom in query content, structure, and domain as long as the complexity level is appropriate and the language is natural.

Begin generation now, prioritizing authenticity and diversity over rigid patterns.