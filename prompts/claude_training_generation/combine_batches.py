#!/usr/bin/env python3
"""
Combine multiple Claude-generated batches into final training dataset.
Can work with individual files or automatically find all valid JSON files in a directory.

Usage:
    python combine_batches.py                    # Use current directory
    python combine_batches.py <directory>        # Use specific directory
    python combine_batches.py file1.json file2.json ...  # Specific files
"""

import json
import random
import statistics
import sys
from pathlib import Path
from typing import List, Dict, Any, Union
from datetime import datetime

def is_training_dataset(data: Any) -> bool:
    """Check if data looks like a training dataset."""
    if not isinstance(data, list):
        return False
    
    if len(data) == 0:
        return False
    
    # Check first sample for expected structure
    sample = data[0]
    if not isinstance(sample, dict):
        return False
    
    required_fields = ["query_text", "expected_complexity_score", "expected_complexity_level", "view_scores"]
    return all(field in sample for field in required_fields)

def load_batch(file_path: Union[str, Path]) -> List[Dict[str, Any]]:
    """Load a single batch file."""
    file_path = Path(file_path)
    
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        # Handle wrapped dataset format (with metadata)
        if isinstance(data, dict) and "samples" in data:
            data = data["samples"]
        
        # Check if it's a valid training dataset
        if not is_training_dataset(data):
            print(f"⚠️  Skipping {file_path.name}: Not a valid training dataset")
            return []
            
        print(f"✅ Loaded {len(data)} samples from {file_path.name}")
        return data
    except json.JSONDecodeError:
        print(f"⚠️  Skipping {file_path.name}: Invalid JSON")
        return []
    except Exception as e:
        print(f"❌ Error loading {file_path.name}: {e}")
        return []

def find_training_files(directory: Path) -> List[Path]:
    """Find all valid training JSON files in a directory."""
    json_files = list(directory.glob("*.json"))
    valid_files = []
    
    for json_file in sorted(json_files):
        try:
            with open(json_file, 'r') as f:
                data = json.load(f)
            
            # Handle wrapped format
            if isinstance(data, dict) and "samples" in data:
                data = data["samples"]
            
            if is_training_dataset(data):
                valid_files.append(json_file)
        except:
            continue  # Skip invalid files silently
    
    return valid_files

def analyze_dataset(data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze the combined dataset."""
    scores = [sample.get("expected_complexity_score", 0) for sample in data]
    levels = [sample.get("expected_complexity_level", "unknown") for sample in data]
    
    level_counts = {}
    for level in levels:
        level_counts[level] = level_counts.get(level, 0) + 1
    
    analysis = {
        "total_samples": len(data),
        "score_stats": {
            "mean": round(statistics.mean(scores), 3) if scores else 0,
            "min": round(min(scores), 3) if scores else 0,
            "max": round(max(scores), 3) if scores else 0,
            "std": round(statistics.stdev(scores), 3) if len(scores) > 1 else 0
        },
        "complexity_distribution": level_counts,
        "score_ranges": {
            "simple_range": [s for s in scores if s <= 0.35],
            "medium_range": [s for s in scores if 0.35 < s <= 0.66], 
            "complex_range": [s for s in scores if s > 0.66]
        }
    }
    
    return analysis

def validate_final_dataset(data: List[Dict[str, Any]]) -> List[str]:
    """Validate the final combined dataset."""
    issues = []
    
    # Check total count
    if len(data) != 100:
        issues.append(f"Expected 100 samples, got {len(data)}")
    
    # Check distribution
    levels = [sample.get("expected_complexity_level", "unknown") for sample in data]
    level_counts = {}
    for level in levels:
        level_counts[level] = level_counts.get(level, 0) + 1
    
    # Expected: ~25% simple, ~50% medium, ~25% complex
    total = len(data)
    simple_pct = (level_counts.get("simple", 0) / total) * 100
    medium_pct = (level_counts.get("medium", 0) / total) * 100
    complex_pct = (level_counts.get("complex", 0) / total) * 100
    
    if simple_pct < 20 or simple_pct > 30:
        issues.append(f"Simple percentage {simple_pct:.1f}% outside target range [20-30%]")
    if medium_pct < 45 or medium_pct > 55:
        issues.append(f"Medium percentage {medium_pct:.1f}% outside target range [45-55%]")
    if complex_pct < 20 or complex_pct > 30:
        issues.append(f"Complex percentage {complex_pct:.1f}% outside target range [20-30%]")
    
    # Check score distribution
    scores = [sample.get("expected_complexity_score", 0) for sample in data]
    if min(scores) > 0.15:
        issues.append(f"Minimum score {min(scores):.3f} too high (should have some below 0.15)")
    if max(scores) < 0.80:
        issues.append(f"Maximum score {max(scores):.3f} too low (should have some above 0.80)")
    
    # Check for duplicates
    queries = [sample.get("query_text", "") for sample in data]
    unique_queries = set(queries)
    if len(unique_queries) != len(queries):
        duplicates = len(queries) - len(unique_queries)
        issues.append(f"Found {duplicates} duplicate queries")
    
    return issues

def main():
    """Main function to combine batches."""
    print("🔄 Epic 1 Training Dataset Assembly")
    print("=" * 50)
    
    # Determine input method
    if len(sys.argv) == 1:
        # Use current directory
        directory = Path(".")
        print(f"📁 Using current directory: {directory.resolve()}")
        batch_files = find_training_files(directory)
    elif len(sys.argv) == 2:
        arg = sys.argv[1]
        path = Path(arg)
        
        if path.is_dir():
            # Use specified directory
            print(f"📁 Using directory: {path}")
            batch_files = find_training_files(path)
        elif path.is_file():
            # Single file specified
            print(f"📄 Using single file: {path}")
            batch_files = [path]
        else:
            print(f"❌ Error: {arg} is not a valid file or directory")
            return
    else:
        # Multiple files specified
        batch_files = []
        for arg in sys.argv[1:]:
            path = Path(arg)
            if path.is_file():
                batch_files.append(path)
            else:
                print(f"⚠️  Warning: {arg} is not a valid file, skipping")
        
        if not batch_files:
            print("❌ No valid files provided")
            return
    
    if not batch_files:
        print("❌ No training JSON files found. Make sure you have generated batch files.")
        print("   Expected files like: simple_batch_25_samples.json, medium_batch1_25_samples.json, etc.")
        return
    
    print(f"\n🔍 Found {len(batch_files)} potential training files")
    
    # Load all batches
    all_samples = []
    for batch_file in batch_files:
        samples = load_batch(batch_file)
        all_samples.extend(samples)
    
    if not all_samples:
        print("❌ No valid samples loaded.")
        return
    
    print(f"\n📊 Loaded {len(all_samples)} total samples")
    
    # Analyze before shuffling
    print("\n🔍 Dataset Analysis:")
    analysis = analyze_dataset(all_samples)
    
    print(f"   Total samples: {analysis['total_samples']}")
    print(f"   Score range: [{analysis['score_stats']['min']}, {analysis['score_stats']['max']}]")
    print(f"   Score mean: {analysis['score_stats']['mean']} (±{analysis['score_stats']['std']})")
    
    print(f"\n📋 Complexity Distribution:")
    total = analysis['total_samples']
    for level, count in analysis['complexity_distribution'].items():
        percentage = (count / total * 100) if total > 0 else 0
        print(f"   {level}: {count} ({percentage:.1f}%)")
    
    print(f"\n📈 Score Range Distribution:")
    ranges = analysis['score_ranges']
    print(f"   Simple (≤0.35): {len(ranges['simple_range'])} samples")
    print(f"   Medium (0.35-0.66): {len(ranges['medium_range'])} samples")
    print(f"   Complex (>0.66): {len(ranges['complex_range'])} samples")
    
    # Validate dataset
    print(f"\n✅ Validation:")
    issues = validate_final_dataset(all_samples)
    if issues:
        print("⚠️  Issues found:")
        for issue in issues:
            print(f"   • {issue}")
    else:
        print("   All validation checks passed!")
    
    # Shuffle dataset
    print(f"\n🔀 Shuffling dataset...")
    random.seed(42)  # For reproducibility
    random.shuffle(all_samples)
    
    # Add generation metadata
    timestamp = datetime.now().isoformat()
    dataset_metadata = {
        "generation_timestamp": timestamp,
        "total_samples": len(all_samples),
        "generation_method": "Claude batch generation",
        "batch_count": 4,
        "complexity_distribution": analysis['complexity_distribution'],
        "score_statistics": analysis['score_stats'],
        "validation_issues": issues
    }
    
    # Save final dataset
    output_file = f"epic1_claude_generated_dataset_{len(all_samples)}_samples.json"
    
    final_dataset = {
        "metadata": dataset_metadata,
        "samples": all_samples
    }
    
    with open(output_file, 'w') as f:
        json.dump(final_dataset, f, indent=2)
    
    print(f"\n💾 Saved final dataset: {output_file}")
    
    # Save samples only (compatible with existing training pipeline)
    samples_only_file = f"epic1_training_dataset_{len(all_samples)}_samples.json"
    with open(samples_only_file, 'w') as f:
        json.dump(all_samples, f, indent=2)
    
    print(f"💾 Saved samples only: {samples_only_file}")
    
    print(f"\n🎉 Dataset assembly complete!")
    print(f"   📁 Full dataset: {output_file}")
    print(f"   📁 Training ready: {samples_only_file}")
    
    if not issues:
        print(f"\n✅ Ready for Epic 1 training pipeline!")
        print(f"   Use: {samples_only_file}")

if __name__ == "__main__":
    main()