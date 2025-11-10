#!/usr/bin/env python3
"""
Fix import paths in test files that were moved to tests/epic1/validation/
"""

import os
from pathlib import Path

# Directory containing the moved test files
test_dir = Path("tests/epic1/validation")

# Pattern to find and replace
old_pattern = "project_root = Path(__file__).parent"
new_pattern = "project_root = Path(__file__).parent.parent.parent.parent"

# Process all test files
for test_file in test_dir.glob("test_epic1_*.py"):
    print(f"Processing {test_file}...")
    
    with open(test_file, 'r') as f:
        content = f.read()
    
    if old_pattern in content:
        content = content.replace(old_pattern, new_pattern)
        
        with open(test_file, 'w') as f:
            f.write(content)
        
        print(f"  Fixed import path in {test_file.name}")
    else:
        print(f"  No changes needed for {test_file.name}")

# Also fix scripts
script_dir = Path("tests/epic1/scripts")

for script_file in script_dir.glob("*.py"):
    print(f"Processing {script_file}...")
    
    with open(script_file, 'r') as f:
        content = f.read()
    
    if old_pattern in content:
        content = content.replace(old_pattern, new_pattern)
        
        with open(script_file, 'w') as f:
            f.write(content)
        
        print(f"  Fixed import path in {script_file.name}")
    else:
        print(f"  No changes needed for {script_file.name}")

print("\nImport path fixes complete!")