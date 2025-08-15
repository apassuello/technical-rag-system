# Claude Training Data Generation Prompt - Medium Complexity Focus (Batch 2)


## System Context

You are an expert in query complexity analysis and machine learning data generation. You will generate high-quality training data for a multi-view ML system that analyzes query complexity across 5 orthogonal dimensions:

1. **Technical Complexity**: Domain-specific terminology, jargon, technical depth
2. **Linguistic Complexity**: Sentence structure, vocabulary, readability  
3. **Task Complexity**: Cognitive load based on Bloom's taxonomy (Knowledge, Comprehension, Application, Analysis, Synthesis, Evaluation)
4. **Semantic Complexity**: Conceptual relationships, abstraction level, implicit knowledge
5. **Computational Complexity**: Algorithm mentions, implementation difficulty, optimization aspects

Your task is to generate **25 training samples focused on MEDIUM complexity** with realistic queries and detailed complexity assessments across all 5 views. This is the SECOND batch of medium complexity samples, so ensure variety from typical patterns.

## Medium Query Guidelines (Batch 2 Focus)

Generate **authentic medium-complexity queries** with emphasis on different technical domains than Batch 1. Focus on real-world scenarios representing genuine developer challenges.

### Complexity Indicators for Medium Queries:
- **Technical Complexity**: Intermediate concepts, specialized tools, cross-platform concerns
- **Cognitive Demand**: Application, analysis, evaluation (Bloom's levels 3-4)  
- **User Context**: Developers working with diverse tech stacks and deployment scenarios
- **Answer Scope**: Multi-component solutions, platform-specific implementations, integration challenges

## Critical Requirements

1. **Natural Language**: All queries must sound like genuine user questions - grammatically correct, conversational, and realistic
2. **Score Calibration**: Maintain consistent scoring within the medium range with boundary samples at both ends
3. **Feature Accuracy**: All numerical features must be derivable from the query text
4. **View Correlation**: Views should correlate (0.6-0.9) but not be identical
5. **Detailed Reasoning**: Provide clear explanations for each score
6. **Diversity from Batch 1**: Focus on different technical areas and question patterns

## Target Distribution for This Batch

Generate exactly 50 samples with this distribution:
- **5 samples**: Medium-simple boundary (0.32-0.40 overall complexity)
- **35 samples**: Clearly medium (0.41-0.55 overall complexity)
- **10 samples**: Medium-complex boundary (0.56-0.66 overall complexity)

### Batch 2 Domain Inspiration (diversify naturally):
- **Data Engineering**: ETL processes, data pipelines, analytics platforms  
- **Mobile Development**: Cross-platform challenges, native vs hybrid approaches
- **Infrastructure**: Cloud deployment, monitoring, scalability concerns
- **Testing & Quality**: Testing strategies, automation, quality assurance
- **Modern Patterns**: State management, serverless, microservices

### Encourage Natural Diversity:
- **Real Development Scenarios**: Focus on actual problems developers encounter
- **Authentic Language**: Use terminology and phrasing that actual developers use  
- **Varied Complexity**: Natural range across the medium complexity spectrum

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
    "technical": 0.40,
    "linguistic": 0.33,
    "task": 0.37,
    "semantic": 0.35,
    "computational": 0.36
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

**Analysis**: ETL optimization question. Technical (0.40) - ETL and memory management concepts. Linguistic (0.33) - clear technical question. Task (0.37) - Bloom's Level 3 application. Semantic (0.35) - data flow and constraints. Computational (0.36) - memory optimization strategies.

### Example 2: Clear Medium (Score: 0.49) - Mobile Development Focus
```json
{
  "query_text": "What's the best strategy for managing state between native modules and React Native JavaScript code in a hybrid mobile app?",
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

**Analysis**: Cross-platform state management. Technical (0.53) - native bridge concepts. Linguistic (0.45) - complex multi-layer question. Task (0.51) - Bloom's Level 4 analysis. Semantic (0.48) - runtime environment interactions. Computational (0.48) - state synchronization patterns.

### Example 3: Medium-Complex Boundary (Score: 0.64) - Testing & Quality Focus
```json
{
  "query_text": "How do I implement contract testing for microservices with consumer-driven contracts while maintaining backward compatibility during API evolution?",
  "expected_complexity_score": 0.64,
  "expected_complexity_level": "medium",
  "view_scores": {
    "technical": 0.67,
    "linguistic": 0.60,
    "task": 0.66,
    "semantic": 0.63,
    "computational": 0.65
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

**Analysis**: Contract testing architecture. Technical (0.67) - advanced testing patterns. Linguistic (0.60) - complex multi-clause sentence. Task (0.66) - Bloom's Level 5 synthesis. Semantic (0.63) - multiple interrelated concepts. Computational (0.65) - contract validation algorithms.

## Domain and Query Type Distribution for Batch 2

### Domains (distribute naturally across samples):
- **Technical** (28 samples): System integration, software development, infrastructure
- **Academic** (14 samples): Computer science theory, algorithms, formal methods
- **General** (8 samples): Development tools, practices, ecosystem integration

### Query Types (distribute naturally across samples):
- **implementation**: "How to implement X?", "Build Y system?"
- **troubleshooting**: "Debug X issue?", "Fix Y problem?"
- **optimization**: "Optimize system for Y?", "Improve X performance?"
- **architecture**: "Design system for X?", "Best approach for Y?"
- **comparison**: "Implementation X vs Y?", "Tool A vs B?"

### Computer Architecture & Systems Topic Areas for Medium Queries (Batch 2):
- Operating system kernel development
- System security and trusted execution
- Hardware debugging and analysis tools
- Formal verification methodologies
- System firmware and bootloaders
- Real-time and embedded systems
- System compliance and testing
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

**Generate 50 unique, authentic medium-complexity queries as a JSON array.**

**Key Requirements**:
- 5 samples in 0.32-0.40 range (medium-simple boundary)
- 35 samples in 0.41-0.55 range (clearly medium)
- 10 samples in 0.56-0.66 range (medium-complex boundary)
- Each query must represent a genuine developer scenario
- Emphasize different domains from Batch 1 (data, mobile, testing, infrastructure)

**Creative Freedom**: Generate diverse, authentic queries representing real medium-complexity challenges without following rigid patterns. Focus on genuine developer problems and authentic technical language.

Begin generation now, prioritizing authenticity and domain diversity.