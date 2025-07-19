"""
Epic 2 Enhanced RAG System with Generation for HF Deployment.

Self-contained implementation combining the existing HF deployment RAG system
with Epic 2 advanced features: neural reranking, graph enhancement, and analytics.
"""

import time
import os
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Any
import sys

# Import existing HF deployment components
from .rag_with_generation import RAGWithGeneration
from .components.advanced_retriever import AdvancedRetriever

logger = __import__('logging').getLogger(__name__)


class Epic2RAGWithGeneration:
    """
    Epic 2 Enhanced RAG system for HF deployment.
    
    This class combines the proven HF deployment RAG system with Epic 2 features:
    - Advanced retrieval with neural reranking
    - Graph-based document relationship enhancement
    - Performance analytics and monitoring
    - Configurable feature toggles for deployment flexibility
    
    Features:
    - ✅ Neural reranking with cross-encoder models
    - ✅ Graph enhancement with entity linking
    - ✅ Hybrid search (dense + sparse + graph)
    - ✅ HuggingFace API integration (3-mode support)
    - ✅ Performance monitoring and analytics
    - ✅ Memory optimization for HF Spaces
    """
    
    def __init__(
        self,
        config_path: Optional[str] = None,
        model_name: str = "microsoft/DialoGPT-medium",
        api_token: str = None,
        temperature: float = 0.3,
        max_tokens: int = 512,
        use_ollama: bool = False,
        ollama_url: str = "http://localhost:11434",
        use_inference_providers: bool = False,
        enable_epic2_features: bool = True
    ):
        """
        Initialize Epic 2 RAG system.
        
        Args:
            config_path: Path to Epic 2 configuration file
            model_name: LLM model name
            api_token: HuggingFace API token
            temperature: Generation temperature
            max_tokens: Maximum tokens to generate
            use_ollama: Whether to use Ollama
            ollama_url: Ollama server URL
            use_inference_providers: Whether to use Inference Providers API
            enable_epic2_features: Whether to enable Epic 2 advanced features
        """
        # Load configuration
        self.config = self._load_config(config_path)
        self.enable_epic2_features = enable_epic2_features
        
        # Override config with parameters if provided
        if api_token:
            self.config.setdefault('generation', {}).setdefault('huggingface_api', {})['api_token'] = api_token
        
        # Auto-detect environment settings
        self._auto_detect_environment()
        
        # Initialize core RAG system (existing proven implementation)
        print(f"🔧 Initializing Epic 2 RAG system (Epic 2 features: {enable_epic2_features})", file=sys.stderr, flush=True)
        
        self.core_rag = RAGWithGeneration(
            model_name=model_name,
            api_token=api_token,
            temperature=temperature,
            max_tokens=max_tokens,
            use_ollama=use_ollama,
            ollama_url=ollama_url,
            use_inference_providers=use_inference_providers
        )
        
        # Initialize Epic 2 advanced retriever if enabled
        self.advanced_retriever = None
        if enable_epic2_features:
            try:
                print(f"🚀 Initializing Epic 2 advanced features...", file=sys.stderr, flush=True)
                retrieval_config = self.config.get('retrieval', {})
                self.advanced_retriever = AdvancedRetriever(retrieval_config)
                print(f"✅ Epic 2 features initialized successfully", file=sys.stderr, flush=True)
            except Exception as e:
                print(f"⚠️ Epic 2 features failed to initialize: {e}", file=sys.stderr, flush=True)
                print(f"🔄 Falling back to basic RAG system", file=sys.stderr, flush=True)
                self.enable_epic2_features = False
        
        # Analytics
        self.analytics = {
            "queries_processed": 0,
            "epic2_queries": 0,
            "basic_queries": 0,
            "total_response_time": 0.0,
            "epic2_response_time": 0.0,
            "component_performance": {
                "retrieval": 0.0,
                "neural_reranking": 0.0,
                "graph_enhancement": 0.0,
                "generation": 0.0
            }
        }
        
        print(f"🎯 Epic 2 RAG system ready! (Mode: {'Epic 2' if enable_epic2_features else 'Basic'})", file=sys.stderr, flush=True)
    
    def _load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """Load Epic 2 configuration."""
        if not config_path:
            # Use default Epic 2 config
            config_path = Path(__file__).parent.parent / "config" / "epic2_deployment.yaml"
        
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            return config
        except Exception as e:
            logger.warning(f"Failed to load config from {config_path}: {e}")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default Epic 2 configuration."""
        return {
            "retrieval": {
                "dense_weight": 0.4,
                "sparse_weight": 0.3,
                "graph_weight": 0.3,
                "rrf_k": 60,
                "reranker": {
                    "enabled": True,
                    "config": {
                        "model_name": "cross-encoder/ms-marco-MiniLM-L6-v2",
                        "max_candidates": 100,
                        "initialize_immediately": False
                    }
                },
                "graph_retrieval": {
                    "enabled": True,
                    "similarity_threshold": 0.65,
                    "use_pagerank": True
                }
            },
            "performance": {
                "lazy_component_initialization": True,
                "enable_caching": True
            }
        }
    
    def _auto_detect_environment(self):
        """Auto-detect environment and apply optimizations."""
        # Check if running in HuggingFace Spaces
        if os.getenv("SPACE_ID"):
            print(f"🌟 Detected HuggingFace Spaces environment", file=sys.stderr, flush=True)
            # Apply HF Spaces optimizations
            self.config.setdefault('performance', {}).update({
                'lazy_component_initialization': True,
                'enable_memory_optimization': True,
                'max_workers': 2
            })
        
        # Auto-detect HF API settings
        hf_token = os.getenv("HF_TOKEN") or os.getenv("HUGGINGFACE_API_TOKEN")
        if hf_token:
            use_inference_providers = os.getenv("USE_INFERENCE_PROVIDERS", "true").lower() == "true"
            self.config.setdefault('generation', {}).setdefault('huggingface_api', {}).update({
                'api_token': hf_token,
                'use_inference_providers': use_inference_providers
            })
    
    def index_document(self, file_path: Path) -> int:
        """
        Index a document using both core RAG and Epic 2 features.
        
        Args:
            file_path: Path to document to index
            
        Returns:
            Number of chunks created
        """
        start_time = time.time()
        
        # Index with core RAG system
        chunk_count = self.core_rag.index_document(file_path)
        
        # Index with Epic 2 advanced retriever if enabled
        if self.enable_epic2_features and self.advanced_retriever:
            try:
                # Convert core RAG chunks to Epic 2 format
                epic2_documents = []
                for chunk in self.core_rag.chunks:
                    epic2_documents.append({
                        'text': chunk['text'],
                        'metadata': {
                            'source': chunk.get('source', 'unknown'),
                            'page': chunk.get('page', 0),
                            'chunk_id': chunk.get('chunk_id', 0)
                        }
                    })
                
                self.advanced_retriever.index_documents(epic2_documents)
                print(f"✅ Epic 2 indexing completed", file=sys.stderr, flush=True)
                
            except Exception as e:
                logger.error(f"Epic 2 indexing failed: {e}")
        
        indexing_time = time.time() - start_time
        print(f"📊 Total indexing time: {indexing_time:.2f}s", file=sys.stderr, flush=True)
        
        return chunk_count
    
    def query_with_answer(
        self,
        question: str,
        top_k: int = 5,
        use_hybrid: bool = True,
        dense_weight: float = 0.7,
        use_fallback_llm: bool = False,
        return_context: bool = False,
        similarity_threshold: float = 0.3,
        use_epic2_features: Optional[bool] = None
    ) -> Dict[str, Any]:
        """
        Query with Epic 2 enhanced features.
        
        Args:
            question: User question
            top_k: Number of results to return
            use_hybrid: Whether to use hybrid search
            dense_weight: Weight for dense search
            use_fallback_llm: Whether to use fallback LLM
            return_context: Whether to return context
            similarity_threshold: Similarity threshold
            use_epic2_features: Override Epic 2 feature usage
            
        Returns:
            Enhanced query results with Epic 2 features
        """
        start_time = time.time()
        self.analytics["queries_processed"] += 1
        
        # Determine whether to use Epic 2 features
        use_epic2 = (use_epic2_features if use_epic2_features is not None 
                    else self.enable_epic2_features)
        
        if use_epic2 and self.advanced_retriever:
            return self._query_with_epic2_features(
                question, top_k, use_hybrid, dense_weight, 
                use_fallback_llm, return_context, similarity_threshold, start_time
            )
        else:
            return self._query_with_basic_rag(
                question, top_k, use_hybrid, dense_weight,
                use_fallback_llm, return_context, similarity_threshold, start_time
            )
    
    def _query_with_epic2_features(
        self, question: str, top_k: int, use_hybrid: bool, dense_weight: float,
        use_fallback_llm: bool, return_context: bool, similarity_threshold: float,
        start_time: float
    ) -> Dict[str, Any]:
        """Query using Epic 2 advanced features."""
        self.analytics["epic2_queries"] += 1
        
        try:
            # Step 1: Advanced retrieval with Epic 2 features
            retrieval_start = time.time()
            search_results = self.advanced_retriever.search(
                query=question,
                top_k=top_k,
                use_neural_reranking=True,
                use_graph_enhancement=True
            )
            retrieval_time = time.time() - retrieval_start
            self.analytics["component_performance"]["retrieval"] += retrieval_time
            
            if not search_results:
                return self._create_no_results_response(question, retrieval_time)
            
            # Step 2: Prepare context for generation
            context_chunks = []
            citations = []
            sources = set()
            
            for i, result in enumerate(search_results):
                chunk_info = {
                    'text': result['text'],
                    'source': result['metadata'].get('source', 'unknown'),
                    'page': result['metadata'].get('page', 0),
                    'chunk_id': result['metadata'].get('chunk_id', i),
                    'score': result['score'],
                    'epic2_enhanced': True
                }
                
                # Add Epic 2 specific information
                if 'graph_connections' in result:
                    chunk_info['graph_connections'] = result['graph_connections']
                if 'related_entities' in result:
                    chunk_info['related_entities'] = result['related_entities']
                
                context_chunks.append(chunk_info)
                
                # Create citation
                citation = {
                    'source': chunk_info['source'],
                    'page': chunk_info['page'],
                    'snippet': result['text'][:200] + "..." if len(result['text']) > 200 else result['text'],
                    'relevance': result['score'],
                    'epic2_enhanced': True
                }
                citations.append(citation)
                sources.add(chunk_info['source'])
            
            # Step 3: Generate answer
            generation_start = time.time()
            
            # Build context for generation
            context_text = "\n\n".join([
                f"Document {i+1}: {chunk['text']}"
                for i, chunk in enumerate(context_chunks)
            ])
            
            # Use core RAG's generation capability
            answer_result = self.core_rag.answer_generator.generate_answer(
                context=context_text,
                question=question,
                max_tokens=self.core_rag.answer_generator.max_tokens
            )
            
            generation_time = time.time() - generation_start
            self.analytics["component_performance"]["generation"] += generation_time
            
            # Step 4: Create enhanced response
            total_time = time.time() - start_time
            self.analytics["epic2_response_time"] += total_time
            
            result = {
                "answer": answer_result.text,
                "citations": citations,
                "confidence": answer_result.confidence,
                "sources": list(sources),
                "retrieval_stats": {
                    "method": "epic2_advanced",
                    "total_chunks": len(context_chunks),
                    "time_ms": retrieval_time * 1000,
                    "epic2_features_used": {
                        "neural_reranking": True,
                        "graph_enhancement": True,
                        "hybrid_search": True
                    }
                },
                "generation_stats": {
                    "time_ms": generation_time * 1000,
                    "model": self.core_rag.get_generator_info()['model_name'],
                    "backend": "epic2_enhanced"
                },
                "epic2_metadata": {
                    "total_processing_time_ms": total_time * 1000,
                    "component_times": {
                        "retrieval": retrieval_time * 1000,
                        "generation": generation_time * 1000
                    },
                    "advanced_features_active": True
                }
            }
            
            if return_context:
                result["context"] = context_chunks
            
            return result
            
        except Exception as e:
            logger.error(f"Epic 2 query failed: {e}")
            # Fallback to basic RAG
            return self._query_with_basic_rag(
                question, top_k, use_hybrid, dense_weight,
                use_fallback_llm, return_context, similarity_threshold, start_time
            )
    
    def _query_with_basic_rag(
        self, question: str, top_k: int, use_hybrid: bool, dense_weight: float,
        use_fallback_llm: bool, return_context: bool, similarity_threshold: float,
        start_time: float
    ) -> Dict[str, Any]:
        """Query using basic RAG system."""
        self.analytics["basic_queries"] += 1
        
        # Use existing core RAG implementation
        result = self.core_rag.query_with_answer(
            question=question,
            top_k=top_k,
            use_hybrid=use_hybrid,
            dense_weight=dense_weight,
            use_fallback_llm=use_fallback_llm,
            return_context=return_context,
            similarity_threshold=similarity_threshold
        )
        
        # Add Epic 2 metadata to indicate basic mode
        result["epic2_metadata"] = {
            "total_processing_time_ms": (time.time() - start_time) * 1000,
            "advanced_features_active": False,
            "fallback_reason": "basic_rag_mode"
        }
        
        total_time = time.time() - start_time
        self.analytics["total_response_time"] += total_time
        
        return result
    
    def _create_no_results_response(self, question: str, retrieval_time: float) -> Dict[str, Any]:
        """Create response when no results found."""
        return {
            "answer": "I couldn't find relevant information in the documentation to answer your question.",
            "citations": [],
            "confidence": 0.0,
            "sources": [],
            "retrieval_stats": {
                "method": "epic2_advanced",
                "total_chunks": 0,
                "time_ms": retrieval_time * 1000
            },
            "generation_stats": {
                "time_ms": 0,
                "model": "none",
                "backend": "no_results"
            },
            "epic2_metadata": {
                "advanced_features_active": True,
                "no_results_found": True
            }
        }
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status including Epic 2 features."""
        base_status = {
            "status": "Online" if self.core_rag else "Offline",
            "documents": len(getattr(self.core_rag, 'chunks', [])),
            "architecture": "epic2" if self.enable_epic2_features else "basic",
            "backend_info": self.core_rag.get_generator_info() if self.core_rag else {}
        }
        
        # Add Epic 2 specific status
        if self.enable_epic2_features and self.advanced_retriever:
            epic2_stats = self.advanced_retriever.get_stats()
            base_status.update({
                "epic2_features": {
                    "neural_reranking": epic2_stats.get("components_enabled", {}).get("neural_reranking", False),
                    "graph_enhancement": epic2_stats.get("components_enabled", {}).get("graph_enhancement", False),
                    "hybrid_search": epic2_stats.get("components_enabled", {}).get("dense_search", False) and epic2_stats.get("components_enabled", {}).get("sparse_search", False)
                },
                "epic2_statistics": epic2_stats
            })
        
        # Add analytics
        base_status["analytics"] = self.analytics
        
        return base_status
    
    def get_epic2_capabilities(self) -> Dict[str, Any]:
        """Get information about Epic 2 capabilities."""
        return {
            "epic2_enabled": self.enable_epic2_features,
            "neural_reranking": self.advanced_retriever and self.advanced_retriever.neural_reranker and self.advanced_retriever.neural_reranker.is_enabled() if self.advanced_retriever else False,
            "graph_enhancement": self.advanced_retriever and self.advanced_retriever.graph_retriever and self.advanced_retriever.graph_retriever.is_enabled() if self.advanced_retriever else False,
            "hybrid_search": self.advanced_retriever is not None,
            "analytics_tracking": True,
            "performance_optimization": True,
            "hf_spaces_optimized": os.getenv("SPACE_ID") is not None
        }
    
    @property
    def chunks(self):
        """Access to chunks for compatibility."""
        return getattr(self.core_rag, 'chunks', [])
    
    @property
    def is_initialized(self):
        """Check if system is initialized."""
        return self.core_rag is not None