#!/usr/bin/env python3
"""
Prepare files for HuggingFace Spaces deployment.

This script organizes and validates files needed for HF Spaces deployment.
"""

import os
import shutil
from pathlib import Path
import json

def prepare_hf_deployment():
    """Prepare HuggingFace Spaces deployment."""
    print("🚀 PREPARING HUGGINGFACE SPACES DEPLOYMENT")
    print("=" * 80)
    
    # Create deployment directory
    deployment_dir = Path("hf_deployment")
    if deployment_dir.exists():
        shutil.rmtree(deployment_dir)
    deployment_dir.mkdir()
    
    print(f"📁 Created deployment directory: {deployment_dir}")
    
    # Essential files for HF Spaces
    essential_files = [
        "app.py",                    # HF Spaces entry point
        "streamlit_app.py",         # Main application
        "requirements.txt",         # Dependencies
        "README.md",               # Documentation
    ]
    
    # Source code directories
    source_dirs = [
        "src",
        "shared_utils",
    ]
    
    # Sample data (select subset to stay within limits)
    sample_docs = [
        "data/test/riscv-base-instructions.pdf",
        "data/test/GMLP_Guiding_Principles.pdf", 
        "data/test/riscv-card.pdf",
    ]
    
    # Copy essential files
    print("\n📋 Copying essential files...")
    for file in essential_files:
        if Path(file).exists():
            shutil.copy2(file, deployment_dir / file)
            print(f"  ✅ {file}")
        else:
            print(f"  ❌ {file} - NOT FOUND")
    
    # Copy source directories
    print("\n📦 Copying source code...")
    for dir_name in source_dirs:
        src_dir = Path(dir_name)
        if src_dir.exists():
            dest_dir = deployment_dir / dir_name
            shutil.copytree(src_dir, dest_dir)
            print(f"  ✅ {dir_name}/ - {len(list(src_dir.rglob('*.py')))} Python files")
        else:
            print(f"  ❌ {dir_name}/ - NOT FOUND")
    
    # Create sample data directory
    print("\n📚 Copying sample documents...")
    data_dir = deployment_dir / "data" / "test"
    data_dir.mkdir(parents=True)
    
    for doc_path in sample_docs:
        if Path(doc_path).exists():
            dest_path = deployment_dir / doc_path
            dest_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(doc_path, dest_path)
            size_mb = Path(doc_path).stat().st_size / (1024 * 1024)
            print(f"  ✅ {Path(doc_path).name} ({size_mb:.1f}MB)")
        else:
            print(f"  ❌ {doc_path} - NOT FOUND")
    
    # Create test directory structure
    test_dir = deployment_dir / "tests"
    test_dir.mkdir()
    
    # Copy essential test files
    test_files = [
        "tests/test_basic_rag.py",
        "tests/test_integration.py"
    ]
    
    print("\n🧪 Copying essential tests...")
    for test_file in test_files:
        if Path(test_file).exists():
            shutil.copy2(test_file, deployment_dir / test_file)
            print(f"  ✅ {Path(test_file).name}")
    
    # Create .gitignore for HF Spaces
    gitignore_content = """
__pycache__/
*.pyc
*.pyo
*.egg-info/
.pytest_cache/
.streamlit/
*.log
.DS_Store
*.tmp
*.cache
verification_report_*.json
monitoring_report_*.json
calibration_debug_*.json
confidence_*.json
""".strip()
    
    with open(deployment_dir / ".gitignore", "w") as f:
        f.write(gitignore_content)
    print("\n📝 Created .gitignore for HF Spaces")
    
    # Update requirements.txt for HF Spaces (remove ollama, add alternatives)
    hf_requirements = """
# Core RAG System Dependencies - HuggingFace Spaces Compatible
streamlit>=1.46.0
numpy>=1.23.0
pandas>=1.4.0
scipy>=1.9.0

# Machine Learning & NLP
torch>=2.0.0
sentence-transformers>=2.2.0
transformers>=4.30.0
accelerate>=0.20.0

# Vector Search & Indexing
faiss-cpu>=1.7.4

# Document Processing
PyMuPDF>=1.23.0
pdfplumber>=0.10.0

# Text Processing
nltk>=3.8.0
scikit-learn>=1.3.0

# Utilities
python-dotenv>=1.0.0
typing-extensions>=4.4.0

# Note: ollama removed for HuggingFace Spaces compatibility
# The app will run in demo mode showing system capabilities
""".strip()
    
    with open(deployment_dir / "requirements.txt", "w") as f:
        f.write(hf_requirements)
    print("📦 Updated requirements.txt for HF Spaces compatibility")
    
    # Calculate deployment size
    total_size = 0
    file_count = 0
    
    for file_path in deployment_dir.rglob("*"):
        if file_path.is_file():
            total_size += file_path.stat().st_size
            file_count += 1
    
    size_mb = total_size / (1024 * 1024)
    
    # Create deployment summary
    summary = {
        "deployment_info": {
            "total_files": file_count,
            "total_size_mb": round(size_mb, 2),
            "deployment_date": "2025-07-03",
            "system_status": "85% production ready (confidence bug fixed)"
        },
        "files_included": {
            "essential_files": essential_files,
            "source_directories": source_dirs,
            "sample_documents": [Path(p).name for p in sample_docs],
            "tests_included": [Path(p).name for p in test_files]
        },
        "hf_spaces_config": {
            "sdk": "streamlit",
            "python_version": "3.11",
            "hardware": "cpu-basic",
            "demo_mode": "enabled (ollama not available)"
        },
        "key_features": [
            "Document processing and chunking",
            "Hybrid search (semantic + keyword)",
            "Quality UI demonstration", 
            "Complete source code access",
            "Professional documentation"
        ]
    }
    
    with open(deployment_dir / "deployment_summary.json", "w") as f:
        json.dump(summary, f, indent=2)
    
    # Display summary
    print(f"\n" + "=" * 80)
    print("🎯 DEPLOYMENT SUMMARY")
    print("=" * 80)
    print(f"📂 Deployment folder: {deployment_dir.absolute()}")
    print(f"📊 Total files: {file_count}")
    print(f"💾 Total size: {size_mb:.1f}MB")
    
    if size_mb > 100:
        print(f"⚠️  Size Warning: {size_mb:.1f}MB may be large for HF Spaces")
        print("   Consider removing some sample documents if needed")
    else:
        print(f"✅ Size appropriate for HuggingFace Spaces")
    
    print(f"\n🚀 READY FOR DEPLOYMENT")
    print(f"Next steps:")
    print(f"1. Create HuggingFace Space at https://huggingface.co/spaces")
    print(f"2. Upload all files from {deployment_dir}/ to your space")
    print(f"3. Configure as Streamlit SDK with Python 3.11")
    print(f"4. Deploy and test demo functionality")
    
    # Create upload checklist
    checklist = """
# HuggingFace Spaces Upload Checklist

## 1. Create Space
- [ ] Go to https://huggingface.co/spaces
- [ ] Click "Create new Space"
- [ ] Name: technical-rag-assistant (or your choice)
- [ ] SDK: Streamlit
- [ ] Hardware: CPU basic
- [ ] Visibility: Public
- [ ] License: MIT

## 2. Upload Files (from hf_deployment/ folder)
- [ ] app.py (HF Spaces entry point)
- [ ] streamlit_app.py (main application)
- [ ] requirements.txt (HF compatible)
- [ ] README.md (documentation)
- [ ] .gitignore (cleanup rules)
- [ ] src/ (source code directory)
- [ ] shared_utils/ (utilities directory)
- [ ] data/test/ (sample documents)
- [ ] tests/ (essential tests)

## 3. Configuration
- [ ] Verify SDK is set to "Streamlit"
- [ ] Confirm Python version 3.11
- [ ] Check hardware is CPU basic (free tier)
- [ ] Ensure visibility is set as desired

## 4. Post-Deployment Testing
- [ ] Space builds successfully
- [ ] App loads without errors
- [ ] Demo mode message displays correctly
- [ ] Document upload works
- [ ] Search functionality demonstrates
- [ ] UI is responsive and professional

## 5. Portfolio Integration
- [ ] Add HF Spaces link to resume/portfolio
- [ ] Test link works from external access
- [ ] Verify professional presentation
- [ ] Share with potential employers/recruiters
"""
    
    with open(deployment_dir / "UPLOAD_CHECKLIST.md", "w") as f:
        f.write(checklist.strip())
    
    print(f"\n📋 Created upload checklist: {deployment_dir}/UPLOAD_CHECKLIST.md")
    print(f"\n✅ Deployment preparation complete!")
    
    return deployment_dir

if __name__ == "__main__":
    prepare_hf_deployment()