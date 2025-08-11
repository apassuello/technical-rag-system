# Epic 1: Comprehensive QueryComplexityAnalyzer Implementation Plan

## Executive Summary
This document provides the complete technical implementation plan for the QueryComplexityAnalyzer, the first sub-component of Epic 1's multi-model Answer Generator. The analyzer will enable intelligent routing of queries to appropriate LLM models based on complexity, optimizing for both cost and quality.

## Architecture Validation ✅

### Component Compliance
- **Target Component**: Answer Generator (C5) - Response Generation
- **Implementation Type**: Direct implementation (pure algorithm, no external APIs)
- **Pattern**: Sub-component following established patterns (prompt_builders, confidence_scorers)
- **Architecture Safeguards**: All validated against ARCHITECTURE_SAFEGUARDS.md

### Architectural Decision Rationale
- **Why Answer Generator?**: Query complexity analysis is specific to answer generation optimization
- **Why Not Platform Orchestrator?**: Not a system-wide service, only needed by Answer Generator
- **Why Not Query Processor?**: Query Processor orchestrates workflow, doesn't implement generation logic
- **Why Direct Implementation?**: Pure algorithmic analysis, no external services needed

## Technical Implementation Details

### 1. Core Linguistic Features (Research-Based)

Based on NLP research showing 10 key features can achieve >85% classification accuracy:

#### 1.1 Query Length Metrics (20% weight)
```python
def extract_length_features(query: str) -> Dict[str, float]:
    return {
        'word_count': len(query.split()),
        'char_count': len(query),
        'token_estimate': len(query) / 4,  # Rough token estimate
        'normalized_length': min(1.0, len(query.split()) / 50)  # Normalize to 0-1
    }
```

#### 1.2 Syntactic Complexity (25% weight)
```python
def extract_syntactic_features(query: str) -> Dict[str, float]:
    # Using lightweight parsing without external dependencies
    return {
        'clause_count': query.count(',') + query.count(';') + 1,
        'nested_depth': self._calculate_nesting_depth(query),
        'conjunction_count': sum(1 for word in ['and', 'or', 'but'] if word in query.lower()),
        'complexity_score': self._syntactic_complexity_score(query)
    }
```

#### 1.3 Technical Vocabulary (30% weight)
```python
TECHNICAL_TERMS = {
    'embedding', 'vector', 'transformer', 'neural', 'gradient',
    'optimization', 'hyperparameter', 'architecture', 'pipeline',
    'inference', 'latency', 'throughput', 'scalability', 'api'
}

def extract_technical_features(query: str) -> Dict[str, float]:
    words = query.lower().split()
    technical_count = sum(1 for word in words if word in TECHNICAL_TERMS)
    return {
        'technical_density': technical_count / max(1, len(words)),
        'has_code': bool(re.search(r'[{}\[\]()<>]', query)),
        'has_config': 'config' in query.lower() or 'yaml' in query.lower(),
        'domain_specificity': self._calculate_domain_score(query)
    }
```

#### 1.4 Question Type Classification (15% weight)
```python
def classify_question_type(query: str) -> Dict[str, float]:
    query_lower = query.lower()
    return {
        'is_factual': 1.0 if query_lower.startswith(('what is', 'who is', 'when')) else 0.0,
        'is_analytical': 1.0 if any(w in query_lower for w in ['why', 'how does', 'explain']) else 0.0,
        'is_procedural': 1.0 if any(w in query_lower for w in ['how to', 'steps', 'implement']) else 0.0,
        'is_comparative': 1.0 if any(w in query_lower for w in ['compare', 'difference', 'vs']) else 0.0
    }
```

#### 1.5 Ambiguity Indicators (10% weight)
```python
def extract_ambiguity_features(query: str) -> Dict[str, float]:
    return {
        'pronoun_ratio': len(re.findall(r'\b(it|this|that|they|them)\b', query.lower())) / max(1, len(query.split())),
        'vague_terms': sum(1 for term in ['something', 'somehow', 'maybe'] if term in query.lower()),
        'clarity_score': self._calculate_clarity_score(query)
    }
```

### 2. Classification Algorithm

```python
class QueryComplexityAnalyzer(BaseQueryAnalyzer):
    
    DEFAULT_WEIGHTS = {
        'length': 0.20,
        'syntactic': 0.25,
        'technical': 0.30,
        'structure': 0.15,
        'ambiguity': 0.10
    }
    
    DEFAULT_THRESHOLDS = {
        'simple': 0.35,
        'complex': 0.70
    }
    
    def calculate_complexity(self, features: Dict[str, float]) -> float:
        """Calculate weighted complexity score from features."""
        weighted_scores = []
        
        for category, weight in self.weights.items():
            category_features = [v for k, v in features.items() if k.startswith(category)]
            if category_features:
                category_score = sum(category_features) / len(category_features)
                weighted_scores.append(category_score * weight)
        
        return sum(weighted_scores)
    
    def classify_complexity(self, score: float) -> str:
        """Classify complexity level based on score."""
        if score < self.thresholds['simple']:
            return 'simple'
        elif score < self.thresholds['complex']:
            return 'medium'
        else:
            return 'complex'
    
    def get_confidence(self, score: float) -> float:
        """Calculate confidence based on distance from thresholds."""
        distances = [
            abs(score - self.thresholds['simple']),
            abs(score - self.thresholds['complex'])
        ]
        min_distance = min(distances)
        
        # Higher confidence when further from thresholds
        if min_distance > 0.15:
            return 0.95
        elif min_distance > 0.10:
            return 0.85
        elif min_distance > 0.05:
            return 0.70
        else:
            return 0.55
```

### 3. Integration with AnswerGenerator

#### 3.1 Configuration Loading
```python
# In AnswerGenerator._initialize_components()
if 'query_analyzer' in self.config:
    analyzer_type = self.config['query_analyzer']['type']
    analyzer_config = self.config['query_analyzer'].get('config', {})
    analyzer_class = get_analyzer_class(analyzer_type)
    self.query_analyzer = analyzer_class(**analyzer_config)
else:
    self.query_analyzer = None  # Backward compatibility
```

#### 3.2 Generate Method Enhancement
```python
def generate(self, query: str, context: List[Document]) -> Answer:
    # NEW: Analyze query complexity
    if self.query_analyzer:
        analysis = self.query_analyzer.analyze_query(query)
        logger.info(f"Query complexity: {analysis.complexity_level} "
                   f"(score: {analysis.complexity_score:.2f}, "
                   f"confidence: {analysis.confidence:.2f})")
        
        # Select appropriate model based on complexity
        if hasattr(self, 'model_router'):
            selected_model = self.model_router.select_model(analysis)
            self._switch_llm_client(selected_model)
    
    # Continue with existing flow...
    prompt = self.prompt_builder.build_prompt(query, context)
    # ...
```

### 4. File Structure Implementation

```
src/components/generators/analyzers/
├── __init__.py                    # Registry pattern
├── base_analyzer.py              # Abstract base class
├── feature_extractor.py          # Feature extraction logic
├── complexity_analyzer.py        # Main analyzer implementation
└── utils/
    ├── __init__.py
    ├── technical_terms.py        # Domain vocabulary management
    └── syntactic_parser.py       # Lightweight syntax analysis
```

### 5. Configuration Schema

```yaml
answer_generator:
  type: "adaptive_modular"  # New type for Epic 1
  config:
    # NEW: Query Analyzer Configuration
    query_analyzer:
      type: "complexity"
      config:
        # Feature weights (must sum to 1.0)
        weights:
          length: 0.20
          syntactic: 0.25
          technical: 0.30
          structure: 0.15
          ambiguity: 0.10
        
        # Complexity thresholds
        thresholds:
          simple: 0.35      # Below = simple
          complex: 0.70     # Above = complex
        
        # Technical vocabulary
        technical_terms_file: "config/technical_vocabulary.txt"
        
        # Performance optimization
        cache_enabled: true
        cache_size: 1000
        cache_ttl: 3600  # 1 hour
    
    # Existing sub-components
    prompt_builder:
      type: "simple"
      # ...
    
    llm_client:
      type: "ollama"  # Will support multiple in Epic 1
      # ...
```

### 6. Testing Strategy

#### 6.1 Unit Tests
```python
class TestQueryComplexityAnalyzer:
    
    def test_simple_query_classification(self):
        """Test that simple queries are correctly classified."""
        analyzer = QueryComplexityAnalyzer(config={})
        simple_queries = [
            "What is a vector?",
            "Define embedding",
            "List the components"
        ]
        for query in simple_queries:
            analysis = analyzer.analyze_query(query)
            assert analysis.complexity_level == 'simple'
    
    def test_complex_query_classification(self):
        """Test that complex queries are correctly classified."""
        complex_queries = [
            "How does the transformer architecture handle long-range dependencies "
            "compared to RNNs, and what are the trade-offs in terms of computational "
            "complexity and parallelization?",
            "Implement a custom attention mechanism that combines both local and "
            "global context with dynamic routing based on input complexity"
        ]
        for query in complex_queries:
            analysis = analyzer.analyze_query(query)
            assert analysis.complexity_level == 'complex'
    
    def test_performance_requirements(self):
        """Test that analysis completes within 50ms."""
        analyzer = QueryComplexityAnalyzer(config={})
        query = "How do I optimize embedding generation for large documents?"
        
        start = time.time()
        analysis = analyzer.analyze_query(query)
        elapsed = time.time() - start
        
        assert elapsed < 0.050  # 50ms requirement
```

#### 6.2 Accuracy Validation Dataset
```python
# Create labeled test dataset
TEST_QUERIES = [
    # Simple queries (expected: simple)
    ("What is FAISS?", "simple"),
    ("Define RAG", "simple"),
    ("List available models", "simple"),
    
    # Medium queries (expected: medium)
    ("How do I configure the retriever for better accuracy?", "medium"),
    ("Explain the difference between dense and sparse retrieval", "medium"),
    
    # Complex queries (expected: complex)
    ("Compare different reranking strategies and their impact on retrieval "
     "quality in domain-specific technical documentation", "complex"),
]

def test_classification_accuracy():
    analyzer = QueryComplexityAnalyzer(config={})
    correct = 0
    
    for query, expected in TEST_QUERIES:
        analysis = analyzer.analyze_query(query)
        if analysis.complexity_level == expected:
            correct += 1
    
    accuracy = correct / len(TEST_QUERIES)
    assert accuracy >= 0.85  # 85% accuracy requirement
```

### 7. Performance Optimization

#### 7.1 Feature Caching
```python
class CachedFeatureExtractor:
    def __init__(self, cache_size: int = 1000):
        self.cache = {}
        self.cache_order = []
        self.cache_size = cache_size
    
    def extract(self, query: str) -> Dict[str, float]:
        # Check cache
        query_hash = hashlib.md5(query.encode()).hexdigest()
        if query_hash in self.cache:
            return self.cache[query_hash]
        
        # Extract features
        features = self._extract_features(query)
        
        # Update cache
        self._add_to_cache(query_hash, features)
        
        return features
```

#### 7.2 Optimized Technical Term Detection
```python
class TrieNode:
    def __init__(self):
        self.children = {}
        self.is_end = False

class TechnicalTermTrie:
    """Efficient technical term detection using Trie data structure."""
    
    def __init__(self, terms: List[str]):
        self.root = TrieNode()
        for term in terms:
            self._insert(term.lower())
    
    def contains(self, word: str) -> bool:
        """O(m) lookup where m is word length."""
        node = self.root
        for char in word.lower():
            if char not in node.children:
                return False
            node = node.children[char]
        return node.is_end
```

### 8. Success Metrics & Validation

| Metric | Target | Validation Method |
|--------|--------|-------------------|
| Classification Accuracy | >85% | Test on 100+ labeled queries |
| Analysis Latency | <50ms | Performance benchmarking |
| Memory Usage | <50MB | Memory profiling |
| Cache Hit Rate | >80% | Runtime monitoring |
| Thread Safety | 100% | Concurrent testing |

### 9. Risk Analysis & Mitigation

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Accuracy <85% | Medium | High | Add more features, use ensemble approach |
| Latency >50ms | Low | Medium | Implement caching, optimize algorithms |
| Integration complexity | Low | Medium | Feature flag for gradual rollout |
| Technical term detection issues | Medium | Low | Configurable vocabulary, fallback to general features |

### 10. Implementation Timeline

#### Week 1: Core Implementation (40 hours)
- Day 1-2: Package structure and base classes
- Day 3-4: Feature extraction implementation
- Day 5: Classification algorithm and integration

#### Week 2: Testing & Optimization (20 hours)
- Day 1-2: Unit tests and accuracy validation
- Day 3: Performance optimization and caching

#### Week 3: Integration (20 hours)
- Day 1-2: AnswerGenerator integration
- Day 3: End-to-end testing

### 11. Future Enhancements

1. **ML-Based Analyzer** (Phase 2)
   - Train sklearn classifier on labeled data
   - Use as alternative or ensemble member

2. **Dynamic Threshold Adjustment** (Phase 3)
   - Learn from user feedback
   - Adjust thresholds based on domain

3. **Multi-Language Support** (Phase 4)
   - Extend features for non-English queries
   - Language-specific complexity metrics

## Conclusion

This implementation plan provides a comprehensive, architecture-compliant approach to building the QueryComplexityAnalyzer. The design follows established patterns, integrates cleanly with the existing system, and provides a solid foundation for Epic 1's multi-model routing capabilities while maintaining Swiss engineering standards.