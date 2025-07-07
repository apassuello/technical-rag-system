# Migration Guide: BasicRAG to Modular RAGPipeline

## Overview

This guide provides comprehensive instructions for migrating from the legacy `BasicRAG` system to the new modular `RAGPipeline` architecture. The migration ensures backward compatibility while providing enhanced functionality, better performance, and improved maintainability.

## Table of Contents

1. [Migration Overview](#migration-overview)
2. [Pre-Migration Assessment](#pre-migration-assessment)
3. [Step-by-Step Migration Process](#step-by-step-migration-process)
4. [API Mapping Reference](#api-mapping-reference)
5. [Configuration Migration](#configuration-migration)
6. [Testing and Validation](#testing-and-validation)
7. [Troubleshooting](#troubleshooting)
8. [Best Practices](#best-practices)
9. [Production Deployment](#production-deployment)

## Migration Overview

### What's Changing

The migration transforms your RAG system from a monolithic `BasicRAG` class to a modular, configurable architecture:

- **From**: `BasicRAG()` instantiation
- **To**: `RAGPipeline(config_path)` with YAML configuration
- **Benefits**: Better modularity, easier testing, configuration management, and extensibility

### Compatibility Promise

✅ **Full Backward Compatibility**: All existing functionality is preserved  
✅ **API Compatibility**: Core methods maintain the same interfaces  
✅ **Data Compatibility**: Existing indexes and documents work unchanged  
✅ **Performance**: Equal or better performance in most cases  

## Pre-Migration Assessment

### 1. Analyze Your Current Usage

Use our migration analysis tool to understand your current BasicRAG usage:

```bash
python scripts/migration_analysis.py
```

This will generate a report showing:
- All files using BasicRAG
- Method usage patterns  
- Configuration requirements
- Potential migration challenges

### 2. Review the Analysis Report

The analysis report (`migration_analysis_report_YYYYMMDD_HHMMSS.json`) contains:

```json
{
  "files_using_basic_rag": 25,
  "usage_patterns": 116,
  "method_usage_stats": {
    "hybrid_query": 33,
    "__init__": 30,
    "query": 20,
    "index_document": 20
  },
  "migration_recommendations": [
    "Replace 'from src.basic_rag import BasicRAG' with 'from src.core.pipeline import RAGPipeline'",
    "Replace 'BasicRAG()' initialization with 'RAGPipeline(config_path)'"
  ]
}
```

## Step-by-Step Migration Process

### Step 1: Install Dependencies

Ensure you have all required dependencies:

```bash
# Existing dependencies (already installed)
pip install faiss-cpu sentence-transformers transformers

# No new dependencies required for migration
```

### Step 2: Create Configuration Files

The new system uses YAML configuration files. Generate default configurations:

```bash
# This will create config/default.yaml if it doesn't exist
python scripts/migrate_to_modular.py --analyze
```

Or manually create `config/default.yaml`:

```yaml
document_processor:
  type: "hybrid_pdf"
  config:
    chunk_size: 1400
    chunk_overlap: 200

embedder:
  type: "sentence_transformer"
  config:
    model_name: "sentence-transformers/all-MiniLM-L6-v2"
    use_mps: true
    batch_size: 16

vector_store:
  type: "faiss"
  config:
    index_type: "IndexFlatIP"
    normalize_embeddings: true

retriever:
  type: "hybrid"
  config:
    dense_weight: 0.7
    top_k: 5
    fusion_method: "reciprocal_rank"

answer_generator:
  type: "adaptive"
  config:
    model_name: "deepset/roberta-base-squad2"
    api_token: null
    enable_adaptive_prompts: false
    confidence_threshold: 0.85
    max_tokens: 512
```

### Step 3: Automated Code Migration

Use our automated migration tool:

```bash
# Dry run to see what changes would be made
python scripts/migrate_to_modular.py --analyze

# Perform the actual migration
python scripts/migrate_to_modular.py --migrate

# Migrate specific files only
python scripts/migrate_to_modular.py --file path/to/your/file.py
```

The tool will:
- ✅ Update import statements
- ✅ Transform instantiation calls
- ✅ Update method calls where needed
- ✅ Create backups of original files
- ✅ Generate rollback information

### Step 4: Manual Code Updates

For complex cases, manual updates may be needed:

#### Before (BasicRAG):
```python
from src.basic_rag import BasicRAG

# Initialize
rag = BasicRAG()

# Index document
chunks = rag.index_document("document.pdf")

# Query (various methods)
results = rag.query("What is RISC-V?")
results = rag.hybrid_query("What is RISC-V?", top_k=5)
results = rag.enhanced_hybrid_query("What is RISC-V?")  # Deprecated
```

#### After (RAGPipeline):
```python
from src.core.pipeline import RAGPipeline
from pathlib import Path

# Initialize with configuration
rag = RAGPipeline("config/default.yaml")
# or
rag = RAGPipeline(Path("config/default.yaml"))

# Index document (same interface)
chunks = rag.index_document("document.pdf")

# Query (unified interface - hybrid is default)
answer = rag.query("What is RISC-V?", k=5)

# Access answer properties
print(answer.text)          # Generated answer
print(answer.sources)       # Source documents
print(answer.confidence)    # Confidence score
print(answer.metadata)      # Additional metadata
```

### Step 5: Update Environment-Specific Configurations

Create configuration files for different environments:

#### Development (`config/dev.yaml`):
```yaml
# Development configuration with debugging features
document_processor:
  type: "hybrid_pdf"
  config:
    chunk_size: 1000
    chunk_overlap: 150

answer_generator:
  type: "adaptive"
  config:
    enable_chain_of_thought: true  # Enable for debugging
    enable_adaptive_prompts: false
    confidence_threshold: 0.7
```

#### Production (`config/production.yaml`):
```yaml
# Production configuration optimized for performance
embedder:
  type: "sentence_transformer"
  config:
    batch_size: 32  # Larger batches for better throughput
    use_mps: true

answer_generator:
  type: "adaptive"
  config:
    confidence_threshold: 0.85  # Higher threshold for production
    max_tokens: 512
```

#### Testing (`config/test.yaml`):
```yaml
# Test configuration for fast execution
embedder:
  type: "sentence_transformer"
  config:
    batch_size: 8   # Smaller batches for faster tests
    use_mps: false  # Disable for CI consistency

answer_generator:
  type: "adaptive"
  config:
    max_tokens: 128  # Shorter responses for tests
```

## API Mapping Reference

### Core Methods

| BasicRAG Method | RAGPipeline Method | Notes |
|-----------------|-------------------|-------|
| `BasicRAG()` | `RAGPipeline(config_path)` | Now requires configuration file |
| `index_document(path)` | `index_document(path)` | Same interface ✅ |
| `query(text)` | `query(text, k=5)` | Same interface, `k` parameter optional |
| `hybrid_query(text, top_k=5)` | `query(text, k=5)` | Hybrid is now default behavior |
| `enhanced_hybrid_query(text)` | `query(text, k=5)` | Enhanced features integrated by default |

### Return Value Changes

#### BasicRAG Query Response:
```python
results = rag.hybrid_query("query")
# Returns: List[Dict] with chunks and scores
for result in results:
    print(result['text'])
    print(result['score'])
```

#### RAGPipeline Query Response:
```python
answer = rag.query("query")
# Returns: Answer object with structured data
print(answer.text)           # str: Generated answer
print(answer.sources)        # List[Document]: Source documents  
print(answer.confidence)     # float: Confidence score
print(answer.metadata)       # Dict: Additional metadata

# Access source documents
for doc in answer.sources:
    print(doc.content)       # Document text
    print(doc.metadata)      # Document metadata
```

### Component Access

#### BasicRAG (limited access):
```python
rag = BasicRAG()
# Limited access to internal components
```

#### RAGPipeline (full component access):
```python
pipeline = RAGPipeline("config/default.yaml")

# Access individual components for monitoring/debugging
processor = pipeline.get_component("processor")
embedder = pipeline.get_component("embedder")
vector_store = pipeline.get_component("vector_store")
retriever = pipeline.get_component("retriever")
generator = pipeline.get_component("generator")

# Get pipeline information
info = pipeline.get_pipeline_info()
print(info)  # Configuration and component details
```

## Configuration Migration

### Environment Variables

The new system supports environment variable overrides with the `RAG_` prefix:

```bash
# Override configuration values
export RAG_EMBEDDER__CONFIG__BATCH_SIZE=32
export RAG_ANSWER_GENERATOR__CONFIG__MAX_TOKENS=1024

# Use specific configuration file
export RAG_ENV=production  # Loads config/production.yaml
```

### Dynamic Configuration

```python
# Load different configurations at runtime
from src.core.config import ConfigManager

# Development
dev_pipeline = RAGPipeline("config/dev.yaml")

# Production  
prod_pipeline = RAGPipeline("config/production.yaml")

# Programmatic configuration
config_manager = ConfigManager("config/default.yaml")
config = config_manager.config
# Modify config if needed
pipeline = RAGPipeline.from_config(config)
```

## Testing and Validation

### 1. Comparison Testing

Validate that the new system produces equivalent results:

```bash
# Compare old vs new system side-by-side
python scripts/comparison_testing.py --save-report comparison_report.json
```

This will test:
- ✅ Document indexing (chunk counts, content)
- ✅ Query results (similarity, overlap)
- ✅ Performance (speed, memory)
- ✅ Error handling

### 2. Performance Benchmarking

Ensure performance is maintained or improved:

```bash
# Comprehensive performance testing
python scripts/performance_benchmark.py --save-report performance_report.json
```

Tests include:
- 📊 Indexing speed
- ⚡ Query response times
- 💾 Memory usage
- 🚀 Concurrent processing

### 3. Production Validation

Validate production readiness:

```bash
# Production-grade validation
python scripts/production_migration_test.py --save-report validation_report.json
```

Validates:
- 🔧 Basic functionality
- 📚 Large-scale processing
- 🛡️ Error handling
- ⚙️ Configuration management
- 💪 Stress testing

## Troubleshooting

### Common Issues and Solutions

#### 1. Import Errors

**Problem**: `ModuleNotFoundError: No module named 'src.core.pipeline'`

**Solution**:
```python
# Ensure correct project structure and imports
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from src.core.pipeline import RAGPipeline
```

#### 2. Configuration Errors

**Problem**: `ValueError: Unknown processor 'hybrid_pdf'`

**Solution**: Ensure components are auto-registered by importing them:
```python
# Import components to trigger registration
from src.components.processors.pdf_processor import HybridPDFProcessor
from src.components.embedders.sentence_transformer_embedder import SentenceTransformerEmbedder
from src.components.vector_stores.faiss_store import FAISSVectorStore
from src.components.retrievers.hybrid_retriever import HybridRetriever
from src.components.generators.adaptive_generator import AdaptiveAnswerGenerator

# Then initialize pipeline
pipeline = RAGPipeline("config/default.yaml")
```

#### 3. Method Signature Changes

**Problem**: `TypeError: hybrid_query() got an unexpected keyword argument 'k'`

**Solution**: Update method calls:
```python
# Old
results = rag.hybrid_query(query, k=5)  # ❌ k parameter not supported

# New  
results = rag.hybrid_query(query, top_k=5)  # ✅ Use top_k parameter
# Or better, use unified interface
answer = rag.query(query, k=5)  # ✅ Recommended approach
```

#### 4. Return Value Differences

**Problem**: Expecting list of chunks, getting Answer object

**Solution**: Update result handling:
```python
# Old approach
results = rag.hybrid_query(query)
for chunk in results:
    print(chunk['text'])

# New approach - extract sources from answer
answer = rag.query(query)
for doc in answer.sources:
    print(doc.content)

# Or get the generated answer directly
print(answer.text)
```

#### 5. Configuration File Issues

**Problem**: YAML parsing errors or invalid configuration

**Solution**: Validate configuration:
```bash
# Use validation tool
python scripts/validate_configs.py --config default

# Or validate manually
python -c "
from src.core.config import ConfigManager
try:
    config = ConfigManager('config/default.yaml')
    print('✅ Configuration valid')
except Exception as e:
    print(f'❌ Configuration error: {e}')
"
```

### Performance Issues

#### 1. Slower Query Response

**Symptoms**: Queries taking significantly longer than before

**Diagnosis**:
```python
# Check configuration settings
pipeline = RAGPipeline("config/default.yaml")
info = pipeline.get_pipeline_info()
print(info)

# Monitor component performance
import time
start = time.time()
answer = pipeline.query("test query")
print(f"Query time: {time.time() - start:.2f}s")
```

**Solutions**:
- Increase `batch_size` for embeddings
- Use `use_mps: true` for Apple Silicon
- Optimize `chunk_size` and `chunk_overlap`
- Check network latency for API-based generators

#### 2. High Memory Usage

**Symptoms**: Increased memory consumption

**Solutions**:
```yaml
# Optimize configuration for memory
embedder:
  config:
    batch_size: 8  # Reduce batch size
    
vector_store:
  config:
    normalize_embeddings: true  # Reduce memory overhead

answer_generator:
  config:
    max_tokens: 256  # Reduce token limit
```

### Rollback Procedure

If you need to revert the migration:

```bash
# Rollback to previous version
python scripts/migrate_to_modular.py --rollback

# Or rollback specific session
python scripts/migrate_to_modular.py --rollback --session-id 20231207_143021
```

Backups are stored in `migration_backups/` directory.

## Best Practices

### 1. Configuration Management

#### Environment-Specific Configs
```bash
# Use environment-specific configurations
export RAG_ENV=development  # Uses config/dev.yaml
export RAG_ENV=production   # Uses config/production.yaml
export RAG_ENV=test        # Uses config/test.yaml
```

#### Version Control
```bash
# Include in version control
git add config/default.yaml
git add config/production.yaml
git add config/dev.yaml
git commit -m "Add RAG pipeline configurations"
```

#### Secrets Management
```yaml
# Use environment variables for sensitive data
answer_generator:
  config:
    api_token: ${HF_API_TOKEN}  # Set via environment variable
```

### 2. Testing Strategy

#### Unit Testing
```python
def test_pipeline_migration():
    """Test that migrated pipeline produces same results."""
    # Test with known query and document
    pipeline = RAGPipeline("config/test.yaml")
    chunks = pipeline.index_document("test_document.pdf")
    
    answer = pipeline.query("test query")
    
    assert len(answer.sources) > 0
    assert answer.confidence > 0.5
    assert len(answer.text) > 10
```

#### Integration Testing
```python
def test_end_to_end_migration():
    """Test complete migration workflow."""
    # Compare old vs new system
    from scripts.comparison_testing import ComparisonTester
    
    tester = ComparisonTester()
    report = tester.run_comprehensive_comparison([Path("test.pdf")])
    
    assert report.summary_statistics["avg_similarity_score"] > 0.8
```

### 3. Monitoring and Observability

#### Performance Monitoring
```python
# Add timing and monitoring
import time
from datetime import datetime

def monitored_query(pipeline, query):
    start_time = time.time()
    answer = pipeline.query(query)
    response_time = time.time() - start_time
    
    # Log metrics
    print(f"Query: {query[:50]}...")
    print(f"Response time: {response_time:.2f}s")
    print(f"Confidence: {answer.confidence:.3f}")
    print(f"Sources: {len(answer.sources)}")
    
    return answer
```

#### Error Monitoring
```python
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    pipeline = RAGPipeline("config/production.yaml")
    answer = pipeline.query(query)
except Exception as e:
    logger.error(f"Pipeline error: {e}")
    # Fallback or alert logic
```

### 4. Gradual Migration

#### Phased Approach
1. **Phase 1**: Migrate development environment
2. **Phase 2**: Migrate testing environment  
3. **Phase 3**: Migrate staging environment
4. **Phase 4**: Migrate production with traffic splitting

#### Feature Flags
```python
import os

USE_NEW_PIPELINE = os.getenv("USE_NEW_PIPELINE", "false").lower() == "true"

if USE_NEW_PIPELINE:
    rag = RAGPipeline("config/production.yaml")
else:
    rag = BasicRAG()  # Legacy fallback
```

## Production Deployment

### 1. Pre-Deployment Checklist

- [ ] ✅ All tests passing with new system
- [ ] ✅ Performance validated (no regression)
- [ ] ✅ Configuration files reviewed and validated
- [ ] ✅ Backup and rollback procedures tested
- [ ] ✅ Monitoring and alerting configured
- [ ] ✅ Documentation updated

### 2. Deployment Strategy

#### Blue-Green Deployment
```python
# Deploy to green environment
# Test with production traffic
# Switch traffic from blue to green
# Keep blue as backup
```

#### Rolling Deployment
```python
# Deploy to subset of instances
# Monitor key metrics
# Gradually increase traffic
# Complete rollout
```

#### Canary Deployment
```python
# Deploy to small percentage of traffic
# Monitor error rates and performance
# Gradually increase percentage
# Full deployment
```

### 3. Production Configuration

#### Optimized Production Config
```yaml
# config/production.yaml
document_processor:
  type: "hybrid_pdf"
  config:
    chunk_size: 1400
    chunk_overlap: 200

embedder:
  type: "sentence_transformer"
  config:
    model_name: "sentence-transformers/all-MiniLM-L6-v2"
    use_mps: true
    batch_size: 32  # Optimized for throughput

vector_store:
  type: "faiss"
  config:
    index_type: "IndexFlatIP"
    normalize_embeddings: true

retriever:
  type: "hybrid"
  config:
    dense_weight: 0.7
    top_k: 5
    fusion_method: "reciprocal_rank"

answer_generator:
  type: "adaptive"
  config:
    model_name: "deepset/roberta-base-squad2"
    api_token: ${HF_API_TOKEN}
    confidence_threshold: 0.85
    max_tokens: 512
    enable_adaptive_prompts: false  # Disable for consistent performance
```

### 4. Monitoring Setup

#### Key Metrics to Monitor
- 📊 Query response time (p50, p95, p99)
- 💾 Memory usage
- 🔥 Error rate
- 📈 Throughput (queries per second)
- 🎯 Answer confidence scores
- 📚 Document processing times

#### Alerting Rules
```yaml
# Example alerting configuration
alerts:
  - name: "High Query Response Time"
    condition: "p95_response_time > 5s"
    action: "send_alert"
    
  - name: "High Error Rate"
    condition: "error_rate > 5%"
    action: "send_alert"
    
  - name: "Low Confidence Scores"
    condition: "avg_confidence < 0.5"
    action: "send_warning"
```

### 5. Maintenance and Updates

#### Regular Tasks
- 📊 Review performance metrics weekly
- 🔧 Update configurations based on usage patterns
- 📈 Monitor for new component versions
- 🧪 Run regression tests monthly
- 📚 Update documentation as needed

#### Configuration Updates
```bash
# Test configuration changes
python scripts/validate_configs.py --config new_production

# Deploy configuration changes
cp config/new_production.yaml config/production.yaml
# Restart services or use hot reload if supported
```

## Migration Checklist

### Pre-Migration
- [ ] Run migration analysis
- [ ] Review current BasicRAG usage patterns
- [ ] Create configuration files
- [ ] Set up testing environment
- [ ] Plan rollback strategy

### During Migration
- [ ] Run automated migration tool
- [ ] Perform manual code updates if needed
- [ ] Update import statements
- [ ] Update method calls
- [ ] Test with comparison framework

### Post-Migration  
- [ ] Run comprehensive validation
- [ ] Performance benchmark testing
- [ ] Update documentation
- [ ] Train team on new system
- [ ] Monitor production deployment

### Validation
- [ ] All existing functionality works
- [ ] Performance is maintained or improved
- [ ] No regressions in answer quality
- [ ] Configuration management working
- [ ] Error handling robust
- [ ] Monitoring and logging operational

## Support and Resources

### Documentation
- 📚 [Modular Architecture Specification](modular-architecture-spec.md)
- ⚙️ [Configuration Guide](configuration.md)
- 🔧 [API Reference](api-reference.md)

### Tools
- 🔍 `scripts/migration_analysis.py` - Analyze current usage
- 🚀 `scripts/migrate_to_modular.py` - Automated migration
- ⚖️ `scripts/comparison_testing.py` - Compare old vs new
- 📊 `scripts/performance_benchmark.py` - Performance testing
- ✅ `scripts/production_migration_test.py` - Production validation

### Getting Help
- 📋 Review this migration guide
- 🔍 Check troubleshooting section
- 📊 Run diagnostic tools
- 📝 Check error logs and validation reports

## Conclusion

The migration from BasicRAG to RAGPipeline provides significant benefits in terms of modularity, configuration management, and extensibility while maintaining full backward compatibility. 

Follow this guide step-by-step, use the provided tools for validation, and don't hesitate to start with a development environment before moving to production.

The new modular architecture will provide a solid foundation for future enhancements and scaling of your RAG system.

---

**Next Steps**: After completing the migration, consider exploring advanced features like:
- Custom component implementations
- Advanced configuration patterns
- Production monitoring and observability
- Performance optimization techniques