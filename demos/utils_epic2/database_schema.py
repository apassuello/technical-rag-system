"""
Database Schema for Epic 2 Demo Persistent Storage
=================================================

SQLAlchemy models for storing processed documents, chunks, and embeddings
to eliminate re-parsing on system restart.
"""

import json
import time
from datetime import datetime
from typing import Dict, Any, Optional, List
from pathlib import Path

from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, LargeBinary, Float, ForeignKey, Boolean, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, Session
from sqlalchemy.dialects.sqlite import JSON
import numpy as np

Base = declarative_base()


class Document(Base):
    """Document metadata table"""
    __tablename__ = 'documents'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    filename = Column(String(512), nullable=False, unique=True)
    file_path = Column(Text, nullable=False)
    file_hash = Column(String(64), nullable=False)  # MD5 hash for change detection
    file_size = Column(Integer, nullable=False)
    file_mtime = Column(Float, nullable=False)  # File modification time
    
    # Processing metadata
    processed_at = Column(DateTime, default=datetime.utcnow)
    processor_config_hash = Column(String(64), nullable=False)  # Config hash for invalidation
    chunk_count = Column(Integer, default=0)
    
    # Document metadata (JSON field)
    doc_metadata = Column(JSON, nullable=True)
    
    # Status tracking
    processing_status = Column(String(32), default='pending')  # pending, processing, completed, failed
    error_message = Column(Text, nullable=True)
    
    # Relationships
    chunks = relationship("DocumentChunk", back_populates="document", cascade="all, delete-orphan")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_filename', 'filename'),
        Index('idx_file_hash', 'file_hash'),
        Index('idx_processing_status', 'processing_status'),
        Index('idx_processed_at', 'processed_at'),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'filename': self.filename,
            'file_path': self.file_path,
            'file_hash': self.file_hash,
            'file_size': self.file_size,
            'chunk_count': self.chunk_count,
            'processed_at': self.processed_at.isoformat() if self.processed_at else None,
            'processing_status': self.processing_status,
            'metadata': self.doc_metadata
        }


class DocumentChunk(Base):
    """Document chunk content and embeddings table"""
    __tablename__ = 'document_chunks'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    document_id = Column(Integer, ForeignKey('documents.id'), nullable=False)
    chunk_index = Column(Integer, nullable=False)  # Order within document
    
    # Content
    content = Column(Text, nullable=False)
    content_hash = Column(String(64), nullable=False)  # For deduplication
    token_count = Column(Integer, nullable=True)
    
    # Embedding data
    embedding_model = Column(String(256), nullable=False)
    embedding_vector = Column(LargeBinary, nullable=True)  # Numpy array as bytes
    embedding_dimension = Column(Integer, nullable=True)
    embedding_norm = Column(Float, nullable=True)  # For faster similarity calculations
    
    # Chunk metadata (JSON field)
    chunk_metadata = Column(JSON, nullable=True)
    
    # Processing info
    created_at = Column(DateTime, default=datetime.utcnow)
    embedder_config_hash = Column(String(64), nullable=False)
    
    # Quality metrics
    confidence_score = Column(Float, nullable=True)
    relevance_score = Column(Float, nullable=True)
    
    # Relationships
    document = relationship("Document", back_populates="chunks")
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_document_chunk', 'document_id', 'chunk_index'),
        Index('idx_content_hash', 'content_hash'),
        Index('idx_embedding_model', 'embedding_model'),
        Index('idx_embedder_config', 'embedder_config_hash'),
        Index('idx_created_at', 'created_at'),
    )
    
    def get_embedding(self) -> Optional[np.ndarray]:
        """Deserialize embedding vector from binary storage"""
        if self.embedding_vector is None:
            return None
        try:
            return np.frombuffer(self.embedding_vector, dtype=np.float32)
        except Exception:
            return None
    
    def set_embedding(self, embedding: np.ndarray) -> None:
        """Serialize embedding vector to binary storage"""
        if embedding is not None:
            self.embedding_vector = embedding.astype(np.float32).tobytes()
            self.embedding_dimension = len(embedding)
            self.embedding_norm = float(np.linalg.norm(embedding))
        else:
            self.embedding_vector = None
            self.embedding_dimension = None
            self.embedding_norm = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'document_id': self.document_id,
            'chunk_index': self.chunk_index,
            'content': self.content[:200] + '...' if len(self.content) > 200 else self.content,
            'token_count': self.token_count,
            'embedding_model': self.embedding_model,
            'embedding_dimension': self.embedding_dimension,
            'metadata': self.chunk_metadata,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'confidence_score': self.confidence_score
        }


class SystemCache(Base):
    """System-level cache and configuration tracking"""
    __tablename__ = 'system_cache'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    cache_key = Column(String(256), nullable=False, unique=True)
    cache_type = Column(String(64), nullable=False)  # 'embedder_config', 'system_config', etc.
    
    # Cache data
    cache_value = Column(JSON, nullable=True)
    cache_hash = Column(String(64), nullable=False)
    
    # Validity tracking
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)
    is_valid = Column(Boolean, default=True)
    
    # Indexes
    __table_args__ = (
        Index('idx_cache_key', 'cache_key'),
        Index('idx_cache_type', 'cache_type'),
        Index('idx_cache_validity', 'is_valid', 'expires_at'),
    )


class ProcessingSession(Base):
    """Track processing sessions for analytics and debugging"""
    __tablename__ = 'processing_sessions'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(64), nullable=False, unique=True)
    
    # Session metadata
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    status = Column(String(32), default='running')  # running, completed, failed
    
    # Processing stats
    documents_processed = Column(Integer, default=0)
    chunks_created = Column(Integer, default=0)
    embeddings_generated = Column(Integer, default=0)
    
    # Performance metrics
    total_processing_time_ms = Column(Float, nullable=True)
    documents_per_second = Column(Float, nullable=True)
    chunks_per_second = Column(Float, nullable=True)
    
    # Configuration hashes
    processor_config_hash = Column(String(64), nullable=True)
    embedder_config_hash = Column(String(64), nullable=True)
    
    # Error tracking
    error_count = Column(Integer, default=0)
    error_details = Column(JSON, nullable=True)
    
    # Indexes
    __table_args__ = (
        Index('idx_session_id', 'session_id'),
        Index('idx_session_status', 'status'),
        Index('idx_session_time', 'started_at', 'completed_at'),
    )


class DatabaseSchema:
    """Database schema management and utilities"""
    
    @staticmethod
    def create_all_tables(engine) -> None:
        """Create all tables in the database"""
        Base.metadata.create_all(engine)
    
    @staticmethod
    def drop_all_tables(engine) -> None:
        """Drop all tables from the database"""
        Base.metadata.drop_all(engine)
    
    @staticmethod
    def get_table_info(engine) -> Dict[str, Any]:
        """Get information about all tables"""
        from sqlalchemy import inspect
        
        inspector = inspect(engine)
        tables = {}
        
        for table_name in inspector.get_table_names():
            columns = inspector.get_columns(table_name)
            indexes = inspector.get_indexes(table_name)
            
            tables[table_name] = {
                'columns': len(columns),
                'indexes': len(indexes),
                'column_names': [col['name'] for col in columns]
            }
        
        return tables
    
    @staticmethod
    def get_database_stats(session: Session) -> Dict[str, Any]:
        """Get database statistics"""
        stats = {}
        
        try:
            # Document stats
            stats['documents'] = {
                'total': session.query(Document).count(),
                'completed': session.query(Document).filter(Document.processing_status == 'completed').count(),
                'failed': session.query(Document).filter(Document.processing_status == 'failed').count(),
                'pending': session.query(Document).filter(Document.processing_status == 'pending').count()
            }
            
            # Chunk stats
            stats['chunks'] = {
                'total': session.query(DocumentChunk).count(),
                'with_embeddings': session.query(DocumentChunk).filter(DocumentChunk.embedding_vector != None).count()
            }
            
            # Processing sessions
            stats['sessions'] = {
                'total': session.query(ProcessingSession).count(),
                'completed': session.query(ProcessingSession).filter(ProcessingSession.status == 'completed').count(),
                'running': session.query(ProcessingSession).filter(ProcessingSession.status == 'running').count()
            }
            
            # Cache entries
            stats['cache'] = {
                'total': session.query(SystemCache).count(),
                'valid': session.query(SystemCache).filter(SystemCache.is_valid == True).count()
            }
            
        except Exception as e:
            stats['error'] = str(e)
        
        return stats


# Export key classes for use in other modules
__all__ = [
    'Base',
    'Document', 
    'DocumentChunk',
    'SystemCache',
    'ProcessingSession',
    'DatabaseSchema'
]