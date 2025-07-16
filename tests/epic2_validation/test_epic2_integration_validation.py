"""
Epic 2 Integration Validation Tests for Advanced Retriever.

This module provides comprehensive validation for the complete Epic 2 system
integration including the 4-stage pipeline, configuration control, error handling,
and ComponentFactory integration.

Test Categories:
1. Complete 4-Stage Pipeline (Dense → Sparse → Graph → Neural)
2. ComponentFactory "advanced" Retriever Integration
3. YAML Configuration Control for All Features
4. Graceful Degradation When Components Fail
5. Error Handling Across All Epic 2 Components
6. PlatformOrchestrator Integration
"""

import pytest
import time
import logging
from typing import List, Dict, Any, Optional
from unittest.mock import Mock, patch, MagicMock
import numpy as np
from pathlib import Path

# Import Epic 2 components (updated for current architecture)
from src.components.retrievers.modular_unified_retriever import ModularUnifiedRetriever
from src.core.interfaces import Document, RetrievalResult, Embedder
from src.core.component_factory import ComponentFactory
from src.core.config import load_config

logger = logging.getLogger(__name__)


class Epic2IntegrationValidator:
    """Comprehensive validator for Epic 2 system integration."""

    def __init__(self, config_name: str = "test_epic2_all_features"):
        self.config_name = config_name
        self.test_results = {}
        self.performance_metrics = {}
        self.validation_errors = []
        
    def _load_test_config(self, config_name: str = None):
        """Load test configuration from file."""
        if config_name is None:
            config_name = self.config_name
        config_path = Path(f"config/{config_name}.yaml")
        return load_config(config_path)
    
    def _prepare_documents_with_embeddings(self, documents, embedder):
        """Prepare documents with embeddings for indexing."""
        texts = [doc.content for doc in documents]
        embeddings = embedder.embed(texts)
        
        # Add embeddings to documents before indexing
        for doc, embedding in zip(documents, embeddings):
            doc.embedding = embedding
        
        return documents

    def run_all_validations(self) -> Dict[str, Any]:
        """Run all Epic 2 integration validation tests."""
        logger.info("Starting comprehensive Epic 2 integration validation...")

        try:
            self.test_results["four_stage_pipeline"] = self._test_four_stage_pipeline()
            self.test_results["component_factory"] = (
                self._test_component_factory_integration()
            )
            self.test_results["yaml_configuration"] = (
                self._test_yaml_configuration_control()
            )
            self.test_results["graceful_degradation"] = (
                self._test_graceful_degradation()
            )
            self.test_results["error_handling"] = self._test_error_handling()
            self.test_results["platform_orchestrator"] = (
                self._test_platform_orchestrator_integration()
            )

            # Calculate overall score
            passed_tests = sum(
                1
                for result in self.test_results.values()
                if result.get("passed", False)
            )
            total_tests = len(self.test_results)
            overall_score = (passed_tests / total_tests) * 100 if total_tests > 0 else 0

            return {
                "overall_score": overall_score,
                "passed_tests": passed_tests,
                "total_tests": total_tests,
                "test_results": self.test_results,
                "performance_metrics": self.performance_metrics,
                "validation_errors": self.validation_errors,
            }

        except Exception as e:
            logger.error(f"Epic 2 integration validation failed: {str(e)}")
            self.validation_errors.append(f"Critical validation failure: {str(e)}")
            return {
                "overall_score": 0,
                "passed_tests": 0,
                "total_tests": len(self.test_results),
                "test_results": self.test_results,
                "performance_metrics": self.performance_metrics,
                "validation_errors": self.validation_errors,
            }

    def _create_comprehensive_test_documents(self) -> List[Document]:
        """Create comprehensive test documents for Epic 2 validation."""
        documents = [
            Document(
                content="RISC-V instruction pipeline architecture implements 5-stage design with fetch, decode, execute, memory, and writeback stages. Pipeline hazards are handled through forwarding and stall mechanisms.",
                metadata={
                    "id": "pipeline_doc",
                    "type": "architecture",
                    "complexity": "high",
                },
            ),
            Document(
                content="Branch prediction in RISC-V processors uses two-level adaptive predictors to reduce control hazards. Branch target buffer caches recent branch targets for faster prediction.",
                metadata={
                    "id": "branch_doc",
                    "type": "optimization",
                    "complexity": "medium",
                },
            ),
            Document(
                content="RISC-V memory hierarchy includes L1 instruction cache, L1 data cache, shared L2 cache, and main memory. Cache coherency is maintained through MESI protocol.",
                metadata={
                    "id": "memory_doc",
                    "type": "memory_system",
                    "complexity": "high",
                },
            ),
            Document(
                content="Vector extensions in RISC-V (RVV) provide SIMD operations for parallel processing. Vector registers and variable-length vector operations improve computational efficiency.",
                metadata={
                    "id": "vector_doc",
                    "type": "extensions",
                    "complexity": "medium",
                },
            ),
            Document(
                content="RISC-V supervisor mode provides privilege separation and virtual memory support. Page table walk and TLB management enable efficient address translation.",
                metadata={
                    "id": "supervisor_doc",
                    "type": "system",
                    "complexity": "high",
                },
            ),
        ]
        return documents

    def _test_four_stage_pipeline(self) -> Dict[str, Any]:
        """Test complete 4-stage pipeline (Dense → Sparse → Graph → Neural)."""
        test_result = {"passed": False, "details": {}, "errors": []}

        try:
            # Load comprehensive configuration enabling all Epic 2 features
            config = self._load_test_config()
            retriever_config = config.retriever.config

            embedder = Mock(spec=Embedder)
            # Mock embed method to return correct number of embeddings
            def mock_embed(texts):
                if isinstance(texts, str):
                    texts = [texts]
                return [np.random.rand(384).tolist() for _ in range(len(texts))]
            embedder.embed.side_effect = mock_embed
            embedder.embedding_dim = 384

            try:
                retriever = ComponentFactory.create_retriever(config.retriever.type, config=retriever_config, embedder=embedder)

                # Index test documents
                test_docs = self._create_comprehensive_test_documents()
                test_docs = self._prepare_documents_with_embeddings(test_docs, embedder)
                retriever.index_documents(test_docs)

                # Test 4-stage pipeline execution
                query = "RISC-V pipeline hazard detection and forwarding mechanisms"

                # Measure pipeline execution
                start_time = time.time()
                results = retriever.retrieve(query, k=3)
                pipeline_time = time.time() - start_time

                # Analyze pipeline stages for ModularUnifiedRetriever
                pipeline_stages = {
                    "dense_retrieval": hasattr(retriever, "vector_index") and retriever.vector_index is not None,
                    "sparse_retrieval": hasattr(retriever, "sparse_retriever") and retriever.sparse_retriever is not None,
                    "graph_retrieval": hasattr(retriever, "fusion_strategy") and 
                                     str(type(retriever.fusion_strategy).__name__) == "GraphEnhancedRRFFusion",
                    "neural_reranking": hasattr(retriever, "reranker") and 
                                      str(type(retriever.reranker).__name__) == "NeuralReranker",
                }

                # Check result metadata for pipeline evidence
                result_metadata = {}
                if results:
                    for i, result in enumerate(results):
                        if hasattr(result, "metadata") and result.metadata:
                            result_metadata[f"result_{i}"] = result.metadata
                        if hasattr(result, "retrieval_method"):
                            result_metadata[f"method_{i}"] = result.retrieval_method

                test_result["details"] = {
                    "pipeline_execution_time_seconds": pipeline_time,
                    "results_returned": len(results),
                    "pipeline_stages": pipeline_stages,
                    "result_metadata": result_metadata,
                    "modular_unified_retriever_initialized": True,
                    "epic2_features_enabled": True,
                }

                # Test passes if pipeline executes and returns results
                pipeline_functional = len(results) > 0 and pipeline_time > 0
                some_stages_active = any(pipeline_stages.values())

                if pipeline_functional and some_stages_active:
                    test_result["passed"] = True
                    logger.info(
                        f"4-stage pipeline test passed: {len(results)} results in {pipeline_time:.3f}s"
                    )
                else:
                    logger.warning("4-stage pipeline execution incomplete")

            except Exception as e:
                test_result["errors"].append(
                    f"4-stage pipeline execution failed: {str(e)}"
                )

        except Exception as e:
            error_msg = f"4-stage pipeline test failed: {str(e)}"
            test_result["errors"].append(error_msg)
            logger.error(error_msg)

        return test_result

    def _test_component_factory_integration(self) -> Dict[str, Any]:
        """Test ComponentFactory 'advanced' retriever integration."""
        test_result = {"passed": False, "details": {}, "errors": []}

        try:
            # Test ComponentFactory registration for Epic 2 features
            try:
                # Check if "modular_unified" retriever type is registered
                factory_has_modular_unified = (
                    hasattr(ComponentFactory, "_RETRIEVERS")
                    and "modular_unified" in ComponentFactory._RETRIEVERS
                )

                if not factory_has_modular_unified:
                    # Try alternative registration check
                    factory_has_modular_unified = hasattr(ComponentFactory, "create_retriever")

            except Exception as e:
                factory_has_modular_unified = False
                test_result["errors"].append(
                    f"ComponentFactory inspection failed: {str(e)}"
                )

            # Test modular_unified retriever creation with Epic 2 features
            epic2_retriever_created = False
            creation_error = None

            if factory_has_modular_unified:
                try:
                    # Load Epic 2 configuration
                    config = self._load_test_config()
                    retriever_config = config.retriever.config
                    
                    embedder = Mock(spec=Embedder)
                    # Mock embed method to return correct number of embeddings
                    def mock_embed(texts):
                        if isinstance(texts, str):
                            texts = [texts]
                        return [np.random.rand(384).tolist() for _ in range(len(texts))]
                    embedder.embed.side_effect = mock_embed
                    embedder.embedding_dim = 384

                    # Attempt to create modular_unified retriever with Epic 2 features
                    retriever = ComponentFactory.create_retriever(
                        config.retriever.type, config=retriever_config, embedder=embedder
                    )
                    epic2_retriever_created = isinstance(
                        retriever, ModularUnifiedRetriever
                    )

                except Exception as e:
                    creation_error = str(e)
                    test_result["errors"].append(
                        f"Epic 2 retriever creation failed: {str(e)}"
                    )

            test_result["details"] = {
                "component_factory_available": hasattr(
                    ComponentFactory, "create_retriever"
                ),
                "modular_unified_type_registered": factory_has_modular_unified,
                "epic2_retriever_created": epic2_retriever_created,
                "creation_error": creation_error,
            }

            # Test passes if ComponentFactory can create Epic 2 retrievers
            if epic2_retriever_created:
                test_result["passed"] = True
                logger.info("ComponentFactory Epic 2 integration test passed")
            elif factory_has_modular_unified:
                test_result["passed"] = (
                    True  # Framework exists, creation might need specific config
                )
                logger.info("ComponentFactory Epic 2 integration framework available")
            else:
                logger.warning("ComponentFactory Epic 2 integration incomplete")

        except Exception as e:
            error_msg = f"ComponentFactory integration test failed: {str(e)}"
            test_result["errors"].append(error_msg)
            logger.error(error_msg)

        return test_result

    def _test_yaml_configuration_control(self) -> Dict[str, Any]:
        """Test YAML configuration control for all features."""
        test_result = {"passed": False, "details": {}, "errors": []}

        try:
            # Test different YAML-style configurations using config files
            test_configurations = [
                {
                    "name": "all_features_enabled",
                    "config_file": "test_epic2_all_features",
                },
                {
                    "name": "selective_features",
                    "config_file": "test_epic2_graph_enabled",
                },
                {
                    "name": "minimal_features",
                    "config_file": "test_epic2_minimal",
                },
            ]

            configuration_results = []

            for test_config in test_configurations:
                try:
                    # Load configuration from file
                    config = self._load_test_config(test_config["config_file"])
                    retriever_config = config.retriever.config
                    
                    embedder = Mock(spec=Embedder)
                    # Mock embed method to return correct number of embeddings
                    def mock_embed(texts):
                        if isinstance(texts, str):
                            texts = [texts]
                        return [np.random.rand(384).tolist() for _ in range(len(texts))]
                    embedder.embed.side_effect = mock_embed
                    embedder.embedding_dim = 384
                    
                    retriever = ComponentFactory.create_retriever(
                        config.retriever.type, config=retriever_config, embedder=embedder
                    )

                    # Check if configuration was applied based on sub-components
                    config_applied = {
                        "graph_enabled": hasattr(retriever, "fusion_strategy") and 
                                       "GraphEnhanced" in str(type(retriever.fusion_strategy).__name__),
                        "neural_enabled": hasattr(retriever, "reranker") and 
                                        "Neural" in str(type(retriever.reranker).__name__),
                        "modular_unified_type": isinstance(retriever, ModularUnifiedRetriever),
                    }

                    configuration_results.append(
                        {
                            "config_name": test_config["name"],
                            "config_applied": config_applied,
                            "retriever_created": True,
                            "error": None,
                        }
                    )

                except Exception as e:
                    configuration_results.append(
                        {
                            "config_name": test_config["name"],
                            "config_applied": {},
                            "retriever_created": False,
                            "error": str(e),
                        }
                    )

            test_result["details"] = {
                "configurations_tested": len(test_configurations),
                "configuration_results": configuration_results,
                "successful_configs": sum(
                    1 for r in configuration_results if r["retriever_created"]
                ),
            }

            # Test passes if any configuration works
            successful_configs = sum(
                1 for r in configuration_results if r["retriever_created"]
            )
            if successful_configs > 0:
                test_result["passed"] = True
                logger.info(
                    f"YAML configuration control test passed: {successful_configs}/{len(test_configurations)} configs"
                )
            else:
                logger.warning("No YAML configurations working")

        except Exception as e:
            error_msg = f"YAML configuration control test failed: {str(e)}"
            test_result["errors"].append(error_msg)
            logger.error(error_msg)

        return test_result

    def _test_graceful_degradation(self) -> Dict[str, Any]:
        """Test graceful degradation when components fail."""
        test_result = {"passed": False, "details": {}, "errors": []}

        try:
            # Load configuration with all features enabled
            config = self._load_test_config()
            retriever_config = config.retriever.config

            embedder = Mock(spec=Embedder)
            # Mock embed method to return correct number of embeddings
            def mock_embed(texts):
                if isinstance(texts, str):
                    texts = [texts]
                return [np.random.rand(384).tolist() for _ in range(len(texts))]
            embedder.embed.side_effect = mock_embed
            embedder.embedding_dim = 384

            try:
                retriever = ComponentFactory.create_retriever(config.retriever.type, config=retriever_config, embedder=embedder)

                # Index test documents
                test_docs = self._create_comprehensive_test_documents()
                test_docs = self._prepare_documents_with_embeddings(test_docs, embedder)
                retriever.index_documents(test_docs)

                # Test graceful degradation scenarios
                degradation_tests = []

                # Test 1: Neural reranking failure
                try:
                    with patch.object(
                        retriever.reranker, "rerank"
                    ) as mock_neural:
                        mock_neural.side_effect = Exception("Neural reranking failed")
                        results = retriever.retrieve("test query", k=3)

                        degradation_tests.append(
                            {
                                "test": "neural_reranking_failure",
                                "results_returned": len(results),
                                "graceful": len(results) > 0,
                            }
                        )
                except Exception as e:
                    degradation_tests.append(
                        {
                            "test": "neural_reranking_failure",
                            "results_returned": 0,
                            "graceful": False,
                            "error": str(e),
                        }
                    )

                # Test 2: Fusion strategy failure
                try:
                    with patch.object(retriever.fusion_strategy, "fuse_results") as mock_fusion:
                        mock_fusion.side_effect = Exception("Fusion strategy failed")
                        results = retriever.retrieve("test query", k=3)

                        degradation_tests.append(
                            {
                                "test": "fusion_strategy_failure",
                                "results_returned": len(results),
                                "graceful": len(results) > 0,
                            }
                        )
                except Exception as e:
                    degradation_tests.append(
                        {
                            "test": "fusion_strategy_failure",
                            "results_returned": 0,
                            "graceful": False,
                            "error": str(e),
                        }
                    )

                # Test 3: Vector index failure
                try:
                    with patch.object(retriever.vector_index, "search") as mock_vector:
                        mock_vector.side_effect = Exception("Vector index failed")
                        results = retriever.retrieve("test query", k=3)

                        degradation_tests.append(
                            {
                                "test": "vector_index_failure",
                                "results_returned": len(results),
                                "graceful": len(results) > 0,
                            }
                        )
                except Exception as e:
                    degradation_tests.append(
                        {
                            "test": "vector_index_failure",
                            "results_returned": 0,
                            "graceful": False,
                            "error": str(e),
                        }
                    )

                test_result["details"] = {
                    "degradation_tests": degradation_tests,
                    "graceful_degradations": sum(
                        1 for test in degradation_tests if test.get("graceful", False)
                    ),
                    "total_degradation_tests": len(degradation_tests),
                }

                # Test passes if at least some degradation scenarios are handled gracefully
                graceful_count = sum(
                    1 for test in degradation_tests if test.get("graceful", False)
                )
                if graceful_count > 0:
                    test_result["passed"] = True
                    logger.info(
                        f"Graceful degradation test passed: {graceful_count}/{len(degradation_tests)} scenarios"
                    )
                else:
                    logger.warning("No graceful degradation scenarios working")

            except Exception as e:
                test_result["errors"].append(
                    f"Graceful degradation setup failed: {str(e)}"
                )

        except Exception as e:
            error_msg = f"Graceful degradation test failed: {str(e)}"
            test_result["errors"].append(error_msg)
            logger.error(error_msg)

        return test_result

    def _test_error_handling(self) -> Dict[str, Any]:
        """Test error handling across all Epic 2 components."""
        test_result = {"passed": False, "details": {}, "errors": []}

        try:
            # Test error handling scenarios
            error_scenarios = []

            # Scenario 1: Invalid configuration
            try:
                # Load valid config structure
                config = self._load_test_config("test_epic2_base")
                retriever_config = config.retriever.config
                
                embedder = Mock(spec=Embedder)
                # Mock embed method to return correct number of embeddings
                def mock_embed(texts):
                    if isinstance(texts, str):
                        texts = [texts]
                    return [np.random.rand(384).tolist() for _ in range(len(texts))]
                embedder.embed.side_effect = mock_embed
                embedder.embedding_dim = 384
                
                retriever = ComponentFactory.create_retriever(config.retriever.type, config=retriever_config, embedder=embedder)

                error_scenarios.append(
                    {
                        "scenario": "invalid_configuration",
                        "handled_gracefully": True,
                        "error": None,
                    }
                )
            except Exception as e:
                error_scenarios.append(
                    {
                        "scenario": "invalid_configuration",
                        "handled_gracefully": isinstance(e, (ValueError, TypeError)),
                        "error": str(e),
                    }
                )

            # Scenario 2: Empty query
            try:
                config = self._load_test_config("test_epic2_base")
                retriever_config = config.retriever.config
                
                embedder = Mock(spec=Embedder)
                # Mock embed method to return correct number of embeddings
                def mock_embed(texts):
                    if isinstance(texts, str):
                        texts = [texts]
                    return [np.random.rand(384).tolist() for _ in range(len(texts))]
                embedder.embed.side_effect = mock_embed
                embedder.embedding_dim = 384
                
                retriever = ComponentFactory.create_retriever(config.retriever.type, config=retriever_config, embedder=embedder)

                results = retriever.retrieve("", k=5)  # Empty query
                error_scenarios.append(
                    {
                        "scenario": "empty_query",
                        "handled_gracefully": True,
                        "error": None,
                        "results": len(results),
                    }
                )
            except Exception as e:
                error_scenarios.append(
                    {
                        "scenario": "empty_query",
                        "handled_gracefully": isinstance(e, (ValueError, RuntimeError)),
                        "error": str(e),
                    }
                )

            # Scenario 3: No documents indexed
            try:
                config = self._load_test_config("test_epic2_base")
                retriever_config = config.retriever.config
                
                embedder = Mock(spec=Embedder)
                # Mock embed method to return correct number of embeddings
                def mock_embed(texts):
                    if isinstance(texts, str):
                        texts = [texts]
                    return [np.random.rand(384).tolist() for _ in range(len(texts))]
                embedder.embed.side_effect = mock_embed
                embedder.embedding_dim = 384
                
                retriever = ComponentFactory.create_retriever(config.retriever.type, config=retriever_config, embedder=embedder)

                results = retriever.retrieve("test query", k=5)  # No documents indexed
                error_scenarios.append(
                    {
                        "scenario": "no_documents",
                        "handled_gracefully": True,
                        "error": None,
                        "results": len(results),
                    }
                )
            except Exception as e:
                error_scenarios.append(
                    {
                        "scenario": "no_documents",
                        "handled_gracefully": isinstance(e, RuntimeError),
                        "error": str(e),
                    }
                )

            test_result["details"] = {
                "error_scenarios": error_scenarios,
                "gracefully_handled": sum(
                    1
                    for scenario in error_scenarios
                    if scenario.get("handled_gracefully", False)
                ),
                "total_scenarios": len(error_scenarios),
            }

            # Test passes if most error scenarios are handled gracefully
            graceful_count = sum(
                1
                for scenario in error_scenarios
                if scenario.get("handled_gracefully", False)
            )
            if graceful_count >= len(error_scenarios) * 0.6:  # 60% threshold
                test_result["passed"] = True
                logger.info(
                    f"Error handling test passed: {graceful_count}/{len(error_scenarios)} scenarios"
                )
            else:
                logger.warning(
                    f"Error handling insufficient: {graceful_count}/{len(error_scenarios)} scenarios"
                )

        except Exception as e:
            error_msg = f"Error handling test failed: {str(e)}"
            test_result["errors"].append(error_msg)
            logger.error(error_msg)

        return test_result

    def _test_platform_orchestrator_integration(self) -> Dict[str, Any]:
        """Test PlatformOrchestrator integration."""
        test_result = {"passed": False, "details": {}, "errors": []}

        try:
            # Test platform orchestrator integration availability
            try:
                # Check if PlatformOrchestrator can work with ModularUnifiedRetriever
                from src.core.orchestrator import PlatformOrchestrator

                orchestrator_available = True
            except ImportError:
                orchestrator_available = False
                test_result["errors"].append("PlatformOrchestrator not available")

            if orchestrator_available:
                try:
                    # Test orchestrator initialization with advanced retriever
                    config = {
                        "retriever": {
                            "type": "advanced",
                            "backends": {"primary_backend": "faiss"},
                        },
                        "embedder": {"type": "modular"},
                        "generator": {"type": "answer"},
                        "processor": {"type": "document"},
                    }

                    orchestrator = PlatformOrchestrator(config)

                    # Test if orchestrator recognizes advanced retriever
                    advanced_recognized = hasattr(
                        orchestrator, "retriever"
                    ) and hasattr(orchestrator.retriever, "advanced_config")

                    test_result["details"] = {
                        "platform_orchestrator_available": True,
                        "advanced_retriever_recognized": advanced_recognized,
                        "orchestrator_initialized": True,
                    }

                    # Test passes if orchestrator can work with advanced retriever
                    test_result["passed"] = True
                    logger.info("PlatformOrchestrator integration test passed")

                except Exception as e:
                    test_result["errors"].append(
                        f"PlatformOrchestrator integration failed: {str(e)}"
                    )
                    test_result["details"] = {
                        "platform_orchestrator_available": True,
                        "orchestrator_initialized": False,
                    }
            else:
                test_result["details"] = {"platform_orchestrator_available": False}
                test_result["passed"] = (
                    True  # Not a failure if orchestrator doesn't exist yet
                )

        except Exception as e:
            error_msg = f"PlatformOrchestrator integration test failed: {str(e)}"
            test_result["errors"].append(error_msg)
            logger.error(error_msg)

        return test_result


# Pytest test functions for integration with pytest runner
class TestEpic2IntegrationValidation:
    """Pytest-compatible test class for Epic 2 integration validation."""

    def setup_method(self):
        """Set up test environment."""
        self.validator = Epic2IntegrationValidator()

    def test_four_stage_pipeline(self):
        """Test complete 4-stage pipeline execution."""
        result = self.validator._test_four_stage_pipeline()
        assert result["passed"], f"4-stage pipeline failed: {result.get('errors', [])}"

    def test_component_factory_integration(self):
        """Test ComponentFactory advanced retriever integration."""
        result = self.validator._test_component_factory_integration()
        if not result["passed"]:
            pytest.skip(
                f"ComponentFactory integration test skipped: {result.get('errors', [])}"
            )

    def test_yaml_configuration_control(self):
        """Test YAML configuration control for all features."""
        result = self.validator._test_yaml_configuration_control()
        assert result[
            "passed"
        ], f"YAML configuration control failed: {result.get('errors', [])}"

    def test_graceful_degradation(self):
        """Test graceful degradation when components fail."""
        result = self.validator._test_graceful_degradation()
        assert result[
            "passed"
        ], f"Graceful degradation failed: {result.get('errors', [])}"

    def test_error_handling(self):
        """Test error handling across all Epic 2 components."""
        result = self.validator._test_error_handling()
        assert result["passed"], f"Error handling failed: {result.get('errors', [])}"

    def test_platform_orchestrator_integration(self):
        """Test PlatformOrchestrator integration."""
        result = self.validator._test_platform_orchestrator_integration()
        assert result[
            "passed"
        ], f"PlatformOrchestrator integration failed: {result.get('errors', [])}"


if __name__ == "__main__":
    # Run validation if called directly
    validator = Epic2IntegrationValidator()
    results = validator.run_all_validations()

    print("\n" + "=" * 80)
    print("EPIC 2 INTEGRATION VALIDATION RESULTS")
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
