#!/usr/bin/env python3
"""
Debug the number removal issue step by step.
"""

import sys
from pathlib import Path
import re

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from shared_utils.generation.answer_generator import AnswerGenerator


def test_regex_patterns():
    """Test what the regex patterns are actually matching and removing."""
    print("🔍 TESTING REGEX PATTERNS")
    print("=" * 60)
    
    # The patterns from the code
    citation_patterns = [
        r'\[chunk_(\d+)\]',  # [chunk_1] format
        r'\s(\d+)\s',        # Standalone numbers (like  1 )
    ]
    
    # Test strings with different number contexts
    test_strings = [
        "RISC-V has 32 registers according to the specification.",
        "RV32E has 16 general-purpose registers.",
        "The instruction is 32-bit wide.",
        "According to [chunk_1], RISC-V is an architecture.",
        "According to  1 , the system has  32  registers.",
        "Page 25 shows that there are 64 possible values.",
        "The range is from 0 to 255 inclusive."
    ]
    
    for test_string in test_strings:
        print(f"\nOriginal: '{test_string}'")
        
        # Test each pattern
        for i, pattern in enumerate(citation_patterns, 1):
            matches = list(re.finditer(pattern, test_string))
            print(f"  Pattern {i} ('{pattern}') matches:")
            if matches:
                for match in matches:
                    print(f"    - '{match.group()}' at positions {match.span()}")
            else:
                print(f"    - No matches")
            
            # Show what gets removed
            cleaned = re.sub(pattern, '', test_string)
            if cleaned != test_string:
                print(f"    - After removal: '{cleaned}'")
                print(f"    - 🚨 CONTENT CHANGED!")
            else:
                print(f"    - No change")


def test_step_by_step_processing():
    """Test the step-by-step processing in the answer generator."""
    print(f"\n" + "=" * 60)
    print("🔬 STEP-BY-STEP PROCESSING TEST")
    print("=" * 60)
    
    generator = AnswerGenerator()
    
    # Create a test with clear numerical content
    chunks = [{
        "content": "RV32E has exactly 16 general-purpose registers, which is half of the 32 registers in standard RISC-V.",
        "metadata": {"page_number": 25, "source": "riscv-spec.pdf"},
        "score": 0.95,
        "id": "chunk_1"
    }]
    
    query = "How many registers does RV32E have?"
    
    print(f"Query: {query}")
    print(f"Context: {chunks[0]['content']}")
    
    # Let's manually step through the process
    print(f"\n1️⃣ FORMATTING CONTEXT:")
    formatted_context = generator._format_context(chunks)
    print(f"Formatted context:\n{formatted_context}")
    
    print(f"\n2️⃣ GENERATING ANSWER:")
    # Let's call the model directly to see raw output
    import ollama
    client = ollama.Client()
    
    user_prompt = f"""Context:
{formatted_context}

Question: {query}

INSTRUCTIONS:
1. Read the context carefully and determine if it contains relevant information to answer the question
2. If the context contains relevant information, answer the question using ONLY that information
3. You MUST cite every piece of information using [chunk_1], [chunk_2], etc. format
4. Example citation: "According to [chunk_1], RISC-V is an open-source architecture."
5. If context is insufficient, state clearly what information is missing

Answer the question now with proper [chunk_X] citations for every factual claim:"""
    
    try:
        response = client.chat(
            model="llama3.2:3b",
            messages=[
                {"role": "system", "content": generator._create_system_prompt()},
                {"role": "user", "content": user_prompt}
            ],
            stream=False
        )
        
        raw_answer = response['message']['content']
        print(f"Raw model output: '{raw_answer}'")
        
        print(f"\n3️⃣ CITATION EXTRACTION:")
        clean_answer, citations = generator._extract_citations(raw_answer, chunks)
        print(f"After citation extraction: '{clean_answer}'")
        print(f"Citations found: {len(citations)}")
        
        # Let's manually test the citation patterns
        print(f"\n4️⃣ TESTING CITATION PATTERNS ON RAW OUTPUT:")
        citation_patterns = [
            r'\[chunk_(\d+)\]',  # [chunk_1] format
            r'\s(\d+)\s',        # Standalone numbers (like  1 )
        ]
        
        for i, pattern in enumerate(citation_patterns, 1):
            matches = list(re.finditer(pattern, raw_answer))
            print(f"  Pattern {i} ('{pattern}'):")
            if matches:
                for match in matches:
                    print(f"    Found: '{match.group()}' capturing '{match.group(1)}'")
            else:
                print(f"    No matches")
            
            # Show the cleaning effect
            test_clean = re.sub(pattern, '', raw_answer)
            if test_clean != raw_answer:
                print(f"    Cleaning effect:")
                print(f"      Before: '{raw_answer}'")
                print(f"      After:  '{test_clean}'")
                
                # Check for number removal
                if any(char.isdigit() for char in raw_answer) and not any(char.isdigit() for char in test_clean):
                    print(f"    🚨 NUMBERS COMPLETELY REMOVED!")
                elif raw_answer.count('16') > test_clean.count('16') or raw_answer.count('32') > test_clean.count('32'):
                    print(f"    🚨 SPECIFIC NUMBERS REMOVED!")
        
        print(f"\n5️⃣ FINAL RESULT:")
        confidence = generator._calculate_confidence(clean_answer, citations, chunks)
        print(f"Final answer: '{clean_answer}'")
        print(f"Final confidence: {confidence:.1%}")
        
        # Check if numbers are preserved
        original_numbers = re.findall(r'\d+', chunks[0]['content'])
        final_numbers = re.findall(r'\d+', clean_answer)
        print(f"Numbers in original context: {original_numbers}")
        print(f"Numbers in final answer: {final_numbers}")
        
        if set(original_numbers) - set(final_numbers):
            print(f"🚨 MISSING NUMBERS: {set(original_numbers) - set(final_numbers)}")
        else:
            print(f"✅ All numbers preserved")
            
    except Exception as e:
        print(f"Error in processing: {e}")


def test_isolated_citation_cleaning():
    """Test citation cleaning in isolation."""
    print(f"\n" + "=" * 60)
    print("🧪 ISOLATED CITATION CLEANING TEST")
    print("=" * 60)
    
    # Test various answer formats
    test_answers = [
        "According to [chunk_1], RV32E has 16 registers.",
        "RV32E has 16 registers according to  1 .",
        "The system has  32  registers as stated in  2 .",
        "RISC-V uses 32-bit instructions and has 16 or 32 registers.",
        "According to chunk 1, there are 64 possible values from 0 to 255."
    ]
    
    citation_patterns = [
        r'\[chunk_(\d+)\]',  # [chunk_1] format
        r'\s(\d+)\s',        # Standalone numbers (like  1 )
    ]
    
    for test_answer in test_answers:
        print(f"\nTesting: '{test_answer}'")
        
        result = test_answer
        for pattern in citation_patterns:
            result = re.sub(pattern, '', result)
        
        print(f"Result:  '{result}'")
        
        # Check for problematic removals
        original_tech_numbers = re.findall(r'\b(?:16|32|64|255|0)\b', test_answer)
        final_tech_numbers = re.findall(r'\b(?:16|32|64|255|0)\b', result)
        
        if len(original_tech_numbers) > len(final_tech_numbers):
            print(f"🚨 TECHNICAL NUMBERS REMOVED: {set(original_tech_numbers) - set(final_tech_numbers)}")
        else:
            print(f"✅ Technical numbers preserved")


def main():
    """Run all debugging tests."""
    test_regex_patterns()
    test_step_by_step_processing()
    test_isolated_citation_cleaning()
    
    print(f"\n" + "=" * 60)
    print("💡 DEBUGGING SUMMARY")
    print("=" * 60)
    print("1. Check which regex patterns are matching what content")
    print("2. Identify exactly where numbers are being removed")
    print("3. Understand the difference between citation numbers and content numbers")
    print("4. Determine the fix needed for citation cleaning")


if __name__ == "__main__":
    main()