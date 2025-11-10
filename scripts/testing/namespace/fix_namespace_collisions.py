#!/usr/bin/env python3
"""
Script to fix Epic 8 namespace collisions by renaming app directories to service-specific names.
"""

import os
import shutil
import re
from pathlib import Path

def fix_service_namespace(service_dir: Path, new_app_name: str):
    """Fix namespace collision for a single service."""
    print(f"\n🔧 Fixing {service_dir.name} service...")
    
    app_dir = service_dir / "app"
    new_app_dir = service_dir / new_app_name
    
    # 1. Rename app directory
    if app_dir.exists() and not new_app_dir.exists():
        print(f"  📁 Renaming {app_dir} -> {new_app_dir}")
        shutil.move(str(app_dir), str(new_app_dir))
    
    # 2. Find and update all files with app imports
    for py_file in service_dir.rglob("*.py"):
        if py_file.is_file():
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                original_content = content
                
                # Update imports: from app. -> from {new_app_name}.
                content = re.sub(r'\bfrom app\.', f'from {new_app_name}.', content)
                content = re.sub(r'\bimport app\.', f'import {new_app_name}.', content)
                
                # Update uvicorn app references: "app.main:app" -> "{new_app_name}.main:app"
                content = re.sub(r'"app\.main:app"', f'"{new_app_name}.main:app"', content)
                content = re.sub(r"'app\.main:app'", f"'{new_app_name}.main:app'", content)
                
                if content != original_content:
                    print(f"  📝 Updated {py_file.relative_to(service_dir)}")
                    with open(py_file, 'w', encoding='utf-8') as f:
                        f.write(content)
            
            except Exception as e:
                print(f"  ❌ Error updating {py_file}: {e}")
    
    # 3. Update Dockerfile
    dockerfile = service_dir / "Dockerfile"
    if dockerfile.exists():
        try:
            with open(dockerfile, 'r') as f:
                content = f.read()
            
            original_content = content
            
            # Update COPY commands
            content = re.sub(
                r'COPY --chown=appuser:appuser services/[^/]+/app/',
                f'COPY --chown=appuser:appuser services/{service_dir.name}/{new_app_name}/',
                content
            )
            
            # Update CMD uvicorn command
            content = re.sub(r'"app\.main:app"', f'"{new_app_name}.main:app"', content)
            
            if content != original_content:
                print(f"  🐳 Updated Dockerfile")
                with open(dockerfile, 'w') as f:
                    f.write(content)
        
        except Exception as e:
            print(f"  ❌ Error updating Dockerfile: {e}")
    
    print(f"  ✅ {service_dir.name} service namespace fixed!")

def main():
    """Main function to fix all Epic 8 service namespace collisions."""
    services_dir = Path("/Users/apa/ml_projects/rag-portfolio/project-1-technical-rag/services")
    
    services_to_fix = [
        ("retriever", "retriever_app"),
        ("query-analyzer", "analyzer_app"), 
        ("api-gateway", "gateway_app"),
        ("analytics", "analytics_app")
    ]
    
    print("🚀 Starting Epic 8 namespace collision fixes...")
    print(f"Services directory: {services_dir}")
    
    for service_name, new_app_name in services_to_fix:
        service_dir = services_dir / service_name
        if service_dir.exists():
            fix_service_namespace(service_dir, new_app_name)
        else:
            print(f"⚠️  Service directory not found: {service_dir}")
    
    print("\n🎉 All namespace collision fixes complete!")
    print("\nServices should now be able to run tests independently without namespace conflicts.")

if __name__ == "__main__":
    main()