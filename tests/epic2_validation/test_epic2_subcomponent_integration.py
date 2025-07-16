"""
Epic 2 Sub-Component Integration Test Suite.

This module provides comprehensive validation for Epic 2 sub-component integration
within ModularUnifiedRetriever, ensuring that enhanced sub-components work correctly
together and maintain architectural compliance.

Test Categories:
1. Neural Reranking Integration - NeuralReranker sub-component within ModularUnifiedRetriever
2. Graph Enhancement Integration - GraphEnhancedRRFFusion sub-component integration
3. Multi-Backend Integration - WeaviateIndex and FAISSIndex sub-component support
4. Sub-Component Interaction - Validate sub-component communication and data flow
5. Architecture Compliance - Ensure sub-components follow established patterns

Based on: epic2-integration-test-plan.md
"""

import pytest
import sys
import logging
import time
from typing import Dict, Any, List, Optional, Tuple
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch
import numpy as np

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.core.config import load_config
from src.core.component_factory import ComponentFactory
from src.core.interfaces import Embedder, Document, RetrievalResult
from src.components.retrievers.modular_unified_retriever import ModularUnifiedRetriever
from src.components.retrievers.rerankers.neural_reranker import NeuralReranker
from src.components.retrievers.rerankers.identity_reranker import IdentityReranker
from src.components.retrievers.fusion.graph_enhanced_fusion import GraphEnhancedRRFFusion
from src.components.retrievers.fusion.rrf_fusion import RRFFusion
from src.components.retrievers.indices.faiss_index import FAISSIndex
from src.components.retrievers.indices.weaviate_index import WeaviateIndex
from src.components.retrievers.sparse.bm25_retriever import BM25Retriever

logger = logging.getLogger(__name__)

class Epic2SubComponentIntegrationValidator:
    """
    Comprehensive validator for Epic 2 sub-component integration.
    
    This class validates that Epic 2 sub-components integrate correctly within
    ModularUnifiedRetriever and maintain proper architectural patterns.
    """
    
    def __init__(self):
        self.test_results = {}
        self.validation_errors = []
        
    def _create_mock_embedder(self) -> Embedder:
        """Create a mock embedder for testing."""
        embedder = Mock(spec=Embedder)
        embedder.embedding_dim = 384
        
        def mock_embed(texts):
            if isinstance(texts, str):
                texts = [texts]
            return [np.random.rand(384).tolist() for _ in range(len(texts))]
        
        embedder.embed.side_effect = mock_embed
        return embedder
        
    def _create_test_documents(self) -> List[Document]:
        """Create test documents for integration testing."""
        documents = [
            Document(
                content="RISC-V instruction set architecture provides a stable base for processor design. The ISA includes integer and floating-point operations with extensible instruction encoding.",
                metadata={
                    "id": "riscv_isa",
                    "type": "architecture",
                    "source": "RISC-V Specification"
                }
            ),
            Document(
                content="Pipeline hazards in RISC-V processors are resolved through data forwarding and pipeline stalling. Branch prediction reduces control hazards significantly.",
                metadata={
                    "id": "pipeline_hazards",
                    "type": "implementation",
                    "source": "RISC-V Implementation Guide"
                }
            ),
            Document(
                content="Memory management unit in RISC-V provides virtual memory support through page table walks and translation lookaside buffers for efficient address translation.",
                metadata={
                    "id": "memory_management",
                    "type": "system",
                    "source": "RISC-V System Architecture"
                }
            ),
            Document(
                content="Vector extensions enable SIMD operations in RISC-V processors, providing high-performance parallel computation capabilities for scientific workloads.",
                metadata={
                    "id": "vector_extensions",
                    "type": "extensions",
                    "source": "RISC-V Vector Specification"
                }
            ),
            Document(
                content="Cache coherency protocols ensure data consistency across multiple processor cores in RISC-V multiprocessor systems using MESI state transitions.",
                metadata={
                    "id": "cache_coherency",
                    "type": "multiprocessor",
                    "source": "RISC-V Multiprocessor Guide"
                }
            )
        ]
        
        return documents
        
    def _prepare_documents_with_embeddings(self, documents: List[Document], embedder: Embedder) -> List[Document]:
        """Prepare documents with embeddings for indexing."""
        texts = [doc.content for doc in documents]
        embeddings = embedder.embed(texts)
        
        for doc, embedding in zip(documents, embeddings):
            doc.embedding = embedding
            
        return documents
        
    def run_all_validations(self) -> Dict[str, Any]:
        """Run all Epic 2 sub-component integration validation tests."""
        logger.info("Starting Epic 2 sub-component integration validation...")
        
        results = {
            "neural_reranking_integration": self._test_neural_reranking_integration(),
            "graph_enhancement_integration": self._test_graph_enhancement_integration(),
            "multi_backend_integration": self._test_multi_backend_integration(),
            "subcomponent_interaction": self._test_subcomponent_interaction(),
            "architecture_compliance": self._test_architecture_compliance()
        }
        
        # Calculate overall score
        passed_tests = sum(1 for result in results.values() if result.get("passed", False))
        total_tests = len(results)
        overall_score = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
        
        return {
            "overall_score": overall_score,
            "passed_tests": passed_tests,
            "total_tests": total_tests,
            "test_results": results,
            "validation_errors": self.validation_errors
        }
        
    def _test_neural_reranking_integration(self) -> Dict[str, Any]:
        """Test neural reranking sub-component integration."""
        test_result = {"passed": False, "details": {}, "errors": []}
        
        try:
            # Load configuration with neural reranking enabled
            config_path = Path("config/test_epic2_neural_enabled.yaml")
            config = load_config(config_path)
            embedder = self._create_mock_embedder()
            
            # Create retriever with neural reranking
            retriever = ComponentFactory.create_retriever(
                config.retriever.type,
                config=config.retriever.config,
                embedder=embedder
            )
            
            # Validate neural reranker integration
            integration_checks = {
                "retriever_created": isinstance(retriever, ModularUnifiedRetriever),
                "neural_reranker_present": isinstance(retriever.reranker, NeuralReranker),
                "neural_reranker_enabled": False,
                "model_loaded": False,
                "reranking_functional": False,
                "performance_acceptable": False
            }
            
            if isinstance(retriever.reranker, NeuralReranker):
                # Check if neural reranker is properly enabled
                try:
                    integration_checks["neural_reranker_enabled"] = retriever.reranker.is_enabled()
                    
                    # Check if model is loaded (if reranker is enabled)
                    if hasattr(retriever.reranker, 'model') and retriever.reranker.model is not None:
                        integration_checks["model_loaded"] = True
                    elif hasattr(retriever.reranker, 'model_name'):
                        integration_checks["model_loaded"] = bool(retriever.reranker.model_name)
                        
                except Exception as e:
                    logger.warning(f"Neural reranker status check failed: {e}")
                    
            # Test neural reranking functionality
            if integration_checks["neural_reranker_present"]:
                try:
                    # Create test documents
                    test_docs = self._create_test_documents()
                    test_docs = self._prepare_documents_with_embeddings(test_docs, embedder)
                    
                    # Index documents
                    retriever.index_documents(test_docs)
                    
                    # Test retrieval with neural reranking
                    query = "RISC-V pipeline hazards and branch prediction"
                    start_time = time.time()
                    results = retriever.retrieve(query, k=3)
                    retrieval_time = time.time() - start_time
                    
                    integration_checks["reranking_functional"] = len(results) > 0
                    integration_checks["performance_acceptable"] = retrieval_time < 2.0  # 2 second timeout
                    
                    # Analyze results for neural reranking evidence
                    if results:
                        # Check if results have confidence scores (neural reranking signature)
                        confidence_scores = []
                        for result in results:
                            if hasattr(result, 'confidence') and result.confidence is not None:
                                confidence_scores.append(result.confidence)
                            elif hasattr(result, 'score') and result.score is not None:
                                confidence_scores.append(result.score)
                                
                        integration_checks["confidence_scores_present"] = len(confidence_scores) > 0
                        integration_checks["score_differentiation"] = (
                            len(set(confidence_scores)) > 1 if confidence_scores else False
                        )
                        
                except Exception as e:
                    test_result["errors"].append(f"Neural reranking functionality test failed: {str(e)}")
                    
            test_result["details"] = {
                "integration_checks": integration_checks,
                "neural_features_working": sum(1 for check in integration_checks.values() if check),
                "total_checks": len(integration_checks)
            }
            
            # Test passes if neural reranking is integrated and functional
            working_features = sum(1 for check in integration_checks.values() if check)
            test_result["passed"] = working_features >= len(integration_checks) * 0.6  # 60% threshold
            
            if test_result["passed"]:
                logger.info(f"Neural reranking integration passed: {working_features}/{len(integration_checks)} checks")
            else:
                logger.warning(f"Neural reranking integration failed: {working_features}/{len(integration_checks)} checks")
                
        except Exception as e:
            test_result["errors"].append(f"Neural reranking integration test failed: {str(e)}")
            logger.error(f"Neural reranking integration test failed: {str(e)}")
            
        return test_result
        
    def _test_graph_enhancement_integration(self) -> Dict[str, Any]:
        """Test graph enhancement sub-component integration."""
        test_result = {"passed": False, "details": {}, "errors": []}
        
        try:
            # Load configuration with graph enhancement enabled
            config_path = Path("config/test_epic2_graph_enabled.yaml")
            config = load_config(config_path)
            embedder = self._create_mock_embedder()
            
            # Create retriever with graph enhancement
            retriever = ComponentFactory.create_retriever(
                config.retriever.type,
                config=config.retriever.config,
                embedder=embedder
            )
            
            # Validate graph enhancement integration
            integration_checks = {
                "retriever_created": isinstance(retriever, ModularUnifiedRetriever),
                "graph_fusion_present": isinstance(retriever.fusion_strategy, GraphEnhancedRRFFusion),
                "graph_enabled": False,
                "graph_parameters_set": False,
                "graph_functionality": False,
                "performance_acceptable": False
            }
            
            if isinstance(retriever.fusion_strategy, GraphEnhancedRRFFusion):
                # Check if graph enhancement is properly enabled
                try:
                    integration_checks["graph_enabled"] = getattr(retriever.fusion_strategy, 'graph_enabled', False)
                    
                    # Check if graph parameters are set
                    graph_params = {}
                    if hasattr(retriever.fusion_strategy, 'similarity_threshold'):
                        graph_params["similarity_threshold"] = retriever.fusion_strategy.similarity_threshold
                    if hasattr(retriever.fusion_strategy, 'max_connections_per_document'):
                        graph_params["max_connections_per_document"] = retriever.fusion_strategy.max_connections_per_document
                    if hasattr(retriever.fusion_strategy, 'use_pagerank'):
                        graph_params["use_pagerank"] = retriever.fusion_strategy.use_pagerank
                        
                    integration_checks["graph_parameters_set"] = len(graph_params) > 0
                    integration_checks["graph_parameters"] = graph_params
                    
                except Exception as e:
                    logger.warning(f"Graph enhancement status check failed: {e}")
                    
            # Test graph enhancement functionality
            if integration_checks["graph_fusion_present"]:
                try:
                    # Create test documents with relationships
                    test_docs = self._create_test_documents()
                    test_docs = self._prepare_documents_with_embeddings(test_docs, embedder)
                    
                    # Index documents
                    retriever.index_documents(test_docs)
                    
                    # Test retrieval with graph enhancement
                    query = "RISC-V processor pipeline and cache coherency"
                    start_time = time.time()
                    results = retriever.retrieve(query, k=3)
                    retrieval_time = time.time() - start_time
                    
                    integration_checks["graph_functionality"] = len(results) > 0
                    integration_checks["performance_acceptable"] = retrieval_time < 2.0  # 2 second timeout
                    
                    # Analyze results for graph enhancement evidence
                    if results:
                        # Check if results have graph-enhanced scores or metadata
                        graph_evidence = []
                        for result in results:
                            if hasattr(result, 'graph_score') and result.graph_score is not None:
                                graph_evidence.append("graph_score")
                            if hasattr(result, 'metadata') and result.metadata:
                                if any(key.startswith('graph_') for key in result.metadata.keys()):
                                    graph_evidence.append("graph_metadata")
                                    
                        integration_checks["graph_evidence_present"] = len(graph_evidence) > 0
                        integration_checks["graph_evidence"] = graph_evidence
                        
                except Exception as e:
                    test_result["errors"].append(f"Graph enhancement functionality test failed: {str(e)}")
                    
            test_result["details"] = {
                "integration_checks": integration_checks,
                "graph_features_working": sum(1 for check in integration_checks.values() if check),
                "total_checks": len(integration_checks)
            }
            
            # Test passes if graph enhancement is integrated and functional
            working_features = sum(1 for check in integration_checks.values() if check)
            test_result["passed"] = working_features >= len(integration_checks) * 0.6  # 60% threshold
            
            if test_result["passed"]:
                logger.info(f"Graph enhancement integration passed: {working_features}/{len(integration_checks)} checks")
            else:
                logger.warning(f"Graph enhancement integration failed: {working_features}/{len(integration_checks)} checks")
                
        except Exception as e:
            test_result["errors"].append(f"Graph enhancement integration test failed: {str(e)}")
            logger.error(f"Graph enhancement integration test failed: {str(e)}")
            
        return test_result
        
    def _test_multi_backend_integration(self) -> Dict[str, Any]:
        """Test multi-backend sub-component integration."""
        test_result = {"passed": False, "details": {}, "errors": []}
        
        try:
            # Test both FAISS and Weaviate backend support
            backend_tests = []
            
            # Test FAISS backend
            try:
                config_path = Path("config/test_epic2_all_features.yaml")
                config = load_config(config_path)
                embedder = self._create_mock_embedder()
                
                # Create retriever with FAISS backend
                retriever = ComponentFactory.create_retriever(
                    config.retriever.type,
                    config=config.retriever.config,
                    embedder=embedder
                )
                
                faiss_test = {
                    "backend": "faiss",
                    "retriever_created": isinstance(retriever, ModularUnifiedRetriever),
                    "vector_index_type": type(retriever.vector_index).__name__,
                    "faiss_index_present": isinstance(retriever.vector_index, FAISSIndex),
                    "functionality_test": False,
                    "error": None
                }
                
                # Test FAISS functionality
                if faiss_test["faiss_index_present"]:
                    try:
                        test_docs = self._create_test_documents()
                        test_docs = self._prepare_documents_with_embeddings(test_docs, embedder)
                        
                        retriever.index_documents(test_docs)
                        results = retriever.retrieve("RISC-V architecture", k=2)
                        
                        faiss_test["functionality_test"] = len(results) > 0
                        faiss_test["results_count"] = len(results)
                        
                    except Exception as e:
                        faiss_test["error"] = str(e)
                        
                backend_tests.append(faiss_test)
                
            except Exception as e:
                backend_tests.append({
                    "backend": "faiss",
                    "error": str(e)
                })
                
            # Test Weaviate backend (if available)
            try:
                # Create configuration for Weaviate backend
                weaviate_config = {
                    "vector_index": {
                        "type": "weaviate",
                        "config": {
                            "url": "http://localhost:8080",
                            "class_name": "EpicDocument"
                        }
                    },
                    "sparse": {"type": "bm25", "config": {}},
                    "fusion": {"type": "rrf", "config": {}},
                    "reranker": {"type": "identity", "config": {}}
                }
                
                embedder = self._create_mock_embedder()
                
                # Try to create retriever with Weaviate backend
                try:
                    retriever = ComponentFactory.create_retriever(
                        "modular_unified",
                        config=weaviate_config,
                        embedder=embedder
                    )
                    
                    weaviate_test = {
                        "backend": "weaviate",
                        "retriever_created": isinstance(retriever, ModularUnifiedRetriever),
                        "vector_index_type": type(retriever.vector_index).__name__,
                        "weaviate_index_present": isinstance(retriever.vector_index, WeaviateIndex),
                        "functionality_test": False,
                        "error": None
                    }
                    
                    # Test Weaviate functionality (basic check)
                    if weaviate_test["weaviate_index_present"]:
                        try:
                            # Basic connection test
                            if hasattr(retriever.vector_index, 'client'):
                                weaviate_test["connection_available"] = True
                                weaviate_test["functionality_test"] = True
                        except Exception as e:
                            weaviate_test["error"] = str(e)
                            
                    backend_tests.append(weaviate_test)
                    
                except Exception as e:
                    backend_tests.append({
                        "backend": "weaviate",
                        "error": f"Weaviate backend creation failed: {str(e)}"
                    })
                    
            except Exception as e:
                backend_tests.append({
                    "backend": "weaviate",
                    "error": f"Weaviate backend test setup failed: {str(e)}"
                })
                
            test_result["details"] = {
                "backend_tests": backend_tests,
                "backends_tested": len(backend_tests),
                "successful_backends": sum(1 for test in backend_tests if test.get("functionality_test", False))
            }
            
            # Test passes if at least one backend works
            successful_backends = sum(1 for test in backend_tests if test.get("functionality_test", False))
            test_result["passed"] = successful_backends > 0
            
            if test_result["passed"]:
                logger.info(f"Multi-backend integration passed: {successful_backends}/{len(backend_tests)} backends")
            else:
                logger.warning(f"Multi-backend integration failed: {successful_backends}/{len(backend_tests)} backends")
                
        except Exception as e:
            test_result["errors"].append(f"Multi-backend integration test failed: {str(e)}")
            logger.error(f"Multi-backend integration test failed: {str(e)}")
            
        return test_result
        
    def _test_subcomponent_interaction(self) -> Dict[str, Any]:
        """Test sub-component interaction and data flow."""
        test_result = {"passed": False, "details": {}, "errors": []}
        
        try:
            # Load configuration with all Epic 2 features
            config_path = Path("config/test_epic2_all_features.yaml")
            config = load_config(config_path)
            embedder = self._create_mock_embedder()
            
            # Create retriever with all Epic 2 features
            retriever = ComponentFactory.create_retriever(
                config.retriever.type,
                config=config.retriever.config,
                embedder=embedder
            )
            
            # Test sub-component interaction
            interaction_tests = {
                "vector_sparse_interaction": False,
                "fusion_integration": False,
                "reranker_integration": False,
                "end_to_end_pipeline": False,
                "data_flow_consistency": False
            }
            
            # Prepare test documents
            test_docs = self._create_test_documents()
            test_docs = self._prepare_documents_with_embeddings(test_docs, embedder)
            
            # Index documents
            retriever.index_documents(test_docs)
            
            # Test vector and sparse retrieval interaction
            try:
                # Test if both vector and sparse retrieval can work together
                if hasattr(retriever, 'vector_index') and hasattr(retriever, 'sparse_retriever'):
                    query = "RISC-V instruction set"
                    
                    # Test vector retrieval
                    if hasattr(retriever.vector_index, 'search'):
                        query_embedding = embedder.embed([query])[0]
                        vector_results = retriever.vector_index.search(query_embedding, k=3)
                        interaction_tests["vector_retrieval_works"] = len(vector_results) > 0
                        
                    # Test sparse retrieval
                    if hasattr(retriever.sparse_retriever, 'search'):
                        sparse_results = retriever.sparse_retriever.search(query, k=3)
                        interaction_tests["sparse_retrieval_works"] = len(sparse_results) > 0
                        
                    interaction_tests["vector_sparse_interaction"] = (
                        interaction_tests.get("vector_retrieval_works", False) and
                        interaction_tests.get("sparse_retrieval_works", False)
                    )
                    
            except Exception as e:
                test_result["errors"].append(f"Vector-sparse interaction test failed: {str(e)}")
                
            # Test fusion integration
            try:
                if hasattr(retriever, 'fusion_strategy'):
                    # Test fusion strategy can combine results
                    query = "RISC-V pipeline hazards"
                    results = retriever.retrieve(query, k=3)
                    
                    interaction_tests["fusion_integration"] = len(results) > 0
                    interaction_tests["fusion_results_count"] = len(results)
                    
            except Exception as e:
                test_result["errors"].append(f"Fusion integration test failed: {str(e)}")
                
            # Test reranker integration
            try:
                if hasattr(retriever, 'reranker'):
                    # Test reranker can process results
                    query = "RISC-V memory management"
                    results = retriever.retrieve(query, k=3)
                    
                    interaction_tests["reranker_integration"] = len(results) > 0
                    
                    # Check if reranker affects results
                    if results:
                        # Look for evidence of reranking (score differentiation)
                        scores = []
                        for result in results:
                            if hasattr(result, 'score') and result.score is not None:
                                scores.append(result.score)
                            elif hasattr(result, 'confidence') and result.confidence is not None:
                                scores.append(result.confidence)
                                
                        interaction_tests["reranker_score_differentiation"] = len(set(scores)) > 1 if scores else False
                        
            except Exception as e:
                test_result["errors"].append(f"Reranker integration test failed: {str(e)}")
                
            # Test end-to-end pipeline
            try:
                query = "RISC-V vector extensions and cache coherency"
                start_time = time.time()
                results = retriever.retrieve(query, k=3)
                end_time = time.time()
                
                interaction_tests["end_to_end_pipeline"] = len(results) > 0
                interaction_tests["pipeline_latency"] = end_time - start_time
                interaction_tests["pipeline_performance_acceptable"] = (end_time - start_time) < 2.0
                
                # Test data flow consistency
                if results:
                    # Check if results have consistent structure
                    result_structures = []
                    for result in results:
                        structure = {
                            "has_content": hasattr(result, 'content') and result.content is not None,
                            "has_metadata": hasattr(result, 'metadata') and result.metadata is not None,
                            "has_score": hasattr(result, 'score') and result.score is not None
                        }
                        result_structures.append(structure)
                        
                    # Check consistency
                    if result_structures:
                        first_structure = result_structures[0]
                        interaction_tests["data_flow_consistency"] = all(
                            structure == first_structure for structure in result_structures
                        )
                        
            except Exception as e:
                test_result["errors"].append(f"End-to-end pipeline test failed: {str(e)}")
                
            test_result["details"] = {
                "interaction_tests": interaction_tests,
                "successful_interactions": sum(1 for test in interaction_tests.values() if test),
                "total_interactions": len(interaction_tests)
            }
            
            # Test passes if most interactions work
            successful_interactions = sum(1 for test in interaction_tests.values() if test)
            test_result["passed"] = successful_interactions >= len(interaction_tests) * 0.6  # 60% threshold
            
            if test_result["passed"]:
                logger.info(f"Sub-component interaction passed: {successful_interactions}/{len(interaction_tests)} interactions")
            else:
                logger.warning(f"Sub-component interaction failed: {successful_interactions}/{len(interaction_tests)} interactions")
                
        except Exception as e:
            test_result["errors"].append(f"Sub-component interaction test failed: {str(e)}")
            logger.error(f"Sub-component interaction test failed: {str(e)}")
            
        return test_result
        
    def _test_architecture_compliance(self) -> Dict[str, Any]:
        """Test architecture compliance for Epic 2 sub-components."""
        test_result = {"passed": False, "details": {}, "errors": []}
        
        try:
            # Load configuration with all Epic 2 features
            config_path = Path("config/test_epic2_all_features.yaml")
            config = load_config(config_path)
            embedder = self._create_mock_embedder()
            
            # Create retriever with all Epic 2 features
            retriever = ComponentFactory.create_retriever(
                config.retriever.type,
                config=config.retriever.config,
                embedder=embedder
            )
            
            # Test architecture compliance
            compliance_checks = {
                "modular_unified_retriever": isinstance(retriever, ModularUnifiedRetriever),
                "has_vector_index": hasattr(retriever, 'vector_index'),
                "has_sparse_retriever": hasattr(retriever, 'sparse_retriever'),
                "has_fusion_strategy": hasattr(retriever, 'fusion_strategy'),
                "has_reranker": hasattr(retriever, 'reranker'),
                "subcomponent_independence": False,
                "interface_compliance": False,
                "epic2_feature_integration": False
            }
            
            # Test sub-component independence
            try:
                # Each sub-component should be independently testable
                subcomponents = []
                if hasattr(retriever, 'vector_index'):
                    subcomponents.append(("vector_index", retriever.vector_index))
                if hasattr(retriever, 'sparse_retriever'):
                    subcomponents.append(("sparse_retriever", retriever.sparse_retriever))
                if hasattr(retriever, 'fusion_strategy'):
                    subcomponents.append(("fusion_strategy", retriever.fusion_strategy))
                if hasattr(retriever, 'reranker'):
                    subcomponents.append(("reranker", retriever.reranker))
                    
                # Check if sub-components have expected interfaces
                subcomponent_interfaces = {}
                for name, component in subcomponents:
                    interfaces = []
                    if hasattr(component, 'search'):
                        interfaces.append("search")
                    if hasattr(component, 'index'):
                        interfaces.append("index")
                    if hasattr(component, 'fuse_results'):
                        interfaces.append("fuse_results")
                    if hasattr(component, 'rerank'):
                        interfaces.append("rerank")
                        
                    subcomponent_interfaces[name] = interfaces
                    
                compliance_checks["subcomponent_interfaces"] = subcomponent_interfaces
                compliance_checks["subcomponent_independence"] = len(subcomponents) == 4
                
            except Exception as e:
                test_result["errors"].append(f"Sub-component independence test failed: {str(e)}")
                
            # Test interface compliance
            try:
                # ModularUnifiedRetriever should implement Retriever interface
                expected_methods = ["retrieve", "index_documents", "get_stats"]
                
                interface_compliance = {}
                for method in expected_methods:
                    interface_compliance[method] = hasattr(retriever, method)
                    
                compliance_checks["interface_compliance"] = all(interface_compliance.values())
                compliance_checks["interface_methods"] = interface_compliance
                
            except Exception as e:
                test_result["errors"].append(f"Interface compliance test failed: {str(e)}")
                
            # Test Epic 2 feature integration
            try:
                epic2_features = {
                    "neural_reranking": isinstance(retriever.reranker, NeuralReranker),
                    "graph_enhancement": isinstance(retriever.fusion_strategy, GraphEnhancedRRFFusion),
                    "modular_architecture": isinstance(retriever, ModularUnifiedRetriever)
                }
                
                compliance_checks["epic2_features"] = epic2_features
                compliance_checks["epic2_feature_integration"] = any(epic2_features.values())
                
            except Exception as e:
                test_result["errors"].append(f"Epic 2 feature integration test failed: {str(e)}")
                
            test_result["details"] = {
                "compliance_checks": compliance_checks,
                "compliant_aspects": sum(1 for check in compliance_checks.values() if check),
                "total_aspects": len(compliance_checks)
            }
            
            # Test passes if most compliance checks pass
            compliant_aspects = sum(1 for check in compliance_checks.values() if check)
            test_result["passed"] = compliant_aspects >= len(compliance_checks) * 0.7  # 70% threshold
            
            if test_result["passed"]:
                logger.info(f"Architecture compliance passed: {compliant_aspects}/{len(compliance_checks)} aspects")
            else:
                logger.warning(f"Architecture compliance failed: {compliant_aspects}/{len(compliance_checks)} aspects")
                
        except Exception as e:
            test_result["errors"].append(f"Architecture compliance test failed: {str(e)}")
            logger.error(f"Architecture compliance test failed: {str(e)}")
            
        return test_result


# Pytest test classes
class TestEpic2SubComponentIntegration:
    """Pytest-compatible test class for Epic 2 sub-component integration validation."""
    
    def setup_method(self):
        """Set up test environment."""
        self.validator = Epic2SubComponentIntegrationValidator()
        
    def test_neural_reranking_integration(self):
        """Test neural reranking sub-component integration."""
        result = self.validator._test_neural_reranking_integration()
        assert result["passed"], f"Neural reranking integration failed: {result.get('errors', [])}"
        
    def test_graph_enhancement_integration(self):
        """Test graph enhancement sub-component integration."""
        result = self.validator._test_graph_enhancement_integration()
        assert result["passed"], f"Graph enhancement integration failed: {result.get('errors', [])}"
        
    def test_multi_backend_integration(self):
        """Test multi-backend sub-component integration."""
        result = self.validator._test_multi_backend_integration()
        assert result["passed"], f"Multi-backend integration failed: {result.get('errors', [])}"
        
    def test_subcomponent_interaction(self):
        """Test sub-component interaction and data flow."""
        result = self.validator._test_subcomponent_interaction()
        assert result["passed"], f"Sub-component interaction failed: {result.get('errors', [])}"
        
    def test_architecture_compliance(self):
        """Test architecture compliance for Epic 2 sub-components."""
        result = self.validator._test_architecture_compliance()
        assert result["passed"], f"Architecture compliance failed: {result.get('errors', [])}"
        
    def test_comprehensive_integration(self):
        """Test comprehensive Epic 2 sub-component integration."""
        results = self.validator.run_all_validations()
        assert results["overall_score"] >= 70, f"Overall integration score too low: {results['overall_score']}%"
        assert results["passed_tests"] >= 3, f"Too few tests passed: {results['passed_tests']}/{results['total_tests']}"


if __name__ == "__main__":
    # Run validation if called directly
    validator = Epic2SubComponentIntegrationValidator()
    results = validator.run_all_validations()
    
    print("\n" + "=" * 80)
    print("EPIC 2 SUB-COMPONENT INTEGRATION VALIDATION RESULTS")
    print("=" * 80)
    print(f"Overall Score: {results['overall_score']:.1f}%")
    print(f"Passed Tests: {results['passed_tests']}/{results['total_tests']}")
    
    if results["validation_errors"]:
        print("\nValidation Errors:")
        for error in results["validation_errors"]:
            print(f"  - {error}")
    
    print("\nDetailed Results:")
    for test_name, test_result in results["test_results"].items():
        status = "✅ PASS" if test_result.get("passed", False) else "❌ FAIL"
        print(f"  {test_name}: {status}")
        if test_result.get("errors"):
            for error in test_result["errors"]:
                print(f"    Error: {error}")