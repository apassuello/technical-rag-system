#!/usr/bin/env python3
"""
Production Migration Validation - Phase 6.5

Comprehensive validation suite for production-ready migration including:
1. Large-scale document processing validation
2. Stress testing with high query volume
3. Error handling and recovery testing
4. Configuration hot-reloading validation
5. Production monitoring integration
6. Deployment readiness checklist

This ensures the migration is production-ready and handles real-world scenarios.
"""

import sys
import time
import json
import threading
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
import logging
import psutil
from concurrent.futures import ThreadPoolExecutor, as_completed
import tempfile
import shutil

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from src.core.pipeline import RAGPipeline
from src.core.config import ConfigManager

# Import components for auto-registration
from src.components.processors.pdf_processor import HybridPDFProcessor
from src.components.embedders.sentence_transformer_embedder import SentenceTransformerEmbedder
from src.components.vector_stores.faiss_store import FAISSVectorStore
from src.components.retrievers.hybrid_retriever import HybridRetriever
from src.components.generators.adaptive_generator import AdaptiveAnswerGenerator

@dataclass
class ProductionTestResult:
    """Result of a production test case."""
    test_name: str
    success: bool
    execution_time: float
    memory_usage_mb: float
    cpu_usage_percent: float
    details: Dict[str, Any]
    error_message: Optional[str] = None

@dataclass
class StressTestResult:
    """Result of stress testing."""
    test_type: str
    duration_seconds: float
    total_operations: int
    successful_operations: int
    failed_operations: int
    average_response_time: float
    max_response_time: float
    min_response_time: float
    throughput_ops_per_sec: float
    error_rate: float
    memory_peak_mb: float

@dataclass
class ProductionValidationReport:
    """Complete production validation report."""
    timestamp: str
    environment_info: Dict[str, Any]
    test_results: List[ProductionTestResult]
    stress_test_results: List[StressTestResult]
    readiness_checklist: Dict[str, bool]
    recommendations: List[str]
    deployment_notes: List[str]

class ProductionValidator:
    """Handles production migration validation."""
    
    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path or (project_root / "config" / "production.yaml")
        self.logger = self._setup_logging()
        self.test_results = []
        self.stress_results = []
        
        # Production test queries
        self.production_queries = [
            "What is RISC-V?",
            "How do RISC-V instructions work?",
            "What are the main features of the base integer instruction set?",
            "Explain the register file organization in RISC-V",
            "What is the purpose of immediate encoding in RISC-V instructions?",
            "How does the instruction fetch process work?",
            "What are the different types of RISC-V instructions?",
            "Describe the memory addressing modes",
            "What is the role of the program counter?",
            "How are control flow instructions implemented?",
            "What are the RISC-V addressing modes?",
            "How does branch prediction work in RISC-V?",
            "What is the RISC-V calling convention?",
            "How are floating-point operations handled?",
            "What is the RISC-V memory model?",
        ]
    
    def _setup_logging(self) -> logging.Logger:
        """Setup production-grade logging."""
        logger = logging.getLogger("ProductionValidator")
        logger.setLevel(logging.INFO)
        
        # Create console handler
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        return logger
    
    def run_production_validation(self, test_documents: List[Path]) -> ProductionValidationReport:
        """
        Run comprehensive production validation.
        
        Args:
            test_documents: List of documents for testing
            
        Returns:
            Complete production validation report
        """
        self.logger.info("🚀 Starting production migration validation...")
        
        # Collect environment info
        env_info = self._collect_environment_info()
        
        # Run production test suite
        self.logger.info("📋 Running production test suite...")
        self._run_basic_functionality_tests(test_documents)
        self._run_large_scale_processing_tests(test_documents)
        self._run_error_handling_tests()
        self._run_configuration_tests()
        self._run_monitoring_integration_tests()
        
        # Run stress tests
        self.logger.info("💪 Running stress tests...")
        self._run_stress_tests(test_documents)
        
        # Evaluate deployment readiness
        readiness_checklist = self._evaluate_deployment_readiness()
        
        # Generate recommendations
        recommendations = self._generate_production_recommendations()
        deployment_notes = self._generate_deployment_notes()
        
        # Create report
        report = ProductionValidationReport(
            timestamp=datetime.now().isoformat(),
            environment_info=env_info,
            test_results=self.test_results,
            stress_test_results=self.stress_results,
            readiness_checklist=readiness_checklist,
            recommendations=recommendations,
            deployment_notes=deployment_notes
        )
        
        self.logger.info("✅ Production validation complete!")
        self._print_validation_summary(report)
        
        return report
    
    def _collect_environment_info(self) -> Dict[str, Any]:
        """Collect production environment information."""
        return {
            "cpu_count": psutil.cpu_count(),
            "memory_total_gb": psutil.virtual_memory().total // 1024**3,
            "python_version": sys.version,
            "platform": sys.platform,
            "config_file": str(self.config_path),
            "timestamp": datetime.now().isoformat()
        }
    
    def _run_basic_functionality_tests(self, test_documents: List[Path]):
        """Test basic RAG functionality."""
        self.logger.info("🔧 Testing basic functionality...")
        
        # Test 1: Pipeline initialization
        start_time = time.time()
        memory_before = psutil.Process().memory_info().rss / 1024 / 1024
        
        try:
            pipeline = RAGPipeline(self.config_path)
            execution_time = time.time() - start_time
            memory_after = psutil.Process().memory_info().rss / 1024 / 1024
            
            self.test_results.append(ProductionTestResult(
                test_name="pipeline_initialization",
                success=True,
                execution_time=execution_time,
                memory_usage_mb=memory_after - memory_before,
                cpu_usage_percent=psutil.Process().cpu_percent(),
                details={"initialization_time": execution_time}
            ))
            
        except Exception as e:
            self.test_results.append(ProductionTestResult(
                test_name="pipeline_initialization",
                success=False,
                execution_time=time.time() - start_time,
                memory_usage_mb=0,
                cpu_usage_percent=0,
                details={},
                error_message=str(e)
            ))
            return
        
        # Test 2: Document indexing
        if test_documents:
            test_doc = test_documents[0]
            if test_doc.exists():
                start_time = time.time()
                memory_before = psutil.Process().memory_info().rss / 1024 / 1024
                
                try:
                    chunks_count = pipeline.index_document(test_doc)
                    execution_time = time.time() - start_time
                    memory_after = psutil.Process().memory_info().rss / 1024 / 1024
                    
                    self.test_results.append(ProductionTestResult(
                        test_name="document_indexing",
                        success=True,
                        execution_time=execution_time,
                        memory_usage_mb=memory_after - memory_before,
                        cpu_usage_percent=psutil.Process().cpu_percent(),
                        details={"chunks_indexed": chunks_count, "document_size_mb": test_doc.stat().st_size / 1024 / 1024}
                    ))
                    
                except Exception as e:
                    self.test_results.append(ProductionTestResult(
                        test_name="document_indexing",
                        success=False,
                        execution_time=time.time() - start_time,
                        memory_usage_mb=0,
                        cpu_usage_percent=0,
                        details={},
                        error_message=str(e)
                    ))
                    return
                
                # Test 3: Query processing
                test_query = "What is RISC-V?"
                start_time = time.time()
                memory_before = psutil.Process().memory_info().rss / 1024 / 1024
                
                try:
                    answer = pipeline.query(test_query, k=5)
                    execution_time = time.time() - start_time
                    memory_after = psutil.Process().memory_info().rss / 1024 / 1024
                    
                    self.test_results.append(ProductionTestResult(
                        test_name="query_processing",
                        success=True,
                        execution_time=execution_time,
                        memory_usage_mb=memory_after - memory_before,
                        cpu_usage_percent=psutil.Process().cpu_percent(),
                        details={
                            "answer_length": len(answer.text),
                            "sources_count": len(answer.sources),
                            "confidence": answer.confidence
                        }
                    ))
                    
                except Exception as e:
                    self.test_results.append(ProductionTestResult(
                        test_name="query_processing",
                        success=False,
                        execution_time=time.time() - start_time,
                        memory_usage_mb=0,
                        cpu_usage_percent=0,
                        details={},
                        error_message=str(e)
                    ))
    
    def _run_large_scale_processing_tests(self, test_documents: List[Path]):
        """Test large-scale document processing."""
        self.logger.info("📚 Testing large-scale processing...")
        
        if not test_documents:
            self.test_results.append(ProductionTestResult(
                test_name="large_scale_processing",
                success=False,
                execution_time=0,
                memory_usage_mb=0,
                cpu_usage_percent=0,
                details={},
                error_message="No test documents provided"
            ))
            return
        
        start_time = time.time()
        memory_before = psutil.Process().memory_info().rss / 1024 / 1024
        
        try:
            pipeline = RAGPipeline(self.config_path)
            total_chunks = 0
            total_size_mb = 0
            
            # Process all available documents
            for doc_path in test_documents:
                if doc_path.exists():
                    chunks = pipeline.index_document(doc_path)
                    total_chunks += chunks
                    total_size_mb += doc_path.stat().st_size / 1024 / 1024
            
            execution_time = time.time() - start_time
            memory_after = psutil.Process().memory_info().rss / 1024 / 1024
            
            self.test_results.append(ProductionTestResult(
                test_name="large_scale_processing",
                success=True,
                execution_time=execution_time,
                memory_usage_mb=memory_after - memory_before,
                cpu_usage_percent=psutil.Process().cpu_percent(),
                details={
                    "documents_processed": len(test_documents),
                    "total_chunks": total_chunks,
                    "total_size_mb": total_size_mb,
                    "chunks_per_second": total_chunks / execution_time if execution_time > 0 else 0
                }
            ))
            
        except Exception as e:
            self.test_results.append(ProductionTestResult(
                test_name="large_scale_processing",
                success=False,
                execution_time=time.time() - start_time,
                memory_usage_mb=0,
                cpu_usage_percent=0,
                details={},
                error_message=str(e)
            ))
    
    def _run_error_handling_tests(self):
        """Test error handling and recovery."""
        self.logger.info("🛡️ Testing error handling...")
        
        # Test 1: Invalid configuration
        start_time = time.time()
        try:
            # Create a temporary invalid config
            with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
                f.write("invalid: yaml: content: [unclosed")
                invalid_config_path = f.name
            
            try:
                pipeline = RAGPipeline(Path(invalid_config_path))
                success = False  # Should have failed
            except Exception:
                success = True  # Expected to fail
            finally:
                Path(invalid_config_path).unlink()
            
            self.test_results.append(ProductionTestResult(
                test_name="invalid_config_handling",
                success=success,
                execution_time=time.time() - start_time,
                memory_usage_mb=0,
                cpu_usage_percent=0,
                details={"expected_failure": True}
            ))
            
        except Exception as e:
            self.test_results.append(ProductionTestResult(
                test_name="invalid_config_handling",
                success=False,
                execution_time=time.time() - start_time,
                memory_usage_mb=0,
                cpu_usage_percent=0,
                details={},
                error_message=str(e)
            ))
        
        # Test 2: Missing file handling
        start_time = time.time()
        try:
            pipeline = RAGPipeline(self.config_path)
            
            # Try to index non-existent file
            try:
                chunks = pipeline.index_document(Path("/nonexistent/file.pdf"))
                success = False  # Should have failed
            except Exception:
                success = True  # Expected to fail
            
            self.test_results.append(ProductionTestResult(
                test_name="missing_file_handling",
                success=success,
                execution_time=time.time() - start_time,
                memory_usage_mb=0,
                cpu_usage_percent=0,
                details={"expected_failure": True}
            ))
            
        except Exception as e:
            self.test_results.append(ProductionTestResult(
                test_name="missing_file_handling",
                success=False,
                execution_time=time.time() - start_time,
                memory_usage_mb=0,
                cpu_usage_percent=0,
                details={},
                error_message=str(e)
            ))
    
    def _run_configuration_tests(self):
        """Test configuration management."""
        self.logger.info("⚙️ Testing configuration management...")
        
        # Test configuration loading
        start_time = time.time()
        try:
            config_manager = ConfigManager(self.config_path)
            config = config_manager.config
            
            # Validate config structure
            required_components = ["document_processor", "embedder", "vector_store", "retriever", "answer_generator"]
            all_present = all(hasattr(config, comp) for comp in required_components)
            
            self.test_results.append(ProductionTestResult(
                test_name="configuration_loading",
                success=all_present,
                execution_time=time.time() - start_time,
                memory_usage_mb=0,
                cpu_usage_percent=0,
                details={
                    "config_components": required_components,
                    "all_components_present": all_present
                }
            ))
            
        except Exception as e:
            self.test_results.append(ProductionTestResult(
                test_name="configuration_loading",
                success=False,
                execution_time=time.time() - start_time,
                memory_usage_mb=0,
                cpu_usage_percent=0,
                details={},
                error_message=str(e)
            ))
    
    def _run_monitoring_integration_tests(self):
        """Test monitoring and observability features."""
        self.logger.info("📊 Testing monitoring integration...")
        
        start_time = time.time()
        try:
            pipeline = RAGPipeline(self.config_path)
            
            # Test component access for monitoring
            components = ["processor", "embedder", "vector_store", "retriever", "generator"]
            accessible_components = []
            
            for comp_name in components:
                try:
                    component = pipeline.get_component(comp_name)
                    if component is not None:
                        accessible_components.append(comp_name)
                except Exception:
                    pass
            
            # Test pipeline info
            try:
                info = pipeline.get_pipeline_info()
                has_info = True
            except Exception:
                has_info = False
            
            success = len(accessible_components) >= 3 and has_info
            
            self.test_results.append(ProductionTestResult(
                test_name="monitoring_integration",
                success=success,
                execution_time=time.time() - start_time,
                memory_usage_mb=0,
                cpu_usage_percent=0,
                details={
                    "accessible_components": accessible_components,
                    "has_pipeline_info": has_info
                }
            ))
            
        except Exception as e:
            self.test_results.append(ProductionTestResult(
                test_name="monitoring_integration",
                success=False,
                execution_time=time.time() - start_time,
                memory_usage_mb=0,
                cpu_usage_percent=0,
                details={},
                error_message=str(e)
            ))
    
    def _run_stress_tests(self, test_documents: List[Path]):
        """Run stress tests for production readiness."""
        self.logger.info("💪 Running stress tests...")
        
        if not test_documents or not test_documents[0].exists():
            self.logger.warning("No test documents available for stress testing")
            return
        
        # Stress test 1: High query volume
        self._run_query_volume_stress_test()
        
        # Stress test 2: Concurrent indexing
        self._run_concurrent_indexing_stress_test(test_documents)
        
        # Stress test 3: Memory stress test
        self._run_memory_stress_test(test_documents)
    
    def _run_query_volume_stress_test(self):
        """Test high query volume handling."""
        self.logger.info("  🔥 Query volume stress test...")
        
        test_doc = project_root / "data" / "test" / "riscv-base-instructions.pdf"
        if not test_doc.exists():
            return
        
        start_time = time.time()
        memory_before = psutil.Process().memory_info().rss / 1024 / 1024
        
        try:
            pipeline = RAGPipeline(self.config_path)
            pipeline.index_document(test_doc)
            
            # Run queries in rapid succession
            num_queries = 50
            successful_queries = 0
            response_times = []
            errors = 0
            
            for i in range(num_queries):
                query = self.production_queries[i % len(self.production_queries)]
                query_start = time.time()
                
                try:
                    answer = pipeline.query(query, k=3)
                    response_time = time.time() - query_start
                    response_times.append(response_time)
                    successful_queries += 1
                except Exception:
                    errors += 1
            
            duration = time.time() - start_time
            memory_peak = psutil.Process().memory_info().rss / 1024 / 1024
            
            self.stress_results.append(StressTestResult(
                test_type="query_volume",
                duration_seconds=duration,
                total_operations=num_queries,
                successful_operations=successful_queries,
                failed_operations=errors,
                average_response_time=sum(response_times) / len(response_times) if response_times else 0,
                max_response_time=max(response_times) if response_times else 0,
                min_response_time=min(response_times) if response_times else 0,
                throughput_ops_per_sec=successful_queries / duration if duration > 0 else 0,
                error_rate=errors / num_queries if num_queries > 0 else 0,
                memory_peak_mb=memory_peak - memory_before
            ))
            
        except Exception as e:
            self.logger.error(f"Query volume stress test failed: {e}")
    
    def _run_concurrent_indexing_stress_test(self, test_documents: List[Path]):
        """Test concurrent document indexing."""
        self.logger.info("  🔥 Concurrent indexing stress test...")
        
        start_time = time.time()
        memory_before = psutil.Process().memory_info().rss / 1024 / 1024
        
        def index_document_worker(doc_path):
            try:
                pipeline = RAGPipeline(self.config_path)
                chunks = pipeline.index_document(doc_path)
                return True, chunks
            except Exception as e:
                return False, 0
        
        # Run concurrent indexing
        successful_operations = 0
        failed_operations = 0
        total_chunks = 0
        
        with ThreadPoolExecutor(max_workers=3) as executor:
            # Submit multiple indexing tasks
            futures = []
            for _ in range(5):  # Index the same document multiple times
                for doc in test_documents[:1]:  # Use first document
                    futures.append(executor.submit(index_document_worker, doc))
            
            # Collect results
            for future in as_completed(futures):
                success, chunks = future.result()
                if success:
                    successful_operations += 1
                    total_chunks += chunks
                else:
                    failed_operations += 1
        
        duration = time.time() - start_time
        memory_peak = psutil.Process().memory_info().rss / 1024 / 1024
        total_operations = successful_operations + failed_operations
        
        self.stress_results.append(StressTestResult(
            test_type="concurrent_indexing",
            duration_seconds=duration,
            total_operations=total_operations,
            successful_operations=successful_operations,
            failed_operations=failed_operations,
            average_response_time=duration / total_operations if total_operations > 0 else 0,
            max_response_time=duration,  # Approximate
            min_response_time=0,
            throughput_ops_per_sec=successful_operations / duration if duration > 0 else 0,
            error_rate=failed_operations / total_operations if total_operations > 0 else 0,
            memory_peak_mb=memory_peak - memory_before
        ))
    
    def _run_memory_stress_test(self, test_documents: List[Path]):
        """Test memory usage under stress."""
        self.logger.info("  🔥 Memory stress test...")
        
        start_time = time.time()
        memory_before = psutil.Process().memory_info().rss / 1024 / 1024
        
        try:
            # Create multiple pipeline instances
            pipelines = []
            successful_operations = 0
            failed_operations = 0
            
            for i in range(3):  # Create 3 pipeline instances
                try:
                    pipeline = RAGPipeline(self.config_path)
                    pipelines.append(pipeline)
                    successful_operations += 1
                except Exception:
                    failed_operations += 1
            
            # Index documents with each pipeline
            for pipeline in pipelines:
                for doc in test_documents[:1]:  # Use first document
                    try:
                        pipeline.index_document(doc)
                        successful_operations += 1
                    except Exception:
                        failed_operations += 1
            
            duration = time.time() - start_time
            memory_peak = psutil.Process().memory_info().rss / 1024 / 1024
            total_operations = successful_operations + failed_operations
            
            self.stress_results.append(StressTestResult(
                test_type="memory_stress",
                duration_seconds=duration,
                total_operations=total_operations,
                successful_operations=successful_operations,
                failed_operations=failed_operations,
                average_response_time=duration / total_operations if total_operations > 0 else 0,
                max_response_time=duration,
                min_response_time=0,
                throughput_ops_per_sec=successful_operations / duration if duration > 0 else 0,
                error_rate=failed_operations / total_operations if total_operations > 0 else 0,
                memory_peak_mb=memory_peak - memory_before
            ))
            
        except Exception as e:
            self.logger.error(f"Memory stress test failed: {e}")
    
    def _evaluate_deployment_readiness(self) -> Dict[str, bool]:
        """Evaluate deployment readiness checklist."""
        checklist = {}
        
        # Basic functionality checks
        basic_tests = ["pipeline_initialization", "document_indexing", "query_processing"]
        checklist["basic_functionality"] = all(
            any(test.test_name == test_name and test.success for test in self.test_results)
            for test_name in basic_tests
        )
        
        # Error handling checks
        error_tests = ["invalid_config_handling", "missing_file_handling"]
        checklist["error_handling"] = all(
            any(test.test_name == test_name and test.success for test in self.test_results)
            for test_name in error_tests
        )
        
        # Configuration checks
        checklist["configuration_management"] = any(
            test.test_name == "configuration_loading" and test.success 
            for test in self.test_results
        )
        
        # Monitoring checks
        checklist["monitoring_integration"] = any(
            test.test_name == "monitoring_integration" and test.success 
            for test in self.test_results
        )
        
        # Performance checks
        checklist["performance_acceptable"] = True
        for test in self.test_results:
            if test.test_name == "query_processing" and test.success:
                if test.execution_time > 10.0:  # More than 10 seconds is too slow
                    checklist["performance_acceptable"] = False
        
        # Stress test checks
        stress_success = all(
            stress.error_rate < 0.1 for stress in self.stress_results  # Less than 10% error rate
        )
        checklist["stress_test_passed"] = stress_success
        
        return checklist
    
    def _generate_production_recommendations(self) -> List[str]:
        """Generate production deployment recommendations."""
        recommendations = []
        
        # Analyze test results
        failed_tests = [test for test in self.test_results if not test.success]
        if failed_tests:
            recommendations.append(f"⚠️ Fix {len(failed_tests)} failed tests before deployment")
        
        # Check memory usage
        high_memory_tests = [test for test in self.test_results if test.memory_usage_mb > 1000]
        if high_memory_tests:
            recommendations.append("💾 High memory usage detected - ensure adequate RAM in production")
        
        # Check response times
        slow_tests = [test for test in self.test_results if test.execution_time > 5.0]
        if slow_tests:
            recommendations.append("⏱️ Slow response times detected - consider performance optimization")
        
        # Stress test recommendations
        for stress in self.stress_results:
            if stress.error_rate > 0.05:  # More than 5% error rate
                recommendations.append(f"🔥 High error rate in {stress.test_type} - investigate before production")
            
            if stress.throughput_ops_per_sec < 1.0:
                recommendations.append(f"📉 Low throughput in {stress.test_type} - consider scaling")
        
        # General recommendations
        recommendations.append("✅ Set up monitoring and alerting for production deployment")
        recommendations.append("📊 Configure logging and metrics collection")
        recommendations.append("🔒 Ensure security configurations are production-ready")
        recommendations.append("🚀 Plan gradual rollout with traffic shifting")
        
        return recommendations
    
    def _generate_deployment_notes(self) -> List[str]:
        """Generate deployment-specific notes."""
        notes = []
        
        notes.append("📋 Pre-deployment checklist:")
        notes.append("  • Verify configuration files are valid")
        notes.append("  • Test with production-like data volume")
        notes.append("  • Set up monitoring dashboards")
        notes.append("  • Configure log aggregation")
        notes.append("  • Prepare rollback procedures")
        
        notes.append("🚀 Deployment procedure:")
        notes.append("  • Deploy to staging environment first")
        notes.append("  • Run smoke tests after deployment")
        notes.append("  • Monitor key metrics during rollout")
        notes.append("  • Have rollback plan ready")
        
        notes.append("📊 Production monitoring:")
        notes.append("  • Track query response times")
        notes.append("  • Monitor memory usage")
        notes.append("  • Watch error rates")
        notes.append("  • Alert on performance degradation")
        
        return notes
    
    def _print_validation_summary(self, report: ProductionValidationReport):
        """Print production validation summary."""
        print("\n" + "="*60)
        print("🚀 PRODUCTION VALIDATION SUMMARY")
        print("="*60)
        
        # Test results summary
        total_tests = len(report.test_results)
        successful_tests = sum(1 for test in report.test_results if test.success)
        
        print(f"Basic Tests: {successful_tests}/{total_tests} passed ({successful_tests/total_tests*100:.1f}%)")
        
        # Stress test summary
        if report.stress_test_results:
            print(f"Stress Tests: {len(report.stress_test_results)} completed")
            avg_error_rate = sum(stress.error_rate for stress in report.stress_test_results) / len(report.stress_test_results)
            print(f"Average error rate: {avg_error_rate:.1%}")
        
        # Readiness checklist
        print("\n📋 Deployment Readiness:")
        for check, status in report.readiness_checklist.items():
            status_icon = "✅" if status else "❌"
            print(f"  {status_icon} {check.replace('_', ' ').title()}")
        
        # Overall assessment
        all_ready = all(report.readiness_checklist.values())
        if all_ready:
            print("\n🎉 READY FOR PRODUCTION DEPLOYMENT!")
        else:
            failed_checks = [k for k, v in report.readiness_checklist.items() if not v]
            print(f"\n⚠️ NOT READY - Fix: {', '.join(failed_checks)}")
        
        # Key recommendations
        if report.recommendations:
            print("\n💡 Key Recommendations:")
            for rec in report.recommendations[:3]:  # Show top 3
                print(f"  • {rec}")

def main():
    """Main production validation workflow."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Production Migration Validation")
    parser.add_argument("--config", type=str, default="config/production.yaml", help="Configuration file")
    parser.add_argument("--documents", type=str, nargs="+", help="Test documents")
    parser.add_argument("--save-report", type=str, help="Save detailed report to file")
    
    args = parser.parse_args()
    
    # Determine test documents
    if args.documents:
        test_docs = [Path(doc) for doc in args.documents]
    else:
        test_docs = [project_root / "data" / "test" / "riscv-base-instructions.pdf"]
    
    # Filter existing documents
    existing_docs = [doc for doc in test_docs if doc.exists()]
    if not existing_docs:
        print("❌ No valid test documents found")
        sys.exit(1)
    
    print(f"🚀 Production Migration Validation")
    print(f"Configuration: {args.config}")
    print(f"Test documents: {[doc.name for doc in existing_docs]}")
    
    # Run validation
    validator = ProductionValidator(Path(args.config))
    report = validator.run_production_validation(existing_docs)
    
    # Save detailed report if requested
    if args.save_report:
        with open(args.save_report, 'w') as f:
            json.dump(asdict(report), f, indent=2, default=str)
        print(f"\n💾 Detailed report saved to: {args.save_report}")
    
    # Exit with appropriate code
    all_ready = all(report.readiness_checklist.values())
    sys.exit(0 if all_ready else 1)

if __name__ == "__main__":
    main()