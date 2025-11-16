# Ollama Setup Guide

Quick guide to set up Ollama for local LLM inference in the RAG system.

## Installation (Mac)

```bash
# Install Ollama via Homebrew
brew install ollama

# Verify installation
ollama --version
```

## Download Models

### Recommended Models

**Option 1: llama3.2:3b** (Recommended for Mac)
- Size: ~2GB
- Speed: Fast
- Quality: Good for technical Q&A

```bash
ollama pull llama3.2:3b
```

**Option 2: llama3.1:8b** (Better quality)
- Size: ~4.7GB
- Speed: Moderate
- Quality: Excellent

```bash
ollama pull llama3.1:8b
```

**Option 3: qwen2.5:7b** (Alternative)
- Size: ~4.4GB
- Good for technical documentation

```bash
ollama pull qwen2.5:7b
```

## Start Ollama Service

### Option A: Run as Background Service (Recommended)

```bash
# Start service (runs in background)
brew services start ollama

# Check status
brew services list | grep ollama

# Stop service
brew services stop ollama
```

### Option B: Run in Terminal

```bash
# Start Ollama (keeps terminal open)
ollama serve

# In another terminal, test it
ollama run llama3.2:3b "Hello!"
```

## Test Ollama

```bash
# Interactive chat
ollama run llama3.2:3b

# Single query
ollama run llama3.2:3b "What is RISC-V?"

# Check downloaded models
ollama list

# Test API (should return list of models)
curl http://localhost:11434/api/tags
```

## Using with RAG System

Once Ollama is running:

```bash
# Test RAG demo
python scripts/demo_rag.py --query "What are RISC-V vector instructions?"

# Interactive mode
python scripts/demo_rag.py --interactive

# Streamlit app
streamlit run app.py
```

## Troubleshooting

### Ollama Not Running

```bash
# Check if Ollama service is running
curl http://localhost:11434/api/tags

# If not, start it
brew services start ollama
# OR
ollama serve
```

### Model Not Found

```bash
# List downloaded models
ollama list

# If empty, download a model
ollama pull llama3.2:3b
```

### Port Already in Use

```bash
# Check what's using port 11434
lsof -i :11434

# Kill the process if needed
kill -9 <PID>

# Restart Ollama
brew services restart ollama
```

### Performance Issues

```bash
# Use smaller model
ollama pull llama3.2:1b

# Check system resources
htop
# (install: brew install htop)
```

## Alternative: Use OpenAI API

If Ollama doesn't work or you prefer cloud-based LLM:

```bash
# Set API key
export OPENAI_API_KEY="sk-..."

# Use with RAG system
python scripts/demo_rag.py --query "..." --use-openai
```

## Recommended Setup for RAG Portfolio

```bash
# 1. Install Ollama
brew install ollama

# 2. Start service
brew services start ollama

# 3. Download model
ollama pull llama3.2:3b

# 4. Verify
ollama list
curl http://localhost:11434/api/tags

# 5. Test with RAG
python scripts/demo_rag.py --interactive
```

## Model Comparison

| Model | Size | Speed | Quality | Best For |
|-------|------|-------|---------|----------|
| llama3.2:1b | ~1GB | Very Fast | Basic | Quick testing |
| llama3.2:3b | ~2GB | Fast | Good | Production (Mac) |
| llama3.1:8b | ~4.7GB | Moderate | Excellent | Best quality |
| qwen2.5:7b | ~4.4GB | Moderate | Very Good | Technical docs |

## Resources

- Ollama Documentation: https://ollama.com/
- Model Library: https://ollama.com/library
- GitHub: https://github.com/ollama/ollama
