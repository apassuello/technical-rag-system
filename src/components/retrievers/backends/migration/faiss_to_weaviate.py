"""
FAISS to Weaviate migration tool.

This module provides tools for migrating data from FAISS to Weaviate
while preserving document content, embeddings, and metadata. It includes
validation and rollback capabilities for safe migration.
"""

import logging
import time
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import json
import numpy as np

from src.core.interfaces import Document
from ..faiss_backend import FAISSBackend
from ..weaviate_backend import WeaviateBackend
from .data_validator import DataValidator

logger = logging.getLogger(__name__)


class MigrationError(Exception):
    """Raised when migration operations fail."""
    pass


class FAISSToWeaviateMigrator:
    """
    Tool for migrating data from FAISS to Weaviate backend.
    
    This migrator handles the complete process of moving documents,
    embeddings, and metadata from a FAISS index to Weaviate while
    preserving data integrity and enabling validation.
    
    Features:
    - Complete data migration with validation
    - Backup creation before migration
    - Progress tracking and reporting
    - Rollback capabilities
    - Batch processing for performance
    - Data integrity verification
    
    The migration process:
    1. Extract all documents from FAISS
    2. Validate document integrity
    3. Create backup of current state
    4. Initialize Weaviate schema
    5. Batch transfer documents
    6. Validate migration success
    7. Generate migration report
    """
    
    def __init__(self,
                 faiss_backend: FAISSBackend,
                 weaviate_backend: WeaviateBackend,
                 batch_size: int = 100,
                 validation_enabled: bool = True):
        """
        Initialize the migrator.
        
        Args:
            faiss_backend: Source FAISS backend
            weaviate_backend: Target Weaviate backend
            batch_size: Number of documents to process per batch
            validation_enabled: Whether to perform validation
        """
        self.faiss_backend = faiss_backend
        self.weaviate_backend = weaviate_backend
        self.batch_size = batch_size
        self.validation_enabled = validation_enabled
        
        # Migration tracking
        self.migration_stats = {
            "start_time": None,
            "end_time": None,
            "total_documents": 0,
            "migrated_documents": 0,
            "failed_documents": 0,
            "validation_passed": False,
            "backup_created": False,
            "migration_id": None
        }
        
        # Initialize validator
        if validation_enabled:
            self.validator = DataValidator()
        else:
            self.validator = None
        
        logger.info("FAISS to Weaviate migrator initialized")
    
    def migrate(self, 
                documents: List[Document],
                backup_path: Optional[Path] = None,
                preserve_faiss: bool = True) -> Dict[str, Any]:
        """
        Perform complete migration from FAISS to Weaviate.
        
        Args:
            documents: List of documents to migrate (from FAISS)
            backup_path: Optional path to create backup
            preserve_faiss: Whether to keep FAISS data after migration
            
        Returns:
            Dictionary with migration results and statistics
        """
        migration_id = f"migration_{int(time.time())}"
        self.migration_stats["migration_id"] = migration_id
        self.migration_stats["start_time"] = time.time()
        
        logger.info(f"Starting migration {migration_id}: {len(documents)} documents")
        
        try:
            # Step 1: Validate source data
            if self.validation_enabled:
                logger.info("Validating source documents...")
                validation_result = self.validator.validate_documents(documents)
                if not validation_result["is_valid"]:
                    raise MigrationError(f"Source validation failed: {validation_result['issues']}")
                logger.info("Source validation passed")
            
            # Step 2: Create backup if requested
            if backup_path:
                logger.info(f"Creating backup at {backup_path}...")
                self._create_backup(documents, backup_path)
                self.migration_stats["backup_created"] = True
                logger.info("Backup created successfully")
            
            # Step 3: Initialize Weaviate
            logger.info("Initializing Weaviate backend...")
            self._initialize_weaviate(documents)
            logger.info("Weaviate backend initialized")
            
            # Step 4: Migrate documents in batches
            logger.info("Starting document migration...")
            self._migrate_documents_batch(documents)
            logger.info("Document migration completed")
            
            # Step 5: Validate migration
            if self.validation_enabled:
                logger.info("Validating migration results...")
                validation_passed = self._validate_migration(documents)
                self.migration_stats["validation_passed"] = validation_passed
                
                if not validation_passed:
                    raise MigrationError("Migration validation failed")
                logger.info("Migration validation passed")
            
            # Step 6: Clean up FAISS if requested
            if not preserve_faiss:
                logger.info("Clearing FAISS backend...")
                self.faiss_backend.clear()
                logger.info("FAISS backend cleared")
            
            # Complete migration
            self.migration_stats["end_time"] = time.time()
            self.migration_stats["total_documents"] = len(documents)
            
            # Generate report
            report = self._generate_migration_report()
            logger.info(f"Migration {migration_id} completed successfully")
            
            return {
                "success": True,
                "migration_id": migration_id,
                "report": report,
                "stats": self.migration_stats.copy()
            }
            
        except Exception as e:
            self.migration_stats["end_time"] = time.time()
            logger.error(f"Migration {migration_id} failed: {str(e)}")
            
            return {
                "success": False,
                "migration_id": migration_id,
                "error": str(e),
                "stats": self.migration_stats.copy()
            }
    
    def _initialize_weaviate(self, documents: List[Document]) -> None:
        """
        Initialize Weaviate backend for migration.
        
        Args:
            documents: Documents to be migrated (for dimension detection)
        """
        # Detect embedding dimension
        embedding_dim = None
        for doc in documents:
            if doc.embedding:
                embedding_dim = len(doc.embedding)
                break
        
        if embedding_dim is None:
            raise MigrationError("No embeddings found in documents")
        
        # Initialize Weaviate index
        self.weaviate_backend.initialize_index(embedding_dim)
        
        # Verify connection and schema
        if not self.weaviate_backend.is_trained():
            raise MigrationError("Weaviate backend not ready after initialization")
    
    def _migrate_documents_batch(self, documents: List[Document]) -> None:
        """
        Migrate documents in batches.
        
        Args:
            documents: Documents to migrate
        """
        total_batches = (len(documents) + self.batch_size - 1) // self.batch_size
        
        for batch_idx in range(total_batches):
            start_idx = batch_idx * self.batch_size
            end_idx = min(start_idx + self.batch_size, len(documents))
            batch_documents = documents[start_idx:end_idx]
            
            try:
                logger.info(f"Migrating batch {batch_idx + 1}/{total_batches} ({len(batch_documents)} documents)")
                
                # Add batch to Weaviate
                self.weaviate_backend.add_documents(batch_documents)
                
                # Update stats
                self.migration_stats["migrated_documents"] += len(batch_documents)
                
                logger.debug(f"Batch {batch_idx + 1} completed successfully")
                
            except Exception as e:
                self.migration_stats["failed_documents"] += len(batch_documents)
                logger.error(f"Batch {batch_idx + 1} failed: {str(e)}")
                raise MigrationError(f"Batch migration failed: {str(e)}") from e
    
    def _validate_migration(self, original_documents: List[Document]) -> bool:
        """
        Validate that migration was successful.
        
        Args:
            original_documents: Original documents from FAISS
            
        Returns:
            True if validation passes, False otherwise
        """
        try:
            # Check document count
            weaviate_count = self.weaviate_backend.get_document_count()
            expected_count = len(original_documents)
            
            if weaviate_count != expected_count:
                logger.error(f"Document count mismatch: expected {expected_count}, got {weaviate_count}")
                return False
            
            # Sample-based content validation
            sample_size = min(10, len(original_documents))
            sample_indices = np.random.choice(len(original_documents), sample_size, replace=False)
            
            for idx in sample_indices:
                original_doc = original_documents[idx]
                
                # Search for the document in Weaviate
                if original_doc.embedding:
                    results = self.weaviate_backend.search(
                        np.array(original_doc.embedding),
                        k=1
                    )
                    
                    if not results:
                        logger.error(f"Document {idx} not found in Weaviate")
                        return False
                    
                    # Note: Full content validation would require additional metadata
                    # to match documents exactly. For now, we verify presence.
            
            logger.info("Migration validation completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Migration validation failed: {str(e)}")
            return False
    
    def _create_backup(self, documents: List[Document], backup_path: Path) -> None:
        """
        Create backup of documents before migration.
        
        Args:
            documents: Documents to backup
            backup_path: Path to save backup
        """
        backup_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create backup data structure
        backup_data = {
            "metadata": {
                "timestamp": time.time(),
                "document_count": len(documents),
                "migration_id": self.migration_stats["migration_id"]
            },
            "documents": []
        }
        
        # Add documents to backup
        for i, doc in enumerate(documents):
            doc_data = {
                "index": i,
                "content": doc.content,
                "metadata": doc.metadata,
                "embedding": doc.embedding
            }
            backup_data["documents"].append(doc_data)
        
        # Save backup
        with open(backup_path, 'w', encoding='utf-8') as f:
            json.dump(backup_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Backup saved to {backup_path}")
    
    def _generate_migration_report(self) -> Dict[str, Any]:
        """
        Generate comprehensive migration report.
        
        Returns:
            Dictionary with migration report
        """
        duration = self.migration_stats["end_time"] - self.migration_stats["start_time"]
        
        return {
            "migration_summary": {
                "migration_id": self.migration_stats["migration_id"],
                "duration_seconds": duration,
                "total_documents": self.migration_stats["total_documents"],
                "migrated_documents": self.migration_stats["migrated_documents"],
                "failed_documents": self.migration_stats["failed_documents"],
                "success_rate": (
                    self.migration_stats["migrated_documents"] / 
                    max(1, self.migration_stats["total_documents"])
                )
            },
            "validation": {
                "enabled": self.validation_enabled,
                "passed": self.migration_stats["validation_passed"]
            },
            "backup": {
                "created": self.migration_stats["backup_created"]
            },
            "performance": {
                "documents_per_second": (
                    self.migration_stats["migrated_documents"] / max(0.1, duration)
                ),
                "batch_size": self.batch_size
            },
            "backend_status": {
                "faiss": self.faiss_backend.get_backend_info(),
                "weaviate": self.weaviate_backend.get_backend_info()
            }
        }
    
    def rollback_migration(self, backup_path: Path) -> Dict[str, Any]:
        """
        Rollback migration using backup data.
        
        Args:
            backup_path: Path to backup file
            
        Returns:
            Dictionary with rollback results
        """
        logger.info(f"Starting rollback from backup {backup_path}")
        
        try:
            # Load backup
            with open(backup_path, 'r', encoding='utf-8') as f:
                backup_data = json.load(f)
            
            # Reconstruct documents
            documents = []
            for doc_data in backup_data["documents"]:
                doc = Document(
                    content=doc_data["content"],
                    metadata=doc_data["metadata"],
                    embedding=doc_data["embedding"]
                )
                documents.append(doc)
            
            # Clear Weaviate
            self.weaviate_backend.clear()
            
            # Restore to FAISS
            if documents:
                # Detect embedding dimension
                embedding_dim = len(documents[0].embedding)
                self.faiss_backend.initialize_index(embedding_dim)
                self.faiss_backend.add_documents(documents)
            
            logger.info(f"Rollback completed: restored {len(documents)} documents")
            
            return {
                "success": True,
                "restored_documents": len(documents),
                "backup_metadata": backup_data["metadata"]
            }
            
        except Exception as e:
            logger.error(f"Rollback failed: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_migration_status(self) -> Dict[str, Any]:
        """
        Get current migration status.
        
        Returns:
            Dictionary with current status
        """
        return {
            "migration_id": self.migration_stats["migration_id"],
            "is_running": (
                self.migration_stats["start_time"] is not None and 
                self.migration_stats["end_time"] is None
            ),
            "progress": {
                "total": self.migration_stats["total_documents"],
                "migrated": self.migration_stats["migrated_documents"],
                "failed": self.migration_stats["failed_documents"]
            },
            "stats": self.migration_stats.copy()
        }