"""
Comprehensive Diagnostic Test Runner

This script executes all diagnostic test suites and generates a comprehensive
forensic analysis report of the RAG system.
"""

import os
import sys
import json
import time
import logging
from pathlib import Path
from datetime import datetime

# Configure logging to see ComponentFactory logs
logging.basicConfig(level=logging.INFO, format='[%(name)s] %(levelname)s: %(message)s')

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from tests.diagnostic.base_diagnostic import DiagnosticTestBase
from tests.diagnostic.test_configuration_forensics import ConfigurationForensics
from tests.diagnostic.test_answer_generation_forensics import AnswerGenerationForensics


class ComprehensiveDiagnosticRunner:
    """
    Runs all diagnostic test suites and generates comprehensive analysis.
    
    This runner executes all forensic tests and provides:
    - Complete system state analysis
    - Critical issue identification
    - Root cause analysis
    - Fix recommendations with priorities
    """
    
    def __init__(self, output_dir: Path = None):
        self.output_dir = output_dir or Path("tests/diagnostic/results")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.all_results = []
        self.critical_issues = []
        self.recommendations = []
    
    def run_all_diagnostics(self):
        """Execute all diagnostic test suites."""
        print("="*80)
        print("RAG SYSTEM COMPREHENSIVE DIAGNOSTIC ANALYSIS")
        print(f"Session ID: {self.session_id}")
        print(f"Timestamp: {datetime.now().isoformat()}")
        print("="*80)
        
        # Test suites to run
        test_suites = [
            ("Configuration & Architecture Forensics", ConfigurationForensics),
            ("Answer Generation Deep Analysis (CRITICAL)", AnswerGenerationForensics),
        ]
        
        suite_results = {}
        
        for suite_name, suite_class in test_suites:
            print(f"\n🔍 RUNNING: {suite_name}")
            print("-" * 60)
            
            try:
                # Initialize and run test suite
                suite = suite_class(self.output_dir)
                start_time = time.time()
                
                results = suite.run_all_tests()
                
                end_time = time.time()
                duration = end_time - start_time
                
                suite_results[suite_name] = {
                    "results": results,
                    "duration": duration,
                    "success": True
                }
                
                # Extract critical issues and recommendations
                for result in results:
                    if hasattr(result, 'issues_found'):
                        self.critical_issues.extend(result.issues_found)
                    if hasattr(result, 'recommendations'):
                        self.recommendations.extend(result.recommendations)
                
                print(f"✅ Completed: {suite_name} ({duration:.2f}s)")
                suite.print_summary()
                
            except Exception as e:
                print(f"❌ Failed: {suite_name} - {str(e)}")
                suite_results[suite_name] = {
                    "results": [],
                    "duration": 0,
                    "success": False,
                    "error": str(e)
                }
        
        # Generate comprehensive analysis
        self.generate_comprehensive_analysis(suite_results)
        
        return suite_results
    
    def generate_comprehensive_analysis(self, suite_results: dict):
        """Generate comprehensive analysis of all diagnostic results."""
        
        analysis = {
            "session_info": {
                "session_id": self.session_id,
                "timestamp": datetime.now().isoformat(),
                "total_duration": sum(s.get("duration", 0) for s in suite_results.values())
            },
            "execution_summary": self._generate_execution_summary(suite_results),
            "critical_issues_analysis": self._analyze_critical_issues(),
            "root_cause_analysis": self._perform_root_cause_analysis(),
            "fix_recommendations": self._prioritize_recommendations(),
            "development_validation_assessment": self._assess_development_validation(),
            "detailed_results": suite_results
        }
        
        # Save comprehensive analysis
        analysis_file = self.output_dir / f"comprehensive_analysis_{self.session_id}.json"
        with open(analysis_file, 'w') as f:
            json.dump(analysis, f, indent=2, default=str)
        
        # Generate executive summary
        self._generate_executive_summary(analysis)
        
        print(f"\n📊 Comprehensive analysis saved to: {analysis_file}")
        
    def _generate_execution_summary(self, suite_results: dict) -> dict:
        """Generate execution summary."""
        total_suites = len(suite_results)
        successful_suites = sum(1 for s in suite_results.values() if s.get("success", False))
        
        total_tests = 0
        successful_tests = 0
        
        for suite in suite_results.values():
            if suite.get("success", False):
                results = suite.get("results", [])
                total_tests += len(results)
                successful_tests += sum(1 for r in results if getattr(r, 'success', False))
        
        return {
            "total_test_suites": total_suites,
            "successful_suites": successful_suites,
            "suite_success_rate": successful_suites / total_suites if total_suites > 0 else 0,
            "total_individual_tests": total_tests,
            "successful_individual_tests": successful_tests,
            "test_success_rate": successful_tests / total_tests if total_tests > 0 else 0
        }
    
    def _analyze_critical_issues(self) -> dict:
        """Analyze and categorize critical issues."""
        issue_categories = {
            "answer_quality": [],
            "model_configuration": [],
            "confidence_calculation": [],
            "architecture": [],
            "source_attribution": [],
            "other": []
        }
        
        for issue in self.critical_issues:
            issue_lower = issue.lower()
            
            if any(keyword in issue_lower for keyword in ["squad2", "fragment", "extractive", "answer"]):
                issue_categories["answer_quality"].append(issue)
            elif any(keyword in issue_lower for keyword in ["model", "configuration", "config"]):
                issue_categories["model_configuration"].append(issue)
            elif any(keyword in issue_lower for keyword in ["confidence", "hardcoded"]):
                issue_categories["confidence_calculation"].append(issue)
            elif any(keyword in issue_lower for keyword in ["architecture", "legacy", "unified"]):
                issue_categories["architecture"].append(issue)
            elif any(keyword in issue_lower for keyword in ["source", "attribution", "metadata", "unknown"]):
                issue_categories["source_attribution"].append(issue)
            else:
                issue_categories["other"].append(issue)
        
        return {
            "total_critical_issues": len(self.critical_issues),
            "issues_by_category": issue_categories,
            "severity_assessment": self._assess_issue_severity(issue_categories)
        }
    
    def _perform_root_cause_analysis(self) -> dict:
        """Perform root cause analysis of identified issues."""
        root_causes = {
            "primary_root_causes": [],
            "secondary_causes": [],
            "causal_relationships": {}
        }
        
        # Analyze issue patterns to identify root causes
        if any("squad2" in issue.lower() for issue in self.critical_issues):
            root_causes["primary_root_causes"].append({
                "cause": "Squad2 Extractive QA Model Usage",
                "description": "Configuration using extractive QA model instead of generative model",
                "affected_areas": ["answer_quality", "response_completeness", "user_experience"],
                "evidence": [issue for issue in self.critical_issues if "squad2" in issue.lower()]
            })
        
        if any("hardcoded" in issue.lower() for issue in self.critical_issues):
            root_causes["primary_root_causes"].append({
                "cause": "Hardcoded Confidence Values",
                "description": "Confidence calculation using hardcoded defaults instead of model uncertainty",
                "affected_areas": ["confidence_calibration", "answer_reliability", "system_transparency"],
                "evidence": [issue for issue in self.critical_issues if "hardcoded" in issue.lower()]
            })
        
        if any("legacy" in issue.lower() for issue in self.critical_issues):
            root_causes["secondary_causes"].append({
                "cause": "Configuration Architecture Mismatch",
                "description": "System using legacy architecture configuration instead of Phase 4 modular",
                "affected_areas": ["architecture_display", "component_usage", "performance_metrics"],
                "evidence": [issue for issue in self.critical_issues if "legacy" in issue.lower()]
            })
        
        return root_causes
    
    def _prioritize_recommendations(self) -> dict:
        """Prioritize fix recommendations by impact and complexity."""
        recommendations = {
            "immediate_critical_fixes": [],
            "high_priority_fixes": [],
            "medium_priority_fixes": [],
            "implementation_order": []
        }
        
        # Categorize recommendations by priority
        for rec in set(self.recommendations):  # Remove duplicates
            rec_lower = rec.lower()
            
            if any(keyword in rec_lower for keyword in ["squad2", "model", "generative"]):
                recommendations["immediate_critical_fixes"].append({
                    "recommendation": rec,
                    "priority": "CRITICAL",
                    "estimated_effort": "Medium",
                    "expected_impact": "High",
                    "implementation_notes": "Replace Squad2 with generative model in configuration"
                })
            elif any(keyword in rec_lower for keyword in ["confidence", "hardcoded"]):
                recommendations["immediate_critical_fixes"].append({
                    "recommendation": rec,
                    "priority": "CRITICAL",
                    "estimated_effort": "Medium",
                    "expected_impact": "High",
                    "implementation_notes": "Fix confidence calculation in HuggingFaceAnswerGenerator"
                })
            elif any(keyword in rec_lower for keyword in ["architecture", "configuration"]):
                recommendations["high_priority_fixes"].append({
                    "recommendation": rec,
                    "priority": "HIGH",
                    "estimated_effort": "Low",
                    "expected_impact": "Medium",
                    "implementation_notes": "Update configuration to use Phase 4 modular architecture"
                })
            else:
                recommendations["medium_priority_fixes"].append({
                    "recommendation": rec,
                    "priority": "MEDIUM",
                    "estimated_effort": "Variable",
                    "expected_impact": "Variable"
                })
        
        # Define implementation order
        recommendations["implementation_order"] = [
            "1. Replace Squad2 model with generative model (CRITICAL)",
            "2. Fix hardcoded confidence calculation (CRITICAL)",
            "3. Update configuration to Phase 4 modular architecture (HIGH)",
            "4. Fix source attribution metadata propagation (HIGH)",
            "5. Validate all fixes with comprehensive testing (HIGH)"
        ]
        
        return recommendations
    
    def _assess_development_validation(self) -> dict:
        """Assess development validation based on diagnostic results."""
        readiness = {
            "current_status": "NOT_READY",
            "readiness_score": 0,
            "blocking_issues": [],
            "quality_gates": {},
            "requirements_for_validation_complete": []
        }
        
        # Quality gates assessment
        quality_gates = {
            "answer_quality": False,
            "confidence_calibration": False,
            "source_attribution": False,
            "architecture_display": False,
            "professional_responses": False
        }
        
        # Check each quality gate
        critical_issues_lower = [issue.lower() for issue in self.critical_issues]
        
        if not any("fragment" in issue or "squad2" in issue for issue in critical_issues_lower):
            quality_gates["answer_quality"] = True
        
        if not any("hardcoded" in issue or "confidence" in issue for issue in critical_issues_lower):
            quality_gates["confidence_calibration"] = True
        
        if not any("unknown" in issue or "attribution" in issue for issue in critical_issues_lower):
            quality_gates["source_attribution"] = True
        
        if not any("legacy" in issue or "architecture" in issue for issue in critical_issues_lower):
            quality_gates["architecture_display"] = True
        
        readiness["quality_gates"] = quality_gates
        
        # Calculate readiness score
        passed_gates = sum(1 for gate in quality_gates.values() if gate)
        readiness["readiness_score"] = (passed_gates / len(quality_gates)) * 100
        
        # Determine status
        if readiness["readiness_score"] >= 90:
            readiness["current_status"] = "VALIDATION_COMPLETE"
        elif readiness["readiness_score"] >= 70:
            readiness["current_status"] = "STAGING_READY"
        elif readiness["readiness_score"] >= 50:
            readiness["current_status"] = "DEVELOPMENT_READY"
        else:
            readiness["current_status"] = "NOT_READY"
        
        # Identify blocking issues
        for gate, passed in quality_gates.items():
            if not passed:
                readiness["blocking_issues"].append(gate)
        
        # Requirements for validation complete
        readiness["requirements_for_validation_complete"] = [
            "✅ Answer quality: Coherent, complete responses (not fragments)",
            "✅ Confidence calibration: Dynamic scoring based on actual uncertainty",
            "✅ Source attribution: Proper page/section references (not 'unknown')",
            "✅ Architecture display: Correct Phase 4 'modular' architecture",
            "✅ Professional responses: Suitable for development validation"
        ]
        
        return readiness
    
    def _assess_issue_severity(self, issue_categories: dict) -> dict:
        """Assess the severity of issues by category."""
        severity = {
            "critical": 0,
            "high": 0,
            "medium": 0,
            "low": 0
        }
        
        # Critical: Answer quality and model configuration issues
        severity["critical"] = len(issue_categories["answer_quality"]) + len(issue_categories["model_configuration"])
        
        # High: Confidence and architecture issues
        severity["high"] = len(issue_categories["confidence_calculation"]) + len(issue_categories["architecture"])
        
        # Medium: Source attribution issues
        severity["medium"] = len(issue_categories["source_attribution"])
        
        # Low: Other issues
        severity["low"] = len(issue_categories["other"])
        
        return severity
    
    def _generate_executive_summary(self, analysis: dict):
        """Generate executive summary for console output."""
        print("\n" + "="*80)
        print("EXECUTIVE SUMMARY - RAG SYSTEM DIAGNOSTIC ANALYSIS")
        print("="*80)
        
        # Development validation
        readiness = analysis["development_validation_assessment"]
        print(f"\n🎯 DEVELOPMENT VALIDATION: {readiness['current_status']}")
        print(f"📊 Readiness Score: {readiness['readiness_score']:.0f}%")
        
        # Critical issues
        critical_analysis = analysis["critical_issues_analysis"]
        print(f"\n🚨 CRITICAL ISSUES FOUND: {critical_analysis['total_critical_issues']}")
        
        for category, issues in critical_analysis["issues_by_category"].items():
            if issues:
                print(f"   {category.upper()}: {len(issues)} issues")
        
        # Root causes
        root_causes = analysis["root_cause_analysis"]
        print(f"\n🔍 PRIMARY ROOT CAUSES:")
        for i, cause in enumerate(root_causes["primary_root_causes"], 1):
            print(f"   {i}. {cause['cause']}")
        
        # Implementation order
        recommendations = analysis["fix_recommendations"]
        print(f"\n🛠️  FIX IMPLEMENTATION ORDER:")
        for order in recommendations["implementation_order"]:
            print(f"   {order}")
        
        # Quality gates
        print(f"\n✅ QUALITY GATES STATUS:")
        for gate, status in readiness["quality_gates"].items():
            status_icon = "✅" if status else "❌"
            print(f"   {status_icon} {gate.replace('_', ' ').title()}")
        
        print(f"\n📁 Detailed results saved to: {self.output_dir}")
        print("="*80)


def main():
    """Main execution function."""
    print("Starting comprehensive RAG system diagnostic analysis...")
    
    # Create output directory
    output_dir = Path("tests/diagnostic/results")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Run diagnostics
    runner = ComprehensiveDiagnosticRunner(output_dir)
    results = runner.run_all_diagnostics()
    
    print("\n🎉 Diagnostic analysis completed!")
    print(f"📋 Results available in: {output_dir}")
    
    return results


if __name__ == "__main__":
    main()