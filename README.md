# 🔍 Technical Documentation RAG Assistant

A production-ready RAG (Retrieval-Augmented Generation) system for technical documentation Q&A, built for ML Engineer portfolio demonstration in the Swiss tech market.

## 🌟 Key Features

- **🚀 Hybrid Retrieval**: Combines semantic search (embeddings) with keyword search (BM25) using Reciprocal Rank Fusion
- **🤖 Local LLM**: Llama 3.2 (3B) via Ollama for privacy and speed
- **📚 Multi-Document Support**: Process and search across multiple PDF documents simultaneously  
- **🎯 Smart Citations**: Automatic source attribution with page numbers and relevance scores
- **⚡ Apple Silicon Optimized**: MPS acceleration for embedding generation
- **🔧 Advanced Options**: Configurable search weights and retrieval methods
- **📊 Quality Metrics**: Confidence scoring and detailed performance analytics

## 🏗️ Architecture

```
📄 PDF Documents → 🔗 Hybrid Parser (TOC + PDFPlumber) → 
🧩 Quality Chunks (0% fragments) → 🔢 Embeddings (FAISS) → 
🔍 Hybrid Search (Dense + Sparse + RRF) → 🤖 Local LLM → 
📝 Cited Answers
```

## 🎯 Performance Metrics

- **Document Processing**: 28.4 chunks/second, <10s per document
- **Query Response**: <2s retrieval + 6-15s generation = 8-17s total  
- **Chunk Quality**: 99.5% optimal sizing, 0% fragments, 0.967 avg quality score
- **Memory Usage**: <500MB for complete pipeline
- **Citation Accuracy**: 85-95% confidence with proper source attribution

## 🚀 Quick Start

### 1. Setup Environment
```bash
# Install Ollama
brew install ollama

# Pull required model
ollama pull llama3.2:3b

# Install Python dependencies
pip install -r requirements.txt
```

### 2. Run the Application
```bash
streamlit run streamlit_app.py
```

### 3. Use the System
1. **Upload Documents**: Use the "Manage Documents" tab to upload PDF files
2. **Ask Questions**: Enter technical questions in the "Ask Questions" tab
3. **Explore Options**: Adjust hybrid search weights and retrieval methods
4. **Review Results**: Get comprehensive answers with source citations

## 📁 Project Structure

```
project-1-technical-rag/
├── streamlit_app.py              # Main Streamlit interface
├── src/
│   ├── basic_rag.py             # Core RAG system with hybrid search
│   ├── rag_with_generation.py   # RAG + answer generation integration  
│   ├── sparse_retrieval.py      # BM25 sparse retrieval
│   └── fusion.py                # Score fusion algorithms
├── shared_utils/
│   ├── document_processing/     # PDF parsing & chunking
│   ├── embeddings/             # Embedding generation
│   ├── generation/             # Answer generation & prompts
│   └── retrieval/              # Hybrid search systems
├── tests/                       # Comprehensive test suite
├── scripts/                     # Development & analysis tools
└── data/test/                   # Sample documents
```

## 🧪 Technical Innovation

### Hybrid Document Parser
- **TOC-Guided Navigation**: Uses table of contents for structure mapping
- **PDFPlumber Precision**: Advanced PDF parsing with metadata preservation  
- **Quality Filtering**: Removes artifacts while preserving technical content
- **Achieved**: 99.5% optimal chunks, 0% fragment rate

### Advanced Retrieval System
- **Dense Retrieval**: Semantic similarity via sentence transformers
- **Sparse Retrieval**: BM25 keyword matching with technical optimization
- **Fusion Algorithm**: Reciprocal Rank Fusion with configurable parameters
- **Optimal Config**: 70% dense + 30% sparse weighting

### Domain-Specific Prompting
- **7 Specialized Templates**: Definition, implementation, comparison, etc.
- **Auto-Detection**: Automatically selects appropriate prompt template
- **Technical Focus**: Optimized for embedded systems and AI documentation

## 📊 Evaluation & Quality Assurance

### Manual Verification Framework
- **Content Quality**: 99.5% technical content, <1% artifacts
- **Citation Accuracy**: Proper source attribution with page numbers
- **Fragment Detection**: 0% incomplete sentences or broken context
- **Cross-Document Testing**: Verified multi-source retrieval and citation

### Performance Benchmarks
- **Retrieval Quality**: 78% score variation (vs 40% baseline)
- **Answer Confidence**: 85-95% on technical queries
- **Source Coverage**: 91.6% average page coverage
- **System Reliability**: 100% document processing success rate

## 🎓 Educational Value

### ML Engineering Best Practices
- **Modular Architecture**: Clean separation of concerns
- **Comprehensive Testing**: Unit, integration, and end-to-end tests
- **Quality Metrics**: Evidence-based evaluation methodology
- **Production Readiness**: Error handling, monitoring, deployment

### Swiss Tech Market Alignment
- **Quality Focus**: Thorough testing and validation
- **Technical Excellence**: Advanced algorithms and optimization  
- **Reliability**: Robust error handling and graceful degradation
- **Documentation**: Comprehensive guides and analysis

## 🛠️ Development Commands

```bash
# Run tests
python -m pytest tests/ -v

# Test end-to-end pipeline
python test_answer_generation.py

# Test multi-document support  
python test_multi_document_support.py

# Analyze chunk quality
python scripts/analysis/comprehensive_chunk_analysis.py

# Run RAG faithfulness tests
python scripts/analysis/rag_faithfulness_suite.py
```

## 🌍 Deployment

### Local Development
- Optimized for Apple Silicon M4-Pro
- Uses MPS acceleration for embeddings
- Local LLM via Ollama for privacy

### HuggingFace Spaces  
- Production deployment ready
- Streamlit interface optimized for web
- Resource-efficient for cloud hosting

## 📈 Future Enhancements

- **RAGAS Evaluation**: Comprehensive evaluation framework
- **Streaming UI**: Real-time answer generation display
- **Advanced Analytics**: Query pattern analysis and optimization
- **API Interface**: RESTful API for programmatic access

## 👨‍💻 About

**Author**: Arthur Passuello  
**Background**: Embedded Systems → AI/ML transition  
**Experience**: 2.5 years medical device firmware + 7-week ML intensive  
**Focus**: Production-ready ML systems for Swiss tech market  

Built to demonstrate ML engineering excellence with domain expertise in embedded systems and technical documentation processing.

---

*🔍 This project showcases advanced RAG system development, combining cutting-edge ML techniques with practical software engineering for real-world technical documentation challenges.*