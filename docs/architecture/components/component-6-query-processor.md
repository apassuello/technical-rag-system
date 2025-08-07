# Component 6: Query Processor

**Component ID**: C6  
**Version**: 2.0  
**References**: [MASTER-ARCHITECTURE.md](../MASTER-ARCHITECTURE.md)  
**Related Components**: [C4-Retriever](./component-4-retriever.md), [C5-Answer Generator](./component-5-answer-generator.md)  
**Epic Enhancements**: Epic 1 Query Complexity Analyzer

---

## 1. Component Overview

### 1.1 Purpose & Responsibility

The Query Processor orchestrates the **query execution workflow**:
- Analyze and understand user queries including complexity assessment
- Coordinate retrieval and generation with intelligent routing
- Select optimal context for generation
- Assemble final responses with comprehensive metadata

### 1.2 Position in System

**Workflow Coordinator**: Between retrieval and generation
- **Input**: User queries from Platform Orchestrator
- **Output**: Complete answers with sources and routing metadata

### 1.3 Key Design Decisions

1. **Workflow Orchestration**: Manages the RAG pipeline
2. **Intelligent Context Selection**: Optimize for relevance and diversity
3. **Response Assembly**: Consistent output format
4. **Multi-Model Routing Support**: Epic 1 complexity-based routing

---

## 2. Requirements

### 2.1 Functional Requirements

**Core Capabilities**:
- FR1: Analyze query intent and complexity (Epic 1 enhanced)
- FR2: Execute retrieval with appropriate parameters
- FR3: Select best context within token limits
- FR4: Coordinate answer generation with model routing
- FR5: Assemble responses with metadata
- FR6: Provide complexity analysis for multi-model routing (Epic 1)

**Interface Contracts**: See [Query Processor Interface](../rag-interfaces-spec.md#query-processor-interfaces)

**Behavioral Specifications**:
- Must handle queries of varying complexity with appropriate routing
- Must optimize context for answer quality
- Must provide consistent response format with routing metadata
- Must achieve <50ms routing overhead (Epic 1 requirement)

### 2.2 Quality Requirements

**Performance**:
- Query analysis: <50ms (including complexity assessment)
- Context selection: <100ms
- Total overhead: <200ms
- Routing decision: <50ms (Epic 1 target)

**Reliability**:
- Handle all query types gracefully
- Recover from component failures
- Consistent result quality
- >85% classification accuracy (Epic 1 target)

**Scalability**:
- Process concurrent queries
- Handle varying context sizes
- Support query routing across multiple models

---

## 3. Architecture Design

### 3.1 Internal Structure

```
Query Processor
├── Query Analyzer (sub-component)
│   └── Query Complexity Analyzer (Epic 1)
│       ├── Multi-View Classifiers
│       ├── Stacking Meta-Classifier
│       └── Model Recommender
├── Context Selector (sub-component)
├── Response Assembler (sub-component)
└── Workflow Engine
```

### 3.2 Sub-Components

#### Query Analyzer (Enhanced with Epic 1)

**Purpose**: Understand query characteristics and complexity

**Epic 1 Query Complexity Analyzer**:
- **Architecture**: Multi-view stacking with pretrained models
- **Views**: 5 orthogonal complexity perspectives
  - Linguistic Complexity (DistilBERT)
  - Semantic Complexity (Sentence-BERT)
  - Task Complexity (DeBERTa-v3)
  - Technical Complexity (SciBERT)
  - Computational Complexity (T5-small)
- **Meta-Classifier**: Regularized logistic regression
- **Output**: ComplexityResult with score, model recommendation, confidence

**Implementation Details**:
```python
class Epic1QueryAnalyzer:
    """Multi-view query complexity analyzer for intelligent routing."""
    
    def analyze(self, query: str) -> QueryAnalysis:
        # Extract features from 5 views
        view_scores = self._get_view_scores(query)
        
        # Meta-classifier combines view outputs
        complexity_result = self._meta_classify(view_scores)
        
        # Generate routing recommendation
        model_recommendation = self._recommend_model(complexity_result)
        
        return QueryAnalysis(
            complexity_score=complexity_result.score,
            complexity_level=complexity_result.level,
            recommended_model=model_recommendation,
            view_contributions=view_scores,
            confidence=complexity_result.confidence
        )
```

**Training Strategy**:
- Phase 1: Zero-shot with pretrained models
- Phase 2: Few-shot adaptation (50-100 examples)
- Phase 3: Full training (200-500 examples)

**Context Selector**:
- **Purpose**: Choose optimal documents for generation
- **Implementation**: Direct implementation
- **Decision**: Selection algorithms
- **Variants**: MMR, Diversity, Token-optimized

**Response Assembler**:
- **Purpose**: Format final response with routing metadata
- **Implementation**: Direct implementation
- **Decision**: Formatting logic with Epic 1 metadata
- **Variants**: Standard, Rich (with routing info), Streaming

### 3.3 Adapter vs Direct

**Uses Adapters For**:
- External NLP services (if used)
- LLM-based query analysis
- Pretrained model loading (Epic 1)

**Direct Implementation For**:
- Context selection algorithms
- Response assembly logic
- Workflow orchestration
- Feature extraction (Epic 1)

### 3.4 State Management

**Stateless Processing**:
- Each query processed independently
- No conversation history
- Workflow state temporary
- Model weights cached (Epic 1)

---

## 4. Interfaces

### 4.1 Provided Interfaces

**Main Interface**:
```python
class QueryProcessor:
    def process(self, query: str, options: QueryOptions) -> Answer:
        """Process query through complete RAG pipeline."""
        
    def analyze_query(self, query: str) -> QueryAnalysis:
        """Analyze query complexity and characteristics."""
        
    def select_context(self, results: List[Document], max_tokens: int) -> List[Document]:
        """Select optimal context for generation."""
```

**Epic 1 Enhanced Analysis**:
```python
class QueryAnalysis:
    complexity_score: float  # 0.0-1.0
    complexity_level: str   # simple|moderate|complex
    recommended_model: ModelRecommendation
    view_contributions: Dict[str, float]
    confidence: float
    metadata: Dict[str, Any]
```

### 4.2 Required Interfaces

- Retriever for document search
- Answer Generator for response creation (with model routing)
- Embedder for similarity calculations (context selection)

### 4.3 Events Published

- Query processing started/completed
- Complexity analysis completed (Epic 1)
- Retrieval executed
- Context selected
- Generation requested with model selection

---

## 5. Design Rationale

### Architectural Decisions

**AD1: Separate from Orchestrator**
- **Decision**: Query logic separate from system logic
- **Rationale**: Single responsibility principle
- **Trade-off**: Additional component

**AD2: Multi-View Complexity Analysis (Epic 1)**
- **Decision**: 5 orthogonal views with stacking
- **Rationale**: Robust with limited training data
- **Trade-off**: Model loading overhead

**AD3: Pretrained Model Leverage (Epic 1)**
- **Decision**: Use state-of-art pretrained transformers
- **Rationale**: Transfer learning with minimal data
- **Trade-off**: Memory footprint

**AD4: Modular Sub-components**
- **Decision**: Separate analyze/select/assemble
- **Rationale**: Flexibility and testing
- **Trade-off**: Coordination complexity

### Alternatives Considered

1. **Single Complexity Model**: Poor with limited data
2. **Rule-based Complexity**: Too brittle
3. **Attention-based Fusion**: Requires more data
4. **Simple Features Only**: Misses nuanced complexity

---

## 6. Implementation Guidelines

### Current Implementation Notes

- Epic 1 multi-view complexity analysis operational
- NLP-based query analysis with spaCy
- MMR context selection for diversity
- Rich response assembly with routing metadata

### Best Practices

1. **Cache pretrained model outputs** for common queries
2. **Batch process views** when possible
3. **Balance relevance and diversity** in context
4. **Include routing rationale** in metadata
5. **Monitor classification accuracy** continuously

### Common Pitfalls

- Don't reload models for each query
- Don't ignore confidence scores
- Don't over-optimize for single metric
- Don't lose view contributions in metadata

### Performance Considerations

- Lazy load pretrained models
- Use INT8 quantization where possible
- Cache embeddings for common terms
- Parallelize view processing
- Stream response assembly

---

## 7. Configuration

### Configuration Schema

```yaml
query_processor:
  # Query Analyzer Configuration (Epic 1 Enhanced)
  query_analyzer:
    type: "epic1"  # Multi-view complexity analyzer
    config:
      # View-specific models
      linguistic_model: "distilbert-base-uncased"
      semantic_model: "sentence-transformers/all-MiniLM-L6-v2"
      task_model: "microsoft/deberta-v3-base"
      technical_model: "allenai/scibert_scivocab_uncased"
      computational_model: "t5-small"
      
      # Feature extraction settings
      feature_extractor:
        technical_terms_file: "config/technical_vocabulary.txt"
        enable_entity_extraction: true
        extract_question_types: true
        analyze_syntactic_complexity: true
      
      # Complexity classification thresholds
      complexity_classifier:
        weights:
          linguistic: 0.20
          semantic: 0.15
          task: 0.25
          technical: 0.30
          computational: 0.10
        thresholds:
          simple_threshold: 0.35
          complex_threshold: 0.70
      
      # Model recommendation strategy
      model_recommender:
        strategy: "balanced"  # cost_optimized, quality_first, balanced
        confidence_threshold: 0.8
        
  # Context Selection Configuration
  context_selector:
    type: "mmr"
    config:
      lambda_param: 0.5
      max_tokens: 2048
      min_relevance: 0.5
      
  # Response Assembly Configuration  
  response_assembler:
    type: "rich"
    config:
      include_sources: true
      include_metadata: true
      include_routing_info: true  # Epic 1
      format_citations: true
      
  # Workflow Configuration
  workflow:
    retrieval_k: 10
    generation_k: 5
    fallback_enabled: true
    enable_complexity_routing: true  # Epic 1
```

---

## 8. Operations

### Health Checks

- Query analyzer models loaded
- Pretrained models cached (Epic 1)
- Workflow engine operational
- Dependencies (Retriever, Generator) healthy

### Metrics Exposed

- `query_processor_requests_total`
- `query_processor_latency_seconds{phase="analyze|retrieve|select|generate"}`
- `query_processor_complexity_distribution{level="simple|moderate|complex"}`
- `query_processor_routing_accuracy`
- `query_processor_view_contributions{view="linguistic|semantic|task|technical|computational"}`

### Logging Strategy

- DEBUG: Query analysis details, view scores
- INFO: Processing summary, routing decisions
- WARN: Low confidence predictions, poor retrieval
- ERROR: Model loading failures, workflow errors

### Troubleshooting Guide

| Symptom | Likely Cause | Resolution |
|---------|--------------|------------|
| Slow analysis | Model loading overhead | Implement model caching |
| Poor routing | Threshold miscalibration | Adjust complexity thresholds |
| Low confidence | Ambiguous queries | Add confidence threshold handling |
| Memory issues | All models loaded | Implement lazy loading |

---

## 9. Future Enhancements

### Planned Features

1. **Active Learning**: Identify uncertain examples for labeling
2. **Online Learning**: Continuous improvement from usage
3. **Domain Adaptation**: Specialize for different technical domains
4. **Multilingual Support**: Extend to non-English queries
5. **Conversational Context**: Multi-turn support

### Extension Points

- Custom complexity views
- Alternative fusion strategies
- Specialized model recommenders
- Query preprocessors

### Known Limitations

- English-only analysis currently
- No conversation history
- Fixed view architecture
- Limited to text queries

---

## 10. Epic 1 Specific Requirements

### Performance Targets
- **Classification Accuracy**: >85%
- **Routing Overhead**: <50ms
- **Cost Reduction**: >40% vs single model
- **Model Selection Accuracy**: >90%

### Training Data Requirements
- **Minimum**: 200-500 synthetic examples
- **Distribution**: Balanced across complexity levels
- **Validation**: 20% holdout set
- **Adversarial**: 50 edge cases

### Integration Points
- **Answer Generator**: Receives model recommendations
- **Platform Orchestrator**: Reports routing decisions
- **Cost Tracker**: Monitors optimization effectiveness

---

## Appendix: Multi-View Architecture Details

### View Specifications

| View | Model | Purpose | Features | Output |
|------|-------|---------|----------|--------|
| Linguistic | DistilBERT | Surface complexity | Attention patterns, syntax | Score [0,1] |
| Semantic | Sentence-BERT | Conceptual depth | Embedding similarity | Score [0,1] |
| Task | DeBERTa-v3 | Task classification | Question patterns | Category + Score |
| Technical | SciBERT | Domain complexity | Term density | Score [0,1] |
| Computational | T5-small | Processing needs | Query structure | Estimate |

### Meta-Classifier Input Vector
```
[
  linguistic_score,      # View scores (5)
  semantic_score,
  task_score,
  technical_score,
  computational_score,
  linguistic_confidence, # View confidences (5)
  semantic_confidence,
  task_confidence,
  technical_confidence,
  computational_confidence,
  mean_score,           # Statistical aggregations (5)
  std_score,
  min_score,
  max_score,
  range_score
]
```

This 15-dimensional vector feeds into the regularized logistic regression meta-classifier for final complexity determination and model routing.