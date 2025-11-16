#!/usr/bin/env python3
"""
Data Quality Inspection Script.

This script inspects the quality of indexed data by sampling
documents and displaying their content, metadata, and embeddings.

Features:
- Sample random documents from the index
- Display document content and metadata
- Check embedding dimensions and values
- Verify data quality and coherence
- Identify potential issues

Usage:
    # Inspect 5 random documents
    python scripts/inspect_data.py

    # Inspect 10 documents
    python scripts/inspect_data.py --num-samples 10

    # Show full content
    python scripts/inspect_data.py --full-content

    # Inspect specific document by index
    python scripts/inspect_data.py --doc-index 100

Author: Arthur Passuello
Created: 2025-11-16
"""

import sys
import os
import argparse
import json
import pickle
import random
from pathlib import Path
from typing import List, Dict, Any

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.interfaces import Document


class DataInspector:
    """Inspects quality of indexed data."""

    def __init__(self, indices_dir: Path = None):
        """
        Initialize the data inspector.

        Args:
            indices_dir: Directory containing indices
        """
        self.indices_dir = indices_dir or project_root / "data" / "indices"
        self.metadata_path = self.indices_dir / "index_metadata.json"
        self.documents_path = self.indices_dir / "documents.pkl"

        self._load_data()

    def _load_data(self):
        """Load metadata and documents."""
        print("Loading data...")

        # Load metadata
        with open(self.metadata_path, 'r') as f:
            self.metadata = json.load(f)

        print(f"  ✓ Index metadata loaded")

        # Load documents
        with open(self.documents_path, 'rb') as f:
            self.documents = pickle.load(f)

        print(f"  ✓ {len(self.documents)} documents loaded\n")

    def show_index_summary(self):
        """Display index summary information."""
        print("=" * 80)
        print("INDEX SUMMARY")
        print("=" * 80)

        print(f"\nMetadata:")
        print(f"  Created: {self.metadata.get('created_at', 'Unknown')}")
        print(f"  Updated: {self.metadata.get('updated_at', 'Unknown')}")
        print(f"  Document count: {self.metadata.get('document_count', 0)}")
        print(f"  Embedding model: {self.metadata.get('embedding_model', 'Unknown')}")
        print(f"  Embedding dimension: {self.metadata.get('embedding_dim', 0)}")
        print(f"  Index type: {self.metadata.get('index_type', 'Unknown')}")

        # Analyze source distribution
        sources = {}
        total_chars = 0
        chunk_sizes = []

        for doc in self.documents:
            if hasattr(doc, 'metadata') and doc.metadata:
                source = doc.metadata.get('source', 'Unknown')
                # Extract filename
                if '/' in source or '\\' in source:
                    source = Path(source).name
                sources[source] = sources.get(source, 0) + 1

            if hasattr(doc, 'content') and doc.content:
                chars = len(doc.content)
                total_chars += chars
                chunk_sizes.append(chars)

        print(f"\nData Statistics:")
        print(f"  Unique source files: {len(sources)}")
        print(f"  Total characters: {total_chars:,}")
        if chunk_sizes:
            print(f"  Avg chunk size: {sum(chunk_sizes) / len(chunk_sizes):.0f} chars")
            print(f"  Min chunk size: {min(chunk_sizes)} chars")
            print(f"  Max chunk size: {max(chunk_sizes)} chars")

        print(f"\nTop Source Files:")
        sorted_sources = sorted(sources.items(), key=lambda x: x[1], reverse=True)
        for source, count in sorted_sources[:10]:
            print(f"  {source}: {count} chunks")

        print("=" * 80)

    def inspect_document(
        self,
        doc_index: int,
        show_full_content: bool = False,
        show_embedding: bool = False
    ):
        """
        Inspect a specific document.

        Args:
            doc_index: Index of document to inspect
            show_full_content: Whether to show full content
            show_embedding: Whether to show embedding values
        """
        if doc_index >= len(self.documents):
            print(f"❌ Invalid document index: {doc_index} (max: {len(self.documents)-1})")
            return

        doc = self.documents[doc_index]

        print("\n" + "=" * 80)
        print(f"DOCUMENT {doc_index}")
        print("=" * 80)

        # Show metadata
        if hasattr(doc, 'metadata') and doc.metadata:
            print("\nMetadata:")
            for key, value in doc.metadata.items():
                if key == 'source':
                    # Show just filename for brevity
                    if '/' in str(value) or '\\' in str(value):
                        value = Path(value).name
                print(f"  {key}: {value}")
        else:
            print("\n⚠️  No metadata")

        # Show content
        if hasattr(doc, 'content') and doc.content:
            content = doc.content.strip()
            print(f"\nContent ({len(content)} chars):")
            print("-" * 80)

            if show_full_content:
                print(content)
            else:
                # Show first 500 chars
                preview = content[:500]
                if len(content) > 500:
                    preview += "\n\n... [truncated] ..."
                print(preview)

            # Check for quality issues
            issues = []
            if content.count('\n\n\n') > 2:
                issues.append("Excessive blank lines")
            if len(content.split()) < 10:
                issues.append("Very short content")
            if content.count('�') > 0:
                issues.append("Encoding errors detected")

            if issues:
                print("\n⚠️  Quality Issues:")
                for issue in issues:
                    print(f"  - {issue}")

        else:
            print("\n❌ No content")

        # Show embedding info
        if hasattr(doc, 'embedding') and doc.embedding:
            import numpy as np
            emb = np.array(doc.embedding)
            print(f"\nEmbedding:")
            print(f"  Dimension: {len(emb)}")
            print(f"  Min value: {emb.min():.4f}")
            print(f"  Max value: {emb.max():.4f}")
            print(f"  Mean: {emb.mean():.4f}")
            print(f"  Std dev: {emb.std():.4f}")
            print(f"  Norm: {np.linalg.norm(emb):.4f}")

            if show_embedding:
                print(f"\n  First 10 values: {emb[:10]}")

        else:
            print("\n❌ No embedding")

        print("=" * 80)

    def sample_documents(
        self,
        num_samples: int = 5,
        show_full_content: bool = False
    ):
        """
        Sample and display random documents.

        Args:
            num_samples: Number of documents to sample
            show_full_content: Whether to show full content
        """
        print("\n" + "=" * 80)
        print(f"SAMPLING {num_samples} RANDOM DOCUMENTS")
        print("=" * 80)

        # Sample random indices
        num_samples = min(num_samples, len(self.documents))
        sample_indices = random.sample(range(len(self.documents)), num_samples)

        for idx in sample_indices:
            self.inspect_document(idx, show_full_content=show_full_content)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Inspect indexed data quality",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Show index summary
    python scripts/inspect_data.py --summary

    # Sample 5 random documents
    python scripts/inspect_data.py --sample 5

    # Inspect specific document
    python scripts/inspect_data.py --doc-index 100

    # Show full content
    python scripts/inspect_data.py --sample 3 --full-content
        """
    )

    parser.add_argument(
        '--summary',
        action='store_true',
        help='Show index summary'
    )

    parser.add_argument(
        '--sample',
        type=int,
        metavar='N',
        help='Sample N random documents'
    )

    parser.add_argument(
        '--doc-index',
        type=int,
        metavar='INDEX',
        help='Inspect specific document by index'
    )

    parser.add_argument(
        '--full-content',
        action='store_true',
        help='Show full document content'
    )

    parser.add_argument(
        '--show-embedding',
        action='store_true',
        help='Show embedding values'
    )

    parser.add_argument(
        '--indices-dir',
        type=Path,
        help='Directory containing indices (default: data/indices)'
    )

    args = parser.parse_args()

    try:
        # Initialize inspector
        inspector = DataInspector(indices_dir=args.indices_dir)

        # Always show summary first
        inspector.show_index_summary()

        # Run requested inspection
        if args.sample:
            inspector.sample_documents(
                num_samples=args.sample,
                show_full_content=args.full_content
            )
        elif args.doc_index is not None:
            inspector.inspect_document(
                doc_index=args.doc_index,
                show_full_content=args.full_content,
                show_embedding=args.show_embedding
            )
        elif not args.summary:
            # Default: sample 5 documents
            print("\n💡 Tip: Use --sample N to inspect random documents")
            print("        Use --doc-index N to inspect specific document")

    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
