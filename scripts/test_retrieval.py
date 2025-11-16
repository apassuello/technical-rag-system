#!/usr/bin/env python3
"""
Retrieval Quality Test Script.

This script tests the quality of the RAG system's retrieval functionality
by allowing you to query the built indices and inspect the results.

Features:
- Query the FAISS index with natural language
- Display top-k retrieved documents with scores
- Show document content and metadata
- Test multiple queries in sequence
- Validate semantic search quality

Usage:
    # Single query
    python scripts/test_retrieval.py --query "RISC-V vector instructions"

    # Interactive mode
    python scripts/test_retrieval.py --interactive

    # Show more results
    python scripts/test_retrieval.py --query "memory management" --top-k 10

    # Show full document content
    python scripts/test_retrieval.py --query "privilege levels" --full-content

Author: Arthur Passuello
Created: 2025-11-16
"""

import sys
import os
import argparse
import logging
import pickle
from pathlib import Path
from typing import List, Dict, Any, Tuple
import time

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.component_factory import ComponentFactory
from src.core.interfaces import Document
from src.core.config import load_config

# Configure logging
logging.basicConfig(
    level=logging.WARNING,  # Suppress info logs for cleaner output
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class RetrievalTester:
    """Tests retrieval quality of the RAG system."""

    def __init__(
        self,
        indices_dir: Path = None,
        config_path: Path = None
    ):
        """
        Initialize the retrieval tester.

        Args:
            indices_dir: Directory containing indices
            config_path: Path to configuration file
        """
        self.indices_dir = indices_dir or project_root / "data" / "indices"
        self.config_path = config_path or project_root / "config" / "default.yaml"

        # Load configuration
        self.config = load_config(self.config_path)

        # File paths
        self.metadata_path = self.indices_dir / "index_metadata.json"
        self.documents_path = self.indices_dir / "documents.pkl"
        self.index_path = self.indices_dir / "faiss_index.bin"

        # Load components
        self._load_indices()
        self._initialize_embedder()

    def _load_indices(self):
        """Load FAISS index and documents."""
        print("Loading indices...")

        # Load documents
        with open(self.documents_path, 'rb') as f:
            self.documents = pickle.load(f)

        print(f"  ✓ Loaded {len(self.documents)} documents")

        # Load FAISS index
        import faiss
        self.faiss_index = faiss.read_index(str(self.index_path))

        print(f"  ✓ Loaded FAISS index ({self.faiss_index.ntotal} vectors, dim={self.faiss_index.d})")

    def _initialize_embedder(self):
        """Initialize embedder for query encoding."""
        print("Initializing embedder...")

        factory = ComponentFactory()
        embedder_config = self.config.embedder.model_dump()

        self.embedder = factory.create_embedder(
            embedder_config["type"],
            **embedder_config.get("config", {})
        )

        print("  ✓ Embedder ready")

    def query(
        self,
        query_text: str,
        top_k: int = 5,
        show_full_content: bool = False
    ) -> List[Tuple[Document, float]]:
        """
        Query the index and return top-k results.

        Args:
            query_text: Natural language query
            top_k: Number of results to return
            show_full_content: Whether to show full document content

        Returns:
            List of (document, score) tuples
        """
        print("\n" + "=" * 80)
        print(f"QUERY: {query_text}")
        print("=" * 80)

        # Generate query embedding
        start_time = time.time()
        query_embedding = self.embedder.embed([query_text])[0]
        embedding_time = (time.time() - start_time) * 1000

        # Search FAISS index
        import numpy as np
        query_vec = np.array([query_embedding], dtype=np.float32)

        start_time = time.time()
        distances, indices = self.faiss_index.search(query_vec, k=top_k)
        search_time = (time.time() - start_time) * 1000

        # Collect results
        results = []
        for idx, distance in zip(indices[0], distances[0]):
            if idx < len(self.documents):
                results.append((self.documents[idx], float(distance)))

        # Display results
        print(f"\nTiming: Embedding={embedding_time:.2f}ms, Search={search_time:.2f}ms")
        print(f"\nTop {len(results)} Results:")
        print("-" * 80)

        for i, (doc, score) in enumerate(results, 1):
            print(f"\n[{i}] Score: {score:.4f}")

            # Show metadata
            if hasattr(doc, 'metadata') and doc.metadata:
                source = doc.metadata.get('source', 'Unknown')
                # Extract just filename from path
                if '/' in source or '\\' in source:
                    source = Path(source).name
                print(f"    Source: {source}")

                page = doc.metadata.get('page_number')
                if page:
                    print(f"    Page: {page}")

            # Show content
            if hasattr(doc, 'content') and doc.content:
                content = doc.content.strip()

                if show_full_content:
                    print(f"\n    Content:")
                    print("    " + "\n    ".join(content.split('\n')))
                else:
                    # Show first 300 chars
                    preview = content[:300]
                    if len(content) > 300:
                        preview += "..."
                    print(f"\n    Preview:")
                    print("    " + "\n    ".join(preview.split('\n')))

        print("\n" + "=" * 80)
        return results

    def interactive_mode(self, top_k: int = 5, show_full_content: bool = False):
        """
        Run in interactive mode for multiple queries.

        Args:
            top_k: Number of results per query
            show_full_content: Whether to show full document content
        """
        print("\n" + "=" * 80)
        print("INTERACTIVE RETRIEVAL TEST MODE")
        print("=" * 80)
        print("\nCommands:")
        print("  - Enter a query to search")
        print("  - 'quit' or 'exit' to stop")
        print("  - 'stats' to show index statistics")
        print("=" * 80)

        while True:
            try:
                query = input("\n🔍 Query: ").strip()

                if not query:
                    continue

                if query.lower() in ['quit', 'exit', 'q']:
                    print("\nExiting interactive mode...")
                    break

                if query.lower() == 'stats':
                    self._show_stats()
                    continue

                # Execute query
                self.query(query, top_k=top_k, show_full_content=show_full_content)

            except KeyboardInterrupt:
                print("\n\nExiting interactive mode...")
                break
            except Exception as e:
                print(f"\n❌ Error: {e}")
                logger.error(f"Query error: {e}", exc_info=True)

    def _show_stats(self):
        """Display index statistics."""
        print("\n" + "=" * 80)
        print("INDEX STATISTICS")
        print("=" * 80)
        print(f"Total documents: {len(self.documents)}")
        print(f"Index vectors: {self.faiss_index.ntotal}")
        print(f"Embedding dimension: {self.faiss_index.d}")

        # Count unique sources
        sources = set()
        for doc in self.documents:
            if hasattr(doc, 'metadata') and doc.metadata:
                source = doc.metadata.get('source', '')
                if source:
                    sources.add(Path(source).name if ('/' in source or '\\' in source) else source)

        print(f"Unique source files: {len(sources)}")
        print(f"\nIndex location: {self.indices_dir}")
        print("=" * 80)

    def test_sample_queries(self):
        """Run a set of sample test queries."""
        print("\n" + "=" * 80)
        print("RUNNING SAMPLE TEST QUERIES")
        print("=" * 80)

        sample_queries = [
            "RISC-V vector instructions",
            "memory management and virtual addressing",
            "privilege levels and execution modes",
            "interrupt handling mechanism",
            "instruction encoding format"
        ]

        for query in sample_queries:
            self.query(query, top_k=3, show_full_content=False)
            time.sleep(0.5)  # Brief pause between queries


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Test retrieval quality of RAG system",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Single query
    python scripts/test_retrieval.py --query "RISC-V vector instructions"

    # Interactive mode
    python scripts/test_retrieval.py --interactive

    # Show more results
    python scripts/test_retrieval.py --query "memory management" --top-k 10

    # Show full content
    python scripts/test_retrieval.py --query "privilege levels" --full-content

    # Run sample test queries
    python scripts/test_retrieval.py --sample-queries
        """
    )

    parser.add_argument(
        '--query',
        type=str,
        help='Query text to search for'
    )

    parser.add_argument(
        '--interactive',
        action='store_true',
        help='Run in interactive mode for multiple queries'
    )

    parser.add_argument(
        '--sample-queries',
        action='store_true',
        help='Run a set of sample test queries'
    )

    parser.add_argument(
        '--top-k',
        type=int,
        default=5,
        help='Number of results to return (default: 5)'
    )

    parser.add_argument(
        '--full-content',
        action='store_true',
        help='Show full document content instead of preview'
    )

    parser.add_argument(
        '--indices-dir',
        type=Path,
        help='Directory containing indices (default: data/indices)'
    )

    parser.add_argument(
        '--config',
        type=Path,
        help='Path to configuration file (default: config/default.yaml)'
    )

    args = parser.parse_args()

    try:
        # Initialize tester
        tester = RetrievalTester(
            indices_dir=args.indices_dir,
            config_path=args.config
        )

        # Run appropriate mode
        if args.interactive:
            tester.interactive_mode(
                top_k=args.top_k,
                show_full_content=args.full_content
            )
        elif args.sample_queries:
            tester.test_sample_queries()
        elif args.query:
            tester.query(
                args.query,
                top_k=args.top_k,
                show_full_content=args.full_content
            )
        else:
            # Default: show help
            parser.print_help()
            print("\n💡 Tip: Try --interactive mode to test multiple queries")

    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        logger.error(f"Test failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
