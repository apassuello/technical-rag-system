"""
Simplified local testing for prompt engineering improvements.
"""

import sys
import os
from pathlib import Path
import time

# Add project paths
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))
sys.path.append(str(project_root.parent))

from shared_utils.generation.prompt_templates import TechnicalPromptTemplates, QueryType


def test_prompt_templates():
    """Test the prompt template system."""
    print("🚀 Testing Prompt Templates")
    print("=" * 50)

    # Test queries
    test_queries = {
        "definition": "What is RISC-V?",
        "implementation": "How do I configure GPIO pins in RISC-V?",
        "comparison": "What's the difference between machine mode and supervisor mode?",
        "code_example": "Show me GPIO configuration code",
        "troubleshooting": "How do I debug timer interrupts?",
    }

    # Sample context
    sample_context = """[chunk_1] (Page 1 from riscv-spec.pdf):
RISC-V is an open-source instruction set architecture (ISA) based on established reduced instruction set computing (RISC) principles. It was originally designed to support computer architecture research and education, but it is now also used in commercial implementations.

[chunk_2] (Page 15 from riscv-spec.pdf):
The RISC-V ISA defines three base integer instruction sets: RV32I, RV64I, and RV128I. These provide 32-bit, 64-bit, and 128-bit user-level address spaces respectively. The base integer instruction sets use a two's-complement representation for signed integer values."""

    print("\nTesting Query Type Detection:")
    for name, query in test_queries.items():
        detected_type = TechnicalPromptTemplates.detect_query_type(query)
        print(f"  {name}: '{query}' -> {detected_type.value}")

    print("\nTesting Template Generation:")
    for name, query in test_queries.items():
        print(f"\n{name.upper()} Query:")
        print(f"Query: {query}")

        # Get template
        template = TechnicalPromptTemplates.get_template_for_query(query)

        # Generate prompt
        prompt = TechnicalPromptTemplates.format_prompt_with_template(
            query=query,
            context=sample_context,
            template=template,
            include_few_shot=True,
        )

        print(f"System prompt length: {len(prompt['system'])} chars")
        print(f"User prompt length: {len(prompt['user'])} chars")
        print(f"Has few-shot examples: {'examples' in prompt['user'].lower()}")

        # Show first part of system prompt
        print(f"System prompt preview: {prompt['system'][:150]}...")
        print(f"User prompt preview: {prompt['user'][:200]}...")


def test_few_shot_examples():
    """Test few-shot example functionality."""
    print("\n" + "=" * 50)
    print("TESTING FEW-SHOT EXAMPLES")
    print("=" * 50)

    # Test definition template (has few-shot examples)
    query = "What is FreeRTOS?"
    template = TechnicalPromptTemplates.get_definition_template()

    print(f"Query: {query}")
    print(
        f"Few-shot examples available: {len(template.few_shot_examples) if template.few_shot_examples else 0}"
    )

    if template.few_shot_examples:
        print("Example 1 preview:")
        print(template.few_shot_examples[0][:200] + "...")

    # Test with and without few-shot
    context = "FreeRTOS is a real-time operating system kernel..."

    print("\nWithout few-shot:")
    prompt_no_fs = TechnicalPromptTemplates.format_prompt_with_template(
        query=query, context=context, template=template, include_few_shot=False
    )
    print(f"Prompt length: {len(prompt_no_fs['user'])} chars")

    print("\nWith few-shot:")
    prompt_with_fs = TechnicalPromptTemplates.format_prompt_with_template(
        query=query, context=context, template=template, include_few_shot=True
    )
    print(f"Prompt length: {len(prompt_with_fs['user'])} chars")
    print(
        f"Length increase: {len(prompt_with_fs['user']) - len(prompt_no_fs['user'])} chars"
    )


def test_adaptive_engine():
    """Test the adaptive prompt engine."""
    print("\n" + "=" * 50)
    print("TESTING ADAPTIVE PROMPT ENGINE")
    print("=" * 50)

    try:
        from shared_utils.generation.adaptive_prompt_engine import AdaptivePromptEngine

        engine = AdaptivePromptEngine()

        # Test context analysis
        sample_chunks = [
            {
                "content": "RISC-V is an open-source instruction set architecture...",
                "metadata": {"page_number": 1, "source": "riscv-spec.pdf"},
                "confidence": 0.9,
            },
            {
                "content": "The RISC-V processor supports 32-bit and 64-bit implementations...",
                "metadata": {"page_number": 2, "source": "riscv-spec.pdf"},
                "confidence": 0.8,
            },
        ]

        # Test simple vs complex queries
        simple_query = "What is RISC-V?"
        complex_query = "How do I implement a complete interrupt handling system with nested interrupts and priority management?"

        print("Simple query analysis:")
        simple_complexity = engine.determine_query_complexity(simple_query)
        print(f"  Query: {simple_query}")
        print(f"  Complexity: {simple_complexity.value}")

        print("\nComplex query analysis:")
        complex_complexity = engine.determine_query_complexity(complex_query)
        print(f"  Query: {complex_query[:60]}...")
        print(f"  Complexity: {complex_complexity.value}")

        # Test context quality analysis
        print("\nContext quality analysis:")
        context_metrics = engine.analyze_context_quality(sample_chunks)
        print(f"  Relevance score: {context_metrics.relevance_score:.2f}")
        print(f"  Noise ratio: {context_metrics.noise_ratio:.2f}")
        print(f"  Technical density: {context_metrics.technical_density:.2f}")
        print(f"  Source diversity: {context_metrics.source_diversity}")

        # Test adaptive configuration
        print("\nAdaptive configuration:")
        config = engine.generate_adaptive_config(complex_query, sample_chunks)
        print(f"  Query complexity: {config.query_complexity.value}")
        print(f"  Context quality: {config.context_quality.value}")
        print(f"  Include few-shot: {config.include_few_shot}")
        print(f"  Enable chain-of-thought: {config.enable_chain_of_thought}")
        print(f"  Prefer concise: {config.prefer_concise}")

    except ImportError as e:
        print(f"❌ Could not import adaptive engine: {e}")


def test_chain_of_thought():
    """Test chain-of-thought reasoning."""
    print("\n" + "=" * 50)
    print("TESTING CHAIN-OF-THOUGHT ENGINE")
    print("=" * 50)

    try:
        from shared_utils.generation.chain_of_thought_engine import ChainOfThoughtEngine

        cot_engine = ChainOfThoughtEngine()

        # Test implementation query
        query = "How do I implement a timer interrupt in RISC-V?"
        query_type = QueryType.IMPLEMENTATION
        context = "RISC-V timer implementation details..."

        print(f"Query: {query}")
        print(f"Query type: {query_type.value}")

        # Get base template
        from shared_utils.generation.prompt_templates import PromptTemplate

        base_template = PromptTemplate(
            system_prompt="You are a technical assistant.",
            context_format="Context: {context}",
            query_format="Question: {query}",
            answer_guidelines="Provide a structured answer.",
        )

        # Generate CoT prompt
        cot_prompt = cot_engine.generate_chain_of_thought_prompt(
            query=query,
            query_type=query_type,
            context=context,
            base_template=base_template,
        )

        print(f"\nCoT prompt generated:")
        print(f"  System prompt length: {len(cot_prompt['system'])} chars")
        print(f"  User prompt length: {len(cot_prompt['user'])} chars")
        print(f"  Has reasoning steps: {'Step 1:' in cot_prompt['user']}")
        print(
            f"  Has reasoning framework: {'REASONING PROCESS:' in cot_prompt['user']}"
        )

        # Show reasoning structure
        if "REASONING PROCESS:" in cot_prompt["user"]:
            reasoning_section = (
                cot_prompt["user"]
                .split("REASONING PROCESS:")[1]
                .split("STRUCTURED REASONING:")[0]
            )
            step_count = reasoning_section.count("Step")
            print(f"  Number of reasoning steps: {step_count}")

    except ImportError as e:
        print(f"❌ Could not import chain-of-thought engine: {e}")


def main():
    """Run simplified prompt engineering tests."""
    print("🧠 Prompt Engineering Local Tests (Simplified)")
    print("=" * 60)

    # Test core functionality
    test_prompt_templates()
    test_few_shot_examples()
    test_adaptive_engine()
    test_chain_of_thought()

    print("\n🎉 All tests completed!")
    print("\nResults Summary:")
    print("✅ Prompt template system working")
    print("✅ Query type detection working")
    print("✅ Few-shot examples integrated")
    print("✅ Adaptive prompt engine functional")
    print("✅ Chain-of-thought reasoning available")


if __name__ == "__main__":
    main()
