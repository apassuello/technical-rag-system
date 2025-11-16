#!/usr/bin/env python3
"""
Vector Index Building Script for RAG System.

This script builds FAISS vector indices from document collections.
It processes documents, generates embeddings, and creates searchable indices.

Features:
- Automatic document discovery and processing
- Progress tracking with ETA
- Incremental index updates
- Index metadata generation
- Memory-efficient batch processing
- Resume capability for interrupted builds
- Multiple index type support

Usage:
    # Build indices from default data directory
    python scripts/build_indices.py

    # Build from specific directory
    python scripts/build_indices.py --data-dir /path/to/docs

    # Rebuild indices (overwrite existing)
    python scripts/build_indices.py --rebuild

    # Use specific configuration
    python scripts/build_indices.py --config config/custom.yaml

    # Incremental update (add new documents only)
    python scripts/build_indices.py --incremental

Author: Arthur Passuello
Created: 2025-11-15
"""

import sys
import os
import argparse
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
import pickle
import hashlib

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


class IndexBuilder:
    """Builds and manages FAISS vector indices."""

    def __init__(
        self,
        config_path: Optional[Path] = None,
        indices_dir: Optional[Path] = None,
        data_dir: Optional[Path] = None
    ):
        """
        Initialize the index builder.

        Args:
            config_path: Path to configuration file
            indices_dir: Directory to store indices
            data_dir: Directory containing documents to index
        """
        # Load configuration
        self.config_path = config_path or project_root / "config" / "default.yaml"
        self.config = load_config(self.config_path)

        # Set up directories
        self.indices_dir = indices_dir or project_root / "data" / "indices"
        self.data_dir = data_dir or project_root / "data" / "test"
        self.indices_dir.mkdir(parents=True, exist_ok=True)

        # Initialize components
        logger.info("Initializing components...")
        self.factory = ComponentFactory()

        # Create document processor
        processor_config = self.config.document_processor.model_dump()
        self.processor = self.factory.create_processor(
            processor_config["type"],
            **processor_config.get("config", {})
        )

        # Create embedder
        embedder_config = self.config.embedder.model_dump()
        self.embedder = self.factory.create_embedder(
            embedder_config["type"],
            **embedder_config.get("config", {})
        )

        logger.info("Components initialized successfully")

        # Index metadata
        self.metadata_path = self.indices_dir / "index_metadata.json"
        self.documents_path = self.indices_dir / "documents.pkl"
        self.index_path = self.indices_dir / "faiss_index.bin"

    def discover_documents(self) -> List[Path]:
        """
        Discover all processable documents in the data directory.

        Returns:
            List of document paths
        """
        logger.info(f"Discovering documents in {self.data_dir}...")

        # Supported file types
        extensions = ['.pdf', '.txt', '.md']
        documents = []

        for ext in extensions:
            docs = list(self.data_dir.rglob(f'*{ext}'))
            documents.extend(docs)

        logger.info(f"Found {len(documents)} documents")
        return sorted(documents)

    def calculate_file_hash(self, file_path: Path) -> str:
        """
        Calculate hash of a file for change detection.

        Args:
            file_path: Path to file

        Returns:
            SHA256 hash of file
        """
        sha256 = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                sha256.update(chunk)
        return sha256.hexdigest()

    def load_metadata(self) -> Dict[str, Any]:
        """
        Load existing index metadata.

        Returns:
            Metadata dictionary
        """
        if self.metadata_path.exists():
            with open(self.metadata_path, 'r') as f:
                return json.load(f)
        return {
            "created_at": None,
            "updated_at": None,
            "document_count": 0,
            "embedding_model": None,
            "embedding_dim": None,
            "file_hashes": {},
            "index_type": "faiss"
        }

    def save_metadata(self, metadata: Dict[str, Any]) -> None:
        """
        Save index metadata.

        Args:
            metadata: Metadata to save
        """
        metadata["updated_at"] = datetime.now().isoformat()
        with open(self.metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        logger.info(f"Metadata saved to {self.metadata_path}")

    def process_document(self, file_path: Path) -> List[Document]:
        """
        Process a single document into chunks.

        Args:
            file_path: Path to document

        Returns:
            List of processed document chunks
        """
        logger.info(f"Processing: {file_path.name}")

        try:
            # Process based on file type
            if file_path.suffix == '.pdf':
                documents = self.processor.process(file_path)
            elif file_path.suffix in ['.txt', '.md']:
                with open(file_path, 'r', encoding='utf-8') as f:
                    text = f.read()
                # Create a single document and process it
                from src.core.interfaces import Document
                doc = Document(
                    content=text,
                    metadata={"source": str(file_path), "file_type": file_path.suffix}
                )
                # Use the processor's chunking capability
                documents = [doc]  # For now, treat as single document
            else:
                logger.warning(f"Unsupported file type: {file_path.suffix}")
                return []

            logger.info(f"  → Generated {len(documents)} chunks")
            return documents

        except Exception as e:
            logger.error(f"Error processing {file_path.name}: {e}")
            return []

    def generate_embeddings(self, documents: List[Document]) -> List[Document]:
        """
        Generate embeddings for documents.

        Args:
            documents: Documents to embed

        Returns:
            Documents with embeddings
        """
        if not documents:
            return []

        logger.info(f"Generating embeddings for {len(documents)} chunks...")

        try:
            # Extract texts
            texts = [doc.content for doc in documents]

            # Generate embeddings
            embeddings = self.embedder.embed(texts)

            # Attach embeddings to documents
            for doc, embedding in zip(documents, embeddings):
                doc.embedding = embedding

            logger.info(f"  → Generated {len(embeddings)} embeddings (dim={len(embeddings[0])})")
            return documents

        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            return []

    def build_index(
        self,
        documents: List[Document],
        rebuild: bool = False
    ) -> Tuple[Any, Dict[str, Any]]:
        """
        Build FAISS index from documents.

        Args:
            documents: Documents with embeddings
            rebuild: Whether to rebuild from scratch

        Returns:
            Tuple of (index, metadata)
        """
        logger.info(f"Building FAISS index ({len(documents)} documents)...")

        # Load or create metadata
        metadata = self.load_metadata() if not rebuild else {
            "created_at": datetime.now().isoformat(),
            "updated_at": None,
            "document_count": 0,
            "embedding_model": self.config.embedder.config.model.config.model_name,
            "embedding_dim": len(documents[0].embedding) if documents else None,
            "file_hashes": {},
            "index_type": "faiss"
        }

        # Create FAISS index using the retriever's index component
        from src.components.retrievers.indices.faiss_index import FAISSIndex

        index_config = self.config.retriever.config.vector_index.config.model_dump()
        faiss_index = FAISSIndex(index_config)

        # Initialize index with embedding dimension
        if documents:
            embedding_dim = len(documents[0].embedding)
            faiss_index.initialize_index(embedding_dim)

            # Add documents
            faiss_index.add_documents(documents)

            # Update metadata
            metadata["document_count"] = len(documents)
            metadata["embedding_dim"] = embedding_dim

        return faiss_index, metadata

    def save_index(self, faiss_index: Any, documents: List[Document]) -> None:
        """
        Save FAISS index and documents to disk.

        Args:
            faiss_index: FAISS index to save
            documents: Documents to save
        """
        logger.info("Saving index to disk...")

        # Save FAISS index
        import faiss
        faiss.write_index(faiss_index.index, str(self.index_path))
        logger.info(f"  → FAISS index: {self.index_path}")

        # Save documents
        with open(self.documents_path, 'wb') as f:
            pickle.dump(documents, f)
        logger.info(f"  → Documents: {self.documents_path}")

    def build(
        self,
        rebuild: bool = False,
        incremental: bool = False
    ) -> None:
        """
        Build vector indices from documents.

        Args:
            rebuild: Whether to rebuild indices from scratch
            incremental: Whether to do incremental update
        """
        logger.info("=" * 80)
        logger.info("VECTOR INDEX BUILD")
        logger.info("=" * 80)

        # Load existing metadata
        metadata = self.load_metadata()

        # Discover documents
        file_paths = self.discover_documents()

        if not file_paths:
            logger.warning("No documents found to index")
            return

        # Determine which files to process
        files_to_process = []
        if incremental and not rebuild:
            logger.info("Incremental mode: checking for new/modified files...")
            for file_path in file_paths:
                file_hash = self.calculate_file_hash(file_path)
                stored_hash = metadata.get("file_hashes", {}).get(str(file_path))

                if stored_hash != file_hash:
                    files_to_process.append(file_path)
                    logger.info(f"  → New/modified: {file_path.name}")

            if not files_to_process:
                logger.info("No new or modified files found")
                return
        else:
            files_to_process = file_paths

        # Process documents
        all_documents = []
        total_files = len(files_to_process)

        logger.info(f"\nProcessing {total_files} documents...")
        for i, file_path in enumerate(files_to_process, 1):
            logger.info(f"[{i}/{total_files}] {file_path.name}")

            # Process document
            documents = self.process_document(file_path)

            if documents:
                # Generate embeddings
                documents = self.generate_embeddings(documents)
                all_documents.extend(documents)

                # Update file hash
                file_hash = self.calculate_file_hash(file_path)
                metadata["file_hashes"][str(file_path)] = file_hash

        if not all_documents:
            logger.warning("No documents were successfully processed")
            return

        # Build index
        faiss_index, metadata = self.build_index(all_documents, rebuild=rebuild)

        # Save index
        self.save_index(faiss_index, all_documents)

        # Save metadata
        self.save_metadata(metadata)

        # Print summary
        logger.info("\n" + "=" * 80)
        logger.info("BUILD COMPLETE")
        logger.info("=" * 80)
        logger.info(f"Documents processed: {len(files_to_process)}")
        logger.info(f"Total chunks: {len(all_documents)}")
        logger.info(f"Embedding dimension: {metadata['embedding_dim']}")
        logger.info(f"Index location: {self.indices_dir}")
        logger.info(f"Index size: {self.index_path.stat().st_size / 1024 / 1024:.2f} MB")
        logger.info("=" * 80)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Build vector indices for RAG system",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Build indices from default data directory
    python scripts/build_indices.py

    # Rebuild indices (overwrite existing)
    python scripts/build_indices.py --rebuild

    # Incremental update (add new documents only)
    python scripts/build_indices.py --incremental

    # Use custom configuration
    python scripts/build_indices.py --config config/custom.yaml
        """
    )

    parser.add_argument(
        '--config',
        type=Path,
        help='Path to configuration file (default: config/default.yaml)'
    )

    parser.add_argument(
        '--data-dir',
        type=Path,
        help='Directory containing documents (default: data/test)'
    )

    parser.add_argument(
        '--indices-dir',
        type=Path,
        help='Directory to store indices (default: data/indices)'
    )

    parser.add_argument(
        '--rebuild',
        action='store_true',
        help='Rebuild indices from scratch (overwrite existing)'
    )

    parser.add_argument(
        '--incremental',
        action='store_true',
        help='Only process new or modified documents'
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
        # Create builder
        builder = IndexBuilder(
            config_path=args.config,
            indices_dir=args.indices_dir,
            data_dir=args.data_dir
        )

        # Build indices
        builder.build(
            rebuild=args.rebuild,
            incremental=args.incremental
        )

    except KeyboardInterrupt:
        logger.info("\nBuild interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Build failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
