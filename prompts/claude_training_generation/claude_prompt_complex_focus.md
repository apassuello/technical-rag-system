# Claude Training Data Generation Prompt - Complex Complexity Focus

## 📝 **EASY TOPIC MODIFICATION GUIDE**

**🎯 Current Focus**: RISC-V Architecture and Development (Complex/Expert Level)


**Instructions**: Focus 80-90% of queries on the chosen advanced topic, with 10-20% related expert-level concepts.

## System Context

You are an expert in query complexity analysis and machine learning data generation. You will generate high-quality training data for a multi-view ML system that analyzes query complexity across 5 orthogonal dimensions:

1. **Technical Complexity**: Domain-specific terminology, jargon, technical depth
2. **Linguistic Complexity**: Sentence structure, vocabulary, readability  
3. **Task Complexity**: Cognitive load based on Bloom's taxonomy (Knowledge, Comprehension, Application, Analysis, Synthesis, Evaluation)
4. **Semantic Complexity**: Conceptual relationships, abstraction level, implicit knowledge
5. **Computational Complexity**: Algorithm mentions, implementation difficulty, optimization aspects

Your task is to generate **25 training samples focused on COMPLEX complexity** with realistic queries representing advanced technical challenges and detailed complexity assessments across all 5 views.

## 🎯 **TOPIC FOCUS FOR THIS BATCH**

**Primary Topic**: RISC-V Architecture and Development (Complex/Expert Level)

Generate queries related to:
- **RISC-V Research**: Novel ISA extensions, microarchitecture innovations, emerging paradigms
- **RISC-V Compiler Research**: Advanced optimizations, novel code generation, ISA co-design
- **RISC-V System Architecture**: Heterogeneous computing, accelerator integration, coherency protocols
- **RISC-V Verification**: Formal ISA specification, advanced testing methodologies, coverage analysis
- **RISC-V Ecosystem**: Industry adoption challenges, standardization issues, competitive analysis

**Important**: Focus on cutting-edge research questions, novel technical challenges, and expert-level architectural decisions.

## Critical Requirements

1. **Expert-Level Queries**: All queries must represent genuine challenges faced by senior engineers, architects, and researchers
2. **Advanced Technical Depth**: Queries should assume significant background knowledge and expertise
3. **Multi-Domain Integration**: Complex queries often span multiple technical domains
4. **Score Calibration**: Maintain consistent scoring within the complex range
5. **Feature Accuracy**: All numerical features must be derivable from the query text
6. **View Correlation**: Views should correlate (0.6-0.9) but not be identical
7. **Detailed Reasoning**: Provide clear explanations referencing specific complexity factors

## Target Distribution for This Batch

Generate exactly 25 samples with this distribution:
- **5 samples**: Complex-medium boundary (0.64-0.72 overall complexity)
- **20 samples**: Clearly complex (0.73-0.90 overall complexity)

## Complex Query Characteristics

### Complex-Medium Boundary (0.64-0.72)
- **Query Length**: 20-40 words
- **Vocabulary**: Advanced technical terminology with some domain specialization
- **Technical Terms**: 5-10 technical terms
- **Task Type**: System design, performance optimization, complex debugging
- **Cognitive Level**: Bloom's 4-5 (Analysis, Synthesis)
- **Examples**: "How do I implement distributed transaction coordination with two-phase commit across multiple databases while handling network partitions?"

### Clearly Complex (0.73-0.90)
- **Query Length**: 25-60+ words
- **Vocabulary**: Highly specialized, expert-level terminology
- **Technical Terms**: 8-15+ technical terms
- **Task Type**: Novel system architecture, research-level problems, cutting-edge optimization
- **Cognitive Level**: Bloom's 5-6 (Synthesis, Evaluation)
- **Examples**: "What are the theoretical and practical trade-offs between implementing a Byzantine fault-tolerant consensus algorithm like PBFT versus Raft for a globally distributed blockchain system with millions of transactions per second?"

## JSON Structure for Each Sample

**CRITICAL: Use this EXACT structure to match existing training infrastructure:**

```json
{
  "query_text": "Advanced, expert-level technical question",
  "expected_complexity_score": 0.81,
  "expected_complexity_level": "complex",
  "view_scores": {
    "technical": 0.86,
    "linguistic": 0.75,
    "task": 0.84,
    "semantic": 0.82,
    "computational": 0.80
  },
  "confidence": 0.82,
  "metadata": {
    "domain": "research",
    "query_type": "evaluation",
    "generation_timestamp": "2025-08-07T20:00:00Z",
    "base_score": 0.81,
    "template_used": "none - natural generation"
  }
}
```

**IMPORTANT**: 
- `view_scores` contains ONLY simple float values (0.0-1.0), not complex objects
- Each view name must be exactly: "technical", "linguistic", "task", "semantic", "computational"
- All scores should be in the complex range: 0.64-0.90 for expected_complexity_score
- View scores can vary but should correlate with expected score

## Feature Value Guidelines for Complex Queries

### Technical View Features (Advanced Level)
- **technical_terms_count**: 5-15+ (algorithms, protocols, architectures, formal methods)
- **domain_specificity_score**: 0.6-0.95 (highly specialized knowledge required)
- **jargon_density**: 0.3-0.6 (dense technical terminology)
- **concept_depth**: 3-5 (deep expertise, multiple layers of abstraction)
- **passive_voice_ratio**: Often higher in formal technical discourse

### Linguistic View Features (Sophisticated Language)
- **avg_sentence_length**: 20-60+ words (complex multi-clause constructions)
- **syntactic_depth**: 3-5 (deeply nested structures)
- **clause_complexity**: 0.4-0.8 (multiple subordinate clauses)
- **abstract_concept_ratio**: 0.3-0.7 (high abstraction, theoretical concepts)
- **lexical_diversity**: 0.6-0.9 (rich, varied vocabulary)

### Task View Features (Expert Cognitive Demands)
- **primary_bloom_level**: 4-6 (Analysis, Synthesis, Evaluation)
- **cognitive_load**: 0.6-0.95 (high mental effort, expert thinking)
- **task_scope**: 0.6-0.95 (broad, multi-faceted challenges)
- **solution_steps**: 6-15+ (complex multi-stage processes)
- **creativity_required**: 0.4-0.8 (novel solutions, original thinking)

### Semantic View Features (High Conceptual Complexity)
- **concept_density**: 0.6-0.95 (many interrelated concepts)
- **relationship_complexity**: 0.6-0.95 (complex interdependencies)
- **abstraction_level**: 3-5 (highly abstract, theoretical)
- **context_dependency**: 0.6-0.9 (requires extensive domain context)
- **implicit_knowledge**: 0.5-0.85 (assumes expert background)

### Computational View Features (Advanced Algorithms/Systems)
- **algorithm_mentions**: 1-8 (complex algorithms, formal methods)
- **complexity_class**: 0.5-0.95 (NP-hard, distributed consensus, etc.)
- **data_structure_count**: 1-6 (sophisticated data structures)
- **implementation_difficulty**: 0.6-0.95 (expert-level coding challenges)
- **optimization_aspects**: 0.5-0.9 (advanced performance considerations)

## Example Samples for Calibration

### Example 1: Complex-Medium Boundary (Score: 0.68)
```json
{
  "query_text": "How can I implement a distributed consensus algorithm with Byzantine fault tolerance that maintains linearizability while optimizing for network partition recovery?",
  "expected_complexity_score": 0.68,
  "expected_complexity_level": "complex",
  "view_scores": {
    "technical": {
      "complexity_score": 0.72,
      "confidence": 0.85,
      "reasoning": "Advanced distributed systems concepts: Byzantine fault tolerance, linearizability, consensus algorithms. Requires deep understanding of distributed systems theory.",
      "feature_values": {
        "technical_terms_count": 7,
        "domain_specificity_score": 0.75,
        "jargon_density": 0.35,
        "concept_depth": 4,
        "passive_voice_ratio": 0.1
      }
    },
    "linguistic": {
      "complexity_score": 0.62,
      "confidence": 0.87,
      "reasoning": "Technical precision with multiple specialized terms. Complex but structured sentence with clear relationships.",
      "feature_values": {
        "avg_sentence_length": 24.0,
        "syntactic_depth": 3,
        "clause_complexity": 0.5,
        "abstract_concept_ratio": 0.45,
        "lexical_diversity": 0.83
      }
    },
    "task": {
      "complexity_score": 0.71,
      "confidence": 0.83,
      "reasoning": "Bloom's Level 5 (Synthesis) - combining multiple advanced concepts into a novel implementation considering trade-offs.",
      "feature_values": {
        "primary_bloom_level": 5,
        "cognitive_load": 0.72,
        "task_scope": 0.75,
        "solution_steps": 10,
        "creativity_required": 0.6
      }
    },
    "semantic": {
      "complexity_score": 0.69,
      "confidence": 0.84,
      "reasoning": "High conceptual density with complex relationships between fault tolerance, consistency models, and performance optimization.",
      "feature_values": {
        "concept_density": 0.7,
        "relationship_complexity": 0.75,
        "abstraction_level": 4,
        "context_dependency": 0.7,
        "implicit_knowledge": 0.65
      }
    },
    "computational": {
      "complexity_score": 0.68,
      "confidence": 0.86,
      "reasoning": "Complex distributed algorithms, consensus protocols, Byzantine agreement. High implementation complexity with formal correctness requirements.",
      "feature_values": {
        "algorithm_mentions": 3,
        "complexity_class": 0.75,
        "data_structure_count": 2,
        "implementation_difficulty": 0.7,
        "optimization_aspects": 0.65
      }
    }
  },
  "confidence": 0.85,
  "metadata": {
    "domain": "academic",
    "query_type": "architecture",
    "generation_timestamp": "2025-08-07T20:00:00Z",
    "base_score": 0.68,
    "template_used": "none - natural generation"
  }
}
```

### Example 2: Clearly Complex (Score: 0.81)
```json
{
  "query_text": "What are the theoretical and practical implications of implementing a CRDT-based eventually consistent data store with causal consistency guarantees for a globally distributed collaborative editing system handling millions of concurrent operations with sub-100ms conflict resolution?",
  "expected_complexity_score": 0.81,
  "expected_complexity_level": "complex",
  "view_scores": {
    "technical": {
      "complexity_score": 0.86,
      "confidence": 0.82,
      "reasoning": "Cutting-edge distributed systems research combining CRDTs, consistency models, collaborative editing algorithms, and global-scale performance requirements.",
      "feature_values": {
        "technical_terms_count": 12,
        "domain_specificity_score": 0.88,
        "jargon_density": 0.45,
        "concept_depth": 5,
        "passive_voice_ratio": 0.0
      }
    },
    "linguistic": {
      "complexity_score": 0.75,
      "confidence": 0.84,
      "reasoning": "Highly technical language with precise terminology. Long, complex sentence requiring careful parsing of multiple related concepts.",
      "feature_values": {
        "avg_sentence_length": 38.0,
        "syntactic_depth": 4,
        "clause_complexity": 0.65,
        "abstract_concept_ratio": 0.55,
        "lexical_diversity": 0.84
      }
    },
    "task": {
      "complexity_score": 0.84,
      "confidence": 0.81,
      "reasoning": "Bloom's Level 6 (Evaluation) - evaluating theoretical foundations against practical implementation challenges across multiple dimensions.",
      "feature_values": {
        "primary_bloom_level": 6,
        "cognitive_load": 0.85,
        "task_scope": 0.9,
        "solution_steps": 12,
        "creativity_required": 0.75
      }
    },
    "semantic": {
      "complexity_score": 0.82,
      "confidence": 0.82,
      "reasoning": "Extremely high conceptual density with complex theoretical and practical relationships. Multiple layers of abstraction from theory to implementation.",
      "feature_values": {
        "concept_density": 0.85,
        "relationship_complexity": 0.88,
        "abstraction_level": 5,
        "context_dependency": 0.85,
        "implicit_knowledge": 0.8
      }
    },
    "computational": {
      "complexity_score": 0.80,
      "confidence": 0.83,
      "reasoning": "Advanced algorithms: CRDTs, operational transformation, vector clocks, distributed consensus. Extreme performance constraints with correctness guarantees.",
      "feature_values": {
        "algorithm_mentions": 5,
        "complexity_class": 0.8,
        "data_structure_count": 4,
        "implementation_difficulty": 0.85,
        "optimization_aspects": 0.82
      }
    }
  },
  "confidence": 0.82,
  "metadata": {
    "domain": "research",
    "query_type": "evaluation",
    "generation_timestamp": "2025-08-07T20:00:00Z",
    "base_score": 0.81,
    "template_used": "none - natural generation"
  }
}
```

### Example 3: High Complex (Score: 0.87)
```json
{
  "query_text": "How would you architect a quantum-resistant cryptographic protocol for secure multi-party computation that maintains zero-knowledge properties while enabling homomorphic operations on encrypted data at petabyte scale with provable security guarantees against both classical and quantum adversaries?",
  "expected_complexity_score": 0.87,
  "expected_complexity_level": "complex",
  "view_scores": {
    "technical": {
      "complexity_score": 0.92,
      "confidence": 0.78,
      "reasoning": "Cutting-edge cryptography combining quantum resistance, zero-knowledge proofs, homomorphic encryption, and secure multi-party computation at massive scale.",
      "feature_values": {
        "technical_terms_count": 15,
        "domain_specificity_score": 0.95,
        "jargon_density": 0.52,
        "concept_depth": 5,
        "passive_voice_ratio": 0.15
      }
    },
    "linguistic": {
      "complexity_score": 0.80,
      "confidence": 0.81,
      "reasoning": "Extremely technical language with precise mathematical and cryptographic terminology. Very long sentence with multiple dependent clauses.",
      "feature_values": {
        "avg_sentence_length": 45.0,
        "syntactic_depth": 5,
        "clause_complexity": 0.75,
        "abstract_concept_ratio": 0.65,
        "lexical_diversity": 0.87
      }
    },
    "task": {
      "complexity_score": 0.90,
      "confidence": 0.79,
      "reasoning": "Bloom's Level 6 (Evaluation) - requires synthesizing cutting-edge research across multiple domains with formal security analysis.",
      "feature_values": {
        "primary_bloom_level": 6,
        "cognitive_load": 0.92,
        "task_scope": 0.95,
        "solution_steps": 15,
        "creativity_required": 0.85
      }
    },
    "semantic": {
      "complexity_score": 0.88,
      "confidence": 0.80,
      "reasoning": "Maximum conceptual complexity with highly abstract mathematical relationships across cryptography, quantum computing, and distributed systems.",
      "feature_values": {
        "concept_density": 0.9,
        "relationship_complexity": 0.92,
        "abstraction_level": 5,
        "context_dependency": 0.9,
        "implicit_knowledge": 0.88
      }
    },
    "computational": {
      "complexity_score": 0.86,
      "confidence": 0.82,
      "reasoning": "Novel algorithms in post-quantum cryptography, zero-knowledge proofs, homomorphic encryption. Extreme computational complexity with formal verification requirements.",
      "feature_values": {
        "algorithm_mentions": 7,
        "complexity_class": 0.9,
        "data_structure_count": 5,
        "implementation_difficulty": 0.9,
        "optimization_aspects": 0.85
      }
    }
  },
  "confidence": 0.80,
  "metadata": {
    "domain": "research",
    "query_type": "synthesis",
    "generation_timestamp": "2025-08-07T20:00:00Z",
    "base_score": 0.87,
    "template_used": "none - natural generation"
  }
}
```

## Expert-Level Topic Areas to Cover

### Distributed Systems & Architecture
- Consensus algorithms (Paxos, Raft, PBFT, HotStuff)
- CAP theorem implications and consistency models
- Event sourcing and CQRS at scale
- Service mesh architecture and observability
- Microservices decomposition strategies

### Advanced Algorithms & Data Structures
- Approximate algorithms for NP-hard problems
- Persistent and functional data structures
- Cache-oblivious algorithms
- Parallel and lock-free algorithms
- Graph algorithms for large-scale networks

### Security & Cryptography
- Zero-knowledge proofs and applications
- Homomorphic encryption schemes
- Post-quantum cryptography
- Secure multi-party computation
- Side-channel attack mitigation

### Performance & Scale
- Performance modeling and capacity planning
- NUMA-aware programming
- Network optimization (DPDK, RDMA)
- Memory management and garbage collection
- Hardware acceleration (GPUs, FPGAs, ASICs)

### Machine Learning Systems
- Distributed training algorithms
- Model serving at scale
- Online learning and adaptation
- Federated learning systems
- ML model compression and quantization

### Formal Methods & Verification
- TLA+ specifications for distributed systems
- Model checking and theorem proving
- Contract-based design
- Static analysis at scale
- Correctness proofs for concurrent algorithms

## Domain and Query Type Distribution

### Domains (distribute across samples):
- **Research** (10 samples): RISC-V ISA research, microarchitecture innovation
- **Technical** (10 samples): Advanced RISC-V system design, compiler research
- **Academic** (5 samples): Formal methods, theoretical computer architecture

### Query Types (distribute across samples):
- **research** (8 samples): "What are the implications of X?", "How to advance Y?"
- **architecture** (6 samples): "Design novel RISC-V system for X?", "Architect Y solution?"
- **evaluation** (5 samples): "Evaluate trade-offs between X and Y?", "Compare approaches?"
- **synthesis** (4 samples): "Combine X with Y for Z?", "Integrate multiple techniques?"
- **optimization** (2 samples): "Optimize for extreme constraints?", "Achieve theoretical limits?"

### RISC-V Topic Areas for Complex Queries:
- Novel ISA extension design and evaluation
- Advanced microarchitecture research
- Heterogeneous RISC-V system architectures
- Compiler-architecture co-design
- Formal ISA specification and verification
- RISC-V ecosystem standardization challenges
- Advanced security architecture research
- Performance modeling and prediction
- Accelerator integration and coherency
- Industry adoption and competitive analysis

## Validation Checklist

Before outputting each sample, verify:

✅ **Expert-Level Quality**
- Represents genuine challenges for senior engineers/researchers
- Uses precise, advanced technical terminology
- Assumes significant background knowledge

✅ **Complexity Calibration**
- View scores appropriately high (0.60-0.95 range)
- Boundary samples properly positioned
- Clear progression in complexity

✅ **Technical Accuracy**
- All technical concepts are real and current
- Feature values match query complexity
- Reasoning demonstrates deep understanding

✅ **Cognitive Demands**
- Requires Bloom's levels 4-6 thinking
- Multiple solution steps
- High creativity/originality requirements

✅ **Multi-Domain Integration**
- Complex queries often span multiple areas
- Shows interconnections between concepts
- Demonstrates systems thinking

## Output Instructions

Generate exactly 25 samples in a JSON array:
```json
[
  { /* Sample 1 - boundary (0.64-0.72) - Distributed systems */ },
  { /* Sample 2 - boundary (0.64-0.72) - Performance optimization */ },
  { /* Sample 3 - boundary (0.64-0.72) - Security */ },
  { /* Sample 4 - boundary (0.64-0.72) - ML systems */ },
  { /* Sample 5 - boundary (0.64-0.72) - Algorithms */ },
  { /* Samples 6-25 - clearly complex (0.73-0.90) - Various expert topics */ }
]
```

Ensure:
1. All queries represent expert-level challenges
2. Natural progression from boundary to highly complex
3. Diverse coverage of advanced technical domains
4. Realistic problems faced by senior practitioners
5. Consistent high quality throughout all samples
6. Precise technical language and concepts

Begin generation now, maintaining expert-level quality throughout all 25 samples.