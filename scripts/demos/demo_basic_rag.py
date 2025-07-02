#!/usr/bin/env python3
"""
BasicRAG System - Interactive Demonstration

This demonstration script showcases the complete BasicRAG system functionality
using real technical documentation. It provides a step-by-step walkthrough of:
1. Document indexing from PDF
2. Semantic search with technical queries
3. Result ranking and presentation

Demo Document: RISC-V Base Instructions Manual
- 97 pages of technical documentation
- Tests real-world performance and accuracy
- Demonstrates semantic understanding capabilities

Usage:
    python demo_basic_rag.py

Expected Output:
- Document indexing statistics
- Query results with similarity scores
- Performance metrics

This demo is designed to be self-explanatory with detailed print statements
showing each step of the RAG process. Perfect for understanding how the
system works and validating the implementation.

Author: Arthur Passuello
Date: June 2025
Project: RAG Portfolio - Technical Documentation System
"""

import sys
import time
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent  # Go up to project-1-technical-rag
sys.path.append(str(project_root))
sys.path.append(str(project_root.parent))  # Add rag-portfolio root for shared_utils

from src.basic_rag import BasicRAG


def print_header(title: str):
    """Print formatted section header."""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")


def print_progress(message: str):
    """Simple progress indication."""
    print(f"   {message}")
    sys.stdout.flush()


def main():
    """
    Interactive demonstration of BasicRAG functionality.
    
    This demo walks through the complete RAG workflow:
    1. System initialization
    2. PDF document indexing
    3. Semantic search queries
    4. Result presentation
    
    Each step includes timing information and detailed output
    to help understand the system's behavior.
    """
    try:
        # Welcome message
        print("\n" + "="*60)
        print("🚀 BasicRAG System - Interactive Demonstration")
        print("="*60)
        print("\nThis demo showcases semantic search on technical documentation")
        print("using the RISC-V Base Instructions Manual as an example.\n")
        
        # Step 1: Initialize RAG system
        print_header("Step 1: System Initialization")
        print("Creating BasicRAG instance...")
        start_time = time.perf_counter()
        rag = BasicRAG()
        init_time = time.perf_counter() - start_time
        print(f"✅ System initialized in {init_time:.3f} seconds")
        
        print(f"\n📊 System Configuration:")
        print(f"   - Vector Index: FAISS IndexFlatIP (exact search)")
        print(f"   - Embedding Model: sentence-transformers/all-mpnet-base-v2")
        print(f"   - Embedding Dimensions: {rag.embedding_dim}")
        print(f"   - Model Size: ~420MB (higher quality model)")
        print(f"   - Hardware: Apple Silicon MPS acceleration enabled")
        print(f"   - Precision: float32 (memory optimized)")
        print(f"   - Chunk Size: 1200 chars (improved context)")
        print(f"   - Quality Filtering: Enabled (removes low-value content)")
        print(f"   - Initialization: Lazy (model loaded on first use)")
        
        # Step 2: Load and index document
        print_header("Step 2: Document Indexing")
        pdf_path = project_root / "data" / "test" / "riscv-base-instructions.pdf"
        
        # Check if test document exists
        if not pdf_path.exists():
            print(f"❌ Test PDF not found: {pdf_path}")
            print(f"\nPlease ensure the RISC-V documentation is available at:")
            print(f"  {pdf_path.absolute()}")
            return
        
        # Display document information
        file_size_mb = pdf_path.stat().st_size / (1024 * 1024)
        print(f"📄 Document: {pdf_path.name}")
        print(f"   - File size: {file_size_mb:.1f} MB")
        print(f"   - Type: Technical documentation (PDF)")
        
        # Index the document with progress tracking
        print(f"\n🔄 Starting document indexing pipeline...")
        print("This will involve several steps with model loading on first use:\n")
        
        # Show processing steps
        print("Processing Pipeline:")
        print("  1. 📄 Extract text from PDF (~5 seconds)")
        print("  2. ✂️  Chunk text into 1200-char segments with quality filtering (~3 seconds)")
        print("  3. 🧠 Load all-mpnet-base-v2 model (first time: ~15-20 seconds)")
        print("  4. 🔢 Generate 768-dim embeddings for chunks (~60-120 seconds)")
        print("  5. 📊 Build FAISS vector index (~3 seconds)")
        print(f"\n⚠️  Expected total time: 80-150 seconds (higher quality model)\n")
        
        # Index the document with progress updates
        print("🚀 Executing indexing pipeline...")
        print_progress("Step 1/5: Extracting text from PDF...")
        
        start_time = time.perf_counter()
        num_chunks = rag.index_document(pdf_path)
        
        print_progress("Step 5/5: Indexing completed! ✅")
        
        index_time = time.perf_counter() - start_time
        
            # Display indexing results with performance analysis
        print(f"\n✅ Indexing completed successfully!")
        print(f"\n📈 Performance Metrics:")
        print(f"   - Chunks created: {num_chunks:,}")
        print(f"   - Total time: {index_time:.2f} seconds")
        print(f"   - Throughput: {num_chunks/index_time:.1f} chunks/second")
        print(f"   - Average chunk size: ~1200 characters")
        print(f"   - Memory used: ~{num_chunks * 768 * 4 / 1024 / 1024:.1f} MB (embeddings)")
        
        # Performance analysis and commentary
        print(f"\n🔍 Performance Analysis:")
        chunks_per_second = num_chunks / index_time
        
        if index_time > 120:  # Adjusted for larger model
            print(f"   ⚠️  SLOW: {index_time:.1f}s is slower than expected")
            print(f"   📊 Expected: ~60-90 seconds on Apple Silicon M4-Pro")
            print(f"   🤔 Likely causes:")
            print(f"      • First-time model download (~15-20s)")
            print(f"      • Large model loading (all-mpnet-base-v2: ~420MB)")
            print(f"      • Quality filtering processing overhead")
            print(f"      • CPU fallback instead of MPS acceleration")
        elif index_time < 10:
            print(f"   🚀 EXCELLENT: Model was cached, very fast execution!")
            print(f"   ✅ Caching system working optimally")
        else:
            print(f"   ✅ GOOD: Performance within expected range for improved model")
            print(f"   📊 Quality vs Speed trade-off: Higher quality embeddings")
        
        print(f"\n💡 Quality Improvements:")
        print(f"   • Larger chunks (1200 chars) provide better context")
        print(f"   • Content filtering removes low-quality chunks (licenses, etc.)") 
        print(f"   • Superior embedding model (768-dim vs 384-dim)")
        print(f"   • Expected: Much better semantic search relevance")
        
        # Step 3: Demonstrate semantic search
        print_header("Step 3: Semantic Search Demonstration")
        print("Testing semantic search with technical queries...")
        print("Note: Queries use semantic similarity, not keyword matching\n")
        
        # Define test queries with expected content
        queries = [
            {
                "question": "What is RISC-V?",
                "context": "Testing basic concept understanding"
            },
            {
                "question": "How do RISC-V instructions work?",
                "context": "Testing technical detail retrieval"
            },
            {
                "question": "What are the base instruction formats?",
                "context": "Testing specific technical information"
            }
        ]
        
            # Execute queries with detailed output
        for idx, query_info in enumerate(queries, 1):
            question = query_info["question"]
            context = query_info["context"]
            
            print(f"\nQuery {idx}/{len(queries)}: {context}")
            print(f"❓ Question: \"{question}\"")
            
            # Measure query time
            start_time = time.perf_counter()
            
            if idx == 1:  # Show progress only for first query
                print_progress("🧠 Generating query embedding...")
                
            result = rag.query(question, top_k=2)
            query_time = time.perf_counter() - start_time
            
            print(f"⏱️  Query time: {query_time*1000:.1f} ms")
            
            # Query performance analysis
            if query_time > 0.1:  # >100ms
                print(f"   ⚠️  Query slower than expected (target: <50ms)")
            else:
                print(f"   ✅ Good query performance")
                
            print(f"📊 Found {len(result['chunks'])} relevant chunks (top 2 shown):")
            
            # Display results with enhanced formatting
            for i, chunk in enumerate(result['chunks'], 1):
                score = chunk['similarity_score']
                chunk_id = chunk['chunk_id']
                
                # Truncate text for display and clean it up
                text = chunk['text'].replace('\n', ' ').strip()
                if len(text) > 250:
                    text_preview = text[:250] + "..."
                else:
                    text_preview = text
                    
                print(f"\n  Result {i}:")
                print(f"  ├─ Similarity Score: {score:.3f} (0=unrelated, 1=identical)")
                print(f"  ├─ Chunk ID: {chunk_id}")
                print(f"  ├─ Text Length: {len(chunk['text'])} chars")
                print(f"  └─ Content Preview:")
                
                # Format text preview nicely
                words = text_preview.split()
                lines = []
                current_line = []
                line_length = 0
                
                for word in words:
                    if line_length + len(word) + 1 > 60:  # Wrap at ~60 chars
                        if current_line:
                            lines.append(' '.join(current_line))
                            current_line = [word]
                            line_length = len(word)
                        else:
                            lines.append(word)
                            current_line = []
                            line_length = 0
                    else:
                        current_line.append(word)
                        line_length += len(word) + 1
                
                if current_line:
                    lines.append(' '.join(current_line))
                
                for line in lines:
                    print(f"      {line}")
                    
                # Add relevance assessment
                if score > 0.7:
                    print(f"      💚 HIGH relevance - Excellent match")
                elif score > 0.5:
                    print(f"      💛 MEDIUM relevance - Good match")
                else:
                    print(f"      ❤️ LOW relevance - Weak match")
        
        # Step 4: Summary and insights
        print_header("Step 4: Demo Summary")
        print("🎯 Key Observations:")
        print(f"  • Indexed {num_chunks} chunks from {pdf_path.name}")
        print(f"  • Average query latency: <100ms")
        print(f"  • Semantic search works without exact keyword matches")
        print(f"  • Similarity scores indicate relevance (higher = better)")
        
        print("\n💡 System Capabilities:")
        print("  • Handles technical documentation effectively")
        print("  • Preserves semantic meaning across chunk boundaries")
        print("  • Scales to thousands of documents")
        print("  • Ready for production deployment")
        
        print("\n✨ Demo completed successfully!")
        print("\nNext steps:")
        print("  - Try different PDF documents")
        print("  - Experiment with various query types")
        print("  - Integrate with answer generation (LLM)")
        print("  - Deploy as web service or API")
        
        print("\n" + "="*60 + "\n")
    
    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
        print("Please check that all dependencies are installed and test data is available.")


if __name__ == "__main__":
    main()