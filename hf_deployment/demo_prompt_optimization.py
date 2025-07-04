"""
Demo script showing prompt optimization capabilities with Ollama.
Non-interactive version for demonstration.
"""

import sys
import os
from pathlib import Path
import time

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from rag_with_generation import RAGWithGeneration


def demo_prompt_optimization():
    """Demonstrate prompt optimization with different configurations."""
    print("🧠 Prompt Optimization Demo with Local Ollama")
    print("=" * 60)
    
    # Test document
    test_doc = Path("data/test/riscv-base-instructions.pdf")
    
    # Test query
    test_query = "What is RISC-V and how does it work?"
    
    print(f"📄 Test Document: {test_doc}")
    print(f"❓ Test Query: {test_query}")
    print()
    
    # Test configurations
    configs = [
        {
            "name": "Baseline",
            "description": "Standard prompts without enhancements",
            "adaptive": False,
            "cot": False
        },
        {
            "name": "Adaptive Only", 
            "description": "Context-aware adaptive prompts",
            "adaptive": True,
            "cot": False
        },
        {
            "name": "Chain-of-Thought Only",
            "description": "Multi-step reasoning without adaptation",
            "adaptive": False,
            "cot": True
        },
        {
            "name": "Full Enhancement",
            "description": "Adaptive prompts + Chain-of-thought reasoning",
            "adaptive": True,
            "cot": True
        }
    ]
    
    results = {}
    
    for config in configs:
        print(f"{'='*50}")
        print(f"🧪 Testing: {config['name']}")
        print(f"📋 {config['description']}")
        print(f"{'='*50}")
        
        try:
            # Initialize RAG system with current configuration
            rag = RAGWithGeneration(
                model_name="llama3.2:3b",
                use_ollama=True,
                ollama_url="http://localhost:11434",
                enable_adaptive_prompts=config['adaptive'],
                enable_chain_of_thought=config['cot']
            )
            
            # Index document
            print("📚 Indexing document...")
            chunks_indexed = rag.index_document(test_doc)
            print(f"✅ Indexed {chunks_indexed} chunks")
            
            # Run query
            print(f"🔍 Running query: {test_query}")
            start_time = time.time()
            
            result = rag.query_with_answer(
                question=test_query,
                top_k=3,
                use_hybrid=True,
                return_context=False
            )
            
            query_time = time.time() - start_time
            
            # Store results
            results[config['name']] = {
                "answer": result['answer'],
                "confidence": result['confidence'],
                "citations": len(result['citations']),
                "time": query_time,
                "chunks_retrieved": result['retrieval_stats']['chunks_retrieved'],
                "generation_time": result['generation_stats']['generation_time']
            }
            
            # Display results
            print(f"\n📊 Results:")
            print(f"  ⏱️ Total time: {query_time:.2f}s")
            print(f"  🤖 Generation time: {result['generation_stats']['generation_time']:.2f}s")
            print(f"  📝 Answer length: {len(result['answer'])} chars")
            print(f"  📊 Confidence: {result['confidence']:.1%}")
            print(f"  📚 Citations: {len(result['citations'])}")
            print(f"  🔍 Chunks retrieved: {result['retrieval_stats']['chunks_retrieved']}")
            
            # Show answer preview
            answer_preview = result['answer'][:200] + "..." if len(result['answer']) > 200 else result['answer']
            print(f"\n📖 Answer Preview:")
            print(f"  {answer_preview}")
            
            # Show citations
            if result['citations']:
                print(f"\n📄 Citations:")
                for i, citation in enumerate(result['citations'][:3], 1):
                    print(f"  {i}. {citation['source']} (Page {citation['page']})")
            
            print(f"\n✅ {config['name']} completed successfully")
            
        except Exception as e:
            print(f"❌ {config['name']} failed: {e}")
            results[config['name']] = {
                "error": str(e),
                "time": 0,
                "confidence": 0,
                "citations": 0
            }
        
        print("\n" + "─" * 50 + "\n")
    
    # Compare all results
    print("📊 COMPARISON SUMMARY")
    print("=" * 60)
    
    print(f"{'Configuration':<20} {'Time':<8} {'Conf':<6} {'Cites':<6} {'Length':<8}")
    print("─" * 60)
    
    best_confidence = 0
    best_config = ""
    
    for config_name, result in results.items():
        if "error" not in result:
            time_str = f"{result['time']:.1f}s"
            conf_str = f"{result['confidence']:.1%}"
            cite_str = str(result['citations'])
            length_str = str(len(result['answer']))
            
            print(f"{config_name:<20} {time_str:<8} {conf_str:<6} {cite_str:<6} {length_str:<8}")
            
            if result['confidence'] > best_confidence:
                best_confidence = result['confidence']
                best_config = config_name
        else:
            print(f"{config_name:<20} {'ERROR':<8} {'0%':<6} {'0':<6} {'0':<8}")
    
    print("─" * 60)
    if best_config:
        print(f"🏆 Best performing: {best_config} ({best_confidence:.1%} confidence)")
    
    # Quality analysis
    print(f"\n📈 QUALITY ANALYSIS")
    print("─" * 30)
    
    for config_name, result in results.items():
        if "error" not in result:
            answer = result['answer']
            
            # Count technical terms
            tech_terms = ["RISC-V", "instruction", "architecture", "processor", "register", "ISA"]
            tech_count = sum(1 for term in tech_terms if term.lower() in answer.lower())
            
            # Count implementation details
            impl_terms = ["implement", "configure", "setup", "enable", "design"]
            impl_count = sum(1 for term in impl_terms if term.lower() in answer.lower())
            
            # Count reasoning indicators
            reasoning_terms = ["because", "therefore", "since", "due to", "first", "second", "then"]
            reasoning_count = sum(1 for term in reasoning_terms if term.lower() in answer.lower())
            
            print(f"{config_name}:")
            print(f"  Technical terms: {tech_count}")
            print(f"  Implementation details: {impl_count}")
            print(f"  Reasoning indicators: {reasoning_count}")
            print()
    
    print("🎉 Prompt optimization demo completed!")
    return results


def main():
    """Run the prompt optimization demo."""
    # Check if Ollama is running
    import requests
    try:
        response = requests.get("http://localhost:11434/api/tags", timeout=5)
        if response.status_code == 200:
            print("✅ Ollama server is running")
        else:
            print("❌ Ollama server not responding properly")
            return
    except Exception as e:
        print(f"❌ Cannot connect to Ollama server: {e}")
        print("Please start Ollama server with: ollama serve")
        return
    
    # Run the demo
    demo_prompt_optimization()


if __name__ == "__main__":
    main()