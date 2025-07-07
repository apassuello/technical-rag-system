"""
RAG Pipeline implementation with dependency injection.

This module provides the main RAGPipeline class that orchestrates all components
using dependency injection and configuration-driven initialization.
"""

import logging
from typing import List, Optional, Dict, Any
from pathlib import Path

from .interfaces import (
    Document, 
    RetrievalResult, 
    Answer, 
    DocumentProcessor, 
    Embedder, 
    VectorStore, 
    Retriever, 
    AnswerGenerator
)
from .config import ConfigManager, PipelineConfig
from .registry import ComponentRegistry

logger = logging.getLogger(__name__)


class RAGPipeline:
    """
    Modular RAG pipeline with dependency injection.
    
    This class orchestrates all RAG components using a configuration-driven
    approach with dependency injection. Components are initialized based on
    configuration and can be easily swapped without code changes.
    
    Features:
    - Configuration-driven component initialization
    - Dependency injection for all components
    - Comprehensive error handling and logging
    - Performance monitoring capabilities
    - Easy component access for testing/debugging
    
    Example:
        pipeline = RAGPipeline(Path("config/default.yaml"))
        pipeline.index_document(Path("document.pdf"))
        answer = pipeline.query("What is RISC-V?")
    """
    
    def __init__(self, config_path: Path):
        """
        Initialize the RAG pipeline with configuration.
        
        Args:
            config_path: Path to YAML configuration file
            
        Raises:
            FileNotFoundError: If configuration file doesn't exist
            ValueError: If configuration is invalid
        """
        # Convert string to Path if needed
        if isinstance(config_path, str):
            config_path = Path(config_path)
            
        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
        self.config_path = config_path
        self.config_manager = ConfigManager(config_path)
        self.config = self.config_manager.config
        
        # Component storage
        self._components: Dict[str, Any] = {}
        self._initialized = False
        
        # Initialize all components
        self._initialize_components()
        
        logger.info(f"RAG pipeline initialized with config: {config_path}")
    
    def _initialize_components(self) -> None:
        """
        Initialize all components from configuration.
        
        This method creates all components in the correct order, handling
        dependencies between components.
        
        Raises:
            ValueError: If component type is not registered
            RuntimeError: If component initialization fails
        """
        try:
            # Create document processor
            logger.debug("Initializing document processor...")
            proc_config = self.config.document_processor
            self._components['processor'] = ComponentRegistry.create_processor(
                proc_config.type,
                **proc_config.config
            )
            
            # Create embedder
            logger.debug("Initializing embedder...")
            emb_config = self.config.embedder
            self._components['embedder'] = ComponentRegistry.create_embedder(
                emb_config.type,
                **emb_config.config
            )
            
            # Create vector store
            logger.debug("Initializing vector store...")
            vs_config = self.config.vector_store
            self._components['vector_store'] = ComponentRegistry.create_vector_store(
                vs_config.type,
                **vs_config.config
            )
            
            # Create retriever (depends on vector store and embedder)
            logger.debug("Initializing retriever...")
            ret_config = self.config.retriever
            self._components['retriever'] = ComponentRegistry.create_retriever(
                ret_config.type,
                vector_store=self._components['vector_store'],
                embedder=self._components['embedder'],
                **ret_config.config
            )
            
            # Create answer generator
            logger.debug("Initializing answer generator...")
            gen_config = self.config.answer_generator
            self._components['generator'] = ComponentRegistry.create_generator(
                gen_config.type,
                **gen_config.config
            )
            
            self._initialized = True
            logger.info("All components initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize components: {str(e)}")
            raise RuntimeError(f"Component initialization failed: {str(e)}") from e
    
    def index_document(self, file_path: Path) -> int:
        """
        Index a document and return number of chunks created.
        
        This method processes a document through the entire pipeline:
        1. Process document into chunks
        2. Generate embeddings for chunks
        3. Store chunks and embeddings in vector store
        
        Args:
            file_path: Path to document file
            
        Returns:
            Number of document chunks created
            
        Raises:
            ValueError: If file format is not supported
            RuntimeError: If indexing fails
        """
        if not self._initialized:
            raise RuntimeError("Pipeline not initialized")
        
        if not file_path.exists():
            raise FileNotFoundError(f"Document file not found: {file_path}")
        
        logger.info(f"Indexing document: {file_path}")
        
        try:
            # Process document into chunks
            processor: DocumentProcessor = self._components['processor']
            documents = processor.process(file_path)
            
            if not documents:
                logger.warning(f"No documents created from {file_path}")
                return 0
            
            logger.debug(f"Created {len(documents)} document chunks")
            
            # Generate embeddings
            embedder: Embedder = self._components['embedder']
            texts = [doc.content for doc in documents]
            embeddings = embedder.embed(texts)
            
            # Add embeddings to documents
            for doc, embedding in zip(documents, embeddings):
                doc.embedding = embedding
            
            # Store in vector store
            vector_store: VectorStore = self._components['vector_store']
            vector_store.add(documents)
            
            # Also index in retriever if it supports it
            retriever = self._components['retriever']
            if hasattr(retriever, 'index_documents'):
                retriever.index_documents(documents)
            
            logger.info(f"Successfully indexed {len(documents)} chunks from {file_path}")
            return len(documents)
            
        except Exception as e:
            logger.error(f"Failed to index document {file_path}: {str(e)}")
            raise RuntimeError(f"Document indexing failed: {str(e)}") from e
    
    def index_documents(self, file_paths: List[Path]) -> Dict[str, int]:
        """
        Index multiple documents and return chunk counts.
        
        Args:
            file_paths: List of paths to document files
            
        Returns:
            Dictionary mapping file paths to chunk counts
            
        Raises:
            RuntimeError: If batch indexing fails
        """
        if not self._initialized:
            raise RuntimeError("Pipeline not initialized")
        
        results = {}
        failed_files = []
        
        logger.info(f"Indexing {len(file_paths)} documents...")
        
        for file_path in file_paths:
            try:
                chunk_count = self.index_document(file_path)
                results[str(file_path)] = chunk_count
            except Exception as e:
                logger.error(f"Failed to index {file_path}: {str(e)}")
                failed_files.append(str(file_path))
                results[str(file_path)] = 0
        
        if failed_files:
            logger.warning(f"Failed to index {len(failed_files)} files: {failed_files}")
        
        total_chunks = sum(results.values())
        logger.info(f"Batch indexing complete: {total_chunks} total chunks from {len(file_paths)} files")
        
        return results
    
    def query(self, query: str, k: int = 5) -> Answer:
        """
        Query the pipeline and return an answer.
        
        This method performs the complete RAG workflow:
        1. Retrieve relevant documents
        2. Generate answer from query and context
        
        Args:
            query: User query string
            k: Number of documents to retrieve for context
            
        Returns:
            Answer object with generated text, sources, and metadata
            
        Raises:
            ValueError: If query is empty or k is invalid
            RuntimeError: If query processing fails
        """
        if not self._initialized:
            raise RuntimeError("Pipeline not initialized")
        
        if not query.strip():
            raise ValueError("Query cannot be empty")
        
        if k <= 0:
            raise ValueError("k must be positive")
        
        logger.info(f"Processing query: {query[:100]}...")
        
        try:
            # Retrieve relevant documents
            retriever: Retriever = self._components['retriever']
            results = retriever.retrieve(query, k)
            
            if not results:
                logger.warning(f"No relevant documents found for query: {query}")
                # Return empty answer
                return Answer(
                    text="No relevant information found for your query.",
                    sources=[],
                    confidence=0.0,
                    metadata={
                        "query": query,
                        "retrieved_docs": 0,
                        "pipeline_config": str(self.config_path)
                    }
                )
            
            logger.debug(f"Retrieved {len(results)} relevant documents")
            
            # Extract documents from results
            context_docs = [r.document for r in results]
            
            # Generate answer
            generator: AnswerGenerator = self._components['generator']
            answer = generator.generate(query, context_docs)
            
            # Add pipeline metadata
            answer.metadata.update({
                "query": query,
                "retrieved_docs": len(results),
                "retrieval_scores": [r.score for r in results],
                "retrieval_methods": [r.retrieval_method for r in results],
                "pipeline_config": str(self.config_path)
            })
            
            logger.info(f"Generated answer with confidence: {answer.confidence}")
            return answer
            
        except Exception as e:
            logger.error(f"Failed to process query: {str(e)}")
            raise RuntimeError(f"Query processing failed: {str(e)}") from e
    
    def get_component(self, name: str) -> Optional[Any]:
        """
        Get a specific component for testing/debugging.
        
        Args:
            name: Component name ('processor', 'embedder', 'vector_store', 'retriever', 'generator')
            
        Returns:
            Component instance or None if not found
        """
        return self._components.get(name)
    
    def get_pipeline_info(self) -> Dict[str, Any]:
        """
        Get information about the current pipeline configuration.
        
        Returns:
            Dictionary with pipeline configuration and status
        """
        info = {
            "config_path": str(self.config_path),
            "initialized": self._initialized,
            "components": {}
        }
        
        if self._initialized:
            # Get component information
            for name, component in self._components.items():
                component_info = {
                    "type": type(component).__name__,
                    "module": type(component).__module__
                }
                
                # Add component-specific info if available
                if hasattr(component, 'get_configuration'):
                    component_info["config"] = component.get_configuration()
                elif hasattr(component, 'get_model_info'):
                    component_info["config"] = component.get_model_info()
                elif hasattr(component, 'get_index_info'):
                    component_info["config"] = component.get_index_info()
                
                info["components"][name] = component_info
        
        return info
    
    def clear_index(self) -> None:
        """
        Clear all indexed documents from the vector store.
        
        This method resets the vector store to its initial state.
        """
        if not self._initialized:
            raise RuntimeError("Pipeline not initialized")
        
        vector_store: VectorStore = self._components['vector_store']
        vector_store.clear()
        
        logger.info("Pipeline index cleared")
    
    def reload_config(self) -> None:
        """
        Reload configuration and reinitialize components.
        
        This method allows for dynamic configuration changes without
        creating a new pipeline instance.
        
        Raises:
            RuntimeError: If reinitialization fails
        """
        logger.info("Reloading pipeline configuration...")
        
        try:
            # Reload configuration
            self.config_manager = ConfigManager(self.config_path)
            self.config = self.config_manager.config
            
            # Clear existing components
            self._components.clear()
            self._initialized = False
            
            # Reinitialize components
            self._initialize_components()
            
            logger.info("Pipeline configuration reloaded successfully")
            
        except Exception as e:
            logger.error(f"Failed to reload configuration: {str(e)}")
            raise RuntimeError(f"Configuration reload failed: {str(e)}") from e
    
    def validate_configuration(self) -> List[str]:
        """
        Validate the current configuration.
        
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        try:
            # Validate that all component types are registered
            component_types = {
                'processor': self.config.document_processor.type,
                'embedder': self.config.embedder.type,
                'vector_store': self.config.vector_store.type,
                'retriever': self.config.retriever.type,
                'generator': self.config.answer_generator.type
            }
            
            for comp_type, comp_name in component_types.items():
                if not ComponentRegistry.is_registered(comp_type, comp_name):
                    errors.append(f"Component '{comp_name}' not registered for type '{comp_type}'")
            
            # Validate configuration compatibility
            # (Add more validation logic as needed)
            
        except Exception as e:
            errors.append(f"Configuration validation error: {str(e)}")
        
        return errors
    
    def __str__(self) -> str:
        """String representation of the pipeline."""
        return f"RAGPipeline(config={self.config_path}, initialized={self._initialized})"
    
    def __repr__(self) -> str:
        """Detailed representation of the pipeline."""
        return (f"RAGPipeline(config_path={self.config_path}, "
                f"initialized={self._initialized}, "
                f"components={list(self._components.keys())})")