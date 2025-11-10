# GPT-OSS Integration Plan
## OpenAI's Open Source Models in Epic 8 Answer Generator

**Date**: November 10, 2025
**Target Models**: gpt-oss-120b (117B params) & gpt-oss-20b (21B params)
**License**: Apache 2.0
**Status**: READY FOR IMPLEMENTATION

---

## 🎯 Executive Summary

This plan details the integration of OpenAI's newly released open-source GPT-OSS models into the Epic 8 Answer Generator system, enabling advanced reasoning capabilities with local deployment options.

### Key Benefits

✅ **Apache 2.0 License**: Fully open for commercial use
✅ **Superior Performance**: Matches/exceeds o4-mini on reasoning tasks
✅ **Hardware Efficient**: 120B model runs on single 80GB GPU, 20B model on 16GB
✅ **Cost Optimization**: No API costs for self-hosted deployment
✅ **4-bit Quantization**: Fast inference with MXFP4 scheme

---

## 📊 GPT-OSS Model Specifications

### gpt-oss-120b (Large Model)

**Parameters**: 117 billion
**Architecture**: Mixture-of-Experts (MoE)
**Quantization**: 4-bit MXFP4
**Memory Requirement**: 80GB VRAM (single GPU)
**Performance**: Matches OpenAI o4-mini on benchmarks

**Benchmarks**:
- Codeforces: Competitive coding performance
- MMLU: General problem solving
- HLE: High-level reasoning
- TauBench: Tool calling capabilities

### gpt-oss-20b (Compact Model)

**Parameters**: 21 billion
**Architecture**: Mixture-of-Experts (MoE)
**Quantization**: 4-bit MXFP4
**Memory Requirement**: 16GB VRAM (edge devices compatible)
**Performance**: Similar to OpenAI o3-mini

**Use Cases**:
- Edge deployment
- Cost-sensitive applications
- High-throughput scenarios
- Development and testing

---

## 🏗️ Integration Architecture

### Current System Analysis

**Existing LLM Adapters**:
```python
# Current adapters in src/components/generators/llm_adapters/
- OllamaAdapter       # Local models via Ollama
- OpenAIAdapter       # GPT models via API
- MistralAdapter      # Mistral models via API
- HuggingFaceAdapter  # HuggingFace Inference API
- MockLLMAdapter      # Testing without dependencies
```

**Answer Generator Architecture**:
```
Epic1AnswerGenerator
├── Adaptive Router (query complexity → model selection)
├── LLM Adapters (pluggable backends)
├── Cost Tracker (usage monitoring)
└── Fallback Chain (reliability)
```

### Integration Strategy: Three Options

#### **Option 1: HuggingFace Hub (RECOMMENDED)**

**Approach**: Use existing HuggingFaceAdapter with GPT-OSS models
**Implementation Time**: 1-2 hours
**Advantages**:
- ✅ No new adapter code required
- ✅ Automatic model downloading from HuggingFace
- ✅ Works with existing infrastructure
- ✅ Easiest deployment

**Configuration**:
```yaml
llm_client:
  type: "huggingface"
  config:
    model_name: "openai/gpt-oss-120b"  # or "openai/gpt-oss-20b"
    api_token: "${HF_TOKEN}"
    use_inference_api: false  # For local inference
    device: "cuda:0"
    load_in_4bit: true
```

**Requirements**:
- HuggingFace Hub token (free)
- GPU with sufficient VRAM (80GB for 120B, 16GB for 20B)
- `transformers` library >=4.30.0

#### **Option 2: Native Integration via Transformers**

**Approach**: Create dedicated GPTOSSAdapter using transformers directly
**Implementation Time**: 4-6 hours
**Advantages**:
- ✅ Full control over inference
- ✅ Optimized for GPT-OSS specifics
- ✅ Better performance tuning

**New File**: `src/components/generators/llm_adapters/gptoss_adapter.py`

```python
class GPTOSSAdapter(BaseLLMAdapter):
    """
    Native adapter for OpenAI GPT-OSS models.

    Features:
    - Direct transformers integration
    - 4-bit quantization support
    - Optimized for MoE architecture
    - Flash Attention 2 support
    """

    def __init__(self,
                 model_name: str = "openai/gpt-oss-20b",
                 device: str = "cuda:0",
                 load_in_4bit: bool = True,
                 use_flash_attention: bool = True,
                 **kwargs):
        # Implementation details
        pass
```

#### **Option 3: Ollama Integration** (Future)

**Approach**: Wait for Ollama to add GPT-OSS support
**Implementation Time**: Depends on Ollama team
**Advantages**:
- ✅ Use existing OllamaAdapter
- ✅ Familiar deployment workflow
- ✅ No infrastructure changes

**Note**: As of November 2025, Ollama has not yet added GPT-OSS models. Monitor: https://github.com/ollama/ollama/issues

---

## 🔧 Implementation Plan

### Phase 1: HuggingFace Integration (QUICK START)

**Duration**: 1-2 hours
**Goal**: Get GPT-OSS models running with minimal changes

#### Step 1: Install Dependencies
```bash
# From project root
cd project-1-technical-rag

# Install HuggingFace Hub and transformers
pip install -U huggingface-hub transformers accelerate bitsandbytes

# Verify installation
python -c "from transformers import AutoModelForCausalLM; print('OK')"
```

#### Step 2: Authenticate with HuggingFace
```bash
# Get token from https://huggingface.co/settings/tokens
export HF_TOKEN="your_huggingface_token_here"

# Or login via CLI
huggingface-cli login
```

#### Step 3: Create Configuration File

**File**: `config/gptoss_120b.yaml`

```yaml
# Epic 8 Configuration with GPT-OSS-120B
generator:
  type: "epic1"  # Use adaptive generator

  routing:
    enabled: true
    default_strategy: "quality_first"

    strategies:
      quality_first:
        simple_query_model: "ollama/llama3.2:3b"
        medium_query_model: "huggingface/openai/gpt-oss-20b"
        complex_query_model: "huggingface/openai/gpt-oss-120b"

  llm_client:
    type: "huggingface"
    config:
      model_name: "openai/gpt-oss-120b"
      api_token: "${HF_TOKEN}"
      use_inference_api: false
      device_map: "auto"
      load_in_4bit: true
      torch_dtype: "auto"
      trust_remote_code: false
      max_new_tokens: 2048
      temperature: 0.7
      top_p: 0.9

  fallback:
    enabled: true
    fallback_model: "ollama/llama3.2:3b"

  cost_tracking:
    enabled: true
    # GPT-OSS has no API costs, but track GPU usage
    compute_cost_per_second: 0.0001  # Estimated GPU cost
```

**File**: `config/gptoss_20b.yaml` (For edge deployment)

```yaml
# Epic 8 Configuration with GPT-OSS-20B (Edge-Friendly)
generator:
  type: "epic1"

  llm_client:
    type: "huggingface"
    config:
      model_name: "openai/gpt-oss-20b"
      api_token: "${HF_TOKEN}"
      device_map: "auto"
      load_in_4bit: true
      max_memory: {0: "14GB"}  # Reserve 2GB for system
      torch_dtype: "auto"
      max_new_tokens: 2048
```

#### Step 4: Test Integration

**Test Script**: `tests/test_gptoss_integration.py`

```python
#!/usr/bin/env python3
"""
Test GPT-OSS integration with Epic 8 Answer Generator.
"""
import sys
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.platform_orchestrator import PlatformOrchestrator
from src.core.interfaces import Document

def test_gptoss_120b():
    """Test GPT-OSS-120B integration."""
    print("🧪 Testing GPT-OSS-120B Integration")
    print("=" * 60)

    # Initialize orchestrator with GPT-OSS config
    config_path = "config/gptoss_120b.yaml"
    orchestrator = PlatformOrchestrator(config_path)

    # Create test query and context
    query = "Explain the key differences between RISC-V and ARM architectures"
    context = [
        Document(
            content="RISC-V is an open-source instruction set architecture...",
            metadata={"source": "test"}
        )
    ]

    # Generate answer
    print(f"\n📝 Query: {query}")
    print("\n⏳ Generating answer with GPT-OSS-120B...")

    answer = orchestrator.query(query)

    print(f"\n✅ Answer Generated:")
    print(f"   Text: {answer.text[:200]}...")
    print(f"   Confidence: {answer.confidence:.3f}")
    print(f"   Model Used: {answer.metadata.get('model_used', 'unknown')}")
    print(f"   Generation Time: {answer.metadata.get('generation_time_ms', 0)}ms")

    # Verify it's using GPT-OSS
    assert "gpt-oss" in answer.metadata.get('model_used', '').lower()

    print("\n✅ GPT-OSS-120B integration test PASSED")
    return True

def test_gptoss_20b():
    """Test GPT-OSS-20B integration (edge model)."""
    print("\n🧪 Testing GPT-OSS-20B Integration (Edge Model)")
    print("=" * 60)

    # Similar test with 20B model
    config_path = "config/gptoss_20b.yaml"
    orchestrator = PlatformOrchestrator(config_path)

    query = "What is RISC-V?"
    answer = orchestrator.query(query)

    print(f"\n✅ Answer Generated:")
    print(f"   Text: {answer.text[:200]}...")
    print(f"   Model: {answer.metadata.get('model_used', 'unknown')}")

    print("\n✅ GPT-OSS-20B integration test PASSED")
    return True

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--model", choices=["120b", "20b", "both"], default="both")
    args = parser.parse_args()

    try:
        if args.model in ["120b", "both"]:
            test_gptoss_120b()

        if args.model in ["20b", "both"]:
            test_gptoss_20b()

        print("\n🎉 All GPT-OSS integration tests PASSED!")

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
```

**Run Tests**:
```bash
# Test both models
python tests/test_gptoss_integration.py

# Test specific model
python tests/test_gptoss_integration.py --model 120b
python tests/test_gptoss_integration.py --model 20b
```

#### Step 5: Verify First Inference

**Expected Behavior**:
1. First run will download models from HuggingFace (~40GB for 120B, ~8GB for 20B)
2. Models cached in `~/.cache/huggingface/hub/`
3. Subsequent runs use cached models

**Troubleshooting**:

**Issue**: Out of memory
```bash
# Solution: Use 20B model or enable CPU offloading
export CUDA_VISIBLE_DEVICES=0
python tests/test_gptoss_integration.py --model 20b
```

**Issue**: Download timeout
```bash
# Solution: Increase timeout
export HF_HUB_DOWNLOAD_TIMEOUT=600
```

**Issue**: CUDA not available
```bash
# Solution: Install CUDA toolkit
# For Ubuntu/Debian:
sudo apt-get install nvidia-cuda-toolkit
```

---

### Phase 2: Epic 1 Adaptive Routing Integration

**Duration**: 2-4 hours
**Goal**: Integrate GPT-OSS into multi-model routing

#### Step 1: Update Epic 1 Configuration

**File**: `config/epic1_gptoss_multimodel.yaml`

```yaml
# Epic 1 Multi-Model Routing with GPT-OSS
generator:
  type: "epic1"

  routing:
    enabled: true
    default_strategy: "balanced"

    # Query complexity → Model mapping
    strategies:
      cost_optimized:
        simple_query_model: "ollama/llama3.2:3b"     # Free, local
        medium_query_model: "huggingface/openai/gpt-oss-20b"  # Free, local
        complex_query_model: "huggingface/openai/gpt-oss-20b"  # Still free

      balanced:
        simple_query_model: "ollama/llama3.2:3b"
        medium_query_model: "huggingface/openai/gpt-oss-20b"
        complex_query_model: "huggingface/openai/gpt-oss-120b"

      quality_first:
        simple_query_model: "huggingface/openai/gpt-oss-20b"
        medium_query_model: "huggingface/openai/gpt-oss-120b"
        complex_query_model: "huggingface/openai/gpt-oss-120b"

    # Complexity thresholds (trained values)
    complexity_thresholds:
      simple_max: 0.3    # 0-0.3 = simple
      medium_max: 0.7    # 0.3-0.7 = medium
                         # 0.7-1.0 = complex

  # Model-specific configurations
  model_configs:
    "huggingface/openai/gpt-oss-120b":
      load_in_4bit: true
      device_map: "auto"
      max_new_tokens: 2048
      temperature: 0.7

    "huggingface/openai/gpt-oss-20b":
      load_in_4bit: true
      max_memory: {0: "14GB"}
      max_new_tokens: 1024
      temperature: 0.7

  cost_tracking:
    enabled: true
    models:
      "huggingface/openai/gpt-oss-120b":
        cost_per_token: 0.0000  # No API cost
        compute_cost: 0.0001    # GPU amortized
      "huggingface/openai/gpt-oss-20b":
        cost_per_token: 0.0000
        compute_cost: 0.00002   # Cheaper compute
```

#### Step 2: Demo Adaptive Routing

**Demo Script**: `demos/gptoss_adaptive_demo.py`

```python
#!/usr/bin/env python3
"""
Demonstrate Epic 1 adaptive routing with GPT-OSS models.
"""
from src.core.platform_orchestrator import PlatformOrchestrator

def demo_adaptive_routing():
    """Demo query routing across model tiers."""

    # Initialize with multi-model config
    orchestrator = PlatformOrchestrator("config/epic1_gptoss_multimodel.yaml")

    # Test queries of varying complexity
    queries = [
        ("What is RISC-V?", "simple"),
        ("Explain RISC-V instruction encoding with examples", "medium"),
        ("Compare RISC-V vector extensions with ARM SVE and x86 AVX-512, including performance implications", "complex")
    ]

    print("🎯 Epic 1 Adaptive Routing with GPT-OSS Models")
    print("=" * 70)

    for query, expected_complexity in queries:
        print(f"\n📝 Query ({expected_complexity}): {query}")

        # Generate answer
        answer = orchestrator.query(query)

        # Show routing decision
        model = answer.metadata.get('model_used', 'unknown')
        complexity = answer.metadata.get('query_complexity', 0.0)
        routing_time = answer.metadata.get('routing_time_ms', 0)

        print(f"   🔍 Detected Complexity: {complexity:.3f}")
        print(f"   🤖 Selected Model: {model}")
        print(f"   ⚡ Routing Time: {routing_time}ms")
        print(f"   ✅ Answer: {answer.text[:150]}...")

        # Verify correct model tier used
        if expected_complexity == "simple":
            assert "llama" in model.lower() or "20b" in model.lower()
        elif expected_complexity == "complex":
            assert "120b" in model.lower()

    print("\n✅ Adaptive routing demo completed successfully")

if __name__ == "__main__":
    demo_adaptive_routing()
```

---

### Phase 3: Kubernetes Deployment

**Duration**: 4-6 hours
**Goal**: Deploy GPT-OSS models in Epic 8 K8s cluster

#### GPU Node Pool Configuration

**File**: `k8s/deployments/generator-deployment-gptoss.yaml`

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: generator-gptoss-120b
  namespace: epic8-prod
  labels:
    app: generator
    model: gptoss-120b
    epic8.platform/component: generator
spec:
  replicas: 1  # Single replica due to GPU requirement
  selector:
    matchLabels:
      app: generator
      model: gptoss-120b
  template:
    metadata:
      labels:
        app: generator
        model: gptoss-120b
    spec:
      # GPU node selector
      nodeSelector:
        nvidia.com/gpu: "true"
        gpu-memory: "80gb"

      # Tolerate GPU taints
      tolerations:
      - key: nvidia.com/gpu
        operator: Equal
        value: "true"
        effect: NoSchedule

      containers:
      - name: generator
        image: epic8/generator:gptoss-latest
        resources:
          requests:
            cpu: "4"
            memory: "32Gi"
            nvidia.com/gpu: 1
          limits:
            cpu: "8"
            memory: "64Gi"
            nvidia.com/gpu: 1

        env:
        - name: HF_TOKEN
          valueFrom:
            secretKeyRef:
              name: huggingface-secrets
              key: hf-token
        - name: MODEL_NAME
          value: "openai/gpt-oss-120b"
        - name: CUDA_VISIBLE_DEVICES
          value: "0"

        volumeMounts:
        - name: model-cache
          mountPath: /root/.cache/huggingface

        livenessProbe:
          httpGet:
            path: /health/live
            port: 8081
          initialDelaySeconds: 300  # Model loading takes time
          periodSeconds: 30

        readinessProbe:
          httpGet:
            path: /health/ready
            port: 8081
          initialDelaySeconds: 300
          periodSeconds: 10

      volumes:
      - name: model-cache
        persistentVolumeClaim:
          claimName: gptoss-model-cache

---
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: gptoss-model-cache
  namespace: epic8-prod
spec:
  accessModes:
  - ReadWriteOnce
  storageClassName: gp3
  resources:
    requests:
      storage: 100Gi  # For model weights
```

#### GPU Node Pool (AWS EKS)

**File**: `terraform/modules/aws-eks/gpu-nodegroup.tf`

```hcl
# GPU node group for GPT-OSS models
resource "aws_eks_node_group" "gpu_nodes" {
  cluster_name    = aws_eks_cluster.main.name
  node_group_name = "gptoss-gpu-nodes"
  node_role_arn   = aws_iam_role.node.arn
  subnet_ids      = var.private_subnet_ids

  # GPU instance types
  instance_types = [
    "p3.2xlarge",   # V100 16GB (for gpt-oss-20b)
    "g5.2xlarge",   # A10G 24GB (for gpt-oss-20b)
    "p4d.24xlarge"  # A100 80GB (for gpt-oss-120b)
  ]

  scaling_config {
    desired_size = 1
    max_size     = 3
    min_size     = 0  # Scale to zero when not in use
  }

  labels = {
    "nvidia.com/gpu" = "true"
    "gpu-memory"     = "80gb"
    "workload"       = "gptoss"
  }

  # GPU taint to prevent non-GPU workloads
  taint {
    key    = "nvidia.com/gpu"
    value  = "true"
    effect = "NO_SCHEDULE"
  }

  tags = {
    Name = "Epic8-GPTOSS-GPU-Nodes"
  }
}
```

---

## 📊 Performance Expectations

### Inference Performance

**gpt-oss-120b**:
- Cold start: 2-5 minutes (model loading)
- Warm inference: 2-5 tokens/second
- Throughput: 5-10 queries/hour (depends on query length)
- Memory: 80GB VRAM

**gpt-oss-20b**:
- Cold start: 30-60 seconds
- Warm inference: 10-20 tokens/second
- Throughput: 20-40 queries/hour
- Memory: 16GB VRAM

### Cost Analysis

**API Comparison** (1M tokens/day):
```
OpenAI GPT-4:      $30-60/day
OpenAI GPT-4o-mini: $0.15/day
GPT-OSS-120b:      $10-20/day (GPU rental)
GPT-OSS-20b:       $2-5/day (GPU rental)
```

**Ownership TCO** (1 year):
- GPU server (A100 80GB): $10,000-15,000
- Electricity: $1,000-2,000/year
- Maintenance: $500-1,000/year
- **Break-even**: ~6-12 months vs GPT-4 API

---

## ✅ Validation Checklist

### Pre-Integration
- [ ] GPU available with sufficient VRAM
- [ ] HuggingFace account created
- [ ] HF_TOKEN obtained
- [ ] `transformers` library installed (>=4.30.0)
- [ ] CUDA toolkit installed

### Integration Testing
- [ ] GPT-OSS-20B loads successfully
- [ ] GPT-OSS-120B loads successfully
- [ ] Inference generates coherent answers
- [ ] Latency acceptable (<5s per query)
- [ ] Memory usage within limits

### Epic 1 Integration
- [ ] Adaptive routing selects GPT-OSS models
- [ ] Cost tracking shows $0 API cost
- [ ] Fallback works when GPU unavailable
- [ ] Routing overhead <50ms

### Production Deployment
- [ ] K8s deployment successful
- [ ] GPU node pool operational
- [ ] Model cache persistent volume mounted
- [ ] Health checks passing
- [ ] Monitoring dashboards showing metrics

---

## 🔧 Troubleshooting

### Common Issues

**Issue**: Model download fails
```bash
# Solution: Check HF token and network
huggingface-cli whoami
curl -I https://huggingface.co
```

**Issue**: CUDA out of memory
```bash
# Solution: Use smaller model or enable offloading
# In config:
load_in_4bit: true
device_map: "auto"
max_memory: {0: "14GB", "cpu": "30GB"}
```

**Issue**: Slow inference
```bash
# Solution: Enable Flash Attention 2
pip install flash-attn --no-build-isolation

# In config:
use_flash_attention_2: true
```

**Issue**: Model not found on HuggingFace
```bash
# Verify model name
huggingface-cli list-models | grep gpt-oss

# Check permissions
# Some models require accepting terms on HF website
```

---

## 📚 Resources

### Documentation
- **GPT-OSS Release**: https://openai.com/index/introducing-gpt-oss/
- **Model Card**: https://openai.com/index/gpt-oss-model-card/
- **HuggingFace Hub**: https://huggingface.co/openai/gpt-oss-120b
- **Transformers Docs**: https://huggingface.co/docs/transformers/

### Community
- **OpenAI Blog**: https://openai.com/blog
- **HuggingFace Forums**: https://discuss.huggingface.co/
- **GitHub Issues**: https://github.com/openai/openai-oss

---

## 🎯 Next Steps

1. **Immediate** (Today):
   - [ ] Install dependencies
   - [ ] Create GPT-OSS config files
   - [ ] Run integration tests

2. **Short-term** (This Week):
   - [ ] Integrate with Epic 1 adaptive routing
   - [ ] Benchmark performance vs existing models
   - [ ] Document configuration options

3. **Medium-term** (This Month):
   - [ ] Deploy to Kubernetes with GPU nodes
   - [ ] Implement monitoring and alerting
   - [ ] Optimize inference performance

4. **Long-term** (Next Quarter):
   - [ ] Fine-tune for domain-specific tasks
   - [ ] Implement model quantization optimizations
   - [ ] Scale to production workloads

---

**Status**: ✅ READY FOR IMPLEMENTATION
**Estimated Time**: 1-2 hours for basic integration, 1-2 days for full production deployment
**Risk Level**: LOW (well-documented models, existing adapter infrastructure)

*This integration brings cutting-edge open-source reasoning capabilities to the Epic 8 platform while maintaining cost efficiency through local deployment.*
