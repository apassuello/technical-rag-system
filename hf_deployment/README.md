---
title: Technical RAG Assistant
emoji: 🔍
colorFrom: blue
colorTo: purple
sdk: docker
app_port: 8501
pinned: false
---

# Technical Documentation RAG Assistant

Advanced RAG system with local Ollama LLM integration running in HuggingFace Spaces.

## Features
- 🦙 **Local Ollama LLM** - No API dependencies
- 🔍 **Hybrid Search** - Semantic + keyword retrieval  
- 📚 **Citation Support** - Automatic source attribution
- 🎯 **Confidence Scoring** - Answer quality assessment
- ⚡ **Fast Performance** - Local inference

## Models Used
- **LLM**: Llama 3.2 3B (via Ollama)
- **Embeddings**: all-MiniLM-L6-v2
- **Fallback**: HuggingFace API if Ollama fails

## How it Works
1. Upload PDF documents
2. Documents are chunked and indexed
3. Ask questions in natural language
4. Get answers with citations and confidence scores

Built for technical documentation Q&A with Swiss engineering standards.