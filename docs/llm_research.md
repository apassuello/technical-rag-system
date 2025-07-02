# Local LLM Research for Technical QA on Apple Silicon M4-Pro

## Date: 2025-07-02
## Objective: Evaluate suitable local LLMs for technical documentation QA

## Requirements
- **Hardware**: Apple Silicon M4-Pro with 16GB+ RAM
- **Use Case**: Technical documentation Q&A with citation
- **Memory Budget**: <4GB for LLM inference
- **Performance Target**: <2 seconds per response
- **Quality**: Good performance on technical/embedded systems content

## Top Candidates for Apple Silicon

### 1. Llama 3.2 (3B) via Ollama
**Pros**:
- Excellent Apple Silicon optimization via Ollama
- 3B parameter sweet spot for M4-Pro performance
- Strong instruction following
- ~2GB memory usage
- Native Metal Performance Shaders support

**Cons**:
- May struggle with very complex technical queries
- Limited context window (8K tokens)

**Installation**:
```bash
# Install Ollama
brew install ollama

# Pull model
ollama pull llama3.2:3b
```

### 2. Mistral 7B Instruct (Quantized) via llama.cpp
**Pros**:
- Excellent technical reasoning
- 4-bit quantization fits in 4GB
- Strong code understanding
- Good with structured outputs

**Cons**:
- Slower than 3B models
- Requires careful quantization

**Installation**:
```bash
# Using llama-cpp-python with Metal support
CMAKE_ARGS="-DLLAMA_METAL=on" pip install llama-cpp-python
```

### 3. Phi-3.5-mini (3.8B) via Transformers
**Pros**:
- Microsoft's optimized small model
- Excellent technical performance
- Good code understanding
- Efficient tokenizer

**Cons**:
- Less community support
- May require more prompt engineering

**Installation**:
```bash
pip install transformers accelerate
```

### 4. Qwen2.5-Coder-3B via Ollama
**Pros**:
- Specifically trained for code/technical content
- Excellent performance on technical documentation
- Optimized for structured outputs
- Good citation formatting

**Cons**:
- Newer model, less tested
- May be overly code-focused

**Installation**:
```bash
ollama pull qwen2.5-coder:3b
```

## Recommendation: Llama 3.2 (3B) via Ollama

### Rationale
1. **Best Apple Silicon Support**: Ollama provides excellent Metal optimization
2. **Optimal Size**: 3B parameters balance quality and speed on M4-Pro
3. **Production Ready**: Mature ecosystem, good community support
4. **Easy Integration**: Simple API, supports streaming
5. **Proven Performance**: Widely tested on technical content

### Fallback Strategy
- **Primary**: Llama 3.2 (3B) for most queries
- **Complex Queries**: Mistral 7B for difficult technical questions
- **API Fallback**: GPT-3.5-turbo when local models struggle

## Integration Plan

### 1. Ollama Setup
```python
import ollama

class LocalLLMGenerator:
    def __init__(self, model_name="llama3.2:3b"):
        self.client = ollama.Client()
        self.model = model_name
        
    def generate(self, prompt, context, stream=True):
        """Generate answer with citations from context."""
        response = self.client.chat(
            model=self.model,
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": self.format_prompt(prompt, context)}
            ],
            stream=stream
        )
        return response
```

### 2. Memory Optimization
- Use 4-bit quantization if needed
- Implement context windowing for long documents
- Cache model in memory between requests
- Use streaming to reduce perceived latency

### 3. Performance Targets
- Model loading: <5 seconds (one-time)
- Inference: <2 seconds for 200-token response
- Memory usage: <3GB steady state
- Throughput: 10+ requests/minute

## Next Steps
1. Install Ollama and pull Llama 3.2 (3B)
2. Create answer generation module with this model
3. Implement prompt templates for technical QA
4. Test with actual technical documentation
5. Add Mistral 7B as fallback for complex queries