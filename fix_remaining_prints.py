#!/usr/bin/env python3
"""
Script to replace all remaining print() statements with logging calls.
"""

import re
import os
from pathlib import Path

# Files to process (production code only - excluding tests and __main__ sections)
FILES_TO_PROCESS = [
    "src/shared_utils/document_processing/hybrid_parser.py",
    "src/shared_utils/document_processing/toc_guided_parser.py",
    "src/shared_utils/retrieval/hybrid_search.py",
    "src/shared_utils/metrics/__init__.py",
    "src/shared_utils/metrics/calibration_collector.py",
    "src/components/calibration/calibration_manager.py",
    "src/components/calibration/optimization_engine.py",
    "src/components/calibration/parameter_registry.py",
    "src/components/processors/pipeline.py",
    "src/evaluation/retrieval_evaluator.py",
    "src/training/data_loader.py",
    "src/training/epic1_training_orchestrator.py",
    "src/training/evaluation_framework.py",
    "src/training/view_trainer.py",
    "src/training/dataset_generation_framework.py",
    "demo/utils/initialization_profiler.py",
]

def categorize_print(line: str) -> str:
    """Determine the appropriate logger level for a print statement."""
    line_lower = line.lower()

    # Error indicators
    if any(word in line_lower for word in ["error", "failed", "exception", "❌"]):
        return "error"

    # Warning indicators
    if any(word in line_lower for word in ["warning", "⚠️", "warn"]):
        return "warning"

    # Debug indicators
    if any(word in line_lower for word in ["debug", "🔧", "diagnostic"]):
        return "debug"

    # Default to info
    return "info"

def has_logging_import(content: str) -> bool:
    """Check if file already has logging imported."""
    return re.search(r'^import logging$', content, re.MULTILINE) is not None

def has_logger_definition(content: str) -> bool:
    """Check if file already has logger defined."""
    return re.search(r'logger\s*=\s*logging\.getLogger', content) is not None

def add_logging_setup(content: str) -> str:
    """Add logging import and logger definition if not present."""
    lines = content.split('\n')

    # Find the last import line
    last_import_idx = 0
    for i, line in enumerate(lines):
        if line.startswith('import ') or line.startswith('from '):
            last_import_idx = i

    # Add logging import if not present
    if not has_logging_import(content):
        lines.insert(last_import_idx + 1, 'import logging')

    # Add logger definition if not present
    if not has_logger_definition(content):
        # Find first blank line after imports
        insert_idx = last_import_idx + 2
        while insert_idx < len(lines) and lines[insert_idx].strip():
            insert_idx += 1

        lines.insert(insert_idx + 1, 'logger = logging.getLogger(__name__)')
        lines.insert(insert_idx + 1, '')

    return '\n'.join(lines)

def replace_print_statements(content: str) -> str:
    """Replace print statements with appropriate logger calls."""
    lines = content.split('\n')
    modified = False

    for i, line in enumerate(lines):
        # Skip __main__ sections
        if '__main__' in line or (i > 0 and '__main__' in lines[i-1]):
            continue

        # Find print statements
        match = re.match(r'^(\s*)print\((.*)\)$', line)
        if match:
            indent = match.group(1)
            args = match.group(2)

            # Remove file=sys.stderr, flush=True parameters
            args = re.sub(r',\s*file\s*=\s*sys\.\w+', '', args)
            args = re.sub(r',\s*flush\s*=\s*\w+', '', args)
            args = args.strip()

            # Determine log level
            level = categorize_print(line)

            # Replace with logger call
            lines[i] = f"{indent}logger.{level}({args})"
            modified = True

    return '\n'.join(lines) if modified else content

def process_file(file_path: Path) -> bool:
    """Process a single file."""
    try:
        # Read file
        with open(file_path, 'r', encoding='utf-8') as f:
            original_content = f.read()

        # Add logging setup
        content = add_logging_setup(original_content)

        # Replace print statements
        content = replace_print_statements(content)

        # Only write if changed
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"✅ Fixed: {file_path}")
            return True
        else:
            print(f"⏭️  Skipped (no changes): {file_path}")
            return False
    except Exception as e:
        print(f"❌ Error processing {file_path}: {e}")
        return False

def main():
    """Main processing function."""
    project_root = Path(__file__).parent

    print("=" * 80)
    print("PRINT STATEMENT REPLACEMENT SCRIPT")
    print("=" * 80)
    print()

    fixed_count = 0
    skipped_count = 0
    error_count = 0

    for file_rel_path in FILES_TO_PROCESS:
        file_path = project_root / file_rel_path

        if not file_path.exists():
            print(f"⚠️  File not found: {file_path}")
            error_count += 1
            continue

        if process_file(file_path):
            fixed_count += 1
        else:
            skipped_count += 1

    print()
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Files fixed: {fixed_count}")
    print(f"Files skipped: {skipped_count}")
    print(f"Errors: {error_count}")
    print()
    print("✅ Print statement replacement complete!")

if __name__ == "__main__":
    main()
