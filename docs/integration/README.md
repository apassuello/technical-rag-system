# Integration Documentation

Guides for integrating external models and services with the Epic 8 RAG Platform.

---

## 🤖 Available Integrations

### [GPT-OSS Integration](./gpt-oss/)

**OpenAI's Open-Source Models** (August 2025 Release)

Integration of OpenAI's GPT-OSS models (gpt-oss-120b and gpt-oss-20b) as advanced Answer Generator models.

**Models**:
- **gpt-oss-120b**: 117B parameters, runs on 80GB GPU
- **gpt-oss-20b**: 21B parameters, runs on 16GB GPU
- **License**: Apache 2.0 (fully open for commercial use)
- **Performance**: Matches OpenAI o4-mini on reasoning tasks

**Integration Approaches**:
1. **HuggingFace Hub** (RECOMMENDED) - 1-2 hours setup
2. **Native Integration** - 4-6 hours setup, full control
3. **Ollama Integration** (Future) - Wait for Ollama support

**Cost Analysis**:
- API vs Self-Hosted comparison
- Break-even analysis (6-12 months)
- Zero API costs for self-hosted

📚 **Documentation**:
- [Quick Start](./gpt-oss/README.md) - Executive summary and overview
- [Integration Plan](./gpt-oss/integration-plan.md) - Complete implementation guide

🎯 **Use Cases**:
- Complex reasoning queries (Epic 1 adaptive routing)
- Technical documentation analysis
- Advanced question answering
- Cost optimization vs. commercial APIs

---

## 🔄 Integration Status

| Integration | Status | Cost | Complexity | Documentation |
|-------------|--------|------|-----------|---------------|
| GPT-OSS via HF API | ✅ Ready | FREE tier | Low | Complete |
| GPT-OSS Native | ✅ Ready | GPU rental | Medium | Complete |
| Ollama (existing) | ✅ Production | FREE | Low | Built-in |
| Mistral via HF | ✅ Production | FREE | Low | Built-in |

---

## 📖 Related Documentation

- **Deployment**: [AWS ECS Deployment](../deployment/aws-ecs/) includes GPT-OSS integration
- **Configuration**: See `/config/epic1_ecs_deployment.yaml` for model routing
- **Architecture**: [Epic 1 Adaptive Routing](../epics/epic1-specification.md)

---

## 🚀 Quick Start: GPT-OSS Integration

```bash
# 1. Install dependencies
pip install -U huggingface-hub transformers accelerate bitsandbytes

# 2. Authenticate with HuggingFace
export HUGGINGFACE_TOKEN="hf_xxxxx"

# 3. Test GPT-OSS access
curl -H "Authorization: Bearer $HUGGINGFACE_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"inputs": "Explain quantum computing"}' \
     https://api-inference.huggingface.co/models/openai/gpt-oss-20b

# 4. Deploy with Epic 1 routing (already configured in ECS deployment)
cd deployment/ecs
./deploy.sh deploy
```

---

## 💡 Integration Strategy

The Epic 8 platform uses **3-tier intelligent model routing**:

```
Simple Queries (60%)    → Ollama llama3.2:3b     [FREE - Local]
Medium Queries (30%)    → Mistral-7B HF API      [FREE - HF tokens]
Complex Queries (10%)   → GPT-OSS-20B HF API     [FREE tier/cheap]
```

This maximizes cost efficiency while providing high-quality answers across all query complexities.

---

## 📊 Cost Comparison

| Model | Deployment | Cost per 1M tokens | Quality | Setup Time |
|-------|------------|-------------------|---------|------------|
| OpenAI GPT-4 | API | $30-60 | Excellent | 5 min |
| OpenAI GPT-4o-mini | API | $0.15 | Very Good | 5 min |
| GPT-OSS-120b | Self-hosted GPU | $10-20 | Very Good | 4-6 hours |
| GPT-OSS-20b | HF API | $0-0.01 | Good | 1-2 hours |
| Mistral-7B | HF API | $0 | Good | 5 min |
| Ollama Local | Local | $0 | Good | 5 min |

**Recommendation**: Use HuggingFace API for GPT-OSS (FREE tier, easy setup)

---

## 🛠️ Future Integrations

Potential integrations to consider:

- **Claude via AWS Bedrock** - High-quality reasoning
- **Cohere** - Retrieval optimization
- **Anthropic Claude API** - Advanced reasoning
- **Azure OpenAI** - Enterprise compliance
- **Google Gemini** - Multimodal capabilities

---

## 🆘 Need Help?

1. **GPT-OSS Questions**: See [GPT-OSS Integration Plan](./gpt-oss/integration-plan.md)
2. **Model Routing**: Check Epic 1 complexity-based routing configuration
3. **Cost Optimization**: Run cost analysis in integration plan
4. **Troubleshooting**: Each integration guide has troubleshooting section

---

**Key Insight**: The Epic 8 platform is designed for easy model integration. All models use the adapter pattern, making it simple to add new providers without changing core code.
