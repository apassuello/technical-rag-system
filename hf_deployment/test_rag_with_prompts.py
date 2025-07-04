"""
Test the RAG system with integrated prompt engineering improvements.
"""

import sys
import os
from pathlib import Path
import time

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from rag_with_generation import RAGWithGeneration


def test_rag_with_prompt_improvements():
    """Test the RAG system with new prompt engineering features."""
    print("🚀 Testing RAG with Prompt Engineering Improvements")
    print("=" * 60)
    
    # Initialize RAG system with prompt improvements using Google Gemma
    print("Initializing RAG system with adaptive prompts using Google Gemma...")
    rag = RAGWithGeneration(
        model_name="google/gemma-2-2b-it",
        api_token=os.getenv("HF_API_TOKEN", ""),
        use_ollama=False,
        use_inference_providers=False,
        enable_adaptive_prompts=True,
        enable_chain_of_thought=True
    )
    
    # Check if test document exists
    test_doc = Path("data/test/riscv-base-instructions.pdf")
    if not test_doc.exists():
        print(f"❌ Test document not found: {test_doc}")
        return False
    
    # Index the document
    print(f"Indexing document: {test_doc}")
    try:
        chunks_indexed = rag.index_document(test_doc)
        print(f"✅ Indexed {chunks_indexed} chunks")
    except Exception as e:
        print(f"❌ Failed to index document: {e}")
        return False
    
    # Test queries with different complexity levels
    test_queries = [
        {
            "name": "Simple Definition",
            "query": "What is RISC-V?",
            "expected_complexity": "simple"
        },
        {
            "name": "Complex Implementation", 
            "query": "How do I implement a complete interrupt handling system in RISC-V with nested interrupts, priority management, and context switching?",
            "expected_complexity": "complex"
        },
        {
            "name": "Comparison",
            "query": "What's the difference between machine mode and supervisor mode in RISC-V?",
            "expected_complexity": "moderate"
        },
        {
            "name": "Code Example",
            "query": "Show me an example of GPIO configuration in RISC-V",
            "expected_complexity": "moderate"
        }
    ]
    
    print(f"\nTesting {len(test_queries)} queries...")
    
    for i, test_case in enumerate(test_queries, 1):
        print(f"\n{'-'*50}")
        print(f"Test {i}: {test_case['name']}")
        print(f"Query: {test_case['query']}")
        
        # Test with adaptive prompts enabled
        print("\n🧠 Testing with adaptive prompts:")
        start_time = time.time()
        
        try:
            result = rag.query_with_answer(
                question=test_case['query'],
                top_k=3,
                use_hybrid=True,
                return_context=True
            )
            
            query_time = time.time() - start_time
            
            print(f"✅ Query completed in {query_time:.2f}s")
            print(f"📝 Answer length: {len(result['answer'])} chars")
            print(f"📊 Confidence: {result['confidence']:.1%}")
            print(f"📚 Citations: {len(result['citations'])}")
            print(f"🔍 Chunks retrieved: {result['retrieval_stats']['chunks_retrieved']}")
            print(f"🤖 Model: {result['generation_stats']['model']}")
            print(f"⏱️ Generation time: {result['generation_stats']['generation_time']:.2f}s")
            
            # Show first part of answer
            answer_preview = result['answer'][:200] + "..." if len(result['answer']) > 200 else result['answer']
            print(f"📖 Answer preview: {answer_preview}")
            
            # Show citations if any
            if result['citations']:
                print("📄 Citations found:")
                for j, citation in enumerate(result['citations'][:3], 1):
                    print(f"  {j}. {citation['source']} (Page {citation['page']})")
            
        except Exception as e:
            print(f"❌ Query failed: {e}")
            import traceback
            traceback.print_exc()
    
    # Test generator info
    print(f"\n{'-'*50}")
    print("Generator Information:")
    generator_info = rag.get_generator_info()
    for key, value in generator_info.items():
        print(f"  {key}: {value}")
    
    print(f"\n✅ All tests completed!")
    return True


def test_prompt_features_isolated():
    """Test prompt engineering features in isolation."""
    print("\n" + "=" * 60)
    print("🧪 Testing Prompt Features in Isolation")
    print("=" * 60)
    
    # Test adaptive engine
    try:
        from shared_utils.generation.adaptive_prompt_engine import AdaptivePromptEngine
        
        engine = AdaptivePromptEngine()
        
        # Test query complexity detection
        simple_query = "What is RISC-V?"
        complex_query = "How do I implement a complete interrupt handling system?"
        
        simple_complexity = engine.determine_query_complexity(simple_query)
        complex_complexity = engine.determine_query_complexity(complex_query)
        
        print(f"✅ Query complexity detection:")
        print(f"  Simple: '{simple_query}' -> {simple_complexity.value}")
        print(f"  Complex: '{complex_query[:40]}...' -> {complex_complexity.value}")
        
    except Exception as e:
        print(f"❌ Adaptive engine test failed: {e}")
    
    # Test chain-of-thought
    try:
        from shared_utils.generation.chain_of_thought_engine import ChainOfThoughtEngine
        from shared_utils.generation.prompt_templates import QueryType
        
        cot_engine = ChainOfThoughtEngine()
        
        # Test reasoning chain generation
        reasoning_chains = cot_engine.reasoning_chains
        
        print(f"\n✅ Chain-of-thought reasoning:")
        print(f"  Available query types: {len(reasoning_chains)}")
        for query_type in reasoning_chains.keys():
            chain_length = len(reasoning_chains[query_type])
            print(f"  {query_type.value}: {chain_length} reasoning steps")
        
    except Exception as e:
        print(f"❌ Chain-of-thought test failed: {e}")
    
    # Test prompt templates
    try:
        from shared_utils.generation.prompt_templates import TechnicalPromptTemplates
        
        templates = TechnicalPromptTemplates()
        
        test_query = "What is FreeRTOS?"
        template = templates.get_template_for_query(test_query)
        
        print(f"\n✅ Prompt templates:")
        print(f"  Query: '{test_query}'")
        print(f"  Detected type: {templates.detect_query_type(test_query).value}")
        print(f"  Has few-shot examples: {len(template.few_shot_examples) if template.few_shot_examples else 0}")
        
    except Exception as e:
        print(f"❌ Prompt templates test failed: {e}")


def main():
    """Run all tests."""
    print("🧠 RAG System with Prompt Engineering - Integration Tests")
    print("=" * 70)
    
    # Test isolated features first
    test_prompt_features_isolated()
    
    # Test full integration
    test_rag_with_prompt_improvements()
    
    print(f"\n🎉 Integration testing complete!")


if __name__ == "__main__":
    main()