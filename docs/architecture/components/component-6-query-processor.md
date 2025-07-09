# Component 6: Query Processor

**Component ID**: C6  
**Version**: 1.0  
**References**: [MASTER-ARCHITECTURE.md](./MASTER-ARCHITECTURE.md)  
**Related Components**: [C4-Retriever](./COMPONENT-4-RETRIEVER.md), [C5-Answer Generator](./COMPONENT-5-ANSWER-GENERATOR.md)

---

## 1. Component Overview

### 1.1 Purpose & Responsibility

The Query Processor orchestrates the **query execution workflow**:
- Analyze and understand user queries
- Coordinate retrieval and generation
- Select optimal context for generation
- Assemble final responses

### 1.2 Position in System

**Workflow Coordinator**: Between retrieval and generation
- **Input**: User queries from Platform Orchestrator
- **Output**: Complete answers with sources

### 1.3 Key Design Decisions

1. **Workflow Orchestration**: Manages the RAG pipeline
2. **Intelligent Context Selection**: Optimize for relevance and diversity
3. **Response Assembly**: Consistent output format

---

## 2. Requirements

### 2.1 Functional Requirements

**Core Capabilities**:
- FR1: Analyze query intent and complexity
- FR2: Execute retrieval with appropriate parameters
- FR3: Select best context within token limits
- FR4: Coordinate answer generation
- FR5: Assemble responses with metadata

**Interface Contracts**: See [Query Processor Interface](./rag-interface-reference.md#2-main-component-interfaces)

**Behavioral Specifications**:
- Must handle queries of varying complexity
- Must optimize context for answer quality
- Must provide consistent response format

### 2.2 Quality Requirements

**Performance**:
- Query analysis: <50ms
- Context selection: <100ms
- Total overhead: <200ms

**Reliability**:
- Handle all query types gracefully
- Recover from component failures
- Consistent result quality

**Scalability**:
- Process concurrent queries
- Handle varying context sizes
- Support query routing

---

## 3. Architecture Design

### 3.1 Internal Structure

```
Query Processor
├── Query Analyzer (sub-component)
├── Context Selector (sub-component)
├── Response Assembler (sub-component)
└── Workflow Engine
```

### 3.2 Sub-Components

**Query Analyzer**:
- **Purpose**: Understand query characteristics
- **Implementation**: Direct implementation mostly
- **Decision**: NLP algorithms, possible LLM adapter
- **Variants**: NLP-based, LLM-based, Rule-based

**Context Selector**:
- **Purpose**: Choose optimal documents for generation
- **Implementation**: Direct implementation
- **Decision**: Selection algorithms
- **Variants**: MMR, Diversity, Token-optimized

**Response Assembler**:
- **Purpose**: Format final response
- **Implementation**: Direct implementation
- **Decision**: Formatting logic
- **Variants**: Standard, Rich, Streaming

### 3.3 Adapter vs Direct

**Uses Adapters For**:
- External NLP services (if used)
- LLM-based query analysis

**Direct Implementation For**:
- Context selection algorithms
- Response assembly logic
- Workflow orchestration

### 3.4 State Management

**Stateless Processing**:
- Each query processed independently
- No conversation history
- Workflow state temporary

---

## 4. Interfaces

### 4.1 Provided Interfaces

See [Query Processor Sub-component Interfaces](./rag-interface-reference.md#2-main-component-interfaces)

**Main Interface**:
- `process(query, options) -> Answer`
- `analyze_query(query) -> QueryAnalysis`
- `select_context(results, max_tokens) -> List[Document]`

### 4.2 Required Interfaces

- Retriever for document search
- Answer Generator for response creation

### 4.3 Events Published

- Query processing started/completed
- Retrieval executed
- Context selected
- Generation requested

---

## 5. Design Rationale

### Architectural Decisions

**AD1: Separate from Orchestrator**
- **Decision**: Query logic separate from system logic
- **Rationale**: Single responsibility principle
- **Trade-off**: Additional component

**AD2: Context Selection Strategy**
- **Decision**: Dedicated selection logic
- **Rationale**: Critical for answer quality
- **Trade-off**: Processing overhead

**AD3: Modular Sub-components**
- **Decision**: Separate analyze/select/assemble
- **Rationale**: Flexibility and testing
- **Trade-off**: Coordination complexity

### Alternatives Considered

1. **Merged with Platform Orchestrator**: Violates SRP
2. **Simple Top-K Selection**: Poor answer quality
3. **No Query Analysis**: Misses optimization opportunities

---

## 6. Implementation Guidelines

### Current Implementation Notes

- NLP-based query analysis with spaCy
- MMR context selection for diversity
- Rich response assembly with metadata

### Best Practices

1. **Analyze before retrieval** to optimize parameters
2. **Balance relevance and diversity** in context
3. **Respect token limits** strictly
4. **Include query metadata** in response

### Common Pitfalls

- Don't retrieve too many documents
- Don't pack context to token limit
- Don't ignore query complexity
- Don't lose retrieval metadata

### Performance Considerations

- Cache query analysis results
- Parallelize retrieval if possible
- Optimize context selection algorithm
- Stream response assembly

---

## 7. Configuration

### Configuration Schema

```yaml
query_processor:
  query_analyzer:
    type: "nlp"  # or "llm", "rule_based"
    config:
      model: "en_core_web_sm"
      extract_entities: true
      classify_intent: true
      
  context_selector:
    type: "mmr"  # or "diversity", "token_limit"
    config:
      lambda_param: 0.5
      max_tokens: 2048
      min_relevance: 0.5
      
  response_assembler:
    type: "rich"  # or "standard", "streaming"
    config:
      include_sources: true
      include_metadata: true
      format_citations: true
      
  workflow:
    retrieval_k: 10  # Retrieve more than needed
    generation_k: 5   # Use top-k for generation
    fallback_enabled: true
```

---

## 8. Operations

### Health Checks

- Query analyzer models loaded
- Workflow engine operational
- Dependencies (Retriever, Generator) healthy

### Metrics Exposed

- `query_processor_requests_total`
- `query_processor_latency_seconds{phase="analyze|retrieve|select|generate"}`
- `query_processor_context_size_histogram`
- `query_processor_complexity_distribution`

### Logging Strategy

- DEBUG: Query analysis details
- INFO: Processing summary
- WARN: Poor retrieval results
- ERROR: Workflow failures

### Troubleshooting Guide

| Symptom | Likely Cause | Resolution |
|---------|--------------|------------|
| Slow processing | Complex query analysis | Simplify analyzer |
| Poor answers | Bad context selection | Tune selection params |
| Timeout errors | Large retrieval sets | Reduce retrieval_k |
| Missing sources | Assembly configuration | Check config |

---

## 9. Future Enhancements

### Planned Features

1. **Query Expansion**: Automatic query enhancement
2. **Multi-hop Reasoning**: Complex query decomposition
3. **Conversational Context**: Multi-turn support
4. **Adaptive Retrieval**: Dynamic k selection

### Extension Points

- Custom query analyzers
- Alternative selection strategies
- Specialized assemblers
- Query preprocessors

### Known Limitations

- Single-turn queries only
- No query history
- Fixed retrieval parameters
- English-only analysis