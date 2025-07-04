#!/usr/bin/env python3
"""
Performance profiling script for RAG system.

Identifies bottlenecks in the query processing pipeline
to optimize response time from 5-10s to <2s target.
"""

import sys
from pathlib import Path
import time
import statistics
from contextlib import contextmanager

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(Path(__file__).parent))

from src.rag_with_generation import RAGWithGeneration
from shared_utils.generation.answer_generator import AnswerGenerator


@contextmanager
def timer(operation_name: str):
    """Context manager for timing operations."""
    start_time = time.time()
    yield
    end_time = time.time()
    elapsed = end_time - start_time
    print(f"⏱️  {operation_name}: {elapsed:.3f}s")
    return elapsed


def profile_complete_pipeline():
    """Profile the complete RAG pipeline end-to-end."""
    print("🚀 PROFILING COMPLETE RAG PIPELINE")
    print("=" * 60)
    
    # Initialize system
    print("\n1. SYSTEM INITIALIZATION")
    print("-" * 30)
    
    with timer("RAG system initialization"):
        rag = RAGWithGeneration(
            primary_model="llama3.2:3b",
            temperature=0.3,
            enable_streaming=False  # Test non-streaming first
        )
    
    # Check if documents are already indexed
    existing_chunks = len(getattr(rag, 'chunks', []))
    print(f"Existing chunks in index: {existing_chunks}")
    
    if existing_chunks == 0:
        print("\n2. DOCUMENT INDEXING (if needed)")
        print("-" * 30)
        test_pdf = Path("data/test/riscv-base-instructions.pdf")
        
        if test_pdf.exists():
            with timer("Document indexing"):
                chunk_count = rag.index_document(test_pdf)
            print(f"Indexed {chunk_count} chunks")
        else:
            print("❌ Test document not found, using mock chunks")
            # Create mock chunks for testing
            rag.chunks = [{
                "text": "RISC-V is an open-source instruction set architecture.",
                "page": 1,
                "source": "test.pdf",
                "chunk_id": 0,
                "quality_score": 0.95
            }] * 10
    
    # Test queries with different complexities
    test_queries = [
        "What is RISC-V?",
        "How does RISC-V determine instruction length?", 
        "What are the main features of RISC-V architecture?",
    ]
    
    print(f"\n3. QUERY PROCESSING ANALYSIS")
    print("-" * 30)
    
    total_times = []
    
    for i, query in enumerate(test_queries, 1):
        print(f"\nQuery {i}: {query}")
        print("-" * 40)
        
        # Measure complete pipeline
        pipeline_start = time.time()
        
        try:
            with timer("Complete query processing"):
                result = rag.query_with_answer(
                    question=query,
                    top_k=5,
                    use_hybrid=True,
                    dense_weight=0.7,
                    return_context=True
                )
            
            total_time = time.time() - pipeline_start
            total_times.append(total_time)
            
            print(f"✅ Success: {result['confidence']:.1%} confidence, {len(result['citations'])} citations")
            print(f"📊 Stats: Retrieval: {result['retrieval_stats']['retrieval_time']:.3f}s, Generation: {result['generation_stats']['generation_time']:.3f}s")
            
        except Exception as e:
            print(f"❌ Error: {e}")
    
    # Summary statistics
    if total_times:
        print(f"\n4. PERFORMANCE SUMMARY")
        print("-" * 30)
        print(f"Average response time: {statistics.mean(total_times):.3f}s")
        print(f"Min response time: {min(total_times):.3f}s")
        print(f"Max response time: {max(total_times):.3f}s")
        print(f"Target: <2.0s")
        print(f"Status: {'✅ PASS' if max(total_times) < 2.0 else '❌ NEEDS OPTIMIZATION'}")
        
        return statistics.mean(total_times)
    
    return float('inf')


def profile_individual_components():
    """Profile individual components to identify bottlenecks."""
    print("\n\n🔬 PROFILING INDIVIDUAL COMPONENTS")
    print("=" * 60)
    
    # Test answer generation in isolation
    print("\n1. ANSWER GENERATION COMPONENT")
    print("-" * 40)
    
    generator = AnswerGenerator()
    
    # Mock chunks
    test_chunks = [{
        "id": "chunk_1",
        "content": "RISC-V is an open-source instruction set architecture (ISA) based on reduced instruction set computer (RISC) principles.",
        "metadata": {"page_number": 1, "source": "riscv-spec.pdf"},
        "score": 0.95
    }]
    
    query = "What is RISC-V?"
    
    # Test multiple iterations for consistent timing
    generation_times = []
    
    for i in range(3):
        with timer(f"Answer generation (run {i+1})"):
            start = time.time()
            result = generator.generate(query, test_chunks)
            elapsed = time.time() - start
            generation_times.append(elapsed)
    
    avg_generation_time = statistics.mean(generation_times)
    print(f"Average generation time: {avg_generation_time:.3f}s")
    
    # Identify what's taking time in generation
    print(f"\n2. GENERATION BREAKDOWN")
    print("-" * 40)
    
    # Test without confidence calculation
    import time
    
    # Mock the confidence calculation to see if that's the bottleneck
    original_calc_confidence = generator._calculate_confidence
    
    def fast_confidence(answer, citations, chunks):
        return 0.8  # Fixed confidence for timing test
    
    generator._calculate_confidence = fast_confidence
    
    with timer("Generation without confidence calculation"):
        result_fast = generator.generate(query, test_chunks)
    
    generator._calculate_confidence = original_calc_confidence
    
    print(f"Speedup without confidence calc: {avg_generation_time / (time.time() - start):.2f}x")
    
    return avg_generation_time


def profile_llm_calls():
    """Profile LLM call performance specifically."""
    print("\n\n🤖 PROFILING LLM PERFORMANCE")
    print("=" * 60)
    
    import ollama
    
    client = ollama.Client()
    
    # Test simple LLM call
    simple_prompt = "What is RISC-V? Answer in one sentence."
    
    print("\n1. SIMPLE LLM CALL")
    print("-" * 30)
    
    llm_times = []
    
    for i in range(3):
        start = time.time()
        try:
            response = client.chat(
                model="llama3.2:3b",
                messages=[
                    {"role": "user", "content": simple_prompt}
                ],
                options={"temperature": 0.3, "num_predict": 100},
                stream=False
            )
            elapsed = time.time() - start
            llm_times.append(elapsed)
            print(f"Run {i+1}: {elapsed:.3f}s")
        except Exception as e:
            print(f"❌ LLM call failed: {e}")
            return float('inf')
    
    avg_llm_time = statistics.mean(llm_times)
    print(f"Average LLM call time: {avg_llm_time:.3f}s")
    
    # Test with complex RAG prompt
    print(f"\n2. COMPLEX RAG PROMPT")
    print("-" * 30)
    
    complex_prompt = """Context:
[chunk_1] (Page 1 from riscv-spec.pdf):
RISC-V is an open-source instruction set architecture (ISA) based on reduced instruction set computer (RISC) principles.

Question: What is RISC-V?

INSTRUCTIONS:
1. Read the context carefully and determine if it contains relevant information to answer the question
2. If the context contains relevant information, answer the question using ONLY that information
3. You MUST cite every piece of information using [chunk_1], [chunk_2], etc. format
4. Example citation: "According to [chunk_1], RISC-V is an open-source architecture."

Answer the question now with proper [chunk_X] citations for every factual claim:"""
    
    start = time.time()
    try:
        response = client.chat(
            model="llama3.2:3b",
            messages=[
                {"role": "system", "content": "You are a technical documentation assistant that provides clear, accurate answers based on the provided context."},
                {"role": "user", "content": complex_prompt}
            ],
            options={"temperature": 0.3, "num_predict": 200},
            stream=False
        )
        complex_time = time.time() - start
        print(f"Complex RAG prompt time: {complex_time:.3f}s")
    except Exception as e:
        print(f"❌ Complex LLM call failed: {e}")
        complex_time = float('inf')
    
    return avg_llm_time, complex_time


def main():
    """Main profiling function."""
    print("🔍 RAG SYSTEM PERFORMANCE PROFILING")
    print("Target: <2s response time")
    print("=" * 60)
    
    # Profile complete pipeline
    avg_pipeline_time = profile_complete_pipeline()
    
    # Profile individual components
    avg_generation_time = profile_individual_components()
    
    # Profile LLM calls
    llm_simple, llm_complex = profile_llm_calls()
    
    # Analysis and recommendations
    print(f"\n\n📊 PERFORMANCE ANALYSIS")
    print("=" * 60)
    
    print(f"Complete pipeline: {avg_pipeline_time:.3f}s")
    print(f"Answer generation: {avg_generation_time:.3f}s")
    print(f"Simple LLM call: {llm_simple:.3f}s")
    print(f"Complex LLM call: {llm_complex:.3f}s")
    
    print(f"\n🎯 BOTTLENECK ANALYSIS")
    print("-" * 30)
    
    if llm_complex > 2.0:
        print("❌ Primary bottleneck: LLM inference time")
        print("💡 Recommendations:")
        print("   - Use smaller/faster model")
        print("   - Reduce max_tokens")
        print("   - Simplify prompts")
        print("   - Consider streaming responses")
    elif avg_generation_time > 1.0:
        print("❌ Primary bottleneck: Answer generation pipeline")
        print("💡 Recommendations:")
        print("   - Optimize confidence calculation")
        print("   - Reduce chunk processing")
        print("   - Cache embeddings")
    else:
        print("✅ System performance acceptable")
    
    print(f"\n📋 OPTIMIZATION PRIORITIES")
    print("-" * 30)
    
    components = [
        ("LLM inference", llm_complex),
        ("Answer generation", avg_generation_time),
        ("Complete pipeline", avg_pipeline_time)
    ]
    
    # Sort by time (highest first)
    components.sort(key=lambda x: x[1], reverse=True)
    
    for i, (component, time_taken) in enumerate(components, 1):
        status = "🔴" if time_taken > 2.0 else "🟡" if time_taken > 1.0 else "🟢"
        print(f"{i}. {status} {component}: {time_taken:.3f}s")


if __name__ == "__main__":
    main()