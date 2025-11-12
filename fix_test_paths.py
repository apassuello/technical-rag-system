#!/usr/bin/env python3
"""
Fix incorrect project_root paths in test files.

This script corrects the number of .parent calls based on the file's depth
in the directory tree.
"""

import re
from pathlib import Path
from typing import Dict, List, Tuple

# Files that need fixing (detected by systematic analysis)
FILES_TO_FIX = {
    # Need 3 parents, have 1
    "tests/integration_validation/run_comprehensive_validation.py": (1, 3),
    "tests/integration_validation/test_edge_cases_and_validation.py": (1, 3),
    "tests/integration_validation/test_factory_integration.py": (1, 3),
    "tests/integration_validation/test_legacy_compatibility.py": (1, 3),
    "tests/integration_validation/test_performance_benchmarks.py": (1, 3),
    "tests/integration_validation/test_test_runner_integration.py": (1, 3),
    "tests/integration_validation/validation_report_generator.py": (1, 3),

    # Need 4 parents, have 1
    "tests/epic1/integration/test_epic1_end_to_end.py": (1, 4),
    "tests/epic1/regression/test_epic1_accuracy_fixes.py": (1, 4),
    "tests/epic1/smoke/test_epic1_smoke.py": (1, 4),

    # Need 3 parents, have 2
    "tests/component/component_specific_tests.py": (2, 3),
    "tests/component/test_embeddings.py": (2, 3),
    "tests/component/test_modular_document_processor.py": (2, 3),
    "tests/component/test_pdf_parser.py": (2, 3),
    "tests/integration/comprehensive_integration_test.py": (2, 3),
    "tests/integration/test_integration.py": (2, 3),
    "tests/system/comprehensive_verification_test.py": (2, 3),
    "tests/tools/test_prompt_optimization.py": (2, 3),
    "tests/tools/test_prompt_simple.py": (2, 3),

    # Need 4 parents, have 3
    "tests/epic1/integration/test_epic1_modular_processor.py": (3, 4),

    # Need 3 parents, have 4
    "tests/architecture/test_component_interfaces.py": (4, 3),
}


def fix_project_root_path(file_path: str, current_parents: int, needed_parents: int) -> Tuple[bool, str]:
    """
    Fix the project_root path in a file.

    Args:
        file_path: Path to the file
        current_parents: Current number of .parent calls
        needed_parents: Needed number of .parent calls

    Returns:
        Tuple of (success, message)
    """
    path = Path(file_path)

    if not path.exists():
        return False, f"File not found: {file_path}"

    try:
        content = path.read_text()

        # Build the patterns
        current_pattern = r'project_root\s*=\s*Path\(__file__\)\.parent' + r'\.parent' * (current_parents - 1)
        needed_replacement = 'project_root = Path(__file__).parent' + '.parent' * (needed_parents - 1)

        # Check if pattern exists
        if not re.search(current_pattern, content):
            return False, f"Pattern not found in {file_path}"

        # Replace
        new_content = re.sub(current_pattern, needed_replacement, content)

        if new_content == content:
            return False, f"No changes made to {file_path}"

        # Write back
        path.write_text(new_content)
        return True, f"Fixed {file_path}: {current_parents} → {needed_parents} parents"

    except Exception as e:
        return False, f"Error processing {file_path}: {e}"


def main():
    """Fix all files with incorrect project_root paths."""
    print("=" * 80)
    print("Fix Test Import Paths")
    print("=" * 80)
    print(f"\nFound {len(FILES_TO_FIX)} files to fix\n")

    success_count = 0
    failure_count = 0
    failures: List[str] = []

    for file_path, (current, needed) in FILES_TO_FIX.items():
        success, message = fix_project_root_path(file_path, current, needed)

        if success:
            print(f"✅ {message}")
            success_count += 1
        else:
            print(f"❌ {message}")
            failure_count += 1
            failures.append(message)

    print("\n" + "=" * 80)
    print(f"Results: {success_count} fixed, {failure_count} failed")
    print("=" * 80)

    if failures:
        print("\nFailures:")
        for failure in failures:
            print(f"  - {failure}")

    return success_count, failure_count


if __name__ == "__main__":
    success, failures = main()
    exit(0 if failures == 0 else 1)
