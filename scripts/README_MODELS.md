# Model Management Infrastructure

This directory contains scripts for managing ML models required by the RAG Portfolio System.

## Overview

The RAG system uses several machine learning models:

1. **Sentence Transformers** - For document and query embeddings
2. **Cross-Encoders** - For semantic reranking (optional)
3. **spaCy Models** - For NLP analysis (optional)
4. **Ollama Models** - For local LLM inference (optional)

## Quick Start

### Download All Required Models

```bash
# Download only required models (~180 MB)
python scripts/download_models.py --no-ollama

# Download all models including Ollama (~2.4 GB)
python scripts/download_models.py --include-ollama

# Download specific model type only
python scripts/download_models.py --model-type sentence_transformers
```

### Verify Model Installation

```bash
# Quick check (no loading)
python scripts/verify_models.py --quick

# Full verification (loads and tests models)
python scripts/verify_models.py

# Verify specific model type
python scripts/verify_models.py --model-type spacy
```

## Model Inventory

### Required Models (180 MB)

| Model | Size | Purpose |
|-------|------|---------|
| `sentence-transformers/all-MiniLM-L6-v2` | 90 MB | Default embedding model |
| `sentence-transformers/multi-qa-MiniLM-L6-cos-v1` | 90 MB | Multi-QA optimized embeddings |

**Total Required**: ~180 MB

### Optional Models (130 MB + 2 GB)

| Model | Size | Purpose | Used In |
|-------|------|---------|---------|
| `cross-encoder/ms-marco-MiniLM-L6-v2` | 90 MB | Semantic reranking | Epic 2 features |
| `en_core_web_sm` | 40 MB | NLP analysis | Query processor |
| `llama3.2:3b` | 2 GB | Local LLM | Answer generation |

**Total Optional**: ~2.13 GB

## Storage Requirements

### Minimal Installation
- **Size**: 180 MB
- **Models**: Required models only
- **Use Case**: Development with API-based LLM

```bash
python scripts/download_models.py --no-ollama
```

### Recommended Installation
- **Size**: 310 MB
- **Models**: Required + cross-encoder + spaCy
- **Use Case**: Full retrieval features without local LLM

```bash
python scripts/download_models.py --no-ollama
# spaCy will be downloaded when needed
```

### Full Installation
- **Size**: 2.4 GB
- **Models**: All models
- **Use Case**: Complete offline capability

```bash
python scripts/download_models.py --include-ollama
```

## Usage Examples

### Download Models

```bash
# Interactive download with size estimates
python scripts/download_models.py

# Skip Ollama (saves ~2 GB)
python scripts/download_models.py --no-ollama

# Force redownload
python scripts/download_models.py --force

# Download to custom directory
python scripts/download_models.py --cache-dir /path/to/models

# Non-interactive (for CI/CD)
echo "y" | python scripts/download_models.py
```

### Verify Models

```bash
# Quick check (just existence)
python scripts/verify_models.py --quick

# Full verification (loads and tests)
python scripts/verify_models.py

# Verbose output
python scripts/verify_models.py --verbose

# Check specific type
python scripts/verify_models.py --model-type sentence_transformers
```

## Model Locations

Models are cached in standard locations:

- **HuggingFace models**: `~/.cache/huggingface/hub/`
- **spaCy models**: Python site-packages
- **Ollama models**: `~/.ollama/models/`

### Custom Cache Directory

You can specify a custom cache directory:

```bash
export HF_HOME=/custom/path/huggingface
python scripts/download_models.py
```

## Docker Integration

### Volume Mounts

The docker-compose.yml includes volume mounts for model caching:

```yaml
volumes:
  - huggingface_models:/app/models/huggingface
```

This ensures models persist across container restarts and are shared between services.

### Pre-downloading Models for Docker

**Option 1: Download to volume before starting**
```bash
# Download models locally first
python scripts/download_models.py --no-ollama

# Start Docker with volume mount
docker-compose up
```

**Option 2: Download inside container**
```bash
# Start services
docker-compose up -d

# Download models in container
docker-compose exec query-analyzer python scripts/download_models.py --no-ollama
```

**Option 3: Build-time download (Dockerfile)**
```dockerfile
# Add to Dockerfile
RUN python scripts/download_models.py --no-ollama --yes
```

### .dockerignore

The `.dockerignore` file excludes model caches from being copied during build:

```
.cache/
.huggingface/
models/
.ollama/
```

This prevents large model files from being included in Docker images.

## CI/CD Integration

### GitHub Actions Example

```yaml
- name: Download ML Models
  run: |
    python scripts/download_models.py --no-ollama
    python scripts/verify_models.py --quick

- name: Cache Models
  uses: actions/cache@v3
  with:
    path: ~/.cache/huggingface
    key: ${{ runner.os }}-models-${{ hashFiles('config/models.yaml') }}
```

### Validation in CI

```bash
# Verify models are available
python scripts/verify_models.py --quick || exit 1
```

## Troubleshooting

### Models Not Found After Download

**Problem**: Verification fails after successful download

**Solution**: Check cache directory
```bash
ls -lah ~/.cache/huggingface/hub/
```

### Disk Space Issues

**Problem**: Insufficient disk space

**Solution**:
1. Check available space: `df -h`
2. Clean old model versions: `rm -rf ~/.cache/huggingface/hub/models--*`
3. Download only required models: `--no-ollama`

### spaCy Model Import Error

**Problem**: `No module named 'spacy'`

**Solution**: Install spaCy
```bash
pip install spacy>=3.7.0
python -m spacy download en_core_web_sm
```

### Ollama Not Available

**Problem**: `Ollama not installed`

**Solution**: Install Ollama from https://ollama.ai
```bash
# macOS
brew install ollama

# Linux
curl -fsSL https://ollama.ai/install.sh | sh

# Pull model
ollama pull llama3.2:3b
```

### Network Issues During Download

**Problem**: Download fails with timeout

**Solution**:
1. Check internet connection
2. Use retry: `--force` flag will retry failed downloads
3. Download individual models:
   ```bash
   python scripts/download_models.py --model-type sentence_transformers
   ```

### Permission Errors

**Problem**: Cannot write to cache directory

**Solution**:
```bash
# Check permissions
ls -ld ~/.cache

# Fix permissions
chmod 755 ~/.cache
mkdir -p ~/.cache/huggingface
```

## Model Configuration

Models are configured in `config/models.yaml`. See that file for:

- Model versions and sizes
- Download priorities
- Docker-specific configurations
- Environment overrides

## Advanced Usage

### Selective Model Download

Download only what you need:

```python
from download_models import ModelDownloader

downloader = ModelDownloader()

# Download only sentence transformers
stats = downloader.download_all(
    model_types=["sentence_transformers"],
    include_ollama=False
)
```

### Custom Model Paths

Specify custom paths for different model types:

```python
import os
os.environ['HF_HOME'] = '/data/models/huggingface'
os.environ['OLLAMA_MODELS'] = '/data/models/ollama'
```

### Offline Mode

Once models are downloaded, the system works completely offline:

1. Download all models: `python scripts/download_models.py --include-ollama`
2. Disconnect from internet
3. Run verification: `python scripts/verify_models.py`
4. Use system normally

## Model Updates

### Checking for Updates

Models are pulled from HuggingFace and Ollama registries. To update:

```bash
# Force redownload (gets latest versions)
python scripts/download_models.py --force
```

### Version Pinning

For production, consider pinning specific model versions in `config/models.yaml`:

```yaml
sentence_transformers:
  default:
    name: sentence-transformers/all-MiniLM-L6-v2
    version: "v2.0"  # Pin to specific version
```

## Security Considerations

### Trust Remote Code

By default, remote code execution is DISABLED:

```python
# In download_models.py
trust_remote_code: false  # NEVER allow remote code
```

### Model Verification

Always verify model checksums in production:

```yaml
security:
  verify_checksums: true
```

### Model Scanning

Consider scanning models for security issues:

```bash
# Example with custom scanner
python scripts/verify_models.py --security-scan
```

## Performance Optimization

### Batch Downloads

Download models in parallel (for faster setup):

```bash
# Download different types concurrently
python scripts/download_models.py --model-type sentence_transformers &
python scripts/download_models.py --model-type cross_encoder &
wait
```

### Model Preloading

For faster startup, preload models:

```python
from sentence_transformers import SentenceTransformer

# Preload on startup
model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
```

### Caching Strategy

Use Docker volumes to share models across containers:

```yaml
volumes:
  huggingface_models:
    driver: local
```

## Support

For issues or questions:

1. Check this README
2. Review `config/models.yaml` for configuration
3. Run verification: `python scripts/verify_models.py --verbose`
4. Check model sizes: `du -sh ~/.cache/huggingface`

## Related Documentation

- Model Configuration: `config/models.yaml`
- Docker Setup: `docker-compose.yml`
- System Architecture: Main `README.md`
