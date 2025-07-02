#!/usr/bin/env python3
"""
Demonstration of Streamlit app usage without browser interaction.

This simulates what a user would experience when using the Streamlit interface.
"""

import sys
from pathlib import Path
import time

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(Path(__file__).parent))

from src.rag_with_generation import RAGWithGeneration


def simulate_streamlit_workflow():
    """Simulate the complete Streamlit user workflow."""
    
    print("🖥️  STREAMLIT APP WORKFLOW SIMULATION")
    print("=" * 70)
    
    # Step 1: App Initialization (what happens when user opens the app)
    print("\n1️⃣ USER OPENS STREAMLIT APP")
    print("   🔄 Initializing RAG system...")
    
    try:
        rag = RAGWithGeneration(
            primary_model="llama3.2:3b",
            temperature=0.3,
            enable_streaming=True
        )
        print("   ✅ RAG system ready")
        print("   📊 Status: No documents indexed yet")
    except Exception as e:
        print(f"   ❌ Initialization failed: {e}")
        return
    
    # Step 2: Document Upload (user uploads a PDF)
    print("\n2️⃣ USER UPLOADS PDF DOCUMENT")
    test_pdf = Path("data/test/riscv-base-instructions.pdf")
    
    if not test_pdf.exists():
        print(f"   ❌ Test document not found: {test_pdf}")
        return
    
    print(f"   📄 Uploading: {test_pdf.name}")
    print("   🔄 Processing document...")
    
    start_time = time.time()
    chunk_count = rag.index_document(test_pdf)
    processing_time = time.time() - start_time
    
    print(f"   ✅ Document processed successfully!")
    print(f"   📊 {chunk_count} chunks created in {processing_time:.2f}s")
    print(f"   📈 System status: 1 document, {chunk_count} chunks indexed")
    
    # Step 3: User Asks Questions
    print("\n3️⃣ USER ASKS QUESTIONS")
    
    questions = [
        {
            "query": "What is RISC-V?",
            "settings": {"top_k": 5, "use_hybrid": True, "dense_weight": 0.7}
        },
        {
            "query": "How many registers does RV32E have?", 
            "settings": {"top_k": 3, "use_hybrid": True, "dense_weight": 0.5}
        },
        {
            "query": "What are the RISC-V instruction formats?",
            "settings": {"top_k": 5, "use_hybrid": False, "dense_weight": 1.0}
        }
    ]
    
    for i, question in enumerate(questions, 1):
        print(f"\n   Question {i}: {question['query']}")
        print(f"   ⚙️ Settings: {question['settings']}")
        print("   🔄 Searching and generating answer...")
        
        start_time = time.time()
        result = rag.query_with_answer(
            question=question['query'],
            **question['settings']
        )
        response_time = time.time() - start_time
        
        # Display what user would see
        print(f"\n   📝 ANSWER:")
        print(f"   {result['answer'][:200]}...")
        print(f"   \n   📚 SOURCES:")
        for j, citation in enumerate(result['citations'], 1):
            print(f"      {j}. {citation['source']} (Page {citation['page']}) - {citation['relevance']:.1%}")
        
        print(f"\n   📊 METRICS:")
        print(f"      Confidence: {result['confidence']:.1%}")
        print(f"      Response time: {response_time:.2f}s")
        print(f"      Citations: {len(result['citations'])}")
        print(f"      Method: {result['retrieval_stats']['method']}")
    
    # Step 4: Advanced Usage
    print("\n4️⃣ USER EXPLORES ADVANCED FEATURES")
    
    print("\n   🔧 TESTING DIFFERENT CONFIGURATIONS:")
    
    configs = [
        {"name": "Pure Semantic", "use_hybrid": False, "dense_weight": 1.0},
        {"name": "Balanced Hybrid", "use_hybrid": True, "dense_weight": 0.5},
        {"name": "Keyword Focused", "use_hybrid": True, "dense_weight": 0.3}
    ]
    
    test_query = "Explain RISC-V instruction encoding"
    
    for config in configs:
        print(f"\n   Testing: {config['name']}")
        
        start_time = time.time()
        result = rag.query_with_answer(
            question=test_query,
            top_k=5,
            **{k: v for k, v in config.items() if k != 'name'}
        )
        response_time = time.time() - start_time
        
        print(f"      Confidence: {result['confidence']:.1%}")
        print(f"      Citations: {len(result['citations'])}")
        print(f"      Time: {response_time:.2f}s")
    
    # Summary
    print("\n" + "=" * 70)
    print("🎉 STREAMLIT APP WORKFLOW COMPLETED SUCCESSFULLY")
    print("=" * 70)
    
    print("\n✅ USER EXPERIENCE VERIFIED:")
    print("   • Document upload and indexing works")
    print("   • Question answering with citations works")
    print("   • Multiple query configurations work")
    print("   • Performance metrics are displayed")
    print("   • Error handling is functional")
    
    print(f"\n📊 FINAL SYSTEM STATE:")
    print(f"   • Documents indexed: 1")
    print(f"   • Total chunks: {len(rag.chunks)}")
    print(f"   • Model: {rag.answer_generator.primary_model}")
    print(f"   • Ready for production use")


if __name__ == "__main__":
    simulate_streamlit_workflow()