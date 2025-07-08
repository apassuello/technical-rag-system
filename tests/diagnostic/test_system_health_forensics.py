#!/usr/bin/env python3
"""
Test Suite 7: System Health and Performance Analysis

This test suite provides comprehensive forensic analysis of system health,
performance metrics, and deployment readiness.

Critical Focus Areas:
- Architecture detection and validation
- Component factory performance analysis
- System performance metrics and bottlenecks
- Memory usage and resource monitoring
- Cache performance and hit rates
- Deployment readiness assessment
"""

import sys
import logging
import json
import time
import psutil
import gc
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass, asdict

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from tests.diagnostic.base_diagnostic import DiagnosticTestBase, DiagnosticResult
from src.core.platform_orchestrator import PlatformOrchestrator
from src.core.component_factory import ComponentFactory
from src.core.interfaces import Document

logger = logging.getLogger(__name__)


@dataclass
class SystemHealthAnalysis:
    """Analysis results for system health and performance."""
    architecture_detected: str
    component_factory_performance: float
    system_performance_score: float  # DISABLED - was misleading
    memory_usage_efficiency: float
    cache_performance_rating: float
    deployment_readiness_score: float
    performance_bottlenecks: List[str]
    resource_optimization_opportunities: List[str]
    issues_found: List[str]
    recommendations: List[str]


class SystemHealthForensics(DiagnosticTestBase):
    """
    Forensic analysis of system health and performance.
    
    This class provides comprehensive testing of:
    - Architecture detection and validation
    - Component factory performance
    - System performance metrics
    - Memory usage and resource monitoring
    - Cache performance analysis
    - Deployment readiness assessment
    """
    
    def __init__(self):
        super().__init__()
        self.orchestrator = None
        self.baseline_memory = None
        self.performance_metrics = {}
    
    def run_all_system_health_tests(self) -> SystemHealthAnalysis:
        """
        Run comprehensive system health and performance tests.
        
        Returns:
            SystemHealthAnalysis with complete results
        """
        print("=" * 80)
        print("TEST SUITE 7: SYSTEM HEALTH AND PERFORMANCE ANALYSIS")
        print("=" * 80)
        
        # Initialize system monitoring
        self._initialize_system_monitoring()
        
        # Test 1: Architecture Detection and Validation
        print("\n🏗️ Test 7.1: Architecture Detection and Validation")
        architecture_results = self.safe_execute(
            self._test_architecture_detection_validation, 
            "Architecture_Detection_Validation", 
            "platform_orchestrator"
        )
        
        # Test 2: Component Factory Performance Analysis
        print("\n🏭 Test 7.2: Component Factory Performance Analysis")
        factory_results = self.safe_execute(
            self._test_component_factory_performance,
            "Component_Factory_Performance",
            "component_factory"
        )
        
        # Test 3: System Performance Metrics Analysis
        print("\n📊 Test 7.3: System Performance Metrics Analysis")
        performance_results = self.safe_execute(
            self._test_system_performance_metrics,
            "System_Performance_Metrics",
            "platform_orchestrator"
        )
        
        # Test 4: Memory Usage and Resource Monitoring
        print("\n🧠 Test 7.4: Memory Usage and Resource Monitoring")
        memory_results = self.safe_execute(
            self._test_memory_usage_monitoring,
            "Memory_Usage_Monitoring",
            "platform_orchestrator"
        )
        
        # Test 5: Cache Performance Analysis
        print("\n🚀 Test 7.5: Cache Performance Analysis")
        cache_results = self.safe_execute(
            self._test_cache_performance_analysis,
            "Cache_Performance_Analysis",
            "component_factory"
        )
        
        # Test 6: Deployment Readiness Assessment
        print("\n🚀 Test 7.6: Deployment Readiness Assessment")
        deployment_results = self.safe_execute(
            self._test_deployment_readiness_assessment,
            "Deployment_Readiness_Assessment",
            "platform_orchestrator"
        )
        
        # Aggregate results
        analysis = self._aggregate_health_analysis([
            architecture_results, factory_results, performance_results,
            memory_results, cache_results, deployment_results
        ])
        
        print(f"\n📊 SYSTEM HEALTH AND PERFORMANCE ANALYSIS COMPLETE")
        print(f"Architecture Detected: {analysis.architecture_detected}")
        print(f"Component Factory Performance: {analysis.component_factory_performance:.2f}")
        print(f"⚠️  System Performance Scoring DISABLED (was misleading)")
        print(f"Memory Usage Efficiency: {analysis.memory_usage_efficiency:.1%}")
        print(f"Cache Performance Rating: {analysis.cache_performance_rating:.2f}")
        print(f"Deployment Readiness Score: {analysis.deployment_readiness_score:.1%}")
        
        if analysis.performance_bottlenecks:
            print(f"\n🐌 Performance Bottlenecks ({len(analysis.performance_bottlenecks)}):")
            for bottleneck in analysis.performance_bottlenecks:
                print(f"  - {bottleneck}")
        
        if analysis.resource_optimization_opportunities:
            print(f"\n⚡ Resource Optimization Opportunities ({len(analysis.resource_optimization_opportunities)}):")
            for opportunity in analysis.resource_optimization_opportunities:
                print(f"  - {opportunity}")
        
        if analysis.issues_found:
            print(f"\n🚨 Issues Found ({len(analysis.issues_found)}):")
            for issue in analysis.issues_found:
                print(f"  - {issue}")
        
        if analysis.recommendations:
            print(f"\n💡 Recommendations ({len(analysis.recommendations)}):")
            for rec in analysis.recommendations:
                print(f"  - {rec}")
        
        return analysis
    
    def _initialize_system_monitoring(self):
        """Initialize system monitoring and baseline measurements."""
        print("  Initializing system monitoring...")
        
        # Get baseline memory usage
        self.baseline_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        
        # Initialize orchestrator
        self.orchestrator = PlatformOrchestrator("config/default.yaml")
        
        print("  ✅ System monitoring initialized")
    
    def _test_architecture_detection_validation(self) -> tuple:
        """Test architecture detection and validation."""
        print("  Testing architecture detection and validation...")
        
        architecture_results = {}
        
        try:
            # Get system health information
            health_info = self.orchestrator.get_system_health()
            
            # Analyze architecture detection
            architecture_analysis = self._analyze_architecture_detection(health_info)
            architecture_results.update(architecture_analysis)
            
            print(f"    Architecture detected: {architecture_analysis.get('architecture_type', 'unknown')}")
            print(f"    Component count: {architecture_analysis.get('component_count', 0)}")
            print(f"    Health status: {architecture_analysis.get('health_status', 'unknown')}")
            
        except Exception as e:
            print(f"    Error analyzing architecture: {e}")
            architecture_results = {
                'success': False,
                'issues': [f"Architecture detection failed: {str(e)}"]
            }
        
        # Validate architecture consistency
        consistency_analysis = self._validate_architecture_consistency()
        architecture_results.update(consistency_analysis)
        
        issues_found = architecture_results.get('issues', [])
        
        data_captured = {
            "architecture_analysis": architecture_results,
            "health_info": health_info if 'health_info' in locals() else {}
        }
        
        analysis_results = {
            "architecture_detected": architecture_results.get('architecture_type', 'unknown'),
            "architecture_valid": len(issues_found) == 0,
            "summary": f"Architecture: {architecture_results.get('architecture_type', 'unknown')}"
        }
        
        return (
            data_captured,
            analysis_results,
            list(set(issues_found)),
            self._generate_architecture_recommendations(architecture_results)
        )
    
    def _test_component_factory_performance(self) -> tuple:
        """Test component factory performance analysis."""
        print("  Testing component factory performance...")
        
        factory_results = {}
        
        try:
            # Get factory performance metrics
            factory_metrics = ComponentFactory.get_performance_metrics()
            
            # Analyze factory performance
            performance_analysis = self._analyze_factory_performance(factory_metrics)
            factory_results.update(performance_analysis)
            
            print(f"    Component creations: {factory_metrics.get('total_components_created', 0)}")
            print(f"    Cache hit rate: {factory_metrics.get('cache_hit_rate', 0):.1%}")
            print(f"    Average creation time: {factory_metrics.get('average_creation_time', 0):.3f}s")
            
        except Exception as e:
            print(f"    Error analyzing factory performance: {e}")
            factory_results = {
                'success': False,
                'issues': [f"Factory performance analysis failed: {str(e)}"]
            }
        
        issues_found = factory_results.get('issues', [])
        
        data_captured = {
            "factory_results": factory_results,
            "factory_metrics": factory_metrics if 'factory_metrics' in locals() else {}
        }
        
        analysis_results = {
            "factory_performance_data": factory_results,
            "performance_scoring_disabled": True,
            "summary": f"Factory performance data collected - manual analysis required"
        }
        
        return (
            data_captured,
            analysis_results,
            list(set(issues_found)),
            self._generate_factory_recommendations(factory_results)
        )
    
    def _test_system_performance_metrics(self) -> tuple:
        """Test system performance metrics analysis."""
        print("  Testing system performance metrics...")
        
        performance_results = {}
        
        try:
            # Test system performance with sample operations
            performance_metrics = self._measure_system_performance()
            
            # Analyze performance metrics
            performance_analysis = self._analyze_system_performance(performance_metrics)
            performance_results.update(performance_analysis)
            
            print(f"    Document processing rate: {performance_metrics.get('doc_processing_rate', 0):.0f} chars/sec")
            print(f"    Query response time: {performance_metrics.get('query_response_time', 0):.3f}s")
            print(f"    System throughput: {performance_metrics.get('system_throughput', 0):.2f} queries/sec")
            
        except Exception as e:
            print(f"    Error measuring system performance: {e}")
            performance_results = {
                'success': False,
                'issues': [f"System performance analysis failed: {str(e)}"]
            }
        
        issues_found = performance_results.get('issues', [])
        
        data_captured = {
            "performance_results": performance_results,
            "performance_metrics": performance_metrics if 'performance_metrics' in locals() else {}
        }
        
        analysis_results = {
            "system_performance_data": performance_results,
            "performance_scoring_disabled": True,
            "summary": f"System performance data collected - manual analysis required"
        }
        
        return (
            data_captured,
            analysis_results,
            list(set(issues_found)),
            self._generate_performance_recommendations(performance_results)
        )
    
    def _test_memory_usage_monitoring(self) -> tuple:
        """Test memory usage and resource monitoring."""
        print("  Testing memory usage and resource monitoring...")
        
        memory_results = {}
        
        try:
            # Monitor memory usage during operations
            memory_metrics = self._monitor_memory_usage()
            
            # Analyze memory efficiency
            memory_analysis = self._analyze_memory_efficiency(memory_metrics)
            memory_results.update(memory_analysis)
            
            print(f"    Current memory usage: {memory_metrics.get('current_memory_mb', 0):.1f} MB")
            print(f"    Peak memory usage: {memory_metrics.get('peak_memory_mb', 0):.1f} MB")
            print(f"    Memory efficiency: {memory_analysis.get('memory_efficiency', 0):.1%}")
            
        except Exception as e:
            print(f"    Error monitoring memory usage: {e}")
            memory_results = {
                'success': False,
                'issues': [f"Memory monitoring failed: {str(e)}"]
            }
        
        issues_found = memory_results.get('issues', [])
        
        data_captured = {
            "memory_results": memory_results,
            "memory_metrics": memory_metrics if 'memory_metrics' in locals() else {}
        }
        
        analysis_results = {
            "memory_usage_efficiency": memory_results.get('memory_efficiency', 0),
            "memory_usage_good": memory_results.get('memory_efficiency', 0) > 0.8,
            "summary": f"Memory efficiency: {memory_results.get('memory_efficiency', 0):.1%}"
        }
        
        return (
            data_captured,
            analysis_results,
            list(set(issues_found)),
            self._generate_memory_recommendations(memory_results)
        )
    
    def _test_cache_performance_analysis(self) -> tuple:
        """Test cache performance analysis."""
        print("  Testing cache performance analysis...")
        
        cache_results = {}
        
        try:
            # Test cache performance with repeated operations
            cache_metrics = self._measure_cache_performance()
            
            # Analyze cache effectiveness
            cache_analysis = self._analyze_cache_effectiveness(cache_metrics)
            cache_results.update(cache_analysis)
            
            print(f"    Cache hit rate: {cache_metrics.get('cache_hit_rate', 0):.1%}")
            print(f"    Cache miss rate: {cache_metrics.get('cache_miss_rate', 0):.1%}")
            print(f"    Cache effectiveness: {cache_analysis.get('cache_effectiveness', 0):.2f}")
            
        except Exception as e:
            print(f"    Error analyzing cache performance: {e}")
            cache_results = {
                'success': False,
                'issues': [f"Cache performance analysis failed: {str(e)}"]
            }
        
        issues_found = cache_results.get('issues', [])
        
        data_captured = {
            "cache_results": cache_results,
            "cache_metrics": cache_metrics if 'cache_metrics' in locals() else {}
        }
        
        analysis_results = {
            "cache_performance_rating": cache_results.get('cache_effectiveness', 0),
            "cache_performance_good": cache_results.get('cache_effectiveness', 0) > 0.8,
            "summary": f"Cache effectiveness: {cache_results.get('cache_effectiveness', 0):.2f}"
        }
        
        return (
            data_captured,
            analysis_results,
            list(set(issues_found)),
            self._generate_cache_recommendations(cache_results)
        )
    
    def _test_deployment_readiness_assessment(self) -> tuple:
        """Test deployment readiness assessment."""
        print("  Testing deployment readiness assessment...")
        
        deployment_results = {}
        
        try:
            # Assess deployment readiness
            deployment_metrics = self._assess_deployment_readiness()
            
            # Analyze deployment readiness
            deployment_analysis = self._analyze_deployment_readiness(deployment_metrics)
            deployment_results.update(deployment_analysis)
            
            print(f"    Configuration completeness: {deployment_metrics.get('config_completeness', 0):.1%}")
            print(f"    Component health: {deployment_metrics.get('component_health', 0):.1%}")
            print(f"    Deployment readiness: {deployment_analysis.get('deployment_readiness', 0):.1%}")
            
        except Exception as e:
            print(f"    Error assessing deployment readiness: {e}")
            deployment_results = {
                'success': False,
                'issues': [f"Deployment readiness assessment failed: {str(e)}"]
            }
        
        issues_found = deployment_results.get('issues', [])
        
        data_captured = {
            "deployment_results": deployment_results,
            "deployment_metrics": deployment_metrics if 'deployment_metrics' in locals() else {}
        }
        
        analysis_results = {
            "deployment_readiness_score": deployment_results.get('deployment_readiness', 0),
            "deployment_ready": deployment_results.get('deployment_readiness', 0) > 0.8,
            "summary": f"Deployment readiness: {deployment_results.get('deployment_readiness', 0):.1%}"
        }
        
        return (
            data_captured,
            analysis_results,
            list(set(issues_found)),
            self._generate_deployment_recommendations(deployment_results)
        )
    
    def _analyze_architecture_detection(self, health_info: Dict) -> Dict[str, Any]:
        """Analyze architecture detection results."""
        issues = []
        
        # Check architecture type
        architecture_type = health_info.get('architecture', 'unknown')
        if architecture_type == 'unknown':
            issues.append("Architecture type not detected")
        
        # Check component count
        component_count = len(health_info.get('component_health', {}))
        if component_count == 0:
            issues.append("No components detected")
        elif component_count < 4:
            issues.append(f"Only {component_count} components detected (expected 4+)")
        
        # Check health status
        health_status = health_info.get('status', 'unknown')
        if health_status != 'healthy':
            issues.append(f"System health status: {health_status}")
        
        return {
            'architecture_type': architecture_type,
            'component_count': component_count,
            'health_status': health_status,
            'issues': issues
        }
    
    def _validate_architecture_consistency(self) -> Dict[str, Any]:
        """Validate architecture consistency."""
        issues = []
        
        # Check if unified architecture is being used correctly
        if self.orchestrator._using_unified_retriever:
            # Should not have vector_store component
            if 'vector_store' in self.orchestrator._components:
                issues.append("Unified architecture should not have separate vector_store")
        else:
            # Legacy architecture should have vector_store
            if 'vector_store' not in self.orchestrator._components:
                issues.append("Legacy architecture missing vector_store component")
        
        return {
            'consistency_issues': issues,
            'issues': issues
        }
    
    def _analyze_factory_performance(self, factory_metrics: Dict) -> Dict[str, Any]:
        """Analyze component factory performance."""
        issues = []
        
        # Check cache hit rate
        cache_hit_rate = factory_metrics.get('cache_hit_rate', 0)
        if cache_hit_rate < 0.7:
            issues.append(f"Low cache hit rate: {cache_hit_rate:.1%}")
        
        # Check creation time
        avg_creation_time = factory_metrics.get('average_creation_time', 0)
        if avg_creation_time > 0.1:
            issues.append(f"Slow component creation: {avg_creation_time:.3f}s")
        
        # DISABLED: Performance scoring was misleading
        # performance_score = min(1.0, cache_hit_rate + (1.0 - min(1.0, avg_creation_time / 0.05)))
        
        return {
            'performance_scoring_disabled': True,
            'raw_performance_data': {
                'cache_hit_rate': cache_hit_rate,
                'avg_creation_time': avg_creation_time,
                'total_components_created': factory_metrics.get('total_components_created', 0)
            },
            'cache_hit_rate': cache_hit_rate,
            'avg_creation_time': avg_creation_time,
            'issues': issues
        }
    
    def _measure_system_performance(self) -> Dict[str, Any]:
        """Measure system performance metrics."""
        # Create test documents
        test_docs = [
            Document(
                content="RISC-V is an open-source instruction set architecture.",
                metadata={'source': 'test.pdf', 'page': 1, 'doc_id': 'test_1'},
                embedding=None
            ),
            Document(
                content="The RISC-V vector extension provides scalable processing.",
                metadata={'source': 'test.pdf', 'page': 2, 'doc_id': 'test_2'},
                embedding=None
            )
        ]
        
        # Measure document processing rate
        start_time = time.time()
        self.orchestrator.index_documents(test_docs)
        processing_time = time.time() - start_time
        
        total_chars = sum(len(doc.content) for doc in test_docs)
        doc_processing_rate = total_chars / processing_time if processing_time > 0 else 0
        
        # Measure query response time
        start_time = time.time()
        answer = self.orchestrator.process_query("What is RISC-V?")
        query_response_time = time.time() - start_time
        
        system_throughput = 1.0 / query_response_time if query_response_time > 0 else 0
        
        return {
            'doc_processing_rate': doc_processing_rate,
            'query_response_time': query_response_time,
            'system_throughput': system_throughput,
            'processing_time': processing_time
        }
    
    def _analyze_system_performance(self, performance_metrics: Dict) -> Dict[str, Any]:
        """Analyze system performance metrics."""
        issues = []
        
        # Check document processing rate
        doc_rate = performance_metrics.get('doc_processing_rate', 0)
        if doc_rate < 1000:
            issues.append(f"Slow document processing: {doc_rate:.0f} chars/sec")
        
        # Check query response time
        query_time = performance_metrics.get('query_response_time', 0)
        if query_time > 2.0:
            issues.append(f"Slow query response: {query_time:.3f}s")
        
        # Check system throughput
        throughput = performance_metrics.get('system_throughput', 0)
        if throughput < 0.5:
            issues.append(f"Low system throughput: {throughput:.2f} queries/sec")
        
        # DISABLED: Performance scoring was misleading
        # performance_score = min(1.0, (doc_rate / 1000) * 0.4 + (min(1.0, 2.0 / query_time) * 0.6))
        
        return {
            'performance_scoring_disabled': True,
            'raw_performance_data': {
                'doc_processing_rate': doc_rate,
                'query_response_time': query_time,
                'query_throughput': 1.0 / query_time if query_time > 0 else 0
            },
            'doc_processing_rate': doc_rate,
            'query_response_time': query_time,
            'system_throughput': throughput,
            'issues': issues
        }
    
    def _monitor_memory_usage(self) -> Dict[str, Any]:
        """Monitor memory usage during operations."""
        process = psutil.Process()
        
        # Get current memory usage
        current_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Force garbage collection
        gc.collect()
        
        # Monitor memory during operations
        memory_before = process.memory_info().rss / 1024 / 1024
        
        # Perform some operations
        test_doc = Document(
            content="Test document for memory monitoring.",
            metadata={'source': 'memory_test.pdf', 'page': 1, 'doc_id': 'mem_test'},
            embedding=None
        )
        self.orchestrator.index_documents([test_doc])
        self.orchestrator.process_query("Test query")
        
        memory_after = process.memory_info().rss / 1024 / 1024
        
        return {
            'baseline_memory_mb': self.baseline_memory,
            'current_memory_mb': current_memory,
            'memory_before_ops_mb': memory_before,
            'memory_after_ops_mb': memory_after,
            'memory_increase_mb': memory_after - memory_before,
            'peak_memory_mb': max(current_memory, memory_after)
        }
    
    def _analyze_memory_efficiency(self, memory_metrics: Dict) -> Dict[str, Any]:
        """Analyze memory efficiency."""
        issues = []
        
        # Check memory increase during operations
        memory_increase = memory_metrics.get('memory_increase_mb', 0)
        if memory_increase > 50:
            issues.append(f"High memory increase during operations: {memory_increase:.1f} MB")
        
        # Check peak memory usage
        peak_memory = memory_metrics.get('peak_memory_mb', 0)
        if peak_memory > 1000:
            issues.append(f"High peak memory usage: {peak_memory:.1f} MB")
        
        # Calculate memory efficiency
        baseline = memory_metrics.get('baseline_memory_mb', 100)
        efficiency = max(0, 1.0 - (peak_memory - baseline) / 1000)
        
        return {
            'memory_efficiency': efficiency,
            'peak_memory_mb': peak_memory,
            'memory_increase_mb': memory_increase,
            'issues': issues
        }
    
    def _measure_cache_performance(self) -> Dict[str, Any]:
        """Measure cache performance metrics."""
        try:
            # Get initial cache metrics
            initial_metrics = ComponentFactory.get_performance_metrics()
            
            # Perform operations that should hit cache
            for i in range(5):
                self.orchestrator.process_query(f"Test query {i}")
            
            # Get final cache metrics
            final_metrics = ComponentFactory.get_performance_metrics()
            
            return {
                'cache_hit_rate': final_metrics.get('cache_hit_rate', 0),
                'cache_miss_rate': 1.0 - final_metrics.get('cache_hit_rate', 0),
                'initial_hits': initial_metrics.get('cache_hits', 0),
                'final_hits': final_metrics.get('cache_hits', 0),
                'cache_improvement': final_metrics.get('cache_hits', 0) - initial_metrics.get('cache_hits', 0)
            }
        except Exception:
            return {
                'cache_hit_rate': 0,
                'cache_miss_rate': 1.0,
                'cache_improvement': 0
            }
    
    def _analyze_cache_effectiveness(self, cache_metrics: Dict) -> Dict[str, Any]:
        """Analyze cache effectiveness."""
        issues = []
        
        # Check cache hit rate
        hit_rate = cache_metrics.get('cache_hit_rate', 0)
        if hit_rate < 0.7:
            issues.append(f"Low cache hit rate: {hit_rate:.1%}")
        
        # Check cache improvement
        improvement = cache_metrics.get('cache_improvement', 0)
        if improvement < 3:
            issues.append(f"Low cache improvement: {improvement} hits")
        
        # Calculate cache effectiveness
        effectiveness = hit_rate * 0.8 + min(1.0, improvement / 5.0) * 0.2
        
        return {
            'cache_effectiveness': effectiveness,
            'cache_hit_rate': hit_rate,
            'cache_improvement': improvement,
            'issues': issues
        }
    
    def _assess_deployment_readiness(self) -> Dict[str, Any]:
        """Assess deployment readiness."""
        # Check configuration completeness
        config_completeness = self._check_configuration_completeness()
        
        # Check component health
        component_health = self._check_component_health()
        
        # Check resource requirements
        resource_requirements = self._check_resource_requirements()
        
        return {
            'config_completeness': config_completeness,
            'component_health': component_health,
            'resource_requirements': resource_requirements
        }
    
    def _analyze_deployment_readiness(self, deployment_metrics: Dict) -> Dict[str, Any]:
        """Analyze deployment readiness."""
        issues = []
        
        # Check configuration completeness
        config_completeness = deployment_metrics.get('config_completeness', 0)
        if config_completeness < 0.9:
            issues.append(f"Incomplete configuration: {config_completeness:.1%}")
        
        # Check component health
        component_health = deployment_metrics.get('component_health', 0)
        if component_health < 0.9:
            issues.append(f"Component health issues: {component_health:.1%}")
        
        # Calculate deployment readiness
        deployment_readiness = (config_completeness + component_health) / 2
        
        return {
            'deployment_readiness': deployment_readiness,
            'config_completeness': config_completeness,
            'component_health': component_health,
            'issues': issues
        }
    
    def _check_configuration_completeness(self) -> float:
        """Check configuration completeness."""
        required_configs = ['document_processor', 'embedder', 'retriever', 'answer_generator']
        config = self.orchestrator.config
        
        completeness = 0
        for req_config in required_configs:
            if hasattr(config, req_config) and getattr(config, req_config):
                completeness += 1
        
        return completeness / len(required_configs)
    
    def _check_component_health(self) -> float:
        """Check component health."""
        try:
            health_info = self.orchestrator.get_system_health()
            component_health = health_info.get('component_health', {})
            
            if not component_health:
                return 0.0
            
            healthy_components = sum(1 for status in component_health.values() if status == 'healthy')
            return healthy_components / len(component_health)
        except Exception:
            return 0.0
    
    def _check_resource_requirements(self) -> float:
        """Check resource requirements."""
        process = psutil.Process()
        memory_usage = process.memory_info().rss / 1024 / 1024  # MB
        
        # Check if memory usage is within reasonable limits
        if memory_usage < 500:
            return 1.0
        elif memory_usage < 1000:
            return 0.8
        else:
            return 0.5
    
    def _generate_architecture_recommendations(self, results: Dict) -> List[str]:
        """Generate recommendations for architecture."""
        recommendations = []
        
        if results.get('architecture_type') == 'unknown':
            recommendations.append("Fix architecture detection issues")
        
        if results.get('component_count', 0) < 4:
            recommendations.append("Ensure all required components are initialized")
        
        return recommendations
    
    def _generate_factory_recommendations(self, results: Dict) -> List[str]:
        """Generate recommendations for factory performance."""
        recommendations = []
        
        if results.get('performance_score', 0) < 0.8:
            recommendations.append("Optimize component factory performance")
        
        if results.get('cache_hit_rate', 0) < 0.7:
            recommendations.append("Improve component caching strategy")
        
        return recommendations
    
    def _generate_performance_recommendations(self, results: Dict) -> List[str]:
        """Generate recommendations for system performance."""
        recommendations = []
        
        if results.get('performance_score', 0) < 0.8:
            recommendations.append("Optimize system performance")
        
        if results.get('doc_processing_rate', 0) < 1000:
            recommendations.append("Improve document processing speed")
        
        return recommendations
    
    def _generate_memory_recommendations(self, results: Dict) -> List[str]:
        """Generate recommendations for memory usage."""
        recommendations = []
        
        if results.get('memory_efficiency', 0) < 0.8:
            recommendations.append("Optimize memory usage")
        
        if results.get('peak_memory_mb', 0) > 1000:
            recommendations.append("Reduce peak memory usage")
        
        return recommendations
    
    def _generate_cache_recommendations(self, results: Dict) -> List[str]:
        """Generate recommendations for cache performance."""
        recommendations = []
        
        if results.get('cache_effectiveness', 0) < 0.8:
            recommendations.append("Improve cache effectiveness")
        
        if results.get('cache_hit_rate', 0) < 0.7:
            recommendations.append("Optimize cache hit rate")
        
        return recommendations
    
    def _generate_deployment_recommendations(self, results: Dict) -> List[str]:
        """Generate recommendations for deployment."""
        recommendations = []
        
        if results.get('deployment_readiness', 0) < 0.8:
            recommendations.append("Address deployment readiness issues")
        
        if results.get('config_completeness', 0) < 0.9:
            recommendations.append("Complete configuration setup")
        
        return recommendations
    
    def _aggregate_health_analysis(self, results: List[DiagnosticResult]) -> SystemHealthAnalysis:
        """Aggregate all health test results."""
        architecture_detected = "unknown"
        factory_performance = 0
        system_performance_score = 0
        memory_efficiency = 0
        cache_performance = 0
        deployment_readiness = 0
        
        performance_bottlenecks = []
        optimization_opportunities = []
        all_issues = []
        all_recommendations = []
        
        for result in results:
            all_issues.extend(result.issues_found)
            all_recommendations.extend(result.recommendations)
            
            # Extract specific metrics
            if result.test_name == "Architecture_Detection_Validation":
                architecture_detected = result.analysis_results.get('architecture_detected', 'unknown')
            
            elif result.test_name == "Component_Factory_Performance":
                factory_performance = result.analysis_results.get('factory_performance', 0)
            
            elif result.test_name == "System_Performance_Metrics":
                system_performance_score = result.analysis_results.get('system_performance_score', 0)
            
            elif result.test_name == "Memory_Usage_Monitoring":
                memory_efficiency = result.analysis_results.get('memory_usage_efficiency', 0)
            
            elif result.test_name == "Cache_Performance_Analysis":
                cache_performance = result.analysis_results.get('cache_performance_rating', 0)
            
            elif result.test_name == "Deployment_Readiness_Assessment":
                deployment_readiness = result.analysis_results.get('deployment_readiness_score', 0)
        
        # Identify bottlenecks and opportunities
        if system_performance_score < 0.8:
            performance_bottlenecks.append("System performance below optimal")
        if cache_performance < 0.8:
            performance_bottlenecks.append("Cache performance suboptimal")
        if memory_efficiency < 0.8:
            optimization_opportunities.append("Memory usage optimization needed")
        if factory_performance < 0.8:
            optimization_opportunities.append("Component factory optimization needed")
        
        return SystemHealthAnalysis(
            architecture_detected=architecture_detected,
            component_factory_performance=factory_performance,
            system_performance_score=0.0,  # DISABLED - was misleading
            memory_usage_efficiency=memory_efficiency,
            cache_performance_rating=cache_performance,
            deployment_readiness_score=deployment_readiness,
            performance_bottlenecks=performance_bottlenecks,
            resource_optimization_opportunities=optimization_opportunities,
            issues_found=list(set(all_issues)),
            recommendations=list(set(all_recommendations))
        )


def main():
    """Run system health and performance forensic tests."""
    forensics = SystemHealthForensics()
    analysis = forensics.run_all_system_health_tests()
    
    # Save results
    results_file = project_root / f"system_health_forensics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(results_file, 'w') as f:
        json.dump(asdict(analysis), f, indent=2)
    
    print(f"\n💾 Results saved to: {results_file}")
    return analysis


if __name__ == "__main__":
    main()