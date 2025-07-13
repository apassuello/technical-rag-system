# ML/RAG Portfolio Development Setup Guide 2025

This comprehensive guide covers the essential tools and configurations for building a modern ML/RAG portfolio in 2025, focusing on free tiers, latest updates, and practical implementation steps.

## Local development environment optimized for 2025

**Apple Silicon users gain significant advantages** with native Metal support across the ML stack. The key setup involves using **Miniforge for conda management** (37% better performance than standard conda), enabling **MPS acceleration in PyTorch 2.1+**, and building **llama.cpp with Metal support** for local model inference.

The recommended Python stack uses **Python 3.11** for optimal 2025 compatibility, with conda for ML packages and pip for specialized tools. Environment isolation becomes critical with separate environments for each project, and requirements files should pin major versions while allowing minor updates.

**LLaMa.cpp installation** now offers multiple approaches: Homebrew provides the simplest installation (`brew install llama.cpp`), while building from source enables full Metal optimization. The Python bindings require specific CMAKE flags for Apple Silicon: `CMAKE_ARGS="-DGGML_METAL=ON" pip install llama-cpp-python`.

**PyTorch MPS optimization** requires careful memory management with the `PYTORCH_MPS_HIGH_WATERMARK_RATIO` environment variable set to 0.7, smaller batch sizes initially, and strategic use of gradient checkpointing for large models. Common MPS limitations include unsupported operations that require CPU fallbacks.

**FAISS configuration** differs significantly between platforms - GPU acceleration remains Linux-only, while macOS users should focus on CPU optimization with OpenBLAS. The conda installation (`conda install -c pytorch faiss-cpu=1.11.0`) provides better stability than pip for most users.

## Model deployment platforms evolved significantly in 2025

**HuggingFace Spaces** introduced **ZeroGPU with dynamic A100 allocation** - free users get 300 seconds daily (5 minutes), while PRO users ($9/month) receive 1,500 seconds daily with highest queue priority. The `@spaces.GPU` decorator enables seamless GPU access in Gradio applications.

**RunPod** restructured pricing with **per-second billing** and spot instances offering 60-91% savings. RTX 4090 instances cost $0.34/hour with community cloud, while A100 (80GB) runs $1.99/hour. The serverless deployment model provides automatic scaling with `runpod.serverless.start()`.

**Modal.com** offers **$30/month free compute credits** with serverless ML deployment. Their pricing model charges $0.000583/second for A100 (40GB), making it competitive for burst workloads. The `@app.function(gpu="A100")` decorator simplifies GPU deployment.

**Google Colab Pro+** ($49.99/month) now provides **500 compute units monthly** with A100 access and terminal functionality. The compute unit system replaces time-based limits - V100 High-RAM consumes 5 units/hour versus T4's 1.96 units/hour.

Cost comparison reveals **RunPod offers the lowest GPU costs** for sustained workloads, **Modal excels for serverless/burst usage**, **HuggingFace Spaces provides the best free tier for demos**, and **Colab Pro+ works best for research and experimentation**.

## RAG-specific tools showcase major 2025 advancements

**LangGraph 0.4.10** introduces **LangGraph Platform for production deployment** and **LangGraph Studio** accessed via CLI (`langgraph dev`). The new **LoggedModel Entity** moves beyond run-centric architecture to support complex agentic workflows. Enhanced GenAI tracing provides production-ready monitoring for RAG systems.

**Vector database landscape** shows clear differentiation - **Pinecone** leads in performance (50,000 QPS) with managed service reliability, **ChromaDB** offers unlimited free usage for local development with 5,000-8,000 QPS, and **Weaviate** provides 10,000-15,000 QPS with superior multi-modal capabilities.

**RAGAS evaluation framework** enables comprehensive RAG assessment with metrics like Faithfulness, AnswerRelevancy, ContextPrecision, and ContextRecall. The framework now supports **reference-free evaluation** and **automated synthetic dataset creation**, reducing manual evaluation overhead.

**Embedding model strategy** depends on use case - **OpenAI's text-embedding-3-large** provides highest accuracy at $0.00013 per 1K tokens, while **local Sentence Transformers** eliminate ongoing costs. The **all-mpnet-base-v2** model offers excellent quality for local deployment, and **gte-multilingual-base** supports 70+ languages.

## MLOps infrastructure reaches production maturity

**MLflow 3.0** delivers **native GenAI capabilities** with enhanced tracing for RAG systems, the new **ResponsesAgent class** for streaming, and **unified evaluation framework** across traditional ML and GenAI. Auto-tracing support includes **PydanticAI and smolagents integration**.

**Weights & Biases** provides **100GB free storage** with unlimited personal projects. The **OpenAI integration** enables automatic logging with `wandb.integration.openai.autolog()`, while **LangChain callbacks** support comprehensive workflow tracking.

**Prometheus + Grafana** setup becomes straightforward with **Docker Compose** deployment. ML-specific metrics include request latency histograms, model quality gauges, and data drift detection. The monitoring stack supports **custom alerting** for model performance degradation.

**DVC for data versioning** integrates seamlessly with Git workflows, supporting **S3, GCS, and Azure** backends. The **pipeline definition** in `dvc.yaml` enables reproducible ML workflows with parameter tracking and metric comparison across experiments.

## API services pricing became more competitive

**OpenAI's 2025 pricing** features **GPT-4o at $5/$15 per 1M tokens** (input/output), making it the most cost-effective flagship model. The **Batch API offers 50% discounts** for non-real-time processing, while **o1 reasoning models** start at $15 per 1M input tokens for complex analysis.

**Anthropic Claude** pricing shows **Claude 3.5 Sonnet at $3/$15 per 1M tokens** with **200K context window** and **prompt caching up to 90% savings**. The **Claude 3.5 Haiku** provides fastest response at $1/$5 per 1M tokens.

**Security best practices** mandate **never hardcoding API keys**, using **environment variables and secrets management**, implementing **30-day key rotation**, and setting up **automated budget alerts**. Production deployments require **different keys per environment** with comprehensive **usage monitoring**.

**Cost optimization strategies** include starting with cheaper models for development, using **batch processing for 50% savings**, implementing **aggressive caching**, and **model switching based on task complexity**. Custom tracking middleware enables **real-time cost monitoring** with automatic budget enforcement.

## Development tools integrate modern workflows

**GitHub Projects 2025** introduces **sub-issues for hierarchical planning**, **advanced search with Boolean operators**, and **50+ built-in templates** including ML-specific workflows. The **issue forms integration** enables structured ML bug reporting with model-specific fields.

**CI/CD pipelines** leverage **Arm64 runners for 37% cost savings** with optimized ML workflows. The pipeline structure includes parallel testing across Python versions, automated model training on main branch commits, and **artifact management** for model deployment. **DVC integration** enables reproducible model versioning within CI/CD.

**Documentation strategy** favors **MkDocs Material** over Sphinx for portfolio projects due to **easier Markdown setup**, **live preview capabilities**, and **excellent mobile responsiveness**. The 2025 Material theme includes **social card generation**, **improved search**, and **automated API documentation** from docstrings.

**Testing frameworks** emphasize **behavioral testing for ML models** with invariance tests, directional expectation validation, and **Great Expectations for data quality**. The **pytest configuration** includes ML-specific markers (training, gpu, slow) and **parametrized tests** for systematic model validation.

## Integration recommendations optimize the complete stack

**For rapid prototyping**: ChromaDB + Sentence Transformers + LangChain provides **zero-cost local development** with unlimited experimentation capacity.

**For production deployment**: Pinecone + OpenAI Embeddings + LangGraph offers **enterprise-grade reliability** with comprehensive monitoring and scaling capabilities.

**For cost-conscious portfolio projects**: ChromaDB + local embeddings + RAGAS evaluation delivers **professional results** while minimizing ongoing API costs.

**For complex multi-modal applications**: Weaviate + custom embedding pipeline + LangGraph supports **advanced search capabilities** with rich media processing.

The 2025 ML/RAG landscape emphasizes **serverless deployment**, **cost optimization**, and **production-grade monitoring**. The convergence of better free tiers, simplified deployment tools, and mature MLOps infrastructure makes professional RAG development accessible to individual developers while maintaining enterprise capabilities for production workloads.