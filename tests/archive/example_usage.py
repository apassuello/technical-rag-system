"""
Example: Using OpenAI Function Calling with Tool Registry

This example demonstrates how to use the enhanced OpenAIAdapter
with the tool registry for agentic RAG capabilities.

Key Features Demonstrated:
- Tool registration and schema generation
- Function calling with OpenAI
- Multi-turn conversations
- Error handling
- Cost tracking
"""

import os
import json
from typing import Dict, Any, List

# Component imports
from src.components.generators.llm_adapters.openai_adapter import OpenAIAdapter
from src.components.generators.base import GenerationParams
from src.components.query_processors.tools.tool_registry import ToolRegistry
from src.components.query_processors.tools.implementations.calculator_tool import CalculatorTool


def setup_tools() -> tuple[OpenAIAdapter, ToolRegistry, List[Dict[str, Any]]]:
    """
    Setup the adapter, registry, and tools.

    Returns:
        Tuple of (adapter, registry, tool_schemas)
    """
    # Create adapter
    adapter = OpenAIAdapter(
        model_name="gpt-3.5-turbo",
        api_key=os.getenv('OPENAI_API_KEY')
    )

    # Create and populate registry
    registry = ToolRegistry()

    # Register calculator tool
    calculator = CalculatorTool()
    registry.register(calculator)

    # Get OpenAI-compatible schemas
    tools = registry.get_openai_schemas()

    print(f"✓ Initialized adapter with {len(tools)} tool(s)")
    print(f"  Registered tools: {', '.join(registry.get_tool_names())}")
    print()

    return adapter, registry, tools


def execute_tool_calls(
    registry: ToolRegistry,
    pending_calls: List[Dict[str, Any]]
) -> List[Dict[str, str]]:
    """
    Execute pending tool calls via the registry.

    Args:
        registry: Tool registry
        pending_calls: List of tool calls from OpenAI

    Returns:
        List of function results ready for OpenAI
    """
    results = []

    for tool_call in pending_calls:
        # Extract call details
        call_id = tool_call['id']
        func_name = tool_call['function']['name']
        func_args = json.loads(tool_call['function']['arguments'])

        print(f"  Executing: {func_name}({func_args})")

        # Execute via registry
        exec_result = registry.execute_tool(func_name, **func_args)

        # Format for OpenAI
        if exec_result.success:
            content = str(exec_result.content)
            print(f"  → Result: {content}")
        else:
            content = f"Error: {exec_result.error}"
            print(f"  → Error: {exec_result.error}")

        results.append({
            'tool_call_id': call_id,
            'content': content
        })

    return results


def run_agentic_conversation(
    adapter: OpenAIAdapter,
    registry: ToolRegistry,
    tools: List[Dict[str, Any]],
    prompt: str,
    max_iterations: int = 5
) -> Dict[str, Any]:
    """
    Run a complete agentic conversation with function calling.

    Args:
        adapter: OpenAI adapter
        registry: Tool registry
        tools: Tool schemas
        prompt: User prompt
        max_iterations: Maximum iterations

    Returns:
        Final conversation result
    """
    print(f"User: {prompt}")
    print()

    # Initial request
    print("Making initial request to OpenAI...")
    result = adapter.generate_with_functions(
        prompt=prompt,
        tools=tools,
        params=GenerationParams(temperature=0.0),
        max_iterations=max_iterations
    )

    iteration = 1

    # Loop until completion
    while result['status'] == 'requires_function_execution' and iteration < max_iterations:
        print(f"\n--- Iteration {iteration} ---")
        print(f"Status: {result['status']}")
        print(f"Pending tool calls: {len(result['pending_tool_calls'])}")
        print()

        # Execute tools
        function_results = execute_tool_calls(registry, result['pending_tool_calls'])

        print()
        print("Continuing conversation with results...")

        # Continue conversation
        result = adapter.continue_with_function_results(
            messages=result['messages'],
            function_results=function_results,
            tools=tools,
            max_iterations=max_iterations - iteration
        )

        iteration += 1

    return result


def print_result_summary(result: Dict[str, Any]) -> None:
    """Print a formatted summary of the conversation result."""
    print("\n" + "=" * 70)
    print("CONVERSATION SUMMARY")
    print("=" * 70)

    print(f"Status: {result['status']}")
    print(f"Iterations: {result['iterations']}")
    print(f"Function calls made: {len(result.get('function_calls', []))}")
    print()

    if result.get('function_calls'):
        print("Functions called:")
        for fc in result['function_calls']:
            print(f"  - {fc['name']}({fc['arguments']})")
        print()

    if result.get('final_response'):
        print("Assistant Response:")
        print(f"  {result['final_response']}")
        print()

    print("Cost Tracking:")
    print(f"  Total tokens: {result.get('total_tokens', 0)}")
    print(f"  Total cost: ${result.get('total_cost_usd', 0):.6f}")
    print()

    if result.get('cost_breakdown'):
        print("Per-iteration breakdown:")
        for i, breakdown in enumerate(result['cost_breakdown'], 1):
            print(f"  Iteration {i}:")
            print(f"    - Tokens: {breakdown.get('total_tokens', 0)}")
            print(f"    - Cost: ${breakdown.get('total_cost_usd', 0):.6f}")
        print()


def example_1_simple_calculation() -> None:
    """Example 1: Simple calculation with single function call."""
    print("\n" + "=" * 70)
    print("EXAMPLE 1: Simple Calculation")
    print("=" * 70 + "\n")

    # Setup
    adapter, registry, tools = setup_tools()

    # Run conversation
    result = run_agentic_conversation(
        adapter=adapter,
        registry=registry,
        tools=tools,
        prompt="What is 25 multiplied by 47?"
    )

    # Print summary
    print_result_summary(result)


def example_2_multi_step() -> None:
    """Example 2: Multi-step calculation requiring multiple function calls."""
    print("\n" + "=" * 70)
    print("EXAMPLE 2: Multi-Step Calculation")
    print("=" * 70 + "\n")

    # Setup
    adapter, registry, tools = setup_tools()

    # Run conversation
    result = run_agentic_conversation(
        adapter=adapter,
        registry=registry,
        tools=tools,
        prompt="Calculate (15 + 25) * 2. Show your work step by step.",
        max_iterations=5
    )

    # Print summary
    print_result_summary(result)


def example_3_parallel_calls() -> None:
    """Example 3: Parallel function calls."""
    print("\n" + "=" * 70)
    print("EXAMPLE 3: Parallel Function Calls")
    print("=" * 70 + "\n")

    # Setup
    adapter, registry, tools = setup_tools()

    # Run conversation
    result = run_agentic_conversation(
        adapter=adapter,
        registry=registry,
        tools=tools,
        prompt="Calculate both 10+5 and 20*3. What are the results?",
        max_iterations=3
    )

    # Print summary
    print_result_summary(result)


def example_4_direct_answer() -> None:
    """Example 4: LLM answers directly without using tools."""
    print("\n" + "=" * 70)
    print("EXAMPLE 4: Direct Answer (No Tools)")
    print("=" * 70 + "\n")

    # Setup
    adapter, registry, tools = setup_tools()

    # Run conversation
    result = run_agentic_conversation(
        adapter=adapter,
        registry=registry,
        tools=tools,
        prompt="What is the capital of France?"
    )

    # Print summary
    print_result_summary(result)


def main() -> None:
    """Run all examples."""
    # Check for API key
    if not os.getenv('OPENAI_API_KEY'):
        print("ERROR: OPENAI_API_KEY environment variable not set")
        print("Please set it before running examples:")
        print("  export OPENAI_API_KEY='sk-...'")
        return

    print("\n" + "=" * 70)
    print("OpenAI Function Calling Examples")
    print("=" * 70)

    # Run examples
    try:
        example_1_simple_calculation()
        example_2_multi_step()
        example_3_parallel_calls()
        example_4_direct_answer()

        print("\n" + "=" * 70)
        print("All examples completed successfully!")
        print("=" * 70 + "\n")

    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    main()
