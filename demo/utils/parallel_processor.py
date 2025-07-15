"""
Parallel Document Processing Utilities
=====================================

Optimized document processing for faster Epic 2 system initialization.
"""

import logging
from pathlib import Path
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import threading

logger = logging.getLogger(__name__)


class ParallelDocumentProcessor:
    """Parallel document processor for faster system initialization"""
    
    def __init__(self, system, max_workers: int = 2):
        """
        Initialize parallel processor
        
        Args:
            system: PlatformOrchestrator instance
            max_workers: Maximum number of parallel workers (reduced to 2 for stability)
        """
        self.system = system
        self.max_workers = max_workers
        self.lock = threading.Lock()  # Thread safety for system operations
    
    def process_documents_batched(self, pdf_files: List[Path], batch_size: int = 10) -> Dict[str, int]:
        """
        Process documents in batches for better performance and memory management
        
        Args:
            pdf_files: List of PDF file paths
            batch_size: Number of documents to process in each batch
            
        Returns:
            Dictionary mapping file paths to chunk counts
        """
        logger.info(f"Processing {len(pdf_files)} documents in batches of {batch_size}")
        
        results = {}
        failed_files = []
        
        # Process documents in batches to avoid memory issues
        for i in range(0, len(pdf_files), batch_size):
            batch = pdf_files[i:i + batch_size]
            logger.info(f"Processing batch {i//batch_size + 1}/{(len(pdf_files) + batch_size - 1)//batch_size}: {len(batch)} files")
            
            # Process batch sequentially for stability
            batch_results = self.system.process_documents(batch)
            results.update(batch_results)
            
            # Brief pause between batches to avoid overwhelming the system
            time.sleep(0.1)
        
        total_chunks = sum(results.values())
        logger.info(f"Batch processing complete: {total_chunks} chunks from {len(pdf_files)} files")
        
        return results
    
    def process_documents_parallel(self, pdf_files: List[Path]) -> Dict[str, int]:
        """
        Process documents in parallel for faster initialization
        
        Args:
            pdf_files: List of PDF file paths
            
        Returns:
            Dictionary mapping file paths to chunk counts
        """
        logger.info(f"Processing {len(pdf_files)} documents with {self.max_workers} parallel workers")
        
        results = {}
        failed_files = []
        
        # Use ThreadPoolExecutor with timeout for I/O-bound operations
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit all document processing tasks
            future_to_file = {
                executor.submit(self._process_single_document, pdf_file): pdf_file 
                for pdf_file in pdf_files
            }
            
            # Collect results as they complete with timeout
            completed = 0
            for future in as_completed(future_to_file, timeout=600):  # 10 minute timeout per batch
                pdf_file = future_to_file[future]
                completed += 1
                
                try:
                    chunk_count = future.result(timeout=120)  # 2 minute timeout per document
                    results[str(pdf_file)] = chunk_count
                    logger.info(f"✅ Processed {pdf_file.name}: {chunk_count} chunks ({completed}/{len(pdf_files)})")
                except Exception as e:
                    logger.error(f"❌ Failed to process {pdf_file}: {e}")
                    failed_files.append(str(pdf_file))
                    results[str(pdf_file)] = 0
                
                # Progress logging every 5 files for better feedback
                if completed % 5 == 0:
                    logger.info(f"📊 Progress: {completed}/{len(pdf_files)} documents processed")
        
        if failed_files:
            logger.warning(f"Failed to process {len(failed_files)} files")
        
        return results
    
    def _process_single_document(self, pdf_file: Path) -> int:
        """
        Process a single document with thread safety
        
        Args:
            pdf_file: Path to PDF file
            
        Returns:
            Number of chunks created
        """
        try:
            # Process document without indexing first (to avoid FAISS thread conflicts)
            logger.debug(f"🔄 Starting processing: {pdf_file.name}")
            
            # Get document processor and embedder directly
            doc_processor = self.system.get_component('document_processor')
            embedder = self.system.get_component('embedder')
            
            # Process document to get chunks (thread-safe)
            documents = doc_processor.process(pdf_file)
            
            # Generate embeddings for chunks (thread-safe)
            texts_to_embed = []
            docs_needing_embedding = []
            
            for doc in documents:
                if not hasattr(doc, 'embedding') or doc.embedding is None:
                    texts_to_embed.append(doc.content)
                    docs_needing_embedding.append(doc)
            
            # Batch embed all texts that need embeddings
            if texts_to_embed:
                embeddings = embedder.embed(texts_to_embed)
                for doc, embedding in zip(docs_needing_embedding, embeddings):
                    doc.embedding = embedding
            
            # Store results for later indexing (thread-safe)
            chunk_count = len(documents)
            
            # Index documents in the main thread (using lock for FAISS safety)
            with self.lock:
                retriever = self.system.get_component('retriever')
                retriever.index_documents(documents)
            
            logger.debug(f"✅ Completed processing: {pdf_file.name} ({chunk_count} chunks)")
            return chunk_count
            
        except Exception as e:
            logger.error(f"❌ Error processing {pdf_file}: {e}")
            raise


def create_optimized_batch_processor(pdf_files: List[Path], batch_size: int = 16) -> List[List[Path]]:
    """
    Create optimized batches for document processing
    
    Args:
        pdf_files: List of PDF files
        batch_size: Size of each batch
        
    Returns:
        List of batches (each batch is a list of file paths)
    """
    # Sort files by size for better load balancing
    try:
        pdf_files_with_size = [(f, f.stat().st_size) for f in pdf_files if f.exists()]
        pdf_files_with_size.sort(key=lambda x: x[1], reverse=True)  # Largest first
        sorted_files = [f for f, _ in pdf_files_with_size]
    except:
        sorted_files = pdf_files
    
    # Create batches
    batches = []
    for i in range(0, len(sorted_files), batch_size):
        batch = sorted_files[i:i + batch_size]
        batches.append(batch)
    
    return batches