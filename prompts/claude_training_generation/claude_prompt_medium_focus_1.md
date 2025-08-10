	# Claude Training Data Generation Prompt - Medium Complexity Focus (Batch 1)

## 📝 **EASY TOPIC MODIFICATION GUIDE**

**🎯 Current Focus**: RISC-V Architecture and Development (Medium Complexity)



**Instructions**: Focus 70-80% of queries on the chosen topic, with 20-30% related technical areas for context.

## System Context

You are an expert in query complexity analysis and machine learning data generation. You will generate high-quality training data for a multi-view ML system that analyzes query complexity across 5 orthogonal dimensions:

1. **Technical Complexity**: Domain-specific terminology, jargon, technical depth
2. **Linguistic Complexity**: Sentence structure, vocabulary, readability  
3. **Task Complexity**: Cognitive load based on Bloom's taxonomy (Knowledge, Comprehension, Application, Analysis, Synthesis, Evaluation)
4. **Semantic Complexity**: Conceptual relationships, abstraction level, implicit knowledge
5. **Computational Complexity**: Algorithm mentions, implementation difficulty, optimization aspects

Your task is to generate **25 training samples focused on MEDIUM complexity** with realistic queries and detailed complexity assessments across all 5 views.

## 🎯 **TOPIC FOCUS FOR THIS BATCH**

**Primary Topic**: RISC-V Architecture and Development (Medium Complexity)

Generate queries related to:
- **RISC-V Performance**: Optimization techniques, pipeline analysis, cache behavior
- **RISC-V Extensions**: Vector extensions (RVV), custom instructions, specialized ISAs
- **RISC-V System Programming**: Privileged architecture, interrupts, memory management
- **RISC-V Compiler Technology**: GCC optimizations, LLVM backend, code generation
- **RISC-V Implementation**: Core design choices, microarchitecture considerations

**Important**: Focus on intermediate-level concepts requiring some domain knowledge and multi-step reasoning.

## Critical Requirements

1. **Natural Language**: All queries must sound like genuine user questions - grammatically correct, conversational, and realistic
2. **Score Calibration**: Maintain consistent scoring within the medium range with boundary samples at both ends
3. **Feature Accuracy**: All numerical features must be derivable from the query text
4. **View Correlation**: Views should correlate (0.6-0.9) but not be identical
5. **Detailed Reasoning**: Provide clear explanations for each score

## Target Distribution for This Batch

Generate exactly 25 samples with this distribution:
- **5 samples**: Medium-simple boundary (0.32-0.40 overall complexity)
- **15 samples**: Clearly medium (0.41-0.55 overall complexity)
- **5 samples**: Medium-complex boundary (0.56-0.66 overall complexity)

## Medium Query Characteristics

### Medium-Simple Boundary (0.32-0.40)
- **Query Length**: 10-20 words
- **Vocabulary**: Mix of common and technical terms
- **Technical Terms**: 2-4 technical terms
- **Task Type**: Basic debugging, simple optimizations, comparisons
- **Cognitive Level**: Bloom's 2-3 (Comprehension, Application)
- **Examples**: "How do I optimize database queries with indexes?", "What causes memory leaks in JavaScript?"

### Clear Medium (0.41-0.55)
- **Query Length**: 15-30 words
- **Vocabulary**: Technical terminology with some domain specificity
- **Technical Terms**: 3-6 technical terms
- **Task Type**: Implementation questions, troubleshooting, design decisions
- **Cognitive Level**: Bloom's 3-4 (Application, Analysis)
- **Examples**: "How can I implement caching to reduce API calls in a React application?", "What's the best way to handle authentication in a microservices architecture?"

### Medium-Complex Boundary (0.56-0.66)
- **Query Length**: 20-35 words
- **Vocabulary**: Sophisticated technical language
- **Technical Terms**: 5-8 technical terms
- **Task Type**: Architecture decisions, performance optimization, complex debugging
- **Cognitive Level**: Bloom's 4-5 (Analysis, Synthesis)
- **Examples**: "How do I implement retry logic with exponential backoff for distributed service calls?", "What are the trade-offs between event sourcing and traditional CRUD in a high-traffic system?"

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

## Feature Value Guidelines for Medium Complexity

### Technical View Features
- **technical_terms_count**: 2-8 (APIs, frameworks, patterns, protocols)
- **domain_specificity_score**: 0.3-0.7 (moderate to high specialization)
- **jargon_density**: 0.15-0.40 (significant technical vocabulary)
- **concept_depth**: 2-4 (requires understanding of relationships)
- **passive_voice_ratio**: Often higher in technical explanations

### Linguistic View Features
- **avg_sentence_length**: 10-30 words (more complex constructions)
- **syntactic_depth**: 2-3 (nested clauses, compound sentences)
- **clause_complexity**: 0.2-0.6 (moderate subordination)
- **abstract_concept_ratio**: 0.15-0.45 (mix of concrete and abstract)
- **lexical_diversity**: 0.5-0.8 (varied vocabulary)

### Task View Features (Bloom's Taxonomy)
- **primary_bloom_level**: 2-4 (Comprehension to Analysis)
- **cognitive_load**: 0.3-0.65 (moderate mental effort)
- **task_scope**: 0.3-0.65 (multi-component tasks)
- **solution_steps**: 3-8 (multi-step solutions)
- **creativity_required**: 0.1-0.5 (some problem-solving creativity)

### Semantic View Features
- **concept_density**: 0.3-0.65 (multiple interrelated concepts)
- **relationship_complexity**: 0.25-0.65 (moderate interconnections)
- **abstraction_level**: 2-3 (mix of concrete and abstract)
- **context_dependency**: 0.3-0.65 (requires domain context)
- **implicit_knowledge**: 0.2-0.55 (assumes some background)

### Computational View Features
- **algorithm_mentions**: 0-3 (sorting, searching, optimization)
- **complexity_class**: 0.2-0.65 (O(n) to O(n log n) typical)
- **data_structure_count**: 0-3 (arrays, trees, graphs mentioned)
- **implementation_difficulty**: 0.3-0.65 (moderate coding challenge)
- **optimization_aspects**: 0.1-0.6 (performance considerations)

## Example Samples for Calibration

### Example 1: Medium-Simple Boundary (Score: 0.38)
```json
{
  "query_text": "How do I handle errors properly in async JavaScript functions with try-catch?",
  "expected_complexity_score": 0.38,
  "expected_complexity_level": "medium",
  "view_scores": {
    "technical": {
      "complexity_score": 0.42,
      "confidence": 0.88,
      "reasoning": "Involves asynchronous programming concepts and error handling patterns. Requires understanding of promises and async/await syntax.",
      "feature_values": {
        "technical_terms_count": 4,
        "domain_specificity_score": 0.4,
        "jargon_density": 0.25,
        "concept_depth": 2,
        "passive_voice_ratio": 0.0
      }
    },
    "linguistic": {
      "complexity_score": 0.35,
      "confidence": 0.90,
      "reasoning": "Moderate sentence complexity with technical vocabulary. Clear structure but requires domain knowledge to fully understand.",
      "feature_values": {
        "avg_sentence_length": 12.0,
        "syntactic_depth": 2,
        "clause_complexity": 0.3,
        "abstract_concept_ratio": 0.25,
        "lexical_diversity": 0.75
      }
    },
    "task": {
      "complexity_score": 0.39,
      "confidence": 0.85,
      "reasoning": "Bloom's Level 3 (Application) - applying error handling patterns to async code. Requires understanding and practical implementation.",
      "feature_values": {
        "primary_bloom_level": 3,
        "cognitive_load": 0.38,
        "task_scope": 0.35,
        "solution_steps": 4,
        "creativity_required": 0.15
      }
    },
    "semantic": {
      "complexity_score": 0.37,
      "confidence": 0.86,
      "reasoning": "Involves understanding relationships between error handling, asynchronous execution, and control flow. Moderate abstraction.",
      "feature_values": {
        "concept_density": 0.35,
        "relationship_complexity": 0.4,
        "abstraction_level": 2,
        "context_dependency": 0.35,
        "implicit_knowledge": 0.3
      }
    },
    "computational": {
      "complexity_score": 0.38,
      "confidence": 0.87,
      "reasoning": "Understanding async execution model and error propagation. No specific algorithms but implementation patterns are important.",
      "feature_values": {
        "algorithm_mentions": 0,
        "complexity_class": 0.3,
        "data_structure_count": 0,
        "implementation_difficulty": 0.38,
        "optimization_aspects": 0.2
      }
    }
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

### Example 2: Clear Medium (Score: 0.48)
```json
{
  "query_text": "What's the best approach to implement rate limiting for REST APIs to prevent abuse while maintaining good user experience?",
  "expected_complexity_score": 0.48,
  "expected_complexity_level": "medium",
  "view_scores": {
    "technical": {
      "complexity_score": 0.52,
      "confidence": 0.86,
      "reasoning": "Involves API design, security concepts, and performance considerations. Multiple technical domains intersect.",
      "feature_values": {
        "technical_terms_count": 5,
        "domain_specificity_score": 0.5,
        "jargon_density": 0.28,
        "concept_depth": 3,
        "passive_voice_ratio": 0.1
      }
    },
    "linguistic": {
      "complexity_score": 0.44,
      "confidence": 0.88,
      "reasoning": "Complex sentence with multiple considerations. Balances technical precision with clarity.",
      "feature_values": {
        "avg_sentence_length": 18.0,
        "syntactic_depth": 3,
        "clause_complexity": 0.4,
        "abstract_concept_ratio": 0.35,
        "lexical_diversity": 0.72
      }
    },
    "task": {
      "complexity_score": 0.50,
      "confidence": 0.84,
      "reasoning": "Bloom's Level 4 (Analysis) - requires evaluating trade-offs and designing a solution balancing multiple concerns.",
      "feature_values": {
        "primary_bloom_level": 4,
        "cognitive_load": 0.5,
        "task_scope": 0.5,
        "solution_steps": 6,
        "creativity_required": 0.35
      }
    },
    "semantic": {
      "complexity_score": 0.47,
      "confidence": 0.85,
      "reasoning": "Involves balancing competing concepts (security vs usability). Requires understanding multiple domain relationships.",
      "feature_values": {
        "concept_density": 0.45,
        "relationship_complexity": 0.5,
        "abstraction_level": 3,
        "context_dependency": 0.45,
        "implicit_knowledge": 0.4
      }
    },
    "computational": {
      "complexity_score": 0.49,
      "confidence": 0.86,
      "reasoning": "Rate limiting algorithms, token bucket, sliding window. Performance implications of different approaches.",
      "feature_values": {
        "algorithm_mentions": 2,
        "complexity_class": 0.45,
        "data_structure_count": 2,
        "implementation_difficulty": 0.48,
        "optimization_aspects": 0.45
      }
    }
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

### Example 3: Medium-Complex Boundary (Score: 0.62)
```json
{
  "query_text": "How should I design a distributed caching layer with cache invalidation strategies for a microservices architecture handling millions of requests per hour?",
  "expected_complexity_score": 0.62,
  "expected_complexity_level": "medium",
  "view_scores": {
    "technical": {
      "complexity_score": 0.65,
      "confidence": 0.83,
      "reasoning": "Advanced distributed systems concepts including caching, invalidation, microservices, and high-scale considerations.",
      "feature_values": {
        "technical_terms_count": 7,
        "domain_specificity_score": 0.65,
        "jargon_density": 0.35,
        "concept_depth": 4,
        "passive_voice_ratio": 0.05
      }
    },
    "linguistic": {
      "complexity_score": 0.58,
      "confidence": 0.85,
      "reasoning": "Complex sentence structure with multiple technical concepts. Requires careful parsing to understand all requirements.",
      "feature_values": {
        "avg_sentence_length": 22.0,
        "syntactic_depth": 3,
        "clause_complexity": 0.5,
        "abstract_concept_ratio": 0.4,
        "lexical_diversity": 0.77
      }
    },
    "task": {
      "complexity_score": 0.64,
      "confidence": 0.82,
      "reasoning": "Bloom's Level 5 (Synthesis) - designing a complex system combining multiple patterns and considering scale.",
      "feature_values": {
        "primary_bloom_level": 5,
        "cognitive_load": 0.62,
        "task_scope": 0.65,
        "solution_steps": 8,
        "creativity_required": 0.5
      }
    },
    "semantic": {
      "complexity_score": 0.61,
      "confidence": 0.83,
      "reasoning": "High conceptual complexity with distributed systems, consistency models, and performance trade-offs.",
      "feature_values": {
        "concept_density": 0.6,
        "relationship_complexity": 0.65,
        "abstraction_level": 3,
        "context_dependency": 0.6,
        "implicit_knowledge": 0.55
      }
    },
    "computational": {
      "complexity_score": 0.63,
      "confidence": 0.84,
      "reasoning": "Cache algorithms, consistency protocols, distributed systems complexity. High-scale performance considerations.",
      "feature_values": {
        "algorithm_mentions": 2,
        "complexity_class": 0.6,
        "data_structure_count": 3,
        "implementation_difficulty": 0.62,
        "optimization_aspects": 0.6
      }
    }
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

## Domain and Query Type Distribution

Ensure variety across the 25 samples:

### Domains (distribute across samples):
- **Technical** (15 samples): RISC-V system programming, compiler optimization, performance tuning
- **Academic** (7 samples): RISC-V microarchitecture, ISA extensions, research topics
- **General** (3 samples): RISC-V ecosystem integration, development workflow

### Query Types (distribute across samples):
- **implementation** (8 samples): "How to implement X in RISC-V?", "How to optimize Y?"
- **architecture** (6 samples): "How to design RISC-V system?", "Best practices for X?"
- **optimization** (5 samples): "How to improve RISC-V performance?", "Optimize for X metric?"
- **troubleshooting** (4 samples): "Why is RISC-V code slow?", "Debug X issue?"
- **comparison** (2 samples): "RISC-V vs ARM for X?", "RVV vs scalar performance?"

### RISC-V Topic Areas for Medium Queries:
- Vector extension programming (RVV)
- Privileged architecture and system calls
- Memory model and synchronization
- Compiler optimization strategies
- Pipeline optimization and hazards
- Custom instruction development
- RISC-V core implementation details
- Performance profiling and analysis

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

## Validation Checklist

Before outputting each sample, verify:

✅ **Query Quality**
- Sounds like a real developer question
- Grammatically correct and natural
- Appropriate complexity for the range

✅ **Score Consistency**
- View scores correlate (0.6-0.9 correlation)
- Expected complexity matches view average (±0.05)
- Proper distribution across boundary and core samples

✅ **Feature Accuracy**
- All features derivable from query text
- Values within specified ranges for medium complexity
- Logical relationships between features

✅ **Reasoning Quality**
- Specific references to query elements
- Clear justification for complexity level
- Mentions relevant technical concepts

✅ **Diversity**
- No duplicate concepts or overly similar queries
- Good distribution across domains and types
- Various technical topics covered

## Output Instructions

Generate exactly 25 samples in a JSON array:
```json
[
  { /* Sample 1 - boundary (0.32-0.40) */ },
  { /* Sample 2 - boundary (0.32-0.40) */ },
  { /* Sample 3 - boundary (0.32-0.40) */ },
  { /* Sample 4 - boundary (0.32-0.40) */ },
  { /* Sample 5 - boundary (0.32-0.40) */ },
  { /* Sample 6 - clear medium (0.41-0.55) */ },
  { /* Sample 7 - clear medium (0.41-0.55) */ },
  /* ... samples 8-20 - clear medium ... */,
  { /* Sample 21 - boundary (0.56-0.66) */ },
  { /* Sample 22 - boundary (0.56-0.66) */ },
  { /* Sample 23 - boundary (0.56-0.66) */ },
  { /* Sample 24 - boundary (0.56-0.66) */ },
  { /* Sample 25 - boundary (0.56-0.66) */ }
]
```

Ensure:
1. Natural progression from simple-medium boundary to complex-medium boundary
2. Realistic developer questions throughout
3. Variety in technical topics and approaches
4. Consistent quality and detail in all samples
5. Proper calibration within medium complexity range

Begin generation now, maintaining high quality throughout all 25 samples.