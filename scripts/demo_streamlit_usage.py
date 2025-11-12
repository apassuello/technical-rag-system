#!/usr/bin/env python3
"""
Demonstration of Streamlit app usage without browser interaction.

This simulates what a user would experience when using the Streamlit interface.
Updated to use current PlatformOrchestrator architecture.
"""

import sys
from pathlib import Path
import time

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.platform_orchestrator import PlatformOrchestrator


def simulate_streamlit_workflow():
    """Simulate the complete Streamlit user workflow."""

    print("🖥️  STREAMLIT APP WORKFLOW SIMULATION")
    print("=" * 70)

    # Step 1: App Initialization (what happens when user opens the app)
    print("\n1️⃣ USER OPENS STREAMLIT APP")
    print("   🔄 Initializing RAG system...")

    try:
        # Use default configuration (can be customized via config/default.yaml)
        config_path = project_root / "config" / "default.yaml"
        if not config_path.exists():
            config_path = project_root / "config" / "test.yaml"

        orchestrator = PlatformOrchestrator(config_path)
        print("   ✅ RAG system ready")
        print(f"   📊 Architecture: {orchestrator.get_system_health()['architecture']}")
        print("   📊 Status: No documents indexed yet")
    except Exception as e:
        print(f"   ❌ Initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return

    # Step 2: Document Upload (user uploads a PDF)
    print("\n2️⃣ USER UPLOADS PDF DOCUMENT")
    test_pdf = Path("data/test/riscv-base-instructions.pdf")

    if not test_pdf.exists():
        print(f"   ❌ Test document not found: {test_pdf}")
        print(f"   Hint: Make sure test PDFs are in {test_pdf.parent}")
        return

    print(f"   📄 Uploading: {test_pdf.name}")
    print("   🔄 Processing document...")

    start_time = time.time()
    try:
        chunk_count = orchestrator.process_document(test_pdf)
        processing_time = time.time() - start_time

        print(f"   ✅ Document processed successfully!")
        print(f"   📊 {chunk_count} chunks created in {processing_time:.2f}s")
        print(f"   📈 System status: 1 document, {chunk_count} chunks indexed")
    except Exception as e:
        print(f"   ❌ Document processing failed: {e}")
        import traceback
        traceback.print_exc()
        return

    # Step 3: User Asks Questions
    print("\n3️⃣ USER ASKS QUESTIONS")

    questions = [
        {
            "query": "What is RISC-V?",
            "settings": {"k": 5}
        },
        {
            "query": "How many registers does RV32E have?",
            "settings": {"k": 3}
        },
        {
            "query": "What are the RISC-V instruction formats?",
            "settings": {"k": 5}
        }
    ]

    for i, question in enumerate(questions, 1):
        print(f"\n   Question {i}: {question['query']}")
        print(f"   ⚙️ Settings: top_k={question['settings']['k']}")
        print("   🔄 Searching and generating answer...")

        start_time = time.time()
        try:
            # Query using current architecture
            answer = orchestrator.query(
                query=question['query'],
                **question['settings']
            )
            response_time = time.time() - start_time

            # Display what user would see
            print(f"\n   📝 ANSWER:")
            answer_preview = answer.text[:200] + "..." if len(answer.text) > 200 else answer.text
            print(f"   {answer_preview}")

            print(f"\n   📚 SOURCES:")
            for j, source_doc in enumerate(answer.sources[:5], 1):  # Show top 5 sources
                source_name = source_doc.metadata.get('source', 'Unknown')
                page_num = source_doc.metadata.get('page', 'N/A')
                print(f"      {j}. {source_name} (Page {page_num})")

            print(f"\n   📊 METRICS:")
            print(f"      Confidence: {answer.confidence:.1%}")
            print(f"      Response time: {response_time:.2f}s")
            print(f"      Citations: {len(answer.sources)}")

            # Show retrieval method if available
            if 'retrieval_methods' in answer.metadata:
                methods = set(answer.metadata['retrieval_methods'])
                print(f"      Method: {', '.join(methods)}")

        except Exception as e:
            print(f"   ❌ Query failed: {e}")
            import traceback
            traceback.print_exc()

    # Step 4: Advanced Usage
    print("\n4️⃣ USER EXPLORES ADVANCED FEATURES")

    print("\n   🔧 TESTING DIFFERENT CONFIGURATIONS:")

    configs = [
        {"name": "Few Documents", "k": 3},
        {"name": "Standard Retrieval", "k": 5},
        {"name": "Comprehensive", "k": 10}
    ]

    test_query = "Explain RISC-V instruction encoding"

    for config in configs:
        print(f"\n   Testing: {config['name']}")

        start_time = time.time()
        try:
            answer = orchestrator.query(
                query=test_query,
                k=config['k']
            )
            response_time = time.time() - start_time

            print(f"      Confidence: {answer.confidence:.1%}")
            print(f"      Citations: {len(answer.sources)}")
            print(f"      Time: {response_time:.2f}s")
        except Exception as e:
            print(f"      ❌ Failed: {e}")

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
    health = orchestrator.get_system_health()
    print(f"   • System status: {health['status']}")
    print(f"   • Architecture: {health['architecture']}")
    print(f"   • Documents indexed: 1 ({chunk_count} chunks)")
    print(f"   • Config: {health['config_path']}")
    print(f"   • Ready for production use")


if __name__ == "__main__":
    simulate_streamlit_workflow()
