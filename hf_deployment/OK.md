---
title: Technical RAG Assistant
emoji: 🔍
colorFrom: blue
colorTo: purple
sdk: docker
pinned: false
license: mit
app_port: 8501
---

# Technical Documentation RAG Assistant

Advanced hybrid retrieval system with local LLM answer generation, optimized for technical documentation Q&A.

## Features

- **Hybrid Search**: Combines semantic similarity with BM25 keyword matching
- **Pro-Tier Models**: Mistral-7B, CodeLlama, Llama-2 with HuggingFace Pro
- **Document Processing**: PDF parsing with intelligent chunking
- **Citation Support**: Accurate source attribution with chunk references
- **Real-time Performance**: Sub-second retrieval with detailed metrics

## Usage

1. **Add HF Token**: Paste your HuggingFace Pro token in the sidebar
2. **Select Model**: Choose from Mistral, CodeLlama, or Llama-2
3. **Upload Documents**: Process PDFs for technical Q&A
4. **Ask Questions**: Get answers with proper citations

## Model Recommendations

- **Technical Q&A**: `mistralai/Mistral-7B-Instruct-v0.2`
- **Code Documentation**: `codellama/CodeLlama-7b-Instruct-hf`
- **Complex Queries**: `meta-llama/Llama-2-7b-chat-hf`

Built for ML Engineer Portfolio | Swiss Tech Market Focus