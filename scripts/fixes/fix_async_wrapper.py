#!/usr/bin/env python3
"""
Fix async test methods by wrapping them with asyncio.run()
"""

import re

def fix_async_methods():
    file_path = 'tests/epic1/ml_infrastructure/integration/test_model_manager.py'
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Methods that need async wrapping (contain await calls)
    methods_to_fix = [
        'test_model_loading_timeout_handling',
        'test_concurrent_model_loading', 
        'test_memory_budget_enforcement',
        'test_automatic_quantization',
        'test_performance_tracking',
        'test_model_loading_failure_recovery'
    ]
    
    for method_name in methods_to_fix:
        # Find the method and wrap it
        pattern = rf'(    def {method_name}\(self\):\n        """[^"]*?"""\n)(.*?)(\n    def|\nclass|\n\nclass|\Z)'
        
        def wrap_method(match):
            method_signature = match.group(1)
            method_body = match.group(2)
            next_section = match.group(3) if match.group(3) else ''
            
            # Already processed if it has async def async_test
            if 'async def async_test():' in method_body:
                return match.group(0)
            
            # Indent method body for async function
            lines = method_body.split('\n')
            indented_lines = []
            for line in lines:
                if line.strip():  # Only indent non-empty lines
                    indented_lines.append('    ' + line)
                else:
                    indented_lines.append(line)
            
            indented_body = '\n'.join(indented_lines)
            
            # Create wrapped method
            new_method = method_signature
            new_method += '        async def async_test():\n'
            new_method += indented_body + '\n'
            new_method += '        \n'
            new_method += '        asyncio.run(async_test())'
            
            return new_method + next_section
        
        content = re.sub(pattern, wrap_method, content, flags=re.DOTALL)
    
    with open(file_path, 'w') as f:
        f.write(content)
    
    print(f"Fixed async methods in {file_path}")

if __name__ == '__main__':
    fix_async_methods()