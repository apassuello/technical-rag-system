"""
Local prompt optimization testing with Ollama for back-and-forth iterations.
Uses local Ollama for responsive testing and Google Gemma for validation.
"""

import sys
import os
from pathlib import Path
import time
import json

# Add project paths
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))
sys.path.append(str(project_root.parent))

from src.rag_with_generation import RAGWithGeneration
from shared_utils.generation.prompt_templates import TechnicalPromptTemplates, QueryType
from shared_utils.generation.adaptive_prompt_engine import AdaptivePromptEngine
from shared_utils.generation.chain_of_thought_engine import ChainOfThoughtEngine


class PromptOptimizationTester:
    """Interactive prompt optimization testing with local Ollama."""

    def __init__(self):
        """Initialize the testing environment."""
        print("🚀 Initializing Prompt Optimization Testing Environment")
        print("=" * 60)

        # Initialize Ollama RAG system for local testing
        print("🦙 Setting up Ollama RAG system for local testing...")
        self.ollama_rag = RAGWithGeneration(
            model_name="llama3.2:3b",
            use_ollama=True,
            ollama_url="http://localhost:11434",
            enable_adaptive_prompts=True,
            enable_chain_of_thought=True,
        )

        # Initialize HF RAG system for validation
        print("🤗 Setting up HuggingFace RAG system for validation...")
        self.hf_rag = RAGWithGeneration(
            model_name="google/gemma-2-2b-it",
            api_token=os.getenv("HF_API_TOKEN", ""),
            use_ollama=False,
            enable_adaptive_prompts=True,
            enable_chain_of_thought=True,
        )

        # Test document
        self.test_doc = Path("data/test/riscv-base-instructions.pdf")

        # Test queries for optimization
        self.test_queries = {
            "simple": {
                "query": "What is RISC-V?",
                "expected_type": "definition",
                "complexity": "simple",
            },
            "implementation": {
                "query": "How do I configure GPIO pins for input and output in RISC-V?",
                "expected_type": "implementation",
                "complexity": "moderate",
            },
            "complex_implementation": {
                "query": "How do I implement a complete interrupt handling system in RISC-V with nested interrupts, priority management, and context switching?",
                "expected_type": "implementation",
                "complexity": "complex",
            },
            "comparison": {
                "query": "What's the difference between machine mode and supervisor mode in RISC-V?",
                "expected_type": "comparison",
                "complexity": "moderate",
            },
            "troubleshooting": {
                "query": "How do I debug a timer interrupt that's not firing in RISC-V?",
                "expected_type": "troubleshooting",
                "complexity": "moderate",
            },
        }

        print("✅ Environment initialized")

    def setup_test_data(self):
        """Set up test data by indexing the document."""
        print("\n📄 Setting up test data...")

        if not self.test_doc.exists():
            print(f"❌ Test document not found: {self.test_doc}")
            return False

        try:
            # Index document in both systems
            print("Indexing document in Ollama system...")
            ollama_chunks = self.ollama_rag.index_document(self.test_doc)
            print(f"✅ Ollama: {ollama_chunks} chunks indexed")

            print("Indexing document in HF system...")
            hf_chunks = self.hf_rag.index_document(self.test_doc)
            print(f"✅ HuggingFace: {hf_chunks} chunks indexed")

            return True

        except Exception as e:
            print(f"❌ Failed to index documents: {e}")
            return False

    def test_prompt_variations(self, query_name: str, interactive: bool = True):
        """Test different prompt variations for a specific query."""
        print(f"\n{'='*60}")
        print(f"🧪 Testing Prompt Variations: {query_name}")
        print(f"{'='*60}")

        query_info = self.test_queries[query_name]
        query = query_info["query"]

        print(f"Query: {query}")
        print(f"Expected complexity: {query_info['complexity']}")
        print(f"Expected type: {query_info['expected_type']}")

        # Test 1: Baseline prompt (no adaptive features)
        print(f"\n{'-'*40}")
        print("📝 Test 1: Baseline Prompt (No Adaptive Features)")
        print(f"{'-'*40}")

        baseline_rag = RAGWithGeneration(
            model_name="llama3.2:3b",
            use_ollama=True,
            enable_adaptive_prompts=False,
            enable_chain_of_thought=False,
        )
        baseline_rag.index_document(self.test_doc)

        baseline_result = self._test_query(baseline_rag, query, "Baseline")

        # Test 2: Adaptive prompts only
        print(f"\n{'-'*40}")
        print("🧠 Test 2: Adaptive Prompts Only")
        print(f"{'-'*40}")

        adaptive_rag = RAGWithGeneration(
            model_name="llama3.2:3b",
            use_ollama=True,
            enable_adaptive_prompts=True,
            enable_chain_of_thought=False,
        )
        adaptive_rag.index_document(self.test_doc)

        adaptive_result = self._test_query(adaptive_rag, query, "Adaptive")

        # Test 3: Chain-of-thought only
        print(f"\n{'-'*40}")
        print("🔗 Test 3: Chain-of-Thought Only")
        print(f"{'-'*40}")

        cot_rag = RAGWithGeneration(
            model_name="llama3.2:3b",
            use_ollama=True,
            enable_adaptive_prompts=False,
            enable_chain_of_thought=True,
        )
        cot_rag.index_document(self.test_doc)

        cot_result = self._test_query(cot_rag, query, "Chain-of-Thought")

        # Test 4: Both adaptive and chain-of-thought
        print(f"\n{'-'*40}")
        print("⚡ Test 4: Adaptive + Chain-of-Thought")
        print(f"{'-'*40}")

        full_result = self._test_query(self.ollama_rag, query, "Full Enhancement")

        # Compare results
        self._compare_results(
            query_name,
            {
                "baseline": baseline_result,
                "adaptive": adaptive_result,
                "chain_of_thought": cot_result,
                "full_enhancement": full_result,
            },
        )

        # Interactive optimization if requested
        if interactive:
            self._interactive_optimization(query, query_info)

    def _test_query(self, rag_system, query: str, test_name: str):
        """Test a single query and return results."""
        print(f"Testing: {test_name}")

        start_time = time.time()
        try:
            result = rag_system.query_with_answer(
                question=query, top_k=3, use_hybrid=True, return_context=True
            )

            query_time = time.time() - start_time

            print(f"  ⏱️ Time: {query_time:.2f}s")
            print(f"  📝 Answer length: {len(result['answer'])} chars")
            print(f"  📊 Confidence: {result['confidence']:.1%}")
            print(f"  📚 Citations: {len(result['citations'])}")

            # Show answer preview
            preview = (
                result["answer"][:150] + "..."
                if len(result["answer"]) > 150
                else result["answer"]
            )
            print(f"  📖 Preview: {preview}")

            return {
                "answer": result["answer"],
                "confidence": result["confidence"],
                "citations": len(result["citations"]),
                "time": query_time,
                "chunks_retrieved": result["retrieval_stats"]["chunks_retrieved"],
            }

        except Exception as e:
            print(f"  ❌ Error: {e}")
            return {
                "answer": f"Error: {e}",
                "confidence": 0.0,
                "citations": 0,
                "time": 0.0,
                "chunks_retrieved": 0,
            }

    def _compare_results(self, query_name: str, results: dict):
        """Compare results from different prompt variations."""
        print(f"\n📊 Results Comparison for {query_name}")
        print("=" * 50)

        # Create comparison table
        headers = ["Method", "Time (s)", "Confidence", "Citations", "Length"]
        print(f"{'Method':<20} {'Time':<8} {'Conf':<6} {'Cites':<6} {'Length':<8}")
        print("-" * 50)

        best_confidence = 0
        best_method = ""

        for method, result in results.items():
            time_str = f"{result['time']:.1f}s"
            conf_str = f"{result['confidence']:.1%}"
            cite_str = str(result["citations"])
            length_str = str(len(result["answer"]))

            print(
                f"{method:<20} {time_str:<8} {conf_str:<6} {cite_str:<6} {length_str:<8}"
            )

            if result["confidence"] > best_confidence:
                best_confidence = result["confidence"]
                best_method = method

        print("-" * 50)
        print(f"🏆 Best confidence: {best_method} ({best_confidence:.1%})")

        # Quality analysis
        print(f"\n📈 Quality Analysis:")
        for method, result in results.items():
            answer = result["answer"]

            # Check for technical terms
            tech_terms = [
                "RISC-V",
                "register",
                "instruction",
                "architecture",
                "processor",
            ]
            tech_count = sum(1 for term in tech_terms if term.lower() in answer.lower())

            # Check for implementation details
            impl_terms = ["configure", "implement", "steps", "setup", "enable"]
            impl_count = sum(1 for term in impl_terms if term.lower() in answer.lower())

            print(f"  {method}: Tech terms: {tech_count}, Impl details: {impl_count}")

    def _interactive_optimization(self, query: str, query_info: dict):
        """Interactive prompt optimization session."""
        print(f"\n🔧 Interactive Optimization Session")
        print("=" * 40)

        while True:
            print(f"\nOptions:")
            print("1. Test with HuggingFace Gemma for validation")
            print("2. Analyze query complexity detection")
            print("3. Test custom prompt modifications")
            print("4. Compare few-shot vs zero-shot")
            print("5. Exit optimization")

            try:
                choice = input("\nEnter choice (1-5): ").strip()

                if choice == "1":
                    self._test_hf_validation(query)
                elif choice == "2":
                    self._analyze_query_complexity(query, query_info)
                elif choice == "3":
                    self._test_custom_prompts(query)
                elif choice == "4":
                    self._compare_few_shot(query)
                elif choice == "5":
                    print("🏁 Exiting optimization session")
                    break
                else:
                    print("❌ Invalid choice. Please enter 1-5.")

            except KeyboardInterrupt:
                print("\n🏁 Optimization session interrupted")
                break
            except Exception as e:
                print(f"❌ Error: {e}")

    def _test_hf_validation(self, query: str):
        """Test the same query with HuggingFace Gemma for validation."""
        print(f"\n🤗 Testing with HuggingFace Gemma-2-2B-IT")
        print("-" * 40)

        try:
            result = self.hf_rag.query_with_answer(
                question=query, top_k=3, use_hybrid=True
            )

            print(f"✅ HF Gemma Response:")
            print(f"  📝 Answer: {result['answer']}")
            print(f"  📊 Confidence: {result['confidence']:.1%}")
            print(f"  📚 Citations: {len(result['citations'])}")
            print(f"  ⏱️ Time: {result['generation_stats']['generation_time']:.2f}s")

        except Exception as e:
            print(f"❌ HF Gemma failed: {e}")

    def _analyze_query_complexity(self, query: str, query_info: dict):
        """Analyze how the system detects query complexity."""
        print(f"\n🔍 Query Complexity Analysis")
        print("-" * 30)

        # Use adaptive engine directly
        adaptive_engine = AdaptivePromptEngine()

        detected_complexity = adaptive_engine.determine_query_complexity(query)
        print(f"Query: {query}")
        print(f"Expected complexity: {query_info['complexity']}")
        print(f"Detected complexity: {detected_complexity.value}")
        print(
            f"Match: {'✅' if detected_complexity.value == query_info['complexity'] else '❌'}"
        )

        # Analyze prompt template detection
        templates = TechnicalPromptTemplates()
        detected_type = templates.detect_query_type(query)
        print(f"Expected type: {query_info['expected_type']}")
        print(f"Detected type: {detected_type.value}")
        print(
            f"Match: {'✅' if detected_type.value == query_info['expected_type'] else '❌'}"
        )

    def _test_custom_prompts(self, query: str):
        """Test custom prompt modifications."""
        print(f"\n✏️ Custom Prompt Testing")
        print("-" * 25)

        print("Enter custom system prompt (or press Enter for default):")
        custom_system = input().strip()

        print("Enter custom user prompt template (or press Enter for default):")
        custom_user = input().strip()

        if custom_system or custom_user:
            print("🧪 Testing custom prompt...")
            # This would require implementing custom prompt testing
            print("⚠️ Custom prompt testing not yet implemented")
        else:
            print("Using default prompts")

    def _compare_few_shot(self, query: str):
        """Compare few-shot vs zero-shot prompting."""
        print(f"\n🎯 Few-Shot vs Zero-Shot Comparison")
        print("-" * 35)

        # This would test with and without few-shot examples
        print("🧪 Testing few-shot examples...")
        print("⚠️ Few-shot comparison not yet fully implemented")

    def run_optimization_suite(self):
        """Run the complete optimization suite."""
        print("🚀 Starting Prompt Optimization Suite")
        print("=" * 50)

        if not self.setup_test_data():
            return

        for query_name in self.test_queries.keys():
            print(f"\n🎯 Testing query: {query_name}")

            # Ask if user wants to test this query
            response = input(f"Test '{query_name}'? (y/n/q): ").strip().lower()

            if response == "q":
                break
            elif response == "y" or response == "":
                self.test_prompt_variations(query_name, interactive=True)
            else:
                print(f"⏭️ Skipping {query_name}")

        print("\n🎉 Optimization suite complete!")


def main():
    """Run the prompt optimization testing."""
    print("🧠 Prompt Optimization Testing with Local Ollama")
    print("=" * 60)

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

    # Initialize and run tester
    tester = PromptOptimizationTester()
    tester.run_optimization_suite()


if __name__ == "__main__":
    main()
