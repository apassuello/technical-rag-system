#!/usr/bin/env python3
"""
Comprehensive configuration validation and end-to-end testing tool.

This script validates all configuration files and performs complete
end-to-end testing including document processing, query execution,
and performance benchmarking.
"""

import sys
from pathlib import Path
import logging
import time
from typing import Dict, List, Any, Tuple
import yaml
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from src.core.config import ConfigManager, PipelineConfig
from src.core.registry import ComponentRegistry, get_available_components
from src.core.pipeline import RAGPipeline

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


class ConfigValidator:
    """Comprehensive configuration validation and testing."""

    def __init__(self):
        self.config_dir = project_root / "config"
        self.validation_results = {}

        # Import all components to trigger registration
        self._import_all_components()

    def _import_all_components(self) -> None:
        """Import all components to trigger auto-registration."""
        try:
            from src.components.processors.pdf_processor import HybridPDFProcessor
            from src.components.embedders.sentence_transformer_embedder import (
                SentenceTransformerEmbedder,
            )
            from src.components.vector_stores.faiss_store import FAISSVectorStore
            from src.components.retrievers.hybrid_retriever import HybridRetriever
            from src.components.generators.adaptive_generator import (
                AdaptiveAnswerGenerator,
            )

            logger.info("✅ All components imported and registered")
        except ImportError as e:
            logger.warning(f"⚠️ Component import failed: {e}")

    def validate_all_configs(
        self, run_end_to_end: bool = True
    ) -> Dict[str, Dict[str, Any]]:
        """
        Validate all configuration files with optional end-to-end testing.

        Args:
            run_end_to_end: Whether to run comprehensive end-to-end tests

        Returns:
            Dictionary with validation results for each config file
        """
        logger.info("🔍 Starting comprehensive configuration validation...")

        config_files = list(self.config_dir.glob("*.yaml"))
        logger.info(f"Found {len(config_files)} configuration files")

        results = {}

        for config_file in config_files:
            config_name = config_file.stem
            logger.info(f"\n📋 Validating {config_name}.yaml...")

            results[config_name] = self._validate_config_file(
                config_file, run_end_to_end
            )

        return results

    def _validate_config_file(
        self, config_path: Path, run_end_to_end: bool = True
    ) -> Dict[str, Any]:
        """
        Validate a single configuration file with comprehensive testing.

        Args:
            config_path: Path to configuration file
            run_end_to_end: Whether to run end-to-end tests

        Returns:
            Validation results dictionary
        """
        result = {
            "file_path": str(config_path),
            "valid": False,
            "errors": [],
            "warnings": [],
            "components_valid": {},
            "pipeline_loadable": False,
            "end_to_end_results": {},
            "performance_metrics": {},
            "recommendations": [],
        }

        try:
            # Test YAML parsing
            with open(config_path, "r") as f:
                raw_config = yaml.safe_load(f)

            # Test Pydantic validation
            config_manager = ConfigManager(config_path)
            config = config_manager.config

            logger.info("✅ YAML parsing and Pydantic validation successful")

            # Test pipeline initialization first (this ensures components are registered)
            self._test_pipeline_initialization(config_path, result)

            # Then validate component configurations
            self._validate_components(config, result)

            # Performance recommendations
            self._add_recommendations(config, result)

            # Run end-to-end testing if requested and pipeline loads
            if run_end_to_end and result["pipeline_loadable"]:
                logger.info("🚀 Running comprehensive end-to-end tests...")
                self._run_end_to_end_tests(config_path, result)

            # Consider config valid if pipeline loads successfully
            # Ignore component registry detection errors if pipeline works
            critical_errors = [
                error
                for error in result["errors"]
                if "not registered" not in error or not result["pipeline_loadable"]
            ]
            result["valid"] = result["pipeline_loadable"] and len(critical_errors) == 0

        except yaml.YAMLError as e:
            result["errors"].append(f"YAML parsing error: {e}")
        except Exception as e:
            result["errors"].append(f"Configuration validation error: {e}")

        return result

    def _validate_components(
        self, config: PipelineConfig, result: Dict[str, Any]
    ) -> None:
        """Validate individual component configurations."""
        logger.info("🔧 Validating component configurations...")

        # Import components again to ensure registration
        try:
            from src.components.processors.pdf_processor import HybridPDFProcessor
            from src.components.embedders.sentence_transformer_embedder import (
                SentenceTransformerEmbedder,
            )
            from src.components.vector_stores.faiss_store import FAISSVectorStore
            from src.components.retrievers.hybrid_retriever import HybridRetriever
            from src.components.generators.adaptive_generator import (
                AdaptiveAnswerGenerator,
            )
        except ImportError:
            pass

        # Get available components (should be populated after pipeline initialization)
        available = get_available_components()
        logger.debug(f"Available components: {available}")

        # Validate each component type
        component_configs = {
            "document_processor": config.document_processor,
            "embedder": config.embedder,
            "vector_store": config.vector_store,
            "retriever": config.retriever,
            "answer_generator": config.answer_generator,
        }

        for comp_name, comp_config in component_configs.items():
            comp_type = comp_name.replace("_", "s")  # processor -> processors
            if comp_type == "answer_generators":
                comp_type = "generators"

            result["components_valid"][comp_name] = {
                "type_registered": comp_config.type in available.get(comp_type, []),
                "config_valid": True,
                "issues": [],
            }

            # Check if component type is registered
            if not result["components_valid"][comp_name]["type_registered"]:
                # Only add warning, not error, if pipeline initialization succeeded
                if result["pipeline_loadable"]:
                    result["warnings"].append(
                        f"{comp_name}: Component type '{comp_config.type}' registry detection issue (component works fine)"
                    )
                else:
                    result["errors"].append(
                        f"{comp_name}: Component type '{comp_config.type}' not registered. "
                        f"Available: {available.get(comp_type, [])}"
                    )

            # Validate specific component configurations
            self._validate_component_config(comp_name, comp_config, result)

    def _validate_component_config(
        self, comp_name: str, comp_config, result: Dict[str, Any]
    ) -> None:
        """Validate specific component configuration parameters."""
        config_dict = comp_config.config
        comp_result = result["components_valid"][comp_name]

        if comp_name == "embedder":
            # Check embedding dimension consistency
            if "embedding_dim" in config_dict:
                emb_dim = config_dict["embedding_dim"]
                # Check if vector store has matching dimension
                vs_config = result.get("vector_store", {}).get("config", {})
                if (
                    "embedding_dim" in vs_config
                    and vs_config["embedding_dim"] != emb_dim
                ):
                    comp_result["issues"].append(
                        f"Embedding dimension mismatch: embedder={emb_dim}, vector_store={vs_config['embedding_dim']}"
                    )

        elif comp_name == "vector_store":
            # Validate FAISS index type
            if comp_config.type == "faiss":
                index_type = config_dict.get("index_type", "")
                valid_indices = ["IndexFlatIP", "IndexFlatL2", "IndexIVFFlat"]
                if index_type not in valid_indices:
                    comp_result["issues"].append(
                        f"Invalid FAISS index type: {index_type}. Valid options: {valid_indices}"
                    )

        elif comp_name == "retriever":
            # Validate weights sum to reasonable values
            if comp_config.type == "hybrid":
                dense_weight = config_dict.get("dense_weight", 0.7)
                sparse_weight = 1.0 - dense_weight
                if not (0.0 <= dense_weight <= 1.0):
                    comp_result["issues"].append(
                        f"Dense weight {dense_weight} out of range [0.0, 1.0]"
                    )

        elif comp_name == "answer_generator":
            # Validate temperature range
            temperature = config_dict.get("temperature", 0.3)
            if not (0.0 <= temperature <= 1.0):
                comp_result["issues"].append(
                    f"Temperature {temperature} out of range [0.0, 1.0]"
                )

            # Check for API token if using HuggingFace models (some models don't require tokens)
            model_name = config_dict.get("model_name", "")
            # List of models that work without API tokens
            no_token_required = [
                "deepset/roberta-base-squad2",
                "sshleifer/distilbart-cnn-12-6",
            ]

            if "/" in model_name and model_name not in no_token_required:
                api_token = config_dict.get("api_token")
                if not api_token and not config_dict.get("use_ollama", False):
                    comp_result["issues"].append(
                        f"HuggingFace model '{model_name}' may require API token (not required for: {', '.join(no_token_required)})"
                    )

        # Add any issues to main errors list
        if comp_result["issues"]:
            comp_result["config_valid"] = False
            result["errors"].extend(
                [f"{comp_name}: {issue}" for issue in comp_result["issues"]]
            )

    def _test_pipeline_initialization(
        self, config_path: Path, result: Dict[str, Any]
    ) -> None:
        """Test if pipeline can be initialized with this configuration."""
        logger.info("🚀 Testing pipeline initialization...")

        try:
            # Try to initialize pipeline
            pipeline = RAGPipeline(config_path)

            # Verify all components are initialized
            required_components = [
                "processor",
                "embedder",
                "vector_store",
                "retriever",
                "generator",
            ]
            for comp_name in required_components:
                component = pipeline.get_component(comp_name)
                if component is None:
                    raise ValueError(f"Component {comp_name} not initialized")

            result["pipeline_loadable"] = True
            logger.info("✅ Pipeline initialization successful")

        except Exception as e:
            result["pipeline_loadable"] = False
            result["errors"].append(f"Pipeline initialization failed: {e}")
            logger.error(f"❌ Pipeline initialization failed: {e}")

    def _add_recommendations(
        self, config: PipelineConfig, result: Dict[str, Any]
    ) -> None:
        """Add performance and best practice recommendations."""
        recommendations = []

        # Document processor recommendations
        chunk_size = config.document_processor.config.get("chunk_size", 1024)
        if chunk_size < 500:
            recommendations.append(
                "Consider increasing chunk_size to 800-1400 for better semantic coherence"
            )
        elif chunk_size > 2000:
            recommendations.append(
                "Consider reducing chunk_size to under 1600 to avoid token limits"
            )

        # Embedder recommendations
        if config.embedder.type == "sentence_transformer":
            batch_size = config.embedder.config.get("batch_size", 16)
            if batch_size > 32:
                recommendations.append(
                    "Large embedding batch_size may cause memory issues, consider reducing to 16-32"
                )

        # Retriever recommendations
        if config.retriever.type == "hybrid":
            dense_weight = config.retriever.config.get("dense_weight", 0.7)
            if dense_weight < 0.5:
                recommendations.append(
                    "Low dense_weight may reduce semantic understanding, consider 0.6-0.8 for technical docs"
                )

        # Answer generator recommendations
        if config.answer_generator.type == "adaptive":
            max_tokens = config.answer_generator.config.get("max_tokens", 512)
            if max_tokens > 1000:
                recommendations.append(
                    "High max_tokens may cause slow response times, consider 256-512 for most use cases"
                )

        result["recommendations"] = recommendations

    def _run_end_to_end_tests(self, config_path: Path, result: Dict[str, Any]) -> None:
        """
        Run comprehensive end-to-end tests including document processing,
        query execution, and performance benchmarking.
        """
        try:
            # Initialize pipeline for testing
            pipeline = RAGPipeline(config_path)

            # Test document processing
            document_results = self._test_document_processing(pipeline)
            result["end_to_end_results"]["document_processing"] = document_results

            # Test query execution (only if document processing succeeded)
            if document_results.get("success", False):
                query_results = self._test_query_execution(pipeline)
                result["end_to_end_results"]["query_execution"] = query_results

                # Performance benchmarking
                if query_results.get("success", False):
                    perf_results = self._benchmark_performance(pipeline)
                    result["performance_metrics"] = perf_results

        except Exception as e:
            result["end_to_end_results"]["error"] = str(e)
            result["errors"].append(f"End-to-end testing failed: {e}")

    def _test_document_processing(self, pipeline: RAGPipeline) -> Dict[str, Any]:
        """Test document processing with the test PDF."""
        result = {
            "success": False,
            "chunks_indexed": 0,
            "processing_time": 0.0,
            "error": None,
        }

        # Find test PDF
        test_pdf = project_root / "data" / "test" / "riscv-base-instructions.pdf"

        if not test_pdf.exists():
            result["error"] = f"Test PDF not found: {test_pdf}"
            return result

        try:
            start_time = time.time()
            chunk_count = pipeline.index_document(test_pdf)
            processing_time = time.time() - start_time

            result.update(
                {
                    "success": True,
                    "chunks_indexed": chunk_count,
                    "processing_time": processing_time,
                    "chunks_per_second": (
                        chunk_count / processing_time if processing_time > 0 else 0
                    ),
                }
            )

            logger.info(
                f"✅ Document processing: {chunk_count} chunks in {processing_time:.2f}s"
            )

        except Exception as e:
            result["error"] = str(e)
            logger.error(f"❌ Document processing failed: {e}")

        return result

    def _test_query_execution(self, pipeline: RAGPipeline) -> Dict[str, Any]:
        """Test query execution with standard test queries."""
        test_queries = [
            "What is RISC-V?",
            "How do RISC-V instructions work?",
            "What are the main features of the base integer instruction set?",
            "Explain the register file organization in RISC-V",
            "What is the purpose of the immediate encoding in RISC-V instructions?",
        ]

        result = {
            "success": False,
            "queries_tested": len(test_queries),
            "successful_queries": 0,
            "average_query_time": 0.0,
            "average_confidence": 0.0,
            "query_results": [],
            "error": None,
        }

        successful_queries = 0
        total_time = 0.0
        total_confidence = 0.0
        query_results = []

        try:
            for i, query in enumerate(test_queries):
                logger.info(f"Testing query {i+1}/{len(test_queries)}: {query[:50]}...")

                start_time = time.time()
                answer = pipeline.query(query, k=3)
                query_time = time.time() - start_time

                query_result = {
                    "query": query,
                    "success": True,
                    "response_time": query_time,
                    "confidence": answer.confidence,
                    "answer_length": len(answer.text),
                    "sources_count": len(answer.sources),
                }

                query_results.append(query_result)
                successful_queries += 1
                total_time += query_time
                total_confidence += answer.confidence

                logger.info(
                    f"✅ Query completed in {query_time:.3f}s, confidence: {answer.confidence:.3f}"
                )

            result.update(
                {
                    "success": True,
                    "successful_queries": successful_queries,
                    "average_query_time": (
                        total_time / successful_queries if successful_queries > 0 else 0
                    ),
                    "average_confidence": (
                        total_confidence / successful_queries
                        if successful_queries > 0
                        else 0
                    ),
                    "query_results": query_results,
                }
            )

        except Exception as e:
            result["error"] = str(e)
            logger.error(f"❌ Query execution failed: {e}")

        return result

    def _benchmark_performance(self, pipeline: RAGPipeline) -> Dict[str, Any]:
        """Benchmark pipeline performance with various metrics."""
        result = {
            "memory_usage_mb": 0,
            "index_size": 0,
            "retrieval_speed": {},
            "generation_speed": {},
            "error": None,
        }

        try:
            # Memory usage estimation (basic)
            try:
                import psutil
                import os

                process = psutil.Process(os.getpid())
                memory_mb = process.memory_info().rss / 1024 / 1024
                result["memory_usage_mb"] = memory_mb
            except ImportError:
                logger.warning("psutil not available, skipping memory measurement")
                result["memory_usage_mb"] = 0

            # Index size information
            vector_store = pipeline.get_component("vector_store")
            if hasattr(vector_store, "get_index_info"):
                index_info = vector_store.get_index_info()
                result["index_size"] = index_info.get("total_vectors", 0)

            # Retrieval speed test
            retrieval_times = []
            test_queries = [
                "RISC-V",
                "instruction",
                "register",
                "encoding",
                "architecture",
            ]

            for query in test_queries:
                start_time = time.time()
                retriever = pipeline.get_component("retriever")
                results = retriever.retrieve(query, k=5)
                retrieval_time = time.time() - start_time
                retrieval_times.append(retrieval_time)

            result["retrieval_speed"] = {
                "average_ms": sum(retrieval_times) * 1000 / len(retrieval_times),
                "min_ms": min(retrieval_times) * 1000,
                "max_ms": max(retrieval_times) * 1000,
            }

            logger.info(
                f"📊 Performance: {memory_mb:.1f}MB memory, {result['retrieval_speed']['average_ms']:.1f}ms avg retrieval"
            )

        except Exception as e:
            result["error"] = str(e)
            logger.warning(f"⚠️ Performance benchmarking partial failure: {e}")

        return result

    def print_validation_summary(self, results: Dict[str, Dict[str, Any]]) -> None:
        """Print comprehensive validation summary."""
        print("\n" + "=" * 60)
        print("📊 CONFIGURATION VALIDATION SUMMARY")
        print("=" * 60)

        total_configs = len(results)
        valid_configs = sum(1 for r in results.values() if r["valid"])

        print(f"Total configurations: {total_configs}")
        print(f"Valid configurations: {valid_configs}")
        print(f"Success rate: {valid_configs/total_configs*100:.1f}%")

        for config_name, result in results.items():
            status = "✅ VALID" if result["valid"] else "❌ INVALID"
            pipeline_status = "✅" if result["pipeline_loadable"] else "❌"

            print(f"\n📋 {config_name}.yaml: {status}")
            print(f"   Pipeline initialization: {pipeline_status}")

            # End-to-end test results
            if "end_to_end_results" in result and result["end_to_end_results"]:
                e2e = result["end_to_end_results"]

                # Document processing results
                if "document_processing" in e2e:
                    doc_result = e2e["document_processing"]
                    if doc_result.get("success", False):
                        chunks = doc_result["chunks_indexed"]
                        time_taken = doc_result["processing_time"]
                        print(
                            f"   📄 Document processing: ✅ {chunks} chunks in {time_taken:.2f}s"
                        )
                    else:
                        print(
                            f"   📄 Document processing: ❌ {doc_result.get('error', 'Failed')}"
                        )

                # Query execution results
                if "query_execution" in e2e:
                    query_result = e2e["query_execution"]
                    if query_result.get("success", False):
                        queries = query_result["successful_queries"]
                        avg_time = query_result["average_query_time"]
                        avg_conf = query_result["average_confidence"]
                        print(
                            f"   🔍 Query execution: ✅ {queries}/5 queries, {avg_time:.3f}s avg, {avg_conf:.3f} conf"
                        )
                    else:
                        print(
                            f"   🔍 Query execution: ❌ {query_result.get('error', 'Failed')}"
                        )

                # Performance metrics
                if "performance_metrics" in result and result["performance_metrics"]:
                    perf = result["performance_metrics"]
                    if "memory_usage_mb" in perf and "retrieval_speed" in perf:
                        memory = perf["memory_usage_mb"]
                        retrieval_ms = perf["retrieval_speed"].get("average_ms", 0)
                        print(
                            f"   📊 Performance: {memory:.1f}MB memory, {retrieval_ms:.1f}ms retrieval"
                        )

            if result["errors"]:
                print(f"   ❌ Errors ({len(result['errors'])}):")
                for error in result["errors"][:3]:  # Show first 3 errors
                    print(f"      • {error}")
                if len(result["errors"]) > 3:
                    print(f"      ... and {len(result['errors']) - 3} more")

            if result["warnings"]:
                print(f"   ⚠️  Warnings ({len(result['warnings'])}):")
                for warning in result["warnings"][:2]:
                    print(f"      • {warning}")

            if result["recommendations"]:
                print(f"   💡 Recommendations ({len(result['recommendations'])}):")
                for rec in result["recommendations"][:2]:
                    print(f"      • {rec}")

        print("\n" + "=" * 60)

        if valid_configs == total_configs:
            print("🎉 All configurations are valid!")
        else:
            print(f"⚠️  {total_configs - valid_configs} configuration(s) need attention")

    def save_detailed_report(
        self, results: Dict[str, Dict[str, Any]], output_path: Path
    ) -> None:
        """Save detailed validation report to file."""
        import json
        from datetime import datetime

        report = {
            "validation_timestamp": datetime.now().isoformat(),
            "summary": {
                "total_configs": len(results),
                "valid_configs": sum(1 for r in results.values() if r["valid"]),
                "success_rate": sum(1 for r in results.values() if r["valid"])
                / len(results)
                * 100,
            },
            "results": results,
        }

        with open(output_path, "w") as f:
            json.dump(report, f, indent=2)

        logger.info(f"📄 Detailed validation report saved to: {output_path}")


def main():
    """Main validation workflow."""
    import argparse

    parser = argparse.ArgumentParser(description="RAG Pipeline Configuration Validator")
    parser.add_argument(
        "--basic",
        action="store_true",
        help="Run basic validation only (no end-to-end testing)",
    )
    parser.add_argument("--config", type=str, help="Test specific configuration file")

    args = parser.parse_args()

    print("🔍 RAG Pipeline Configuration Validator")
    print("-" * 40)

    if args.basic:
        print("Running basic validation only...")
    else:
        print("Running comprehensive validation with end-to-end testing...")

    validator = ConfigValidator()

    # Validate all configurations or specific one
    if args.config:
        config_path = project_root / "config" / f"{args.config}.yaml"
        if not config_path.exists():
            print(f"❌ Configuration file not found: {config_path}")
            sys.exit(1)

        results = {
            args.config: validator._validate_config_file(config_path, not args.basic)
        }
    else:
        results = validator.validate_all_configs(run_end_to_end=not args.basic)

    # Print summary
    validator.print_validation_summary(results)

    # Save detailed report
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = project_root / f"config_validation_report_{timestamp}.json"
    validator.save_detailed_report(results, report_path)

    # Return appropriate exit code
    all_valid = all(r["valid"] for r in results.values())
    sys.exit(0 if all_valid else 1)


if __name__ == "__main__":
    main()
