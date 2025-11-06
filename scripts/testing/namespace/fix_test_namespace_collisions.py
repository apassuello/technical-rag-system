#!/usr/bin/env python3
"""
Fix test namespace collisions by making test directories service-specific.
"""

import os
import shutil
import re
from pathlib import Path

def fix_test_imports_in_file(file_path: Path, old_conftest_import: str, new_conftest_import: str):
    """Fix conftest imports in a single test file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Update conftest imports
        if old_conftest_import in content:
            content = content.replace(old_conftest_import, new_conftest_import)
        
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
    except Exception as e:
        print(f"    ❌ Error updating {file_path}: {e}")
    return False

def fix_service_test_namespace(service_dir: Path, service_name: str):
    """Fix test namespace collision for a single service."""
    print(f"\n🔧 Fixing {service_name} test namespace...")
    
    tests_dir = service_dir / "tests"
    if not tests_dir.exists():
        print(f"  ⚠️ No tests directory found in {service_dir}")
        return
    
    # Find all conftest.py files and __init__.py files in tests
    conftest_files = list(tests_dir.rglob("conftest.py"))
    init_files = list(tests_dir.rglob("__init__.py"))
    
    print(f"  📁 Found {len(conftest_files)} conftest.py files and {len(init_files)} __init__.py files")
    
    # For pytest, we need to ensure each service's tests can be run independently
    # The main issue is that pytest creates a namespace collision when importing conftest modules
    # Solution: Make sure each service's conftest has unique imports
    
    # Update conftest.py to have service-specific imports
    for conftest_file in conftest_files:
        try:
            with open(conftest_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            
            # Update any app imports to use service-specific names
            service_app_name = {
                'generator': 'generator_app',
                'cache': 'cache_app', 
                'retriever': 'retriever_app',
                'query-analyzer': 'analyzer_app',
                'api-gateway': 'gateway_app',
                'analytics': 'analytics_app'
            }.get(service_name)
            
            if service_app_name:
                content = re.sub(r'\bfrom app\.', f'from {service_app_name}.', content)
                content = re.sub(r'\bimport app\.', f'import {service_app_name}.', content)
            
            if content != original_content:
                print(f"  📝 Updated {conftest_file.relative_to(service_dir)}")
                with open(conftest_file, 'w', encoding='utf-8') as f:
                    f.write(content)
                    
        except Exception as e:
            print(f"  ❌ Error updating {conftest_file}: {e}")
    
    print(f"  ✅ {service_name} test namespace fixed!")

def main():
    """Fix all Epic 8 test namespace collisions."""
    services_dir = Path("/Users/apa/ml_projects/rag-portfolio/project-1-technical-rag/services")
    
    services = [
        "generator", "cache", "retriever", "query-analyzer", "api-gateway", "analytics"
    ]
    
    print("🧪 Starting Epic 8 test namespace collision fixes...")
    
    for service_name in services:
        service_dir = services_dir / service_name
        if service_dir.exists():
            fix_service_test_namespace(service_dir, service_name)
    
    print("\n🎉 All test namespace collision fixes complete!")
    print("\nEach service's tests should now be able to run independently.")

if __name__ == "__main__":
    main()