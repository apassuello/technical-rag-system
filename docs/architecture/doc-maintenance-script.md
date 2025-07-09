# Documentation Maintenance Script Example

## scripts/check_doc_references.py

```python
#!/usr/bin/env python3
"""
Check that documentation references in code match actual documentation files.
Ensures architecture documentation stays in sync with implementation.
"""

import os
import re
from pathlib import Path
from typing import List, Tuple, Set

# Project root
PROJECT_ROOT = Path(__file__).parent.parent

# Documentation paths
ARCH_DOCS = PROJECT_ROOT / "docs" / "architecture"
SRC_ROOT = PROJECT_ROOT / "src"

# Pattern to find doc references in code
DOC_REF_PATTERN = re.compile(
    r'(?:Architecture Specification|Interface Reference|See):\s*([^\n]+\.md(?:#[\w-]+)?)'
)

def find_doc_references_in_code() -> List[Tuple[Path, str, str]]:
    """Find all documentation references in Python files."""
    references = []
    
    for py_file in SRC_ROOT.rglob("*.py"):
        with open(py_file, 'r') as f:
            content = f.read()
            
        # Find in docstrings
        for match in DOC_REF_PATTERN.finditer(content):
            doc_path = match.group(1).strip()
            references.append((py_file, doc_path, match.group(0)))
    
    return references

def verify_doc_exists(doc_ref: str) -> bool:
    """Check if referenced documentation file exists."""
    # Remove anchor if present
    doc_path = doc_ref.split('#')[0]
    
    # Try relative to different doc roots
    possible_paths = [
        PROJECT_ROOT / doc_path,
        PROJECT_ROOT / "docs" / doc_path,
        ARCH_DOCS / doc_path,
    ]
    
    return any(p.exists() for p in possible_paths)

def find_component_mapping() -> dict:
    """Map component classes to their documentation."""
    mapping = {
        'PlatformOrchestrator': 'components/COMPONENT-1-PLATFORM-ORCHESTRATOR.md',
        'DocumentProcessor': 'components/COMPONENT-2-DOCUMENT-PROCESSOR.md',
        'Embedder': 'components/COMPONENT-3-EMBEDDER.md',
        'Retriever': 'components/COMPONENT-4-RETRIEVER.md',
        'AnswerGenerator': 'components/COMPONENT-5-ANSWER-GENERATOR.md',
        'QueryProcessor': 'components/COMPONENT-6-QUERY-PROCESSOR.md',
    }
    return mapping

def check_component_docs():
    """Verify each component has proper documentation reference."""
    mapping = find_component_mapping()
    missing = []
    
    for class_name, expected_doc in mapping.items():
        # Find the class definition
        class_found = False
        for py_file in SRC_ROOT.rglob("*.py"):
            with open(py_file, 'r') as f:
                if f'class {class_name}' in f.read():
                    class_found = True
                    # Check if it references its documentation
                    f.seek(0)
                    content = f.read()
                    if expected_doc not in content:
                        missing.append((class_name, py_file, expected_doc))
        
        if not class_found:
            print(f"Warning: Class {class_name} not found in codebase")
    
    return missing

def main():
    """Run documentation reference checks."""
    print("🔍 Checking documentation references...\n")
    
    # Check 1: Verify all doc references in code exist
    print("1. Verifying documentation references in code:")
    references = find_doc_references_in_code()
    broken_refs = []
    
    for src_file, doc_ref, context in references:
        if not verify_doc_exists(doc_ref):
            broken_refs.append((src_file, doc_ref))
            print(f"   ❌ {src_file.relative_to(PROJECT_ROOT)}")
            print(f"      References: {doc_ref}")
            print(f"      Context: {context[:60]}...")
        else:
            print(f"   ✅ {src_file.relative_to(PROJECT_ROOT)} -> {doc_ref}")
    
    # Check 2: Verify component documentation
    print("\n2. Checking component documentation references:")
    missing_refs = check_component_docs()
    
    for class_name, src_file, expected_doc in missing_refs:
        print(f"   ⚠️  {class_name} in {src_file.relative_to(PROJECT_ROOT)}")
        print(f"      Should reference: {expected_doc}")
    
    # Check 3: Cross-references between docs
    print("\n3. Checking cross-references between documents:")
    for md_file in ARCH_DOCS.rglob("*.md"):
        with open(md_file, 'r') as f:
            content = f.read()
        
        # Find markdown links
        link_pattern = re.compile(r'\[([^\]]+)\]\(([^)]+\.md[^)]*)\)')
        for match in link_pattern.finditer(content):
            link_text, link_path = match.groups()
            
            # Resolve relative paths
            if link_path.startswith('./'):
                full_path = md_file.parent / link_path[2:]
            elif link_path.startswith('../'):
                full_path = md_file.parent / link_path
            else:
                full_path = ARCH_DOCS / link_path
            
            # Check if exists (ignore anchors)
            check_path = str(full_path).split('#')[0]
            if not Path(check_path).exists():
                print(f"   ❌ {md_file.relative_to(PROJECT_ROOT)}")
                print(f"      Broken link: [{link_text}]({link_path})")
    
    # Summary
    print("\n📊 Summary:")
    print(f"   Total references found: {len(references)}")
    print(f"   Broken references: {len(broken_refs)}")
    print(f"   Missing component docs: {len(missing_refs)}")
    
    if broken_refs or missing_refs:
        print("\n❌ Documentation issues found!")
        return 1
    else:
        print("\n✅ All documentation references are valid!")
        return 0

if __name__ == "__main__":
    exit(main())
```

## scripts/generate_doc_stubs.py

```python
#!/usr/bin/env python3
"""
Generate documentation stubs for components missing documentation.
"""

import os
from pathlib import Path
from datetime import datetime

def generate_component_doc_stub(component_name: str, component_id: int) -> str:
    """Generate a documentation stub for a component."""
    
    template = f"""# Component {component_id}: {component_name}

**Component ID**: C{component_id}  
**Version**: 1.0  
**References**: [MASTER-ARCHITECTURE.md](./MASTER-ARCHITECTURE.md)  
**Related Components**: TODO

---

## 1. Component Overview

### 1.1 Purpose & Responsibility

TODO: Describe the component's main purpose and responsibilities.

### 1.2 Position in System

TODO: Describe where this component fits in the overall system.

### 1.3 Key Design Decisions

TODO: List key architectural decisions for this component.

---

## 2. Requirements

### 2.1 Functional Requirements

TODO: List functional requirements.

### 2.2 Quality Requirements

TODO: List quality requirements (performance, reliability, scalability, security).

---

[Continue with remaining sections from template...]
"""
    
    return template

def update_code_with_doc_reference(file_path: Path, class_name: str, doc_path: str):
    """Add documentation reference to a Python class."""
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Find the class definition
    import_section_end = content.rfind('import')
    if import_section_end != -1:
        # Find the end of imports
        import_end_line = content.find('\n\n', import_section_end)
        if import_end_line != -1:
            # Insert documentation reference after imports
            doc_ref = f'''
"""
{class_name} - Component Documentation

Architecture Specification: {doc_path}
Interface Reference: docs/architecture/diagrams/rag-interface-reference.md#{class_name.lower()}
"""

'''
            new_content = (
                content[:import_end_line + 2] + 
                doc_ref + 
                content[import_end_line + 2:]
            )
            
            with open(file_path, 'w') as f:
                f.write(new_content)
            
            print(f"✅ Added documentation reference to {file_path}")

if __name__ == "__main__":
    # Example usage
    print("📝 Documentation Stub Generator")
    print("This would generate missing documentation stubs")
    print("and update code files with proper references.")
```

## Integration Checklist

```markdown
# Architecture Documentation Integration Checklist

## Phase 1: Setup Structure
- [ ] Create `docs/architecture/` directory
- [ ] Create `docs/architecture/components/` directory  
- [ ] Create `docs/architecture/diagrams/` directory
- [ ] Copy architecture documents to appropriate locations
- [ ] Create `docs/architecture/README.md` navigation file

## Phase 2: Code Integration
- [ ] Add documentation references to component classes
- [ ] Update configuration files with doc links
- [ ] Add references to test files
- [ ] Update module docstrings

## Phase 3: Automation
- [ ] Add `scripts/check_doc_references.py`
- [ ] Add `scripts/generate_doc_stubs.py`
- [ ] Update Makefile with doc commands
- [ ] Add CI/CD documentation checks

## Phase 4: Team Adoption
- [ ] Update main README.md
- [ ] Create onboarding guide
- [ ] Set up review process
- [ ] Train team on structure

## Phase 5: Maintenance
- [ ] Schedule regular doc reviews
- [ ] Set up automated checks
- [ ] Create update procedures
- [ ] Monitor doc freshness
```