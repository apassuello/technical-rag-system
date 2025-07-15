"""
Migration Utilities for Epic 2 Demo Database
============================================

Utilities to migrate existing pickle-based cache to persistent database
and handle data migrations between versions.
"""

import logging
import pickle
import json
import time
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import numpy as np

from .database_manager import DatabaseManager, get_database_manager
from .knowledge_cache import KnowledgeCache

logger = logging.getLogger(__name__)


class CacheMigrator:
    """Handles migration from pickle cache to database"""
    
    def __init__(self, db_manager: Optional[DatabaseManager] = None):
        """
        Initialize cache migrator
        
        Args:
            db_manager: Database manager instance (creates default if None)
        """
        self.db_manager = db_manager or get_database_manager()
        self.knowledge_cache = KnowledgeCache()
    
    def migrate_cache_to_database(self, pdf_files: List[Path], 
                                processor_config: Dict[str, Any],
                                embedder_config: Dict[str, Any]) -> bool:
        """
        Migrate existing pickle cache to database
        
        Args:
            pdf_files: List of PDF files that were processed
            processor_config: Document processor configuration
            embedder_config: Embedder configuration
            
        Returns:
            True if migration successful
        """
        logger.info("Starting migration from pickle cache to database...")
        
        try:
            # Check if cache is valid and has data
            # Note: knowledge_cache.is_cache_valid expects (pdf_files, embedder_config) but 
            # create_embedder_config_hash expects a system object
            # For migration, we'll use a simplified validation
            if not self.knowledge_cache.is_valid():
                logger.warning("Pickle cache is not valid or missing")
                return False
            
            # Load documents and embeddings from pickle cache
            documents, embeddings = self.knowledge_cache.load_knowledge_base()
            
            if not documents or embeddings is None:
                logger.warning("No data found in pickle cache")
                return False
            
            logger.info(f"Loaded {len(documents)} documents and {embeddings.shape} embeddings from pickle cache")
            
            # Convert documents to expected format
            converted_docs = self._convert_documents_format(documents, embeddings)
            
            logger.info(f"Converted {len(converted_docs)} documents for database save")
            
            # Save to database
            success = self.db_manager.save_documents_and_embeddings(
                converted_docs, pdf_files, processor_config, embedder_config
            )
            
            if success:
                logger.info("Migration to database completed successfully")
                
                # Create backup of pickle cache before clearing
                self._backup_pickle_cache()
                
                # Optionally clear pickle cache
                logger.info("Migration successful - pickle cache backed up")
                return True
            else:
                logger.error("Failed to save migrated data to database")
                return False
                
        except Exception as e:
            logger.error(f"Cache migration failed: {e}")
            return False
    
    def _convert_documents_format(self, documents: List[Any], embeddings: np.ndarray) -> List[Dict[str, Any]]:
        """Convert documents from pickle format to database format"""
        converted_docs = []
        
        for i, doc in enumerate(documents):
            # Handle different document formats
            if hasattr(doc, '__dict__'):
                # Object format
                converted_doc = {
                    'content': getattr(doc, 'content', ''),
                    'metadata': getattr(doc, 'metadata', {}),
                    'confidence': getattr(doc, 'confidence', 0.8),
                    'embedding': embeddings[i] if i < len(embeddings) else None
                }
            elif isinstance(doc, dict):
                # Dictionary format
                converted_doc = {
                    'content': doc.get('content', ''),
                    'metadata': doc.get('metadata', {}),
                    'confidence': doc.get('confidence', 0.8),
                    'embedding': embeddings[i] if i < len(embeddings) else None
                }
            else:
                # String format
                converted_doc = {
                    'content': str(doc),
                    'metadata': {},
                    'confidence': 0.8,
                    'embedding': embeddings[i] if i < len(embeddings) else None
                }
            
            # Ensure metadata has required fields
            if 'metadata' not in converted_doc:
                converted_doc['metadata'] = {}
            
            # Extract source from metadata or create default
            if 'source' not in converted_doc['metadata']:
                # Try to get source from existing metadata
                if hasattr(doc, 'metadata') and isinstance(doc.metadata, dict) and 'source' in doc.metadata:
                    converted_doc['metadata']['source'] = doc.metadata['source']
                elif isinstance(doc, dict) and 'metadata' in doc and isinstance(doc['metadata'], dict) and 'source' in doc['metadata']:
                    converted_doc['metadata']['source'] = doc['metadata']['source']
                else:
                    converted_doc['metadata']['source'] = f'document_{i}.pdf'
            
            if 'page' not in converted_doc['metadata']:
                converted_doc['metadata']['page'] = 1
            
            converted_docs.append(converted_doc)
        
        logger.info(f"Converted {len(converted_docs)} documents to database format")
        return converted_docs
    
    def _backup_pickle_cache(self) -> None:
        """Create backup of pickle cache files"""
        try:
            cache_dir = self.knowledge_cache.cache_dir
            backup_dir = cache_dir / "backup"
            backup_dir.mkdir(exist_ok=True)
            
            timestamp = int(time.time())
            
            # Backup main cache files
            for cache_file in [self.knowledge_cache.documents_file, 
                             self.knowledge_cache.embeddings_file,
                             self.knowledge_cache.metadata_file]:
                if cache_file.exists():
                    backup_file = backup_dir / f"{cache_file.name}.{timestamp}.bak"
                    backup_file.write_bytes(cache_file.read_bytes())
            
            logger.info(f"Pickle cache backed up to {backup_dir}")
            
        except Exception as e:
            logger.warning(f"Failed to backup pickle cache: {e}")
    
    def verify_migration(self, pdf_files: List[Path]) -> bool:
        """
        Verify that migration was successful by comparing data
        
        Args:
            pdf_files: List of PDF files to verify
            
        Returns:
            True if migration verification successful
        """
        try:
            # Load data from database
            db_docs, db_embeddings = self.db_manager.load_documents_and_embeddings(pdf_files)
            
            if not db_docs or db_embeddings is None:
                logger.error("No data found in database after migration")
                return False
            
            # Basic checks
            if len(db_docs) == 0:
                logger.error("No documents found in database")
                return False
            
            if db_embeddings.shape[0] != len(db_docs):
                logger.error(f"Embedding count mismatch: {db_embeddings.shape[0]} vs {len(db_docs)}")
                return False
            
            # Check that embeddings are valid
            if np.isnan(db_embeddings).any():
                logger.error("Database contains invalid embeddings (NaN values)")
                return False
            
            logger.info(f"Migration verification successful: {len(db_docs)} documents, {db_embeddings.shape} embeddings")
            return True
            
        except Exception as e:
            logger.error(f"Migration verification failed: {e}")
            return False


class DatabaseUpgrader:
    """Handles database schema upgrades and version migrations"""
    
    def __init__(self, db_manager: Optional[DatabaseManager] = None):
        """
        Initialize database upgrader
        
        Args:
            db_manager: Database manager instance
        """
        self.db_manager = db_manager or get_database_manager()
    
    def get_database_version(self) -> str:
        """Get current database version"""
        try:
            with self.db_manager.get_session() as session:
                from .database_schema import SystemCache
                
                version_cache = session.query(SystemCache).filter(
                    SystemCache.cache_key == 'database_version'
                ).first()
                
                if version_cache:
                    return version_cache.cache_value.get('version', '1.0')
                else:
                    # First time setup
                    return '1.0'
                    
        except Exception as e:
            logger.warning(f"Could not get database version: {e}")
            return '1.0'
    
    def set_database_version(self, version: str) -> None:
        """Set database version"""
        try:
            with self.db_manager.get_session() as session:
                from .database_schema import SystemCache
                
                version_cache = session.query(SystemCache).filter(
                    SystemCache.cache_key == 'database_version'
                ).first()
                
                if version_cache:
                    version_cache.cache_value = {'version': version}
                    version_cache.is_valid = True
                else:
                    version_cache = SystemCache(
                        cache_key='database_version',
                        cache_type='system',
                        cache_value={'version': version},
                        cache_hash=self.db_manager._hash_config({'version': version})
                    )
                    session.add(version_cache)
                
                session.commit()
                
        except Exception as e:
            logger.error(f"Could not set database version: {e}")
    
    def upgrade_database(self) -> bool:
        """
        Upgrade database to latest version
        
        Returns:
            True if upgrade successful
        """
        current_version = self.get_database_version()
        target_version = '1.0'  # Current version
        
        logger.info(f"Database version check: current={current_version}, target={target_version}")
        
        if current_version == target_version:
            logger.info("Database is already at latest version")
            return True
        
        try:
            # Apply version-specific upgrades
            if current_version < '1.0':
                self._upgrade_to_1_0()
            
            # Set final version
            self.set_database_version(target_version)
            logger.info(f"Database upgraded to version {target_version}")
            return True
            
        except Exception as e:
            logger.error(f"Database upgrade failed: {e}")
            return False
    
    def _upgrade_to_1_0(self) -> None:
        """Upgrade to version 1.0"""
        logger.info("Upgrading database to version 1.0...")
        
        # Version 1.0 is the initial version, so just ensure tables exist
        from .database_schema import DatabaseSchema
        DatabaseSchema.create_all_tables(self.db_manager.engine)
        
        logger.info("Database upgrade to 1.0 complete")


def migrate_existing_cache(pdf_files: List[Path], processor_config: Dict[str, Any], 
                          embedder_config: Dict[str, Any]) -> bool:
    """
    High-level function to migrate existing cache to database
    
    Args:
        pdf_files: List of PDF files
        processor_config: Document processor configuration
        embedder_config: Embedder configuration
        
    Returns:
        True if migration successful
    """
    logger.info("Starting cache migration process...")
    
    try:
        # Initialize migrator
        migrator = CacheMigrator()
        
        # Attempt migration
        success = migrator.migrate_cache_to_database(pdf_files, processor_config, embedder_config)
        
        if success:
            # Verify migration
            if migrator.verify_migration(pdf_files):
                logger.info("Cache migration completed and verified successfully")
                return True
            else:
                logger.error("Migration verification failed")
                return False
        else:
            logger.error("Cache migration failed")
            return False
            
    except Exception as e:
        logger.error(f"Cache migration process failed: {e}")
        return False


def upgrade_database() -> bool:
    """
    High-level function to upgrade database to latest version
    
    Returns:
        True if upgrade successful
    """
    logger.info("Starting database upgrade process...")
    
    try:
        upgrader = DatabaseUpgrader()
        return upgrader.upgrade_database()
        
    except Exception as e:
        logger.error(f"Database upgrade process failed: {e}")
        return False


def get_migration_status() -> Dict[str, Any]:
    """
    Get status of migration and database
    
    Returns:
        Dictionary with migration status information
    """
    try:
        db_manager = get_database_manager()
        upgrader = DatabaseUpgrader(db_manager)
        knowledge_cache = KnowledgeCache()
        
        status = {
            'database_exists': db_manager.is_database_populated(),
            'database_version': upgrader.get_database_version(),
            'database_stats': db_manager.get_database_stats(),
            'pickle_cache_exists': knowledge_cache.is_valid(),
            'pickle_cache_info': knowledge_cache.get_cache_info()
        }
        
        return status
        
    except Exception as e:
        logger.error(f"Failed to get migration status: {e}")
        return {'error': str(e)}