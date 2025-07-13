# Project 1: Advanced Technical Documentation RAG System for Embedded AI

## Project Overview

**Duration**: 3-4 weeks\
**Complexity**: Medium\
**Primary Goal**: Build production-grade RAG system demonstrating ML engineering fundamentals while leveraging embedded systems expertise

### Business Context

Technical documentation is fragmented across PDFs, making it difficult for engineers to find specific implementation details quickly, especially when dealing with resource-constrained embedded systems and AI deployment. Current search tools don't understand technical context, hardware constraints, or code relationships. This project creates an intelligent documentation assistant that understands technical context, embedded system constraints, code snippets, and cross-references, providing accurate answers with source attribution.

### Author Background

* **Arthur Passuello**: Embedded Systems Engineer transitioning to AI/ML
* **Current Skills**: 7 weeks intensive ML (transformers from scratch, multimodal systems)
* **Domain Expertise**: 2.5 years embedded systems in medical devices, real-time systems, regulatory compliance
* **Target Market**: Swiss tech companies (Lausanne/Geneva focus), particularly those working on embedded AI, medical devices, and industrial IoT

## Technical Architecture

### System Design

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│                 │     │                  │     │                 │
│  Document       │────▶│  Processing      │────▶│  Vector Store   │
│  Repository     │     │  Pipeline        │     │  (FAISS/Chroma) │
│                 │     │                  │     │                 │
└─────────────────┘     └──────────────────┘     └─────────────────┘
         │                       │                         │
         │                       ▼                         │
         │              ┌──────────────────┐              │
         │              │  Domain-Aware    │              │
         └─────────────▶│  RAG Orchestrator│◀─────────────┘
                        │  (LangGraph)     │
                        │                  │
                        └────────┬─────────┘
                                 │
                        ┌────────▼─────────┐
                        │                  │
                        │  LLM Service     │
                        │  (Local/Hybrid)  │
                        │                  │
                        └────────┬─────────┘
                                 │
                        ┌────────▼─────────┐
                        │                  │
                        │  User Interface  │
                        │  (Streamlit)     │
                        │                  │
                        └──────────────────┘
```

### Core Components

#### Language Models

* **Primary LLM**: Mistral-7B-Instruct v0.2 (self-hosted)

  * Quantized with llama.cpp for efficiency
  * Running on HuggingFace Spaces (free T4 GPU)

* **Fallback**: GPT-3.5-turbo for complex queries

* **Cost Strategy**: 70% local models, 30% API usage

#### Embedding Models

* **Base Model**: BAAI/bge-base-en-v1.5
* **Fine-tuning**: On technical documentation vocabulary with emphasis on embedded systems terminology
* **Dimension**: 768
* **Special Features**: Optimized for code, technical terms, and hardware specifications

#### Vector Databases

* **Development**: FAISS (local, free)
* **Production**: ChromaDB (simple deployment)
* **Alternative**: Pinecone (if scaling needed)

#### Frameworks & Tools

* **RAG Framework**: LangChain + LangGraph

* **Document Processing**:

  * PyMuPDF for PDF parsing
  * Unstructured.io for complex documents
  * Custom parsers for tables and specifications

* **Evaluation**: RAGAS framework

* **Monitoring**: Weights & Biases (free tier)

* **Deployment**: Streamlit + HuggingFace Spaces

## Advanced Techniques

### 1. Hybrid Search Implementation

```python
# Combines semantic and keyword search
- Dense retrieval: Sentence transformer embeddings
- Sparse retrieval: BM25 algorithm
- Fusion: Reciprocal Rank Fusion (RRF)
- Weights: 0.7 dense, 0.3 sparse
```

### 2. Smart Document Chunking

* Preserve code blocks intact
* Maintain section hierarchies
* Keep tables and diagrams together
* Special handling for hardware specifications and pinout tables
* Overlap: 10% for context preservation
* Chunk size: 512 tokens optimal

### 3. Query Enhancement with Domain Awareness

* Use transformer knowledge for query expansion
* Generate synonyms for technical terms
* Identify acronyms and expand them (e.g., RTOS, MCU, ISR)
* Detect hardware constraints in queries (memory limits, power budgets)
* Add context from conversation history

### 4. Reranking Pipeline

* Cross-encoder: ms-marco-MiniLM-L-6-v2
* Score threshold: 0.7 for inclusion
* Boost relevance for resource-constrained contexts
* Max results: Top 5 after reranking

### 5. Answer Generation

* Streaming responses for better UX
* Source attribution with highlighting
* Confidence scoring
* Hardware feasibility notes when relevant
* Fallback to simpler explanation if needed

## Datasets & Resources

### Primary Documentation Sources

#### RISC-V Specifications (Core Focus)

* **URL**: https://riscv.org/technical/specifications/

* **Content**:

  * ISA manual (PDF, ~500 pages)
  * Privileged architecture (PDF, ~200 pages)
  * Vector extension for ML acceleration (PDF, ~300 pages)

* **License**: Open source

* **Processing**: Extract chapters, preserve tables, highlight AI-relevant extensions

#### Embedded RTOS Documentation

* **FreeRTOS**: https://www.freertos.org/Documentation/RTOS\_book.html

  * Kernel reference manual
  * API documentation
  * Real-time guarantees

* **Zephyr RTOS**: https://docs.zephyrproject.org/

  * ML subsystem documentation
  * Power management guides

* **License**: MIT/Apache

* **Processing**: Parse API signatures, extract timing constraints

#### ARM Cortex-M Documentation

* **URL**: https://developer.arm.com/documentation/dui0553/latest/

* **Content**:

  * Technical reference manuals
  * Programming guides
  * CMSIS-NN neural network kernels

* **License**: Free with registration

* **Processing**: Handle nested sections, extract performance data

#### Embedded AI Resources

* **TensorFlow Lite Micro**: Official documentation

  * Memory requirements
  * Supported operations
  * Optimization techniques

* **Edge Impulse**: Public documentation

  * Model deployment guides
  * Resource profiling

### Additional Resources

* **Linux Kernel Docs**: https://www.kernel.org/doc/html/latest/
* **OpenHW Group**: https://www.openhwgroup.org/
* **FDA Software Guidance**: https://www.fda.gov/media/73141/download (for medical context)

### Evaluation Data Creation

```python
# Generate test questions from docs with embedded AI focus
1. Extract section headings → "What is [heading]?"
2. Find code examples → "How to implement [function]?"
3. Locate parameters → "What are the parameters for [API]?"
4. Cross-references → "How does [A] relate to [B]?"
5. Resource queries → "Can [model] run on [MCU] with [constraints]?"
6. Compliance queries → "What safety considerations for [use case]?"

# Target: 200+ Q&A pairs
# Include difficulty levels: Easy/Medium/Hard
# Include embedded-specific queries: 25% of dataset
```

## Implementation Plan

### Week 1: Foundation

**Day 1-2: Environment & Data**

* Set up development environment
* Download all documentation PDFs
* Create initial project structure
* Configure git repository

**Day 3-4: Document Processing**

* Implement PDF parser with PyMuPDF
* Build smart chunking algorithm
* Extract metadata (sections, pages, specifications)
* Create document index

**Day 5-7: Embeddings & Storage**

* Fine-tune sentence transformer on embedded terminology
* Set up FAISS vector store
* Implement document ingestion
* Test retrieval quality

### Week 2: Advanced Features

**Day 8-9: Hybrid Search**

* Implement BM25 sparse retrieval
* Create fusion algorithm
* Optimize search weights
* Benchmark performance

**Day 10-11: Query Processing**

* Build query expansion module
* Implement hardware constraint detection
* Add context injection
* Handle multi-turn queries

**Day 12-14: Answer Generation**

* Integrate Mistral-7B locally
* Implement streaming responses
* Add source attribution
* Create answer validation

### Week 3: Production & Evaluation

**Day 15-16: Evaluation Framework**

* Set up RAGAS metrics
* Create test dataset with embedded focus
* Implement automated testing
* Generate performance reports

**Day 17-18: Optimization**

* Quantize models for speed
* Implement caching layer
* Add request batching
* Profile bottlenecks

**Day 19-21: Deployment**

* Build Streamlit interface
* Deploy to HuggingFace Spaces
* Create documentation
* Record demo video with embedded AI examples

## Evaluation Metrics

### RAGAS Framework Metrics

1. **Context Precision**: How relevant are retrieved documents?
2. **Context Recall**: Are all relevant documents retrieved?
3. **Faithfulness**: Does answer match source documents?
4. **Answer Relevancy**: Does answer address the query?

### Custom Metrics

* **Code Accuracy**: Correct code snippets retrieved
* **Technical Precision**: Accurate technical terms and specifications
* **Constraint Awareness**: Correctly identifies hardware limitations
* **Response Time**: < 2 seconds target
* **Source Quality**: Proper attribution

### Success Criteria

* 90%+ accuracy on test set
* < 2 second response time
* 95%+ accuracy on hardware constraint queries
* 95%+ uptime
* Positive user feedback

## Skills Demonstrated

### For Recruiters

1. **ML Engineering Competence**

   * "Built custom embeddings improving retrieval by 40% on technical documentation"
   * "Implemented production RAG handling embedded systems documentation"
   * "Achieved 94% accuracy on technical documentation queries"

2. **Domain Expertise Integration**

   * "Leveraged embedded systems knowledge for specialized query processing"
   * "Built constraint-aware system understanding hardware limitations"
   * "Integrated real-time systems concepts into AI application"

3. **System Design Skills**

   * "Designed scalable architecture with proper abstractions"
   * "Implemented comprehensive monitoring and evaluation"
   * "Built fault-tolerant system with automatic fallbacks"

4. **Cost Optimization**

   * "Reduced inference costs by 95% using local models"
   * "Implemented intelligent caching reducing API calls by 80%"
   * "Balanced performance and cost for production deployment"

### Portfolio Positioning

* **Unique Angle**: RAG system built by embedded engineer for embedded engineers
* **Not Another ChatGPT Wrapper**: Custom embeddings, advanced retrieval, domain awareness
* **Production-Ready**: Proper evaluation, monitoring, deployment
* **Market-Relevant**: Addresses real needs in embedded AI development

## Development Resources

### Setup Commands

```bash
# Create environment
conda create -n rag-embedded-ai python=3.10
conda activate rag-embedded-ai

# Install dependencies
pip install torch transformers langchain langgraph
pip install sentence-transformers faiss-cpu chromadb
pip install streamlit pymupdf ragas
pip install python-dotenv pydantic fastapi

# Download models
python scripts/download_models.py
```

### Project Structure

```
embedded-ai-rag/
├── src/
│   ├── document_processor.py
│   ├── embeddings.py
│   ├── retrieval.py
│   ├── generation.py
│   ├── query_enhancer.py
│   └── evaluation.py
├── data/
│   ├── raw_pdfs/
│   ├── processed/
│   └── test_sets/
├── models/
│   ├── embeddings/
│   └── llm/
├── configs/
│   └── config.yaml
├── deployment/
│   ├── app.py
│   └── requirements.txt
└── README.md
```

### Key Configuration

```yaml
# config.yaml
model:
  llm: "mistralai/Mistral-7B-Instruct-v0.2"
  embeddings: "BAAI/bge-base-en-v1.5"
  reranker: "cross-encoder/ms-marco-MiniLM-L-6-v2"

retrieval:
  chunk_size: 512
  chunk_overlap: 50
  k_documents: 10
  hybrid_alpha: 0.7

generation:
  temperature: 0.3
  max_tokens: 1024
  streaming: true
  
domain_config:
  detect_constraints: true
  embedded_terminology: true
  include_feasibility: true
```

## Risk Mitigation

### Identified Risks

1. **Data Quality**: PDFs may have poor formatting
   * Mitigation: Multiple parser fallbacks, manual verification
2. **Model Size**: Large models slow on free GPUs
   * Mitigation: Quantization, caching, strategic API usage
3. **Evaluation Complexity**: Creating good test sets
   * Mitigation: Start with 50 Q\&A, expand gradually
4. **Domain Specificity**: Over-specialization
   * Mitigation: Keep general capabilities while adding domain features

## Next Steps

After completing this project:

1. Write technical blog post: "Building Domain-Aware RAG for Embedded AI"
2. Create LinkedIn post with demo video showing embedded AI queries
3. Prepare 5-minute technical presentation for interviews
4. Consider adding medical device compliance features based on feedback
5. Move to Project 2 (Multimodal Assistant) or embedded AI demo

## Repository

* **GitHub**: github.com/apassuello/embedded-ai-rag
* **Demo**: huggingface.co/spaces/apassuello/embedded-ai-assistant
* **Blog**: "From Embedded Systems to AI: Building Specialized RAG"

***

## Detailed Justification of Modifications

### 1. **Project Title and Positioning**

**Change**: Added "for Embedded AI" to title and throughout\
**Justification**: Immediately signals your unique domain expertise. Shows you're not building generic RAG but solving specific problems you understand deeply.

### 2. **Business Context Enhancement**

**Change**: Added mention of "resource-constrained embedded systems and AI deployment"\
**Justification**: Frames the problem in terms of real challenges you've faced. Makes it clear why an embedded engineer would build this.

### 3. **Author Background Expansion**

**Change**: Added "real-time systems, regulatory compliance" and expanded target market\
**Justification**: Highlights additional valuable skills. Swiss companies care about regulatory knowledge.

### 4. **Architecture Diagram Update**

**Change**: Changed "RAG Orchestrator" to "Domain-Aware RAG Orchestrator"\
**Justification**: Small but important - shows this isn't generic orchestration but has special logic.

### 5. **Embedding Model Description**

**Change**: Added "emphasis on embedded systems terminology"\
**Justification**: Shows you understand domain-specific vocabulary matters for good retrieval.

### 6. **Smart Chunking Enhancement**

**Change**: Added "Special handling for hardware specifications and pinout tables"\
**Justification**: Demonstrates understanding of embedded documentation structure.

### 7. **Query Enhancement Section**

**Change**: Added hardware constraint detection and embedded acronyms\
**Justification**: This is your killer feature - no other RAG does this. It's practical and showcases domain knowledge.

### 8. **Answer Generation Updates**

**Change**: Added "Hardware feasibility notes when relevant"\
**Justification**: Shows the system can provide embedded-specific insights, not just retrieve text.

### 9. **Documentation Sources**

**Change**:

* Emphasized AI-relevant parts of RISC-V (vector extensions)
* Added Zephyr RTOS with ML subsystem
* Added TensorFlow Lite Micro and Edge Impulse
* Added one FDA guidance doc for medical context

**Justification**: Shows progression from pure embedded (RISC-V) to embedded AI (TF Lite Micro) to regulated embedded (FDA). Tells your career story through documentation choices.

### 10. **Evaluation Data Creation**

**Change**: Added embedded-specific query types (resource queries, compliance queries)\
**Justification**: Proves you can evaluate the system on real embedded AI challenges, not just generic questions.

### 11. **Custom Metrics**

**Change**: Added "Constraint Awareness" metric\
**Justification**: Unique evaluation criterion that only an embedded engineer would think to include.

### 12. **Skills Demonstrated**

**Change**: Added "Domain Expertise Integration" section\
**Justification**: Explicitly calls out how you're leveraging your background - important for recruiters to see.

### 13. **Project Structure**

**Change**: Added `query_enhancer.py` module\
**Justification**: Shows modular design and highlights the domain-specific enhancement as a key component.

### 14. **Configuration**

**Change**: Added `domain_config` section\
**Justification**: Makes domain features configurable, showing good software engineering practices.

### 15. **Repository Naming**

**Change**: Changed from "rag-technical-docs" to "embedded-ai-rag"\
**Justification**: Better SEO, clearer positioning, more memorable.

### 16. **Blog Title**

**Change**: "Building Domain-Aware RAG for Embedded AI"\
**Justification**: Positions you as someone who understands both domains deeply.

## Key Philosophy Behind Changes

The modifications follow three principles:

1. **Subtle Enhancement**: Didn't restructure your project, just added strategic touches that showcase your unique background

2. **Practical Focus**: Every addition solves a real problem you've likely encountered (checking if models fit on MCUs, understanding timing constraints)

3. **Progressive Disclosure**: Basic RAG users won't be confused, but embedded engineers will immediately recognize the specialized features

