#!/usr/bin/env python3
"""
Batch Document Processing for Scaled Knowledge Base

This module handles efficient processing of multiple documents (20-50+) 
to significantly expand the RAG system's knowledge coverage.
"""

import sys
from pathlib import Path
import json
import time
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.rag_with_generation import RAGWithGeneration
from shared_utils.document_processing.hybrid_parser import HybridParser

logger = logging.getLogger(__name__)


@dataclass
class DocumentProcessingResult:
    """Result of processing a single document."""
    filename: str
    success: bool
    chunks_created: int
    processing_time: float
    file_size_mb: float
    error_message: Optional[str] = None
    document_metadata: Optional[Dict[str, Any]] = None


@dataclass
class BatchProcessingStats:
    """Statistics for batch processing operation."""
    total_documents: int
    successful_documents: int
    failed_documents: int
    total_chunks: int
    total_processing_time: float
    total_size_mb: float
    avg_chunks_per_doc: float
    avg_processing_time_per_doc: float
    documents_per_minute: float


class BatchDocumentProcessor:
    """
    Efficiently processes multiple documents for scaled knowledge base.
    
    Optimized for 20-50 documents with memory management and parallel processing.
    """
    
    def __init__(
        self,
        rag_system: Optional[RAGWithGeneration] = None,
        max_workers: int = 4,
        memory_limit_mb: int = 2048,
        chunk_batch_size: int = 100
    ):
        """
        Initialize batch processor.
        
        Args:
            rag_system: Existing RAG system or None to create new
            max_workers: Maximum parallel document processing threads
            memory_limit_mb: Memory limit for processing
            chunk_batch_size: Batch size for chunk indexing
        """
        self.rag_system = rag_system or RAGWithGeneration()
        self.max_workers = max_workers
        self.memory_limit_mb = memory_limit_mb
        self.chunk_batch_size = chunk_batch_size
        
        # Processing statistics
        self.processing_results: List[DocumentProcessingResult] = []
        self.total_chunks_processed = 0
        
        # Document tracking
        self.processed_documents: Dict[str, str] = {}  # filename -> content_hash
        self.document_metadata: Dict[str, Dict[str, Any]] = {}
        
        logger.info(f"BatchDocumentProcessor initialized with {max_workers} workers")
    
    def calculate_document_hash(self, file_path: Path) -> str:
        """Calculate hash of document content for duplicate detection."""
        try:
            with open(file_path, 'rb') as f:
                content = f.read()
            return hashlib.md5(content).hexdigest()
        except Exception as e:
            logger.warning(f"Failed to calculate hash for {file_path}: {e}")
            return str(file_path)
    
    def process_single_document(
        self, 
        file_path: Path,
        skip_duplicates: bool = True
    ) -> DocumentProcessingResult:
        """
        Process a single document with error handling and statistics.
        
        Args:
            file_path: Path to document
            skip_duplicates: Skip if document already processed
            
        Returns:
            DocumentProcessingResult with processing statistics
        """
        start_time = time.time()
        filename = file_path.name
        
        try:
            # Get file size
            file_size_mb = file_path.stat().st_size / (1024 * 1024)
            
            # Check for duplicates
            if skip_duplicates:
                content_hash = self.calculate_document_hash(file_path)
                if content_hash in self.processed_documents.values():
                    logger.info(f"Skipping duplicate document: {filename}")
                    return DocumentProcessingResult(
                        filename=filename,
                        success=True,
                        chunks_created=0,
                        processing_time=time.time() - start_time,
                        file_size_mb=file_size_mb,
                        error_message="Duplicate skipped"
                    )
            
            # Process document
            logger.info(f"Processing document: {filename} ({file_size_mb:.2f} MB)")
            
            # Use the RAG system's index_document method which handles the hybrid parser correctly
            original_chunk_count = len(self.rag_system.chunks)
            chunk_count = self.rag_system.index_document(file_path)
            
            if chunk_count == 0:
                raise ValueError("No chunks extracted from document")
            
            # Get the newly added chunks
            new_chunks = self.rag_system.chunks[original_chunk_count:]
            chunks = new_chunks
            chunks_created = len(chunks)
            
            # Chunks are already added by rag_system.index_document()
            if chunks_created > 0:
                
                # Store metadata
                self.document_metadata[filename] = {
                    'file_path': str(file_path),
                    'chunks_count': chunks_created,
                    'file_size_mb': file_size_mb,
                    'processing_time': time.time() - start_time,
                    'content_hash': content_hash if skip_duplicates else None,
                    'processed_at': datetime.now().isoformat()
                }
                
                if skip_duplicates:
                    self.processed_documents[filename] = content_hash
            
            processing_time = time.time() - start_time
            
            logger.info(f"Successfully processed {filename}: {chunks_created} chunks in {processing_time:.2f}s")
            
            return DocumentProcessingResult(
                filename=filename,
                success=True,
                chunks_created=chunks_created,
                processing_time=processing_time,
                file_size_mb=file_size_mb,
                document_metadata=self.document_metadata.get(filename)
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            error_msg = str(e)
            
            logger.error(f"Failed to process {filename}: {error_msg}")
            
            return DocumentProcessingResult(
                filename=filename,
                success=False,
                chunks_created=0,
                processing_time=processing_time,
                file_size_mb=file_size_mb if 'file_size_mb' in locals() else 0.0,
                error_message=error_msg
            )
    
    def _add_chunks_to_rag_system(self, chunks: List[Dict[str, Any]], source_filename: str):
        """Add chunks to RAG system in batches for memory efficiency."""
        try:
            # Process chunks in batches
            for i in range(0, len(chunks), self.chunk_batch_size):
                batch = chunks[i:i + self.chunk_batch_size]
                
                # Add source information to each chunk
                for chunk in batch:
                    if 'metadata' not in chunk:
                        chunk['metadata'] = {}
                    chunk['metadata']['batch_source'] = source_filename
                
                # Add batch to RAG system
                self.rag_system.chunks.extend(batch)
                self.total_chunks_processed += len(batch)
                
                logger.debug(f"Added batch of {len(batch)} chunks from {source_filename}")
            
            # Rebuild indices after adding all chunks from document
            self._rebuild_indices_if_needed()
            
        except Exception as e:
            logger.error(f"Failed to add chunks from {source_filename} to RAG system: {e}")
            raise
    
    def _rebuild_indices_if_needed(self):
        """Rebuild search indices periodically for efficiency."""
        # Rebuild every 1000 chunks to maintain performance
        if self.total_chunks_processed % 1000 == 0 and self.total_chunks_processed > 0:
            logger.info(f"Rebuilding indices after {self.total_chunks_processed} chunks")
            try:
                # Rebuild dense index
                if hasattr(self.rag_system, 'dense_index'):
                    self.rag_system._build_dense_index()
                
                # Rebuild sparse index
                if hasattr(self.rag_system, 'sparse_retriever'):
                    self.rag_system._build_sparse_index()
                    
                logger.info("Indices rebuilt successfully")
            except Exception as e:
                logger.warning(f"Failed to rebuild indices: {e}")
    
    def process_document_collection(
        self,
        document_paths: List[Path],
        parallel: bool = True,
        skip_duplicates: bool = True,
        progress_callback: Optional[callable] = None
    ) -> BatchProcessingStats:
        """
        Process a collection of documents efficiently.
        
        Args:
            document_paths: List of document file paths
            parallel: Use parallel processing
            skip_duplicates: Skip duplicate documents
            progress_callback: Optional callback for progress updates
            
        Returns:
            BatchProcessingStats with comprehensive metrics
        """
        start_time = time.time()
        self.processing_results = []
        
        logger.info(f"Starting batch processing of {len(document_paths)} documents")
        logger.info(f"Parallel processing: {parallel}, Max workers: {self.max_workers}")
        
        if parallel and len(document_paths) > 1:
            # Parallel processing
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                # Submit all tasks
                future_to_path = {
                    executor.submit(self.process_single_document, path, skip_duplicates): path
                    for path in document_paths
                }
                
                # Collect results as they complete
                for future in as_completed(future_to_path):
                    path = future_to_path[future]
                    try:
                        result = future.result()
                        self.processing_results.append(result)
                        
                        if progress_callback:
                            progress_callback(len(self.processing_results), len(document_paths))
                            
                    except Exception as e:
                        logger.error(f"Failed to process {path}: {e}")
                        self.processing_results.append(
                            DocumentProcessingResult(
                                filename=path.name,
                                success=False,
                                chunks_created=0,
                                processing_time=0.0,
                                file_size_mb=0.0,
                                error_message=str(e)
                            )
                        )
        else:
            # Sequential processing
            for i, path in enumerate(document_paths):
                result = self.process_single_document(path, skip_duplicates)
                self.processing_results.append(result)
                
                if progress_callback:
                    progress_callback(i + 1, len(document_paths))
        
        # Final index rebuild
        logger.info("Performing final index rebuild...")
        self._rebuild_final_indices()
        
        # Calculate statistics
        total_processing_time = time.time() - start_time
        stats = self._calculate_batch_stats(total_processing_time)
        
        logger.info(f"Batch processing completed: {stats.successful_documents}/{stats.total_documents} documents, "
                   f"{stats.total_chunks} chunks in {stats.total_processing_time:.2f}s")
        
        return stats
    
    def _rebuild_final_indices(self):
        """Rebuild all indices after batch processing is complete."""
        try:
            logger.info("Rebuilding final search indices...")
            
            # Rebuild dense embeddings index
            if hasattr(self.rag_system, '_build_dense_index'):
                self.rag_system._build_dense_index()
            
            # Rebuild sparse BM25 index
            if hasattr(self.rag_system, '_build_sparse_index'):
                self.rag_system._build_sparse_index()
            
            # Rebuild vocabulary index
            if hasattr(self.rag_system, '_build_vocabulary_index'):
                self.rag_system._build_vocabulary_index()
            
            logger.info(f"Final indices rebuilt for {len(self.rag_system.chunks)} total chunks")
            
        except Exception as e:
            logger.error(f"Failed to rebuild final indices: {e}")
    
    def _calculate_batch_stats(self, total_processing_time: float) -> BatchProcessingStats:
        """Calculate comprehensive batch processing statistics."""
        successful_results = [r for r in self.processing_results if r.success]
        failed_results = [r for r in self.processing_results if not r.success]
        
        total_chunks = sum(r.chunks_created for r in successful_results)
        total_size_mb = sum(r.file_size_mb for r in self.processing_results)
        
        avg_chunks_per_doc = total_chunks / len(successful_results) if successful_results else 0
        avg_processing_time = sum(r.processing_time for r in successful_results) / len(successful_results) if successful_results else 0
        documents_per_minute = (len(self.processing_results) / total_processing_time) * 60 if total_processing_time > 0 else 0
        
        return BatchProcessingStats(
            total_documents=len(self.processing_results),
            successful_documents=len(successful_results),
            failed_documents=len(failed_results),
            total_chunks=total_chunks,
            total_processing_time=total_processing_time,
            total_size_mb=total_size_mb,
            avg_chunks_per_doc=avg_chunks_per_doc,
            avg_processing_time_per_doc=avg_processing_time,
            documents_per_minute=documents_per_minute
        )
    
    def get_processing_report(self) -> Dict[str, Any]:
        """Generate comprehensive processing report."""
        if not self.processing_results:
            return {"error": "No processing results available"}
        
        stats = self._calculate_batch_stats(
            sum(r.processing_time for r in self.processing_results)
        )
        
        # Detailed results by document
        document_details = []
        for result in self.processing_results:
            document_details.append({
                "filename": result.filename,
                "success": result.success,
                "chunks_created": result.chunks_created,
                "processing_time": f"{result.processing_time:.2f}s",
                "file_size_mb": f"{result.file_size_mb:.2f}MB",
                "error": result.error_message,
                "chunks_per_mb": result.chunks_created / result.file_size_mb if result.file_size_mb > 0 else 0
            })
        
        # Processing efficiency metrics
        successful_results = [r for r in self.processing_results if r.success]
        processing_rates = [r.chunks_created / r.processing_time for r in successful_results if r.processing_time > 0]
        
        return {
            "summary": {
                "total_documents": stats.total_documents,
                "successful_documents": stats.successful_documents,
                "failed_documents": stats.failed_documents,
                "success_rate": f"{(stats.successful_documents / stats.total_documents * 100):.1f}%",
                "total_chunks": stats.total_chunks,
                "total_size_processed": f"{stats.total_size_mb:.2f}MB",
                "total_processing_time": f"{stats.total_processing_time:.2f}s",
                "documents_per_minute": f"{stats.documents_per_minute:.1f}",
                "avg_chunks_per_document": f"{stats.avg_chunks_per_doc:.1f}",
                "avg_processing_time_per_document": f"{stats.avg_processing_time_per_doc:.2f}s"
            },
            "efficiency": {
                "chunks_per_second": f"{stats.total_chunks / stats.total_processing_time:.1f}",
                "mb_per_second": f"{stats.total_size_mb / stats.total_processing_time:.2f}",
                "avg_chunks_per_second_per_doc": f"{sum(processing_rates) / len(processing_rates):.1f}" if processing_rates else "0"
            },
            "document_details": document_details,
            "failed_documents": [
                {"filename": r.filename, "error": r.error_message}
                for r in self.processing_results if not r.success
            ],
            "system_status": {
                "total_chunks_in_system": len(self.rag_system.chunks),
                "unique_sources": len(set(self.document_metadata.keys())),
                "memory_usage_estimate": f"{len(self.rag_system.chunks) * 2:.0f}MB"  # Rough estimate
            }
        }
    
    def save_processing_report(self, output_path: str):
        """Save processing report to JSON file."""
        report = self.get_processing_report()
        report["generated_at"] = datetime.now().isoformat()
        report["processor_config"] = {
            "max_workers": self.max_workers,
            "memory_limit_mb": self.memory_limit_mb,
            "chunk_batch_size": self.chunk_batch_size
        }
        
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Processing report saved to {output_path}")


def process_documents_from_directory(
    directory_path: str,
    file_patterns: List[str] = ["*.pdf"],
    max_workers: int = 4,
    output_report: Optional[str] = None
) -> Tuple[RAGWithGeneration, BatchProcessingStats]:
    """
    Convenience function to process all documents in a directory.
    
    Args:
        directory_path: Path to directory containing documents
        file_patterns: List of file patterns to match (e.g., ["*.pdf", "*.txt"])
        max_workers: Number of parallel workers
        output_report: Optional path to save processing report
        
    Returns:
        Tuple of (RAG system, processing statistics)
    """
    directory = Path(directory_path)
    
    # Find all matching documents
    document_paths = []
    for pattern in file_patterns:
        document_paths.extend(directory.glob(pattern))
    
    if not document_paths:
        raise ValueError(f"No documents found in {directory_path} matching {file_patterns}")
    
    logger.info(f"Found {len(document_paths)} documents to process")
    
    # Initialize processor
    processor = BatchDocumentProcessor(max_workers=max_workers)
    
    # Process documents
    def progress_callback(completed, total):
        print(f"Progress: {completed}/{total} documents processed ({completed/total*100:.1f}%)")
    
    stats = processor.process_document_collection(
        document_paths,
        parallel=True,
        progress_callback=progress_callback
    )
    
    # Save report if requested
    if output_report:
        processor.save_processing_report(output_report)
    
    return processor.rag_system, stats


if __name__ == "__main__":
    # Example usage
    print("🚀 Testing Batch Document Processing")
    print("=" * 50)
    
    # Test with existing test documents
    test_dir = Path("data/test")
    if test_dir.exists():
        print(f"Processing documents from: {test_dir}")
        
        try:
            rag_system, stats = process_documents_from_directory(
                str(test_dir),
                file_patterns=["*.pdf"],
                max_workers=2,  # Conservative for testing
                output_report="batch_processing_report.json"
            )
            
            print(f"\n✅ Batch processing completed!")
            print(f"   📊 Documents: {stats.successful_documents}/{stats.total_documents}")
            print(f"   📚 Total chunks: {stats.total_chunks}")
            print(f"   ⏱️ Processing time: {stats.total_processing_time:.2f}s")
            print(f"   🚀 Documents/minute: {stats.documents_per_minute:.1f}")
            
            # Test query on expanded knowledge base
            print(f"\n🔍 Testing query on expanded knowledge base...")
            result = rag_system.query_with_answer(
                question="What is RISC-V and what are its main principles?",
                top_k=5,
                use_hybrid=True
            )
            
            print(f"   Confidence: {result['confidence']:.1%}")
            print(f"   Citations: {len(result['citations'])}")
            print(f"   Sources: {set(c['source'] for c in result['citations'])}")
            
        except Exception as e:
            print(f"❌ Error during batch processing: {e}")
    else:
        print(f"❌ Test directory not found: {test_dir}")