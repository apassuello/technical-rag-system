"""
Knowledge Database Cache System
==============================

Persistent storage for processed documents, chunks, and embeddings to avoid
reprocessing on system restart.
"""

import logging
import pickle
import json
import hashlib
import time
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
from dataclasses import asdict

logger = logging.getLogger(__name__)


class KnowledgeCache:
    """Persistent cache for processed documents and embeddings"""
    
    def __init__(self, cache_dir: Path = Path("cache")):
        """
        Initialize knowledge cache
        
        Args:
            cache_dir: Directory to store cache files
        """
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(exist_ok=True)
        
        # Cache file paths
        self.metadata_file = self.cache_dir / "metadata.json"
        self.documents_file = self.cache_dir / "documents.pkl"
        self.embeddings_file = self.cache_dir / "embeddings.npy"
        self.index_file = self.cache_dir / "faiss_index.bin"
        
        # In-memory cache
        self.metadata = self._load_metadata()
        self.documents = None
        self.embeddings = None
        
    def _load_metadata(self) -> Dict[str, Any]:
        """Load cache metadata"""
        try:
            if self.metadata_file.exists():
                with open(self.metadata_file, 'r') as f:
                    return json.load(f)
            return {
                "version": "1.0",
                "created": time.time(),
                "last_updated": time.time(),
                "document_count": 0,
                "chunk_count": 0,
                "file_hashes": {},
                "embedder_config": None
            }
        except Exception as e:
            logger.error(f"Error loading metadata: {e}")
            return self._create_empty_metadata()
    
    def _create_empty_metadata(self) -> Dict[str, Any]:
        """Create empty metadata structure"""
        return {
            "version": "1.0",
            "created": time.time(),
            "last_updated": time.time(),
            "document_count": 0,
            "chunk_count": 0,
            "file_hashes": {},
            "embedder_config": None
        }
    
    def _save_metadata(self):
        """Save metadata to file"""
        try:
            self.metadata["last_updated"] = time.time()
            with open(self.metadata_file, 'w') as f:
                json.dump(self.metadata, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving metadata: {e}")
    
    def _get_file_hash(self, file_path: Path) -> str:
        """Get hash of file for change detection"""
        try:
            with open(file_path, 'rb') as f:
                content = f.read()
                return hashlib.md5(content).hexdigest()
        except Exception as e:
            logger.error(f"Error hashing file {file_path}: {e}")
            return ""
    
    def _get_corpus_hash(self, pdf_files: List[Path]) -> str:
        """Get combined hash of all files in corpus"""
        file_hashes = []
        for pdf_file in sorted(pdf_files):
            file_hash = self._get_file_hash(pdf_file)
            file_hashes.append(f"{pdf_file.name}:{file_hash}")
        
        combined = "|".join(file_hashes)
        return hashlib.md5(combined.encode()).hexdigest()
    
    def is_cache_valid(self, pdf_files: List[Path], embedder_config: Dict[str, Any]) -> bool:
        """
        Check if cache is valid for given files and embedder config
        
        Args:
            pdf_files: List of PDF files in corpus
            embedder_config: Current embedder configuration
            
        Returns:
            True if cache is valid and can be used
        """
        try:
            # Check if cache files exist
            if not all(f.exists() for f in [self.documents_file, self.embeddings_file]):
                logger.info("Cache files missing, cache invalid")
                return False
            
            # Check if metadata exists
            if not self.metadata or self.metadata.get("document_count", 0) == 0:
                logger.info("No metadata or empty cache, cache invalid")
                return False
            
            # Check embedder configuration hash
            current_config_hash = create_embedder_config_hash(embedder_config)
            cached_config_hash = self.metadata.get("embedder_config_hash")
            
            if current_config_hash != cached_config_hash:
                logger.info("Embedder configuration changed, cache invalid")
                return False
            
            # Check file count
            if len(pdf_files) != self.metadata.get("document_count", 0):
                logger.info(f"Document count changed: {len(pdf_files)} vs {self.metadata.get('document_count', 0)}")
                return False
            
            # Quick check: if no files have changed timestamps, cache is likely valid
            all_files_unchanged = True
            for pdf_file in pdf_files:
                if not pdf_file.exists():
                    logger.info(f"File missing: {pdf_file.name}")
                    return False
                
                # Check modification time first (faster than hashing)
                cached_mtime = self.metadata.get("file_mtimes", {}).get(pdf_file.name)
                current_mtime = pdf_file.stat().st_mtime
                
                if cached_mtime != current_mtime:
                    all_files_unchanged = False
                    break
            
            if all_files_unchanged:
                logger.info("Cache validation successful (no timestamp changes)")
                return True
            
            # If timestamps changed, check file hashes (slower but accurate)
            logger.info("Timestamps changed, checking file hashes...")
            changed_files = []
            for pdf_file in pdf_files:
                current_hash = self._get_file_hash(pdf_file)
                cached_hash = self.metadata.get("file_hashes", {}).get(pdf_file.name)
                
                if current_hash != cached_hash:
                    changed_files.append(pdf_file.name)
            
            if changed_files:
                logger.info(f"Files changed: {', '.join(changed_files)}")
                return False
            
            logger.info("Cache validation successful (hashes match)")
            return True
            
        except Exception as e:
            logger.error(f"Error validating cache: {e}")
            return False
    
    def load_documents(self) -> Optional[List[Any]]:
        """Load processed documents from cache"""
        try:
            if self.documents is None and self.documents_file.exists():
                with open(self.documents_file, 'rb') as f:
                    self.documents = pickle.load(f)
                logger.info(f"Loaded {len(self.documents)} documents from cache")
            
            return self.documents
            
        except Exception as e:
            logger.error(f"Error loading documents: {e}")
            return None
    
    def load_embeddings(self) -> Optional[np.ndarray]:
        """Load embeddings from cache"""
        try:
            if self.embeddings is None and self.embeddings_file.exists():
                self.embeddings = np.load(self.embeddings_file)
                logger.info(f"Loaded embeddings with shape {self.embeddings.shape}")
            
            return self.embeddings
            
        except Exception as e:
            logger.error(f"Error loading embeddings: {e}")
            return None
    
    def load_knowledge_base(self) -> Tuple[Optional[List[Any]], Optional[np.ndarray]]:
        """Load both documents and embeddings from cache"""
        try:
            documents = self.load_documents()
            embeddings = self.load_embeddings()
            
            if documents is not None and embeddings is not None:
                logger.info(f"Loaded knowledge base: {len(documents)} documents, embeddings shape {embeddings.shape}")
                return documents, embeddings
            else:
                logger.warning("Failed to load complete knowledge base from cache")
                return None, None
                
        except Exception as e:
            logger.error(f"Error loading knowledge base: {e}")
            return None, None
    
    def is_valid(self) -> bool:
        """Check if cache has valid data"""
        try:
            return (self.documents_file.exists() and 
                   self.embeddings_file.exists() and 
                   self.metadata.get("chunk_count", 0) > 0)
        except:
            return False
    
    def save_knowledge_base(self, documents: List[Any], embeddings: np.ndarray, 
                          pdf_files: List[Path], embedder_config: Dict[str, Any]):
        """
        Save processed documents and embeddings to cache
        
        Args:
            documents: List of processed document objects
            embeddings: Numpy array of embeddings
            pdf_files: List of source PDF files
            embedder_config: Embedder configuration used
        """
        try:
            logger.info(f"Saving knowledge base: {len(documents)} documents, {embeddings.shape} embeddings")
            
            # Save documents
            with open(self.documents_file, 'wb') as f:
                pickle.dump(documents, f)
            
            # Save embeddings
            np.save(self.embeddings_file, embeddings)
            
            # Collect file metadata
            file_hashes = {}
            file_mtimes = {}
            for pdf_file in pdf_files:
                file_hashes[pdf_file.name] = self._get_file_hash(pdf_file)
                file_mtimes[pdf_file.name] = pdf_file.stat().st_mtime
            
            # Update metadata
            self.metadata.update({
                "document_count": len(pdf_files),
                "chunk_count": len(documents),
                "embedder_config": embedder_config,
                "embedder_config_hash": create_embedder_config_hash(embedder_config),
                "file_hashes": file_hashes,
                "file_mtimes": file_mtimes
            })
            
            self._save_metadata()
            
            # Cache in memory
            self.documents = documents
            self.embeddings = embeddings
            
            logger.info("Knowledge base saved successfully")
            
        except Exception as e:
            logger.error(f"Error saving knowledge base: {e}")
            raise
    
    def get_cache_info(self) -> Dict[str, Any]:
        """Get information about cached data"""
        return {
            "cache_valid": self.documents_file.exists() and self.embeddings_file.exists(),
            "document_count": self.metadata.get("document_count", 0),
            "chunk_count": self.metadata.get("chunk_count", 0),
            "last_updated": self.metadata.get("last_updated", 0),
            "cache_size_mb": self._get_cache_size_mb(),
            "embedder_config": self.metadata.get("embedder_config")
        }
    
    def _get_cache_size_mb(self) -> float:
        """Get total cache size in MB"""
        try:
            total_size = 0
            for file_path in [self.metadata_file, self.documents_file, self.embeddings_file]:
                if file_path.exists():
                    total_size += file_path.stat().st_size
            return total_size / (1024 * 1024)
        except:
            return 0.0
    
    def clear_cache(self):
        """Clear all cached data"""
        try:
            for file_path in [self.metadata_file, self.documents_file, self.embeddings_file, self.index_file]:
                if file_path.exists():
                    file_path.unlink()
            
            self.metadata = self._create_empty_metadata()
            self.documents = None
            self.embeddings = None
            
            logger.info("Cache cleared successfully")
            
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
            raise
    
    def save_faiss_index(self, index_data: bytes):
        """Save FAISS index to cache"""
        try:
            with open(self.index_file, 'wb') as f:
                f.write(index_data)
            logger.info("FAISS index saved to cache")
        except Exception as e:
            logger.error(f"Error saving FAISS index: {e}")
    
    def load_faiss_index(self) -> Optional[bytes]:
        """Load FAISS index from cache"""
        try:
            if self.index_file.exists():
                with open(self.index_file, 'rb') as f:
                    return f.read()
            return None
        except Exception as e:
            logger.error(f"Error loading FAISS index: {e}")
            return None


def create_embedder_config_hash(system) -> Dict[str, Any]:
    """Extract embedder configuration for cache validation"""
    try:
        embedder = system.get_component('embedder')
        
        # Get key configuration parameters
        config = {
            "model_name": getattr(embedder, 'model_name', 'unknown'),
            "model_type": type(embedder).__name__,
            "device": getattr(embedder, 'device', 'unknown'),
            "normalize_embeddings": getattr(embedder, 'normalize_embeddings', True)
        }
        
        # Add batch processor config if available
        if hasattr(embedder, 'batch_processor'):
            config["batch_size"] = getattr(embedder.batch_processor, 'batch_size', 32)
        
        return config
        
    except Exception as e:
        logger.error(f"Error creating embedder config hash: {e}")
        return {"error": str(e)}