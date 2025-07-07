"""
Platform Orchestrator - System lifecycle and platform integration.

This component manages the system lifecycle, component initialization,
and platform-specific adaptations while maintaining backward compatibility.
It reuses all existing component implementations through the ComponentRegistry.
"""

import logging
from typing import Dict, Any, List, Optional
from pathlib import Path

from .interfaces import Document, Answer, RetrievalResult
from .config import ConfigManager, PipelineConfig
from .registry import ComponentRegistry

logger = logging.getLogger(__name__)


class PlatformOrchestrator:
    """
    Platform Orchestrator manages system lifecycle and platform integration.
    
    Responsibilities:
    - Component initialization and dependency injection
    - Configuration management
    - Platform-specific adaptations (cloud, on-premise, edge)
    - System health monitoring
    - Resource management
    - API exposure and routing
    
    This class reuses all existing component implementations through the
    ComponentRegistry during Phase 1 to maintain backward compatibility.
    """
    
    def __init__(self, config_path: Path):
        """
        Initialize platform orchestrator with configuration.
        
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
        
        # Initialize system
        self._initialize_system()
        
        logger.info(f"Platform Orchestrator initialized with config: {config_path}")
    
    def _initialize_system(self) -> None:
        """
        Initialize all system components using existing implementations.
        
        During Phase 1, this method uses the ComponentRegistry to create
        components, maintaining full backward compatibility.
        """
        logger.info("Initializing RAG system components...")
        
        try:
            # Create document processor using existing registry
            proc_config = self.config.document_processor
            self._components['document_processor'] = ComponentRegistry.create_processor(
                proc_config.type,
                **proc_config.config
            )
            logger.debug(f"Document processor initialized: {proc_config.type}")
            
            # Create embedder using existing registry
            emb_config = self.config.embedder
            self._components['embedder'] = ComponentRegistry.create_embedder(
                emb_config.type,
                **emb_config.config
            )
            logger.debug(f"Embedder initialized: {emb_config.type}")
            
            # Create vector store using existing registry
            vs_config = self.config.vector_store
            self._components['vector_store'] = ComponentRegistry.create_vector_store(
                vs_config.type,
                **vs_config.config
            )
            logger.debug(f"Vector store initialized: {vs_config.type}")
            
            # Create retriever using existing registry
            ret_config = self.config.retriever
            self._components['retriever'] = ComponentRegistry.create_retriever(
                ret_config.type,
                vector_store=self._components['vector_store'],
                embedder=self._components['embedder'],
                **ret_config.config
            )
            logger.debug(f"Retriever initialized: {ret_config.type}")
            
            # Create answer generator using existing registry
            gen_config = self.config.answer_generator
            self._components['answer_generator'] = ComponentRegistry.create_generator(
                gen_config.type,
                **gen_config.config
            )
            logger.debug(f"Answer generator initialized: {gen_config.type}")
            
            # Note: Query processor will be created in the next step
            # For now, we'll handle query processing directly
            
            self._initialized = True
            logger.info("System initialization complete")
            
        except Exception as e:
            logger.error(f"Failed to initialize components: {str(e)}")
            raise RuntimeError(f"System initialization failed: {str(e)}") from e
    
    def process_document(self, file_path: Path) -> int:
        """
        Process and index a document.
        
        This method orchestrates the document processing workflow:
        1. Process document into chunks
        2. Generate embeddings for chunks
        3. Store chunks and embeddings in vector store
        
        Args:
            file_path: Path to document file
            
        Returns:
            Number of document chunks created
            
        Raises:
            FileNotFoundError: If document file doesn't exist
            RuntimeError: If processing fails
        """
        if not self._initialized:
            raise RuntimeError("System not initialized")
        
        if not file_path.exists():
            raise FileNotFoundError(f"Document file not found: {file_path}")
        
        logger.info(f"Processing document: {file_path}")
        
        try:
            # Process document using existing component
            processor = self._components['document_processor']
            documents = processor.process(file_path)
            
            if not documents:
                logger.warning(f"No documents created from {file_path}")
                return 0
            
            logger.debug(f"Created {len(documents)} document chunks")
            
            # Generate embeddings using existing component
            embedder = self._components['embedder']
            texts = [doc.content for doc in documents]
            embeddings = embedder.embed(texts)
            
            # Add embeddings to documents
            for doc, embedding in zip(documents, embeddings):
                doc.embedding = embedding
            
            # Store in vector store using existing component
            vector_store = self._components['vector_store']
            vector_store.add(documents)
            
            # Also index in retriever if it supports it
            retriever = self._components['retriever']
            if hasattr(retriever, 'index_documents'):
                retriever.index_documents(documents)
            
            logger.info(f"Successfully indexed {len(documents)} chunks from {file_path}")
            return len(documents)
            
        except Exception as e:
            logger.error(f"Failed to process document {file_path}: {str(e)}")
            raise RuntimeError(f"Document processing failed: {str(e)}") from e
    
    def process_documents(self, file_paths: List[Path]) -> Dict[str, int]:
        """
        Process multiple documents and return chunk counts.
        
        Args:
            file_paths: List of paths to document files
            
        Returns:
            Dictionary mapping file paths to chunk counts
        """
        if not self._initialized:
            raise RuntimeError("System not initialized")
        
        results = {}
        failed_files = []
        
        logger.info(f"Processing {len(file_paths)} documents...")
        
        for file_path in file_paths:
            try:
                chunk_count = self.process_document(file_path)
                results[str(file_path)] = chunk_count
            except Exception as e:
                logger.error(f"Failed to process {file_path}: {str(e)}")
                failed_files.append(str(file_path))
                results[str(file_path)] = 0
        
        if failed_files:
            logger.warning(f"Failed to process {len(failed_files)} files: {failed_files}")
        
        total_chunks = sum(results.values())
        logger.info(f"Batch processing complete: {total_chunks} total chunks from {len(file_paths)} files")
        
        return results
    
    def process_query(self, query: str, k: int = 5) -> Answer:
        """
        Process a query and return an answer.
        
        This method orchestrates the query processing workflow:
        1. Retrieve relevant documents
        2. Generate answer from query and context
        
        Note: In Phase 1, this directly implements query processing.
        In Phase 3, this will delegate to the QueryProcessor component.
        
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
            raise RuntimeError("System not initialized")
        
        if not query.strip():
            raise ValueError("Query cannot be empty")
        
        if k <= 0:
            raise ValueError("k must be positive")
        
        logger.info(f"Processing query: {query[:100]}...")
        
        try:
            # Retrieve relevant documents using existing component
            retriever = self._components['retriever']
            results = retriever.retrieve(query, k)
            
            if not results:
                logger.warning(f"No relevant documents found for query: {query}")
                return Answer(
                    text="No relevant information found for your query.",
                    sources=[],
                    confidence=0.0,
                    metadata={
                        "query": query,
                        "retrieved_docs": 0,
                        "orchestrator": "PlatformOrchestrator"
                    }
                )
            
            logger.debug(f"Retrieved {len(results)} relevant documents")
            
            # Extract documents from results
            context_docs = [r.document for r in results]
            
            # Generate answer using existing component
            generator = self._components['answer_generator']
            answer = generator.generate(query, context_docs)
            
            # Add orchestrator metadata
            answer.metadata.update({
                "query": query,
                "retrieved_docs": len(results),
                "retrieval_scores": [r.score for r in results],
                "retrieval_methods": [r.retrieval_method for r in results],
                "orchestrator": "PlatformOrchestrator"
            })
            
            logger.info(f"Generated answer with confidence: {answer.confidence}")
            return answer
            
        except Exception as e:
            logger.error(f"Failed to process query: {str(e)}")
            raise RuntimeError(f"Query processing failed: {str(e)}") from e
    
    def get_system_health(self) -> Dict[str, Any]:
        """
        Get system health information.
        
        Returns:
            Dictionary with system health metrics and component status
        """
        health = {
            "initialized": self._initialized,
            "config_path": str(self.config_path),
            "components": {},
            "platform": self.config.global_settings.get("platform", {})
        }
        
        if self._initialized:
            # Get component status
            for name, component in self._components.items():
                component_info = {
                    "type": type(component).__name__,
                    "module": type(component).__module__,
                    "healthy": True  # Basic health check
                }
                
                # Add component-specific health info if available
                if hasattr(component, 'get_stats'):
                    try:
                        component_info["stats"] = component.get_stats()
                    except Exception as e:
                        component_info["healthy"] = False
                        component_info["error"] = str(e)
                elif hasattr(component, 'get_configuration'):
                    component_info["config"] = component.get_configuration()
                elif hasattr(component, 'get_model_info'):
                    component_info["config"] = component.get_model_info()
                
                health["components"][name] = component_info
        
        return health
    
    def get_component(self, name: str) -> Optional[Any]:
        """
        Get a specific component for testing/debugging.
        
        Args:
            name: Component name
            
        Returns:
            Component instance or None if not found
        """
        return self._components.get(name)
    
    def clear_index(self) -> None:
        """
        Clear all indexed documents from the vector store.
        
        This method resets the vector store to its initial state.
        """
        if not self._initialized:
            raise RuntimeError("System not initialized")
        
        vector_store = self._components['vector_store']
        vector_store.clear()
        
        # Also clear retriever if it has separate state
        retriever = self._components['retriever']
        if hasattr(retriever, 'clear'):
            retriever.clear()
        
        logger.info("System index cleared")
    
    def reload_config(self) -> None:
        """
        Reload configuration and reinitialize components.
        
        This method allows for dynamic configuration changes without
        creating a new orchestrator instance.
        
        Raises:
            RuntimeError: If reinitialization fails
        """
        logger.info("Reloading system configuration...")
        
        try:
            # Reload configuration
            self.config_manager = ConfigManager(self.config_path)
            self.config = self.config_manager.config
            
            # Clear existing components
            self._components.clear()
            self._initialized = False
            
            # Reinitialize components
            self._initialize_system()
            
            logger.info("System configuration reloaded successfully")
            
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
            
        except Exception as e:
            errors.append(f"Configuration validation error: {str(e)}")
        
        return errors
    
    def __str__(self) -> str:
        """String representation of the orchestrator."""
        return f"PlatformOrchestrator(config={self.config_path}, initialized={self._initialized})"
    
    def __repr__(self) -> str:
        """Detailed representation of the orchestrator."""
        return (f"PlatformOrchestrator(config_path={self.config_path}, "
                f"initialized={self._initialized}, "
                f"components={list(self._components.keys())})")