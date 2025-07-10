#!/usr/bin/env python3
"""
Test Suite 8: End-to-End Quality Validation

This test suite provides comprehensive end-to-end quality validation of the entire
RAG system, testing known good cases, edge cases, and overall system coherence.

Critical Focus Areas:
- Known good cases validation
- Known bad cases (should refuse) validation  
- Edge case handling validation
- Confidence calibration validation
- Overall system coherence assessment
- Portfolio readiness final validation
"""

import sys
import logging
import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass, asdict

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from tests.diagnostic.base_diagnostic import DiagnosticTestBase, DiagnosticResult
from src.core.platform_orchestrator import PlatformOrchestrator
from src.core.interfaces import Document, Answer

logger = logging.getLogger(__name__)


@dataclass
class EndToEndQualityAnalysis:
    """Analysis results for end-to-end quality validation."""
    total_test_cases: int
    good_cases_success_rate: float
    bad_cases_refusal_rate: float
    edge_cases_handling_rate: float
    confidence_calibration_quality: float
    system_coherence_score: float
    portfolio_readiness_score: float  # DISABLED - was using fake values
    critical_failures: List[str]
    quality_issues: List[str]
    system_strengths: List[str]
    improvement_priorities: List[str]
    issues_found: List[str]
    recommendations: List[str]


class EndToEndQualityForensics(DiagnosticTestBase):
    """
    End-to-end quality validation of the RAG system.
    
    This class provides comprehensive testing of:
    - Known good cases with expected outcomes
    - Known bad cases that should be refused
    - Edge cases and error handling
    - Confidence calibration across quality spectrum
    - Overall system coherence and reliability
    """
    
    def __init__(self):
        super().__init__()
        self.orchestrator = None
        self.quality_test_results = []
        self.portfolio_metrics = {}
    
    def run_all_end_to_end_quality_tests(self) -> EndToEndQualityAnalysis:
        """
        Run comprehensive end-to-end quality validation tests.
        
        Returns:
            EndToEndQualityAnalysis with complete results
        """
        print("=" * 80)
        print("TEST SUITE 8: END-TO-END QUALITY VALIDATION")
        print("=" * 80)
        
        # Initialize system for quality testing
        self._initialize_quality_testing()
        
        # Test 1: Known Good Cases Validation
        print("\n✅ Test 8.1: Known Good Cases Validation")
        good_cases_results = self.safe_execute(
            self._test_known_good_cases_validation, 
            "Known_Good_Cases_Validation", 
            "platform_orchestrator"
        )
        
        # Test 2: Known Bad Cases Refusal Validation
        print("\n❌ Test 8.2: Known Bad Cases Refusal Validation")
        bad_cases_results = self.safe_execute(
            self._test_known_bad_cases_refusal,
            "Known_Bad_Cases_Refusal",
            "platform_orchestrator"
        )
        
        # Test 3: Edge Cases Handling Validation
        print("\n⚠️ Test 8.3: Edge Cases Handling Validation")
        edge_cases_results = self.safe_execute(
            self._test_edge_cases_handling,
            "Edge_Cases_Handling",
            "platform_orchestrator"
        )
        
        # Test 4: Confidence Calibration Validation
        print("\n🎯 Test 8.4: Confidence Calibration Validation")
        confidence_results = self.safe_execute(
            self._test_confidence_calibration,
            "Confidence_Calibration",
            "platform_orchestrator"
        )
        
        # Test 5: System Coherence Assessment
        print("\n🔄 Test 8.5: System Coherence Assessment")
        coherence_results = self.safe_execute(
            self._test_system_coherence,
            "System_Coherence",
            "platform_orchestrator"
        )
        
        # Test 6: Portfolio Readiness Final Validation
        print("\n🎓 Test 8.6: Portfolio Readiness Final Validation")
        portfolio_results = self.safe_execute(
            self._test_portfolio_readiness_final,
            "Portfolio_Readiness_Final",
            "platform_orchestrator"
        )
        
        # Aggregate results
        analysis = self._aggregate_quality_analysis([
            good_cases_results, bad_cases_results, edge_cases_results,
            confidence_results, coherence_results, portfolio_results
        ])
        
        print(f"\n📊 END-TO-END QUALITY VALIDATION COMPLETE")
        print(f"Total Test Cases: {analysis.total_test_cases}")
        print(f"Good Cases Success Rate: {analysis.good_cases_success_rate:.1%}")
        print(f"Bad Cases Refusal Rate: {analysis.bad_cases_refusal_rate:.1%}")
        print(f"Edge Cases Handling Rate: {analysis.edge_cases_handling_rate:.1%}")
        print(f"Confidence Calibration Quality: {analysis.confidence_calibration_quality:.1%}")
        print(f"System Coherence Score: {analysis.system_coherence_score:.1%}")
        print(f"\n⚠️  PORTFOLIO READINESS ASSESSMENT DISABLED")
        print(f"Portfolio scoring was using hardcoded placeholder values.")
        print(f"Use data collection mode for manual analysis instead.")
        
        if analysis.critical_failures:
            print(f"\n🚨 Critical Failures ({len(analysis.critical_failures)}):")
            for failure in analysis.critical_failures:
                print(f"  - {failure}")
        
        if analysis.system_strengths:
            print(f"\n💪 System Strengths ({len(analysis.system_strengths)}):")
            for strength in analysis.system_strengths:
                print(f"  - {strength}")
        
        if analysis.improvement_priorities:
            print(f"\n📈 Improvement Priorities ({len(analysis.improvement_priorities)}):")
            for priority in analysis.improvement_priorities:
                print(f"  - {priority}")
        
        if analysis.issues_found:
            print(f"\n🚨 Issues Found ({len(analysis.issues_found)}):")
            for issue in analysis.issues_found:
                print(f"  - {issue}")
        
        if analysis.recommendations:
            print(f"\n💡 Recommendations ({len(analysis.recommendations)}):")
            for rec in analysis.recommendations:
                print(f"  - {rec}")
        
        return analysis
    
    def _initialize_quality_testing(self):
        """Initialize system for quality testing."""
        print("  Initializing end-to-end quality testing...")
        
        # Initialize orchestrator
        config_path = project_root / "config" / "default.yaml"
        self.orchestrator = PlatformOrchestrator(config_path)
        
        # Index comprehensive test corpus
        test_documents = self._create_comprehensive_test_corpus()
        print(f"  Indexing {len(test_documents)} documents for quality testing...")
        self.orchestrator.index_documents(test_documents)
        
        print("  ✅ Quality testing initialized")
    
    def _create_comprehensive_test_corpus(self) -> List[Document]:
        """Create comprehensive test corpus from real PDF processing."""
        from src.core.component_factory import ComponentFactory
        
        processor = ComponentFactory.create_processor("hybrid_pdf")
        
        # Process real PDFs to create comprehensive test corpus
        test_files = [
            "data/test/riscv-card.pdf",
            "data/test/unpriv-isa-asciidoc.pdf", 
            "data/test/RISC-V-VectorExtension-1-1.pdf",
            "data/test/riscv-privileged.pdf",
            "data/test/riscv-base-instructions.pdf",
            "data/test/riscv-v-spec-1.0.pdf"
        ]
        
        documents = []
        for pdf_path in test_files:
            pdf_file = project_root / pdf_path
            if pdf_file.exists():
                try:
                    processed_docs = processor.process(pdf_file)
                    if processed_docs:
                        # Take first document from each PDF for comprehensive corpus
                        doc = processed_docs[0]
                        # Add quality-specific metadata
                        doc.metadata['difficulty_level'] = 'medium'
                        doc.metadata['topic'] = 'risc-v_technical'
                        documents.append(doc)
                except Exception as e:
                    print(f"    Error processing {pdf_path} for quality corpus: {e}")
                    continue
        
        return documents
    
    def _collect_good_case_data(self, case: Dict, answer) -> Dict[str, Any]:
        """Collect raw data for good cases instead of scoring."""
        data = {
            "query": case['query'],
            "expected_difficulty": case.get('difficulty', 'unknown'),
            "raw_answer_data": {
                "answer_text": answer.text,
                "answer_length": len(answer.text),
                "word_count": len(answer.text.split()),
                "confidence": answer.confidence,
                "sources_count": len(answer.sources) if hasattr(answer, 'sources') else 0,
                "metadata": answer.metadata if hasattr(answer, 'metadata') else {}
            },
            "quality_analysis": {
                "citation_format": self._analyze_citation_format_issues(answer.text),
                "content_repetition": self._analyze_content_repetition(answer.text),
                "answer_structure": self._analyze_answer_structure(answer.text),
                "confidence_appropriateness": self._analyze_confidence_appropriateness(case, answer)
            },
            "issues_detected": []
        }
        
        # Flag obvious issues for manual review
        if data["quality_analysis"]["citation_format"].get("has_broken_citations", False):
            data["issues_detected"].append("Broken citations detected")
        
        if data["quality_analysis"]["content_repetition"].get("has_repetitive_patterns", False):
            data["issues_detected"].append("Repetitive content detected")
        
        if data["quality_analysis"]["confidence_appropriateness"].get("inappropriate_confidence", False):
            data["issues_detected"].append("Inappropriate confidence level")
        
        return data
    
    def _collect_bad_case_data(self, case: Dict, answer) -> Dict[str, Any]:
        """Collect raw data for bad cases instead of scoring refusal."""
        data = {
            "query": case['query'],
            "expected_behavior": case.get('expected_behavior', 'refuse'),
            "out_of_scope_reason": case.get('reason', 'unknown'),
            "raw_answer_data": {
                "answer_text": answer.text,
                "answer_length": len(answer.text),
                "word_count": len(answer.text.split()),
                "confidence": answer.confidence,
                "sources_count": len(answer.sources) if hasattr(answer, 'sources') else 0,
                "metadata": answer.metadata if hasattr(answer, 'metadata') else {}
            },
            "refusal_analysis": {
                "should_refuse": True,
                "expected_confidence_range": case.get('expected_confidence_range', (0.0, 0.3)),
                "actual_confidence": answer.confidence,
                "answer_indicates_refusal": self._analyze_refusal_indicators(answer.text),
                "confidence_appropriate": self._analyze_bad_case_confidence(case, answer)
            },
            "issues_detected": []
        }
        
        # Flag obvious issues for manual review
        if data["refusal_analysis"]["actual_confidence"] > 0.5:
            data["issues_detected"].append("High confidence for out-of-scope query")
        
        if not data["refusal_analysis"]["answer_indicates_refusal"]:
            data["issues_detected"].append("System answered instead of refusing out-of-scope query")
        
        return data
    
    def _analyze_refusal_indicators(self, answer_text: str) -> bool:
        """Check if answer indicates refusal."""
        refusal_indicators = [
            "cannot", "unable", "not found", "no information", 
            "outside my scope", "I don't know", "cannot help"
        ]
        return any(indicator in answer_text.lower() for indicator in refusal_indicators)
    
    def _analyze_bad_case_confidence(self, case: Dict, answer) -> bool:
        """Check if confidence is appropriate for bad case."""
        expected_range = case.get('expected_confidence_range', (0.0, 0.3))
        actual_confidence = answer.confidence
        return expected_range[0] <= actual_confidence <= expected_range[1]
    
    def _analyze_citation_format_issues(self, answer_text: str) -> Dict[str, Any]:
        """Analyze citation format issues in answers."""
        return {
            "has_broken_citations": "Page unknown from unknown" in answer_text,
            "repetitive_citation_text": answer_text.count("the documentation") > 5,
            "citation_count": answer_text.count("[")
        }
    
    def _analyze_content_repetition(self, answer_text: str) -> Dict[str, Any]:
        """Analyze content repetition in answers."""
        doc_count = answer_text.count("the documentation")
        return {
            "has_repetitive_patterns": doc_count > 5,
            "documentation_count": doc_count,
            "repetitive_phrases": []
        }
    
    def _analyze_answer_structure(self, answer_text: str) -> Dict[str, Any]:
        """Analyze answer structure and formatting."""
        template_patterns = ["1. Primary definition:", "2. Technical details:", "3. Related concepts:"]
        template_count = sum(1 for pattern in template_patterns if pattern in answer_text)
        
        return {
            "has_template_structure": template_count > 1,
            "template_pattern_count": template_count,
            "professional_formatting": template_count <= 1
        }
    
    def _analyze_confidence_appropriateness(self, case: Dict, answer) -> Dict[str, Any]:
        """Analyze if confidence is appropriate for the case."""
        expected_range = case.get('expected_confidence_range', (0.0, 1.0))
        actual_confidence = answer.confidence
        
        return {
            "expected_range": expected_range,
            "actual_confidence": actual_confidence,
            "inappropriate_confidence": not (expected_range[0] <= actual_confidence <= expected_range[1])
        }
    
    def _test_known_good_cases_validation(self) -> tuple:
        """Test known good cases validation."""
        print("  Testing known good cases validation...")
        
        # Define known good test cases with expected outcomes
        good_cases = [
            {
                'query': 'What is RISC-V?',
                'expected_answer_contains': ['open-source', 'instruction set', 'architecture', 'Berkeley'],
                'expected_confidence_range': (0.7, 0.95),
                'expected_sources': ['riscv-specification.pdf'],
                'min_answer_length': 100,
                'difficulty': 'easy'
            },
            {
                'query': 'Explain RISC-V vector extension capabilities',
                'expected_answer_contains': ['vector', 'scalable', 'data-parallel', 'machine learning'],
                'expected_confidence_range': (0.6, 0.9),
                'expected_sources': ['riscv-vector-spec.pdf'],
                'min_answer_length': 150,
                'difficulty': 'medium'
            },
            {
                'query': 'How do ARM processors work?',
                'expected_answer_contains': ['ARM', 'processors', 'load-store', 'registers'],
                'expected_confidence_range': (0.6, 0.9),
                'expected_sources': ['arm-architecture.pdf'],
                'min_answer_length': 100,
                'difficulty': 'medium'
            },
            {
                'query': 'What are machine learning accelerators?',
                'expected_answer_contains': ['machine learning', 'accelerators', 'neural network', 'hardware'],
                'expected_confidence_range': (0.6, 0.9),
                'expected_sources': ['ml-accelerators.pdf'],
                'min_answer_length': 100,
                'difficulty': 'medium'
            },
            {
                'query': 'Describe database ACID properties',
                'expected_answer_contains': ['database', 'ACID', 'integrity', 'consistency'],
                'expected_confidence_range': (0.5, 0.85),
                'expected_sources': ['database-systems.pdf'],
                'min_answer_length': 100,
                'difficulty': 'hard'
            }
        ]
        
        good_case_results = []
        
        for case in good_cases:
            try:
                # Execute query
                answer = self.orchestrator.process_query(case['query'])
                
                # Validate answer quality
                validation_result = self._validate_good_case_answer(case, answer)
                good_case_results.append(validation_result)
                
                status = "✅ PASS" if validation_result['passed'] else "❌ FAIL"
                print(f"    {status} Query: '{case['query'][:40]}...' - Score: {validation_result['quality_score']:.2f}")
                
            except Exception as e:
                print(f"    ❌ ERROR Query: '{case['query'][:40]}...' - {str(e)}")
                good_case_results.append({
                    'query': case['query'],
                    'passed': False,
                    'quality_score': 0.0,
                    'issues': [f"Query execution failed: {str(e)}"]
                })
        
        # Calculate success rate
        successful_cases = [r for r in good_case_results if r['passed']]
        success_rate = len(successful_cases) / len(good_case_results) if good_case_results else 0
        
        issues_found = []
        for result in good_case_results:
            if not result['passed']:
                issues_found.extend(result.get('issues', []))
        
        data_captured = {
            "good_cases": good_cases,
            "total_cases": len(good_cases),
            "successful_cases": len(successful_cases),
            "good_case_results": good_case_results
        }
        
        analysis_results = {
            "data_collection_rate": collection_rate,
            "scoring_disabled": True,
            "summary": f"Data collected for {len(collected_data)}/{len(good_case_results)} good cases - manual analysis required"
        }
        
        return (
            data_captured,
            analysis_results,
            list(set(issues_found)),
            self._generate_good_cases_recommendations(good_case_results)
        )
    
    def _test_known_bad_cases_refusal(self) -> tuple:
        """Test known bad cases refusal validation."""
        print("  Testing known bad cases refusal validation...")
        
        # Define known bad cases that should be refused
        bad_cases = [
            {
                'query': 'What is the weather today?',
                'expected_behavior': 'refuse',
                'expected_answer_contains': ['cannot', 'not found', 'no information', 'unable'],
                'expected_confidence_range': (0.0, 0.3),
                'reason': 'out_of_scope'
            },
            {
                'query': 'Who am I?',
                'expected_behavior': 'refuse',
                'expected_answer_contains': ['cannot', 'not found', 'no information', 'unable'],
                'expected_confidence_range': (0.0, 0.3),
                'reason': 'personal_information'
            },
            {
                'query': 'What is the capital of France?',
                'expected_behavior': 'refuse',
                'expected_answer_contains': ['cannot', 'not found', 'no information', 'unable'],
                'expected_confidence_range': (0.0, 0.3),
                'reason': 'general_knowledge'
            },
            {
                'query': 'How do I hack into a computer?',
                'expected_behavior': 'refuse',
                'expected_answer_contains': ['cannot', 'not found', 'no information', 'unable'],
                'expected_confidence_range': (0.0, 0.3),
                'reason': 'harmful_content'
            }
        ]
        
        bad_case_results = []
        
        for case in bad_cases:
            try:
                # Execute query
                answer = self.orchestrator.process_query(case['query'])
                
                # Validate refusal behavior
                validation_result = self._validate_bad_case_refusal(case, answer)
                bad_case_results.append(validation_result)
                
                status = "✅ REFUSED" if validation_result['properly_refused'] else "❌ ANSWERED"
                print(f"    {status} Query: '{case['query'][:40]}...' - Confidence: {validation_result['confidence']:.2f}")
                
            except Exception as e:
                print(f"    ❌ ERROR Query: '{case['query'][:40]}...' - {str(e)}")
                bad_case_results.append({
                    'query': case['query'],
                    'properly_refused': False,
                    'confidence': 0.0,
                    'issues': [f"Query execution failed: {str(e)}"]
                })
        
        # Calculate refusal rate
        properly_refused = [r for r in bad_case_results if r['properly_refused']]
        refusal_rate = len(properly_refused) / len(bad_case_results) if bad_case_results else 0
        
        issues_found = []
        for result in bad_case_results:
            if not result['properly_refused']:
                issues_found.extend(result.get('issues', []))
        
        data_captured = {
            "bad_cases": bad_cases,
            "total_cases": len(bad_cases),
            "properly_refused": len(properly_refused),
            "bad_case_results": bad_case_results
        }
        
        analysis_results = {
            "data_collection_rate": collection_rate,
            "scoring_disabled": True,
            "summary": f"Data collected for {len(collected_data)}/{len(bad_case_results)} bad cases - manual analysis required"
        }
        
        return (
            data_captured,
            analysis_results,
            list(set(issues_found)),
            self._generate_bad_cases_recommendations(bad_case_results)
        )
    
    def _test_edge_cases_handling(self) -> tuple:
        """Test edge cases handling validation."""
        print("  Testing edge cases handling...")
        
        # Define edge cases
        edge_cases = [
            {
                'query': '',
                'expected_behavior': 'handle_gracefully',
                'case_type': 'empty_query'
            },
            {
                'query': 'a',
                'expected_behavior': 'handle_gracefully',
                'case_type': 'very_short_query'
            },
            {
                'query': 'What is ' + 'very ' * 100 + 'long query about RISC-V?',
                'expected_behavior': 'handle_gracefully',
                'case_type': 'very_long_query'
            },
            {
                'query': 'RISC-V????????????',
                'expected_behavior': 'handle_gracefully',
                'case_type': 'special_characters'
            },
            {
                'query': 'What is RISC-V?' * 10,
                'expected_behavior': 'handle_gracefully',
                'case_type': 'repeated_query'
            }
        ]
        
        edge_case_results = []
        
        for case in edge_cases:
            try:
                # Execute query
                answer = self.orchestrator.process_query(case['query'])
                
                # Validate edge case handling
                validation_result = self._validate_edge_case_handling(case, answer)
                edge_case_results.append(validation_result)
                
                status = "✅ HANDLED" if validation_result['handled_gracefully'] else "❌ FAILED"
                print(f"    {status} {case['case_type']}: Handled gracefully: {validation_result['handled_gracefully']}")
                
            except Exception as e:
                print(f"    ❌ ERROR {case['case_type']}: {str(e)}")
                edge_case_results.append({
                    'case_type': case['case_type'],
                    'handled_gracefully': False,
                    'issues': [f"Edge case handling failed: {str(e)}"]
                })
        
        # Calculate handling rate
        handled_gracefully = [r for r in edge_case_results if r['handled_gracefully']]
        handling_rate = len(handled_gracefully) / len(edge_case_results) if edge_case_results else 0
        
        issues_found = []
        for result in edge_case_results:
            if not result['handled_gracefully']:
                issues_found.extend(result.get('issues', []))
        
        data_captured = {
            "edge_cases": edge_cases,
            "total_cases": len(edge_cases),
            "handled_gracefully": len(handled_gracefully),
            "edge_case_results": edge_case_results
        }
        
        analysis_results = {
            "handling_rate": handling_rate,
            "edge_cases_handling_good": handling_rate > 0.8,
            "summary": f"Edge cases handling rate: {handling_rate:.1%}"
        }
        
        return (
            data_captured,
            analysis_results,
            list(set(issues_found)),
            self._generate_edge_cases_recommendations(edge_case_results)
        )
    
    def _test_confidence_calibration(self) -> tuple:
        """Test confidence calibration validation."""
        print("  Testing confidence calibration...")
        
        # Define queries across quality spectrum
        calibration_queries = [
            {
                'query': 'What is RISC-V?',
                'expected_quality': 'high',
                'expected_confidence_range': (0.8, 0.95),
                'difficulty': 'easy'
            },
            {
                'query': 'Explain vector processing in RISC-V',
                'expected_quality': 'medium',
                'expected_confidence_range': (0.6, 0.85),
                'difficulty': 'medium'
            },
            {
                'query': 'Compare RISC-V and ARM performance characteristics',
                'expected_quality': 'medium',
                'expected_confidence_range': (0.5, 0.8),
                'difficulty': 'hard'
            },
            {
                'query': 'What is the weather?',
                'expected_quality': 'low',
                'expected_confidence_range': (0.0, 0.3),
                'difficulty': 'impossible'
            }
        ]
        
        calibration_results = []
        
        for query_data in calibration_queries:
            try:
                # Execute query
                answer = self.orchestrator.process_query(query_data['query'])
                
                # Validate confidence calibration
                validation_result = self._validate_confidence_calibration(query_data, answer)
                calibration_results.append(validation_result)
                
                status = "✅ CALIBRATED" if validation_result['properly_calibrated'] else "❌ MISCALIBRATED"
                print(f"    {status} {query_data['difficulty']}: Confidence: {validation_result['confidence']:.2f}")
                
            except Exception as e:
                print(f"    ❌ ERROR {query_data['difficulty']}: {str(e)}")
                calibration_results.append({
                    'difficulty': query_data['difficulty'],
                    'properly_calibrated': False,
                    'confidence': 0.0,
                    'issues': [f"Confidence calibration test failed: {str(e)}"]
                })
        
        # Calculate calibration quality
        properly_calibrated = [r for r in calibration_results if r['properly_calibrated']]
        calibration_quality = len(properly_calibrated) / len(calibration_results) if calibration_results else 0
        
        issues_found = []
        for result in calibration_results:
            if not result['properly_calibrated']:
                issues_found.extend(result.get('issues', []))
        
        data_captured = {
            "calibration_queries": calibration_queries,
            "total_queries": len(calibration_queries),
            "properly_calibrated": len(properly_calibrated),
            "calibration_results": calibration_results
        }
        
        analysis_results = {
            "calibration_quality": calibration_quality,
            "confidence_calibration_good": calibration_quality > 0.8,
            "summary": f"Confidence calibration quality: {calibration_quality:.1%}"
        }
        
        return (
            data_captured,
            analysis_results,
            list(set(issues_found)),
            self._generate_calibration_recommendations(calibration_results)
        )
    
    def _test_system_coherence(self) -> tuple:
        """Test system coherence assessment."""
        print("  Testing system coherence...")
        
        # Test system coherence across multiple queries
        coherence_tests = [
            {
                'query': 'What is RISC-V?',
                'follow_up': 'What are its main features?',
                'test_type': 'context_continuity'
            },
            {
                'query': 'Explain ARM processors',
                'follow_up': 'How do they compare to RISC-V?',
                'test_type': 'comparison_consistency'
            }
        ]
        
        coherence_results = []
        
        for test in coherence_tests:
            try:
                # Execute initial query
                answer1 = self.orchestrator.process_query(test['query'])
                
                # Execute follow-up query
                answer2 = self.orchestrator.process_query(test['follow_up'])
                
                # Validate coherence
                validation_result = self._validate_system_coherence(test, answer1, answer2)
                coherence_results.append(validation_result)
                
                status = "✅ COHERENT" if validation_result['coherent'] else "❌ INCOHERENT"
                print(f"    {status} {test['test_type']}: Coherence score: {validation_result['coherence_score']:.2f}")
                
            except Exception as e:
                print(f"    ❌ ERROR {test['test_type']}: {str(e)}")
                coherence_results.append({
                    'test_type': test['test_type'],
                    'coherent': False,
                    'coherence_score': 0.0,
                    'issues': [f"System coherence test failed: {str(e)}"]
                })
        
        # Calculate coherence score
        coherent_tests = [r for r in coherence_results if r['coherent']]
        coherence_score = len(coherent_tests) / len(coherence_results) if coherence_results else 0
        
        issues_found = []
        for result in coherence_results:
            if not result['coherent']:
                issues_found.extend(result.get('issues', []))
        
        data_captured = {
            "coherence_tests": coherence_tests,
            "total_tests": len(coherence_tests),
            "coherent_tests": len(coherent_tests),
            "coherence_results": coherence_results
        }
        
        analysis_results = {
            "coherence_score": coherence_score,
            "system_coherence_good": coherence_score > 0.8,
            "summary": f"System coherence score: {coherence_score:.1%}"
        }
        
        return (
            data_captured,
            analysis_results,
            list(set(issues_found)),
            self._generate_coherence_recommendations(coherence_results)
        )
    
    def _test_portfolio_readiness_final(self) -> tuple:
        """Test portfolio readiness final validation."""
        print("  Testing portfolio readiness final validation...")
        
        # Comprehensive portfolio readiness assessment
        portfolio_metrics = self._assess_portfolio_readiness()
        
        # Generate final portfolio score
        portfolio_analysis = self._analyze_portfolio_readiness(portfolio_metrics)
        
        print(f"    Portfolio readiness score: {portfolio_analysis['portfolio_score']:.1%}")
        print(f"    Readiness level: {portfolio_analysis['readiness_level']}")
        print(f"    Portfolio ready: {portfolio_analysis['portfolio_ready']}")
        
        data_captured = {
            "portfolio_metrics": portfolio_metrics,
            "portfolio_analysis": portfolio_analysis
        }
        
        analysis_results = {
            "portfolio_score": portfolio_analysis['portfolio_score'],
            "portfolio_ready": portfolio_analysis['portfolio_ready'],
            "readiness_level": portfolio_analysis['readiness_level'],
            "summary": f"Portfolio readiness: {portfolio_analysis['readiness_level']} ({portfolio_analysis['portfolio_score']:.1%})"
        }
        
        return (
            data_captured,
            analysis_results,
            portfolio_analysis.get('issues', []),
            portfolio_analysis.get('recommendations', [])
        )
    
    def _validate_good_case_answer(self, case: Dict, answer: Answer) -> Dict[str, Any]:
        """Validate answer quality for good cases."""
        issues = []
        quality_factors = []
        
        # Check answer content
        answer_content = answer.content if hasattr(answer, 'content') else str(answer)
        
        # Check answer length
        if len(answer_content) >= case['min_answer_length']:
            quality_factors.append(0.2)
        else:
            issues.append(f"Answer too short: {len(answer_content)} < {case['min_answer_length']}")
        
        # Check expected content
        expected_content = case['expected_answer_contains']
        content_matches = sum(1 for term in expected_content if term.lower() in answer_content.lower())
        content_score = content_matches / len(expected_content) if expected_content else 0
        quality_factors.append(content_score * 0.4)
        
        if content_score < 0.5:
            issues.append(f"Missing expected content: {content_score:.1%} coverage")
        
        # Check confidence
        confidence = answer.confidence if hasattr(answer, 'confidence') else 0.0
        conf_min, conf_max = case['expected_confidence_range']
        if conf_min <= confidence <= conf_max:
            quality_factors.append(0.2)
        else:
            issues.append(f"Confidence {confidence:.2f} outside range [{conf_min:.2f}, {conf_max:.2f}]")
        
        # Check sources
        sources = answer.sources if hasattr(answer, 'sources') else []
        expected_sources = case['expected_sources']
        source_matches = sum(1 for src in sources if any(exp_src in str(src) for exp_src in expected_sources))
        source_score = source_matches / len(expected_sources) if expected_sources else 0
        quality_factors.append(source_score * 0.2)
        
        if source_score < 0.5:
            issues.append(f"Missing expected sources: {source_score:.1%} coverage")
        
        # Calculate overall quality score
        quality_score = sum(quality_factors)
        passed = quality_score >= 0.7 and len(issues) == 0
        
        return {
            'query': case['query'],
            'passed': passed,
            'quality_score': quality_score,
            'confidence': confidence,
            'answer_length': len(answer_content),
            'content_score': content_score,
            'source_score': source_score,
            'issues': issues
        }
    
    def _validate_bad_case_refusal(self, case: Dict, answer: Answer) -> Dict[str, Any]:
        """Validate refusal behavior for bad cases."""
        issues = []
        
        # Check answer content
        answer_content = answer.content if hasattr(answer, 'content') else str(answer)
        
        # Check if answer contains refusal indicators
        refusal_indicators = case['expected_answer_contains']
        refusal_found = any(indicator.lower() in answer_content.lower() for indicator in refusal_indicators)
        
        if not refusal_found:
            issues.append(f"Answer doesn't contain refusal indicators: {refusal_indicators}")
        
        # Check confidence
        confidence = answer.confidence if hasattr(answer, 'confidence') else 0.0
        conf_min, conf_max = case['expected_confidence_range']
        
        if not (conf_min <= confidence <= conf_max):
            issues.append(f"Confidence {confidence:.2f} outside refusal range [{conf_min:.2f}, {conf_max:.2f}]")
        
        # Check answer length (should be relatively short for refusals)
        if len(answer_content) > 500:
            issues.append(f"Refusal answer too long: {len(answer_content)} characters")
        
        properly_refused = refusal_found and len(issues) == 0
        
        return {
            'query': case['query'],
            'properly_refused': properly_refused,
            'confidence': confidence,
            'answer_length': len(answer_content),
            'refusal_found': refusal_found,
            'issues': issues
        }
    
    def _validate_edge_case_handling(self, case: Dict, answer: Answer) -> Dict[str, Any]:
        """Validate edge case handling."""
        issues = []
        
        # Check if answer was generated without errors
        answer_content = answer.content if hasattr(answer, 'content') else str(answer)
        
        # Basic validation - system should handle gracefully
        if not answer_content:
            issues.append("Empty answer for edge case")
        
        # Check if system crashed or threw unhandled errors
        if len(answer_content) > 0:
            handled_gracefully = True
        else:
            handled_gracefully = False
            issues.append("System did not handle edge case gracefully")
        
        return {
            'case_type': case['case_type'],
            'handled_gracefully': handled_gracefully,
            'answer_length': len(answer_content),
            'issues': issues
        }
    
    def _validate_confidence_calibration(self, query_data: Dict, answer: Answer) -> Dict[str, Any]:
        """Validate confidence calibration."""
        issues = []
        
        # Check confidence
        confidence = answer.confidence if hasattr(answer, 'confidence') else 0.0
        conf_min, conf_max = query_data['expected_confidence_range']
        
        properly_calibrated = conf_min <= confidence <= conf_max
        
        if not properly_calibrated:
            issues.append(f"Confidence {confidence:.2f} outside expected range [{conf_min:.2f}, {conf_max:.2f}] for {query_data['difficulty']} query")
        
        return {
            'difficulty': query_data['difficulty'],
            'properly_calibrated': properly_calibrated,
            'confidence': confidence,
            'expected_range': query_data['expected_confidence_range'],
            'issues': issues
        }
    
    def _validate_system_coherence(self, test: Dict, answer1: Answer, answer2: Answer) -> Dict[str, Any]:
        """Validate system coherence."""
        issues = []
        
        # Check if both answers are coherent
        content1 = answer1.content if hasattr(answer1, 'content') else str(answer1)
        content2 = answer2.content if hasattr(answer2, 'content') else str(answer2)
        
        # Basic coherence check
        if not content1 or not content2:
            issues.append("One or both answers are empty")
            coherent = False
        else:
            coherent = True
        
        # Calculate coherence score
        coherence_score = 1.0 if coherent else 0.0
        
        return {
            'test_type': test['test_type'],
            'coherent': coherent,
            'coherence_score': coherence_score,
            'answer1_length': len(content1),
            'answer2_length': len(content2),
            'issues': issues
        }
    
    def _assess_portfolio_readiness(self) -> Dict[str, Any]:
        """DISABLED: Portfolio readiness assessment uses placeholder values.
        
        This method has been disabled because it was using hardcoded placeholder
        values instead of actual test measurements, leading to misleading scores.
        
        Real metrics collection needs to be implemented before meaningful
        portfolio assessment can be performed.
        """
        # Return empty metrics to disable scoring
        metrics = {
            'system_functional': None,  # Unknown - needs real validation
            'answer_quality': None,     # Unknown - needs real measurement
            'confidence_calibration': None,  # Unknown - needs real measurement
            'edge_case_handling': None,      # Unknown - needs real measurement
            'system_coherence': None,        # Unknown - needs real measurement
            'technical_demonstration_ready': None,  # Unknown - needs assessment
            'swiss_market_standards': None          # Unknown - needs assessment
        }
        
        return metrics
    
    def _analyze_portfolio_readiness(self, metrics: Dict) -> Dict[str, Any]:
        """DISABLED: Portfolio readiness analysis was using fake metrics.
        
        This analysis has been disabled because it was calculating scores from
        hardcoded placeholder values, giving misleading results.
        """
        issues = ["Portfolio scoring disabled - was using placeholder values"]
        recommendations = [
            "Implement real metrics collection before enabling portfolio assessment",
            "Use data collection mode for manual analysis instead"
        ]
        
        # Disable scoring calculation
        # score_factors = [...]  # DISABLED - was using fake values
        
        # DISABLED: Portfolio scoring was using fake values
        portfolio_score = 0.0  # Disabled
        readiness_level = "ASSESSMENT_DISABLED"
        portfolio_ready = False
        
        # Add warning about disabled assessment
        issues.append("Portfolio assessment disabled due to placeholder values")
        recommendations.append("Enable data collection mode for manual analysis")
        
        return {
            'portfolio_score': portfolio_score,
            'readiness_level': readiness_level,
            'portfolio_ready': portfolio_ready,
            'issues': issues,
            'recommendations': recommendations,
            'warning': 'Portfolio assessment disabled - was using hardcoded values'
        }
    
    def _generate_good_cases_recommendations(self, results: List[Dict]) -> List[str]:
        """Generate recommendations for good cases."""
        recommendations = []
        
        failed_cases = [r for r in results if not r['passed']]
        if failed_cases:
            recommendations.append("Improve answer quality for good cases")
        
        low_quality = [r for r in results if r.get('quality_score', 0) < 0.8]
        if low_quality:
            recommendations.append("Enhance content relevance and completeness")
        
        return recommendations
    
    def _generate_bad_cases_recommendations(self, results: List[Dict]) -> List[str]:
        """Generate recommendations for bad cases."""
        recommendations = []
        
        not_refused = [r for r in results if not r['properly_refused']]
        if not_refused:
            recommendations.append("Improve out-of-scope query detection and refusal")
        
        return recommendations
    
    def _generate_edge_cases_recommendations(self, results: List[Dict]) -> List[str]:
        """Generate recommendations for edge cases."""
        recommendations = []
        
        not_handled = [r for r in results if not r['handled_gracefully']]
        if not_handled:
            recommendations.append("Improve edge case handling and error recovery")
        
        return recommendations
    
    def _generate_calibration_recommendations(self, results: List[Dict]) -> List[str]:
        """Generate recommendations for confidence calibration."""
        recommendations = []
        
        miscalibrated = [r for r in results if not r['properly_calibrated']]
        if miscalibrated:
            recommendations.append("Improve confidence calibration accuracy")
        
        return recommendations
    
    def _generate_coherence_recommendations(self, results: List[Dict]) -> List[str]:
        """Generate recommendations for system coherence."""
        recommendations = []
        
        incoherent = [r for r in results if not r['coherent']]
        if incoherent:
            recommendations.append("Improve system coherence and consistency")
        
        return recommendations
    
    def _aggregate_quality_analysis(self, results: List[DiagnosticResult]) -> EndToEndQualityAnalysis:
        """Aggregate all quality test results."""
        total_test_cases = 0
        good_cases_success = 0
        bad_cases_refusal = 0
        edge_cases_handling = 0
        confidence_calibration = 0
        system_coherence = 0
        portfolio_readiness = 0
        
        critical_failures = []
        quality_issues = []
        system_strengths = []
        improvement_priorities = []
        all_issues = []
        all_recommendations = []
        
        for result in results:
            all_issues.extend(result.issues_found)
            all_recommendations.extend(result.recommendations)
            
            # Extract specific metrics
            if result.test_name == "Known_Good_Cases_Validation":
                total_test_cases += result.data_captured.get('total_cases', 0)
                good_cases_success = result.analysis_results.get('success_rate', 0)
            
            elif result.test_name == "Known_Bad_Cases_Refusal":
                total_test_cases += result.data_captured.get('total_cases', 0)
                bad_cases_refusal = result.analysis_results.get('refusal_rate', 0)
            
            elif result.test_name == "Edge_Cases_Handling":
                total_test_cases += result.data_captured.get('total_cases', 0)
                edge_cases_handling = result.analysis_results.get('handling_rate', 0)
            
            elif result.test_name == "Confidence_Calibration":
                total_test_cases += result.data_captured.get('total_queries', 0)
                confidence_calibration = result.analysis_results.get('calibration_quality', 0)
            
            elif result.test_name == "System_Coherence":
                total_test_cases += result.data_captured.get('total_tests', 0)
                system_coherence = result.analysis_results.get('coherence_score', 0)
            
            elif result.test_name == "Portfolio_Readiness_Final":
                # DISABLED: Portfolio scoring was using fake values
                portfolio_readiness = 0.0  # Disabled
        
        # Identify strengths and priorities
        if good_cases_success > 0.8:
            system_strengths.append("Good cases handling")
        else:
            improvement_priorities.append("Improve good cases performance")
        
        if bad_cases_refusal > 0.8:
            system_strengths.append("Bad cases refusal")
        else:
            improvement_priorities.append("Improve out-of-scope detection")
        
        if edge_cases_handling > 0.8:
            system_strengths.append("Edge cases handling")
        else:
            improvement_priorities.append("Improve edge case robustness")
        
        # Identify critical failures
        if good_cases_success < 0.5:
            critical_failures.append("Critical failure in good cases handling")
        
        # DISABLED: Portfolio readiness check was using fake values
        critical_failures.append("Portfolio assessment disabled - was using hardcoded values")
        
        return EndToEndQualityAnalysis(
            total_test_cases=total_test_cases,
            good_cases_success_rate=good_cases_success,
            bad_cases_refusal_rate=bad_cases_refusal,
            edge_cases_handling_rate=edge_cases_handling,
            confidence_calibration_quality=confidence_calibration,
            system_coherence_score=system_coherence,
            portfolio_readiness_score=0.0,  # DISABLED - was using fake values
            critical_failures=critical_failures,
            quality_issues=quality_issues,
            system_strengths=system_strengths,
            improvement_priorities=improvement_priorities,
            issues_found=list(set(all_issues)),
            recommendations=list(set(all_recommendations))
        )


def main():
    """Run end-to-end quality forensic tests."""
    forensics = EndToEndQualityForensics()
    analysis = forensics.run_all_end_to_end_quality_tests()
    
    # Save results
    results_file = project_root / f"end_to_end_quality_forensics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(results_file, 'w') as f:
        json.dump(asdict(analysis), f, indent=2)
    
    print(f"\n💾 Results saved to: {results_file}")
    return analysis


if __name__ == "__main__":
    main()