#!/usr/bin/env python3
"""
RAG Faithfulness Analysis Suite

A comprehensive testing framework for assessing RAG system faithfulness,
to be used for future prompt engineering and system optimization.

This suite provides:
1. Standardized tests for context following vs pre-trained knowledge
2. Metrics for faithfulness assessment
3. Automated test case generation
4. Results tracking over time
"""

import sys
from pathlib import Path
import time
import json
from datetime import datetime
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass, asdict

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.rag_with_generation import RAGWithGeneration


@dataclass
class FaithfulnessTestCase:
    """Represents a single faithfulness test case."""
    test_id: str
    test_type: str  # "no_context", "fabricated", "specific", "contradictory"
    query: str
    context_chunks: List[Dict[str, Any]]
    expected_behavior: str
    ground_truth: str = ""


@dataclass
class FaithfulnessResult:
    """Results from a faithfulness test."""
    test_case: FaithfulnessTestCase
    answer: str
    citations: int
    confidence: float
    generation_time: float
    faithfulness_score: float  # 0-1, how well it followed expected behavior
    issues_detected: List[str]
    timestamp: str


class RAGFaithfulnessAnalyzer:
    """
    Comprehensive analyzer for RAG system faithfulness.
    
    Provides standardized tests and metrics for assessing whether
    the RAG system properly uses context vs pre-trained knowledge.
    """
    
    def __init__(self, rag_system: RAGWithGeneration = None):
        """Initialize the analyzer."""
        self.rag_system = rag_system or RAGWithGeneration()
        self.test_cases = self._generate_standard_test_cases()
        self.results_history = []
        
    def _generate_standard_test_cases(self) -> List[FaithfulnessTestCase]:
        """Generate standardized test cases for faithfulness evaluation."""
        
        test_cases = []
        
        # 1. No Context Tests
        no_context_queries = [
            "What is RISC-V?",
            "How many registers does RV32E have?", 
            "What are RISC-V instruction formats?",
            "Who developed RISC-V?",
            "What is the difference between RV32I and RV64I?"
        ]
        
        for i, query in enumerate(no_context_queries):
            test_cases.append(FaithfulnessTestCase(
                test_id=f"no_context_{i+1}",
                test_type="no_context",
                query=query,
                context_chunks=[],
                expected_behavior="Should acknowledge lack of context and refuse detailed answer",
                ground_truth="Should say 'I don't have enough context to answer this question'"
            ))
        
        # 2. Fabricated Context Tests
        fabricated_cases = [
            {
                "query": "What is RISC-V?",
                "fake_context": "RISC-V is a quantum computing architecture developed by SpaceX in 2025 using 256 quantum registers.",
                "false_elements": ["quantum", "SpaceX", "2025", "256 quantum registers"]
            },
            {
                "query": "How many registers does RV32E have?",
                "fake_context": "The RV32E variant has exactly 128 general-purpose registers, making it ideal for AI workloads.",
                "false_elements": ["128 registers", "ideal for AI workloads"]
            }
        ]
        
        for i, case in enumerate(fabricated_cases):
            test_cases.append(FaithfulnessTestCase(
                test_id=f"fabricated_{i+1}",
                test_type="fabricated",
                query=case["query"],
                context_chunks=[{
                    "id": "fake_chunk_1",
                    "content": case["fake_context"],
                    "metadata": {"page_number": 1, "source": "fabricated.pdf"},
                    "score": 0.95
                }],
                expected_behavior="Should be cautious about obviously false information",
                ground_truth=f"Should avoid or question: {', '.join(case['false_elements'])}"
            ))
        
        # 3. Specific Context Tests (very detailed, unlikely to be in training)
        specific_cases = [
            {
                "query": "What is the instruction parcel encoding in RISC-V version 2.3?",
                "context": "RISC-V v2.3 uses instruction parcels where bits [1:0] determine length: 00/01/10 = 16-bit, 11 = 32-bit+. Each parcel is 16-bit aligned.",
                "key_terms": ["instruction parcels", "bits [1:0]", "16-bit aligned", "00/01/10"]
            },
            {
                "query": "How does RISC-V handle memory model ordering constraints?",
                "context": "RISC-V implements RVWMO (RISC-V Weak Memory Ordering) with fence.tso for TSO compatibility and fence.i for instruction-fetch ordering.",
                "key_terms": ["RVWMO", "fence.tso", "fence.i", "TSO compatibility"]
            }
        ]
        
        for i, case in enumerate(specific_cases):
            test_cases.append(FaithfulnessTestCase(
                test_id=f"specific_{i+1}",
                test_type="specific",
                query=case["query"],
                context_chunks=[{
                    "id": "specific_chunk_1",
                    "content": case["context"],
                    "metadata": {"page_number": 15, "source": "riscv-spec-v2.3.pdf"},
                    "score": 0.92
                }],
                expected_behavior=f"Should use specific terms: {', '.join(case['key_terms'])}",
                ground_truth=case["context"]
            ))
        
        # 4. Contradictory Context Tests
        contradictory_cases = [
            {
                "query": "Who developed RISC-V?",
                "false_context": "RISC-V was developed by Microsoft in 1995 as a proprietary ISA for Windows NT.",
                "contradiction": "Microsoft vs UC Berkeley, 1995 vs 2010s, proprietary vs open-source"
            },
            {
                "query": "Is RISC-V open source?",
                "false_context": "RISC-V is a completely proprietary architecture owned by Intel, requiring expensive licenses.",
                "contradiction": "proprietary vs open-source, Intel vs RISC-V Foundation"
            }
        ]
        
        for i, case in enumerate(contradictory_cases):
            test_cases.append(FaithfulnessTestCase(
                test_id=f"contradictory_{i+1}",
                test_type="contradictory",
                query=case["query"],
                context_chunks=[{
                    "id": "contradictory_chunk_1",
                    "content": case["false_context"],
                    "metadata": {"page_number": 1, "source": "wrong-info.pdf"},
                    "score": 0.90
                }],
                expected_behavior="Should question or reject contradictory information",
                ground_truth=f"Should recognize contradiction: {case['contradiction']}"
            ))
        
        return test_cases
    
    def _evaluate_faithfulness(self, test_case: FaithfulnessTestCase, answer: str, citations: int, confidence: float) -> Tuple[float, List[str]]:
        """
        Evaluate how well the response follows expected faithful behavior.
        
        Returns:
            Tuple of (faithfulness_score, issues_detected)
        """
        score = 0.0
        issues = []
        
        answer_lower = answer.lower()
        
        if test_case.test_type == "no_context":
            # Should acknowledge lack of context
            context_acknowledgments = [
                "i don't have", "no context", "not enough information", 
                "cannot answer", "insufficient information", "no relevant"
            ]
            if any(phrase in answer_lower for phrase in context_acknowledgments):
                score += 0.8
            else:
                issues.append("Answered without context when should have refused")
            
            # Should not be overconfident
            if confidence < 0.3:
                score += 0.2
            else:
                issues.append(f"Too confident ({confidence:.1%}) without context")
                
        elif test_case.test_type == "fabricated":
            # Extract false elements from ground truth
            false_elements = test_case.ground_truth.split(": ")[1].split(", ")
            
            # Should avoid fabricated information
            fabricated_used = [elem for elem in false_elements if elem.lower() in answer_lower]
            if not fabricated_used:
                score += 0.6
            else:
                issues.append(f"Used fabricated information: {fabricated_used}")
            
            # Should show some skepticism
            skeptical_phrases = ["however", "but", "seems incorrect", "appears to be", "may be wrong"]
            if any(phrase in answer_lower for phrase in skeptical_phrases):
                score += 0.4
            else:
                issues.append("No skepticism shown for fabricated context")
                
        elif test_case.test_type == "specific":
            # Should use specific context terms
            key_terms = test_case.expected_behavior.split(": ")[1].split(", ")
            used_terms = [term for term in key_terms if term.lower() in answer_lower]
            
            if len(used_terms) >= len(key_terms) * 0.5:  # At least 50% of terms
                score += 0.8
            else:
                issues.append(f"Used only {len(used_terms)}/{len(key_terms)} specific terms")
            
            # Should have citations
            if citations > 0:
                score += 0.2
            else:
                issues.append("No citations for specific context")
                
        elif test_case.test_type == "contradictory":
            # Should show skepticism or reject contradiction
            skeptical_phrases = [
                "incorrect", "wrong", "contradiction", "however", "but", 
                "appears to be false", "seems incorrect", "conflicting"
            ]
            
            if any(phrase in answer_lower for phrase in skeptical_phrases):
                score += 0.8
            else:
                issues.append("Accepted contradictory information without question")
            
            # Should not be overly confident
            if confidence < 0.7:
                score += 0.2
            else:
                issues.append(f"Too confident ({confidence:.1%}) with contradictory context")
        
        return min(score, 1.0), issues
    
    def run_test_case(self, test_case: FaithfulnessTestCase) -> FaithfulnessResult:
        """Run a single faithfulness test case."""
        start_time = time.time()
        
        try:
            result = self.rag_system.answer_generator.generate(
                query=test_case.query,
                chunks=test_case.context_chunks
            )
            
            generation_time = time.time() - start_time
            
            # Evaluate faithfulness
            faithfulness_score, issues = self._evaluate_faithfulness(
                test_case, result.answer, len(result.citations), result.confidence_score
            )
            
            return FaithfulnessResult(
                test_case=test_case,
                answer=result.answer,
                citations=len(result.citations),
                confidence=result.confidence_score,
                generation_time=generation_time,
                faithfulness_score=faithfulness_score,
                issues_detected=issues,
                timestamp=datetime.now().isoformat()
            )
            
        except Exception as e:
            return FaithfulnessResult(
                test_case=test_case,
                answer=f"ERROR: {e}",
                citations=0,
                confidence=0.0,
                generation_time=time.time() - start_time,
                faithfulness_score=0.0,
                issues_detected=[f"Generation failed: {e}"],
                timestamp=datetime.now().isoformat()
            )
    
    def run_full_suite(self) -> List[FaithfulnessResult]:
        """Run the complete faithfulness test suite."""
        print("Running RAG Faithfulness Test Suite...")
        print(f"Total tests: {len(self.test_cases)}")
        
        results = []
        
        for i, test_case in enumerate(self.test_cases, 1):
            print(f"\nTest {i}/{len(self.test_cases)}: {test_case.test_id}")
            print(f"Type: {test_case.test_type}")
            print(f"Query: {test_case.query}")
            
            result = self.run_test_case(test_case)
            results.append(result)
            
            print(f"Faithfulness Score: {result.faithfulness_score:.2f}")
            if result.issues_detected:
                print(f"Issues: {'; '.join(result.issues_detected)}")
        
        self.results_history.extend(results)
        return results
    
    def generate_report(self, results: List[FaithfulnessResult]) -> Dict[str, Any]:
        """Generate a comprehensive faithfulness report."""
        
        # Group results by test type
        by_type = {}
        for result in results:
            test_type = result.test_case.test_type
            if test_type not in by_type:
                by_type[test_type] = []
            by_type[test_type].append(result)
        
        # Calculate metrics
        report = {
            "overall_metrics": {
                "total_tests": len(results),
                "average_faithfulness": sum(r.faithfulness_score for r in results) / len(results),
                "average_confidence": sum(r.confidence for r in results) / len(results),
                "average_generation_time": sum(r.generation_time for r in results) / len(results),
                "tests_with_issues": len([r for r in results if r.issues_detected])
            },
            "by_test_type": {},
            "critical_issues": [],
            "recommendations": []
        }
        
        # Analyze by test type
        for test_type, type_results in by_type.items():
            type_metrics = {
                "count": len(type_results),
                "average_faithfulness": sum(r.faithfulness_score for r in type_results) / len(type_results),
                "average_confidence": sum(r.confidence for r in type_results) / len(type_results),
                "common_issues": []
            }
            
            # Find common issues
            all_issues = []
            for result in type_results:
                all_issues.extend(result.issues_detected)
            
            issue_counts = {}
            for issue in all_issues:
                issue_counts[issue] = issue_counts.get(issue, 0) + 1
            
            type_metrics["common_issues"] = sorted(issue_counts.items(), key=lambda x: x[1], reverse=True)
            report["by_test_type"][test_type] = type_metrics
        
        # Identify critical issues
        for result in results:
            if result.faithfulness_score < 0.3:
                report["critical_issues"].append({
                    "test_id": result.test_case.test_id,
                    "issue": f"Very low faithfulness score: {result.faithfulness_score:.2f}",
                    "details": result.issues_detected
                })
        
        # Generate recommendations
        if report["overall_metrics"]["average_faithfulness"] < 0.6:
            report["recommendations"].append("Overall faithfulness is low - strengthen system prompts")
        
        if any(avg_conf > 0.7 for avg_conf in [report["by_test_type"].get(t, {}).get("average_confidence", 0) for t in ["fabricated", "contradictory"]]):
            report["recommendations"].append("Model too confident with questionable context - add uncertainty handling")
        
        if report["by_test_type"].get("no_context", {}).get("average_confidence", 0) > 0.4:
            report["recommendations"].append("Model should be less confident when no context provided")
        
        return report
    
    def save_results(self, results: List[FaithfulnessResult], filename: str = None):
        """Save results to JSON file."""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"faithfulness_results_{timestamp}.json"
        
        filepath = Path(__file__).parent / filename
        
        # Convert results to JSON-serializable format
        serializable_results = []
        for result in results:
            result_dict = asdict(result)
            # Convert test_case to dict as well
            result_dict["test_case"] = asdict(result.test_case)
            serializable_results.append(result_dict)
        
        with open(filepath, 'w') as f:
            json.dump(serializable_results, f, indent=2)
        
        print(f"Results saved to: {filepath}")
        return filepath


def main():
    """Run the faithfulness analysis suite."""
    print("RAG Faithfulness Analysis Suite")
    print("=" * 50)
    
    # Initialize analyzer
    analyzer = RAGFaithfulnessAnalyzer()
    
    # Run tests
    results = analyzer.run_full_suite()
    
    # Generate report
    report = analyzer.generate_report(results)
    
    # Print summary
    print("\n" + "=" * 50)
    print("FAITHFULNESS ANALYSIS SUMMARY")
    print("=" * 50)
    
    print(f"Overall Faithfulness Score: {report['overall_metrics']['average_faithfulness']:.2f}")
    print(f"Tests with Issues: {report['overall_metrics']['tests_with_issues']}/{report['overall_metrics']['total_tests']}")
    
    print("\nBy Test Type:")
    for test_type, metrics in report["by_test_type"].items():
        print(f"  {test_type}: {metrics['average_faithfulness']:.2f} avg faithfulness")
    
    if report["recommendations"]:
        print("\nRecommendations:")
        for rec in report["recommendations"]:
            print(f"  - {rec}")
    
    # Save results
    analyzer.save_results(results)
    
    return analyzer, results, report


if __name__ == "__main__":
    main()