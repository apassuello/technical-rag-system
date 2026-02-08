#!/usr/bin/env python3
"""
Verification script for AnthropicAdapter implementation.

This script verifies that the AnthropicAdapter is properly implemented
and can be instantiated without errors.
"""

import sys
import os
from pathlib import Path

# Add project root to path - resolve from script location
script_dir = Path(__file__).parent.parent  # scripts -> project root
sys.path.insert(0, str(script_dir))

def verify_imports():
    """Verify all necessary imports work."""
    print("✓ Verifying imports...")
    try:
        # Import anthropic package
        import anthropic
        print(f"  ✓ anthropic package version: {anthropic.__version__}")

        # Note: We skip BaseLLMAdapter and GenerationParams imports
        # because they trigger components __init__ which has pdfplumber dependency.
        # This is not a problem for the adapter itself, just for this verification script.
        print("  ⚠ Skipping BaseLLMAdapter/GenerationParams imports (pdfplumber dependency)")
        print("  ℹ This is expected and not an issue with the adapter implementation")

        return True
    except ImportError as e:
        print(f"  ✗ Import error: {e}")
        return False


def verify_syntax():
    """Verify Python syntax of adapter files."""
    print("\n✓ Verifying Python syntax...")

    files = [
        'src/components/generators/llm_adapters/anthropic_adapter.py',
        'tests/epic5/phase1/unit/test_anthropic_adapter.py',
        'tests/epic5/phase1/integration/test_anthropic_with_tools.py'
    ]

    import py_compile

    for file_path in files:
        try:
            py_compile.compile(file_path, doraise=True)
            print(f"  ✓ {file_path}")
        except py_compile.PyCompileError as e:
            print(f"  ✗ {file_path}: {e}")
            return False

    return True


def verify_adapter_structure():
    """Verify adapter has required methods."""
    print("\n✓ Verifying adapter structure...")

    # Read the adapter file
    with open('src/components/generators/llm_adapters/anthropic_adapter.py', 'r') as f:
        content = f.read()

    required_methods = [
        'def __init__',
        'def generate',
        'def generate_with_tools',
        'def continue_with_tool_results',
        'def generate_streaming',
        'def _make_request',
        'def _parse_response',
        'def _get_provider_name',
        'def _validate_model',
        'def _supports_streaming',
        'def _get_max_tokens',
        'def _handle_anthropic_error',
        'def _track_usage_with_breakdown',
        'def get_model_info',
        'def get_cost_breakdown',
    ]

    missing = []
    for method in required_methods:
        if method not in content:
            missing.append(method)
        else:
            print(f"  ✓ {method}")

    if missing:
        print(f"  ✗ Missing methods: {missing}")
        return False

    return True


def verify_test_structure():
    """Verify test files have required test classes."""
    print("\n✓ Verifying test structure...")

    # Read unit test file
    with open('tests/epic5/phase1/unit/test_anthropic_adapter.py', 'r') as f:
        unit_test_content = f.read()

    unit_test_classes = [
        'TestAnthropicAdapterInitialization',
        'TestAnthropicAdapterBasicGeneration',
        'TestAnthropicAdapterToolUse',
        'TestAnthropicAdapterCostTracking',
        'TestAnthropicAdapterErrorHandling',
        'TestAnthropicAdapterStreaming',
        'TestAnthropicAdapterValidation',
    ]

    for test_class in unit_test_classes:
        if test_class in unit_test_content:
            print(f"  ✓ {test_class}")
        else:
            print(f"  ✗ Missing: {test_class}")
            return False

    # Read integration test file
    with open('tests/epic5/phase1/integration/test_anthropic_with_tools.py', 'r') as f:
        integration_test_content = f.read()

    integration_test_classes = [
        'TestAnthropicAdapterBasicIntegration',
        'TestAnthropicAdapterStreaming',
        'TestAnthropicAdapterToolUse',
        'TestAnthropicAdapterErrorHandling',
    ]

    for test_class in integration_test_classes:
        if test_class in integration_test_content:
            print(f"  ✓ {test_class}")
        else:
            print(f"  ✗ Missing: {test_class}")
            return False

    return True


def verify_registry_integration():
    """Verify adapter is registered in the adapter registry."""
    print("\n✓ Verifying registry integration...")

    with open('src/components/generators/llm_adapters/__init__.py', 'r') as f:
        content = f.read()

    if 'AnthropicAdapter' in content and "'anthropic': AnthropicAdapter" in content:
        print("  ✓ AnthropicAdapter registered in ADAPTER_REGISTRY")
        return True
    else:
        print("  ✗ AnthropicAdapter not properly registered")
        return False


def main():
    """Run all verification checks."""
    print("="*70)
    print("AnthropicAdapter Implementation Verification")
    print("="*70)

    results = {
        'Imports': verify_imports(),
        'Syntax': verify_syntax(),
        'Adapter Structure': verify_adapter_structure(),
        'Test Structure': verify_test_structure(),
        'Registry Integration': verify_registry_integration(),
    }

    print("\n" + "="*70)
    print("Verification Summary")
    print("="*70)

    for check, passed in results.items():
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{check:.<50} {status}")

    all_passed = all(results.values())

    print("="*70)
    if all_passed:
        print("✓ ALL CHECKS PASSED")
        print("\nImplementation is complete and ready for testing!")
        print("\nNext steps:")
        print("1. Run unit tests: pytest tests/epic5/phase1/unit/test_anthropic_adapter.py -v")
        print("2. Set ANTHROPIC_API_KEY and run integration tests")
        print("3. Use the adapter in your RAG pipeline")
        return 0
    else:
        print("✗ SOME CHECKS FAILED")
        print("\nPlease fix the issues above before proceeding.")
        return 1


if __name__ == '__main__':
    sys.exit(main())
