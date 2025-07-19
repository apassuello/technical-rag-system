"""
Database Manager for Epic 2 Demo Persistent Storage
==================================================

Simplified version for HF deployment that works with the existing epic2_demo.db
"""

import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import numpy as np

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages database operations for Epic 2 demo persistence"""
    
    def __init__(self, database_url: str = "sqlite:///epic2_demo.db", echo: bool = False):
        """Initialize database manager"""
        self.database_url = database_url
        self.echo = echo
        self.db_path = Path("epic2_demo.db")
        
    def is_cache_valid(self, pdf_files: List[Path], processor_config: Dict[str, Any], embedder_config: Dict[str, Any]) -> bool:
        """Check if database cache is valid for the given files"""
        # For HF deployment, assume database is always valid if it exists
        return self.db_path.exists()
    
    def load_documents_and_embeddings(self, pdf_files: List[Path]) -> Tuple[Optional[List[Dict]], Optional[np.ndarray]]:
        """Load documents and embeddings from database"""
        # For HF deployment, return None to indicate no cached data
        # This will trigger fresh processing which is fine for demo
        logger.info("Database loading not implemented for HF deployment - will use fresh processing")
        return None, None
    
    def save_documents_and_embeddings(self, documents: List, pdf_files: List[Path], 
                                    processor_config: Dict[str, Any], embedder_config: Dict[str, Any]) -> bool:
        """Save documents and embeddings to database"""
        # For HF deployment, just log that we're skipping database save
        logger.info("Database saving skipped for HF deployment")
        return True
    
    def is_database_populated(self) -> bool:
        """Check if database has data"""
        return self.db_path.exists()
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        if self.db_path.exists():
            size_mb = self.db_path.stat().st_size / (1024 * 1024)
            return {
                "database_size_mb": size_mb,
                "status": "available"
            }
        return {"database_size_mb": 0, "status": "not_found"}
    
    def clear_database(self):
        """Clear the database"""
        logger.info("Database clear not implemented for HF deployment")


def get_database_manager() -> DatabaseManager:
    """Get the global database manager instance"""
    return DatabaseManager()