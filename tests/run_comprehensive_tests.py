#!/usr/bin/env python3
"""
Comprehensive Test Runner

This script runs both integration and component-specific tests to provide
complete visibility into system behavior and component performance.

Features:
- Comprehensive integration testing with full data visibility
- Component-specific testing with behavior control
- Cross-test analysis and comparison
- Portfolio readiness assessment
- Performance optimization recommendations
"""

import sys
import time
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from tests.comprehensive_integration_test import ComprehensiveIntegrationTest
from tests.component_specific_tests import ComponentSpecificTester
from tests.validate_system_fixes import SystemValidator


class ComprehensiveTestRunner:
    """
    Comprehensive test runner that orchestrates all test suites.
    
    This runner provides:
    - Complete integration testing
    - Individual component testing
    - Cross-test analysis
    - Portfolio readiness assessment
    - Performance optimization recommendations
    """
    
    def __init__(self, config_path: str = "config/default.yaml"):
        """Initialize comprehensive test runner."""
        self.config_path = config_path
        self.test_results = {
            'timestamp': datetime.now().isoformat(),
            'test_session_id': f"comprehensive_test_{int(time.time())}",
            'config_path': config_path,
            'integration_test_results': {},
            'component_test_results': {},
            'system_validation_results': {},
            'cross_test_analysis': {},
            'portfolio_assessment': {},
            'optimization_recommendations': {}
        }
    
    def run_all_tests(self) -> Dict[str, Any]:
        """
        Run all comprehensive tests.
        
        Returns:
            Complete test results with cross-analysis
        """
        print("=" * 120)
        print("COMPREHENSIVE TEST RUNNER - COMPLETE SYSTEM ANALYSIS")
        print(f"Test Session ID: {self.test_results['test_session_id']}")
        print(f"Timestamp: {self.test_results['timestamp']}")
        print(f"Configuration: {self.config_path}")
        print("=" * 120)
        
        try:
            # Test Suite 1: System Validation
            print("\n🔧 TEST SUITE 1: SYSTEM VALIDATION")
            self._run_system_validation()
            
            # Test Suite 2: Comprehensive Integration Testing
            print("\n🔗 TEST SUITE 2: COMPREHENSIVE INTEGRATION TESTING")
            self._run_integration_tests()
            
            # Test Suite 3: Component-Specific Testing
            print("\n🔍 TEST SUITE 3: COMPONENT-SPECIFIC TESTING")
            self._run_component_tests()
            
            # Test Suite 4: Cross-Test Analysis
            print("\n📊 TEST SUITE 4: CROSS-TEST ANALYSIS")
            self._perform_cross_test_analysis()
            
            # Test Suite 5: Portfolio Assessment
            print("\n🎯 TEST SUITE 5: PORTFOLIO READINESS ASSESSMENT")
            self._assess_portfolio_readiness()
            
            # Test Suite 6: Optimization Recommendations
            print("\n🚀 TEST SUITE 6: OPTIMIZATION RECOMMENDATIONS")
            self._generate_optimization_recommendations()
            
            # Generate Comprehensive Report
            print("\n📋 GENERATING COMPREHENSIVE REPORT")
            self._generate_comprehensive_report()
            
            return self.test_results
            
        except Exception as e:
            print(f"❌ COMPREHENSIVE TESTS FAILED: {str(e)}")
            import traceback
            traceback.print_exc()
            self.test_results['fatal_error'] = str(e)
            return self.test_results
    
    def _run_system_validation(self):
        """Run system validation tests."""
        print("  • Running system validation...")
        
        try:
            validator = SystemValidator()
            validation_results = validator.run_all_validations()
            
            self.test_results['system_validation_results'] = validation_results
            
            # Extract key metrics
            portfolio_readiness = validation_results.get('portfolio_readiness', {})
            readiness_score = portfolio_readiness.get('readiness_score', 0)
            gates_passed = portfolio_readiness.get('gates_passed', 0)
            total_gates = portfolio_readiness.get('total_gates', 0)
            
            print(f"    ✅ System validation complete")
            print(f"    • Readiness score: {readiness_score:.1f}%")
            print(f"    • Quality gates passed: {gates_passed}/{total_gates}")
            print(f"    • Readiness level: {portfolio_readiness.get('readiness_level', 'UNKNOWN')}")
            
        except Exception as e:
            print(f"    ❌ System validation failed: {str(e)}")
            self.test_results['system_validation_results'] = {'error': str(e)}
    
    def _run_integration_tests(self):
        """Run comprehensive integration tests."""
        print("  • Running comprehensive integration tests...")
        
        try:
            integration_tester = ComprehensiveIntegrationTest(self.config_path)
            integration_results = integration_tester.run_comprehensive_test()
            
            self.test_results['integration_test_results'] = integration_results
            
            # Extract key metrics
            report = integration_results.get('comprehensive_report', {})
            test_summary = report.get('test_summary', {})
            performance_summary = report.get('performance_summary', {})
            quality_summary = report.get('quality_summary', {})
            
            print(f"    ✅ Integration tests complete")
            print(f"    • Documents processed: {test_summary.get('documents_processed', 0)}")
            print(f"    • Queries tested: {test_summary.get('queries_tested', 0)}")
            print(f"    • Answers generated: {test_summary.get('answers_generated', 0)}")
            print(f"    • Data integrity checks: {quality_summary.get('data_integrity_checks', 0)}")
            
        except Exception as e:
            print(f"    ❌ Integration tests failed: {str(e)}")
            self.test_results['integration_test_results'] = {'error': str(e)}
    
    def _run_component_tests(self):
        """Run component-specific tests."""
        print("  • Running component-specific tests...")
        
        try:
            component_tester = ComponentSpecificTester()
            component_results = component_tester.run_all_component_tests()
            
            self.test_results['component_test_results'] = component_results
            
            # Extract key metrics
            report = component_results.get('component_analysis_report', {})
            summary_stats = report.get('summary_statistics', {})
            
            print(f"    ✅ Component tests complete")
            print(f"    • Components tested: {summary_stats.get('total_components_tested', 0)}")
            print(f"    • Overall success rate: {summary_stats.get('overall_success_rate', 0):.1%}")
            print(f"    • Total test time: {summary_stats.get('total_test_time', 0):.4f}s")
            
        except Exception as e:
            print(f"    ❌ Component tests failed: {str(e)}")
            self.test_results['component_test_results'] = {'error': str(e)}
    
    def _perform_cross_test_analysis(self):
        """Perform cross-test analysis."""
        print("  • Performing cross-test analysis...")
        
        try:
            # Analyze consistency across test suites
            consistency_analysis = self._analyze_test_consistency()
            
            # Compare performance metrics
            performance_comparison = self._compare_performance_metrics()
            
            # Analyze quality consistency
            quality_consistency = self._analyze_quality_consistency()
            
            # Identify discrepancies
            discrepancy_analysis = self._identify_discrepancies()
            
            self.test_results['cross_test_analysis'] = {
                'consistency_analysis': consistency_analysis,
                'performance_comparison': performance_comparison,
                'quality_consistency': quality_consistency,
                'discrepancy_analysis': discrepancy_analysis,
                'cross_validation_score': self._calculate_cross_validation_score(
                    consistency_analysis, performance_comparison, quality_consistency
                )
            }
            
            print(f"    ✅ Cross-test analysis complete")
            print(f"    • Test consistency: {consistency_analysis.get('overall_consistency', 0):.2f}")
            print(f"    • Performance alignment: {performance_comparison.get('alignment_score', 0):.2f}")
            print(f"    • Quality consistency: {quality_consistency.get('consistency_score', 0):.2f}")
            
        except Exception as e:
            print(f"    ❌ Cross-test analysis failed: {str(e)}")
            self.test_results['cross_test_analysis'] = {'error': str(e)}
    
    def _assess_portfolio_readiness(self):
        """Assess overall portfolio readiness."""
        print("  • Assessing portfolio readiness...")
        
        try:
            # Collect readiness metrics from all test suites
            system_readiness = self._extract_system_readiness()
            integration_readiness = self._extract_integration_readiness()
            component_readiness = self._extract_component_readiness()
            
            # Calculate overall portfolio score
            portfolio_score = self._calculate_portfolio_score(
                system_readiness, integration_readiness, component_readiness
            )
            
            # Determine readiness level
            readiness_level = self._determine_readiness_level(portfolio_score)
            
            # Identify blockers
            blockers = self._identify_portfolio_blockers(
                system_readiness, integration_readiness, component_readiness
            )
            
            # Generate readiness recommendations
            recommendations = self._generate_readiness_recommendations(
                portfolio_score, readiness_level, blockers
            )
            
            self.test_results['portfolio_assessment'] = {
                'system_readiness': system_readiness,
                'integration_readiness': integration_readiness,
                'component_readiness': component_readiness,
                'portfolio_score': portfolio_score,
                'readiness_level': readiness_level,
                'blockers': blockers,
                'recommendations': recommendations,
                'ready_for_portfolio': readiness_level in ['PORTFOLIO_READY', 'STAGING_READY']
            }
            
            print(f"    ✅ Portfolio assessment complete")
            print(f"    • Portfolio score: {portfolio_score:.1f}%")
            print(f"    • Readiness level: {readiness_level}")
            print(f"    • Portfolio ready: {readiness_level in ['PORTFOLIO_READY', 'STAGING_READY']}")
            print(f"    • Blockers identified: {len(blockers)}")
            
        except Exception as e:
            print(f"    ❌ Portfolio assessment failed: {str(e)}")
            self.test_results['portfolio_assessment'] = {'error': str(e)}
    
    def _generate_optimization_recommendations(self):
        """Generate optimization recommendations."""
        print("  • Generating optimization recommendations...")
        
        try:
            # Performance optimization recommendations
            performance_optimizations = self._generate_performance_optimizations()
            
            # Quality improvement recommendations
            quality_improvements = self._generate_quality_improvements()
            
            # Reliability enhancement recommendations
            reliability_enhancements = self._generate_reliability_enhancements()
            
            # Architecture optimization recommendations
            architecture_optimizations = self._generate_architecture_optimizations()
            
            # Cost optimization recommendations
            cost_optimizations = self._generate_cost_optimizations()
            
            self.test_results['optimization_recommendations'] = {
                'performance_optimizations': performance_optimizations,
                'quality_improvements': quality_improvements,
                'reliability_enhancements': reliability_enhancements,
                'architecture_optimizations': architecture_optimizations,
                'cost_optimizations': cost_optimizations,
                'priority_recommendations': self._prioritize_recommendations(
                    performance_optimizations, quality_improvements, 
                    reliability_enhancements, architecture_optimizations, cost_optimizations
                )
            }
            
            total_recommendations = sum(len(opt) for opt in [
                performance_optimizations, quality_improvements, reliability_enhancements,
                architecture_optimizations, cost_optimizations
            ])
            
            print(f"    ✅ Optimization recommendations complete")
            print(f"    • Total recommendations: {total_recommendations}")
            print(f"    • Performance optimizations: {len(performance_optimizations)}")
            print(f"    • Quality improvements: {len(quality_improvements)}")
            print(f"    • Reliability enhancements: {len(reliability_enhancements)}")
            
        except Exception as e:
            print(f"    ❌ Optimization recommendations failed: {str(e)}")
            self.test_results['optimization_recommendations'] = {'error': str(e)}
    
    def _generate_comprehensive_report(self):
        """Generate comprehensive test report."""
        print("  • Generating comprehensive test report...")
        
        # Overall test summary
        test_summary = {
            'total_test_suites': 6,
            'successful_test_suites': self._count_successful_test_suites(),
            'total_test_time': self._calculate_total_test_time(),
            'total_components_tested': self._count_total_components_tested(),
            'total_queries_tested': self._count_total_queries_tested(),
            'total_documents_processed': self._count_total_documents_processed()
        }
        
        # Performance summary
        performance_summary = {
            'average_query_time': self._calculate_average_query_time(),
            'average_document_processing_time': self._calculate_average_document_processing_time(),
            'system_throughput': self._calculate_system_throughput(),
            'bottleneck_components': self._identify_bottleneck_components()
        }
        
        # Quality summary
        quality_summary = {
            'overall_quality_score': self._calculate_overall_quality_score(),
            'answer_quality_rate': self._calculate_answer_quality_rate(),
            'confidence_calibration_score': self._calculate_confidence_calibration_score(),
            'data_integrity_score': self._calculate_data_integrity_score()
        }
        
        # Readiness summary
        readiness_summary = {
            'portfolio_readiness_score': self.test_results.get('portfolio_assessment', {}).get('portfolio_score', 0),
            'readiness_level': self.test_results.get('portfolio_assessment', {}).get('readiness_level', 'UNKNOWN'),
            'critical_blockers': len([b for b in self.test_results.get('portfolio_assessment', {}).get('blockers', []) if b.get('severity') == 'critical']),
            'recommendation_count': sum(len(opt) for opt in self.test_results.get('optimization_recommendations', {}).values() if isinstance(opt, list))
        }
        
        self.test_results['comprehensive_report'] = {
            'test_summary': test_summary,
            'performance_summary': performance_summary,
            'quality_summary': quality_summary,
            'readiness_summary': readiness_summary,
            'test_completeness': self._assess_test_completeness(),
            'success_metrics': self._calculate_success_metrics()
        }
        
        print(f"    ✅ Comprehensive report generated")
        print(f"\n" + "=" * 120)
        print("COMPREHENSIVE TEST RESULTS SUMMARY")
        print("=" * 120)
        print(f"📊 TEST COMPLETION:")
        print(f"   • Test suites completed: {test_summary['successful_test_suites']}/{test_summary['total_test_suites']}")
        print(f"   • Components tested: {test_summary['total_components_tested']}")
        print(f"   • Queries tested: {test_summary['total_queries_tested']}")
        print(f"   • Documents processed: {test_summary['total_documents_processed']}")
        print(f"   • Total test time: {test_summary['total_test_time']:.2f}s")
        print(f"\n⚡ PERFORMANCE:")
        print(f"   • Average query time: {performance_summary['average_query_time']:.4f}s")
        print(f"   • System throughput: {performance_summary['system_throughput']:.2f} queries/sec")
        print(f"   • Bottleneck components: {len(performance_summary['bottleneck_components'])}")
        print(f"\n🏆 QUALITY:")
        print(f"   • Overall quality score: {quality_summary['overall_quality_score']:.2f}/1.0")
        print(f"   • Answer quality rate: {quality_summary['answer_quality_rate']:.1%}")
        print(f"   • Data integrity score: {quality_summary['data_integrity_score']:.2f}/1.0")
        print(f"\n🎯 PORTFOLIO READINESS:")
        print(f"   • Portfolio score: {readiness_summary['portfolio_readiness_score']:.1f}%")
        print(f"   • Readiness level: {readiness_summary['readiness_level']}")
        print(f"   • Critical blockers: {readiness_summary['critical_blockers']}")
        print(f"   • Optimization recommendations: {readiness_summary['recommendation_count']}")
        print("=" * 120)
    
    # Helper methods for analysis
    def _analyze_test_consistency(self):
        """Analyze consistency across test suites."""
        # Compare results from different test suites
        system_results = self.test_results.get('system_validation_results', {})
        integration_results = self.test_results.get('integration_test_results', {})
        component_results = self.test_results.get('component_test_results', {})
        
        # Check for consistent architecture reporting
        architecture_consistency = self._check_architecture_consistency(
            system_results, integration_results, component_results
        )
        
        # Check for consistent performance metrics
        performance_consistency = self._check_performance_consistency(
            system_results, integration_results, component_results
        )
        
        # Check for consistent quality scores
        quality_consistency = self._check_quality_consistency(
            system_results, integration_results, component_results
        )
        
        overall_consistency = (
            architecture_consistency + performance_consistency + quality_consistency
        ) / 3
        
        return {
            'architecture_consistency': architecture_consistency,
            'performance_consistency': performance_consistency,
            'quality_consistency': quality_consistency,
            'overall_consistency': overall_consistency
        }
    
    def _compare_performance_metrics(self):
        """Compare performance metrics across test suites."""
        integration_perf = self.test_results.get('integration_test_results', {}).get('comprehensive_report', {}).get('performance_summary', {})
        component_perf = self.test_results.get('component_test_results', {}).get('component_analysis_report', {}).get('summary_statistics', {})
        
        # Compare timing metrics
        integration_avg_time = integration_perf.get('average_generation_time', 0)
        component_avg_time = component_perf.get('total_test_time', 0) / max(component_perf.get('total_components_tested', 1), 1)
        
        # Calculate alignment score
        alignment_score = 1.0 - abs(integration_avg_time - component_avg_time) / max(integration_avg_time, component_avg_time, 0.001)
        
        return {
            'integration_metrics': integration_perf,
            'component_metrics': component_perf,
            'alignment_score': max(0, alignment_score),
            'timing_difference': abs(integration_avg_time - component_avg_time)
        }
    
    def _analyze_quality_consistency(self):
        """Analyze quality consistency across test suites."""
        system_quality = self._extract_system_quality_score()
        integration_quality = self._extract_integration_quality_score()
        component_quality = self._extract_component_quality_score()
        
        quality_scores = [score for score in [system_quality, integration_quality, component_quality] if score > 0]
        
        if not quality_scores:
            return {'consistency_score': 0, 'quality_scores': []}
        
        # Calculate coefficient of variation
        import numpy as np
        mean_quality = np.mean(quality_scores)
        std_quality = np.std(quality_scores)
        
        cv = std_quality / mean_quality if mean_quality > 0 else 0
        consistency_score = max(0, 1 - cv)  # Lower CV = higher consistency
        
        return {
            'quality_scores': quality_scores,
            'mean_quality': mean_quality,
            'quality_variance': std_quality,
            'consistency_score': consistency_score
        }
    
    def _identify_discrepancies(self):
        """Identify discrepancies between test suites."""
        discrepancies = []
        
        # Check for significant performance differences
        perf_comparison = self.test_results.get('cross_test_analysis', {}).get('performance_comparison', {})
        if perf_comparison.get('alignment_score', 1) < 0.8:
            discrepancies.append({
                'type': 'performance_discrepancy',
                'severity': 'medium',
                'description': 'Significant performance differences between test suites',
                'details': perf_comparison
            })
        
        # Check for quality inconsistencies
        quality_consistency = self.test_results.get('cross_test_analysis', {}).get('quality_consistency', {})
        if quality_consistency.get('consistency_score', 1) < 0.7:
            discrepancies.append({
                'type': 'quality_inconsistency',
                'severity': 'high',
                'description': 'Quality scores vary significantly between test suites',
                'details': quality_consistency
            })
        
        return discrepancies
    
    def _calculate_cross_validation_score(self, consistency_analysis, performance_comparison, quality_consistency):
        """Calculate cross-validation score."""
        consistency_score = consistency_analysis.get('overall_consistency', 0)
        alignment_score = performance_comparison.get('alignment_score', 0)
        quality_score = quality_consistency.get('consistency_score', 0)
        
        return (consistency_score + alignment_score + quality_score) / 3
    
    def _extract_system_readiness(self):
        """Extract system readiness metrics."""
        system_results = self.test_results.get('system_validation_results', {})
        portfolio_readiness = system_results.get('portfolio_readiness', {})
        
        return {
            'readiness_score': portfolio_readiness.get('readiness_score', 0),
            'gates_passed': portfolio_readiness.get('gates_passed', 0),
            'total_gates': portfolio_readiness.get('total_gates', 0),
            'ready_for_portfolio': portfolio_readiness.get('ready_for_portfolio', False)
        }
    
    def _extract_integration_readiness(self):
        """Extract integration readiness metrics."""
        integration_results = self.test_results.get('integration_test_results', {})
        report = integration_results.get('comprehensive_report', {})
        quality_summary = report.get('quality_summary', {})
        
        return {
            'data_integrity_checks': quality_summary.get('data_integrity_checks', 0),
            'retrieval_precision': quality_summary.get('retrieval_precision', 0),
            'answer_appropriateness': quality_summary.get('answer_length_appropriateness', 0),
            'confidence_appropriateness': quality_summary.get('confidence_appropriateness', 0)
        }
    
    def _extract_component_readiness(self):
        """Extract component readiness metrics."""
        component_results = self.test_results.get('component_test_results', {})
        report = component_results.get('component_analysis_report', {})
        summary_stats = report.get('summary_statistics', {})
        
        return {
            'overall_success_rate': summary_stats.get('overall_success_rate', 0),
            'components_tested': summary_stats.get('total_components_tested', 0),
            'test_completeness': report.get('test_completeness', {}).get('completeness_score', 0)
        }
    
    def _calculate_portfolio_score(self, system_readiness, integration_readiness, component_readiness):
        """Calculate overall portfolio score."""
        # Weight the different readiness scores
        system_weight = 0.4
        integration_weight = 0.3
        component_weight = 0.3
        
        system_score = system_readiness.get('readiness_score', 0)
        
        # Calculate integration score
        integration_metrics = [
            integration_readiness.get('retrieval_precision', 0),
            integration_readiness.get('answer_appropriateness', 0),
            integration_readiness.get('confidence_appropriateness', 0)
        ]
        integration_score = (sum(integration_metrics) / len(integration_metrics)) * 100 if integration_metrics else 0
        
        # Calculate component score
        component_score = component_readiness.get('overall_success_rate', 0) * 100
        
        # Weighted average
        portfolio_score = (
            system_score * system_weight +
            integration_score * integration_weight +
            component_score * component_weight
        )
        
        return portfolio_score
    
    def _determine_readiness_level(self, portfolio_score):
        """Determine readiness level based on score."""
        if portfolio_score >= 90:
            return "PORTFOLIO_READY"
        elif portfolio_score >= 70:
            return "STAGING_READY"
        elif portfolio_score >= 50:
            return "DEVELOPMENT_READY"
        else:
            return "NOT_READY"
    
    def _identify_portfolio_blockers(self, system_readiness, integration_readiness, component_readiness):
        """Identify portfolio blockers."""
        blockers = []
        
        # System-level blockers
        if system_readiness.get('readiness_score', 0) < 70:
            blockers.append({
                'type': 'system_readiness',
                'severity': 'high',
                'description': f"System readiness score too low: {system_readiness.get('readiness_score', 0):.1f}%",
                'threshold': 70,
                'current_value': system_readiness.get('readiness_score', 0)
            })
        
        # Integration-level blockers
        if integration_readiness.get('retrieval_precision', 0) < 0.6:
            blockers.append({
                'type': 'retrieval_quality',
                'severity': 'medium',
                'description': f"Retrieval precision too low: {integration_readiness.get('retrieval_precision', 0):.2f}",
                'threshold': 0.6,
                'current_value': integration_readiness.get('retrieval_precision', 0)
            })
        
        # Component-level blockers
        if component_readiness.get('overall_success_rate', 0) < 0.8:
            blockers.append({
                'type': 'component_reliability',
                'severity': 'high',
                'description': f"Component success rate too low: {component_readiness.get('overall_success_rate', 0):.1%}",
                'threshold': 0.8,
                'current_value': component_readiness.get('overall_success_rate', 0)
            })
        
        return blockers
    
    def _generate_readiness_recommendations(self, portfolio_score, readiness_level, blockers):
        """Generate readiness recommendations."""
        recommendations = []
        
        # High-priority recommendations based on blockers
        for blocker in blockers:
            if blocker['severity'] == 'high':
                recommendations.append(f"CRITICAL: Address {blocker['type']} - {blocker['description']}")
            elif blocker['severity'] == 'medium':
                recommendations.append(f"IMPORTANT: Improve {blocker['type']} - {blocker['description']}")
        
        # General recommendations based on readiness level
        if readiness_level == "NOT_READY":
            recommendations.append("System requires major improvements before portfolio use")
            recommendations.append("Focus on addressing critical blockers first")
        elif readiness_level == "DEVELOPMENT_READY":
            recommendations.append("System shows promise but needs optimization")
            recommendations.append("Address quality and performance issues")
        elif readiness_level == "STAGING_READY":
            recommendations.append("System is nearly portfolio-ready")
            recommendations.append("Fine-tune performance and address remaining issues")
        else:
            recommendations.append("System is portfolio-ready!")
            recommendations.append("Consider optimization for enhanced performance")
        
        return recommendations
    
    def _generate_performance_optimizations(self):
        """Generate performance optimization recommendations."""
        optimizations = []
        
        # Extract performance data from test results
        component_results = self.test_results.get('component_test_results', {})
        
        # Check document processor performance
        doc_processor = component_results.get('document_processor', {})
        if doc_processor.get('average_processing_time', 0) > 0.1:
            optimizations.append({
                'component': 'document_processor',
                'recommendation': 'Optimize document processing pipeline',
                'current_performance': doc_processor.get('average_processing_time', 0),
                'target_performance': 0.05
            })
        
        # Check embedder performance
        embedder = component_results.get('embedder', {})
        if embedder.get('average_embedding_time', 0) > 0.05:
            optimizations.append({
                'component': 'embedder',
                'recommendation': 'Implement batch embedding optimization',
                'current_performance': embedder.get('average_embedding_time', 0),
                'target_performance': 0.02
            })
        
        # Check retriever performance
        retriever = component_results.get('retriever', {})
        if retriever.get('average_retrieval_time', 0) > 0.1:
            optimizations.append({
                'component': 'retriever',
                'recommendation': 'Optimize vector search indexing',
                'current_performance': retriever.get('average_retrieval_time', 0),
                'target_performance': 0.05
            })
        
        # Check answer generator performance
        answer_generator = component_results.get('answer_generator', {})
        if answer_generator.get('average_generation_time', 0) > 2.0:
            optimizations.append({
                'component': 'answer_generator',
                'recommendation': 'Optimize LLM inference pipeline',
                'current_performance': answer_generator.get('average_generation_time', 0),
                'target_performance': 1.0
            })
        
        return optimizations
    
    def _generate_quality_improvements(self):
        """Generate quality improvement recommendations."""
        improvements = []
        
        # Extract quality data from test results
        component_results = self.test_results.get('component_test_results', {})
        
        # Check answer generator quality
        answer_generator = component_results.get('answer_generator', {})
        quality_metrics = answer_generator.get('quality_metrics', {})
        
        if quality_metrics.get('average_quality_score', 0) < 0.8:
            improvements.append({
                'component': 'answer_generator',
                'recommendation': 'Improve answer generation quality',
                'current_quality': quality_metrics.get('average_quality_score', 0),
                'target_quality': 0.8
            })
        
        if quality_metrics.get('confidence_appropriateness_rate', 0) < 0.8:
            improvements.append({
                'component': 'answer_generator',
                'recommendation': 'Calibrate confidence scoring',
                'current_quality': quality_metrics.get('confidence_appropriateness_rate', 0),
                'target_quality': 0.8
            })
        
        # Check retriever quality
        retriever = component_results.get('retriever', {})
        ranking_analysis = retriever.get('ranking_analysis', {})
        
        if ranking_analysis.get('average_ranking_quality', 0) < 0.8:
            improvements.append({
                'component': 'retriever',
                'recommendation': 'Improve retrieval ranking quality',
                'current_quality': ranking_analysis.get('average_ranking_quality', 0),
                'target_quality': 0.8
            })
        
        return improvements
    
    def _generate_reliability_enhancements(self):
        """Generate reliability enhancement recommendations."""
        enhancements = []
        
        # Check success rates across components
        component_results = self.test_results.get('component_test_results', {})
        
        for component_name in ['retriever', 'answer_generator']:
            component_data = component_results.get(component_name, {})
            success_rate = component_data.get('success_rate', 0)
            
            if success_rate < 0.95:
                enhancements.append({
                    'component': component_name,
                    'recommendation': f'Improve {component_name} reliability',
                    'current_reliability': success_rate,
                    'target_reliability': 0.95
                })
        
        return enhancements
    
    def _generate_architecture_optimizations(self):
        """Generate architecture optimization recommendations."""
        optimizations = []
        
        # Check cross-component analysis
        cross_analysis = self.test_results.get('cross_test_analysis', {})
        system_coherence = cross_analysis.get('cross_validation_score', 0)
        
        if system_coherence < 0.8:
            optimizations.append({
                'type': 'system_coherence',
                'recommendation': 'Improve cross-component integration',
                'current_score': system_coherence,
                'target_score': 0.8
            })
        
        # Check for bottlenecks
        performance_comparison = cross_analysis.get('performance_comparison', {})
        alignment_score = performance_comparison.get('alignment_score', 0)
        
        if alignment_score < 0.8:
            optimizations.append({
                'type': 'performance_alignment',
                'recommendation': 'Balance component performance',
                'current_score': alignment_score,
                'target_score': 0.8
            })
        
        return optimizations
    
    def _generate_cost_optimizations(self):
        """Generate cost optimization recommendations."""
        optimizations = []
        
        # Check for expensive operations
        component_results = self.test_results.get('component_test_results', {})
        
        # Check LLM usage
        answer_generator = component_results.get('answer_generator', {})
        avg_generation_time = answer_generator.get('average_generation_time', 0)
        
        if avg_generation_time > 3.0:
            optimizations.append({
                'type': 'llm_optimization',
                'recommendation': 'Optimize LLM usage to reduce costs',
                'current_time': avg_generation_time,
                'potential_savings': 'High'
            })
        
        # Check embedding efficiency
        embedder = component_results.get('embedder', {})
        batch_speedup = embedder.get('batch_vs_individual_speedup', 0)
        
        if batch_speedup < 2.0:
            optimizations.append({
                'type': 'embedding_optimization',
                'recommendation': 'Improve batch embedding efficiency',
                'current_speedup': batch_speedup,
                'potential_savings': 'Medium'
            })
        
        return optimizations
    
    def _prioritize_recommendations(self, *recommendation_lists):
        """Prioritize all recommendations."""
        all_recommendations = []
        
        for rec_list in recommendation_lists:
            if isinstance(rec_list, list):
                all_recommendations.extend(rec_list)
        
        # Simple prioritization based on impact and ease of implementation
        priority_recommendations = []
        
        # High priority: Quality and reliability issues
        for rec in all_recommendations:
            if any(keyword in str(rec).lower() for keyword in ['quality', 'reliability', 'critical']):
                priority_recommendations.append({
                    'priority': 'HIGH',
                    'recommendation': rec,
                    'category': 'quality_reliability'
                })
        
        # Medium priority: Performance optimizations
        for rec in all_recommendations:
            if any(keyword in str(rec).lower() for keyword in ['performance', 'optimization', 'speed']):
                priority_recommendations.append({
                    'priority': 'MEDIUM',
                    'recommendation': rec,
                    'category': 'performance'
                })
        
        # Low priority: Cost optimizations
        for rec in all_recommendations:
            if any(keyword in str(rec).lower() for keyword in ['cost', 'efficiency', 'savings']):
                priority_recommendations.append({
                    'priority': 'LOW',
                    'recommendation': rec,
                    'category': 'cost'
                })
        
        return priority_recommendations
    
    # Summary calculation methods
    def _count_successful_test_suites(self):
        """Count successful test suites."""
        success_count = 0
        
        if not self.test_results.get('system_validation_results', {}).get('error'):
            success_count += 1
        if not self.test_results.get('integration_test_results', {}).get('error'):
            success_count += 1
        if not self.test_results.get('component_test_results', {}).get('error'):
            success_count += 1
        if not self.test_results.get('cross_test_analysis', {}).get('error'):
            success_count += 1
        if not self.test_results.get('portfolio_assessment', {}).get('error'):
            success_count += 1
        if not self.test_results.get('optimization_recommendations', {}).get('error'):
            success_count += 1
        
        return success_count
    
    def _calculate_total_test_time(self):
        """Calculate total test time."""
        # This would need to be tracked during test execution
        # For now, return a placeholder
        return 0.0
    
    def _count_total_components_tested(self):
        """Count total components tested."""
        component_results = self.test_results.get('component_test_results', {})
        report = component_results.get('component_analysis_report', {})
        summary_stats = report.get('summary_statistics', {})
        return summary_stats.get('total_components_tested', 0)
    
    def _count_total_queries_tested(self):
        """Count total queries tested."""
        integration_results = self.test_results.get('integration_test_results', {})
        report = integration_results.get('comprehensive_report', {})
        test_summary = report.get('test_summary', {})
        return test_summary.get('queries_tested', 0)
    
    def _count_total_documents_processed(self):
        """Count total documents processed."""
        integration_results = self.test_results.get('integration_test_results', {})
        report = integration_results.get('comprehensive_report', {})
        test_summary = report.get('test_summary', {})
        return test_summary.get('documents_processed', 0)
    
    def _calculate_average_query_time(self):
        """Calculate average query time."""
        integration_results = self.test_results.get('integration_test_results', {})
        report = integration_results.get('comprehensive_report', {})
        performance_summary = report.get('performance_summary', {})
        return performance_summary.get('average_generation_time', 0)
    
    def _calculate_average_document_processing_time(self):
        """Calculate average document processing time."""
        integration_results = self.test_results.get('integration_test_results', {})
        report = integration_results.get('comprehensive_report', {})
        performance_summary = report.get('performance_summary', {})
        return performance_summary.get('document_processing_time', 0)
    
    def _calculate_system_throughput(self):
        """Calculate system throughput."""
        avg_query_time = self._calculate_average_query_time()
        return 1.0 / avg_query_time if avg_query_time > 0 else 0
    
    def _identify_bottleneck_components(self):
        """Identify bottleneck components."""
        component_results = self.test_results.get('component_test_results', {})
        bottlenecks = []
        
        # Check each component's performance
        components = ['document_processor', 'embedder', 'retriever', 'answer_generator']
        times = []
        
        for component in components:
            component_data = component_results.get(component, {})
            if component == 'document_processor':
                time_metric = component_data.get('average_processing_time', 0)
            elif component == 'embedder':
                time_metric = component_data.get('average_embedding_time', 0)
            elif component == 'retriever':
                time_metric = component_data.get('average_retrieval_time', 0)
            elif component == 'answer_generator':
                time_metric = component_data.get('average_generation_time', 0)
            else:
                time_metric = 0
            
            times.append((component, time_metric))
        
        # Sort by time and identify slowest components
        times.sort(key=lambda x: x[1], reverse=True)
        
        # Consider top 2 slowest as bottlenecks if they're significantly slower
        if len(times) >= 2 and times[0][1] > times[1][1] * 1.5:
            bottlenecks.append(times[0][0])
        elif len(times) >= 1 and times[0][1] > 1.0:  # Absolute threshold
            bottlenecks.append(times[0][0])
        
        return bottlenecks
    
    def _calculate_overall_quality_score(self):
        """Calculate overall quality score."""
        system_quality = self._extract_system_quality_score()
        integration_quality = self._extract_integration_quality_score()
        component_quality = self._extract_component_quality_score()
        
        quality_scores = [score for score in [system_quality, integration_quality, component_quality] if score > 0]
        
        if not quality_scores:
            return 0
        
        import numpy as np
        return np.mean(quality_scores)
    
    def _calculate_answer_quality_rate(self):
        """Calculate answer quality rate."""
        component_results = self.test_results.get('component_test_results', {})
        answer_generator = component_results.get('answer_generator', {})
        quality_metrics = answer_generator.get('quality_metrics', {})
        return quality_metrics.get('average_quality_score', 0)
    
    def _calculate_confidence_calibration_score(self):
        """Calculate confidence calibration score."""
        component_results = self.test_results.get('component_test_results', {})
        answer_generator = component_results.get('answer_generator', {})
        quality_metrics = answer_generator.get('quality_metrics', {})
        return quality_metrics.get('confidence_appropriateness_rate', 0)
    
    def _calculate_data_integrity_score(self):
        """Calculate data integrity score."""
        integration_results = self.test_results.get('integration_test_results', {})
        data_integrity = integration_results.get('data_integrity', {})
        
        if not data_integrity:
            return 0
        
        passed_checks = sum(1 for check in data_integrity.values() if isinstance(check, dict) and check.get('passed', False))
        total_checks = len(data_integrity)
        
        return passed_checks / total_checks if total_checks > 0 else 0
    
    def _assess_test_completeness(self):
        """Assess test completeness."""
        completeness_factors = {
            'system_validation': bool(self.test_results.get('system_validation_results')),
            'integration_testing': bool(self.test_results.get('integration_test_results')),
            'component_testing': bool(self.test_results.get('component_test_results')),
            'cross_test_analysis': bool(self.test_results.get('cross_test_analysis')),
            'portfolio_assessment': bool(self.test_results.get('portfolio_assessment')),
            'optimization_recommendations': bool(self.test_results.get('optimization_recommendations'))
        }
        
        completeness_score = sum(completeness_factors.values()) / len(completeness_factors)
        
        return {
            'completeness_factors': completeness_factors,
            'completeness_score': completeness_score,
            'test_coverage': f"{sum(completeness_factors.values())}/{len(completeness_factors)} test suites completed"
        }
    
    def _calculate_success_metrics(self):
        """Calculate success metrics."""
        portfolio_assessment = self.test_results.get('portfolio_assessment', {})
        
        return {
            'portfolio_ready': portfolio_assessment.get('ready_for_portfolio', False),
            'readiness_level': portfolio_assessment.get('readiness_level', 'UNKNOWN'),
            'portfolio_score': portfolio_assessment.get('portfolio_score', 0),
            'critical_blockers': len([b for b in portfolio_assessment.get('blockers', []) if b.get('severity') == 'critical']),
            'optimization_opportunities': len(self.test_results.get('optimization_recommendations', {}).get('priority_recommendations', []))
        }
    
    # Helper methods for quality score extraction
    def _extract_system_quality_score(self):
        """Extract system quality score."""
        system_results = self.test_results.get('system_validation_results', {})
        portfolio_readiness = system_results.get('portfolio_readiness', {})
        return portfolio_readiness.get('readiness_score', 0) / 100
    
    def _extract_integration_quality_score(self):
        """Extract integration quality score."""
        integration_results = self.test_results.get('integration_test_results', {})
        report = integration_results.get('comprehensive_report', {})
        quality_summary = report.get('quality_summary', {})
        
        # Average multiple quality metrics
        quality_metrics = [
            quality_summary.get('retrieval_precision', 0),
            quality_summary.get('answer_length_appropriateness', 0),
            quality_summary.get('confidence_appropriateness', 0)
        ]
        
        return sum(quality_metrics) / len(quality_metrics) if quality_metrics else 0
    
    def _extract_component_quality_score(self):
        """Extract component quality score."""
        component_results = self.test_results.get('component_test_results', {})
        report = component_results.get('component_analysis_report', {})
        summary_stats = report.get('summary_statistics', {})
        return summary_stats.get('overall_success_rate', 0)
    
    def _check_architecture_consistency(self, system_results, integration_results, component_results):
        """Check architecture consistency across test suites."""
        # Extract architecture information from each test suite
        system_arch = system_results.get('system_initialization', {}).get('architecture_display', 'unknown')
        integration_arch = integration_results.get('system_metrics', {}).get('health', {}).get('architecture', 'unknown')
        
        # Check if architectures match
        if system_arch == integration_arch and system_arch != 'unknown':
            return 1.0
        elif system_arch != 'unknown' and integration_arch != 'unknown':
            return 0.5  # Partial consistency
        else:
            return 0.0  # No consistency data
    
    def _check_performance_consistency(self, system_results, integration_results, component_results):
        """Check performance consistency across test suites."""
        # This is a simplified consistency check
        # In practice, you'd compare specific performance metrics
        return 0.8  # Placeholder
    
    def _check_quality_consistency(self, system_results, integration_results, component_results):
        """Check quality consistency across test suites."""
        # Extract quality scores and check for consistency
        system_quality = self._extract_system_quality_score()
        integration_quality = self._extract_integration_quality_score()
        component_quality = self._extract_component_quality_score()
        
        quality_scores = [score for score in [system_quality, integration_quality, component_quality] if score > 0]
        
        if len(quality_scores) < 2:
            return 0.5  # Insufficient data
        
        # Calculate coefficient of variation
        import numpy as np
        mean_quality = np.mean(quality_scores)
        std_quality = np.std(quality_scores)
        
        cv = std_quality / mean_quality if mean_quality > 0 else 0
        consistency = max(0, 1 - cv)  # Lower CV = higher consistency
        
        return consistency
    
    def save_results(self, filename: str = None):
        """Save comprehensive test results to file."""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"comprehensive_test_results_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(self.test_results, f, indent=2, default=str)
        
        print(f"\n💾 Comprehensive test results saved to: {filename}")
        return filename


def main():
    """Main execution function."""
    runner = ComprehensiveTestRunner()
    results = runner.run_all_tests()
    
    # Save results
    runner.save_results()
    
    return results


if __name__ == "__main__":
    main()