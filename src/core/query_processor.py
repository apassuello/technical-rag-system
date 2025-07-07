"""
Query Processor - Handles query execution workflow.

This component focuses solely on query processing logic,
separated from platform orchestration concerns. In Phase 1,
it extracts the query logic from RAGPipeline.
"""

import logging
from typing import List, Dict, Any, Optional

from .interfaces import Answer, RetrievalResult, Retriever, AnswerGenerator, Document

logger = logging.getLogger(__name__)


class QueryProcessor:
    """
    Query Processor handles the query execution workflow.
    
    Responsibilities:
    - Query analysis and enhancement
    - Retrieval orchestration
    - Context selection and ranking
    - Answer generation coordination
    - Response assembly
    
    In Phase 1, this component works with component references passed
    during initialization. In Phase 3, it will be enhanced with direct
    wiring and additional features like caching.
    """
    
    def __init__(
        self, 
        retriever: Retriever, 
        generator: AnswerGenerator,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize query processor with component references.
        
        Args:
            retriever: Retriever component for document search
            generator: Answer generator component for response generation
            config: Optional configuration dictionary
        """
        self.retriever = retriever
        self.generator = generator
        self.config = config or {}
        
        # Extract configuration values
        self.default_k = self.config.get('retrieval_k', 5)
        self.min_confidence = self.config.get('min_confidence', 0.0)
        
        logger.info("Query processor initialized")
    
    def process(self, query: str, k: Optional[int] = None) -> Answer:
        """
        Process a query and return an answer.
        
        This method orchestrates the query processing workflow:
        1. Analyze query (placeholder for future enhancement)
        2. Retrieve relevant documents
        3. Select and rank context
        4. Generate answer
        5. Assemble final response
        
        Args:
            query: User query string
            k: Number of documents to retrieve (uses default if None)
            
        Returns:
            Answer object with generated text, sources, and metadata
            
        Raises:
            ValueError: If query is empty
            RuntimeError: If query processing fails
        """
        if not query.strip():
            raise ValueError("Query cannot be empty")
        
        k = k or self.default_k
        
        logger.info(f"Processing query: {query[:100]}...")
        
        try:
            # Step 1: Analyze query (future enhancement placeholder)
            analyzed_query = self._analyze_query(query)
            
            # Step 2: Retrieve relevant documents
            retrieval_results = self._retrieve_documents(analyzed_query, k)
            
            # Step 3: Select and rank context
            context_docs = self._select_context(retrieval_results)
            
            # Step 4: Generate answer
            answer = self._generate_answer(query, context_docs)
            
            # Step 5: Assemble final response
            final_answer = self._assemble_response(
                answer, retrieval_results, query
            )
            
            logger.info(f"Query processed successfully with confidence: {final_answer.confidence}")
            return final_answer
            
        except Exception as e:
            logger.error(f"Query processing failed: {str(e)}")
            raise RuntimeError(f"Query processing failed: {str(e)}") from e
    
    def _analyze_query(self, query: str) -> str:
        """
        Analyze and potentially enhance the query.
        
        In Phase 1, this is a placeholder that returns the query as-is.
        In Phase 3, this will be enhanced with actual query analysis.
        
        Args:
            query: Original user query
            
        Returns:
            Analyzed/enhanced query
        """
        # Placeholder for future enhancement
        return query
    
    def _retrieve_documents(self, query: str, k: int) -> List[RetrievalResult]:
        """
        Retrieve relevant documents for the query.
        
        Args:
            query: Query string
            k: Number of documents to retrieve
            
        Returns:
            List of retrieval results
        """
        logger.debug(f"Retrieving {k} documents for query: {query[:50]}...")
        
        results = self.retriever.retrieve(query, k)
        
        if not results:
            logger.warning(f"No documents retrieved for query: {query}")
        else:
            logger.debug(f"Retrieved {len(results)} documents with scores: "
                        f"{[r.score for r in results[:3]]}...")
        
        return results
    
    def _select_context(self, results: List[RetrievalResult]) -> List[Document]:
        """
        Select and rank context documents.
        
        In Phase 1, this applies basic filtering based on confidence.
        In Phase 3, this will be enhanced with re-ranking and other features.
        
        Args:
            results: List of retrieval results
            
        Returns:
            List of selected context documents
        """
        if not results:
            return []
        
        # Apply minimum confidence filtering
        filtered_results = [
            r for r in results 
            if r.score >= self.min_confidence
        ]
        
        if not filtered_results:
            logger.warning(f"No results passed confidence threshold of {self.min_confidence}")
            # Return top results anyway if nothing passes threshold
            filtered_results = results[:3] if results else []
        
        # Extract documents
        context_docs = [r.document for r in filtered_results]
        
        logger.debug(f"Selected {len(context_docs)} context documents")
        return context_docs
    
    def _generate_answer(self, query: str, context_docs: List[Document]) -> Answer:
        """
        Generate answer from query and context.
        
        Args:
            query: User query
            context_docs: List of context documents
            
        Returns:
            Generated answer
        """
        if not context_docs:
            return Answer(
                text="No relevant information found for your query.",
                sources=[],
                confidence=0.0,
                metadata={
                    "query": query,
                    "context_docs": 0,
                    "processor": "QueryProcessor"
                }
            )
        
        logger.debug(f"Generating answer with {len(context_docs)} context documents")
        
        # Use answer generator
        answer = self.generator.generate(query, context_docs)
        
        # Add processor metadata
        if not answer.metadata:
            answer.metadata = {}
        answer.metadata["processor"] = "QueryProcessor"
        
        return answer
    
    def _assemble_response(
        self,
        answer: Answer,
        retrieval_results: List[RetrievalResult],
        query: str
    ) -> Answer:
        """
        Assemble the final response with metadata.
        
        Args:
            answer: Generated answer
            retrieval_results: List of retrieval results
            query: Original query
            
        Returns:
            Final answer with complete metadata
        """
        # Add query processing metadata
        answer.metadata.update({
            "query": query,
            "retrieved_docs": len(retrieval_results),
            "retrieval_scores": [r.score for r in retrieval_results],
            "retrieval_methods": [r.retrieval_method for r in retrieval_results],
            "query_processor_config": {
                "default_k": self.default_k,
                "min_confidence": self.min_confidence
            }
        })
        
        # Ensure sources are from the retrieved documents
        if not answer.sources and retrieval_results:
            answer.sources = [r.document for r in retrieval_results[:3]]
        
        return answer
    
    def explain_query(self, query: str) -> Dict[str, Any]:
        """
        Explain how a query would be processed.
        
        This method provides transparency into the query processing pipeline.
        
        Args:
            query: Query to explain
            
        Returns:
            Dictionary with query processing plan
        """
        return {
            "original_query": query,
            "analyzed_query": self._analyze_query(query),
            "retrieval_k": self.default_k,
            "min_confidence": self.min_confidence,
            "processing_steps": [
                "1. Query analysis (currently passthrough)",
                "2. Document retrieval using configured retriever",
                "3. Context selection with confidence filtering",
                "4. Answer generation using configured generator",
                "5. Response assembly with metadata"
            ],
            "config": self.config
        }
    
    def __str__(self) -> str:
        """String representation of the query processor."""
        return f"QueryProcessor(retriever={type(self.retriever).__name__}, generator={type(self.generator).__name__})"
    
    def __repr__(self) -> str:
        """Detailed representation of the query processor."""
        return (f"QueryProcessor(retriever={repr(self.retriever)}, "
                f"generator={repr(self.generator)}, "
                f"config={self.config})")