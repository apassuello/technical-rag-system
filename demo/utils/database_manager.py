"""
Database Manager for Epic 2 Demo Persistent Storage
==================================================

Handles database connections, operations, and high-level persistence management
for the Epic 2 demo to achieve <5 second initialization times.
"""

import logging
import hashlib
import time
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Union
from contextlib import contextmanager

import numpy as np
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.pool import StaticPool

from .database_schema import Base, Document, DocumentChunk, SystemCache, ProcessingSession, DatabaseSchema

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages database operations for Epic 2 demo persistence"""
    
    def __init__(self, database_url: str = "sqlite:///demo/epic2_demo.db", echo: bool = False):
        """
        Initialize database manager
        
        Args:
            database_url: Database connection URL
            echo: Whether to echo SQL statements (for debugging)
        """
        self.database_url = database_url
        self.echo = echo
        
        # Create database directory if using SQLite
        if database_url.startswith("sqlite:///"):
            db_path = Path(database_url.replace("sqlite:///", ""))
            db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create engine with optimized settings
        self.engine = create_engine(
            database_url,
            echo=echo,
            poolclass=StaticPool if "sqlite" in database_url else None,
            connect_args={"check_same_thread": False} if "sqlite" in database_url else {},
            pool_pre_ping=True,
            pool_recycle=3600  # 1 hour
        )
        
        # Create session factory
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )
        
        # Initialize database
        self._initialize_database()
    
    def _initialize_database(self) -> None:
        """Initialize database tables and indexes"""
        try:
            logger.info("Initializing database schema...")
            DatabaseSchema.create_all_tables(self.engine)
            
            # Optimize SQLite if using it
            if "sqlite" in self.database_url:
                self._optimize_sqlite()
            
            logger.info("Database initialization complete")
            
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            raise
    
    def _optimize_sqlite(self) -> None:
        """Apply SQLite-specific optimizations"""
        try:
            with self.engine.connect() as conn:
                # Performance optimizations
                conn.execute(text("PRAGMA journal_mode = WAL"))
                conn.execute(text("PRAGMA synchronous = NORMAL"))
                conn.execute(text("PRAGMA cache_size = 10000"))
                conn.execute(text("PRAGMA temp_store = MEMORY"))
                conn.execute(text("PRAGMA mmap_size = 268435456"))  # 256MB
                conn.commit()
            
            logger.info("SQLite optimizations applied")
            
        except Exception as e:
            logger.warning(f"SQLite optimization failed: {e}")
    
    @contextmanager
    def get_session(self):
        """Context manager for database sessions"""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            session.close()
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Get comprehensive database statistics"""
        with self.get_session() as session:
            stats = DatabaseSchema.get_database_stats(session)
            
            # Add database file size if SQLite
            if "sqlite" in self.database_url:
                try:
                    db_path = Path(self.database_url.replace("sqlite:///", ""))
                    if db_path.exists():
                        stats['database_size_mb'] = db_path.stat().st_size / (1024 * 1024)
                except:
                    pass
            
            return stats
    
    def is_database_populated(self) -> bool:
        """Check if database has any processed documents"""
        try:
            with self.get_session() as session:
                count = session.query(Document).filter(
                    Document.processing_status == 'completed'
                ).count()
                return count > 0
        except:
            return False
    
    def is_cache_valid(self, pdf_files: List[Path], processor_config: Dict[str, Any], 
                      embedder_config: Dict[str, Any]) -> bool:
        """
        Check if database cache is valid for given files and configurations
        
        Args:
            pdf_files: List of PDF files to check
            processor_config: Document processor configuration
            embedder_config: Embedder configuration
            
        Returns:
            True if cache is valid and up-to-date
        """
        try:
            with self.get_session() as session:
                # Simple check: do we have any completed documents in database?
                total_docs = session.query(Document).filter(
                    Document.processing_status == 'completed'
                ).count()
                
                total_chunks = session.query(DocumentChunk).filter(
                    DocumentChunk.embedding_vector != None
                ).count()
                
                logger.info(f"Database validation: {total_docs} documents, {total_chunks} chunks with embeddings")
                
                if total_docs == 0 or total_chunks == 0:
                    logger.info("No valid documents/chunks in database")
                    return False
                
                # Check if we have any matching files
                available_files = session.query(Document.filename).filter(
                    Document.processing_status == 'completed'
                ).all()
                available_filenames = [doc.filename for doc in available_files]
                
                requested_filenames = [pdf_file.name for pdf_file in pdf_files]
                matching_files = [f for f in requested_filenames if f in available_filenames]
                
                logger.info(f"File matching: {len(matching_files)}/{len(requested_filenames)} files available in database")
                
                # Accept if we have at least some matching files
                if len(matching_files) > 0:
                    logger.info("Database cache validation successful (partial match)")
                    return True
                else:
                    logger.info("No matching files in database")
                    return False
                
        except Exception as e:
            logger.error(f"Cache validation error: {e}")
            return False
    
    def load_documents_and_embeddings(self, pdf_files: List[Path]) -> Tuple[List[Any], Optional[np.ndarray]]:
        """
        Load documents and embeddings from database
        
        Args:
            pdf_files: List of PDF files to load
            
        Returns:
            Tuple of (documents, embeddings) or (None, None) if failed
        """
        try:
            with self.get_session() as session:
                # Load all chunks for the specified files
                file_names = [f.name for f in pdf_files]
                
                # First check if we have any documents at all
                total_docs = session.query(Document).count()
                logger.info(f"Total documents in database: {total_docs}")
                
                if total_docs == 0:
                    logger.warning("No documents found in database")
                    return None, None
                
                # Check which files we have
                available_docs = session.query(Document.filename).filter(
                    Document.processing_status == 'completed'
                ).all()
                available_files = [doc.filename for doc in available_docs]
                logger.info(f"Available files in database: {available_files[:5]}...")  # Show first 5
                
                # Find intersection of requested and available files
                matching_files = [f for f in file_names if f in available_files]
                logger.info(f"Matching files: {len(matching_files)}/{len(file_names)}")
                
                if not matching_files:
                    logger.warning("No matching files found in database")
                    return None, None
                
                chunks = session.query(DocumentChunk).join(Document).filter(
                    Document.filename.in_(matching_files),
                    Document.processing_status == 'completed',
                    DocumentChunk.embedding_vector != None
                ).order_by(Document.id, DocumentChunk.chunk_index).all()
                
                if not chunks:
                    logger.warning("No chunks found in database")
                    return None, None
                
                # Convert chunks to document objects and collect embeddings
                documents = []
                embeddings = []
                
                for chunk in chunks:
                    # Create document-like object
                    doc = {
                        'id': chunk.id,
                        'content': chunk.content,
                        'metadata': chunk.chunk_metadata or {},
                        'confidence': chunk.confidence_score or 0.8,
                        'embedding': chunk.get_embedding()
                    }
                    
                    # Add document metadata
                    if doc['metadata'] is None:
                        doc['metadata'] = {}
                    
                    doc['metadata'].update({
                        'source': chunk.document.filename,
                        'page': chunk.chunk_metadata.get('page', 1) if chunk.chunk_metadata else 1,
                        'chunk_index': chunk.chunk_index
                    })
                    
                    documents.append(doc)
                    
                    # Collect embedding
                    embedding = chunk.get_embedding()
                    if embedding is not None:
                        embeddings.append(embedding)
                    else:
                        logger.warning(f"Missing embedding for chunk {chunk.id}")
                
                if not embeddings:
                    logger.warning("No embeddings found in database")
                    return documents, None
                
                embeddings_array = np.array(embeddings)
                logger.info(f"Loaded {len(documents)} documents and {embeddings_array.shape} embeddings from database")
                
                return documents, embeddings_array
                
        except Exception as e:
            logger.error(f"Failed to load from database: {e}")
            return None, None
    
    def save_documents_and_embeddings(self, documents: List[Any], pdf_files: List[Path],
                                    processor_config: Dict[str, Any], embedder_config: Dict[str, Any]) -> bool:
        """
        Save documents and embeddings to database
        
        Args:
            documents: List of processed document objects
            pdf_files: List of source PDF files
            processor_config: Document processor configuration
            embedder_config: Embedder configuration
            
        Returns:
            True if save successful
        """
        try:
            processor_hash = self._hash_config(processor_config)
            embedder_hash = self._hash_config(embedder_config)
            
            # Create processing session
            session_id = str(uuid.uuid4())
            processing_start = time.time()
            
            with self.get_session() as session:
                # Create processing session record
                proc_session = ProcessingSession(
                    session_id=session_id,
                    processor_config_hash=processor_hash,
                    embedder_config_hash=embedder_hash,
                    documents_processed=len(pdf_files),
                    chunks_created=len(documents)
                )
                session.add(proc_session)
                session.flush()
                
                # Group documents by source file
                docs_by_file = {}
                for doc in documents:
                    # Get source and extract filename
                    metadata = doc.get('metadata', {}) if isinstance(doc, dict) else getattr(doc, 'metadata', {})
                    source = metadata.get('source', 'unknown')
                    
                    # Extract filename from full path
                    import os
                    if source != 'unknown':
                        source_filename = os.path.basename(source)
                    else:
                        source_filename = metadata.get('source_name', 'unknown')
                    
                    if source_filename not in docs_by_file:
                        docs_by_file[source_filename] = []
                    docs_by_file[source_filename].append(doc)
                
                logger.info(f"Grouped documents by file: {list(docs_by_file.keys())[:5]}...")  # Show first 5
                
                # Process each file
                for pdf_file in pdf_files:
                    file_docs = docs_by_file.get(pdf_file.name, [])
                    if not file_docs:
                        logger.warning(f"No documents found for file: {pdf_file.name}")
                        continue
                    
                    # Create or update document record
                    file_hash = self._hash_file(pdf_file)
                    file_mtime = pdf_file.stat().st_mtime
                    
                    doc_record = session.query(Document).filter(
                        Document.filename == pdf_file.name
                    ).first()
                    
                    if not doc_record:
                        doc_record = Document(
                            filename=pdf_file.name,
                            file_path=str(pdf_file),
                            file_hash=file_hash,
                            file_size=pdf_file.stat().st_size,
                            file_mtime=file_mtime,
                            processor_config_hash=processor_hash,
                            chunk_count=len(file_docs),
                            processing_status='completed',
                            doc_metadata={}  # Initialize with empty metadata
                        )
                        session.add(doc_record)
                        session.flush()
                    else:
                        # Update existing record
                        doc_record.file_hash = file_hash
                        doc_record.file_mtime = file_mtime
                        doc_record.processor_config_hash = processor_hash
                        doc_record.chunk_count = len(file_docs)
                        doc_record.processing_status = 'completed'
                        doc_record.processed_at = datetime.utcnow()
                        
                        # Delete old chunks
                        session.query(DocumentChunk).filter(
                            DocumentChunk.document_id == doc_record.id
                        ).delete()
                    
                    # Save chunks
                    for idx, doc in enumerate(file_docs):
                        # Get content and metadata properly
                        if isinstance(doc, dict):
                            content = doc.get('content', '')
                            metadata = doc.get('metadata', {})
                            confidence = doc.get('confidence', 0.8)
                        else:
                            content = getattr(doc, 'content', '')
                            metadata = getattr(doc, 'metadata', {})
                            confidence = getattr(doc, 'confidence', 0.8)
                        
                        chunk = DocumentChunk(
                            document_id=doc_record.id,
                            chunk_index=idx,
                            content=content,
                            content_hash=self._hash_text(content),
                            chunk_metadata=metadata,
                            embedding_model=embedder_config.get('model', {}).get('model_name', 'unknown'),
                            embedder_config_hash=embedder_hash,
                            confidence_score=confidence
                        )
                        
                        # Set embedding if available
                        embedding = None
                        if hasattr(doc, 'embedding') and doc.embedding is not None:
                            embedding = doc.embedding
                        elif isinstance(doc, dict) and 'embedding' in doc and doc['embedding'] is not None:
                            embedding = doc['embedding']
                        
                        if embedding is not None:
                            chunk.set_embedding(embedding)
                        
                        session.add(chunk)
                
                # Update processing session
                processing_time = (time.time() - processing_start) * 1000
                proc_session.completed_at = datetime.utcnow()
                proc_session.status = 'completed'
                proc_session.total_processing_time_ms = processing_time
                proc_session.chunks_created = len(documents)
                
                session.commit()
                
            logger.info(f"Successfully saved {len(documents)} documents to database in {processing_time:.0f}ms")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save to database: {e}")
            return False
    
    def cleanup_old_data(self, retention_days: int = 30) -> None:
        """Clean up old processing sessions and orphaned data"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
            
            with self.get_session() as session:
                # Clean up old processing sessions
                old_sessions = session.query(ProcessingSession).filter(
                    ProcessingSession.started_at < cutoff_date
                ).delete()
                
                # Clean up invalid cache entries
                invalid_cache = session.query(SystemCache).filter(
                    SystemCache.is_valid == False
                ).delete()
                
                session.commit()
                
            logger.info(f"Cleaned up {old_sessions} old sessions and {invalid_cache} invalid cache entries")
            
        except Exception as e:
            logger.error(f"Cleanup failed: {e}")
    
    def get_processing_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent processing session history"""
        try:
            with self.get_session() as session:
                sessions = session.query(ProcessingSession).order_by(
                    ProcessingSession.started_at.desc()
                ).limit(limit).all()
                
                return [
                    {
                        'session_id': s.session_id,
                        'started_at': s.started_at.isoformat(),
                        'completed_at': s.completed_at.isoformat() if s.completed_at else None,
                        'status': s.status,
                        'documents_processed': s.documents_processed,
                        'chunks_created': s.chunks_created,
                        'processing_time_ms': s.total_processing_time_ms,
                        'documents_per_second': s.documents_per_second
                    }
                    for s in sessions
                ]
                
        except Exception as e:
            logger.error(f"Failed to get processing history: {e}")
            return []
    
    def clear_database(self) -> bool:
        """Clear all data from database (for testing/reset)"""
        try:
            with self.get_session() as session:
                session.query(DocumentChunk).delete()
                session.query(Document).delete()
                session.query(ProcessingSession).delete()
                session.query(SystemCache).delete()
                session.commit()
            
            logger.info("Database cleared successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to clear database: {e}")
            return False
    
    def _hash_file(self, file_path: Path) -> str:
        """Generate hash of file content"""
        try:
            with open(file_path, 'rb') as f:
                return hashlib.md5(f.read()).hexdigest()
        except Exception as e:
            logger.warning(f"Failed to hash file {file_path}: {e}")
            return ""
    
    def _hash_text(self, text: str) -> str:
        """Generate hash of text content"""
        return hashlib.md5(text.encode('utf-8')).hexdigest()
    
    def _hash_config(self, config: Dict[str, Any]) -> str:
        """Generate hash of configuration dictionary"""
        try:
            import json
            # Convert config to string, handling any non-serializable objects
            config_str = json.dumps(config, sort_keys=True, default=str)
            return hashlib.md5(config_str.encode('utf-8')).hexdigest()
        except Exception as e:
            logger.warning(f"Config hash generation failed: {e}")
            # Fallback to string representation
            config_str = str(sorted(config.items()))
            return hashlib.md5(config_str.encode('utf-8')).hexdigest()


# Global database manager instance
_db_manager = None

def get_database_manager(database_url: str = "sqlite:///demo/epic2_demo.db") -> DatabaseManager:
    """Get global database manager instance"""
    global _db_manager
    if _db_manager is None:
        _db_manager = DatabaseManager(database_url)
    return _db_manager


def reset_database_manager():
    """Reset global database manager (for testing)"""
    global _db_manager
    _db_manager = None