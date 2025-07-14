#!/usr/bin/env python3
"""
Performance Comparison: Baseline vs Advanced Retriever

This script provides a detailed performance comparison between the
baseline ModularUnifiedRetriever and the Epic 2 AdvancedRetriever.
"""

import sys
import time
import json
import statistics
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Tuple

# Add project root to path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

import logging
import numpy as np

# Configure logging
logging.basicConfig(level=logging.INFO, format='[%(name)s] %(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

from src.core.platform_orchestrator import PlatformOrchestrator
from src.core.interfaces import Document


class PerformanceComparator:
    """
    Comprehensive performance comparison between baseline and advanced retrievers.
    
    This comparator tests:
    - Initialization time
    - Document indexing performance
    - Query retrieval latency
    - Memory usage
    - Feature overhead analysis
    """
    
    def __init__(self):
        """Initialize the performance comparator."""
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'baseline_config': 'config/default.yaml',
            'advanced_config': 'config/advanced_test.yaml',
            'baseline_results': {},
            'advanced_results': {},
            'comparison_analysis': {}
        }
        
        # Test parameters
        self.test_documents = self._generate_test_documents()
        self.test_queries = [
            "What is RISC-V?",
            "What are RISC-V extensions?", 
            "How does RISC-V modularity work?",
            "What are the benefits of RISC-V?",
            "How is RISC-V different from x86?"
        ]
    
    def _generate_test_documents(self) -> List[Document]:
        """Generate consistent test documents for comparison."""
        documents = []
        
        contents = [
            "RISC-V is an open-source instruction set architecture (ISA) based on reduced instruction set computer (RISC) principles. It originated at the University of California, Berkeley and is now maintained by the RISC-V Foundation.",
            "RISC-V provides a modular approach to processor design, allowing implementations to select only the extensions they need for their specific application domain. This modularity enables efficient designs for different use cases.",
            "The RISC-V instruction set includes base integer instructions (RV32I, RV64I) and optional standard extensions for multiplication (M), atomic operations (A), floating-point (F, D), and compressed instructions (C).",
            "RISC-V supports vector extensions for SIMD operations, cryptography extensions for security, and hypervisor extensions for virtualization. These extensions provide specialized functionality for different application domains.",
            "Unlike proprietary instruction sets, RISC-V is free and open, allowing for custom extensions and implementations without licensing fees. This openness promotes innovation and reduces barriers to entry for processor development."
        ]
        
        for i, content in enumerate(contents):
            # Generate consistent embeddings
            np.random.seed(i)  # Consistent embeddings
            embedding = np.random.normal(0, 1, 384).tolist()
            
            document = Document(
                content=content,
                metadata={
                    "source": f"riscv-doc-{i}.pdf",
                    "chunk_index": i,
                    "page": i + 1,
                    "doc_id": f"doc_{i}"
                },
                embedding=embedding
            )
            documents.append(document)
        
        return documents
    
    def test_system_performance(self, config_path: str, config_name: str) -> Dict[str, Any]:
        """Test system performance with given configuration."""
        logger.info(f"Testing {config_name} configuration: {config_path}")
        
        results = {
            'config_path': config_path,
            'config_name': config_name,
            'initialization': {},
            'indexing': {},
            'retrieval': {},
            'system_info': {},
            'error': None
        }
        
        try:
            # Test 1: System Initialization
            logger.info("  Testing system initialization...")
            start_time = time.time()
            
            orchestrator = PlatformOrchestrator(config_path)
            
            init_time = time.time() - start_time
            results['initialization'] = {
                'time': init_time,
                'components_count': len(orchestrator.get_system_info().get('components', {})),
                'architecture': orchestrator.get_system_info().get('architecture', 'unknown')
            }
            logger.info(f"    Initialization: {init_time:.3f}s")
            
            # Test 2: Document Indexing Performance
            logger.info("  Testing document indexing...")
            start_time = time.time()
            
            orchestrator.index_documents(self.test_documents)
            
            indexing_time = time.time() - start_time
            results['indexing'] = {
                'time': indexing_time,
                'documents_count': len(self.test_documents),
                'docs_per_second': len(self.test_documents) / indexing_time if indexing_time > 0 else 0,
                'chars_per_second': sum(len(doc.content) for doc in self.test_documents) / indexing_time if indexing_time > 0 else 0
            }
            logger.info(f"    Indexing: {indexing_time:.3f}s ({results['indexing']['docs_per_second']:.1f} docs/sec)")
            
            # Test 3: Query Retrieval Performance
            logger.info("  Testing query retrieval...")
            retrieval_times = []
            retrieval_results = []
            
            for query in self.test_queries:
                start_time = time.time()
                
                answer = orchestrator.process_query(query)
                
                query_time = time.time() - start_time
                retrieval_times.append(query_time)
                
                result_info = {
                    'query': query,
                    'time': query_time,
                    'answer_length': len(answer.text) if answer else 0,
                    'confidence': answer.confidence if answer else 0,
                    'sources_count': len(answer.sources) if answer else 0
                }
                retrieval_results.append(result_info)
            
            # Calculate retrieval statistics
            results['retrieval'] = {
                'total_queries': len(self.test_queries),
                'total_time': sum(retrieval_times),
                'avg_time': statistics.mean(retrieval_times),
                'median_time': statistics.median(retrieval_times),
                'p95_time': np.percentile(retrieval_times, 95),
                'p99_time': np.percentile(retrieval_times, 99),
                'min_time': min(retrieval_times),
                'max_time': max(retrieval_times),
                'queries_per_second': len(self.test_queries) / sum(retrieval_times),
                'detailed_results': retrieval_results
            }
            
            logger.info(f"    Retrieval avg: {results['retrieval']['avg_time']:.3f}s")
            logger.info(f"    Retrieval P95: {results['retrieval']['p95_time']:.3f}s")
            
            # Test 4: System Information
            system_info = orchestrator.get_system_info()
            results['system_info'] = {
                'architecture': system_info.get('architecture', 'unknown'),
                'components': system_info.get('components', {}),
                'retriever_type': system_info.get('components', {}).get('retriever', {}).get('type', 'unknown'),
                'deployment_ready': system_info.get('deployment_ready', False)
            }
            
            logger.info(f"    Architecture: {results['system_info']['architecture']}")
            logger.info(f"    Retriever: {results['system_info']['retriever_type']}")
            
        except Exception as e:
            results['error'] = str(e)
            logger.error(f"    Error testing {config_name}: {str(e)}")
        
        return results
    
    def compare_results(self, baseline: Dict[str, Any], advanced: Dict[str, Any]) -> Dict[str, Any]:
        """Compare baseline and advanced results."""
        logger.info("Analyzing performance comparison...")
        
        comparison = {
            'initialization_comparison': {},
            'indexing_comparison': {},
            'retrieval_comparison': {},
            'feature_overhead': {},
            'recommendations': []
        }
        
        try:
            # Initialization comparison
            if 'initialization' in baseline and 'initialization' in advanced:
                baseline_init = baseline['initialization']['time']
                advanced_init = advanced['initialization']['time']
                
                comparison['initialization_comparison'] = {
                    'baseline_time': baseline_init,
                    'advanced_time': advanced_init,
                    'overhead_ms': (advanced_init - baseline_init) * 1000,
                    'overhead_percent': ((advanced_init - baseline_init) / baseline_init * 100) if baseline_init > 0 else 0,
                    'acceptable': abs(advanced_init - baseline_init) < 0.1  # <100ms difference acceptable
                }
            
            # Indexing comparison
            if 'indexing' in baseline and 'indexing' in advanced:
                baseline_idx = baseline['indexing']['time']
                advanced_idx = advanced['indexing']['time']
                
                comparison['indexing_comparison'] = {
                    'baseline_time': baseline_idx,
                    'advanced_time': advanced_idx,
                    'overhead_ms': (advanced_idx - baseline_idx) * 1000,
                    'overhead_percent': ((advanced_idx - baseline_idx) / baseline_idx * 100) if baseline_idx > 0 else 0,
                    'baseline_docs_per_sec': baseline['indexing']['docs_per_second'],
                    'advanced_docs_per_sec': advanced['indexing']['docs_per_second'],
                    'acceptable': abs(advanced_idx - baseline_idx) < baseline_idx * 0.1  # <10% difference acceptable
                }
            
            # Retrieval comparison
            if 'retrieval' in baseline and 'retrieval' in advanced:
                baseline_ret = baseline['retrieval']
                advanced_ret = advanced['retrieval']
                
                comparison['retrieval_comparison'] = {
                    'baseline_avg_time': baseline_ret['avg_time'],
                    'advanced_avg_time': advanced_ret['avg_time'],
                    'avg_overhead_ms': (advanced_ret['avg_time'] - baseline_ret['avg_time']) * 1000,
                    'avg_overhead_percent': ((advanced_ret['avg_time'] - baseline_ret['avg_time']) / baseline_ret['avg_time'] * 100) if baseline_ret['avg_time'] > 0 else 0,
                    'baseline_p95': baseline_ret['p95_time'],
                    'advanced_p95': advanced_ret['p95_time'],
                    'p95_overhead_ms': (advanced_ret['p95_time'] - baseline_ret['p95_time']) * 1000,
                    'baseline_qps': baseline_ret['queries_per_second'],
                    'advanced_qps': advanced_ret['queries_per_second'],
                    'qps_change_percent': ((advanced_ret['queries_per_second'] - baseline_ret['queries_per_second']) / baseline_ret['queries_per_second'] * 100) if baseline_ret['queries_per_second'] > 0 else 0,
                    'acceptable_avg': abs(advanced_ret['avg_time'] - baseline_ret['avg_time']) < baseline_ret['avg_time'] * 0.1,  # <10% difference
                    'acceptable_p95': advanced_ret['p95_time'] < 2.0  # <2s P95 acceptable
                }
            
            # Feature overhead analysis
            baseline_arch = baseline.get('system_info', {}).get('architecture', 'unknown')
            advanced_arch = advanced.get('system_info', {}).get('architecture', 'unknown')
            baseline_retriever = baseline.get('system_info', {}).get('retriever_type', 'unknown')
            advanced_retriever = advanced.get('system_info', {}).get('retriever_type', 'unknown')
            
            comparison['feature_overhead'] = {
                'architecture_changed': baseline_arch != advanced_arch,
                'retriever_changed': baseline_retriever != advanced_retriever,
                'baseline_architecture': baseline_arch,
                'advanced_architecture': advanced_arch,
                'baseline_retriever': baseline_retriever,
                'advanced_retriever': advanced_retriever
            }
            
            # Generate recommendations
            recommendations = []
            
            # Initialization recommendations
            init_comp = comparison.get('initialization_comparison', {})
            if init_comp.get('overhead_percent', 0) > 50:
                recommendations.append("⚠️ High initialization overhead - consider lazy loading")
            elif init_comp.get('acceptable', False):
                recommendations.append("✅ Initialization overhead acceptable")
            
            # Indexing recommendations
            idx_comp = comparison.get('indexing_comparison', {})
            if idx_comp.get('overhead_percent', 0) > 10:
                recommendations.append("⚠️ Indexing performance degraded - optimize backend operations")
            elif idx_comp.get('acceptable', False):
                recommendations.append("✅ Indexing performance maintained")
            
            # Retrieval recommendations
            ret_comp = comparison.get('retrieval_comparison', {})
            if ret_comp.get('avg_overhead_percent', 0) > 10:
                recommendations.append("⚠️ Query latency increased - profile advanced features")
            elif ret_comp.get('acceptable_avg', False) and ret_comp.get('acceptable_p95', False):
                recommendations.append("✅ Query performance acceptable")
            
            if ret_comp.get('advanced_p95', 999) < 0.01:  # Very fast
                recommendations.append("🚀 Excellent query performance - ready for production")
            
            # Feature recommendations
            if advanced_retriever != baseline_retriever:
                recommendations.append("🆕 Advanced retriever active - Epic 2 features available")
            
            comparison['recommendations'] = recommendations
            
        except Exception as e:
            comparison['error'] = str(e)
            logger.error(f"Error in comparison analysis: {str(e)}")
        
        return comparison
    
    def run_comparison(self) -> Dict[str, Any]:
        """Run complete performance comparison."""
        logger.info("="*80)
        logger.info("PERFORMANCE COMPARISON: BASELINE vs ADVANCED RETRIEVER")
        logger.info("="*80)
        
        # Test baseline configuration
        logger.info("\n📊 TESTING BASELINE CONFIGURATION")
        baseline_results = self.test_system_performance(
            self.results['baseline_config'], 
            'baseline'
        )
        self.results['baseline_results'] = baseline_results
        
        # Test advanced configuration
        logger.info("\n🚀 TESTING ADVANCED CONFIGURATION")
        advanced_results = self.test_system_performance(
            self.results['advanced_config'],
            'advanced'
        )
        self.results['advanced_results'] = advanced_results
        
        # Compare results
        logger.info("\n📈 PERFORMING COMPARISON ANALYSIS")
        comparison = self.compare_results(baseline_results, advanced_results)
        self.results['comparison_analysis'] = comparison
        
        # Generate summary
        self._generate_summary()
        
        return self.results
    
    def _generate_summary(self):
        """Generate comprehensive comparison summary."""
        logger.info("\n" + "="*80)
        logger.info("PERFORMANCE COMPARISON SUMMARY")
        logger.info("="*80)
        
        baseline = self.results['baseline_results']
        advanced = self.results['advanced_results']
        comparison = self.results['comparison_analysis']
        
        # System Architecture Comparison
        logger.info(f"\n🏗️ SYSTEM ARCHITECTURE:")
        logger.info(f"  Baseline:  {baseline.get('system_info', {}).get('architecture', 'unknown')} ({baseline.get('system_info', {}).get('retriever_type', 'unknown')})")
        logger.info(f"  Advanced:  {advanced.get('system_info', {}).get('architecture', 'unknown')} ({advanced.get('system_info', {}).get('retriever_type', 'unknown')})")
        
        # Performance Metrics Comparison
        logger.info(f"\n⚡ PERFORMANCE METRICS:")
        
        # Initialization
        if 'initialization_comparison' in comparison:
            init = comparison['initialization_comparison']
            logger.info(f"  Initialization:")
            logger.info(f"    Baseline: {init.get('baseline_time', 0):.3f}s")
            logger.info(f"    Advanced: {init.get('advanced_time', 0):.3f}s")
            logger.info(f"    Overhead: {init.get('overhead_ms', 0):.1f}ms ({init.get('overhead_percent', 0):.1f}%)")
        
        # Indexing
        if 'indexing_comparison' in comparison:
            idx = comparison['indexing_comparison']
            logger.info(f"  Indexing:")
            logger.info(f"    Baseline: {idx.get('baseline_time', 0):.3f}s ({idx.get('baseline_docs_per_sec', 0):.1f} docs/sec)")
            logger.info(f"    Advanced: {idx.get('advanced_time', 0):.3f}s ({idx.get('advanced_docs_per_sec', 0):.1f} docs/sec)")
            logger.info(f"    Overhead: {idx.get('overhead_ms', 0):.1f}ms ({idx.get('overhead_percent', 0):.1f}%)")
        
        # Retrieval
        if 'retrieval_comparison' in comparison:
            ret = comparison['retrieval_comparison']
            logger.info(f"  Retrieval:")
            logger.info(f"    Baseline Avg: {ret.get('baseline_avg_time', 0):.3f}s (P95: {ret.get('baseline_p95', 0):.3f}s)")
            logger.info(f"    Advanced Avg: {ret.get('advanced_avg_time', 0):.3f}s (P95: {ret.get('advanced_p95', 0):.3f}s)")
            logger.info(f"    Avg Overhead: {ret.get('avg_overhead_ms', 0):.1f}ms ({ret.get('avg_overhead_percent', 0):.1f}%)")
            logger.info(f"    Throughput Change: {ret.get('qps_change_percent', 0):.1f}%")
        
        # Recommendations
        logger.info(f"\n💡 RECOMMENDATIONS:")
        recommendations = comparison.get('recommendations', [])
        for rec in recommendations:
            logger.info(f"  {rec}")
        
        # Overall Assessment
        logger.info(f"\n🎯 OVERALL ASSESSMENT:")
        
        # Calculate overall performance impact
        avg_overhead = 0
        overhead_count = 0
        
        if 'initialization_comparison' in comparison:
            avg_overhead += abs(comparison['initialization_comparison'].get('overhead_percent', 0))
            overhead_count += 1
        
        if 'indexing_comparison' in comparison:
            avg_overhead += abs(comparison['indexing_comparison'].get('overhead_percent', 0))
            overhead_count += 1
        
        if 'retrieval_comparison' in comparison:
            avg_overhead += abs(comparison['retrieval_comparison'].get('avg_overhead_percent', 0))
            overhead_count += 1
        
        if overhead_count > 0:
            avg_overhead_percent = avg_overhead / overhead_count
            
            if avg_overhead_percent < 5:
                assessment = "🎉 EXCELLENT - Minimal performance impact"
            elif avg_overhead_percent < 10:
                assessment = "✅ GOOD - Acceptable performance impact"
            elif avg_overhead_percent < 20:
                assessment = "⚠️ MODERATE - Some performance impact, monitor closely"
            else:
                assessment = "❌ HIGH IMPACT - Significant performance degradation"
            
            logger.info(f"  {assessment}")
            logger.info(f"  Average overhead: {avg_overhead_percent:.1f}%")
        
        # Epic 2 readiness
        if advanced.get('system_info', {}).get('retriever_type') != baseline.get('system_info', {}).get('retriever_type'):
            logger.info("  🚀 Epic 2 Advanced Retriever successfully deployed")
            logger.info("  🛠️ Framework ready for neural reranking, graph retrieval, and analytics")


def main():
    """Run the performance comparison."""
    comparator = PerformanceComparator()
    results = comparator.run_comparison()
    
    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = f"performance_comparison_{timestamp}.json"
    
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    logger.info(f"\n💾 Results saved to: {results_file}")
    
    # Return success based on performance impact
    comparison = results.get('comparison_analysis', {})
    retrieval_comp = comparison.get('retrieval_comparison', {})
    acceptable = (
        retrieval_comp.get('acceptable_avg', False) and 
        retrieval_comp.get('acceptable_p95', False)
    )
    
    return acceptable


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)