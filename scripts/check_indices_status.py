#!/usr/bin/env python3
"""
Quick Index Status Checker.

This is a lightweight script that checks the status of vector indices
without requiring heavy dependencies. Use this for quick status checks.

Usage:
    python scripts/check_indices_status.py
"""

import json
import sys
from pathlib import Path
from datetime import datetime


def check_indices_status(indices_dir=None):
    """Check the status of vector indices."""

    if indices_dir is None:
        # Assume script is in scripts/ directory
        project_root = Path(__file__).parent.parent
        indices_dir = project_root / "data" / "indices"
    else:
        indices_dir = Path(indices_dir)

    print("=" * 80)
    print("VECTOR INDEX STATUS CHECK")
    print("=" * 80)
    print(f"Checking: {indices_dir}\n")

    # Check if indices directory exists
    if not indices_dir.exists():
        print(f"❌ Indices directory does not exist: {indices_dir}")
        print(f"\nTo create indices, run:")
        print(f"    python scripts/build_indices.py")
        return False

    # Check for required files
    required_files = {
        "FAISS Index": indices_dir / "faiss_index.bin",
        "Documents": indices_dir / "documents.pkl",
        "Metadata": indices_dir / "index_metadata.json"
    }

    all_exist = True
    for name, path in required_files.items():
        if path.exists():
            size_mb = path.stat().st_size / 1024 / 1024
            print(f"✓ {name:20s}: {size_mb:>8.2f} MB - {path.name}")
        else:
            print(f"✗ {name:20s}: MISSING - {path.name}")
            all_exist = False

    print()

    # If metadata exists, show details
    metadata_path = indices_dir / "index_metadata.json"
    if metadata_path.exists():
        try:
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)

            print("Index Metadata:")
            print(f"  Created:        {metadata.get('created_at', 'Unknown')}")
            print(f"  Last Updated:   {metadata.get('updated_at', 'Unknown')}")
            print(f"  Document Count: {metadata.get('document_count', 'Unknown')}")
            print(f"  Embedding Dim:  {metadata.get('embedding_dim', 'Unknown')}")
            print(f"  Embedding Model: {metadata.get('embedding_model', 'Unknown')}")
            print(f"  Index Type:     {metadata.get('index_type', 'Unknown')}")
            print()

            # Check for files indexed
            file_hashes = metadata.get('file_hashes', {})
            print(f"  Files Indexed:  {len(file_hashes)}")

        except Exception as e:
            print(f"⚠️  Could not read metadata: {e}\n")

    # Overall status
    print("=" * 80)
    if all_exist:
        print("STATUS: ✓ Indices are built and ready")
        print("\nTo verify indices:")
        print("    python scripts/verify_indices.py")
    else:
        print("STATUS: ✗ Indices are NOT built")
        print("\nTo build indices:")
        print("    python scripts/build_indices.py")
    print("=" * 80)

    return all_exist


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Check vector index status")
    parser.add_argument(
        '--indices-dir',
        type=str,
        help='Directory containing indices (default: data/indices)'
    )

    args = parser.parse_args()

    status = check_indices_status(args.indices_dir)
    sys.exit(0 if status else 1)
