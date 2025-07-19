"""
Parallel processor for Epic 2 Demo
==================================

Simplified parallel processing for HF deployment
"""

import logging
from pathlib import Path
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


class ParallelDocumentProcessor:
    """Parallel document processor for Epic 2"""
    
    def __init__(self, system, max_workers: int = 2):
        self.system = system
        self.max_workers = max_workers
        
    def process_documents_batched(self, pdf_files: List[Path], batch_size: int = 10) -> Dict[str, int]:
        """Process documents in batches"""
        results = {}
        
        logger.info(f"Processing {len(pdf_files)} documents in batches of {batch_size}")
        
        for i, pdf_file in enumerate(pdf_files):
            try:
                # Process document through system
                result = self.system.process_document(pdf_file)
                chunk_count = result.get("chunk_count", 1)
                results[str(pdf_file)] = chunk_count
                logger.info(f"Processed {pdf_file.name}: {chunk_count} chunks")
            except Exception as e:
                logger.error(f"Failed to process {pdf_file}: {e}")
                results[str(pdf_file)] = 0
        
        return results