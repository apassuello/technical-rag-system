# Claude Generation Prompts for Epic 1 Training Dataset

## Overview
This document contains the structured prompts for Claude to generate high-quality training data for the Epic 1 multi-view ML query complexity analyzer.

## Master Generation Prompt Template

### System Prompt
```
You are an expert in query complexity analysis and machine learning data generation. You will generate training data for a multi-view ML system that analyzes query complexity across 5 orthogonal dimensions:

1. **Technical Complexity**: Domain-specific terminology, jargon, technical depth
2. **Linguistic Complexity**: Sentence structure, vocabulary, readability  
3. **Task Complexity**: Cognitive load based on Bloom's taxonomy
4. **Semantic Complexity**: Conceptual relationships, abstraction level
5. **Computational Complexity**: Algorithm/implementation complexity

Your task is to generate realistic queries with detailed complexity assessments across all 5 views, following the exact data structure specifications provided.

**Quality Standards:**
- Each query must be realistic and represent genuine user information needs
- View scores must be internally consistent and well-justified
- All numerical scores must be on 0.0-1.0 scale with proper calibration
- Feature extraction must be accurate and verifiable
- Reasoning must be clear and educational
```

### Task Prompt Template
```
Generate {num_samples} training datapoints for complexity level: {target_complexity}

**Target Complexity Level**: {target_complexity} 
- Simple (0.0-0.33): Basic questions requiring minimal expertise
- Medium (0.34-0.66): Moderate questions requiring some domain knowledge  
- Complex (0.67-1.0): Advanced questions requiring deep expertise

**Domain Focus**: {target_domain} (if specified)
**Query Types to Include**: {query_types}

For each query, provide a complete TrainingDataPoint following this exact JSON structure:

```json
{
  "query_text": "...",
  "expected_complexity_score": 0.0-1.0,
  "expected_complexity_level": "simple|medium|complex",
  "view_scores": {
    "technical": {
      "view_name": "technical", 
      "complexity_score": 0.0-1.0,
      "confidence": 0.0-1.0,
      "primary_indicators": ["indicator1", "indicator2"],
      "feature_values": {
        "technical_terms_count": int,
        "domain_specificity_score": 0.0-1.0,
        "jargon_density": float,
        "concept_depth": 1-5,
        "passive_voice_ratio": 0.0-1.0
      },
      "reasoning": "Detailed explanation of technical complexity assessment",
      "expected_distribution": "normal|bimodal|uniform",
      "difficulty_factors": ["factor1", "factor2"]
    },
    "linguistic": {
      "view_name": "linguistic",
      "complexity_score": 0.0-1.0, 
      "confidence": 0.0-1.0,
      "primary_indicators": ["indicator1", "indicator2"],
      "feature_values": {
        "avg_sentence_length": float,
        "syntactic_depth": int,
        "clause_complexity": 0.0-1.0,
        "abstract_concept_ratio": 0.0-1.0,
        "lexical_diversity": 0.0-1.0
      },
      "reasoning": "Detailed explanation of linguistic complexity",
      "expected_distribution": "normal|bimodal|uniform", 
      "difficulty_factors": ["factor1", "factor2"]
    },
    "task": {
      "view_name": "task",
      "complexity_score": 0.0-1.0,
      "confidence": 0.0-1.0,
      "primary_indicators": ["bloom_level", "cognitive_demand"],
      "feature_values": {
        "primary_bloom_level": 1-6,
        "cognitive_load": 0.0-1.0,
        "task_scope": 0.0-1.0,
        "solution_steps": int,
        "creativity_required": 0.0-1.0
      },
      "reasoning": "Bloom's taxonomy analysis with cognitive level justification",
      "expected_distribution": "normal|bimodal|uniform",
      "difficulty_factors": ["factor1", "factor2"]
    },
    "semantic": {
      "view_name": "semantic",
      "complexity_score": 0.0-1.0,
      "confidence": 0.0-1.0, 
      "primary_indicators": ["concept_density", "abstraction"],
      "feature_values": {
        "concept_density": 0.0-1.0,
        "relationship_complexity": 0.0-1.0,
        "abstraction_level": 1-5,
        "context_dependency": 0.0-1.0,
        "implicit_knowledge": 0.0-1.0
      },
      "reasoning": "Semantic relationship and conceptual complexity analysis",
      "expected_distribution": "normal|bimodal|uniform",
      "difficulty_factors": ["factor1", "factor2"]
    },
    "computational": {
      "view_name": "computational", 
      "complexity_score": 0.0-1.0,
      "confidence": 0.0-1.0,
      "primary_indicators": ["algorithm_complexity", "implementation"],
      "feature_values": {
        "algorithm_mentions": int,
        "complexity_class": 0.0-1.0,
        "data_structure_count": int,
        "implementation_difficulty": 0.0-1.0,
        "optimization_aspects": 0.0-1.0
      },
      "reasoning": "Computational and algorithmic complexity assessment", 
      "expected_distribution": "normal|bimodal|uniform",
      "difficulty_factors": ["factor1", "factor2"]
    }
  },
  "metadata": {
    "generation_timestamp": "ISO-8601 timestamp",
    "claude_model": "claude-3-5-sonnet-20241022",
    "prompt_version": "v1.0",
    "domain": "technical|general|academic",
    "query_type": "how-to|definition|troubleshooting|comparison|analysis",
    "complexity_category": "primary complexity driver",
    "quality_score": 0.0-1.0,
    "validation_flags": [],
    "human_review_needed": false,
    "target_complexity_level": "{target_complexity}",
    "difficulty_subcategory": "specific subcategory"
  }
}
```

**Critical Requirements:**
1. **Score Consistency**: View scores should correlate but not be identical
2. **Realistic Queries**: All queries must represent genuine user needs
3. **Feature Accuracy**: All feature values must be realistic and derivable
4. **Balanced Distribution**: Generate diverse queries within complexity level
5. **Self-Validation**: Check your work for consistency before output
```

## Complexity-Specific Prompts

### Simple Complexity Prompt (0.0-0.33)
```
Generate simple queries targeting new users or basic concepts:

**Characteristics:**
- Short, direct questions
- Common vocabulary, minimal jargon  
- Single-step tasks (Knowledge/Comprehension in Bloom's)
- Clear, concrete concepts
- Minimal computational complexity

**Example domains:**
- "How do I create a Python list?"
- "What is a database?"
- "How to install Node.js?"

**Scoring calibration:**
- Technical: 0.1-0.3 (basic terms, common concepts)
- Linguistic: 0.1-0.3 (simple sentences, common words)
- Task: 0.1-0.3 (recall, understanding)
- Semantic: 0.1-0.3 (concrete, direct concepts)
- Computational: 0.0-0.3 (basic operations)
```

### Medium Complexity Prompt (0.34-0.66)
```
Generate medium complexity queries for users with some domain knowledge:

**Characteristics:**
- Multi-part questions with moderate depth
- Mix of common and specialized terminology
- Application/Analysis tasks (Bloom's levels 3-4)
- Some abstract concepts requiring explanation
- Moderate algorithmic complexity

**Example domains:**
- "How do I optimize a SQL query with multiple joins?"
- "What's the difference between REST and GraphQL APIs?"
- "How to implement error handling in async JavaScript?"

**Scoring calibration:**
- Technical: 0.3-0.7 (specialized terms, domain knowledge)
- Linguistic: 0.3-0.6 (complex sentences, technical vocabulary)
- Task: 0.3-0.7 (application, analysis)
- Semantic: 0.3-0.7 (relationships, some abstraction)
- Computational: 0.3-0.7 (algorithms, optimization)
```

### Complex Complexity Prompt (0.67-1.0)
```
Generate complex queries requiring deep expertise:

**Characteristics:**
- Multi-layered questions with deep technical depth
- Heavy use of domain-specific jargon and concepts
- Synthesis/Evaluation tasks (Bloom's levels 5-6)
- High abstraction, implicit knowledge requirements
- Advanced algorithmic and architectural complexity

**Example domains:**
- "How do I implement a distributed consensus algorithm with Byzantine fault tolerance?"
- "What are the trade-offs between microservices and modular monoliths in terms of operational complexity?"
- "How to design a real-time ML inference pipeline with sub-10ms latency requirements?"

**Scoring calibration:**
- Technical: 0.6-1.0 (expert terminology, deep concepts)
- Linguistic: 0.5-0.8 (complex syntax, abstract language)
- Task: 0.6-1.0 (synthesis, evaluation, creation)
- Semantic: 0.6-1.0 (high abstraction, implicit knowledge)
- Computational: 0.6-1.0 (complex algorithms, system design)
```

## Domain-Specific Prompts

### Technical Domain Prompt
```
Focus on technical/programming queries:

**Domains to cover:**
- Software engineering, algorithms, system design
- DevOps, infrastructure, performance optimization  
- Machine learning, data engineering
- Security, networking, databases

**Query pattern examples:**
- Implementation: "How do I implement X using Y?"
- Debugging: "Why is my X not working when I do Y?"
- Architecture: "What's the best way to design X for Y requirements?"
- Optimization: "How can I optimize X for better Y performance?"
- Comparison: "What are the pros/cons of X vs Y for Z use case?"
```

### Academic Domain Prompt
```
Focus on research/academic queries:

**Domains to cover:**
- Computer science theory, mathematics
- Research methodologies, experimental design
- Academic writing, literature review
- Statistical analysis, data interpretation

**Query pattern examples:**  
- Theory: "What is the theoretical foundation of X?"
- Research: "How do I design an experiment to test X?"
- Analysis: "What statistical test should I use for X data?"
- Literature: "What are the key papers on X in Y field?"
```

## Quality Validation Prompt

```
Before finalizing your response, validate each datapoint:

**Consistency Checks:**
1. Do view scores align with query complexity?
2. Are feature values realistic and derivable?
3. Is the reasoning clear and educational?
4. Does expected_complexity_score match view score average?

**Quality Standards:**
1. Query represents genuine user need ✓
2. All scores are properly calibrated ✓  
3. Feature extraction is accurate ✓
4. Reasoning is clear and detailed ✓
5. Metadata is complete and accurate ✓

**Red Flags to Avoid:**
- Identical scores across views
- Unrealistic feature values
- Generic or artificial-sounding queries
- Inconsistent complexity assessments
- Missing or incomplete reasoning

Only output datapoints that pass all validation checks.
```

## Example Few-Shot Demonstrations

### Simple Query Example
```json
{
  "query_text": "How do I print hello world in Python?",
  "expected_complexity_score": 0.15,
  "expected_complexity_level": "simple",
  "view_scores": {
    "technical": {
      "complexity_score": 0.2,
      "confidence": 0.95,
      "reasoning": "Basic Python syntax with fundamental print function. Minimal technical depth.",
      "feature_values": {
        "technical_terms_count": 2,
        "domain_specificity_score": 0.3,
        "jargon_density": 0.15
      }
    }
    // ... other views
  }
}
```

This prompt structure ensures:
1. **Consistent quality** across all generated data
2. **Proper calibration** of complexity scores  
3. **Realistic queries** representing genuine user needs
4. **Detailed feature extraction** for ML training
5. **Self-validation** to catch quality issues before output