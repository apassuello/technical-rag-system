# Claude Training Data Generation Prompt - Medium Complexity Focus (Batch 2)

## 📝 **EASY TOPIC MODIFICATION GUIDE**

**🎯 Current Focus**: RISC-V Architecture and Development (Medium Complexity - Batch 2)



**Instructions**: Focus 70-80% of queries on the chosen topic, with 20-30% complementary technical areas.

## System Context

You are an expert in query complexity analysis and machine learning data generation. You will generate high-quality training data for a multi-view ML system that analyzes query complexity across 5 orthogonal dimensions:

1. **Technical Complexity**: Domain-specific terminology, jargon, technical depth
2. **Linguistic Complexity**: Sentence structure, vocabulary, readability  
3. **Task Complexity**: Cognitive load based on Bloom's taxonomy (Knowledge, Comprehension, Application, Analysis, Synthesis, Evaluation)
4. **Semantic Complexity**: Conceptual relationships, abstraction level, implicit knowledge
5. **Computational Complexity**: Algorithm mentions, implementation difficulty, optimization aspects

Your task is to generate **25 training samples focused on MEDIUM complexity** with realistic queries and detailed complexity assessments across all 5 views. This is the SECOND batch of medium complexity samples, so ensure variety from typical patterns.

## 🎯 **TOPIC FOCUS FOR THIS BATCH**

**Primary Topic**: RISC-V Architecture and Development (Medium Complexity - Batch 2)

Generate queries related to:
- **RISC-V Ecosystem Integration**: Linux kernel, bootloaders, device drivers
- **RISC-V Security**: TEE implementation, crypto extensions, secure boot
- **RISC-V Debugging**: GDB usage, hardware debugging, trace analysis
- **RISC-V Verification**: Formal methods, testing strategies, compliance
- **RISC-V Applications**: HPC workloads, embedded systems, real-time applications

**Important**: Focus on practical implementation challenges and system-level integration topics.

## Critical Requirements

1. **Natural Language**: All queries must sound like genuine user questions - grammatically correct, conversational, and realistic
2. **Score Calibration**: Maintain consistent scoring within the medium range with boundary samples at both ends
3. **Feature Accuracy**: All numerical features must be derivable from the query text
4. **View Correlation**: Views should correlate (0.6-0.9) but not be identical
5. **Detailed Reasoning**: Provide clear explanations for each score
6. **Diversity from Batch 1**: Focus on different technical areas and question patterns

## Target Distribution for This Batch

Generate exactly 25 samples with this distribution:
- **5 samples**: Medium-simple boundary (0.32-0.40 overall complexity)
- **15 samples**: Clearly medium (0.41-0.55 overall complexity)
- **5 samples**: Medium-complex boundary (0.56-0.66 overall complexity)

## Focus Areas for Batch 2 (Different from Batch 1)

To ensure diversity, this batch should emphasize:
- **Data Engineering & Analytics**: ETL, data pipelines, warehousing, ML ops
- **Mobile & Cross-Platform Development**: iOS, Android, React Native, Flutter
- **Infrastructure & Networking**: Load balancing, CDNs, protocols, network optimization
- **Testing & Quality**: Unit testing, integration testing, TDD, code quality
- **Modern Frontend Patterns**: State management, SSR/SSG, PWAs, WebAssembly

## JSON Structure for Each Sample

**CRITICAL: Use this EXACT structure to match existing training infrastructure:**

```json
{
  "query_text": "Natural, grammatically correct user question",
  "expected_complexity_score": 0.49,
  "expected_complexity_level": "medium",
  "view_scores": {
    "technical": 0.53,
    "linguistic": 0.45,
    "task": 0.51,
    "semantic": 0.48,
    "computational": 0.48
  },
  "confidence": 0.85,
  "metadata": {
    "domain": "technical",
    "query_type": "architecture",
    "generation_timestamp": "2025-08-07T20:00:00Z",
    "base_score": 0.49,
    "template_used": "none - natural generation"
  }
}
```

**IMPORTANT**: 
- `view_scores` contains ONLY simple float values (0.0-1.0), not complex objects
- Each view name must be exactly: "technical", "linguistic", "task", "semantic", "computational"
- All scores should be in the medium range: 0.32-0.66 for expected_complexity_score
- View scores can vary but should correlate with expected score

## Example Samples for Calibration (Batch 2 Specific)

### Example 1: Medium-Simple Boundary (Score: 0.36) - Data Engineering Focus
```json
{
  "query_text": "How can I optimize my ETL pipeline to handle large CSV files without running out of memory?",
  "expected_complexity_score": 0.36,
  "expected_complexity_level": "medium",
  "view_scores": {
    "technical": {
      "complexity_score": 0.40,
      "confidence": 0.89,
      "reasoning": "ETL concepts with memory optimization. Common problem but requires understanding of data processing patterns.",
      "feature_values": {
        "technical_terms_count": 4,
        "domain_specificity_score": 0.38,
        "jargon_density": 0.22,
        "concept_depth": 2,
        "passive_voice_ratio": 0.0
      }
    },
    "linguistic": {
      "complexity_score": 0.33,
      "confidence": 0.91,
      "reasoning": "Clear question structure with domain-specific terms. Straightforward but technical.",
      "feature_values": {
        "avg_sentence_length": 14.0,
        "syntactic_depth": 2,
        "clause_complexity": 0.25,
        "abstract_concept_ratio": 0.2,
        "lexical_diversity": 0.71
      }
    },
    "task": {
      "complexity_score": 0.37,
      "confidence": 0.87,
      "reasoning": "Bloom's Level 3 (Application) - applying optimization techniques to a specific problem.",
      "feature_values": {
        "primary_bloom_level": 3,
        "cognitive_load": 0.35,
        "task_scope": 0.4,
        "solution_steps": 4,
        "creativity_required": 0.2
      }
    },
    "semantic": {
      "complexity_score": 0.35,
      "confidence": 0.88,
      "reasoning": "Involves understanding data flow, memory management, and processing constraints.",
      "feature_values": {
        "concept_density": 0.35,
        "relationship_complexity": 0.35,
        "abstraction_level": 2,
        "context_dependency": 0.35,
        "implicit_knowledge": 0.25
      }
    },
    "computational": {
      "complexity_score": 0.36,
      "confidence": 0.89,
      "reasoning": "Memory optimization strategies, streaming processing. Performance considerations important.",
      "feature_values": {
        "algorithm_mentions": 1,
        "complexity_class": 0.35,
        "data_structure_count": 1,
        "implementation_difficulty": 0.35,
        "optimization_aspects": 0.4
      }
    }
  },
  "confidence": 0.88,
  "metadata": {
    "domain": "technical",
    "query_type": "optimization",
    "generation_timestamp": "2025-08-07T20:00:00Z",
    "base_score": 0.36,
    "template_used": "none - natural generation"
  }
}
```

### Example 2: Clear Medium (Score: 0.49) - Mobile Development Focus
```json
{
  "query_text": "What's the best strategy for managing state between native modules and React Native JavaScript code in a hybrid mobile app?",
  "expected_complexity_score": 0.49,
  "expected_complexity_level": "medium",
  "view_scores": {
    "technical": {
      "complexity_score": 0.53,
      "confidence": 0.85,
      "reasoning": "Cross-platform mobile development with native bridge concepts. Requires understanding multiple technology layers.",
      "feature_values": {
        "technical_terms_count": 6,
        "domain_specificity_score": 0.52,
        "jargon_density": 0.30,
        "concept_depth": 3,
        "passive_voice_ratio": 0.0
      }
    },
    "linguistic": {
      "complexity_score": 0.45,
      "confidence": 0.87,
      "reasoning": "Complex technical question with multiple related concepts. Clear but requires domain knowledge.",
      "feature_values": {
        "avg_sentence_length": 20.0,
        "syntactic_depth": 3,
        "clause_complexity": 0.45,
        "abstract_concept_ratio": 0.35,
        "lexical_diversity": 0.75
      }
    },
    "task": {
      "complexity_score": 0.51,
      "confidence": 0.83,
      "reasoning": "Bloom's Level 4 (Analysis) - analyzing architectural patterns and evaluating trade-offs.",
      "feature_values": {
        "primary_bloom_level": 4,
        "cognitive_load": 0.52,
        "task_scope": 0.55,
        "solution_steps": 6,
        "creativity_required": 0.4
      }
    },
    "semantic": {
      "complexity_score": 0.48,
      "confidence": 0.84,
      "reasoning": "Complex interaction between different runtime environments and state synchronization patterns.",
      "feature_values": {
        "concept_density": 0.48,
        "relationship_complexity": 0.52,
        "abstraction_level": 3,
        "context_dependency": 0.5,
        "implicit_knowledge": 0.45
      }
    },
    "computational": {
      "complexity_score": 0.48,
      "confidence": 0.85,
      "reasoning": "Bridge communication patterns, state synchronization algorithms. Performance and consistency considerations.",
      "feature_values": {
        "algorithm_mentions": 1,
        "complexity_class": 0.45,
        "data_structure_count": 2,
        "implementation_difficulty": 0.5,
        "optimization_aspects": 0.4
      }
    }
  },
  "confidence": 0.85,
  "metadata": {
    "domain": "technical",
    "query_type": "architecture",
    "generation_timestamp": "2025-08-07T20:00:00Z",
    "base_score": 0.49,
    "template_used": "none - natural generation"
  }
}
```

### Example 3: Medium-Complex Boundary (Score: 0.64) - Testing & Quality Focus
```json
{
  "query_text": "How do I implement contract testing for microservices with consumer-driven contracts while maintaining backward compatibility during API evolution?",
  "expected_complexity_score": 0.64,
  "expected_complexity_level": "medium",
  "view_scores": {
    "technical": {
      "complexity_score": 0.67,
      "confidence": 0.82,
      "reasoning": "Advanced testing concepts with microservices architecture. Multiple sophisticated patterns involved.",
      "feature_values": {
        "technical_terms_count": 8,
        "domain_specificity_score": 0.68,
        "jargon_density": 0.38,
        "concept_depth": 4,
        "passive_voice_ratio": 0.1
      }
    },
    "linguistic": {
      "complexity_score": 0.60,
      "confidence": 0.84,
      "reasoning": "Complex multi-clause sentence with specialized terminology. Requires careful parsing.",
      "feature_values": {
        "avg_sentence_length": 24.0,
        "syntactic_depth": 3,
        "clause_complexity": 0.55,
        "abstract_concept_ratio": 0.42,
        "lexical_diversity": 0.79
      }
    },
    "task": {
      "complexity_score": 0.66,
      "confidence": 0.81,
      "reasoning": "Bloom's Level 5 (Synthesis) - combining testing strategies with versioning and compatibility concerns.",
      "feature_values": {
        "primary_bloom_level": 5,
        "cognitive_load": 0.64,
        "task_scope": 0.68,
        "solution_steps": 8,
        "creativity_required": 0.48
      }
    },
    "semantic": {
      "complexity_score": 0.63,
      "confidence": 0.82,
      "reasoning": "Multiple interrelated concepts: testing, contracts, versioning, compatibility. High conceptual load.",
      "feature_values": {
        "concept_density": 0.62,
        "relationship_complexity": 0.68,
        "abstraction_level": 3,
        "context_dependency": 0.62,
        "implicit_knowledge": 0.55
      }
    },
    "computational": {
      "complexity_score": 0.65,
      "confidence": 0.83,
      "reasoning": "Contract validation algorithms, version management strategies. Complex coordination patterns.",
      "feature_values": {
        "algorithm_mentions": 2,
        "complexity_class": 0.62,
        "data_structure_count": 2,
        "implementation_difficulty": 0.65,
        "optimization_aspects": 0.5
      }
    }
  },
  "confidence": 0.82,
  "metadata": {
    "domain": "technical",
    "query_type": "implementation",
    "generation_timestamp": "2025-08-07T20:00:00Z",
    "base_score": 0.64,
    "template_used": "none - natural generation"
  }
}
```

## Domain and Query Type Distribution for Batch 2

### Domains (distribute across samples):
- **Technical** (14 samples): RISC-V system integration, kernel development, security
- **Academic** (7 samples): RISC-V verification, formal methods, research applications
- **General** (4 samples): RISC-V ecosystem tools, development practices

### Query Types (distribute across samples):
- **implementation** (7 samples): "How to port X to RISC-V?", "Implement Y feature?"
- **troubleshooting** (6 samples): "Debug RISC-V kernel issue?", "Fix X problem?"
- **optimization** (5 samples): "Optimize RISC-V for Y?", "Improve X performance?"
- **architecture** (4 samples): "Design RISC-V system for X?", "Best approach for Y?"
- **comparison** (3 samples): "RISC-V implementation X vs Y?", "Tool A vs B?"

### RISC-V Topic Areas for Medium Queries (Batch 2):
- Linux kernel porting and device drivers
- Security extensions and TEE implementation
- Hardware debugging and trace analysis
- Formal verification and testing methodologies
- Bootloader and firmware development
- Real-time and embedded system design
- RISC-V compliance and certification
- Performance analysis and benchmarking

## Specific Topic Areas for Batch 2

Ensure coverage of these areas (different from Batch 1):

### Data Engineering & Analytics
- Apache Spark, Kafka, Airflow
- Data warehousing (Snowflake, BigQuery, Redshift)
- Stream processing and real-time analytics
- Data quality and governance
- ML pipelines and feature stores

### Mobile Development
- React Native, Flutter, native iOS/Android
- Mobile performance optimization
- Offline-first architectures
- Push notifications and background tasks
- App store deployment and updates

### Testing & Quality
- Unit testing frameworks and mocking
- Integration and E2E testing strategies
- Performance testing and benchmarking
- Code coverage and quality metrics
- Test automation and CI/CD integration

### Infrastructure & Networking
- Load balancers and reverse proxies
- CDN configuration and optimization
- Network protocols (HTTP/2, WebSockets, gRPC)
- Service mesh and API gateways
- Monitoring and observability

### Modern Frontend
- State management (Redux, MobX, Zustand, Recoil)
- Server-side rendering and static generation
- Progressive Web Apps and service workers
- WebAssembly integration
- Micro-frontends architecture

## Validation Checklist

Before outputting each sample, verify:

✅ **Query Quality**
- Natural developer question
- Different from typical Batch 1 patterns
- Grammatically correct

✅ **Score Consistency**
- View scores correlate (0.6-0.9)
- Expected complexity within ±0.05 of view average
- Appropriate for designated range

✅ **Feature Accuracy**
- Features match query content
- Values within medium complexity ranges
- Consistent relationships

✅ **Topic Diversity**
- Covers Batch 2 focus areas
- Avoids overlap with typical Batch 1 topics
- Varied technical domains

✅ **Reasoning Quality**
- References specific query elements
- Justifies complexity assessment
- Technical accuracy

## Output Instructions

Generate exactly 25 samples in a JSON array:
```json
[
  { /* Sample 1 - boundary (0.32-0.40) - Data/Mobile focus */ },
  { /* Sample 2 - boundary (0.32-0.40) - Testing focus */ },
  { /* Sample 3 - boundary (0.32-0.40) - Infrastructure focus */ },
  { /* Sample 4 - boundary (0.32-0.40) - Frontend focus */ },
  { /* Sample 5 - boundary (0.32-0.40) - Mixed focus */ },
  { /* Samples 6-20 - clear medium (0.41-0.55) - Various Batch 2 topics */ },
  { /* Sample 21 - boundary (0.56-0.66) - Advanced data engineering */ },
  { /* Sample 22 - boundary (0.56-0.66) - Complex mobile architecture */ },
  { /* Sample 23 - boundary (0.56-0.66) - Sophisticated testing */ },
  { /* Sample 24 - boundary (0.56-0.66) - Infrastructure at scale */ },
  { /* Sample 25 - boundary (0.56-0.66) - Advanced frontend patterns */ }
]
```

Ensure:
1. Focus on Batch 2 specific topics (data, mobile, testing, infrastructure, modern frontend)
2. Natural progression in complexity
3. Different question patterns from typical web/backend focus
4. Consistent quality throughout
5. Realistic developer concerns in these domains

Begin generation now, maintaining high quality throughout all 25 samples.