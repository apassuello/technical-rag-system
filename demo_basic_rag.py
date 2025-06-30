#!/usr/bin/env python3
"""
Demo script showing BasicRAG functionality.
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from src.basic_rag import BasicRAG


def main():
    """Demo BasicRAG with RISC-V documentation."""
    print("🚀 BasicRAG Demo")
    print("=" * 50)
    
    # Initialize RAG system
    rag = BasicRAG()
    
    # Index the test document
    pdf_path = Path("data/test/riscv-base-instructions.pdf")
    
    if not pdf_path.exists():
        print(f"❌ Test PDF not found: {pdf_path}")
        return
    
    print(f"📄 Indexing document: {pdf_path.name}")
    num_chunks = rag.index_document(pdf_path)
    print(f"✅ Indexed {num_chunks} chunks")
    
    # Demo queries
    questions = [
        "What is RISC-V?",
        "How do RISC-V instructions work?",
        "What are the base instruction formats?"
    ]
    
    for question in questions:
        print(f"\n❓ Question: {question}")
        result = rag.query(question, top_k=2)
        
        print(f"📊 Found {len(result['chunks'])} relevant chunks:")
        for i, chunk in enumerate(result['chunks'], 1):
            score = chunk['similarity_score']
            text_preview = chunk['text'][:150] + "..."
            print(f"  {i}. Score: {score:.3f}")
            print(f"     Preview: {text_preview}")
    
    print("\n✨ Demo completed!")


if __name__ == "__main__":
    main()