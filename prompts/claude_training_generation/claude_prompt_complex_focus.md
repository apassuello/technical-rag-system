# Claude Training Data Generation Prompt - Complex Complexity Focus

## System Context

You are an expert in query complexity analysis and machine learning data generation. You will generate high-quality training data for a multi-view ML system that analyzes query complexity across 5 orthogonal dimensions:

1. **Technical Complexity**: Domain-specific terminology, jargon, technical depth
2. **Linguistic Complexity**: Sentence structure, vocabulary, readability  
3. **Task Complexity**: Cognitive load based on Bloom's taxonomy (Knowledge, Comprehension, Application, Analysis, Synthesis, Evaluation)
4. **Semantic Complexity**: Conceptual relationships, abstraction level, implicit knowledge
5. **Computational Complexity**: Algorithm mentions, implementation difficulty, optimization aspects

Your task is to generate **50 training samples focused on COMPLEX complexity** with realistic queries representing advanced technical challenges and detailed complexity assessments across all 5 views.

## Critical Requirements

1. **Expert-Level Queries**: All queries must represent genuine challenges faced by senior engineers, architects, and researchers
2. **Advanced Technical Depth**: Queries should assume significant background knowledge and expertise
3. **Multi-Domain Integration**: Complex queries often span multiple technical domains
4. **Score Calibration**: Maintain consistent scoring within the complex range
5. **Feature Accuracy**: All numerical features must be derivable from the query text
6. **View Correlation**: Views should correlate (0.6-0.9) but not be identical
7. **Detailed Reasoning**: Provide clear explanations referencing specific complexity factors

## Target Distribution for This Batch

Generate exactly 50 samples with this distribution:
- **10 samples**: Complex-medium boundary (0.64-0.72 overall complexity)
- **40 samples**: Clearly complex (0.73-0.90 overall complexity)

## Complex Query Guidelines

Generate **authentic expert-level queries** that represent genuine challenges faced by senior engineers, architects, and researchers. Focus on cutting-edge problems requiring deep expertise.

### Complexity Indicators for Complex Queries:
- **Technical Complexity**: Advanced concepts, multiple intersecting domains, cutting-edge technology
- **Cognitive Demand**: Synthesis, evaluation, creation (Bloom's levels 4-6)
- **User Context**: Senior engineers, architects, researchers, specialists
- **Answer Scope**: Novel solutions, research-level analysis, system-wide implications

### Encourage Authentic Expert Diversity:
- **Real Expert Problems**: Focus on challenges that actually require deep expertise
- **Natural Language**: Use precise technical language that experts actually use
- **Genuine Complexity**: Each query should represent a genuinely difficult technical challenge

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

## Scoring Guidelines for Complex Queries

### View Score Ranges for Complex Queries:
- **Technical (0.60-0.95)**: Highly specialized terminology, expert-level concepts, multiple domain integration
- **Linguistic (0.50-0.85)**: Complex multi-clause sentences, sophisticated vocabulary, formal technical discourse
- **Task (0.60-0.95)**: Bloom's Level 4-6 (Analysis/Synthesis/Evaluation), many solution steps, high creativity
- **Semantic (0.60-0.95)**: Dense conceptual relationships, high abstraction, extensive implicit knowledge
- **Computational (0.55-0.95)**: Advanced algorithms, NP-hard problems, expert implementation challenges

### How to Score Each View:
1. **Technical**: Count advanced technical terms, assess expertise required, evaluate multi-domain integration
2. **Linguistic**: Analyze sentence complexity (20-60+ words), nested structures, abstract language
3. **Task**: Identify Bloom's level (Synthesis/Evaluation), assess cognitive load, count solution steps (6-15+)
4. **Semantic**: Evaluate concept density, abstraction level, theoretical depth, implicit knowledge
5. **Computational**: Consider algorithm complexity, formal methods, optimization challenges, scale requirements

**Key Principle**: All view scores should correlate (0.6-0.9 correlation) and average to approximately the expected_complexity_score.

## Example Samples for Calibration

### Example 1: Complex-Medium Boundary (Score: 0.68)
```json
{
  "query_text": "How can I implement a distributed consensus algorithm with Byzantine fault tolerance that maintains linearizability while optimizing for network partition recovery?",
  "expected_complexity_score": 0.68,
  "expected_complexity_level": "complex",
  "view_scores": {
    "technical": 0.72,
    "linguistic": 0.62,
    "task": 0.71,
    "semantic": 0.69,
    "computational": 0.68
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

**Analysis**: Distributed consensus with Byzantine tolerance. Technical (0.72) - advanced distributed systems theory. Linguistic (0.62) - complex technical precision. Task (0.71) - Bloom's Level 5 synthesis. Semantic (0.69) - high conceptual density. Computational (0.68) - complex distributed algorithms.

### Example 2: Clearly Complex (Score: 0.81)
```json
{
  "query_text": "What are the theoretical and practical implications of implementing a CRDT-based eventually consistent data store with causal consistency guarantees for a globally distributed collaborative editing system handling millions of concurrent operations with sub-100ms conflict resolution?",
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

**Analysis**: CRDT-based distributed systems. Technical (0.86) - cutting-edge distributed research. Linguistic (0.75) - highly complex sentence. Task (0.84) - Bloom's Level 6 evaluation. Semantic (0.82) - extreme conceptual density. Computational (0.80) - advanced algorithms with performance constraints.

### Example 3: High Complex (Score: 0.87)
```json
{
  "query_text": "How would you architect a quantum-resistant cryptographic protocol for secure multi-party computation that maintains zero-knowledge properties while enabling homomorphic operations on encrypted data at petabyte scale with provable security guarantees against both classical and quantum adversaries?",
  "expected_complexity_score": 0.87,
  "expected_complexity_level": "complex",
  "view_scores": {
    "technical": 0.92,
    "linguistic": 0.80,
    "task": 0.90,
    "semantic": 0.88,
    "computational": 0.86
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

**Analysis**: Quantum-resistant cryptography. Technical (0.92) - cutting-edge cryptographic research. Linguistic (0.80) - extremely complex multi-clause. Task (0.90) - Bloom's Level 6 synthesis. Semantic (0.88) - maximum conceptual complexity. Computational (0.86) - novel algorithms with formal verification.

## Expert-Level Topic Areas to Draw From

### Distributed Systems & Architecture
- Consensus algorithms, consistency models, fault tolerance
- Event sourcing, CQRS, microservices decomposition
- Service mesh architecture, observability systems

### Advanced Algorithms & Data Structures  
- NP-hard problem approximation, parallel algorithms
- Persistent data structures, cache-oblivious design
- Graph algorithms for large-scale networks

### Security & Cryptography
- Zero-knowledge proofs, homomorphic encryption
- Post-quantum cryptography, secure multi-party computation
- Side-channel attack mitigation

### Performance & Scale
- Performance modeling, NUMA-aware programming  
- Network optimization, memory management
- Hardware acceleration (GPUs, FPGAs, ASICs)

### Machine Learning Systems
- Distributed training, model serving at scale
- Online learning, federated systems
- Model compression and quantization

### Formal Methods & Verification
- Model checking, theorem proving
- Static analysis, correctness proofs
- Contract-based design

## Quality Focus

**Primary Goal**: Generate authentic expert-level queries that represent genuine challenges requiring deep technical expertise

✅ **Expert Language Priority**
- Each query should use precise, advanced technical terminology
- Represent problems that actually require expert-level knowledge
- Use natural phrasing that senior practitioners would actually use

✅ **Authentic High Complexity**
- Ensure queries genuinely require advanced expertise (0.64-0.90)
- Focus on multi-domain problems, novel challenges, research-level questions
- View scores should naturally reflect the high complexity

✅ **Maximum Diversity**
- Every query should represent a unique expert challenge
- Draw from various cutting-edge technical domains
- Think like different senior experts with different specializations

## Output Instructions

**Generate 50 unique, authentic expert-level queries as a JSON array.**

**Key Requirements**:
- 10 samples in 0.64-0.72 range (complex-medium boundary)
- 40 samples in 0.73-0.90 range (clearly complex)
- Each query must represent a genuine expert-level challenge
- Focus on problems that require deep technical knowledge and experience

**Creative Freedom**: Generate diverse, authentic queries that truly represent expert-level technical challenges without following rigid patterns. Focus on real problems that senior engineers, architects, and researchers actually face.

Begin generation now, prioritizing authenticity and expert-level technical depth.