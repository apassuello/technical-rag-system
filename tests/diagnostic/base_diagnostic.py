"""
Base diagnostic test framework for comprehensive system analysis.

This module provides the foundation for forensic-level testing of the RAG system,
including data capture, analysis utilities, and reporting capabilities.
"""

import json
import os
import sys
import time
import traceback
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import yaml
import logging

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

logger = logging.getLogger(__name__)


@dataclass
class DiagnosticResult:
    """Structured result for diagnostic test analysis."""
    test_name: str
    component: str
    success: bool
    start_time: str
    end_time: str
    duration: float
    data_captured: Dict[str, Any]
    analysis_results: Dict[str, Any]
    issues_found: List[str]
    recommendations: List[str]
    raw_data: Dict[str, Any]
    error_details: Optional[str] = None


class DiagnosticTestBase:
    """
    Base class for all diagnostic tests with comprehensive data capture.
    
    This class provides utilities for:
    - Systematic data collection at each pipeline stage
    - Error handling and logging
    - Result aggregation and analysis
    - Report generation in multiple formats
    """
    
    def __init__(self, output_dir: Optional[Path] = None):
        """
        Initialize diagnostic test framework.
        
        Args:
            output_dir: Directory to store diagnostic results
        """
        # Use absolute path from project root
        self.output_dir = output_dir or (project_root / "tests" / "diagnostic" / "results")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.results: List[DiagnosticResult] = []
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Setup logging
        self.logger = self._setup_logging()
    
    def _setup_logging(self) -> logging.Logger:
        """Setup detailed logging for diagnostic tests."""
        logger = logging.getLogger(f"diagnostic_{self.__class__.__name__}")
        logger.setLevel(logging.DEBUG)
        
        # Create file handler for detailed logs
        log_file = self.output_dir / f"diagnostic_{self.session_id}.log"
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        
        # Create formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
        return logger
    
    def capture_system_state(self) -> Dict[str, Any]:
        """Capture complete system state for analysis."""
        return {
            "timestamp": datetime.now().isoformat(),
            "python_version": sys.version,
            "python_path": sys.path,
            "working_directory": os.getcwd(),
            "environment_variables": dict(os.environ),
            "project_root": str(project_root),
            "session_id": self.session_id
        }
    
    def safe_execute(self, test_func, test_name: str, component: str) -> DiagnosticResult:
        """
        Safely execute a test function with comprehensive error handling.
        
        Args:
            test_func: Test function to execute
            test_name: Name of the test
            component: Component being tested
            
        Returns:
            DiagnosticResult with complete execution details
        """
        start_time = datetime.now()
        self.logger.info(f"Starting test: {test_name} for component: {component}")
        
        try:
            # Execute test and capture results
            data_captured, analysis_results, issues_found, recommendations = test_func()
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            result = DiagnosticResult(
                test_name=test_name,
                component=component,
                success=True,
                start_time=start_time.isoformat(),
                end_time=end_time.isoformat(),
                duration=duration,
                data_captured=data_captured,
                analysis_results=analysis_results,
                issues_found=issues_found,
                recommendations=recommendations,
                raw_data={"system_state": self.capture_system_state()}
            )
            
            self.logger.info(f"Test completed successfully: {test_name}")
            
        except Exception as e:
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            error_details = {
                "exception_type": type(e).__name__,
                "exception_message": str(e),
                "traceback": traceback.format_exc()
            }
            
            result = DiagnosticResult(
                test_name=test_name,
                component=component,
                success=False,
                start_time=start_time.isoformat(),
                end_time=end_time.isoformat(),
                duration=duration,
                data_captured={},
                analysis_results={},
                issues_found=[f"Test execution failed: {str(e)}"],
                recommendations=["Fix test execution error before proceeding"],
                raw_data={"system_state": self.capture_system_state()},
                error_details=json.dumps(error_details)
            )
            
            self.logger.error(f"Test failed: {test_name} - {str(e)}")
            self.logger.error(f"Traceback: {traceback.format_exc()}")
        
        self.results.append(result)
        return result
    
    def get_absolute_config_path(self, config_path: str) -> Path:
        """Get absolute path to configuration file from project root."""
        if Path(config_path).is_absolute():
            return Path(config_path)
        else:
            return project_root / config_path
    
    def load_config(self, config_path: str) -> Dict[str, Any]:
        """Load and parse configuration file with error handling."""
        try:
            config_file = self.get_absolute_config_path(config_path)
            self.logger.debug(f"Loading config from: {config_file}")
            
            if not config_file.exists():
                raise FileNotFoundError(f"Config file not found: {config_file}")
            
            with open(config_file, 'r') as f:
                if config_path.endswith('.yaml') or config_path.endswith('.yml'):
                    config = yaml.safe_load(f)
                elif config_path.endswith('.json'):
                    config = json.load(f)
                else:
                    # Try YAML first, then JSON
                    try:
                        f.seek(0)
                        config = yaml.safe_load(f)
                    except:
                        f.seek(0)
                        config = json.load(f)
            
            return config
            
        except Exception as e:
            self.logger.error(f"Failed to load config {config_path}: {str(e)}")
            return {}
    
    def analyze_data_quality(self, data: Any, field_name: str) -> Dict[str, Any]:
        """Analyze quality and completeness of captured data."""
        analysis = {
            "field_name": field_name,
            "data_type": type(data).__name__,
            "is_empty": data is None or (hasattr(data, '__len__') and len(data) == 0),
            "has_unknown_values": False,
            "validation_issues": []
        }
        
        # Check for unknown/null values
        if isinstance(data, dict):
            analysis["dict_size"] = len(data)
            analysis["has_unknown_values"] = any(
                v in ["unknown", "Unknown", None, ""] 
                for v in data.values() if isinstance(v, (str, type(None)))
            )
            analysis["unknown_fields"] = [
                k for k, v in data.items() 
                if v in ["unknown", "Unknown", None, ""]
            ]
        elif isinstance(data, list):
            analysis["list_size"] = len(data)
            analysis["has_unknown_values"] = any(
                item in ["unknown", "Unknown", None, ""] 
                for item in data if isinstance(item, (str, type(None)))
            )
        elif isinstance(data, str):
            analysis["string_length"] = len(data)
            analysis["has_unknown_values"] = data in ["unknown", "Unknown", ""]
        
        # Validation checks
        if analysis["is_empty"]:
            analysis["validation_issues"].append("Data is empty")
        
        if analysis["has_unknown_values"]:
            analysis["validation_issues"].append("Contains unknown/null values")
        
        return analysis
    
    def save_result(self, result: DiagnosticResult, filename: Optional[str] = None):
        """Save diagnostic result to file."""
        if filename is None:
            filename = f"{result.test_name}_{result.component}_{self.session_id}.json"
        
        output_file = self.output_dir / filename
        
        try:
            with open(output_file, 'w') as f:
                json.dump(asdict(result), f, indent=2, default=str)
            
            self.logger.info(f"Result saved to: {output_file}")
            
        except Exception as e:
            self.logger.error(f"Failed to save result: {str(e)}")
    
    def generate_summary_report(self) -> Dict[str, Any]:
        """Generate comprehensive summary report of all diagnostic results."""
        total_tests = len(self.results)
        successful_tests = sum(1 for r in self.results if r.success)
        failed_tests = total_tests - successful_tests
        
        # Aggregate issues by component
        issues_by_component = {}
        for result in self.results:
            component = result.component
            if component not in issues_by_component:
                issues_by_component[component] = []
            issues_by_component[component].extend(result.issues_found)
        
        # Performance analysis
        durations = [r.duration for r in self.results if r.success]
        avg_duration = sum(durations) / len(durations) if durations else 0
        
        summary = {
            "session_id": self.session_id,
            "timestamp": datetime.now().isoformat(),
            "test_execution_summary": {
                "total_tests": total_tests,
                "successful_tests": successful_tests,
                "failed_tests": failed_tests,
                "success_rate": (successful_tests / total_tests) if total_tests > 0 else 0,
                "average_duration": avg_duration,
                "total_duration": sum(r.duration for r in self.results)
            },
            "issues_by_component": issues_by_component,
            "critical_issues": [
                issue for result in self.results 
                for issue in result.issues_found 
                if any(keyword in issue.lower() for keyword in ["critical", "error", "fail", "broken"])
            ],
            "recommendations": [
                rec for result in self.results 
                for rec in result.recommendations
            ],
            "test_results": [asdict(result) for result in self.results]
        }
        
        # Save summary report
        summary_file = self.output_dir / f"diagnostic_summary_{self.session_id}.json"
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2, default=str)
        
        self.logger.info(f"Summary report saved to: {summary_file}")
        return summary
    
    def print_summary(self):
        """Print diagnostic summary to console."""
        summary = self.generate_summary_report()
        
        print(f"\n{'='*60}")
        print(f"DIAGNOSTIC TEST SUMMARY - Session {self.session_id}")
        print(f"{'='*60}")
        
        exec_summary = summary["test_execution_summary"]
        print(f"Tests Executed: {exec_summary['total_tests']}")
        print(f"Successful: {exec_summary['successful_tests']}")
        print(f"Failed: {exec_summary['failed_tests']}")
        print(f"Success Rate: {exec_summary['success_rate']:.1%}")
        print(f"Total Duration: {exec_summary['total_duration']:.2f}s")
        
        if summary["critical_issues"]:
            print(f"\n🚨 CRITICAL ISSUES FOUND:")
            for i, issue in enumerate(summary["critical_issues"][:5], 1):
                print(f"  {i}. {issue}")
        
        print(f"\n📊 Issues by Component:")
        for component, issues in summary["issues_by_component"].items():
            if issues:
                print(f"  {component}: {len(issues)} issues")
        
        print(f"\n📁 Results saved to: {self.output_dir}")
        print(f"{'='*60}\n")


class DataValidator:
    """Utilities for validating captured data quality."""
    
    @staticmethod
    def validate_metadata(metadata: Dict[str, Any]) -> List[str]:
        """Validate metadata completeness and quality."""
        issues = []
        
        required_fields = ["source", "page"]
        for field in required_fields:
            if field not in metadata:
                issues.append(f"Missing required field: {field}")
            elif metadata[field] in ["unknown", "Unknown", None, ""]:
                issues.append(f"Field contains unknown value: {field}")
        
        return issues
    
    @staticmethod
    def validate_document_object(doc) -> List[str]:
        """Validate Document object completeness."""
        issues = []
        
        if not hasattr(doc, 'content') or not doc.content:
            issues.append("Document missing content")
        
        if not hasattr(doc, 'metadata') or not doc.metadata:
            issues.append("Document missing metadata")
        else:
            issues.extend(DataValidator.validate_metadata(doc.metadata))
        
        return issues
    
    @staticmethod
    def validate_confidence_score(confidence: float) -> List[str]:
        """Validate confidence score reasonableness."""
        issues = []
        
        if not isinstance(confidence, (int, float)):
            issues.append(f"Confidence is not numeric: {type(confidence)}")
        elif confidence < 0 or confidence > 1:
            issues.append(f"Confidence out of range [0,1]: {confidence}")
        elif confidence == 0.8:
            issues.append("Confidence appears to be hardcoded default (0.8)")
        elif confidence == 0.1:
            issues.append("Confidence appears to be hardcoded default (0.1)")
        
        return issues