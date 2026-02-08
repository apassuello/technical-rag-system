#!/usr/bin/env python3
"""
Quick script to verify all prompts have the correct simple structure.
"""

import re
from pathlib import Path

def check_prompt_file(file_path):
    """Check if a prompt file has the old complex structure."""
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Check for complex structure indicators
    has_complex_structure = False
    issues = []
    
    # Check for nested complexity_score (wrong)
    if '"complexity_score":' in content and '"feature_values":' in content:
        has_complex_structure = True
        issues.append("Found nested complexity_score with feature_values (old complex structure)")
    
    # Check for reasoning fields in examples (wrong)
    if '"reasoning":' in content:
        has_complex_structure = True
        issues.append("Found reasoning fields in JSON examples")
    
    # Count occurrences
    complex_count = content.count('"complexity_score":')
    feature_count = content.count('"feature_values":')
    reasoning_count = content.count('"reasoning":')
    
    return {
        "file": file_path.name,
        "has_complex_structure": has_complex_structure,
        "issues": issues,
        "counts": {
            "complexity_score": complex_count,
            "feature_values": feature_count,
            "reasoning": reasoning_count
        }
    }

def main():
    project_root = Path(__file__).resolve().parents[2]
    prompt_dir = project_root / "prompts" / "claude_training_generation"
    prompt_files = list(prompt_dir.glob("claude_prompt_*.md"))
    
    print("🔍 Checking prompt files for structure issues...")
    print("=" * 50)
    
    all_good = True
    for file_path in sorted(prompt_files):
        result = check_prompt_file(file_path)
        
        if result["has_complex_structure"]:
            all_good = False
            print(f"\n❌ {result['file']}")
            for issue in result["issues"]:
                print(f"   • {issue}")
            print(f"   Counts: {result['counts']}")
        else:
            print(f"✅ {result['file']} - Structure looks good")
    
    print("\n" + "=" * 50)
    if all_good:
        print("✅ All prompts have the correct simple structure!")
    else:
        print("⚠️  Some prompts still have the old complex structure in examples")
        print("   These need to be fixed to match the simple format:")
        print("   view_scores: { 'technical': 0.42, 'linguistic': 0.35, ... }")

if __name__ == "__main__":
    main()