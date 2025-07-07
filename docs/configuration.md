# RAG Pipeline Configuration Guide

## Overview

The RAG pipeline uses YAML-based configuration with environment-specific settings and runtime overrides through environment variables. The configuration system provides type-safe validation, automatic environment detection, and comprehensive error reporting.

## Configuration Files

### Available Configurations

| File | Purpose | Use Case |
|------|---------|----------|
| `config/default.yaml` | Baseline configuration | General use, fallback configuration |
| `config/dev.yaml` | Development settings | Local development with debugging features |
| `config/test.yaml` | Testing configuration | Automated testing with minimal resources |
| `config/production.yaml` | Production deployment | Cloud deployment with optimized settings |

### Environment Detection

The configuration system automatically detects the environment using:

1. **RAG_ENV environment variable**: `export RAG_ENV=production`
2. **Explicit config path**: `RAGPipeline(Path("config/custom.yaml"))`
3. **Auto-discovery**: Looks for `{env}.yaml` in the config directory
4. **Fallback**: Uses `default.yaml` if no specific config found

## Configuration Structure

### Document Processor

Handles PDF parsing and text chunking.

```yaml
document_processor:
  type: "hybrid_pdf"  # Component type (registered in ComponentRegistry)
  config:
    chunk_size: 1024          # Target chunk size in characters
    chunk_overlap: 128        # Character overlap between chunks
    min_chunk_size: 400       # Minimum chunk size (smaller chunks filtered)
    max_chunk_size: 1600      # Maximum chunk size (larger chunks split)
    quality_threshold: 0.6    # Quality threshold (0.0-1.0)
    filter_artifacts: true    # Remove PDF artifacts and boilerplate
    debug_mode: false         # Enable debug output
```

**Available Types:**
- `hybrid_pdf`: Production-grade PDF processor with TOC navigation and quality filtering

### Embedder

Converts text chunks to vector embeddings.

```yaml
embedder:
  type: "sentence_transformer"
  config:
    model_name: "sentence-transformers/multi-qa-MiniLM-L6-cos-v1"
    batch_size: 32            # Embedding batch size
    use_mps: true             # Apple Silicon MPS acceleration
    cache_embeddings: true    # Cache embeddings for performance
    max_seq_length: 512       # Maximum sequence length
    debug_embeddings: false   # Log embedding statistics
```

**Available Models:**
- `sentence-transformers/multi-qa-MiniLM-L6-cos-v1`: Optimized for question-answering (384 dimensions)
- `sentence-transformers/all-MiniLM-L6-v2`: General purpose, smaller model (384 dimensions)

### Vector Store

Manages vector storage and similarity search.

```yaml
vector_store:
  type: "faiss"
  config:
    embedding_dim: 384         # Must match embedder output dimension
    index_type: "IndexFlatIP"  # FAISS index type
    normalize_embeddings: true # Normalize for cosine similarity
    metric: "cosine"          # Distance metric
    cache_size: 10000         # Cache size for frequent queries
    save_index: false         # Persist index to disk
```

**Index Types:**
- `IndexFlatIP`: Inner product (cosine similarity with normalization)
- `IndexFlatL2`: L2 distance (Euclidean distance)

### Retriever

Combines dense and sparse retrieval methods.

```yaml
retriever:
  type: "hybrid"
  config:
    dense_weight: 0.7         # Weight for semantic similarity (0.0-1.0)
    embedding_model: "sentence-transformers/multi-qa-MiniLM-L6-cos-v1"
    use_mps: true             # Apple Silicon acceleration
    bm25_k1: 1.2             # BM25 term frequency saturation
    bm25_b: 0.75             # BM25 document length normalization
    rrf_k: 1                 # Reciprocal Rank Fusion parameter
    enable_reranking: false   # Enable result reranking
    diversity_threshold: 0.1  # Source diversity threshold
```

**Parameters:**
- **dense_weight**: Higher values favor semantic similarity, lower values favor keyword matching
- **rrf_k**: Lower values give more weight to top-ranked results (1-60 range)
- **bm25_k1**: Controls term frequency saturation (1.2-2.0 typical)
- **bm25_b**: Controls length normalization (0.0-1.0, where 0.75 is typical)

### Answer Generator

Generates natural language answers from retrieved context.

```yaml
answer_generator:
  type: "adaptive"
  config:
    model_name: "microsoft/DialoGPT-medium"  # HuggingFace model name
    api_token: "${HUGGINGFACE_API_TOKEN}"    # API token (env variable)
    temperature: 0.3          # Generation temperature (0.0-1.0)
    max_tokens: 512           # Maximum response length
    use_ollama: false         # Use local Ollama server
    ollama_url: "http://localhost:11434"
    enable_adaptive_prompts: true    # Context-aware prompting
    enable_chain_of_thought: false   # Multi-step reasoning
    confidence_threshold: 0.85       # Minimum confidence for answers
    retry_attempts: 3                # Retry failed requests
    timeout_seconds: 30              # Request timeout
```

**Model Options:**
- `microsoft/DialoGPT-medium`: Conversational AI, good for dialogue
- `sshleifer/distilbart-cnn-12-6`: Summarization model, fast and reliable
- `deepset/roberta-base-squad2`: Question-answering specialist

### Global Settings

System-wide configuration options.

```yaml
global_settings:
  environment: "production"    # Environment identifier
  log_level: "INFO"           # Logging level (DEBUG, INFO, WARNING, ERROR)
  enable_metrics: true        # Collect performance metrics
  cache_embeddings: true      # Enable embedding caching
  max_concurrent_requests: 5  # Concurrent request limit
  
  # Optional advanced settings
  optimization:
    enable_batch_processing: true
    batch_size: 16
    memory_limit_mb: 2048
    
  security:
    api_key_required: true
    rate_limiting: true
    
  development:
    debug_mode: false
    profile_performance: false
    save_intermediate_data: false
```

## Environment Variable Overrides

Override any configuration value using environment variables with the `RAG_` prefix and double underscores for nesting:

```bash
# Override embedder model
export RAG_EMBEDDER__CONFIG__MODEL_NAME="sentence-transformers/all-MiniLM-L6-v2"

# Override answer generator settings
export RAG_ANSWER_GENERATOR__CONFIG__TEMPERATURE=0.1
export RAG_ANSWER_GENERATOR__CONFIG__MAX_TOKENS=256

# Override global settings
export RAG_GLOBAL_SETTINGS__LOG_LEVEL="DEBUG"
export RAG_GLOBAL_SETTINGS__ENABLE_METRICS=false
```

### Common Environment Variables

```bash
# API tokens
export HUGGINGFACE_API_TOKEN="your_token_here"
export HF_TOKEN="your_token_here"  # Alternative name

# Environment selection
export RAG_ENV="production"

# Quick development overrides
export RAG_GLOBAL_SETTINGS__LOG_LEVEL="DEBUG"
export RAG_EMBEDDER__CONFIG__USE_MPS=false
export RAG_ANSWER_GENERATOR__CONFIG__USE_OLLAMA=true
```

## Configuration Examples

### Minimal Testing Setup

```yaml
# config/minimal.yaml
document_processor:
  type: "hybrid_pdf"
  config: {chunk_size: 512, chunk_overlap: 64}

embedder:
  type: "sentence_transformer" 
  config: {model_name: "sentence-transformers/all-MiniLM-L6-v2", use_mps: false}

vector_store:
  type: "faiss"
  config: {embedding_dim: 384, index_type: "IndexFlatL2", normalize_embeddings: false}

retriever:
  type: "hybrid"
  config: {dense_weight: 0.6, rrf_k: 5}

answer_generator:
  type: "adaptive"
  config: {model_name: "sshleifer/distilbart-cnn-12-6", temperature: 0.0, max_tokens: 128}

global_settings: {environment: "minimal", log_level: "ERROR"}
```

### High-Performance Setup

```yaml
# config/performance.yaml
document_processor:
  type: "hybrid_pdf"
  config: {chunk_size: 1400, chunk_overlap: 200, quality_threshold: 0.9}

embedder:
  type: "sentence_transformer"
  config:
    model_name: "sentence-transformers/multi-qa-MiniLM-L6-cos-v1"
    batch_size: 64
    use_mps: true
    cache_embeddings: true

vector_store:
  type: "faiss"
  config: 
    embedding_dim: 384
    index_type: "IndexFlatIP"
    normalize_embeddings: true
    cache_size: 50000

retriever:
  type: "hybrid"
  config:
    dense_weight: 0.8
    rrf_k: 1
    enable_reranking: true

answer_generator:
  type: "adaptive"
  config:
    model_name: "microsoft/DialoGPT-medium"
    enable_adaptive_prompts: true
    confidence_threshold: 0.9

global_settings:
  optimization: {enable_batch_processing: true, batch_size: 32}
  max_concurrent_requests: 10
```

## Configuration Validation

### Automatic Validation

The system automatically validates:
- Required fields are present
- Data types match expected types (int, float, bool, str)
- Enum values are valid
- Component types are registered
- Embedding dimensions are consistent
- Model names are properly formatted

### Manual Validation

```python
from src.core.config import ConfigManager

# Validate a configuration file
config_manager = ConfigManager(Path("config/custom.yaml"))
is_valid = config_manager.validate()  # Raises ValueError if invalid

# Check specific component
component_config = config_manager.get_component_config("embedder")
```

### Common Validation Errors

1. **Dimension Mismatch**: Vector store embedding_dim doesn't match embedder output
2. **Missing Component**: Component type not registered in ComponentRegistry
3. **Invalid Range**: Parameters outside valid ranges (e.g., temperature > 1.0)
4. **Model Not Found**: Invalid HuggingFace model name
5. **Missing Token**: API token required but not provided

## Best Practices

### Environment-Specific Settings

1. **Development**: Enable debugging, use local models, smaller batches
2. **Testing**: Minimal resources, deterministic settings, fast execution
3. **Production**: Optimized settings, API tokens, monitoring enabled

### Performance Optimization

1. **Chunk Size**: 1024-1400 characters for optimal semantic coherence
2. **Overlap**: 10-15% of chunk size for context preservation
3. **Batch Size**: 16-32 for embedding generation (adjust for memory)
4. **Dense Weight**: 0.7-0.8 for technical documentation
5. **RRF K**: 1-5 for production, higher values for experimentation

### Security Considerations

1. **Never commit API tokens** to version control
2. **Use environment variables** for sensitive configuration
3. **Enable rate limiting** in production
4. **Validate all inputs** before processing
5. **Use HTTPS** for API endpoints

### Debugging Configuration

1. **Enable debug mode** in development environment
2. **Use verbose logging** for troubleshooting
3. **Save intermediate results** for analysis
4. **Profile performance** to identify bottlenecks
5. **Test with minimal configuration** first

## Troubleshooting

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| "Component type not found" | Unregistered component | Check ComponentRegistry imports |
| "Dimension mismatch" | Inconsistent embedding dimensions | Verify embedder and vector store settings |
| "API rate limit exceeded" | Too many requests | Reduce max_concurrent_requests |
| "Model not found" | Invalid model name | Check HuggingFace model availability |
| "Memory error" | Batch size too large | Reduce batch_size in embedder config |

### Debug Configuration

```bash
# Enable maximum debugging
export RAG_ENV="dev"
export RAG_GLOBAL_SETTINGS__LOG_LEVEL="DEBUG"
export RAG_GLOBAL_SETTINGS__DEBUG_MODE=true

# Run with debug config
python test_phase4.py
```

### Configuration Testing

```python
# Test configuration loading
from src.core.config import ConfigManager
from pathlib import Path

# Test each environment
for env in ["dev", "test", "production"]:
    try:
        config = ConfigManager(env=env).config
        print(f"✅ {env} config valid")
    except Exception as e:
        print(f"❌ {env} config error: {e}")
```

This configuration system provides flexible, type-safe configuration management for all deployment scenarios while maintaining backward compatibility and ease of use.