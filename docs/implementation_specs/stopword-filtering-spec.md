# Stop Word Filtering Specification

**Component**: BM25Retriever (src/components/retrievers/sparse/bm25_retriever.py)  
**Version**: 1.0  
**Status**: Baseline Implementation Complete  
**Architecture Compliance**: Modular Sub-Component Pattern

## 1. Problem Statement

The BM25 retriever currently assigns high scores (0.946+) to irrelevant queries like "Where is Paris?" because it matches common stop words ("where", "is") with high frequency across the corpus. This causes irrelevant documents to pass through the retrieval pipeline with high confidence scores.

## 2. Design Requirements

### 2.1 Functional Requirements
- **FR1**: Filter configurable stop words during BM25 tokenization
- **FR2**: Preserve technical terms that might overlap with stop words (e.g., "IS" in "RISC-V IS")
- **FR3**: Support language-specific stop word lists
- **FR4**: Enable/disable filtering via configuration
- **FR5**: Provide debug mode showing filtered vs. retained terms

### 2.2 Non-Functional Requirements
- **Performance**: <5% impact on indexing speed
- **Memory**: Stop word set lookup must be O(1)
- **Configurability**: All parameters exposed in YAML configuration
- **Observability**: Debug logging for filtered terms

## 3. Configuration Schema

```yaml
# In config files (epic2_modular.yaml, etc.)
retriever:
  sparse:
    type: "bm25"
    config:
      # Existing parameters
      k1: 1.2
      b: 0.75
      lowercase: true
      preserve_technical_terms: true
      
      # Stop word filtering parameters
      filter_stop_words: true  # Master enable/disable
      stop_word_sets:
        - "english_common"     # Built-in set name
        - "custom"            # Custom additions
      custom_stop_words: ["where", "what", "who"]  # Additional words
      technical_exceptions: ["IS", "AS", "OR", "AND"]  # Don't filter these
      min_word_length: 2      # Words shorter than this are filtered
      
      # Debug configuration
      debug_stop_words: false  # Log filtered terms
      stop_word_stats: false   # Track filtering statistics
```

## 4. Implementation Guidelines

### 4.1 Stop Word Set Management
```python
# Built-in sets should include:
STOP_WORD_SETS = {
    "english_common": {...},  # 100-150 most common English stop words
    "english_extended": {...}, # 300+ comprehensive set
    "technical_minimal": {...} # Minimal set preserving technical terms
}
```

### 4.2 Technical Term Preservation
- Implement case-sensitive checking for technical exceptions
- Use regex pattern for technical term detection: `[A-Z]{2,}|\w+_\w+`
- Preserve terms that appear in document titles or headers

### 4.3 Debug Output Format
```
[BM25_DEBUG] Query: "Where is Paris?"
[BM25_DEBUG] Tokens before filtering: ["where", "is", "paris"]
[BM25_DEBUG] Stop words removed: ["where", "is"]
[BM25_DEBUG] Tokens after filtering: ["paris"]
[BM25_DEBUG] Filtering impact: 66.7% tokens removed
```

## 5. Testing Requirements

### 5.1 Unit Tests
```python
def test_stop_word_filtering():
    """Test that common stop words are filtered"""
    
def test_technical_term_preservation():
    """Test that technical terms are preserved despite stop word overlap"""
    
def test_configuration_handling():
    """Test all configuration parameters work correctly"""
    
def test_performance_impact():
    """Verify filtering doesn't significantly impact performance"""
```

### 5.2 Integration Test Cases
1. **Irrelevant Query Test**: "Where is Paris?" should return minimal or no documents
2. **Technical Query Test**: "What is RISC-V ISA?" should preserve "IS" in context
3. **Mixed Query Test**: "How does the RISC-V AND operation work?" preserves "AND"

## 6. Metrics and Monitoring

### 6.1 Key Metrics to Track
- **Filtering Rate**: Percentage of tokens filtered per query
- **False Positive Reduction**: Reduction in irrelevant document retrieval
- **Technical Term Preservation Rate**: Percentage of technical terms correctly preserved
- **Performance Impact**: Indexing and search time delta

### 6.2 Validation Criteria
- Irrelevant queries (Napoleon, Paris) should score <0.3 after filtering
- Technical queries should maintain current retrieval quality
- No more than 5% performance degradation

## 7. Claude Code Implementation Instructions

When implementing with Claude Code:

1. **Start with diagnostic analysis**:
   - "Show me which terms contribute to high BM25 scores for 'Where is Paris?'"
   - "Identify the term frequency and document frequency for each token"

2. **Implement incrementally**:
   - First: Basic stop word filtering with standard set
   - Second: Add technical term preservation
   - Third: Add configuration and debug features

3. **Test with specific queries**:
   - Irrelevant: "Where is Paris?", "Who is Napoleon?"
   - Technical: "What is RISC-V?", "How does RV32I work?"
   - Edge cases: "The instruction set architecture IS important"

## 8. Migration Path

1. **Phase 1**: Deploy with `filter_stop_words: false` (no change)
2. **Phase 2**: Enable in test configuration, validate results
3. **Phase 3**: Gradually increase stop word set size
4. **Phase 4**: Enable in production with monitoring

## 9. Success Criteria

- ✅ Irrelevant query scores drop from 0.85+ to <0.3
- ✅ Technical query quality maintained or improved
- ✅ Configuration fully controllable via YAML
- ✅ Debug mode provides clear insights
- ✅ Performance impact <5%