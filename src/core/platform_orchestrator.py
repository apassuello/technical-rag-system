"""
Platform Orchestrator - System lifecycle and platform integration.

This component manages the system lifecycle, component initialization,
and platform-specific adaptations with factory-based architecture.
It uses ComponentFactory for direct component instantiation with optimal performance.
"""

import logging
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from .component_factory import ComponentFactory
from .config import ConfigManager
from .interfaces import (
    Answer,
    ComponentMetrics,
    Document,
    HealthStatus,
)
from .platform_services import (
    ComponentHealthServiceImpl,
    ConfigurationServiceImpl,
    SystemAnalyticsServiceImpl,
)

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
    
    This class uses the ComponentFactory for direct component instantiation
    during Phase 3, providing improved performance while maintaining backward compatibility.
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
        
        # Phase 2: Track architecture type for compatibility
        self._using_unified_retriever = False
        self._retriever_type: Optional[str] = None
        
        # Initialize system services
        self.health_service = ComponentHealthServiceImpl()
        self.analytics_service = SystemAnalyticsServiceImpl()
        self.configuration_service = ConfigurationServiceImpl(self.config_manager)
        
        # Monitoring adapter for external systems
        self._monitoring_adapter = None  # Will be set based on configuration
        
        # Initialize system
        self._initialize_system()
        
        logger.info(f"Platform Orchestrator initialized with config: {config_path}")
    
    def _initialize_system(self) -> None:
        """
        Initialize all system components with Phase 3 direct wiring.
        
        This method uses ComponentFactory for direct component instantiation,
        supporting both legacy and unified architectures with improved performance.
        """
        logger.info("Initializing RAG system components...")
        
        try:
            # Create document processor using factory
            proc_config = self.config.document_processor
            self._components['document_processor'] = ComponentFactory.create_processor(
                proc_config.type,
                **proc_config.config
            )
            logger.debug(f"Document processor initialized: {proc_config.type}")
            
            # Create embedder using factory with retry logic
            emb_config = self.config.embedder
            max_retries = 2
            for attempt in range(max_retries + 1):
                try:
                    self._components['embedder'] = ComponentFactory.create_embedder(
                        emb_config.type,
                        **emb_config.config
                    )
                    logger.debug(f"Embedder initialized: {emb_config.type}")
                    break
                except Exception as e:
                    if attempt < max_retries:
                        logger.warning(f"Embedder initialization failed (attempt {attempt + 1}): {str(e)}, retrying...")
                        time.sleep(0.01)  # Brief delay before retry
                        continue
                    else:
                        raise
            
            # Phase 3: Architecture detection with factory-based instantiation
            ret_config = self.config.retriever
            if ret_config.type in ["unified", "modular_unified"]:
                # Phase 2: Use unified retriever (no separate vector store needed)
                self._components['retriever'] = ComponentFactory.create_retriever(
                    ret_config.type,
                    embedder=self._components['embedder'],
                    **ret_config.config
                )
                logger.info(f"Phase 3: Unified retriever initialized: {ret_config.type}")
                
                # Mark that we're using unified architecture
                self._using_unified_retriever = True
                self._retriever_type = ret_config.type
                
            else:
                # Phase 1: Legacy architecture with separate vector store and retriever
                vs_config = self.config.vector_store
                if vs_config is None:
                    raise RuntimeError("Legacy architecture requires vector_store configuration")
                
                self._components['vector_store'] = ComponentFactory.create_vector_store(
                    vs_config.type,
                    **vs_config.config
                )
                logger.debug(f"Vector store initialized: {vs_config.type}")
                
                self._components['retriever'] = ComponentFactory.create_retriever(
                    ret_config.type,
                    vector_store=self._components['vector_store'],
                    embedder=self._components['embedder'],
                    **ret_config.config
                )
                logger.debug(f"Retriever initialized: {ret_config.type}")
                
                # Mark that we're using legacy architecture
                self._using_unified_retriever = False
                self._retriever_type = ret_config.type
            
            # Create answer generator using factory
            gen_config = self.config.answer_generator
            self._components['answer_generator'] = ComponentFactory.create_generator(
                gen_config.type,
                config=gen_config.config
            )
            logger.debug(f"Answer generator initialized: {gen_config.type}")
            
            # Connect embedder to answer generator for semantic confidence scoring
            if hasattr(self._components['answer_generator'], 'set_embedder'):
                self._components['answer_generator'].set_embedder(self._components['embedder'])
            
            # Create query processor if configured
            if hasattr(self.config, 'query_processor') and self.config.query_processor:
                qp_config = self.config.query_processor
                # Handle both dict and config object formats
                if isinstance(qp_config, dict):
                    qp_type = qp_config.get('type', 'modular')
                    qp_config_dict = qp_config.get('config', {})
                else:
                    qp_type = qp_config.type
                    qp_config_dict = qp_config.config

                if qp_type in ('intelligent', 'epic5_intelligent'):
                    self._components['query_processor'] = self._initialize_intelligent_processor(
                        qp_config_dict
                    )
                else:
                    self._components['query_processor'] = ComponentFactory.create_query_processor(
                        qp_type,
                        retriever=self._components.get('retriever'),
                        generator=self._components.get('answer_generator'),
                        **qp_config_dict
                    )
                logger.debug(f"Query processor initialized: {qp_type}")
            else:
                # For backward compatibility, create a default query processor with proper config
                self._components['query_processor'] = ComponentFactory.create_query_processor(
                    "modular",
                    retriever=self._components.get('retriever'),
                    generator=self._components.get('answer_generator'),
                )
                logger.debug("Default query processor initialized")
            
            # Register all components with health service
            for component_name, component in self._components.items():
                self.health_service.monitor_component_health(component)
            
            self._initialized = True
            logger.info("System initialization complete")
            
        except Exception as e:
            logger.error(f"Failed to initialize components: {str(e)}")
            raise RuntimeError(f"System initialization failed: {str(e)}") from e
    
    def _initialize_intelligent_processor(self, qp_config_dict: Dict[str, Any]) -> Any:
        """
        Assemble and create an IntelligentQueryProcessor (Epic 5).

        Builds the full agent stack: tools, memory, LLM, ReActAgent,
        QueryAnalyzer, then passes them to the factory.

        Args:
            qp_config_dict: Configuration dict from the query_processor config section.
                Expected keys: agent (dict), tools (list), memory (dict), processor (dict).

        Returns:
            Configured IntelligentQueryProcessor instance.
        """
        from src.components.query_processors.agents.models import (
            AgentConfig,
            ProcessorConfig,
        )
        from src.components.query_processors.agents.planning.query_analyzer import (
            QueryAnalyzer,
        )

        retriever = self._components['retriever']
        generator = self._components['answer_generator']

        # --- Agent config ---
        agent_cfg = qp_config_dict.get('agent', {})
        llm_cfg = agent_cfg.get('llm', {})
        exec_cfg = agent_cfg.get('executor', {})

        agent_config = AgentConfig(
            llm_provider=llm_cfg.get('provider', 'openai'),
            llm_model=llm_cfg.get('model', 'gpt-4-turbo'),
            temperature=llm_cfg.get('temperature', 0.7),
            max_tokens=llm_cfg.get('max_tokens', 2048),
            max_iterations=exec_cfg.get('max_iterations', 10),
            max_execution_time=exec_cfg.get('max_execution_time', 300),
            early_stopping=exec_cfg.get('early_stopping_method', 'force'),
            verbose=exec_cfg.get('verbose', False),
            use_technical_prompts=agent_cfg.get('use_technical_prompts', True),
            include_few_shot=agent_cfg.get('include_few_shot', True),
            agent_role=agent_cfg.get('agent_role', 'technical_docs'),
        )

        # --- LLM ---
        llm = self._create_agent_llm(agent_config)

        # --- Tools ---
        tool_names = qp_config_dict.get('tools', ['calculator', 'code_analyzer', 'document_search'])
        tools = []
        for name in tool_names:
            tool = ComponentFactory.create_tool(name)
            # Inject retriever into document_search tool
            if name == 'document_search' and hasattr(tool, 'set_retriever'):
                tool.set_retriever(retriever)
            tools.append(tool)

        # --- Memory ---
        mem_cfg = qp_config_dict.get('memory', {})
        conv_cfg = mem_cfg.get('conversation', {})
        conversation_memory = ComponentFactory.create_memory(
            'conversation',
            max_messages=conv_cfg.get('max_messages', 50),
        )
        working_memory = ComponentFactory.create_memory('working')

        # --- ReActAgent ---
        from src.components.query_processors.agents.react_agent import ReActAgent

        agent = ReActAgent(
            llm=llm,
            tools=tools,
            memory=conversation_memory,
            config=agent_config,
            working_memory=working_memory,
        )

        # --- QueryAnalyzer ---
        query_analyzer = QueryAnalyzer()

        # --- ProcessorConfig ---
        proc_cfg = qp_config_dict.get('processor', {})
        processor_config = ProcessorConfig(
            use_agent_by_default=proc_cfg.get('use_agent_by_default', False),
            complexity_threshold=proc_cfg.get('complexity_threshold', 0.7),
            max_agent_cost=proc_cfg.get('max_agent_cost', 0.10),
            enable_planning=proc_cfg.get('enable_planning', False),
            enable_parallel_execution=proc_cfg.get('enable_parallel_execution', False),
        )

        logger.info(
            f"Assembling IntelligentQueryProcessor: "
            f"{len(tools)} tools, threshold={processor_config.complexity_threshold}"
        )

        return ComponentFactory.create_query_processor(
            'intelligent',
            retriever=retriever,
            generator=generator,
            agent=agent,
            query_analyzer=query_analyzer,
            config=processor_config,
        )

    @staticmethod
    def _create_agent_llm(agent_config: Any) -> Any:
        """
        Create a LangChain LLM instance from AgentConfig.

        Attempts to import the appropriate Chat model class.
        Falls back to a no-op mock if neither provider library is installed.
        """
        if agent_config.llm_provider == 'openai':
            try:
                from langchain_openai import ChatOpenAI
                return ChatOpenAI(  # type: ignore[call-arg]  # Pydantic model fields invisible to mypy
                    model=agent_config.llm_model,
                    temperature=agent_config.temperature,
                    max_tokens=agent_config.max_tokens,
                )
            except ImportError:
                logger.warning("langchain_openai not installed, agent LLM unavailable")
        elif agent_config.llm_provider == 'anthropic':
            try:
                from langchain_anthropic import ChatAnthropic
                return ChatAnthropic(  # type: ignore[call-arg]  # Pydantic model fields invisible to mypy
                    model=agent_config.llm_model,
                    temperature=agent_config.temperature,
                    max_tokens=agent_config.max_tokens,
                )
            except ImportError:
                logger.warning("langchain_anthropic not installed, agent LLM unavailable")

        raise RuntimeError(
            f"Cannot create LLM for provider '{agent_config.llm_provider}'. "
            f"Install langchain_openai or langchain_anthropic."
        )

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

            # Validate embeddings
            if embeddings is None:
                raise ValueError("Embedder returned None instead of embeddings")
            if not isinstance(embeddings, list):
                raise TypeError(f"Embeddings must be a list, got {type(embeddings)}")
            if len(embeddings) != len(documents):
                raise ValueError(f"Embedding count ({len(embeddings)}) does not match document count ({len(documents)})")

            # Add embeddings to documents
            for doc, embedding in zip(documents, embeddings):
                doc.embedding = embedding
            
            # Phase 2: Handle unified vs legacy architecture
            retriever = self._components['retriever']
            
            if self._using_unified_retriever:
                # Phase 2: Direct indexing in unified retriever
                retriever.index_documents(documents)
                logger.debug("Indexed documents in unified retriever")
            else:
                # Phase 1: Legacy architecture - store in vector store first
                vector_store = self._components['vector_store']
                vector_store.add(documents)
                
                # Then index in retriever if it supports it
                if hasattr(retriever, 'index_documents'):
                    retriever.index_documents(documents)
                
                logger.debug("Indexed documents in legacy vector store + retriever")
            
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
                # Don't include failed files in results dictionary
        
        if failed_files:
            logger.warning(f"Failed to process {len(failed_files)} files: {failed_files}")
        
        total_chunks = sum(results.values())
        logger.info(f"Batch processing complete: {total_chunks} total chunks from {len(file_paths)} files")
        
        return results
    
    def index_documents(self, documents: List[Document]) -> int:
        """
        Directly index pre-created Document objects into the retrieval system.
        
        This method allows bypassing file processing when you already have
        Document objects (e.g., from testing, external processing, etc.).
        
        Args:
            documents: List of Document objects to index
            
        Returns:
            Number of documents successfully indexed
            
        Raises:
            RuntimeError: If system not initialized or indexing fails
        """
        if not self._initialized:
            raise RuntimeError("System not initialized")
        
        if not documents:
            logger.warning("No documents provided for indexing")
            return 0
        
        logger.info(f"Indexing {len(documents)} pre-created documents...")
        
        try:
            # Generate embeddings for documents that don't have them
            embedder = self._components['embedder']
            documents_needing_embeddings = [doc for doc in documents if doc.embedding is None]
            
            if documents_needing_embeddings:
                logger.debug(f"Generating embeddings for {len(documents_needing_embeddings)} documents")
                texts = [doc.content for doc in documents_needing_embeddings]
                embeddings = embedder.embed(texts)
                
                # Add embeddings to documents
                for doc, embedding in zip(documents_needing_embeddings, embeddings):
                    doc.embedding = embedding
            
            # Index documents based on architecture
            retriever = self._components['retriever']
            
            if self._using_unified_retriever:
                # Phase 4: Direct indexing in unified retriever
                retriever.index_documents(documents)
                logger.debug("Indexed documents in unified retriever")
            else:
                # Legacy architecture - store in vector store first
                vector_store = self._components['vector_store']
                vector_store.add(documents)
                
                # Then index in retriever if it supports it
                if hasattr(retriever, 'index_documents'):
                    retriever.index_documents(documents)
                
                logger.debug("Indexed documents in legacy vector store + retriever")
            
            logger.info(f"Successfully indexed {len(documents)} documents")
            return len(documents)
            
        except Exception as e:
            logger.error(f"Failed to index documents: {str(e)}")
            raise RuntimeError(f"Document indexing failed: {str(e)}") from e
    
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
                # Still call generator with empty context to allow it to handle the case
                generator = self._components['answer_generator']
                answer = generator.generate(query, [])
                # Ensure metadata includes retrieval info
                if answer.metadata is None:
                    answer.metadata = {}
                answer.metadata.update({
                    "query": query,
                    "retrieved_docs": 0,
                    "orchestrator": "PlatformOrchestrator"
                })
                return answer
            
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
            "status": "healthy" if self._initialized else "unhealthy",
            "initialized": self._initialized,
            "architecture": self._determine_system_architecture(),
            "config_path": str(self.config_path),
            "components": {},
            "platform": self.config.global_settings.get("platform", {})
        }
        
        # Phase 4: Enhanced factory and performance monitoring
        try:
            from .component_factory import ComponentFactory
            health["factory_info"] = ComponentFactory.get_available_components()
            health["performance_metrics"] = ComponentFactory.get_performance_metrics()
            health["cache_stats"] = ComponentFactory.get_cache_stats()
        except ImportError:
            pass  # Factory not available
        
        if self._initialized:
            # Get component status
            for name, component in self._components.items():
                health_checks: Dict[str, Any] = {}
                component_info: Dict[str, Any] = {
                    "type": type(component).__name__,
                    "module": type(component).__module__,
                    "healthy": True,  # Will be updated by health checks
                    "factory_managed": True,  # Phase 3: All components now factory-managed
                    "created_at": getattr(component, '_created_at', None),
                    "last_used": getattr(component, '_last_used', None),
                    "health_checks": health_checks
                }

                # Phase 4: Enhanced component health validation
                component_info["healthy"] = self._validate_component_health(component, health_checks)
                
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
    
    def _validate_component_health(self, component: Any, health_checks: Dict[str, Any]) -> bool:
        """
        Validate component health with comprehensive checks.
        
        Args:
            component: Component to validate
            health_checks: Dictionary to store health check results
            
        Returns:
            True if component is healthy, False otherwise
        """
        overall_healthy = True
        
        # Check 1: Required methods exist
        required_methods = {
            "DocumentProcessor": ["process"],
            "Embedder": ["embed", "embedding_dim"],
            "VectorStore": ["add", "search"],
            "Retriever": ["retrieve"],
            "AnswerGenerator": ["generate"]
        }
        
        component_type = type(component).__name__
        if component_type in required_methods:
            missing_methods = []
            for method in required_methods[component_type]:
                if not hasattr(component, method):
                    missing_methods.append(method)
                    overall_healthy = False
            
            health_checks["required_methods"] = {
                "passed": len(missing_methods) == 0,
                "missing": missing_methods
            }
        
        # Check 2: Component-specific health validation
        if hasattr(component, 'health_check'):
            try:
                component_health = component.health_check()
                health_checks["component_specific"] = {
                    "passed": component_health.get("healthy", True),
                    "details": component_health
                }
                if not component_health.get("healthy", True):
                    overall_healthy = False
            except Exception as e:
                health_checks["component_specific"] = {
                    "passed": False,
                    "error": str(e)
                }
                overall_healthy = False
        
        # Check 3: Memory usage validation (if available)
        try:
            import os

            import psutil
            process = psutil.Process(os.getpid())
            memory_mb = process.memory_info().rss / 1024 / 1024
            health_checks["memory"] = {
                "current_mb": round(memory_mb, 1),
                "within_limits": memory_mb < 2048  # 2GB limit
            }
            if memory_mb > 2048:
                overall_healthy = False
        except ImportError:
            health_checks["memory"] = {"available": False}
        
        # Check 4: Configuration validation
        if hasattr(component, 'get_configuration'):
            try:
                config = component.get_configuration()
                health_checks["configuration"] = {
                    "passed": isinstance(config, dict),
                    "config_size": len(config) if isinstance(config, dict) else 0
                }
            except Exception as e:
                health_checks["configuration"] = {
                    "passed": False,
                    "error": str(e)
                }
                overall_healthy = False
        
        return overall_healthy
    
    def _determine_system_architecture(self) -> str:
        """
        Determine the overall system architecture based on component types.
        
        Returns:
            String describing the current system architecture
        """
        if not self._initialized:
            return "uninitialized"
        
        # Check component types to determine architecture level
        component_types = {}
        for name, component in self._components.items():
            component_types[name] = type(component).__name__
        
        # Determine architecture based on modular component usage
        modular_components = 0
        total_components = 0
        
        # Check each major component for modular architecture
        if 'document_processor' in component_types:
            total_components += 1
            if component_types['document_processor'] == 'ModularDocumentProcessor':
                modular_components += 1
        
        if 'embedder' in component_types:
            total_components += 1
            if component_types['embedder'] == 'ModularEmbedder':
                modular_components += 1
        
        if 'retriever' in component_types:
            total_components += 1
            if component_types['retriever'] in ['ModularUnifiedRetriever']:
                modular_components += 1
        
        if 'answer_generator' in component_types:
            total_components += 1
            if component_types['answer_generator'] == 'AnswerGenerator':  # This is already modular
                modular_components += 1
        
        # Determine architecture level
        if total_components == 0:
            return "no_components"
        
        modular_percentage = modular_components / total_components
        
        if modular_percentage >= 1.0:
            return "modular"  # All components are modular
        elif modular_percentage >= 0.75:
            return "mostly_modular"  # 3/4 or more components are modular
        elif modular_percentage >= 0.5:
            return "hybrid"  # Half of components are modular
        elif self._using_unified_retriever:
            return "unified"  # Using unified retriever but not fully modular
        else:
            return "legacy"  # Legacy architecture
    
    def get_component(self, name: str) -> Optional[Any]:
        """
        Get a specific component for testing/debugging.
        
        Args:
            name: Component name
            
        Returns:
            Component instance or None if not found
        """
        return self._components.get(name)
    
    def get_config(self) -> Dict[str, Any]:
        """
        Get the current system configuration.

        Returns:
            Configuration as dictionary
        """
        if hasattr(self.config, 'model_dump'):
            # Pydantic v2
            return self.config.model_dump()
        elif hasattr(self.config, 'dict'):
            # Pydantic v1
            return self.config.dict()
        else:
            # Fallback: convert via vars() for non-Pydantic config objects
            return dict(vars(self.config))
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        Get system metrics.
        
        Returns:
            Dictionary with system metrics
        """
        return self.analytics_service.collect_system_metrics()
    
    def reload_configuration(self, new_config_path: Path) -> None:
        """
        Reload configuration from a new config file.
        
        Args:
            new_config_path: Path to new configuration file
        """
        # Update the config path and reload
        self.config_path = new_config_path
        self.config_manager = ConfigManager(new_config_path)
        self.config = self.config_manager.config
        
        # Notify configuration service
        self.configuration_service.reload_configuration()
    
    def clear_index(self) -> None:
        """
        Clear all indexed documents from the system.
        
        This method resets the retrieval system to its initial state,
        handling both unified and legacy architectures.
        """
        if not self._initialized:
            raise RuntimeError("System not initialized")
        
        if self._using_unified_retriever:
            # Phase 2: Unified architecture - clear retriever directly
            retriever = self._components['retriever']
            if hasattr(retriever, 'clear_index'):
                retriever.clear_index()
            elif hasattr(retriever, 'clear'):
                retriever.clear()
            else:
                logger.warning(f"Retriever {type(retriever).__name__} does not support clearing")
        else:
            # Phase 1: Legacy architecture - clear vector store and retriever
            if 'vector_store' in self._components:
                vector_store = self._components['vector_store']
                vector_store.clear()

            # Also clear retriever if it has separate state
            retriever = self._components['retriever']
            if hasattr(retriever, 'clear_index'):
                retriever.clear_index()
            elif hasattr(retriever, 'clear'):
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
            # Create configuration dict for factory validation
            config_dict = {
                'document_processor': {
                    'type': self.config.document_processor.type,
                    'config': self.config.document_processor.config
                },
                'embedder': {
                    'type': self.config.embedder.type,
                    'config': self.config.embedder.config
                },
                'retriever': {
                    'type': self.config.retriever.type,
                    'config': self.config.retriever.config
                },
                'answer_generator': {
                    'type': self.config.answer_generator.type,
                    'config': self.config.answer_generator.config
                }
            }
            
            # Add vector_store if present (optional for unified architecture)
            if self.config.vector_store is not None:
                config_dict['vector_store'] = {
                    'type': self.config.vector_store.type,
                    'config': self.config.vector_store.config
                }
            
            # Use factory validation
            errors = ComponentFactory.validate_configuration(config_dict)
            
        except Exception as e:
            errors.append(f"Configuration validation error: {str(e)}")
        
        return errors
    
    # System Service Access Methods
    
    def check_component_health(self, component_or_name: Any) -> HealthStatus:
        """Check the health of a component by name or object reference.

        Args:
            component_or_name: Component name (str) or component instance

        Returns:
            HealthStatus object with health information

        Raises:
            KeyError: If component name not found
        """
        if isinstance(component_or_name, str):
            if component_or_name not in self._components:
                raise KeyError(f"Component '{component_or_name}' not found")
            component = self._components[component_or_name]
        else:
            component = component_or_name
        return self.health_service.check_component_health(component)
    
    def get_system_health_summary(self) -> Dict[str, Any]:
        """Get a comprehensive system health summary.
        
        Returns:
            Dictionary with system health information
        """
        return self.health_service.get_system_health_summary()
    
    def report_component_failure(self, component_name: str, error: Exception) -> None:
        """Report a failure for a specific component.
        
        Args:
            component_name: Name of the component that failed
            error: Exception that occurred
            
        Raises:
            KeyError: If component not found
        """
        if component_name not in self._components:
            raise KeyError(f"Component '{component_name}' not found")
        
        component = self._components[component_name]
        self.health_service.report_component_failure(component, error)
    
    def collect_component_metrics(self, component_name: str) -> ComponentMetrics:
        """Collect metrics from a specific component.
        
        Args:
            component_name: Name of the component to collect metrics from
            
        Returns:
            ComponentMetrics object with collected metrics
            
        Raises:
            KeyError: If component not found
        """
        if component_name not in self._components:
            raise KeyError(f"Component '{component_name}' not found")
        
        component = self._components[component_name]
        return self.analytics_service.collect_component_metrics(component)
    
    def get_system_analytics_summary(self) -> Dict[str, Any]:
        """Get system-wide analytics summary.
        
        Returns:
            Dictionary with system analytics
        """
        return self.analytics_service.aggregate_system_metrics()
    
    def track_component_performance(self, component_or_name: Any, operation_or_metrics: Any = None, metrics: Optional[Dict[str, Any]] = None) -> None:
        """Track performance metrics for a component.

        Supports two call signatures:
          - track_component_performance(name: str, metrics: dict) -- by component name
          - track_component_performance(component, operation: str, metrics: dict) -- by object

        Args:
            component_or_name: Component name (str looked up in registry) or component instance
            operation_or_metrics: Operation string (object mode) or metrics dict (name mode)
            metrics: Metrics dict (only used in object mode)

        Raises:
            KeyError: If component name not found
        """
        if isinstance(component_or_name, str) and metrics is None:
            # Called as track_component_performance("name", metrics_dict)
            component_name = component_or_name
            if component_name not in self._components:
                raise KeyError(f"Component '{component_name}' not found")
            component = self._components[component_name]
            self.analytics_service.track_component_performance(component, operation_or_metrics)
        else:
            # Called as track_component_performance(component, operation, metrics)
            combined_metrics = {
                "operation": operation_or_metrics,
                **(metrics or {})
            }
            self.analytics_service.track_component_performance(component_or_name, combined_metrics)
    
    def generate_analytics_report(self) -> Dict[str, Any]:
        """Generate a comprehensive analytics report.
        
        Returns:
            Dictionary with analytics report
        """
        return self.analytics_service.generate_analytics_report()
    
    def get_component_configuration(self, component_name: str) -> Dict[str, Any]:
        """Get configuration for a component.
        
        Args:
            component_name: Name of the component
            
        Returns:
            Dictionary with component configuration
        """
        return self.configuration_service.get_component_config(component_name)
    
    def update_component_configuration(self, component_or_name: Any, config: Dict[str, Any]) -> None:
        """Update configuration for a component by name or object reference.

        Args:
            component_or_name: Component name (str) or component instance
            config: New configuration
        """
        if isinstance(component_or_name, str):
            component_name = component_or_name
        else:
            component_name = type(component_or_name).__name__
        self.configuration_service.update_component_config(component_name, config)
    
    def get_system_configuration(self) -> Dict[str, Any]:
        """Get the complete system configuration.
        
        Returns:
            Dictionary with system configuration
        """
        return self.configuration_service.get_system_configuration()

    def __str__(self) -> str:
        """String representation of the orchestrator."""
        return f"PlatformOrchestrator(config={self.config_path}, initialized={self._initialized})"
    
    def __repr__(self) -> str:
        """Detailed representation of the orchestrator."""
        return (f"PlatformOrchestrator(config_path={self.config_path}, "
                f"initialized={self._initialized}, "
                f"components={list(self._components.keys())})")