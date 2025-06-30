# Project 1: Advanced Technical Documentation RAG

## Project Overview

**Duration**: 3-4 weeks  
**Complexity**: Medium  
**Primary Goal**: Build production-grade RAG system demonstrating ML engineering fundamentals

### Business Context
Technical documentation is fragmented across PDFs, making it difficult for engineers to find specific implementation details quickly. Current search tools don't understand technical context or code relationships. This project creates an intelligent documentation assistant that understands technical context, code snippets, and cross-references, providing accurate answers with source attribution.

### Author Background
- **Arthur Passuello**: Embedded Systems Engineer transitioning to AI/ML
- **Current Skills**: 7 weeks intensive ML (transformers from scratch, multimodal systems)
- **Domain Expertise**: 2.5 years embedded systems in medical devices
- **Target Market**: Swiss tech companies (Lausanne/Geneva focus)

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
         │              │                  │              │
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
- **Primary LLM**: Mistral-7B-Instruct v0.2 (self-hosted)
  - Quantized with llama.cpp for efficiency
  - Running on HuggingFace Spaces (free T4 GPU)
- **Fallback**: GPT-3.5-turbo for complex queries
- **Cost Strategy**: 70% local models, 30% API usage

#### Embedding Models
- **Base Model**: BAAI/bge-base-en-v1.5
- **Fine-tuning**: On technical documentation vocabulary
- **Dimension**: 768
- **Special Features**: Optimized for code and technical terms

#### Vector Databases
- **Development**: FAISS (local, free)
- **Production**: ChromaDB (simple deployment)
- **Alternative**: Pinecone (if scaling needed)

#### Frameworks & Tools
- **RAG Framework**: LangChain + LangGraph
- **Document Processing**: 
  - PyMuPDF for PDF parsing
  - Unstructured.io for complex documents
- **Evaluation**: RAGAS framework
- **Monitoring**: Weights & Biases (free tier)
- **Deployment**: Streamlit + HuggingFace Spaces

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
- Preserve code blocks intact
- Maintain section hierarchies
- Keep tables and diagrams together
- Overlap: 10% for context preservation
- Chunk size: 512 tokens optimal

### 3. Query Enhancement
- Use transformer knowledge for query expansion
- Generate synonyms for technical terms
- Identify acronyms and expand them
- Add context from conversation history

### 4. Reranking Pipeline
- Cross-encoder: ms-marco-MiniLM-L-6-v2
- Score threshold: 0.7 for inclusion
- Max results: Top 5 after reranking

### 5. Answer Generation
- Streaming responses for better UX
- Source attribution with highlighting
- Confidence scoring
- Fallback to simpler explanation if needed

## Datasets & Resources

### Primary Documentation Sources

#### RISC-V Specifications
- **URL**: https://riscv.org/technical/specifications/
- **Content**: 
  - ISA manual (PDF, ~500 pages)
  - Privileged architecture (PDF, ~200 pages)
  - Vector extension (PDF, ~300 pages)
- **License**: Open source
- **Processing**: Extract chapters, preserve tables

#### FreeRTOS Documentation
- **URL**: https://www.freertos.org/Documentation/RTOS_book.html
- **Content**:
  - Kernel reference manual
  - API documentation
  - Porting guides
- **License**: MIT
- **Processing**: Parse API signatures specially

#### ARM Cortex-M Documentation
- **URL**: https://developer.arm.com/documentation/dui0553/latest/
- **Content**:
  - Technical reference manuals
  - Programming guides
  - Architecture specifications
- **License**: Free with registration
- **Processing**: Handle nested sections carefully

### Additional Resources
- **Linux Kernel Docs**: https://www.kernel.org/doc/html/latest/
- **Zephyr RTOS**: https://docs.zephyrproject.org/
- **OpenHW Group**: https://www.openhwgroup.org/

### Evaluation Data Creation
```python
# Generate test questions from docs
1. Extract section headings → "What is [heading]?"
2. Find code examples → "How to implement [function]?"
3. Locate parameters → "What are the parameters for [API]?"
4. Cross-references → "How does [A] relate to [B]?"

# Target: 200+ Q&A pairs
# Include difficulty levels: Easy/Medium/Hard
```

## Implementation Plan

### Week 1: Foundation
**Day 1-2: Environment & Data**
- Set up development environment
- Download all documentation PDFs
- Create initial project structure
- Configure git repository

**Day 3-4: Document Processing**
- Implement PDF parser with PyMuPDF
- Build smart chunking algorithm
- Extract metadata (sections, pages)
- Create document index

**Day 5-7: Embeddings & Storage**
- Fine-tune sentence transformer
- Set up FAISS vector store
- Implement document ingestion
- Test retrieval quality

### Week 2: Advanced Features
**Day 8-9: Hybrid Search**
- Implement BM25 sparse retrieval
- Create fusion algorithm
- Optimize search weights
- Benchmark performance

**Day 10-11: Query Processing**
- Build query expansion module
- Implement conversation memory
- Add context injection
- Handle multi-turn queries

**Day 12-14: Answer Generation**
- Integrate Mistral-7B locally
- Implement streaming responses
- Add source attribution
- Create answer validation

### Week 3: Production & Evaluation
**Day 15-16: Evaluation Framework**
- Set up RAGAS metrics
- Create test dataset
- Implement automated testing
- Generate performance reports

**Day 17-18: Optimization**
- Quantize models for speed
- Implement caching layer
- Add request batching
- Profile bottlenecks

**Day 19-21: Deployment**
- Build Streamlit interface
- Deploy to HuggingFace Spaces
- Create documentation
- Record demo video

## Evaluation Metrics

### RAGAS Framework Metrics
1. **Context Precision**: How relevant are retrieved documents?
2. **Context Recall**: Are all relevant documents retrieved?
3. **Faithfulness**: Does answer match source documents?
4. **Answer Relevancy**: Does answer address the query?

### Custom Metrics
- **Code Accuracy**: Correct code snippets retrieved
- **Technical Precision**: Accurate technical terms
- **Response Time**: < 2 seconds target
- **Source Quality**: Proper attribution

### Success Criteria
- 90%+ accuracy on test set
- < 2 second response time
- 95%+ uptime
- Positive user feedback

## Skills Demonstrated

### For Recruiters
1. **ML Engineering Competence**
   - "Built custom embeddings improving retrieval by 40%"
   - "Implemented production RAG handling 1000+ concurrent users"
   - "Achieved 94% accuracy on technical documentation queries"

2. **System Design Skills**
   - "Designed scalable architecture with proper abstractions"
   - "Implemented comprehensive monitoring and evaluation"
   - "Built fault-tolerant system with automatic fallbacks"

3. **Cost Optimization**
   - "Reduced inference costs by 95% using local models"
   - "Implemented intelligent caching reducing API calls by 80%"
   - "Balanced performance and cost for production deployment"

4. **Domain Expertise**
   - "Leveraged embedded systems knowledge for technical accuracy"
   - "Created specialized processing for code and documentation"
   - "Built system understanding hardware-software relationships"

### Portfolio Positioning
- **Not Another ChatGPT Wrapper**: Custom embeddings, advanced retrieval
- **Production-Ready**: Proper evaluation, monitoring, deployment
- **Domain-Specific**: Tailored for technical documentation
- **Cost-Conscious**: Hybrid approach balancing quality and cost

## Development Resources

### Setup Commands
```bash
# Create environment
conda create -n rag-tech-docs python=3.10
conda activate rag-tech-docs

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
technical-rag/
├── src/
│   ├── document_processor.py
│   ├── embeddings.py
│   ├── retrieval.py
│   ├── generation.py
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
```

## Risk Mitigation

### Identified Risks
1. **Data Quality**: PDFs may have poor formatting
   - Mitigation: Multiple parser fallbacks
   
2. **Model Size**: Large models slow on free GPUs
   - Mitigation: Quantization, caching
   
3. **Evaluation Complexity**: Creating good test sets
   - Mitigation: Start with 50 Q&A, expand gradually

## Next Steps

After completing this project:
1. Write technical blog post about hybrid retrieval
2. Create LinkedIn post with demo video
3. Prepare 5-minute technical presentation
4. Move to Project 2 (Multimodal Assistant)

## Repository
- **GitHub**: github.com/apassuello/rag-technical-docs
- **Demo**: huggingface.co/spaces/apassuello/tech-doc-assistant
- **Blog**: "Building Production RAG for Technical Documentation"