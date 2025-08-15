# Claude Training Data Generation Prompt - Medium Complexity Focus (Batch 1)

## System Context

You are an expert in query complexity analysis and machine learning data generation. You will generate high-quality training data for a multi-view ML system that analyzes query complexity across 5 orthogonal dimensions:

1. **Technical Complexity**: Domain-specific terminology, jargon, technical depth
2. **Linguistic Complexity**: Sentence structure, vocabulary, readability  
3. **Task Complexity**: Cognitive load based on Bloom's taxonomy (Knowledge, Comprehension, Application, Analysis, Synthesis, Evaluation)
4. **Semantic Complexity**: Conceptual relationships, abstraction level, implicit knowledge
5. **Computational Complexity**: Algorithm mentions, implementation difficulty, optimization aspects

Your task is to generate **50 training samples focused on MEDIUM complexity** with realistic queries and detailed complexity assessments across all 5 views.

## Critical Requirements

1. **Natural Language**: All queries must sound like genuine user questions - grammatically correct, conversational, and realistic
2. **Score Calibration**: Maintain consistent scoring within the medium range with boundary samples at both ends
3. **Feature Accuracy**: All numerical features must be derivable from the query text
4. **View Correlation**: Views should correlate (0.6-0.9) but not be identical
5. **Detailed Reasoning**: Provide clear explanations for each score

## Target Distribution for This Batch

Generate exactly 50 samples with this distribution:
- **5 samples**: Medium-simple boundary (0.32-0.40 overall complexity)
- **35 samples**: Clearly medium (0.41-0.55 overall complexity)
- **10 samples**: Medium-complex boundary (0.56-0.66 overall complexity)

## Medium Query Guidelines

Generate **authentic medium-complexity queries** that represent genuine intermediate-level developer questions. Focus on real-world scenarios that require some expertise but aren't highly advanced.

### Complexity Indicators for Medium Queries:
- **Technical Complexity**: Intermediate concepts, multiple technologies, some specialization
- **Cognitive Demand**: Application, analysis, evaluation (Bloom's levels 3-4)
- **User Context**: Developers with some experience, intermediate practitioners
- **Answer Scope**: Multi-step solutions, trade-off discussions, implementation guidance

### Encourage Natural Diversity:
- **Real Development Scenarios**: Focus on actual problems developers encounter
- **Multiple Domains**: Web development, backend systems, databases, DevOps, mobile, etc.
- **Authentic Language**: Use terminology and phrasing that actual developers use
- **Varied Complexity**: Natural range from simpler medium to more complex medium questions

## JSON Structure for Each Sample

**CRITICAL: Use this EXACT structure to match existing training infrastructure:**

```json
{
  "query_text": "Natural, grammatically correct user question",
  "expected_complexity_score": 0.48,
  "expected_complexity_level": "medium",
  "view_scores": {
    "technical": 0.52,
    "linguistic": 0.44,
    "task": 0.50,
    "semantic": 0.47,
    "computational": 0.49
  },
  "confidence": 0.86,
  "metadata": {
    "domain": "technical",
    "query_type": "architecture",
    "generation_timestamp": "2025-08-07T20:00:00Z",
    "base_score": 0.48,
    "template_used": "none - natural generation"
  }
}
```

**IMPORTANT**: 
- `view_scores` contains ONLY simple float values (0.0-1.0), not complex objects
- Each view name must be exactly: "technical", "linguistic", "task", "semantic", "computational"
- All scores should be in the medium range: 0.32-0.66 for expected_complexity_score
- View scores can vary but should correlate with expected score

## Scoring Guidelines for Medium Complexity

### View Score Ranges for Medium Queries:
- **Technical (0.30-0.70)**: Specialized terminology, domain knowledge required, multiple technical concepts
- **Linguistic (0.25-0.65)**: Complex sentences, technical vocabulary, multi-clause constructions
- **Task (0.30-0.68)**: Bloom's Level 2-4 (Comprehension to Analysis), multi-step solutions
- **Semantic (0.30-0.68)**: Multiple interrelated concepts, moderate abstraction, domain context needed
- **Computational (0.25-0.70)**: Algorithm mentions, optimization considerations, moderate implementation difficulty

### How to Score Each View:
1. **Technical**: Assess domain specificity, count technical terms, evaluate concept relationships
2. **Linguistic**: Analyze sentence complexity, vocabulary sophistication, syntactic structure
3. **Task**: Identify Bloom's level (Application/Analysis), count solution steps, assess scope
4. **Semantic**: Evaluate concept density, abstraction level, implicit knowledge requirements
5. **Computational**: Consider algorithms, data structures, implementation complexity, optimization needs

**Key Principle**: All view scores should correlate (0.6-0.9 correlation) and average to approximately the expected_complexity_score.

## Example Samples for Calibration

### Example 1: Medium-Simple Boundary (Score: 0.38)
```json
{
  "query_text": "How do I handle errors properly in async JavaScript functions with try-catch?",
  "expected_complexity_score": 0.38,
  "expected_complexity_level": "medium",
  "view_scores": {
    "technical": 0.42,
    "linguistic": 0.35,
    "task": 0.39,
    "semantic": 0.37,
    "computational": 0.38
  },
  "confidence": 0.87,
  "metadata": {
    "domain": "technical",
    "query_type": "implementation",
    "generation_timestamp": "2025-08-07T20:00:00Z",
    "base_score": 0.38,
    "template_used": "none - natural generation"
  }
}
```

**Analysis**: Async JavaScript error handling. Technical (0.42) - async/await concepts and patterns. Linguistic (0.35) - moderate sentence complexity. Task (0.39) - Bloom's Level 3 application. Semantic (0.37) - relationships between error handling and async flow. Computational (0.38) - async execution model understanding.

### Example 2: Clear Medium (Score: 0.48)
```json
{
  "query_text": "What's the best approach to implement rate limiting for REST APIs to prevent abuse while maintaining good user experience?",
  "expected_complexity_score": 0.48,
  "expected_complexity_level": "medium",
  "view_scores": {
    "technical": 0.52,
    "linguistic": 0.44,
    "task": 0.50,
    "semantic": 0.47,
    "computational": 0.49
  },
  "confidence": 0.86,
  "metadata": {
    "domain": "technical",
    "query_type": "architecture",
    "generation_timestamp": "2025-08-07T20:00:00Z",
    "base_score": 0.48,
    "template_used": "none - natural generation"
  }
}
```

**Analysis**: Rate limiting architecture question. Technical (0.52) - API design, security concepts. Linguistic (0.44) - complex sentence with trade-offs. Task (0.50) - Bloom's Level 4 analysis. Semantic (0.47) - balancing competing concepts. Computational (0.49) - rate limiting algorithms.

### Example 3: Medium-Complex Boundary (Score: 0.62)
```json
{
  "query_text": "How should I design a distributed caching layer with cache invalidation strategies for a microservices architecture handling millions of requests per hour?",
  "expected_complexity_score": 0.62,
  "expected_complexity_level": "medium",
  "view_scores": {
    "technical": 0.65,
    "linguistic": 0.58,
    "task": 0.64,
    "semantic": 0.61,
    "computational": 0.63
  },
  "confidence": 0.83,
  "metadata": {
    "domain": "technical",
    "query_type": "architecture",
    "generation_timestamp": "2025-08-07T20:00:00Z",
    "base_score": 0.62,
    "template_used": "none - natural generation"
  }
}
```

**Analysis**: Distributed caching architecture. Technical (0.65) - advanced distributed systems concepts. Linguistic (0.58) - complex multi-concept sentence. Task (0.64) - Bloom's Level 5 synthesis. Semantic (0.61) - high conceptual complexity. Computational (0.63) - cache algorithms and protocols.

## Domain and Query Type Distribution

Ensure variety across the 25 samples:

### Domains (distribute naturally across samples):
- **Technical** (30 samples): Systems programming, performance optimization, architecture design
- **Academic** (12 samples): Computer architecture theory, algorithms, system design
- **General** (8 samples): Development practices, tooling, integration

### Query Types (distribute naturally across samples):
- **implementation**: "How to implement X?", "How to optimize Y?"
- **architecture**: "How to design system for X?", "Best practices for Y?"
- **optimization**: "How to improve performance?", "Optimize for X constraints?"
- **troubleshooting**: "Why is X slow?", "Debug Y issue?"
- **comparison**: "X vs Y for Z?", "Compare approaches A and B?"

### Computer Architecture & Systems Topic Areas for Medium Queries:
- CPU architecture and pipeline optimization
- Memory systems and caching strategies  
- Operating system internals and system calls
- Compiler design and optimization
- Performance analysis and profiling
- Parallel programming and synchronization
- Computer system design principles
- Hardware-software interfaces

## Topic Areas to Cover

Include diverse technical topics across the 25 samples:
- Web development (React, Vue, Angular, APIs)
- Backend systems (Node.js, Python, Java, Go)
- Databases (SQL, NoSQL, caching, optimization)
- Cloud and DevOps (AWS, Docker, Kubernetes, CI/CD)
- Security (authentication, authorization, encryption)
- Performance (optimization, scalability, monitoring)
- Architecture patterns (microservices, event-driven, serverless)
- Data structures and algorithms
- Testing and quality assurance
- Mobile development concepts

## Quality Focus

**Primary Goal**: Generate authentic, diverse queries representing genuine intermediate-level developer challenges

✅ **Natural Language Priority**
- Each query should reflect real problems developers encounter
- Use authentic technical language and terminology
- Avoid formulaic or artificial phrasing

✅ **Authentic Medium Complexity**
- Ensure queries genuinely require intermediate-level knowledge (0.32-0.66)
- Focus on multi-step problems, design decisions, implementation challenges
- View scores should naturally correlate around the target complexity

✅ **Maximum Diversity**
- Every query should represent a unique scenario or problem
- Draw from varied technical domains and real-world situations
- Think like different developers with different experience levels and needs

## Output Instructions

**Generate 50 unique, authentic medium-complexity queries as a JSON array.**

**Key Requirements**:
- 5 samples in 0.32-0.40 range (medium-simple boundary)
- 35 samples in 0.41-0.55 range (clearly medium)
- 10 samples in 0.56-0.66 range (medium-complex boundary)
- Each query must represent a genuine developer scenario
- Focus on real implementation, debugging, and architecture challenges

**Creative Freedom**: Generate diverse, authentic queries that truly represent medium-complexity developer questions without following rigid patterns or templates.

Begin generation now, prioritizing authenticity and real-world relevance.