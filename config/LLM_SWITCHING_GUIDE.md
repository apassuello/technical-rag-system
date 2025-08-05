# LLM Configuration Switching Guide

**Updated**: July 21, 2025  
**Applies to**: basic.yaml, demo.yaml, epic2.yaml  

---

## 🔄 Quick Switching Instructions

All three main configuration files now support easy switching between different LLM backends. Simply comment/uncomment the desired `llm_client` section.

### Configuration Files
- **`basic.yaml`**: Basic RAG system with minimal features
- **`demo.yaml`**: Demo-optimized with selective Epic 2 features  
- **`epic2.yaml`**: Full Epic 2 production configuration

---

## 🎯 LLM Options Available

### 1. Mock LLM (Testing)
**Use for**: Testing, development, CI/CD
**Requires**: No external dependencies
```yaml
llm_client:
  type: "mock"
  config:
    response_pattern: "technical"
    include_citations: true
    max_response_length: 512  # varies by config
    mock_delay: 0.05          # varies by config
```

### 2. Local Ollama LLM (Production)
**Use for**: Production, local development
**Requires**: Ollama running locally on port 11434
```yaml
llm_client:
  type: "ollama"
  config:
    model_name: "llama3.2:3b"
    base_url: "http://localhost:11434"
    timeout: 30
    max_retries: 3            # varies by config
```

### 3. HuggingFace API LLM (Cloud)
**Use for**: Cloud deployment, HuggingFace Spaces
**Requires**: HF_TOKEN environment variable
```yaml
llm_client:
  type: "huggingface"
  config:
    model_name: "microsoft/DialoGPT-medium"
    api_token: "${HF_TOKEN}"
    timeout: 30
    use_chat_completion: true
    fallback_models:
      - "google/gemma-2-2b-it"
      - "meta-llama/Llama-3.2-3B-Instruct"  # epic2.yaml only
      - "Qwen/Qwen2.5-1.5B-Instruct"        # epic2.yaml only
    max_tokens: 512           # varies by config
    temperature: 0.1
    top_p: 0.9
```

---

## 🔧 How to Switch

### Step 1: Choose Configuration File
Select which configuration you want to modify:
- `config/basic.yaml` - Basic functionality
- `config/demo.yaml` - Demo with neural reranking
- `config/epic2.yaml` - Full Epic 2 features

### Step 2: Edit LLM Section
Find the `answer_generator` section and locate the `llm_client` configurations.

### Step 3: Comment/Uncomment
1. **Comment out** the current active configuration (add `#` to each line)
2. **Uncomment** your desired configuration (remove `#` from each line)

### Example: Switch from Mock to Ollama in basic.yaml
```yaml
# Current: Mock LLM (comment this out)
# llm_client:
#   type: "mock"
#   config:
#     response_pattern: "technical"
#     include_citations: true
#     max_response_length: 512
#     mock_delay: 0.05

# New: Ollama LLM (uncomment this)
llm_client:
  type: "ollama"
  config:
    model_name: "llama3.2:3b"
    base_url: "http://localhost:11434"
    timeout: 30
    max_retries: 2
```

### Step 4: Set Environment Variables (HF API only)
If using HuggingFace API, set your token:
```bash
export HF_TOKEN="hf_your_token_here"
```

---

## 🚀 Configuration Differences

### basic.yaml
- **Mock**: 512 max tokens, 0.05s delay
- **Ollama**: 2 retries, basic timeout
- **HF API**: Simple fallback models

### demo.yaml  
- **Mock**: 768 max tokens, 0.1s delay, demo_mode enabled
- **Ollama**: 3 retries, demo optimized
- **HF API**: Demo-appropriate models

### epic2.yaml
- **Ollama**: 1024 max tokens, production timeouts
- **HF API**: Extended fallback model list, higher token limit

---

## ⚠️ Requirements & Setup

### Mock LLM
- **Dependencies**: None (built-in)
- **Setup**: Works immediately
- **Use case**: Testing, development

### Ollama LLM
- **Dependencies**: Ollama installed and running
- **Setup**: 
  1. Install Ollama: `curl -fsSL https://ollama.ai/install.sh | sh`
  2. Pull model: `ollama pull llama3.2:3b`
  3. Start server: `ollama serve` (usually auto-starts)
- **Use case**: Local production, development

### HuggingFace API
- **Dependencies**: HF Token, internet connection
- **Setup**:
  1. Get token: https://huggingface.co/settings/tokens
  2. Set environment: `export HF_TOKEN="your_token"`
  3. Install: `pip install huggingface-hub`
- **Use case**: Cloud deployment, HuggingFace Spaces

---

## 🧪 Testing Your Switch

After switching configurations, test with:

```python
# Quick test script
from src.core.platform_orchestrator import PlatformOrchestrator

# Initialize with your chosen config
po = PlatformOrchestrator("config/basic.yaml")  # or demo.yaml, epic2.yaml

# Test query
result = po.process_query("What is RISC-V?")
print(f"Answer: {result.answer}")
print(f"Confidence: {result.confidence}")
```

---

## 📊 Performance Comparison

| LLM Type | Speed | Quality | Dependencies | Cost |
|----------|--------|---------|-------------|------|
| Mock | ⚡ Instant | 🔧 Fixed | ✅ None | 💰 Free |
| Ollama | 🚀 Fast | 🎯 High | 📦 Local | 💰 Free |
| HF API | 🌐 Variable | 🎯 High | 🌍 Internet | 💳 Usage-based |

---

## 🔍 Troubleshooting

### Mock LLM Issues
- Should always work - no setup required

### Ollama LLM Issues  
- **Connection refused**: Check `ollama serve` is running
- **Model not found**: Run `ollama pull llama3.2:3b`
- **Timeout**: Increase timeout in config or check system resources

### HuggingFace API Issues
- **Authentication**: Verify `HF_TOKEN` is set correctly
- **Rate limits**: Check your HF account usage
- **Model errors**: Try fallback models or switch to different model

---

## 📝 Notes

- All configurations maintain the same `temperature`, `max_tokens`, and `confidence_threshold` at the top level
- Only the `llm_client` section changes between different LLM types
- HuggingFace API configurations include fallback models for reliability
- Environment variable substitution (`${HF_TOKEN}`) is supported in all configs

**Status**: ✅ **All three main configurations updated with easy LLM switching**