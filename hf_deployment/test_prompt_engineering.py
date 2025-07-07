"""
Local testing environment for prompt engineering improvements.

This script sets up a local testing environment to validate prompt optimizations
before deployment to production.
"""

import sys
import os
from pathlib import Path
import time
import json
from typing import Dict, List, Any

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.core.pipeline import RAGPipeline
from shared_utils.generation.prompt_templates import TechnicalPromptTemplates, QueryType
from shared_utils.generation.prompt_optimizer import PromptOptimizer, OptimizationMetric
from shared_utils.generation.adaptive_prompt_engine import AdaptivePromptEngine
from shared_utils.generation.chain_of_thought_engine import ChainOfThoughtEngine


class PromptEngineeringTester:
    """Local testing environment for prompt engineering improvements."""
    
    def __init__(self, test_doc_path: str = "data/test/riscv-base-instructions.pdf"):
        """Initialize the testing environment."""
        self.test_doc_path = Path(test_doc_path)
        self.rag_system = RAGPipeline("config/test.yaml")
        self.prompt_optimizer = PromptOptimizer(experiment_dir="experiments")
        self.adaptive_engine = AdaptivePromptEngine()
        self.cot_engine = ChainOfThoughtEngine()
        
        # Test queries for different scenarios
        self.test_queries = {
            "simple_definition": "What is RISC-V?",
            "complex_implementation": "How do I implement a complete interrupt handling system in RISC-V with nested interrupts, priority management, and context switching?",
            "comparison": "What's the difference between machine mode and supervisor mode in RISC-V?",
            "code_example": "Show me an example of GPIO configuration in RISC-V",
            "hardware_constraint": "Can a neural network model run on a RISC-V processor with 256KB RAM?",
            "troubleshooting": "How do I debug a timer interrupt that's not firing in RISC-V?"
        }
        
        print(f"Initialized testing environment with document: {self.test_doc_path}")
    
    def setup_test_environment(self) -> bool:
        """Set up the testing environment with indexed documents."""
        print("Setting up test environment...")
        
        # Check if test document exists
        if not self.test_doc_path.exists():
            print(f"❌ Test document not found: {self.test_doc_path}")
            return False
        
        # Index the test document
        try:
            chunks_indexed = self.rag_system.index_document(self.test_doc_path)
            print(f"✅ Indexed {chunks_indexed} chunks from test document")
            return True
        except Exception as e:
            print(f"❌ Failed to index document: {e}")
            return False
    
    def test_baseline_prompts(self) -> Dict[str, Any]:
        """Test baseline prompt performance."""
        print("\n" + "="*50)
        print("TESTING BASELINE PROMPTS")
        print("="*50)
        
        results = {}
        
        for query_name, query in self.test_queries.items():
            print(f"\nTesting: {query_name}")
            print(f"Query: {query}")
            
            # Get relevant chunks
            chunks = self.rag_system.query(query, top_k=3)
            
            # Test baseline prompt
            query_type = TechnicalPromptTemplates.detect_query_type(query)
            template = TechnicalPromptTemplates.get_template_for_query(query)
            
            # Format context
            context = self._format_chunks_for_prompt(chunks)
            
            # Generate prompt
            start_time = time.time()
            prompt = TechnicalPromptTemplates.format_prompt_with_template(
                query=query,
                context=context,
                template=template,
                include_few_shot=False  # Baseline without few-shot
            )
            prompt_time = time.time() - start_time
            
            # Analyze prompt
            results[query_name] = {
                "query": query,
                "query_type": query_type.value,
                "chunks_found": len(chunks),
                "prompt_generation_time": prompt_time,
                "prompt_length": len(prompt["user"]),
                "system_prompt_length": len(prompt["system"]),
                "has_few_shot": "few-shot" in prompt["user"].lower() or "examples" in prompt["user"].lower()
            }
            
            print(f"  - Query type: {query_type.value}")
            print(f"  - Chunks found: {len(chunks)}")
            print(f"  - Prompt length: {len(prompt['user'])} chars")
            print(f"  - Generation time: {prompt_time:.3f}s")
        
        return results
    
    def test_few_shot_prompts(self) -> Dict[str, Any]:
        """Test few-shot enhanced prompts."""
        print("\n" + "="*50)
        print("TESTING FEW-SHOT PROMPTS")
        print("="*50)
        
        results = {}
        
        for query_name, query in self.test_queries.items():
            print(f"\nTesting: {query_name}")
            
            # Get relevant chunks
            chunks = self.rag_system.query(query, top_k=3)
            
            # Test few-shot prompt
            query_type = TechnicalPromptTemplates.detect_query_type(query)
            template = TechnicalPromptTemplates.get_template_for_query(query)
            
            # Format context
            context = self._format_chunks_for_prompt(chunks)
            
            # Generate prompt with few-shot
            start_time = time.time()
            prompt = TechnicalPromptTemplates.format_prompt_with_template(
                query=query,
                context=context,
                template=template,
                include_few_shot=True
            )
            prompt_time = time.time() - start_time
            
            # Analyze prompt
            results[query_name] = {
                "query": query,
                "query_type": query_type.value,
                "chunks_found": len(chunks),
                "prompt_generation_time": prompt_time,
                "prompt_length": len(prompt["user"]),
                "system_prompt_length": len(prompt["system"]),
                "has_few_shot": "examples" in prompt["user"].lower(),
                "few_shot_examples": len(template.few_shot_examples) if template.few_shot_examples else 0
            }
            
            print(f"  - Few-shot examples: {results[query_name]['few_shot_examples']}")
            print(f"  - Prompt length: {len(prompt['user'])} chars")
            print(f"  - Generation time: {prompt_time:.3f}s")
        
        return results
    
    def test_adaptive_prompts(self) -> Dict[str, Any]:
        """Test adaptive prompt engine."""
        print("\n" + "="*50)
        print("TESTING ADAPTIVE PROMPTS")
        print("="*50)
        
        results = {}
        
        for query_name, query in self.test_queries.items():
            print(f"\nTesting: {query_name}")
            
            # Get relevant chunks
            chunks = self.rag_system.query(query, top_k=5)
            
            # Test adaptive prompt
            start_time = time.time()
            
            # Convert chunks to expected format
            formatted_chunks = []
            for chunk in chunks:
                if isinstance(chunk, dict):
                    formatted_chunks.append({
                        "content": chunk.get("content", chunk.get("text", "")),
                        "metadata": chunk.get("metadata", {}),
                        "confidence": chunk.get("score", 0.5)
                    })
                elif isinstance(chunk, str):
                    formatted_chunks.append({
                        "content": chunk,
                        "metadata": {},
                        "confidence": 0.5
                    })
                else:
                    formatted_chunks.append({
                        "content": str(chunk),
                        "metadata": {},
                        "confidence": 0.5
                    })
            
            # Generate adaptive configuration
            config = self.adaptive_engine.generate_adaptive_config(
                query=query,
                context_chunks=formatted_chunks,
                prefer_speed=False
            )
            
            # Create adaptive prompt
            adaptive_prompt = self.adaptive_engine.create_adaptive_prompt(
                query=query,
                context_chunks=formatted_chunks,
                config=config
            )
            
            prompt_time = time.time() - start_time
            
            # Analyze adaptive prompt
            results[query_name] = {
                "query": query,
                "query_complexity": config.query_complexity.value,
                "context_quality": config.context_quality.value,
                "chunks_found": len(chunks),
                "prompt_generation_time": prompt_time,
                "prompt_length": len(adaptive_prompt["user"]),
                "system_prompt_length": len(adaptive_prompt["system"]),
                "include_few_shot": config.include_few_shot,
                "enable_chain_of_thought": config.enable_chain_of_thought,
                "prefer_concise": config.prefer_concise
            }
            
            print(f"  - Query complexity: {config.query_complexity.value}")
            print(f"  - Context quality: {config.context_quality.value}")
            print(f"  - Few-shot enabled: {config.include_few_shot}")
            print(f"  - Chain-of-thought: {config.enable_chain_of_thought}")
            print(f"  - Prompt length: {len(adaptive_prompt['user'])} chars")
        
        return results
    
    def test_chain_of_thought_prompts(self) -> Dict[str, Any]:
        """Test chain-of-thought prompts for complex queries."""
        print("\n" + "="*50)
        print("TESTING CHAIN-OF-THOUGHT PROMPTS")
        print("="*50)
        
        results = {}
        
        # Test only complex queries for CoT
        complex_queries = {
            "complex_implementation": self.test_queries["complex_implementation"],
            "comparison": self.test_queries["comparison"],
            "troubleshooting": self.test_queries["troubleshooting"]
        }
        
        for query_name, query in complex_queries.items():
            print(f"\nTesting: {query_name}")
            
            # Get relevant chunks
            chunks = self.rag_system.query(query, top_k=5)
            
            # Test chain-of-thought prompt
            query_type = TechnicalPromptTemplates.detect_query_type(query)
            template = TechnicalPromptTemplates.get_template_for_query(query)
            
            # Format context
            context = self._format_chunks_for_prompt(chunks)
            
            # Generate CoT prompt
            start_time = time.time()
            cot_prompt = self.cot_engine.generate_chain_of_thought_prompt(
                query=query,
                query_type=query_type,
                context=context,
                base_template=template
            )
            prompt_time = time.time() - start_time
            
            # Analyze CoT prompt
            results[query_name] = {
                "query": query,
                "query_type": query_type.value,
                "chunks_found": len(chunks),
                "prompt_generation_time": prompt_time,
                "prompt_length": len(cot_prompt["user"]),
                "system_prompt_length": len(cot_prompt["system"]),
                "has_reasoning_steps": "Step 1:" in cot_prompt["user"],
                "reasoning_framework": "REASONING PROCESS:" in cot_prompt["user"]
            }
            
            print(f"  - Has reasoning steps: {results[query_name]['has_reasoning_steps']}")
            print(f"  - Reasoning framework: {results[query_name]['reasoning_framework']}")
            print(f"  - Prompt length: {len(cot_prompt['user'])} chars")
        
        return results
    
    def run_performance_comparison(self) -> Dict[str, Any]:
        """Run performance comparison across all prompt types."""
        print("\n" + "="*60)
        print("PERFORMANCE COMPARISON")
        print("="*60)
        
        # Run all tests
        baseline_results = self.test_baseline_prompts()
        few_shot_results = self.test_few_shot_prompts()
        adaptive_results = self.test_adaptive_prompts()
        cot_results = self.test_chain_of_thought_prompts()
        
        # Compare results
        comparison = {
            "baseline": baseline_results,
            "few_shot": few_shot_results,
            "adaptive": adaptive_results,
            "chain_of_thought": cot_results
        }
        
        # Calculate averages
        summary = {}
        for prompt_type, results in comparison.items():
            if results:
                avg_prompt_length = sum(r["prompt_length"] for r in results.values()) / len(results)
                avg_generation_time = sum(r["prompt_generation_time"] for r in results.values()) / len(results)
                
                summary[prompt_type] = {
                    "avg_prompt_length": avg_prompt_length,
                    "avg_generation_time": avg_generation_time,
                    "queries_tested": len(results)
                }
        
        # Print summary
        print("\nSUMMARY:")
        for prompt_type, stats in summary.items():
            print(f"\n{prompt_type.upper()}:")
            print(f"  - Average prompt length: {stats['avg_prompt_length']:.0f} chars")
            print(f"  - Average generation time: {stats['avg_generation_time']:.3f}s")
            print(f"  - Queries tested: {stats['queries_tested']}")
        
        return {
            "detailed_results": comparison,
            "summary": summary
        }
    
    def save_results(self, results: Dict[str, Any], filename: str = "prompt_test_results.json"):
        """Save test results to file."""
        output_path = Path(filename)
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\n✅ Results saved to: {output_path}")
    
    def _format_chunks_for_prompt(self, chunks: List[Any]) -> str:
        """Format chunks for prompt context."""
        if not chunks:
            return "No relevant context available."
        
        context_parts = []
        for i, chunk in enumerate(chunks):
            # Handle different chunk formats
            if isinstance(chunk, dict):
                chunk_text = chunk.get('content', chunk.get('text', ''))
                metadata = chunk.get('metadata', {})
                page_num = metadata.get('page_number', 'unknown')
                source = metadata.get('source', 'unknown')
            elif isinstance(chunk, str):
                chunk_text = chunk
                page_num = 'unknown'
                source = 'unknown'
            else:
                chunk_text = str(chunk)
                page_num = 'unknown' 
                source = 'unknown'
            
            context_parts.append(
                f"[chunk_{i+1}] (Page {page_num} from {source}):\n{chunk_text}"
            )
        
        return "\n\n---\n\n".join(context_parts)


def main():
    """Run the local prompt engineering tests."""
    print("🚀 Starting Prompt Engineering Local Tests")
    print("=" * 60)
    
    # Initialize tester
    tester = PromptEngineeringTester()
    
    # Set up environment
    if not tester.setup_test_environment():
        print("❌ Failed to set up test environment")
        return
    
    # Run comprehensive tests
    results = tester.run_performance_comparison()
    
    # Save results
    tester.save_results(results)
    
    print("\n🎉 Local testing complete!")
    print("Review the results to understand prompt performance differences.")


if __name__ == "__main__":
    main()