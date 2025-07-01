import faiss
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional
from shared_utils.document_processing.pdf_parser import extract_text_with_metadata
from shared_utils.document_processing.chunker import chunk_technical_text
from shared_utils.embeddings.generator import generate_embeddings
from shared_utils.retrieval.hybrid_search import HybridRetriever


class BasicRAG:
    """Basic RAG system combining PDF processing, chunking, and embedding search."""
    
    def __init__(self):
        """Initialize FAISS index and document storage."""
        self.index = None
        self.chunks = []  # Store chunk text and metadata
        self.embedding_dim = 384  # all-MiniLM-L6-v2 dimension
        self.hybrid_retriever: Optional[HybridRetriever] = None
        
    def index_document(self, pdf_path: Path) -> int:
        """
        Process PDF into chunks, generate embeddings, and add to FAISS index.
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Number of chunks indexed
        """
        # Extract text from PDF
        text_data = extract_text_with_metadata(pdf_path)
        full_text = text_data["text"]
        
        # Chunk the text
        chunks = chunk_technical_text(full_text, chunk_size=500, overlap=50)
        
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
        
        # Store chunks with metadata
        for i, chunk in enumerate(chunks):
            chunk_info = {
                "text": chunk["text"],
                "source": str(pdf_path),
                "page": chunk.get("page", 0),
                "chunk_id": len(self.chunks) + i,
                "start_char": chunk.get("start_char", 0),
                "end_char": chunk.get("end_char", len(chunk["text"]))
            }
            self.chunks.append(chunk_info)
        
        # Initialize hybrid retriever and index chunks
        if self.hybrid_retriever is None:
            self.hybrid_retriever = HybridRetriever()
        
        # Re-index all chunks for hybrid search
        self.hybrid_retriever.index_documents(self.chunks)
        
        return len(chunks)
    
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