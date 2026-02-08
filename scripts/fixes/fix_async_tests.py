#!/usr/bin/env python3
"""
Script to fix async test methods in ModelManager integration tests.
Converts async def test_... methods to sync methods that use asyncio.run().
"""

import re
import sys
from pathlib import Path

def fix_async_tests(file_path):
    """Fix async test methods in the given file."""
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Find all async test methods
    async_test_pattern = r'(@pytest\.mark\.asyncio\s+)?async def (test_\w+)\(self\):'
    
    def replace_async_method(match):
        decorator = match.group(1) if match.group(1) else ''
        method_name = match.group(2)
        
        # Remove the decorator and make method sync
        return f'def {method_name}(self):'
    
    # Replace async def with def and remove decorator
    content = re.sub(async_test_pattern, replace_async_method, content)
    
    # Now we need to find each method body and wrap it properly
    # This is more complex, so let's do it method by method
    
    # Find the specific methods we know need fixing
    async_methods = [
        'test_model_loading_with_caching',
        'test_model_loading_timeout_handling', 
        'test_concurrent_model_loading',
        'test_memory_budget_enforcement',
        'test_automatic_quantization',
        'test_performance_tracking',
        'test_model_loading_failure_recovery'
    ]
    
    for method_name in async_methods:
        # Pattern to find method definition and its body
        method_pattern = rf'(def {method_name}\(self\):.*?)(def \w+|\Z)'
        
        def wrap_method_body(match):
            method_def_and_body = match.group(1)
            next_method_or_end = match.group(2) if match.group(2) else ''
            
            # Split into method definition and body
            lines = method_def_and_body.split('\n')
            method_def = lines[0]
            docstring_line = lines[1] if len(lines) > 1 and '"""' in lines[1] else ''
            
            # Find where the actual method body starts (after docstring)
            body_start_idx = 2 if docstring_line else 1
            body_lines = lines[body_start_idx:]
            
            # Remove any trailing empty lines from body
            while body_lines and not body_lines[-1].strip():
                body_lines.pop()
            
            # Indent the body for the async function
            indented_body = []
            for line in body_lines:
                if line.strip():  # Only indent non-empty lines
                    indented_body.append('    ' + line)
                else:
                    indented_body.append(line)
            
            # Create the new method structure
            new_method = [method_def]
            if docstring_line:
                new_method.append(docstring_line)
            new_method.append('        async def async_test():')
            new_method.extend(indented_body)
            new_method.append('        ')
            new_method.append('        asyncio.run(async_test())')
            new_method.append('')
            
            return '\n'.join(new_method) + (next_method_or_end if next_method_or_end and next_method_or_end != '\Z' else '')
        
        content = re.sub(method_pattern, wrap_method_body, content, flags=re.DOTALL)
    
    # Write the fixed content back
    with open(file_path, 'w') as f:
        f.write(content)
    
    print(f"Fixed async test methods in {file_path}")

if __name__ == '__main__':
    project_root = Path(__file__).resolve().parents[2]
    file_path = str(project_root / 'tests/epic1/ml_infrastructure/integration/test_model_manager.py')
    fix_async_tests(file_path)