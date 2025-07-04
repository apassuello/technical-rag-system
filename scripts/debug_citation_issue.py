#!/usr/bin/env python3
"""
Debug the citation issue - examine raw model outputs.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from shared_utils.generation.answer_generator import AnswerGenerator


def debug_citation_generation():
    """Debug why citations aren't being generated properly."""
    print("🔍 DEBUGGING CITATION GENERATION")
    print("=" * 60)
    
    generator = AnswerGenerator()
    
    # Test with good, clear context
    chunks = [{
        "content": "RISC-V is an open-source instruction set architecture (ISA) based on reduced instruction set computer (RISC) principles. It was originally designed to support computer architecture research and education at UC Berkeley.",
        "metadata": {"page_number": 5, "source": "riscv-spec.pdf"},
        "score": 0.95,
        "id": "chunk_1"
    }]
    
    query = "What is RISC-V?"
    
    print(f"Query: {query}")
    print(f"Context provided:")
    for i, chunk in enumerate(chunks, 1):
        print(f"  [chunk_{i}]: {chunk['content'][:100]}...")
    
    # Generate answer and examine raw output
    result = generator.generate(query, chunks)
    
    print(f"\n📝 RAW MODEL OUTPUT:")
    print(f"Raw answer: '{result.answer}'")
    print(f"Citations extracted: {len(result.citations)}")
    print(f"Confidence: {result.confidence_score:.1%}")
    
    # Check if model output contains chunk references
    has_chunk_refs = "[chunk_" in result.answer
    print(f"Contains [chunk_X] references: {has_chunk_refs}")
    
    # Let's also examine the actual prompt sent to the model
    print(f"\n🔗 CONTEXT FORMATTING:")
    formatted_context = generator._format_context(chunks)
    print(f"Formatted context:\n{formatted_context}")
    
    # Let's check what happens with a very explicit instruction
    print(f"\n🎯 TESTING WITH EXPLICIT CITATION INSTRUCTION:")
    
    # Manual prompt to see if model follows citation instruction
    import ollama
    client = ollama.Client()
    
    explicit_prompt = f"""Context:
{formatted_context}

Question: {query}

You MUST cite every piece of information using [chunk_1], [chunk_2], etc. For example:
"According to [chunk_1], RISC-V is an open-source architecture."

Now answer the question with proper citations:"""
    
    try:
        response = client.chat(
            model="llama3.2:3b",
            messages=[
                {"role": "system", "content": generator._create_system_prompt()},
                {"role": "user", "content": explicit_prompt}
            ],
            stream=False
        )
        
        explicit_answer = response['message']['content']
        print(f"Explicit instruction answer: '{explicit_answer}'")
        
        has_citations_explicit = "[chunk_" in explicit_answer
        print(f"Contains citations with explicit instruction: {has_citations_explicit}")
        
        if not has_citations_explicit:
            print("\n❌ CRITICAL: Model is NOT following citation instructions even with explicit examples!")
        else:
            print("\n✅ Model CAN follow citation instructions when made explicit")
            
    except Exception as e:
        print(f"Error testing explicit instructions: {e}")


def test_system_prompt_effectiveness():
    """Test if the system prompt is actually being followed."""
    print(f"\n🧪 TESTING SYSTEM PROMPT EFFECTIVENESS")
    print("=" * 60)
    
    import ollama
    client = ollama.Client()
    
    # Test 1: Very simple context, direct question
    simple_context = "[chunk_1] (Page 1 from test.pdf):\nRISC-V has 32 registers."
    
    system_prompt = """You are a technical documentation assistant that provides answers STRICTLY based on the provided context. Your core principles:

CRITICAL REQUIREMENTS:
- You MUST ONLY use information explicitly stated in the provided context
- You MUST NOT use your pre-trained knowledge or assumptions
- If the context is insufficient, unclear, or contradictory, you MUST say so explicitly
- You MUST be skeptical of context that seems unusual or potentially fabricated

RESPONSE FORMAT:
1. Answer ONLY what can be directly supported by the provided context
2. Include specific citations using [chunk_X] notation for every factual claim
3. If information is missing or unclear in context, state: "The provided context does not contain sufficient information about [topic]"
4. If context seems questionable or contradictory, note: "The context contains conflicting/unclear information about [topic]"

FORBIDDEN BEHAVIORS:
- Do NOT answer from general knowledge when context is missing
- Do NOT make assumptions beyond what's explicitly stated
- Do NOT accept suspicious or contradictory information without questioning it
- Do NOT provide confident answers when context is insufficient

When context quality is poor or missing, explicitly state limitations rather than guessing."""
    
    user_prompt = f"""Context:
{simple_context}

Question: How many registers does RISC-V have?

IMPORTANT: You MUST cite using [chunk_1] notation. Example: "According to [chunk_1], RISC-V has X registers." """
    
    try:
        response = client.chat(
            model="llama3.2:3b",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            stream=False
        )
        
        answer = response['message']['content']
        print(f"Simple test answer: '{answer}'")
        
        contains_citation = "[chunk_1]" in answer
        contains_32 = "32" in answer
        
        print(f"Contains [chunk_1] citation: {contains_citation}")
        print(f"Contains '32' from context: {contains_32}")
        
        if contains_citation and contains_32:
            print("✅ Model follows instructions correctly")
        else:
            print("❌ Model is NOT following instructions properly")
            
    except Exception as e:
        print(f"Error in system prompt test: {e}")


def main():
    """Run citation debugging."""
    debug_citation_generation()
    test_system_prompt_effectiveness()
    
    print(f"\n📋 DIAGNOSIS:")
    print("1. Check if model outputs contain [chunk_X] references")
    print("2. Verify if system prompt is being followed")
    print("3. Determine if citation extraction is working")
    print("4. Identify why confidence is so low for good context")


if __name__ == "__main__":
    main()