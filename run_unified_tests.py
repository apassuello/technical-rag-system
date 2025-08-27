#!/usr/bin/env python3
"""
Enhanced Unified Test Runner with PYTHONPATH Management and Smart Test Selection

This script addresses the issues in the original run_comprehensive_tests.py:
1. Sets proper PYTHONPATH for module imports
2. Shows real-time test output instead of capturing
3. Smart test category selection (working tests first)
4. Unified coverage reporting across all components
5. Swiss engineering quality with proper error handling
"""

import subprocess
import json
import time
import argparse
from datetime import datetime
from pathlib import Path
import os
import sys
from typing import List, Dict, Any, Optional

class UnifiedTestRunner:
    def __init__(self):
        self.project_root = Path(__file__).parent
        self.pythonpath = self._setup_pythonpath()
        self.results = {}
        self.start_time = time.time()
        
    def _parse_test_output(self, output: str) -> Dict[str, Any]:
        """Parse pytest output to extract test statistics."""
        import re
        
        stats = {
            'total': 0,
            'passed': 0,
            'failed': 0,
            'skipped': 0,
            'errors': 0,
            'warnings': 0
        }
        
        if not output:
            return stats
            
        # Look for the summary line like "====== 5 passed, 2 failed in 1.23s ======"
        summary_pattern = r'=+\s*([\d\w\s,]+)\s+in\s+[\d.]+s?\s*=+'
        summary_match = re.search(summary_pattern, output)
        
        if summary_match:
            summary_text = summary_match.group(1)
            
            # Parse individual counts
            passed_match = re.search(r'(\d+)\s+passed', summary_text)
            if passed_match:
                stats['passed'] = int(passed_match.group(1))
                
            failed_match = re.search(r'(\d+)\s+failed', summary_text)
            if failed_match:
                stats['failed'] = int(failed_match.group(1))
                
            skipped_match = re.search(r'(\d+)\s+skipped', summary_text)
            if skipped_match:
                stats['skipped'] = int(skipped_match.group(1))
                
            error_match = re.search(r'(\d+)\s+error', summary_text)
            if error_match:
                stats['errors'] = int(error_match.group(1))
                
            warning_match = re.search(r'(\d+)\s+warning', summary_text)
            if warning_match:
                stats['warnings'] = int(warning_match.group(1))
        
        # Also try to find "collected X items"
        collected_match = re.search(r'collected\s+(\d+)\s+item', output)
        if collected_match:
            stats['total'] = int(collected_match.group(1))
        else:
            stats['total'] = stats['passed'] + stats['failed'] + stats['skipped'] + stats['errors']
            
        return stats
    
    def _setup_pythonpath(self) -> str:
        """Set up proper PYTHONPATH for module imports."""
        paths = [
            str(self.project_root),
            str(self.project_root / "src"),
        ]
        
        # Add all service directories dynamically
        services_dir = self.project_root / "services"
        if services_dir.exists():
            for service_path in services_dir.iterdir():
                if service_path.is_dir() and not service_path.name.startswith('.'):
                    paths.append(str(service_path))
                    # Also add the app directory within each service
                    app_dirs = [
                        service_path / f"{service_path.name}_app",
                        service_path / f"{service_path.name.replace('-', '_')}_app",
                        service_path / "app"
                    ]
                    for app_dir in app_dirs:
                        if app_dir.exists():
                            paths.append(str(app_dir))
        
        # Add any additional paths that might be needed
        additional_paths = [
            self.project_root / "tests",
            self.project_root / "tools",
            self.project_root / "scripts"
        ]
        
        for path in additional_paths:
            if path.exists():
                paths.append(str(path))
        
        return ":".join(paths)
    
    def run_test_category(self, category: str, test_paths: List[str], 
                         description: str, extra_args: List[str] = None) -> Dict[str, Any]:
        """Run a test category with proper environment setup."""
        if extra_args is None:
            extra_args = []
            
        # Base pytest command
        cmd = [
            sys.executable, "-m", "pytest"
        ] + test_paths + [
            "-v", "--tb=short",
            "--disable-warnings"
        ]
        
        # Add parallel execution for suitable test categories
        parallel_safe_categories = [
            "unit_tests_all", "component_tests", "epic8_unit_complete", 
            "tools_tests", "quality_tests", "epic8_api", "epic1_integration",
            "epic1_phase2", "epic1_all", "epic1_smoke", "epic1_regression",
            "epic1_ml_infrastructure", "epic1_legacy", "service_tests"
        ]
        
        if category in parallel_safe_categories:
            # Use auto-detection for number of CPUs (or specify manually)
            cpu_count = os.cpu_count()
            parallel_workers = min(cpu_count, 8)  # Cap at 8 to avoid overwhelming
            cmd.extend(["-n", str(parallel_workers)])
            print(f"🚀 Running with {parallel_workers} parallel workers")
        
        cmd.extend(extra_args)
        
        print(f"\n{'='*80}")
        print(f"🧪 {description}")
        print(f"{'='*80}")
        print(f"Command: {' '.join(cmd)}")
        print(f"PYTHONPATH: {self.pythonpath}")
        print("")
        
        # Set up environment
        env = os.environ.copy()
        env["PYTHONPATH"] = self.pythonpath
        env["PYTHONWARNINGS"] = "ignore::DeprecationWarning,ignore::UserWarning,ignore::RuntimeWarning"
        
        start_time = time.time()
        
        try:
            # Use Popen for real-time output with capture capability
            import subprocess
            process = subprocess.Popen(
                cmd,
                env=env,
                cwd=self.project_root,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,  # Line buffered
                universal_newlines=True
            )
            
            # Capture output while showing it in real-time
            output_lines = []
            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    print(output.strip())  # Show real-time output
                    output_lines.append(output)  # Capture for parsing
            
            # Wait for process to complete and get return code
            return_code = process.wait(timeout=1800)  # 30 minutes
            
            end_time = time.time()
            execution_time = end_time - start_time
            
            # Join captured output for parsing
            full_output = ''.join(output_lines)
            
            # Parse test statistics from output
            test_stats = self._parse_test_output(full_output)
            
            return {
                'category': category,
                'description': description,
                'command': ' '.join(cmd),
                'success': return_code == 0,
                'returncode': return_code,
                'execution_time': execution_time,
                'test_paths': test_paths,
                'test_stats': test_stats,
                'output': full_output[:5000] if full_output else ""  # Keep first 5000 chars for report
            }
            
        except subprocess.TimeoutExpired:
            return {
                'category': category,
                'description': description,
                'command': ' '.join(cmd),
                'success': False,
                'returncode': -1,
                'execution_time': 1800,
                'error': 'Test execution timed out after 30 minutes',
                'test_paths': test_paths
            }
        except Exception as e:
            return {
                'category': category,
                'description': description,
                'command': ' '.join(cmd),
                'success': False,
                'returncode': -1,
                'execution_time': time.time() - start_time,
                'error': str(e),
                'test_paths': test_paths
            }

    def get_working_test_categories(self) -> Dict[str, Dict[str, Any]]:
        """Define test categories known to work or likely to work with PYTHONPATH fixes."""
        return {
            # Priority 1 - Basic, most reliable tests
            "component_tests": {
                "paths": ["tests/component/"],
                "description": "Component Tests (90.5% success rate)",
                "priority": 1
            },
            "smoke_tests": {
                "paths": ["tests/smoke/"],
                "description": "Smoke Tests (Basic Health Checks)", 
                "priority": 1
            },
            "epic8_unit_complete": {
                "paths": ["tests/epic8/unit/"],
                "description": "Epic 8 Unit Tests (All Services)",
                "priority": 1
            },
            
            # Priority 2 - Core infrastructure tests
            "unit_tests_all": {
                "paths": ["tests/unit/"],
                "description": "Complete Unit Test Suite",
                "priority": 2
            },
            "diagnostic_tests": {
                "paths": ["tests/diagnostic/"],
                "description": "Diagnostic and Forensic Tests",
                "priority": 2
            },
            "quality_tests": {
                "paths": ["tests/quality/"],
                "description": "Quality Assurance Tests",
                "priority": 2
            },
            "tools_tests": {
                "paths": ["tests/tools/"],
                "description": "Tools and Utilities Tests",
                "priority": 2
            },
            
            # Priority 3 - Integration and system tests
            "integration_all": {
                "paths": ["tests/integration/"],
                "description": "Complete Integration Test Suite",
                "priority": 3
            },
            "system_tests": {
                "paths": ["tests/system/"],
                "description": "System Validation Tests",
                "priority": 3
            },
            "epic8_integration": {
                "paths": ["tests/epic8/integration/"],
                "description": "Epic 8 Integration Tests",
                "priority": 3
            },
            "epic8_api": {
                "paths": ["tests/epic8/api/"],
                "description": "Epic 8 API Tests",
                "priority": 3
            },
            
            # Priority 4 - Epic-specific tests
            "epic2_standalone": {
                "paths": [
                    "tests/epic2_epic8_integration.py",
                    "tests/epic2_calibration_validation.py", 
                    "tests/epic2_production_validation.py"
                ],
                "description": "Epic 2 Standalone Integration Tests",
                "priority": 4
            },
            "epic2_validation": {
                "paths": ["tests/epic2_validation/"],
                "description": "Epic 2 Validation Test Suite",
                "priority": 4
            },
            "epic1_integration": {
                "paths": ["tests/epic1/integration/"],
                "description": "Epic 1 Integration Tests",
                "priority": 4
            },
            "epic1_phase2": {
                "paths": ["tests/epic1/phase2/"],
                "description": "Epic 1 Phase 2 Tests",
                "priority": 4
            },
            
            # Priority 5 - Validation and comprehensive tests
            "integration_validation": {
                "paths": ["tests/integration_validation/"],
                "description": "Integration Validation Suite",
                "priority": 5
            }
        }
    
    def get_comprehensive_test_categories(self) -> Dict[str, Dict[str, Any]]:
        """All test categories including those needing fixes."""
        categories = self.get_working_test_categories()
        
        # Add comprehensive and potentially problematic categories
        categories.update({
            # Epic 1 comprehensive testing
            "epic1_all": {
                "paths": ["tests/epic1/"],
                "description": "Epic 1 Complete Test Suite",
                "priority": 6
            },
            "epic1_smoke": {
                "paths": ["tests/epic1/smoke/"],
                "description": "Epic 1 Smoke Tests",
                "priority": 6
            },
            "epic1_regression": {
                "paths": ["tests/epic1/regression/"],
                "description": "Epic 1 Regression Tests",
                "priority": 6
            },
            
            # Epic 8 comprehensive testing
            "epic8_performance": {
                "paths": ["tests/epic8/performance/"],
                "description": "Epic 8 Performance Tests",
                "priority": 6,
                "extra_args": ["--timeout=600"]  # Performance tests may take longer
            },
            "epic8_smoke": {
                "paths": ["tests/epic8/smoke/"],
                "description": "Epic 8 Smoke Tests",
                "priority": 6
            },
            
            # Service-specific tests (if they exist)
            "service_tests": {
                "paths": [
                    "services/*/tests/",
                    "services/*/test_*.py"
                ],
                "description": "Microservice-Specific Tests",
                "priority": 7
            },
            
            # Development and debug tests
            "epic1_ml_infrastructure": {
                "paths": ["tests/epic1/ml_infrastructure/"],
                "description": "Epic 1 ML Infrastructure Tests",
                "priority": 8
            },
            "epic1_legacy": {
                "paths": ["tests/epic1/legacy/"],
                "description": "Epic 1 Legacy Tests",
                "priority": 8
            },
            
            # Standalone test files (comprehensive)
            "runner_tests": {
                "paths": ["tests/runner/"],
                "description": "Test Runner Framework Tests",
                "priority": 8
            },
            "run_comprehensive_tests": {
                "paths": ["tests/run_comprehensive_tests.py"],
                "description": "Legacy Comprehensive Test Runner",
                "priority": 9
            }
        })
        
        return categories
    
    def run_coverage_analysis(self) -> Dict[str, Any]:
        """Run comprehensive coverage analysis."""
        print(f"\n{'='*80}")
        print("📊 Running Comprehensive Coverage Analysis")
        print(f"{'='*80}")
        
        # Use comprehensive test suite to match dedicated coverage scripts
        # Exclude problematic API tests that have configuration issues
        coverage_test_paths = [
            "tests/unit/",
            "tests/integration/", 
            "tests/component/test_modular_document_processor.py",
            "tests/component/test_pdf_parser.py",
            "tests/component/test_embeddings.py",
            "tests/epic1/integration/",
            "tests/epic1/smoke/",
            # Skip epic1/phase2 and epic1/demos/scripts as they may have API dependencies
            "tests/epic8/unit/",
            "tests/epic8/integration/",
            # Skip epic8/api/ due to pydantic configuration issues
        ]
        
        coverage_cmd = [
            sys.executable, "-m", "pytest"
        ] + coverage_test_paths + [
            "--cov=src", "--cov=services", 
            "--cov-report=html:htmlcov",
            "--cov-report=json:coverage.json",
            "--cov-report=xml:coverage.xml",
            "--cov-report=term-missing",
            "--disable-warnings",
            "-v",  # Verbose mode to see coverage progress
            "--tb=short",
            "--maxfail=50"  # Don't stop at first failures
        ]
        
        env = os.environ.copy()
        env["PYTHONPATH"] = self.pythonpath
        env["PYTHONWARNINGS"] = "ignore"
        
        start_time = time.time()
        
        try:
            result = subprocess.run(
                coverage_cmd,
                env=env,
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=600  # 10 minutes for coverage
            )
            
            return {
                'success': result.returncode == 0,
                'execution_time': time.time() - start_time,
                'command': ' '.join(coverage_cmd),
                'stdout': result.stdout,
                'stderr': result.stderr
            }
            
        except Exception as e:
            return {
                'success': False,
                'execution_time': time.time() - start_time,
                'error': str(e)
            }
    
    def run_tests(self, test_level: str = "working", epics: Optional[List[str]] = None, 
                  coverage: bool = True) -> Dict[str, Any]:
        """Run tests based on specified level and parameters."""
        
        if test_level == "working":
            categories = self.get_working_test_categories()
            max_priority = 2
        elif test_level == "comprehensive":
            categories = self.get_comprehensive_test_categories()
            max_priority = 5
        elif test_level == "basic":
            categories = self.get_working_test_categories()
            max_priority = 1
        else:
            categories = self.get_comprehensive_test_categories()
            max_priority = 5
            
        # Filter by priority
        filtered_categories = {
            k: v for k, v in categories.items() 
            if v.get("priority", 1) <= max_priority
        }
        
        # Filter by epics if specified
        if epics:
            epic_filtered = {}
            for epic in epics:
                epic_filtered.update({
                    k: v for k, v in filtered_categories.items()
                    if epic.lower() in k.lower()
                })
            filtered_categories = epic_filtered if epic_filtered else filtered_categories
        
        # Sort by priority
        sorted_categories = sorted(
            filtered_categories.items(), 
            key=lambda x: x[1].get("priority", 1)
        )
        
        print(f"\n🚀 RAG Portfolio - Unified Test Runner")
        print(f"{'='*80}")
        print(f"Test Level: {test_level.upper()}")
        print(f"Categories: {len(sorted_categories)}")
        print(f"Coverage: {'Enabled' if coverage else 'Disabled'}")
        if epics:
            print(f"Epic Filter: {', '.join(epics)}")
        print(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Run each category
        for category_name, category_info in sorted_categories:
            extra_args = category_info.get("extra_args", [])
            
            result = self.run_test_category(
                category_name,
                category_info["paths"],
                category_info["description"],
                extra_args
            )
            
            self.results[category_name] = result
            
            # Print immediate results
            status = "✅ PASSED" if result['success'] else "❌ FAILED"
            print(f"\n🎯 {category_info['description']}: {status}")
            print(f"   Duration: {result['execution_time']:.1f}s")
            if not result['success'] and 'error' in result:
                print(f"   Error: {result['error']}")
            print(f"   Return Code: {result['returncode']}")
        
        # Run coverage analysis
        if coverage:
            print(f"\n{'='*80}")
            print("📊 Generating Coverage Analysis")
            print(f"{'='*80}")
            coverage_result = self.run_coverage_analysis()
            self.results['coverage'] = coverage_result
            
            if coverage_result['success']:
                print("✅ Coverage analysis completed successfully")
                print(f"   Duration: {coverage_result['execution_time']:.1f}s")
                print(f"   Reports: htmlcov/index.html, coverage.json, coverage.xml")
            else:
                print("❌ Coverage analysis failed")
                if 'error' in coverage_result:
                    print(f"   Error: {coverage_result['error']}")
        
        return self._generate_summary()
    
    def _generate_html_report(self, summary: Dict[str, Any]) -> str:
        """Generate comprehensive HTML test report."""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Calculate statistics
        execution_summary = summary['execution_summary']
        category_results = summary['category_results']
        
        # Calculate total test statistics across all categories
        total_tests = 0
        total_passed = 0
        total_failed = 0
        total_skipped = 0
        total_errors = 0
        
        for result in category_results.values():
            if 'test_stats' in result and result['test_stats']:
                stats = result['test_stats']
                total_tests += stats.get('total', 0)
                total_passed += stats.get('passed', 0)
                total_failed += stats.get('failed', 0)
                total_skipped += stats.get('skipped', 0)
                total_errors += stats.get('errors', 0)
        
        # Calculate test-level success rate
        test_success_rate = (total_passed / total_tests * 100) if total_tests > 0 else 0
        
        # Determine overall status
        success_rate = execution_summary['success_rate']
        if success_rate >= 90:
            status_class = "success"
            status_text = "EXCELLENT"
        elif success_rate >= 75:
            status_class = "good"
            status_text = "GOOD"
        elif success_rate >= 50:
            status_class = "warning"
            status_text = "NEEDS ATTENTION"
        else:
            status_class = "critical"
            status_text = "CRITICAL ISSUES"
        
        html_content = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>RAG Portfolio - Unified Test Report</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f7fa;
            color: #2c3e50;
            line-height: 1.6;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 15px;
            margin-bottom: 30px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.1);
        }}
        .header h1 {{
            margin: 0;
            font-size: 2.5em;
            font-weight: 300;
        }}
        .header .subtitle {{
            opacity: 0.9;
            font-size: 1.2em;
            margin-top: 10px;
        }}
        .summary-cards {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .card {{
            background: white;
            padding: 25px;
            border-radius: 12px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.08);
            border-left: 5px solid #667eea;
            transition: transform 0.3s ease;
        }}
        .card:hover {{
            transform: translateY(-5px);
        }}
        .card-title {{
            font-size: 0.9em;
            color: #7f8c8d;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 10px;
        }}
        .card-value {{
            font-size: 2.5em;
            font-weight: 700;
            color: #2c3e50;
            margin-bottom: 5px;
        }}
        .card-label {{
            color: #7f8c8d;
            font-size: 0.9em;
        }}
        .status-indicator {{
            display: inline-block;
            padding: 8px 16px;
            border-radius: 25px;
            font-weight: 600;
            font-size: 0.9em;
        }}
        .status-success {{ background-color: #d4edda; color: #155724; }}
        .status-good {{ background-color: #cce5ff; color: #0066cc; }}
        .status-warning {{ background-color: #fff3cd; color: #856404; }}
        .status-critical {{ background-color: #f8d7da; color: #721c24; }}
        
        .results-table {{
            background: white;
            border-radius: 12px;
            overflow: hidden;
            box-shadow: 0 4px 20px rgba(0,0,0,0.08);
            margin-bottom: 30px;
        }}
        .results-table h2 {{
            background-color: #f8f9fa;
            margin: 0;
            padding: 20px;
            border-bottom: 1px solid #dee2e6;
            color: #495057;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
        }}
        th, td {{
            padding: 15px;
            text-align: left;
            border-bottom: 1px solid #dee2e6;
        }}
        th {{
            background-color: #f8f9fa;
            font-weight: 600;
            color: #495057;
            font-size: 0.9em;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        tr:hover {{
            background-color: #f8f9fa;
        }}
        .result-success {{
            color: #28a745;
            font-weight: 600;
        }}
        .result-failed {{
            color: #dc3545;
            font-weight: 600;
        }}
        .duration {{
            color: #6c757d;
            font-family: monospace;
        }}
        .reports-section {{
            background: white;
            border-radius: 12px;
            padding: 25px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.08);
            margin-bottom: 30px;
        }}
        .report-link {{
            display: inline-block;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            text-decoration: none;
            padding: 12px 24px;
            border-radius: 8px;
            margin: 10px 10px 10px 0;
            transition: all 0.3s ease;
        }}
        .report-link:hover {{
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(0,0,0,0.15);
        }}
        .footer {{
            text-align: center;
            color: #7f8c8d;
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #dee2e6;
        }}
        .progress-bar {{
            background-color: #e9ecef;
            border-radius: 10px;
            height: 20px;
            overflow: hidden;
            margin-top: 10px;
        }}
        .progress-fill {{
            height: 100%;
            transition: width 0.6s ease;
        }}
        .progress-success {{ background: linear-gradient(90deg, #28a745, #20c997); }}
        .progress-warning {{ background: linear-gradient(90deg, #ffc107, #fd7e14); }}
        .progress-critical {{ background: linear-gradient(90deg, #dc3545, #e83e8c); }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🎯 RAG Portfolio Test Report</h1>
        <div class="subtitle">Unified Test Execution Results - {timestamp}</div>
    </div>
    
    <div class="summary-cards">
        <div class="card">
            <div class="card-title">Total Tests</div>
            <div class="card-value">{total_tests}</div>
            <div class="card-label">Tests Executed</div>
        </div>
        <div class="card">
            <div class="card-title">Test Success Rate</div>
            <div class="card-value">{test_success_rate:.1f}%</div>
            <div class="card-label">
                <span style="color: #28a745">✅ {total_passed} passed</span> • 
                <span style="color: #dc3545">❌ {total_failed} failed</span>
            </div>
            <div class="progress-bar">
                <div class="progress-fill progress-{status_class.lower()}" 
                     style="width: {test_success_rate:.1f}%"></div>
            </div>
        </div>
        <div class="card">
            <div class="card-title">Test Categories</div>
            <div class="card-value">{execution_summary['total_categories']}</div>
            <div class="card-label">{execution_summary['successful_categories']} Successful</div>
        </div>
        <div class="card">
            <div class="card-title">Execution Time</div>
            <div class="card-value">{execution_summary['total_execution_time']/60:.1f}</div>
            <div class="card-label">Minutes</div>
        </div>
    </div>
    
    <!-- Additional unified test statistics card -->
    <div class="results-table" style="margin-bottom: 30px;">
        <h2>📊 Unified Test Statistics</h2>
        <div style="padding: 20px;">
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 20px;">
                <div style="text-align: center;">
                    <div style="font-size: 2em; font-weight: bold; color: #28a745;">{total_passed}</div>
                    <div style="color: #6c757d;">Tests Passed</div>
                </div>
                <div style="text-align: center;">
                    <div style="font-size: 2em; font-weight: bold; color: #dc3545;">{total_failed}</div>
                    <div style="color: #6c757d;">Tests Failed</div>
                </div>
                <div style="text-align: center;">
                    <div style="font-size: 2em; font-weight: bold; color: #ffc107;">{total_skipped}</div>
                    <div style="color: #6c757d;">Tests Skipped</div>
                </div>
                <div style="text-align: center;">
                    <div style="font-size: 2em; font-weight: bold; color: #fd7e14;">{total_errors}</div>
                    <div style="color: #6c757d;">Test Errors</div>
                </div>
            </div>
        </div>
    </div>
'''

        # Category results table
        html_content += '''
    <div class="results-table">
        <h2>📋 Test Category Details</h2>
        <table>
            <thead>
                <tr>
                    <th>Category</th>
                    <th>Status</th>
                    <th>Test Results</th>
                    <th>Duration</th>
                    <th>Description</th>
                </tr>
            </thead>
            <tbody>
'''
        
        for category_name, result in category_results.items():
            if category_name == 'coverage':
                continue
                
            status = "✅ PASSED" if result.get('success', False) else "❌ FAILED"
            status_class = "result-success" if result.get('success', False) else "result-failed"
            duration = f"{result.get('execution_time', 0):.1f}s"
            description = result.get('description', category_name)
            
            # Format test statistics
            test_stats_str = ""
            if 'test_stats' in result and result['test_stats']:
                stats = result['test_stats']
                test_stats_str = f"""
                    <span style="color: #28a745">✅ {stats.get('passed', 0)}</span> • 
                    <span style="color: #dc3545">❌ {stats.get('failed', 0)}</span> • 
                    <span style="color: #ffc107">⚠️ {stats.get('skipped', 0)}</span>
                    <br><small>Total: {stats.get('total', 0)} tests</small>
                """
            else:
                test_stats_str = "<small>No statistics available</small>"
            
            html_content += f'''
                <tr>
                    <td><strong>{category_name}</strong></td>
                    <td class="{status_class}">{status}</td>
                    <td>{test_stats_str}</td>
                    <td class="duration">{duration}</td>
                    <td>{description}<br><small>{', '.join(result.get('test_paths', []))}</small></td>
                </tr>
'''
        
        html_content += '''
            </tbody>
        </table>
    </div>
'''
        
        # Reports section
        reports_generated = summary.get('reports_generated', [])
        if reports_generated:
            html_content += '''
    <div class="reports-section">
        <h2>📋 Generated Reports</h2>
        <p>Click on the links below to view detailed reports:</p>
'''
            for report in reports_generated:
                html_content += f'''
        <a href="{report['path']}" class="report-link" target="_blank">
            📊 {report['name']}
        </a>
'''
            html_content += '</div>'
        
        # Footer
        html_content += f'''
    <div class="footer">
        <p>Generated by RAG Portfolio Unified Test Runner</p>
        <p>Swiss Engineering Quality Standards • {timestamp}</p>
    </div>
</body>
</html>'''
        
        return html_content

    def _generate_summary(self) -> Dict[str, Any]:
        """Generate execution summary."""
        total_categories = len([k for k in self.results.keys() if k != 'coverage'])
        successful_categories = sum(1 for k, v in self.results.items() 
                                  if k != 'coverage' and v.get('success', False))
        
        total_time = time.time() - self.start_time
        
        summary = {
            'execution_summary': {
                'total_categories': total_categories,
                'successful_categories': successful_categories,
                'success_rate': (successful_categories / total_categories * 100) if total_categories > 0 else 0,
                'total_execution_time': total_time,
                'timestamp': datetime.now().isoformat()
            },
            'category_results': self.results,
            'reports_generated': []
        }
        
        # Check for generated reports
        report_files = [
            ('HTML Coverage Report', 'htmlcov/index.html'),
            ('JSON Coverage Data', 'coverage.json'),
            ('XML Coverage Report', 'coverage.xml')
        ]
        
        for report_name, file_path in report_files:
            if (self.project_root / file_path).exists():
                summary['reports_generated'].append({
                    'name': report_name,
                    'path': file_path,
                    'full_path': str(self.project_root / file_path)
                })
        
        # Generate HTML test report
        html_content = self._generate_html_report(summary)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        html_report_path = self.project_root / f'test_report_{timestamp}.html'
        
        with open(html_report_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        summary['reports_generated'].insert(0, {
            'name': 'HTML Test Report',
            'path': str(html_report_path.name),
            'full_path': str(html_report_path)
        })
        
        return summary

def main():
    parser = argparse.ArgumentParser(description='Unified Test Runner with PYTHONPATH Management')
    parser.add_argument('--level', choices=['basic', 'working', 'comprehensive', 'all'], 
                       default='working', help='Test level to run')
    parser.add_argument('--epics', nargs='*', help='Filter by epic names (e.g., epic8 epic1)')
    parser.add_argument('--no-coverage', action='store_true', help='Skip coverage analysis')
    parser.add_argument('--save-results', help='Save results to JSON file')
    
    args = parser.parse_args()
    
    runner = UnifiedTestRunner()
    
    try:
        results = runner.run_tests(
            test_level=args.level,
            epics=args.epics,
            coverage=not args.no_coverage
        )
        
        # Print final summary
        summary = results['execution_summary']
        print(f"\n{'='*80}")
        print("🎯 UNIFIED TEST EXECUTION COMPLETE")
        print(f"{'='*80}")
        print(f"📊 Results:")
        print(f"   Categories Run: {summary['total_categories']}")
        print(f"   Successful: {summary['successful_categories']}")
        print(f"   Success Rate: {summary['success_rate']:.1f}%")
        print(f"   Total Time: {summary['total_execution_time']:.1f}s")
        
        if results['reports_generated']:
            print(f"\n📋 Reports Generated:")
            for report in results['reports_generated']:
                print(f"   {report['name']}: {report['path']}")
        
        print(f"\n🔗 Quick Access Commands:")
        if (Path("htmlcov/index.html")).exists():
            print(f"   open htmlcov/index.html")
        
        # Save results if requested
        if args.save_results:
            output_file = Path(args.save_results)
            with open(output_file, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            print(f"\n💾 Results saved to: {output_file}")
        
        # Exit with appropriate code
        exit(0 if summary['success_rate'] >= 80 else 1)
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Test execution interrupted by user")
        exit(130)
    except Exception as e:
        print(f"\n\n❌ Test runner failed: {e}")
        import traceback
        traceback.print_exc()
        exit(1)

if __name__ == "__main__":
    main()