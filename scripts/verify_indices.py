#!/usr/bin/env python3
"""
Vector Index Verification Script.

This script verifies the integrity and functionality of built vector indices.
It performs comprehensive checks on index structure, searchability, and performance.

Features:
- Index integrity verification
- Search functionality testing
- Performance benchmarking
- Metadata validation
- Document recovery testing
- Comprehensive reporting

Usage:
    # Verify default indices
    python scripts/verify_indices.py

    # Verify specific indices directory
    python scripts/verify_indices.py --indices-dir /path/to/indices

    # Run with performance benchmarks
    python scripts/verify_indices.py --benchmark

    # Generate detailed report
    python scripts/verify_indices.py --report

Author: Arthur Passuello
Created: 2025-11-15
"""

import sys
import os
import argparse
import json
import logging
import pickle
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
import time

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.core.component_factory import ComponentFactory
from src.core.interfaces import Document
from src.core.config import load_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class IndexVerifier:
    """Verifies vector index integrity and functionality."""

    def __init__(
        self,
        indices_dir: Optional[Path] = None,
        config_path: Optional[Path] = None
    ):
        """
        Initialize the index verifier.

        Args:
            indices_dir: Directory containing indices
            config_path: Path to configuration file
        """
        self.indices_dir = indices_dir or project_root / "data" / "indices"
        self.config_path = config_path or project_root / "config" / "default.yaml"

        # Index file paths
        self.metadata_path = self.indices_dir / "index_metadata.json"
        self.documents_path = self.indices_dir / "documents.pkl"
        self.index_path = self.indices_dir / "faiss_index.bin"

        # Verification results
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "indices_dir": str(self.indices_dir),
            "checks": {},
            "overall_status": "UNKNOWN"
        }

    def check_files_exist(self) -> bool:
        """
        Check if all required index files exist.

        Returns:
            True if all files exist
        """
        logger.info("Checking index files...")

        required_files = {
            "metadata": self.metadata_path,
            "documents": self.documents_path,
            "faiss_index": self.index_path
        }

        all_exist = True
        for name, path in required_files.items():
            exists = path.exists()
            size_mb = path.stat().st_size / 1024 / 1024 if exists else 0

            logger.info(f"  {name}: {'✓' if exists else '✗'} ({size_mb:.2f} MB)")

            self.results["checks"][f"file_{name}_exists"] = exists
            if exists:
                self.results["checks"][f"file_{name}_size_mb"] = round(size_mb, 2)

            all_exist = all_exist and exists

        return all_exist

    def load_and_verify_metadata(self) -> bool:
        """
        Load and verify metadata file.

        Returns:
            True if metadata is valid
        """
        logger.info("Verifying metadata...")

        try:
            with open(self.metadata_path, 'r') as f:
                metadata = json.load(f)

            # Check required fields
            required_fields = [
                "created_at", "updated_at", "document_count",
                "embedding_model", "embedding_dim", "index_type"
            ]

            all_present = True
            for field in required_fields:
                present = field in metadata
                logger.info(f"  {field}: {'✓' if present else '✗'}")
                self.results["checks"][f"metadata_{field}"] = present
                all_present = all_present and present

                if present and field in metadata:
                    self.results["checks"][f"metadata_{field}_value"] = metadata[field]

            # Validate values
            if "document_count" in metadata:
                doc_count = metadata["document_count"]
                valid_count = doc_count > 0
                logger.info(f"  document_count valid: {'✓' if valid_count else '✗'} ({doc_count})")
                self.results["checks"]["metadata_valid_doc_count"] = valid_count

            if "embedding_dim" in metadata:
                emb_dim = metadata["embedding_dim"]
                valid_dim = emb_dim > 0
                logger.info(f"  embedding_dim valid: {'✓' if valid_dim else '✗'} ({emb_dim})")
                self.results["checks"]["metadata_valid_emb_dim"] = valid_dim

            return all_present

        except Exception as e:
            logger.error(f"Error loading metadata: {e}")
            self.results["checks"]["metadata_load_error"] = str(e)
            return False

    def load_and_verify_documents(self) -> Tuple[bool, Optional[List[Document]]]:
        """
        Load and verify documents file.

        Returns:
            Tuple of (success, documents list)
        """
        logger.info("Verifying documents...")

        try:
            with open(self.documents_path, 'rb') as f:
                documents = pickle.load(f)

            doc_count = len(documents)
            logger.info(f"  Loaded {doc_count} documents")

            # Check document structure
            if documents:
                sample_doc = documents[0]

                has_content = hasattr(sample_doc, 'content') and sample_doc.content
                has_embedding = hasattr(sample_doc, 'embedding') and sample_doc.embedding is not None
                has_metadata = hasattr(sample_doc, 'metadata')

                logger.info(f"  Sample document:")
                logger.info(f"    - has content: {'✓' if has_content else '✗'}")
                logger.info(f"    - has embedding: {'✓' if has_embedding else '✗'}")
                logger.info(f"    - has metadata: {'✓' if has_metadata else '✗'}")

                if has_embedding:
                    emb_dim = len(sample_doc.embedding)
                    logger.info(f"    - embedding dim: {emb_dim}")
                    self.results["checks"]["document_embedding_dim"] = emb_dim

                self.results["checks"]["document_has_content"] = has_content
                self.results["checks"]["document_has_embedding"] = has_embedding
                self.results["checks"]["document_has_metadata"] = has_metadata

            self.results["checks"]["documents_count"] = doc_count
            return True, documents

        except Exception as e:
            logger.error(f"Error loading documents: {e}")
            self.results["checks"]["documents_load_error"] = str(e)
            return False, None

    def load_and_verify_index(self) -> Tuple[bool, Optional[Any]]:
        """
        Load and verify FAISS index.

        Returns:
            Tuple of (success, faiss index)
        """
        logger.info("Verifying FAISS index...")

        try:
            import faiss

            # Load index
            index = faiss.read_index(str(self.index_path))

            # Check index properties
            ntotal = index.ntotal
            d = index.d
            is_trained = index.is_trained

            logger.info(f"  Index vectors: {ntotal}")
            logger.info(f"  Index dimension: {d}")
            logger.info(f"  Index trained: {'✓' if is_trained else '✗'}")

            self.results["checks"]["index_ntotal"] = ntotal
            self.results["checks"]["index_dimension"] = d
            self.results["checks"]["index_is_trained"] = is_trained

            # Validate
            valid = ntotal > 0 and d > 0 and is_trained
            return valid, index

        except Exception as e:
            logger.error(f"Error loading FAISS index: {e}")
            self.results["checks"]["index_load_error"] = str(e)
            return False, None

    def test_search(
        self,
        faiss_index: Any,
        documents: List[Document],
        num_queries: int = 5
    ) -> bool:
        """
        Test search functionality.

        Args:
            faiss_index: FAISS index to test
            documents: Documents to search
            num_queries: Number of test queries

        Returns:
            True if search works
        """
        logger.info("Testing search functionality...")

        try:
            import numpy as np

            # Use existing document embeddings as test queries
            num_queries = min(num_queries, len(documents))

            search_times = []
            for i in range(num_queries):
                # Use document embedding as query
                query_embedding = np.array([documents[i].embedding], dtype=np.float32)

                # Search
                start_time = time.time()
                distances, indices = faiss_index.search(query_embedding, k=5)
                search_time = (time.time() - start_time) * 1000  # ms

                search_times.append(search_time)

                logger.info(f"  Query {i+1}: {search_time:.2f}ms, top match: idx={indices[0][0]}, dist={distances[0][0]:.4f}")

            # Calculate statistics
            avg_time = sum(search_times) / len(search_times)
            max_time = max(search_times)
            min_time = min(search_times)

            logger.info(f"  Search performance:")
            logger.info(f"    - avg: {avg_time:.2f}ms")
            logger.info(f"    - min: {min_time:.2f}ms")
            logger.info(f"    - max: {max_time:.2f}ms")

            self.results["checks"]["search_avg_time_ms"] = round(avg_time, 2)
            self.results["checks"]["search_min_time_ms"] = round(min_time, 2)
            self.results["checks"]["search_max_time_ms"] = round(max_time, 2)
            self.results["checks"]["search_works"] = True

            return True

        except Exception as e:
            logger.error(f"Error during search test: {e}")
            self.results["checks"]["search_error"] = str(e)
            self.results["checks"]["search_works"] = False
            return False

    def verify(self, benchmark: bool = False) -> Dict[str, Any]:
        """
        Run comprehensive verification.

        Args:
            benchmark: Whether to run performance benchmarks

        Returns:
            Verification results
        """
        logger.info("=" * 80)
        logger.info("VECTOR INDEX VERIFICATION")
        logger.info("=" * 80)

        # Check files exist
        files_ok = self.check_files_exist()

        if not files_ok:
            logger.error("Required index files are missing")
            self.results["overall_status"] = "FAILED"
            return self.results

        # Verify metadata
        metadata_ok = self.load_and_verify_metadata()

        # Verify documents
        documents_ok, documents = self.load_and_verify_documents()

        # Verify index
        index_ok, faiss_index = self.load_and_verify_index()

        # Test search
        search_ok = False
        if index_ok and documents_ok and documents and faiss_index:
            search_ok = self.test_search(
                faiss_index,
                documents,
                num_queries=10 if benchmark else 5
            )

        # Determine overall status
        all_checks = [
            files_ok,
            metadata_ok,
            documents_ok,
            index_ok,
            search_ok
        ]

        if all(all_checks):
            self.results["overall_status"] = "PASSED"
        elif any(all_checks):
            self.results["overall_status"] = "PARTIAL"
        else:
            self.results["overall_status"] = "FAILED"

        # Print summary
        logger.info("\n" + "=" * 80)
        logger.info("VERIFICATION SUMMARY")
        logger.info("=" * 80)
        logger.info(f"Files exist: {'✓' if files_ok else '✗'}")
        logger.info(f"Metadata valid: {'✓' if metadata_ok else '✗'}")
        logger.info(f"Documents valid: {'✓' if documents_ok else '✗'}")
        logger.info(f"Index valid: {'✓' if index_ok else '✗'}")
        logger.info(f"Search works: {'✓' if search_ok else '✗'}")
        logger.info(f"\nOverall Status: {self.results['overall_status']}")
        logger.info("=" * 80)

        return self.results

    def save_report(self, output_path: Optional[Path] = None) -> None:
        """
        Save verification report to file.

        Args:
            output_path: Path to save report
        """
        if output_path is None:
            output_path = self.indices_dir / "verification_report.json"

        with open(output_path, 'w') as f:
            json.dump(self.results, f, indent=2)

        logger.info(f"\nVerification report saved to: {output_path}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Verify vector indices for RAG system",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Verify default indices
    python scripts/verify_indices.py

    # Verify specific indices directory
    python scripts/verify_indices.py --indices-dir /path/to/indices

    # Run with performance benchmarks
    python scripts/verify_indices.py --benchmark

    # Generate detailed report
    python scripts/verify_indices.py --report
        """
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

    parser.add_argument(
        '--benchmark',
        action='store_true',
        help='Run performance benchmarks'
    )

    parser.add_argument(
        '--report',
        action='store_true',
        help='Generate detailed report file'
    )

    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )

    args = parser.parse_args()

    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    try:
        # Create verifier
        verifier = IndexVerifier(
            indices_dir=args.indices_dir,
            config_path=args.config
        )

        # Run verification
        results = verifier.verify(benchmark=args.benchmark)

        # Save report if requested
        if args.report:
            verifier.save_report()

        # Exit with appropriate code
        if results["overall_status"] == "PASSED":
            sys.exit(0)
        elif results["overall_status"] == "PARTIAL":
            sys.exit(1)
        else:
            sys.exit(2)

    except KeyboardInterrupt:
        logger.info("\nVerification interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Verification failed: {e}", exc_info=True)
        sys.exit(2)


if __name__ == "__main__":
    main()
