# RAG Portfolio Projects - Software Architecture Document

**Author**: Arthur Passuello  
**Version**: 1.0  
**Date**: February 2025  
**Purpose**: Master reference document for AI/ML portfolio development targeting Swiss tech market

---

## Executive Summary

This document outlines the architecture and implementation strategy for three sophisticated RAG (Retrieval-Augmented Generation) projects designed to demonstrate production-ready ML engineering capabilities while leveraging existing embedded systems expertise. Each project progressively builds technical complexity and showcases different aspects of modern AI/ML engineering.

### Portfolio Objectives
- Demonstrate transition from embedded systems to AI/ML engineering
- Showcase production-ready implementations beyond basic tutorials
- Leverage unique background in medical devices and technical documentation
- Target Swiss market preferences for quality and technical depth

---

## Project 1: Advanced Technical Documentation RAG System

### 1.1 Project Context & Scope

**Purpose**: Build a production-grade RAG system for querying technical documentation, demonstrating core RAG competencies with advanced retrieval techniques.

**Target Duration**: 3-4 weeks (80-100 hours)

**Business Value**: Addresses the critical need for intelligent technical documentation access in embedded systems development, reducing time spent searching through manuals and specifications.

### 1.2 System Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Frontend UI   │────▶│   API Gateway   │────▶│  Load Balancer  │
│   (Streamlit)   │     │   (FastAPI)     │     │                 │
└─────────────────┘     └─────────────────┘     └────────┬────────┘
                                                           │
                              ┌────────────────────────────┼────────────────────────────┐
                              │                            ▼                            │
                              │         ┌─────────────────────────────┐                │
                              │         │     Query Processing        │                │
                              │         │  - Query Understanding      │                │
                              │         │  - Query Expansion          │                │
                              │         │  - Intent Classification    │                │
                              │         └──────────────┬──────────────┘                │
                              │                        │                               │
                              │         ┌──────────────┴──────────────┐                │
                              │         ▼                             ▼                │
                              │ ┌───────────────┐            ┌───────────────┐        │
                              │ │ Dense Retrieval│            │Sparse Retrieval│        │
                              │ │   (FAISS)      │            │   (BM25)      │        │
                              │ └───────┬────────┘            └────────┬──────┘        │
                              │         │                              │               │
                              │         └──────────┬───────────────────┘               │
                              │                    ▼                                   │
                              │         ┌─────────────────────────────┐                │
                              │         │     Hybrid Reranking        │                │
                              │         │  - Cross-encoder scoring    │                │
                              │         │  - Diversity optimization   │                │
                              │         └──────────────┬──────────────┘                │
                              │                        │                               │
                              │                        ▼                               │
                              │         ┌─────────────────────────────┐                │
                              │         │    Response Generation      │                │
                              │         │  - Context compression     │                │
                              │         │  - LLM inference           │                │
                              │         │  - Citation generation      │                │
                              │         └─────────────────────────────┘                │
                              │                                                        │
                              │                     RAG Pipeline                       │
                              └────────────────────────────────────────────────────────┘

Document Ingestion Pipeline:
┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  PDF Parser  │────▶│   Chunking   │────▶│  Embedding   │────▶│Vector Store  │
│              │     │   Strategy   │     │  Generation  │     │   Update     │
└──────────────┘     └──────────────┘     └──────────────┘     └──────────────┘
```

### 1.3 Technical Stack & Implementation

#### Core Technologies
- **LLM**: Mistral-7B-Instruct-v0.2 (self-hosted) / GPT-3.5-turbo (fallback)
- **Embeddings**: BAAI/bge-base-en-v1.5 (fine-tuned on technical docs)
- **Vector Database**: FAISS (local) with option to migrate to Pinecone
- **Framework**: LangChain + LangGraph for orchestration
- **Deployment**: Streamlit (UI) + FastAPI (backend)
- **Hosting**: HuggingFace Spaces (free GPU) / Modal.com (production)

#### Advanced RAG Techniques
1. **Hybrid Search**: Combining dense (semantic) and sparse (keyword) retrieval
2. **Query Expansion**: Using LLM to generate query variations
3. **Corrective RAG (CRAG)**: Self-reflection and retrieval correction
4. **Contextual Compression**: Reducing retrieved context to relevant portions
5. **Citation Generation**: Automatic source attribution

#### Evaluation Metrics (RAGAS Framework)
- Context Precision: >0.85 target
- Answer Relevancy: >0.90 target
- Faithfulness: >0.95 target
- Response Latency: <2 seconds

### 1.4 Datasets & Resources

#### Primary Documentation Sources
- **RISC-V Specifications**: https://riscv.org/technical/specifications/
  - Complete ISA documentation (PDF format)
  - ~500 pages of technical content
- **FreeRTOS Documentation**: https://www.freertos.org/Documentation/
  - Kernel reference manual
  - API documentation
- **ARM Cortex-M Series**: https://developer.arm.com/documentation/
  - Technical reference manuals
  - Programming guides

#### Test & Evaluation Data
- Hand-crafted Q&A pairs (100+) from documentation
- Stack Overflow embedded systems questions for validation
- Technical forum discussions for query diversity

### 1.5 Development Plan

**Week 1: Foundation**
- Day 1-2: Environment setup, data acquisition
- Day 3-4: Document processing pipeline
- Day 5-7: Embedding strategy implementation

**Week 2: Core RAG Implementation**
- Day 1-3: Hybrid retrieval system
- Day 4-5: LLM integration and prompt engineering
- Day 6-7: Basic UI and API

**Week 3: Advanced Features**
- Day 1-2: Query expansion and CRAG
- Day 3-4: Reranking and optimization
- Day 5-7: Evaluation framework

**Week 4: Production Readiness**
- Day 1-2: Performance optimization
- Day 3-4: Deployment and monitoring
- Day 5-7: Documentation and demo prep

### 1.6 Skills Demonstrated & Recruiter Positioning

#### Technical Skills Showcased
- **RAG Architecture**: End-to-end implementation with advanced techniques
- **Vector Search**: Hybrid retrieval strategies and optimization
- **Model Deployment**: Self-hosted LLM with cost optimization
- **Production ML**: Caching, monitoring, error handling
- **Evaluation**: Systematic quality measurement with RAGAS

#### Positioning for Recruiters
- **Headline Achievement**: "Reduced technical documentation search time by 75% through intelligent retrieval"
- **Technical Depth**: "Implemented hybrid search combining dense and sparse retrieval for 92% accuracy"
- **Cost Optimization**: "Achieved 95% cost reduction vs. GPT-4 while maintaining quality"
- **Production Focus**: "Built with <2s latency and 99.9% uptime requirements"

#### Interview Talking Points
1. Explain the trade-offs between dense and sparse retrieval
2. Discuss chunking strategies for technical documentation
3. Demonstrate understanding of embedding fine-tuning
4. Show cost/performance optimization decisions

### 1.7 Identified Risks & Mitigations
- **Risk**: Large PDF parsing complexity
  - **Mitigation**: Use robust libraries (PyMuPDF), implement fallbacks
- **Risk**: Model hosting costs
  - **Mitigation**: Start with HuggingFace free tier, implement aggressive caching

---

## Project 2: Multimodal Embedded Systems Assistant

### 2.1 Project Context & Scope

**Purpose**: Create an advanced RAG system that understands both text and visual content (circuit diagrams, schematics, datasheets), leveraging multimodal transformer experience.

**Target Duration**: 4-5 weeks (100-120 hours)

**Business Value**: Enables engineers to query using images of circuits or components, bridging the gap between visual hardware debugging and textual documentation.

### 2.2 System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          Multimodal RAG Pipeline                            │
│                                                                             │
│  ┌─────────────┐    ┌─────────────────┐    ┌─────────────────┐           │
│  │   Image     │───▶│  Vision Model   │───▶│ Image Embeddings│           │
│  │   Input     │    │   (Custom ViT)  │    │                 │           │
│  └─────────────┘    └─────────────────┘    └────────┬────────┘           │
│                                                       │                     │
│  ┌─────────────┐    ┌─────────────────┐    ┌────────▼────────┐           │
│  │   Text      │───▶│  Text Encoder   │───▶│ Multimodal     │           │
│  │   Query     │    │  (Fine-tuned)   │    │   Fusion       │           │
│  └─────────────┘    └─────────────────┘    └────────┬────────┘           │
│                                                       │                     │
│                            ┌──────────────────────────┴────────┐           │
│                            ▼                                   ▼           │
│                 ┌───────────────────┐              ┌───────────────────┐  │
│                 │  Visual Knowledge │              │ Textual Knowledge │  │
│                 │      Base         │              │      Base         │  │
│                 │  - Schematics     │              │  - Datasheets     │  │
│                 │  - PCB layouts    │              │  - Manuals        │  │
│                 │  - Pinouts        │              │  - Code samples   │  │
│                 └─────────┬─────────┘              └─────────┬─────────┘  │
│                           │                                   │            │
│                           └───────────┬───────────────────────┘            │
│                                       ▼                                    │
│                          ┌─────────────────────────┐                      │
│                          │  Cross-Modal Retrieval  │                      │
│                          │  - Joint embedding space│                      │
│                          │  - Relevance scoring    │                      │
│                          └──────────────┬──────────┘                      │
│                                         │                                  │
│                                         ▼                                  │
│                          ┌─────────────────────────┐                      │
│                          │ Multimodal Generation   │                      │
│                          │ - Context aware answers │                      │
│                          │ - Visual references     │                      │
│                          └─────────────────────────┘                      │
└─────────────────────────────────────────────────────────────────────────────┘

Knowledge Base Structure:
┌────────────────┐     ┌────────────────┐     ┌────────────────┐
│   Component    │◀───▶│   Schematic    │◀───▶│  Application   │
│   Database     │     │   Database     │     │    Notes       │
│                │     │                │     │                │
│ - Datasheets   │     │ - Circuit imgs │     │ - Code samples │
│ - Pinouts      │     │ - PCB layouts  │     │ - Debug guides │
│ - Specs        │     │ - Block diag.  │     │ - Best practice│
└────────────────┘     └────────────────┘     └────────────────┘
```

### 2.3 Technical Stack & Implementation

#### Core Technologies
- **Vision Model**: Custom ViT (from your implementation) + CLIP adaptation
- **Language Model**: Mistral-7B or Phi-2 for efficiency
- **Multimodal Fusion**: Cross-attention mechanisms (leveraging your experience)
- **Vector Database**: Weaviate (native multimodal support) or custom FAISS
- **OCR**: EasyOCR for text extraction from images
- **Deployment**: Gradio (better for multimodal) + FastAPI

#### Multimodal Techniques
1. **Joint Embedding Space**: Unified representation for text and images
2. **Cross-Modal Attention**: Your custom implementation from previous work
3. **Visual Grounding**: Linking text descriptions to image regions
4. **Multi-Stage Retrieval**: Image→Text→Image verification loop
5. **Contrastive Learning**: For embedding alignment

### 2.4 Datasets & Resources

#### Visual Data Sources
- **CircuitJS Circuits**: https://www.falstad.com/circuit/
  - Export circuits as images with metadata
- **KiCad Libraries**: https://kicad.github.io/
  - Symbol libraries with descriptions
  - Footprint images
- **OpenCircuits**: https://opencircuits.com/
  - CC-licensed circuit designs
- **Fritzing Parts**: https://github.com/fritzing/fritzing-parts
  - Component visuals with metadata

#### Component Databases
- **Octopart API**: https://octopart.com/api/
  - Component specs and datasheet links
  - Free tier: 1000 requests/month
- **DigiKey API**: https://developer.digikey.com/
  - Rich component metadata
  - Product images

#### Training Data Creation
```python
# Synthetic data generation approach
- Extract circuit images from open-source projects
- Generate Q&A pairs using component descriptions
- Create image-text alignment tasks
- Augment with rotations, crops for robustness
```

### 2.5 Development Plan

**Week 1: Multimodal Foundation**
- Day 1-2: Data collection and preprocessing
- Day 3-4: Vision model adaptation (your ViT)
- Day 5-7: Initial multimodal embeddings

**Week 2: Knowledge Base Construction**
- Day 1-3: Circuit image processing pipeline
- Day 4-5: Component database integration
- Day 6-7: Cross-modal indexing

**Week 3: Retrieval System**
- Day 1-3: Joint embedding space training
- Day 4-5: Cross-modal retrieval implementation
- Day 6-7: Relevance scoring optimization

**Week 4: Integration & UI**
- Day 1-2: Multimodal query processing
- Day 3-4: Gradio interface development
- Day 5-7: System integration

**Week 5: Optimization & Deployment**
- Day 1-3: Performance optimization
- Day 4-5: Evaluation framework
- Day 6-7: Documentation and demos

### 2.6 Skills Demonstrated & Recruiter Positioning

#### Technical Skills Showcased
- **Multimodal AI**: Custom vision-language model integration
- **Computer Vision**: Technical diagram understanding
- **Transfer Learning**: Adapting pre-trained models for specialized domain
- **System Integration**: Complex pipeline orchestration
- **Domain Expertise**: Embedded systems knowledge application

#### Positioning for Recruiters
- **Unique Value**: "First multimodal RAG for embedded systems debugging"
- **Technical Innovation**: "Custom vision transformer for circuit understanding"
- **Practical Impact**: "Reduced component identification time by 80%"
- **Differentiation**: "Bridges hardware and software documentation"

#### Interview Talking Points
1. Explain multimodal fusion strategies
2. Discuss challenges in technical diagram understanding
3. Demonstrate custom ViT modifications
4. Show practical applications in hardware debugging

### 2.7 Identified Risks
- **Risk**: Limited labeled circuit-description pairs
  - **Mitigation**: Synthetic data generation, weak supervision
- **Risk**: OCR accuracy on technical diagrams
  - **Mitigation**: Multiple OCR engines, confidence thresholds

---

## Project 3: Production LLM-Powered Development Environment

### 3.1 Project Context & Scope

**Purpose**: Build an enterprise-grade agent-based RAG system demonstrating production ML engineering with sophisticated orchestration and monitoring.

**Target Duration**: 4-5 weeks (100-120 hours)

**Business Value**: Accelerates development workflows by providing intelligent code assistance with awareness of project context, dependencies, and best practices.

### 3.2 System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                      Agent-Orchestrated RAG Platform                            │
│                                                                                 │
│  ┌─────────────────┐        ┌─────────────────────────────────────────┐       │
│  │   User Query    │───────▶│         Orchestrator Agent              │       │
│  │                 │        │   - Query understanding                 │       │
│  └─────────────────┘        │   - Task decomposition                  │       │
│                             │   - Agent selection                      │       │
│                             └────────────────┬─────────────────────────┘       │
│                                              │                                  │
│                    ┌─────────────────────────┴─────────────────────────┐       │
│                    ▼                         ▼                         ▼       │
│         ┌─────────────────┐      ┌─────────────────┐      ┌─────────────────┐ │
│         │  Code Analysis  │      │  Documentation  │      │   Dependency    │ │
│         │     Agent       │      │     Agent       │      │     Agent       │ │
│         │                 │      │                 │      │                 │ │
│         │ - AST parsing   │      │ - Doc retrieval │      │ - Graph analysis│ │
│         │ - Type inference│      │ - API search    │      │ - Version check │ │
│         │ - Bug detection │      │ - Example mining│      │ - Compatibility │ │
│         └────────┬────────┘      └────────┬────────┘      └────────┬────────┘ │
│                  │                         │                         │          │
│                  └─────────────────────────┴─────────────────────────┘          │
│                                            │                                    │
│                                            ▼                                    │
│                             ┌──────────────────────────┐                       │
│                             │   Synthesis Agent        │                       │
│                             │ - Response generation    │                       │
│                             │ - Code generation        │                       │
│                             │ - Explanation creation   │                       │
│                             └───────────┬──────────────┘                       │
│                                         │                                       │
│  ┌─────────────────────────────────────┴────────────────────────────────┐     │
│  │                         Quality Assurance Layer                       │     │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │     │
│  │  │ Safety Check │  │ Fact Verify  │  │ Code Validate│              │     │
│  │  └──────────────┘  └──────────────┘  └──────────────┘              │     │
│  └───────────────────────────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────────────────────────┘

Infrastructure Layer:
┌─────────────┐     ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Message   │     │   Vector    │     │   Cache     │     │  Monitoring │
│    Queue    │     │  Database   │     │   Layer     │     │   Stack     │
│ (RabbitMQ)  │     │ (Pinecone)  │     │  (Redis)    │     │(Prometheus) │
└─────────────┘     └─────────────┘     └─────────────┘     └─────────────┘
```

### 3.3 Technical Stack & Implementation

#### Core Technologies
- **Orchestration**: LangGraph for agent coordination
- **LLM**: Fine-tuned CodeLlama-7B + Mistral-7B ensemble
- **Agent Framework**: Custom implementation with LangChain
- **Vector DB**: Pinecone (production) with metadata filtering
- **Caching**: Redis with intelligent TTL
- **Message Queue**: RabbitMQ for async processing
- **Monitoring**: Prometheus + Grafana + custom dashboards
- **Deployment**: Kubernetes with auto-scaling

#### Advanced Techniques
1. **Hierarchical Agent Architecture**: Specialized agents for different tasks
2. **Dynamic Tool Selection**: Agents choose tools based on query
3. **Memory Management**: Long-term and short-term memory systems
4. **Online Learning**: Continuous improvement from user feedback
5. **A/B Testing**: Multiple strategy evaluation

#### Production Features
- Horizontal scaling with load balancing
- Circuit breaker patterns for resilience
- Comprehensive logging and tracing
- Security: Input sanitization, rate limiting
- CI/CD pipeline with automated testing

### 3.4 Datasets & Resources

#### Code Repositories
- **The Stack**: https://huggingface.co/datasets/bigcode/the-stack
  - 6TB of permissively licensed code
  - Pre-filtered and deduplicated
- **CodeSearchNet**: https://github.com/github/CodeSearchNet
  - 2M functions with documentation
  - Natural language to code mappings

#### Documentation Sources
- **DevDocs API**: https://devdocs.io/
  - Aggregated technical documentation
  - Offline downloadable
- **Libraries.io API**: https://libraries.io/api
  - Dependency information
  - Version compatibility data

#### Embedded-Specific
- **PlatformIO Registry**: https://registry.platformio.org/
  - Embedded libraries and examples
- **Arduino Reference**: https://www.arduino.cc/reference/
  - Complete API documentation

### 3.5 Development Plan

**Week 1: Agent Architecture**
- Day 1-2: LangGraph setup and base agents
- Day 3-4: Inter-agent communication
- Day 5-7: Tool integration

**Week 2: Knowledge Base**
- Day 1-3: Code indexing pipeline
- Day 4-5: Documentation processing
- Day 6-7: Dependency graph construction

**Week 3: Production Infrastructure**
- Day 1-2: Message queue integration
- Day 3-4: Caching layer
- Day 5-7: Monitoring setup

**Week 4: Advanced Features**
- Day 1-3: Online learning implementation
- Day 4-5: A/B testing framework
- Day 6-7: Security hardening

**Week 5: Deployment & Polish**
- Day 1-2: Kubernetes configuration
- Day 3-4: Performance optimization
- Day 5-7: Documentation and demos

### 3.6 Skills Demonstrated & Recruiter Positioning

#### Technical Skills Showcased
- **Production ML**: Scalable architecture with monitoring
- **Agent Systems**: Complex multi-agent orchestration
- **MLOps**: CI/CD, A/B testing, online learning
- **System Design**: Distributed systems patterns
- **Code Understanding**: AST parsing, type inference

#### Positioning for Recruiters
- **Scale Achievement**: "Handles 1000+ concurrent users with <100ms latency"
- **Architectural Depth**: "Microservices-based ML system with 99.9% uptime"
- **Innovation**: "Self-improving system through online learning"
- **Business Impact**: "Reduced development time by 40% in pilot testing"

#### Interview Talking Points
1. Explain agent orchestration strategies
2. Discuss distributed system challenges in ML
3. Demonstrate monitoring and observability approach
4. Show cost optimization techniques at scale

### 3.7 Identified Risks
- **Risk**: Complex infrastructure management
  - **Mitigation**: Start with docker-compose, migrate to K8s
- **Risk**: Agent coordination complexity
  - **Mitigation**: Comprehensive logging, visualization tools

---

## Cross-Project Considerations

### Shared Infrastructure

#### Development Environment
```bash
# Base setup for all projects
conda create -n rag-portfolio python=3.10
pip install torch transformers langchain sentence-transformers
pip install faiss-cpu streamlit gradio fastapi
pip install ragas wandb pytest pre-commit
```

#### Shared Utilities
- Embedding cache manager
- Document processing pipeline
- Evaluation framework
- Deployment scripts

### Progressive Skill Building

**Project Flow**:
1. **Project 1**: Establishes RAG fundamentals
2. **Project 2**: Adds multimodal complexity
3. **Project 3**: Demonstrates production engineering

Each project builds on previous learnings while introducing new challenges.

### Portfolio Presentation Strategy

#### GitHub Organization
```
rag-portfolio/
├── 01-technical-docs-rag/
│   ├── README.md (with demo GIF)
│   ├── docs/ (architecture, usage)
│   ├── src/ (clean, modular code)
│   └── evaluation/ (metrics, benchmarks)
├── 02-multimodal-assistant/
├── 03-enterprise-platform/
└── portfolio-website/
    └── index.html (unified showcase)
```

#### Demo Strategy
- Live demos on HuggingFace Spaces
- Video walkthroughs for complex features
- Performance comparison dashboards
- Cost analysis visualizations

### Swiss Market Alignment

#### Cultural Fit Demonstrations
- **Quality over Quantity**: Three polished projects vs many basic ones
- **Technical Depth**: Detailed documentation and architecture
- **Practical Focus**: Real-world applications and metrics
- **Transparency**: Open about trade-offs and decisions

#### Application Materials Integration
- Resume: Quantified achievements from each project
- Cover Letter: Story arc from embedded to AI/ML
- LinkedIn: Project highlights with metrics
- Interviews: Deep technical discussions ready

---

## Appendix: Quick Reference Links

### Essential Documentation
- [LangChain Docs](https://python.langchain.com/docs/get_started/introduction)
- [LangGraph Guide](https://github.com/langchain-ai/langgraph)
- [RAGAS Framework](https://docs.ragas.io/en/latest/)
- [HuggingFace Spaces](https://huggingface.co/docs/hub/spaces)

### Model Resources
- [Mistral Models](https://huggingface.co/mistralai)
- [Sentence Transformers](https://www.sbert.net/)
- [CodeLlama](https://huggingface.co/codellama)

### Deployment Platforms
- [Modal.com Docs](https://modal.com/docs)
- [Streamlit Cloud](https://docs.streamlit.io/streamlit-cloud)
- [FastAPI](https://fastapi.tiangolo.com/)

### Evaluation Tools
- [Weights & Biases](https://wandb.ai/site)
- [Prometheus](https://prometheus.io/docs/)
- [Grafana](https://grafana.com/docs/)

---

This document serves as your comprehensive reference throughout the portfolio development journey. Each project can be started independently, but the recommended sequence maximizes skill building and portfolio impact.