import faiss
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional
from src.shared_utils.document_processing.pdf_parser import extract_text_with_metadata
from src.shared_utils.document_processing.hybrid_parser import parse_pdf_with_hybrid_approach
from src.shared_utils.embeddings.generator import generate_embeddings
from src.shared_utils.retrieval.hybrid_search import HybridRetriever
from src.shared_utils.retrieval.vocabulary_index import VocabularyIndex


class BasicRAG:
    """Basic RAG system combining PDF processing, chunking, and embedding search."""
    
    def __init__(self):
        """
        Initialize FAISS index and document storage.
        
        Recommended Usage:
        - For production: Use hybrid_query() method (best performance + quality)
        - For research: enhanced_hybrid_query() available but not recommended
        """
        self.index = None
        self.chunks = []  # Store chunk text and metadata
        self.embedding_dim = 384  # multi-qa-MiniLM-L6-cos-v1 dimension
        self.hybrid_retriever: Optional[HybridRetriever] = None
        self.vocabulary_index: Optional[VocabularyIndex] = None
        
    def index_document(self, pdf_path: Path) -> int:
        """
        Process PDF into chunks, generate embeddings, and add to FAISS index.
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Number of chunks indexed
        """
        try:
            # Extract text from PDF with metadata  
            print(f"Extracting text from {pdf_path}...")
            text_data = extract_text_with_metadata(pdf_path)
            print(f"Extracted {len(text_data.get('text', ''))} characters")
            
            # Chunk the text using hybrid TOC + PDFPlumber approach
            print("Chunking text...")
            chunks = parse_pdf_with_hybrid_approach(
                pdf_path, text_data, target_chunk_size=1400, min_chunk_size=800, max_chunk_size=2000
            )
            print(f"Created {len(chunks)} chunks")
            
        except Exception as e:
            print(f"Error in document processing: {e}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
            raise
        
        # Generate embeddings
        chunk_texts = [chunk["text"] for chunk in chunks]
        embeddings = generate_embeddings(chunk_texts)
        
        # Initialize FAISS index if first document
        if self.index is None:
            self.index = faiss.IndexFlatIP(self.embedding_dim)  # Inner product for similarity
        
        # Add embeddings to FAISS index
        # Normalize embeddings for cosine similarity
        normalized_embeddings = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)
        self.index.add(normalized_embeddings.astype(np.float32))
        
        # Store chunks with enhanced metadata from structure-preserving parser
        for i, chunk in enumerate(chunks):
            chunk_info = {
                "text": chunk["text"],
                "source": str(pdf_path),
                "page": chunk.get("page", 0),
                "chunk_id": len(self.chunks) + i,
                "start_char": chunk.get("start_char", 0),
                "end_char": chunk.get("end_char", len(chunk["text"])),
                # Structure-preserving metadata
                "title": chunk.get("title", ""),
                "parent_title": chunk.get("parent_title", ""),
                "context": chunk.get("context", ""),
                "level": chunk.get("level", 0),
                "quality_score": chunk.get("metadata", {}).get("quality_score", 0.0),
                "parsing_method": "structure_preserving"
            }
            self.chunks.append(chunk_info)
        
        # Initialize hybrid retriever and index chunks
        if self.hybrid_retriever is None:
            self.hybrid_retriever = HybridRetriever()
        
        # Re-index all chunks for hybrid search
        self.hybrid_retriever.index_documents(self.chunks)
        
        # Build or update vocabulary index
        if self.vocabulary_index is None:
            self.vocabulary_index = VocabularyIndex()
        
        # Build vocabulary from all chunks
        print("Building vocabulary index...")
        self.vocabulary_index.build_from_chunks(self.chunks)
        
        # Print vocabulary statistics
        stats = self.vocabulary_index.get_vocabulary_stats()
        print(f"Vocabulary stats: {stats['unique_terms']} unique terms, "
              f"{stats['technical_terms']} technical terms")
        
        return len(chunks)
    
    def index_documents(self, pdf_folder: Path) -> Dict[str, int]:
        """
        Process multiple PDF documents from a folder into the unified index.
        
        Args:
            pdf_folder: Path to folder containing PDF files
            
        Returns:
            Dict mapping document names to number of chunks indexed
            
        Raises:
            ValueError: If folder doesn't exist or no PDFs found
        """
        if not pdf_folder.exists() or not pdf_folder.is_dir():
            raise ValueError(f"PDF folder not found: {pdf_folder}")
        
        pdf_files = list(pdf_folder.glob("*.pdf"))
        if not pdf_files:
            raise ValueError(f"No PDF files found in {pdf_folder}")
        
        results = {}
        total_chunks = 0
        
        print(f"Processing {len(pdf_files)} PDF documents...")
        
        for pdf_file in pdf_files:
            print(f"\nProcessing: {pdf_file.name}")
            try:
                chunk_count = self.index_document(pdf_file)
                results[pdf_file.name] = chunk_count
                total_chunks += chunk_count
                print(f"  ✅ Indexed {chunk_count} chunks")
            except Exception as e:
                print(f"  ❌ Failed to process {pdf_file.name}: {e}")
                results[pdf_file.name] = 0
        
        print(f"\n📊 Multi-document indexing complete:")
        print(f"   - {len([r for r in results.values() if r > 0])}/{len(pdf_files)} documents processed successfully")
        print(f"   - {total_chunks} total chunks indexed")
        print(f"   - {len(set(chunk['source'] for chunk in self.chunks))} unique sources")
        
        return results
    
    def query(self, question: str, top_k: int = 5) -> Dict:
        """
        Search for relevant chunks and return results.
        
        Args:
            question: User question
            top_k: Number of top results to return
            
        Returns:
            Dict with question, relevant chunks, and sources
        """
        if self.index is None or len(self.chunks) == 0:
            return {"question": question, "chunks": [], "sources": []}
        
        # Generate embedding for question
        question_embedding = generate_embeddings([question])
        normalized_question = question_embedding / np.linalg.norm(question_embedding, axis=1, keepdims=True)
        
        # Search FAISS index
        scores, indices = self.index.search(normalized_question.astype(np.float32), top_k)
        
        # Retrieve relevant chunks
        relevant_chunks = []
        sources = set()
        
        for score, idx in zip(scores[0], indices[0]):
            if idx < len(self.chunks):  # Valid index
                chunk = self.chunks[idx].copy()
                chunk["similarity_score"] = float(score)
                relevant_chunks.append(chunk)
                sources.add(chunk["source"])
        
        return {
            "question": question,
            "chunks": relevant_chunks,
            "sources": list(sources)
        }
    
    def hybrid_query(self, question: str, top_k: int = 5, dense_weight: float = 0.7) -> Dict:
        """
        Enhanced query using hybrid dense + sparse retrieval.
        
        Combines semantic similarity (embeddings) with keyword matching (BM25)
        using Reciprocal Rank Fusion for optimal relevance ranking.
        
        Args:
            question: User query
            top_k: Number of results to return
            dense_weight: Weight for dense retrieval (0.7 = 70% semantic, 30% keyword)
        
        Returns:
            Enhanced results with hybrid_score field and retrieval method indicators
            
        Raises:
            ValueError: If hybrid retriever not initialized
        """
        if self.hybrid_retriever is None or len(self.chunks) == 0:
            return {"question": question, "chunks": [], "sources": [], "retrieval_method": "none"}
        
        # Perform hybrid search
        try:
            # Update hybrid retriever weight if different
            if abs(self.hybrid_retriever.dense_weight - dense_weight) > 0.01:
                self.hybrid_retriever.dense_weight = dense_weight
            
            hybrid_results = self.hybrid_retriever.search(question, top_k)
            
            # Process results for consistency with basic query format
            relevant_chunks = []
            sources = set()
            
            for chunk_idx, rrf_score, chunk_dict in hybrid_results:
                # Add hybrid-specific metadata
                enhanced_chunk = chunk_dict.copy()
                enhanced_chunk["hybrid_score"] = float(rrf_score)
                enhanced_chunk["retrieval_method"] = "hybrid"
                
                relevant_chunks.append(enhanced_chunk)
                sources.add(enhanced_chunk["source"])
            
            # Get retrieval statistics for transparency
            stats = self.hybrid_retriever.get_retrieval_stats()
            
            return {
                "question": question,
                "chunks": relevant_chunks,
                "sources": list(sources),
                "retrieval_method": "hybrid",
                "dense_weight": dense_weight,
                "sparse_weight": 1.0 - dense_weight,
                "stats": stats
            }
            
        except Exception as e:
            # Fallback to basic semantic search on hybrid failure
            print(f"Hybrid search failed: {e}")
            print("Falling back to basic semantic search...")
            
            basic_result = self.query(question, top_k)
            basic_result["retrieval_method"] = "fallback_semantic"
            basic_result["error"] = str(e)
            
            return basic_result
    
    def enhanced_hybrid_query(self, question: str, top_k: int = 5, enable_enhancement: bool = False) -> Dict:
        """
        Hybrid query with optional enhancement (DISABLED BY DEFAULT).
        
        Based on comprehensive evaluation, query enhancement does not provide
        meaningful improvements and adds computational overhead. Enhancement
        is disabled by default and standard hybrid search is recommended.
        
        Evaluation Results:
        - Enhancement shows no statistical significance (p=0.374)
        - 1.7x slower than standard hybrid search
        - Lower quality scores than baseline methods
        
        Args:
            question: User query string
            top_k: Number of results to return
            enable_enhancement: Enable query enhancement (NOT RECOMMENDED)
            
        Returns:
            Hybrid search results with optional enhancement metadata
            
        Recommendation: Use hybrid_query() directly for better performance
        """
        if not question or not question.strip():
            return {
                "question": question,
                "chunks": [],
                "sources": [],
                "retrieval_method": "none",
                "enhancement_applied": False
            }
        
        # Check if enhancement is enabled (DISABLED BY DEFAULT)
        if not enable_enhancement:
            # Use standard hybrid search (RECOMMENDED)
            hybrid_result = self.hybrid_query(question, top_k)
            hybrid_result.update({
                "original_query": question,
                "enhancement_applied": False,
                "enhancement_disabled": True,
                "retrieval_method": "hybrid_recommended",
                "note": "Enhancement disabled based on evaluation - use hybrid_query() directly"
            })
            return hybrid_result
        
        try:
            # Enhancement enabled (NOT RECOMMENDED - adds overhead without benefit)
            from src.shared_utils.query_processing.query_enhancer import QueryEnhancer
            
            # Initialize enhancer
            enhancer = QueryEnhancer()
            
            # Step 1: Get baseline semantic results for quality comparison
            baseline_result = self.query(question, top_k)
            baseline_score = 0.0
            if baseline_result.get('chunks'):
                baseline_score = baseline_result['chunks'][0].get('similarity_score', 0.0)
            
            # Step 2: Perform vocabulary-aware enhancement if available
            if self.vocabulary_index is not None:
                enhancement_result = enhancer.enhance_query_with_vocabulary(
                    question, 
                    vocabulary_index=self.vocabulary_index,
                    min_frequency=3
                )
            else:
                # Fallback to conservative enhancement
                enhancement_result = enhancer.enhance_query(question, conservative=True)
            
            enhanced_query = enhancement_result['enhanced_query']
            optimal_weight = enhancement_result['optimal_weight']
            analysis = enhancement_result['analysis']
            metadata = enhancement_result['enhancement_metadata']
            
            # Step 3: Quality check - only enhance if expansion is minimal
            expansion_ratio = metadata.get('expansion_ratio', 1.0)
            should_enhance = (
                expansion_ratio <= 2.0 and  # Limit expansion bloat
                analysis.get('technical_term_count', 0) > 0  # Has technical content
            )
            
            if should_enhance:
                # Execute hybrid search with enhanced query
                hybrid_result = self.hybrid_query(enhanced_query, top_k, optimal_weight)
                
                # Enhance result with query enhancement metadata
                hybrid_result.update({
                    "original_query": question,
                    "enhanced_query": enhanced_query,
                    "adaptive_weight": optimal_weight,
                    "query_analysis": analysis,
                    "enhancement_metadata": metadata,
                    "enhancement_applied": True,
                    "retrieval_method": "enhanced_hybrid",
                    "baseline_score": baseline_score,
                    "quality_validated": True,
                    "warning": "Enhancement enabled despite evaluation showing no benefit"
                })
                
                return hybrid_result
            else:
                # Enhancement not beneficial - use standard hybrid
                hybrid_result = self.hybrid_query(question, top_k)
                hybrid_result.update({
                    "original_query": question,
                    "enhancement_applied": False,
                    "fallback_reason": f"Enhancement not beneficial (expansion: {expansion_ratio:.1f}x)",
                    "baseline_score": baseline_score,
                    "quality_validated": True
                })
                return hybrid_result
            
        except ImportError:
            # QueryEnhancer not available - fallback to basic hybrid
            print("QueryEnhancer not available, falling back to standard hybrid search")
            result = self.hybrid_query(question, top_k)
            result["enhancement_applied"] = False
            result["fallback_reason"] = "QueryEnhancer import failed"
            return result
            
        except Exception as e:
            # Enhancement failed - fallback to basic hybrid
            print(f"Query enhancement failed: {e}")
            print("Falling back to standard hybrid search...")
            
            try:
                result = self.hybrid_query(question, top_k)
                result.update({
                    "original_query": question,
                    "enhancement_applied": False,
                    "enhancement_error": str(e),
                    "fallback_reason": "Enhancement processing failed"
                })
                return result
            except Exception as hybrid_error:
                # Both enhancement and hybrid failed - fallback to semantic
                print(f"Hybrid search also failed: {hybrid_error}")
                print("Falling back to basic semantic search...")
                
                semantic_result = self.query(question, top_k)
                semantic_result.update({
                    "original_query": question,
                    "retrieval_method": "fallback_semantic",
                    "enhancement_applied": False,
                    "enhancement_error": str(e),
                    "hybrid_error": str(hybrid_error),
                    "fallback_reason": "Both enhancement and hybrid failed"
                })
                return semantic_result