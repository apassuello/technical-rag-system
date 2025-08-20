"""
Advanced Test Diagnostics Engine

Provides comprehensive issue analysis, root cause identification, and actionable
remediation suggestions for test failures across Epic 1, Epic 2, and legacy tests.
"""

import re
import json
import traceback
from dataclasses import dataclass, asdict
from typing import Dict, List, Any, Optional, Set, Tuple
from pathlib import Path
from enum import Enum
from collections import defaultdict, Counter


class ErrorCategory(Enum):
    """Categories of test errors for systematic analysis."""
    IMPORT_ERROR = "import_error"
    ASSERTION_FAILURE = "assertion_failure"
    CONFIGURATION_ERROR = "configuration_error"
    DEPENDENCY_ERROR = "dependency_error"
    TIMEOUT_ERROR = "timeout_error"
    ENVIRONMENT_ERROR = "environment_error"
    API_ERROR = "api_error"
    LOGIC_ERROR = "logic_error"
    RESOURCE_ERROR = "resource_error"
    UNKNOWN_ERROR = "unknown_error"


class ImpactLevel(Enum):
    """Impact levels for prioritizing issue resolution."""
    CRITICAL = "critical"
    MAJOR = "major"
    MINOR = "minor"
    COSMETIC = "cosmetic"


@dataclass
class ErrorPattern:
    """Defines an error pattern with its characteristics."""
    pattern: str
    category: ErrorCategory
    impact: ImpactLevel
    component: str
    description: str
    root_causes: List[str]
    suggested_fixes: List[str]
    related_patterns: List[str] = None


@dataclass
class IssueAnalysis:
    """Detailed analysis of a specific test issue."""
    test_name: str
    error_category: ErrorCategory
    impact_level: ImpactLevel
    component: str
    root_cause: str
    description: str
    error_message: str
    stack_trace: Optional[str]
    suggested_fixes: List[str]
    related_issues: List[str]
    file_location: Optional[str]
    line_number: Optional[int]
    frequency: int = 1
    epic: Optional[str] = None


@dataclass
class DiagnosticSummary:
    """Executive summary of all identified issues."""
    total_issues: int
    critical_issues: int
    major_issues: int
    minor_issues: int
    cosmetic_issues: int
    categories: Dict[str, int]
    components: Dict[str, int]
    priority_actions: List[str]
    trend_analysis: Dict[str, Any]


class TestDiagnosticsEngine:
    """Advanced diagnostics engine for comprehensive test analysis."""
    
    def __init__(self):
        """Initialize the diagnostics engine."""
        self.error_patterns = self._initialize_error_patterns()
        self.issue_history = defaultdict(int)
        self.component_mapping = self._initialize_component_mapping()
        
    def _initialize_error_patterns(self) -> List[ErrorPattern]:
        """Initialize comprehensive error pattern database."""
        return [
            # Epic 1 Specific Patterns
            ErrorPattern(
                pattern=r"ModuleNotFoundError.*epic1.*answer.*generator",
                category=ErrorCategory.IMPORT_ERROR,
                impact=ImpactLevel.CRITICAL,
                component="Epic1AnswerGenerator",
                description="Epic1AnswerGenerator module import failure",
                root_causes=[
                    "Module path not in PYTHONPATH",
                    "File renamed or moved",
                    "Circular import dependency"
                ],
                suggested_fixes=[
                    "Add 'src' directory to PYTHONPATH",
                    "Verify file exists at expected location",
                    "Check for circular import issues",
                    "Run: export PYTHONPATH=$PYTHONPATH:$(pwd)/src"
                ]
            ),
            
            ErrorPattern(
                pattern=r"AssertionError.*selected_provider.*ollama",
                category=ErrorCategory.LOGIC_ERROR,
                impact=ImpactLevel.MAJOR,
                component="AdaptiveRouter",
                description="Provider fallback logic not selecting Ollama correctly",
                root_causes=[
                    "API key authentication failure in test environment",
                    "Fallback chain configuration mismatch",
                    "Provider availability testing disabled in production mode"
                ],
                suggested_fixes=[
                    "Configure test environment with mock API keys",
                    "Adjust fallback chain to prioritize Ollama for budget constraints",
                    "Enable availability testing in test configuration",
                    "Mock external API calls in unit tests"
                ]
            ),
            
            ErrorPattern(
                pattern=r"AssertionError.*routing.*latency.*(\d+\.?\d*).*15",
                category=ErrorCategory.CONFIGURATION_ERROR,
                impact=ImpactLevel.MINOR,
                component="AdaptiveRouter",
                description="Routing performance test using wrong configuration",
                root_causes=[
                    "Test environment using per-request availability testing",
                    "Production caching not enabled in tests",
                    "Network latency in test environment"
                ],
                suggested_fixes=[
                    "Update test configuration to use production caching mode",
                    "Set enable_availability_testing=False in test config",
                    "Mock availability checks in performance tests",
                    "Use setup_availability_cache() in test setup"
                ]
            ),
            
            ErrorPattern(
                pattern=r"openai\.AuthenticationError.*Incorrect API key",
                category=ErrorCategory.API_ERROR,
                impact=ImpactLevel.MAJOR,
                component="OpenAI Adapter",
                description="OpenAI API authentication failure",
                root_causes=[
                    "Missing or invalid OPENAI_API_KEY environment variable",
                    "API key quota exceeded",
                    "Test environment not configured for API access"
                ],
                suggested_fixes=[
                    "Set valid OPENAI_API_KEY environment variable",
                    "Use mock adapter in test environment",
                    "Implement offline testing mode",
                    "Check API key quota and billing status"
                ]
            ),
            
            ErrorPattern(
                pattern=r"requests\.exceptions\.ConnectionError.*mistral",
                category=ErrorCategory.API_ERROR,
                impact=ImpactLevel.MAJOR,
                component="Mistral Adapter",
                description="Mistral API connection failure",
                root_causes=[
                    "Network connectivity issues",
                    "Mistral API service unavailable",
                    "Firewall blocking external API calls"
                ],
                suggested_fixes=[
                    "Check network connectivity",
                    "Use mock adapter for testing",
                    "Implement retry logic with exponential backoff",
                    "Configure test environment firewall rules"
                ]
            ),
            
            ErrorPattern(
                pattern=r"RuntimeError.*Failed to route query.*All fallback models failed",
                category=ErrorCategory.API_ERROR,
                impact=ImpactLevel.MAJOR,
                component="Epic1AnswerGenerator",
                description="All API models unavailable - authentication or connectivity issues",
                root_causes=[
                    "All configured API keys invalid or missing",
                    "All external services (OpenAI, Mistral, Ollama) unavailable",
                    "Network connectivity blocking all external API calls",
                    "Test environment not configured for API access"
                ],
                suggested_fixes=[
                    "Configure valid API keys: OPENAI_API_KEY, MISTRAL_API_KEY",
                    "Start Ollama service: ollama serve",
                    "Use mock adapters in test environment",
                    "Configure at least one working model for fallback",
                    "Check firewall and network connectivity",
                    "Enable test-only mode with offline models"
                ]
            ),
            
            # General Test Infrastructure Patterns
            ErrorPattern(
                pattern=r"ModuleNotFoundError.*src\..*",
                category=ErrorCategory.IMPORT_ERROR,
                impact=ImpactLevel.CRITICAL,
                component="Test Infrastructure",
                description="Source module import failure",
                root_causes=[
                    "PYTHONPATH not configured correctly",
                    "Source directory structure changed",
                    "Missing __init__.py files"
                ],
                suggested_fixes=[
                    "Add project root to PYTHONPATH",
                    "Verify all directories have __init__.py files",
                    "Use relative imports consistently",
                    "Check sys.path configuration in tests"
                ]
            ),
            
            ErrorPattern(
                pattern=r"FileNotFoundError.*config.*yaml",
                category=ErrorCategory.CONFIGURATION_ERROR,
                impact=ImpactLevel.MAJOR,
                component="Configuration System",
                description="Configuration file not found",
                root_causes=[
                    "Configuration file missing",
                    "Working directory incorrect",
                    "File path calculation error"
                ],
                suggested_fixes=[
                    "Ensure config/default.yaml exists",
                    "Run tests from project root directory",
                    "Use Path(__file__).parent for relative paths",
                    "Add configuration file validation"
                ]
            ),
            
            ErrorPattern(
                pattern=r"AssertionError.*confidence.*score",
                category=ErrorCategory.LOGIC_ERROR,
                impact=ImpactLevel.MINOR,
                component="Answer Quality Assessment",
                description="Confidence score calculation not meeting expectations",
                root_causes=[
                    "Model output format changed",
                    "Confidence calculation algorithm updated",
                    "Test expectations too strict"
                ],
                suggested_fixes=[
                    "Review confidence calculation logic",
                    "Update test expectations to realistic ranges",
                    "Add confidence score debugging output",
                    "Verify model response parsing"
                ]
            ),
            
            ErrorPattern(
                pattern=r"TimeoutError|timeout.*expired",
                category=ErrorCategory.TIMEOUT_ERROR,
                impact=ImpactLevel.MAJOR,
                component="Test Execution",
                description="Test execution timeout",
                root_causes=[
                    "Slow external API calls",
                    "Inefficient test logic",
                    "Resource contention"
                ],
                suggested_fixes=[
                    "Increase test timeout limits",
                    "Mock slow external dependencies",
                    "Optimize test performance",
                    "Use parallel test execution"
                ]
            ),
            
            # Cost Tracking Patterns
            ErrorPattern(
                pattern=r"AssertionError.*cost.*budget",
                category=ErrorCategory.LOGIC_ERROR,
                impact=ImpactLevel.MINOR,
                component="CostTracker",
                description="Cost budget validation failure",
                root_causes=[
                    "Cost calculation precision issues",
                    "Budget enforcement logic mismatch",
                    "Test environment cost model different from production"
                ],
                suggested_fixes=[
                    "Verify cost calculation precision ($0.001)",
                    "Align test budget limits with production",
                    "Add cost debugging output to tests",
                    "Mock cost tracking in unit tests"
                ]
            )
        ]
    
    def _initialize_component_mapping(self) -> Dict[str, str]:
        """Map test patterns to system components."""
        return {
            "epic1_answer_generator": "Epic1AnswerGenerator",
            "adaptive_router": "AdaptiveRouter", 
            "cost_tracker": "CostTracker",
            "routing_strategies": "RoutingStrategies",
            "openai_adapter": "OpenAI Adapter",
            "mistral_adapter": "Mistral Adapter",
            "ollama_adapter": "Ollama Adapter",
            "document_processor": "Document Processor",
            "embedder": "Embedder",
            "retriever": "Retriever",
            "query_processor": "Query Processor"
        }
    
    def analyze_test_output(self, test_output: str, error_output: str, 
                          test_results: List[Any]) -> Dict[str, Any]:
        """Analyze test output and generate comprehensive diagnostics."""
        
        # Parse individual test failures
        issues = []
        for test_result in test_results:
            if test_result.status in ['failed', 'error']:
                issue = self._analyze_test_failure(test_result, test_output, error_output)
                if issue:
                    issues.append(issue)
        
        # Parse global errors from output
        global_issues = self._parse_global_errors(test_output, error_output)
        issues.extend(global_issues)
        
        # Analyze patterns and relationships
        pattern_analysis = self._analyze_error_patterns(issues)
        
        # Generate summary
        summary = self._generate_diagnostic_summary(issues)
        
        # Create enhanced diagnostic report
        diagnostic_report = {
            "schema_version": "2.0",
            "generated_at": None,  # Set by caller
            "diagnostic_summary": asdict(summary),
            "issues": [asdict(issue) for issue in issues],
            "pattern_analysis": pattern_analysis,
            "remediation_plan": self._generate_remediation_plan(issues),
            "trend_analysis": self._analyze_trends(issues),
            "component_health": self._assess_component_health(issues)
        }
        
        return diagnostic_report
    
    def _analyze_test_failure(self, test_result, test_output: str, 
                            error_output: str) -> Optional[IssueAnalysis]:
        """Analyze a single test failure in detail."""
        
        if not test_result.message and not test_result.traceback:
            return None
        
        # Combine all error information
        full_error = f"{test_result.message}\n{test_result.traceback or ''}"
        
        # Match against known error patterns
        matched_pattern = None
        for pattern in self.error_patterns:
            if re.search(pattern.pattern, full_error, re.IGNORECASE | re.MULTILINE):
                matched_pattern = pattern
                break
        
        # Extract file location and line number
        file_location, line_number = self._extract_location_from_traceback(
            test_result.traceback or ""
        )
        
        # Determine component from test name
        component = self._determine_component(test_result.name)
        
        # Determine epic from test path
        epic = self._determine_epic(test_result.name)
        
        if matched_pattern:
            issue = IssueAnalysis(
                test_name=test_result.name,
                error_category=matched_pattern.category,
                impact_level=matched_pattern.impact,
                component=matched_pattern.component,
                root_cause=matched_pattern.description,
                description=matched_pattern.description,
                error_message=test_result.message or "",
                stack_trace=test_result.traceback,
                suggested_fixes=matched_pattern.suggested_fixes,
                related_issues=[],
                file_location=file_location,
                line_number=line_number,
                epic=epic
            )
        else:
            # Create generic analysis for unrecognized patterns
            issue = IssueAnalysis(
                test_name=test_result.name,
                error_category=self._categorize_generic_error(full_error),
                impact_level=ImpactLevel.MINOR,
                component=component,
                root_cause="Unrecognized error pattern",
                description=f"Test failure: {test_result.message or 'Unknown error'}",
                error_message=test_result.message or "",
                stack_trace=test_result.traceback,
                suggested_fixes=self._generate_generic_fixes(full_error),
                related_issues=[],
                file_location=file_location,
                line_number=line_number,
                epic=epic
            )
        
        # Update frequency tracking
        error_key = f"{issue.component}:{issue.error_category.value}"
        self.issue_history[error_key] += 1
        issue.frequency = self.issue_history[error_key]
        
        return issue
    
    def _parse_global_errors(self, test_output: str, error_output: str) -> List[IssueAnalysis]:
        """Parse global errors that affect multiple tests."""
        global_issues = []
        
        combined_output = f"{test_output}\n{error_output}"
        
        # Check for import errors affecting multiple tests
        import_errors = re.findall(
            r"ImportError|ModuleNotFoundError.*?(?=\n\n|\Z)", 
            combined_output, 
            re.DOTALL
        )
        
        for error in import_errors:
            # Skip if already captured in individual test results
            if "test_" in error:
                continue
                
            issue = IssueAnalysis(
                test_name="Global Import Error",
                error_category=ErrorCategory.IMPORT_ERROR,
                impact_level=ImpactLevel.CRITICAL,
                component="Test Infrastructure",
                root_cause="Global module import failure",
                description="Import error affecting multiple tests",
                error_message=error,
                stack_trace=None,
                suggested_fixes=[
                    "Check PYTHONPATH configuration",
                    "Verify all required modules are installed",
                    "Check for missing __init__.py files"
                ],
                related_issues=[],
                file_location=None,
                line_number=None
            )
            global_issues.append(issue)
        
        return global_issues
    
    def _extract_location_from_traceback(self, traceback_str: str) -> Tuple[Optional[str], Optional[int]]:
        """Extract file location and line number from traceback."""
        if not traceback_str:
            return None, None
        
        # Look for file and line patterns
        file_pattern = r'File "([^"]+)", line (\d+)'
        matches = re.findall(file_pattern, traceback_str)
        
        if matches:
            # Return the last (most specific) location
            file_path, line_num = matches[-1]
            return file_path, int(line_num)
        
        return None, None
    
    def _determine_component(self, test_name: str) -> str:
        """Determine component from test name."""
        test_name_lower = test_name.lower()
        
        for key, component in self.component_mapping.items():
            if key in test_name_lower:
                return component
        
        # Extract from test file path if possible
        if "::" in test_name:
            file_part = test_name.split("::")[0]
            for key, component in self.component_mapping.items():
                if key in file_part.lower():
                    return component
        
        return "Unknown Component"
    
    def _determine_epic(self, test_name: str) -> Optional[str]:
        """Determine epic from test name or path."""
        if "epic1" in test_name.lower():
            return "epic1"
        elif "epic2" in test_name.lower():
            return "epic2"
        return None
    
    def _categorize_generic_error(self, error_text: str) -> ErrorCategory:
        """Categorize unrecognized errors based on content."""
        error_lower = error_text.lower()
        
        if "assertion" in error_lower:
            return ErrorCategory.ASSERTION_FAILURE
        elif "import" in error_lower or "module" in error_lower:
            return ErrorCategory.IMPORT_ERROR
        elif "timeout" in error_lower:
            return ErrorCategory.TIMEOUT_ERROR
        elif "connection" in error_lower or "network" in error_lower:
            return ErrorCategory.API_ERROR
        elif "config" in error_lower:
            return ErrorCategory.CONFIGURATION_ERROR
        else:
            return ErrorCategory.UNKNOWN_ERROR
    
    def _generate_generic_fixes(self, error_text: str) -> List[str]:
        """Generate generic fix suggestions for unrecognized errors."""
        fixes = ["Review error message and stack trace"]
        
        error_lower = error_text.lower()
        
        if "assertion" in error_lower:
            fixes.extend([
                "Check test expectations against actual behavior",
                "Verify test data and setup",
                "Review recent code changes"
            ])
        elif "import" in error_lower:
            fixes.extend([
                "Check module installation",
                "Verify import paths",
                "Check PYTHONPATH configuration"
            ])
        elif "timeout" in error_lower:
            fixes.extend([
                "Increase timeout limits",
                "Optimize test performance",
                "Check for blocking operations"
            ])
        
        return fixes
    
    def _analyze_error_patterns(self, issues: List[IssueAnalysis]) -> Dict[str, Any]:
        """Analyze patterns across all issues."""
        
        # Category distribution
        category_counts = Counter(issue.error_category.value for issue in issues)
        
        # Component distribution
        component_counts = Counter(issue.component for issue in issues)
        
        # Impact distribution
        impact_counts = Counter(issue.impact_level.value for issue in issues)
        
        # Epic distribution
        epic_counts = Counter(issue.epic for issue in issues if issue.epic)
        
        # Find related issues
        related_groups = self._find_related_issues(issues)
        
        return {
            "category_distribution": dict(category_counts),
            "component_distribution": dict(component_counts),
            "impact_distribution": dict(impact_counts),
            "epic_distribution": dict(epic_counts),
            "related_issue_groups": related_groups,
            "most_frequent_errors": self._get_most_frequent_errors(issues),
            "error_clusters": self._cluster_similar_errors(issues)
        }
    
    def _generate_diagnostic_summary(self, issues: List[IssueAnalysis]) -> DiagnosticSummary:
        """Generate executive summary of all issues."""
        
        total = len(issues)
        critical = sum(1 for i in issues if i.impact_level == ImpactLevel.CRITICAL)
        major = sum(1 for i in issues if i.impact_level == ImpactLevel.MAJOR)
        minor = sum(1 for i in issues if i.impact_level == ImpactLevel.MINOR)
        cosmetic = sum(1 for i in issues if i.impact_level == ImpactLevel.COSMETIC)
        
        categories = Counter(issue.error_category.value for issue in issues)
        components = Counter(issue.component for issue in issues)
        
        # Generate priority actions
        priority_actions = []
        if critical > 0:
            priority_actions.append(f"URGENT: Resolve {critical} critical issues blocking test execution")
        if major > 0:
            priority_actions.append(f"HIGH: Address {major} major issues affecting core functionality")
        
        # Add specific actions based on most common issues
        most_common_category = categories.most_common(1)
        if most_common_category:
            category, count = most_common_category[0]
            priority_actions.append(f"Focus on {category} issues ({count} occurrences)")
        
        most_common_component = components.most_common(1)
        if most_common_component:
            component, count = most_common_component[0]
            priority_actions.append(f"Review {component} component ({count} issues)")
        
        return DiagnosticSummary(
            total_issues=total,
            critical_issues=critical,
            major_issues=major,
            minor_issues=minor,
            cosmetic_issues=cosmetic,
            categories=dict(categories),
            components=dict(components),
            priority_actions=priority_actions,
            trend_analysis={}  # Populated by _analyze_trends
        )
    
    def _generate_remediation_plan(self, issues: List[IssueAnalysis]) -> Dict[str, Any]:
        """Generate prioritized remediation plan."""
        
        # Group by priority
        critical_fixes = []
        major_fixes = []
        minor_fixes = []
        
        for issue in issues:
            fix_item = {
                "issue": issue.test_name,
                "component": issue.component,
                "description": issue.description,
                "fixes": issue.suggested_fixes,
                "estimated_effort": self._estimate_effort(issue)
            }
            
            if issue.impact_level == ImpactLevel.CRITICAL:
                critical_fixes.append(fix_item)
            elif issue.impact_level == ImpactLevel.MAJOR:
                major_fixes.append(fix_item)
            else:
                minor_fixes.append(fix_item)
        
        return {
            "immediate_actions": critical_fixes,
            "high_priority_actions": major_fixes,
            "low_priority_actions": minor_fixes,
            "estimated_total_effort": self._calculate_total_effort(issues),
            "recommended_sequence": self._recommend_fix_sequence(issues)
        }
    
    def _analyze_trends(self, issues: List[IssueAnalysis]) -> Dict[str, Any]:
        """Analyze trends in issue frequency and patterns."""
        
        # For now, basic trend analysis
        # In a real implementation, this would track issues over time
        recurring_issues = [
            issue for issue in issues 
            if issue.frequency > 1
        ]
        
        return {
            "recurring_issues": len(recurring_issues),
            "most_frequent_issue_types": dict(Counter(
                issue.error_category.value for issue in recurring_issues
            )),
            "stability_indicators": {
                "new_issue_rate": len([i for i in issues if i.frequency == 1]),
                "recurring_issue_rate": len(recurring_issues),
                "critical_issue_trend": "stable"  # Would be calculated from historical data
            }
        }
    
    def _assess_component_health(self, issues: List[IssueAnalysis]) -> Dict[str, Any]:
        """Assess health status of each component."""
        
        component_health = {}
        component_issues = defaultdict(list)
        
        for issue in issues:
            component_issues[issue.component].append(issue)
        
        for component, comp_issues in component_issues.items():
            critical_count = sum(1 for i in comp_issues if i.impact_level == ImpactLevel.CRITICAL)
            major_count = sum(1 for i in comp_issues if i.impact_level == ImpactLevel.MAJOR)
            
            if critical_count > 0:
                health_status = "critical"
            elif major_count > 2:
                health_status = "degraded"
            elif major_count > 0:
                health_status = "warning"
            else:
                health_status = "healthy"
            
            component_health[component] = {
                "status": health_status,
                "issue_count": len(comp_issues),
                "critical_issues": critical_count,
                "major_issues": major_count,
                "confidence_score": self._calculate_confidence_score(comp_issues)
            }
        
        return component_health
    
    def _find_related_issues(self, issues: List[IssueAnalysis]) -> List[List[str]]:
        """Find groups of related issues."""
        related_groups = []
        
        # Group by component
        component_groups = defaultdict(list)
        for issue in issues:
            component_groups[issue.component].append(issue.test_name)
        
        # Only include components with multiple issues
        for component, test_names in component_groups.items():
            if len(test_names) > 1:
                related_groups.append(test_names)
        
        return related_groups
    
    def _get_most_frequent_errors(self, issues: List[IssueAnalysis]) -> List[Dict[str, Any]]:
        """Get most frequently occurring errors."""
        frequent_errors = []
        
        for issue in issues:
            if issue.frequency > 1:
                frequent_errors.append({
                    "error_type": issue.error_category.value,
                    "component": issue.component,
                    "frequency": issue.frequency,
                    "description": issue.description
                })
        
        return sorted(frequent_errors, key=lambda x: x["frequency"], reverse=True)
    
    def _cluster_similar_errors(self, issues: List[IssueAnalysis]) -> List[Dict[str, Any]]:
        """Cluster similar errors together."""
        clusters = []
        
        # Simple clustering by error category and component
        cluster_map = defaultdict(list)
        
        for issue in issues:
            cluster_key = f"{issue.error_category.value}:{issue.component}"
            cluster_map[cluster_key].append(issue)
        
        for cluster_key, cluster_issues in cluster_map.items():
            if len(cluster_issues) > 1:
                category, component = cluster_key.split(":", 1)
                clusters.append({
                    "cluster_id": cluster_key,
                    "error_category": category,
                    "component": component,
                    "issue_count": len(cluster_issues),
                    "test_names": [issue.test_name for issue in cluster_issues],
                    "common_fixes": self._find_common_fixes(cluster_issues)
                })
        
        return clusters
    
    def _find_common_fixes(self, issues: List[IssueAnalysis]) -> List[str]:
        """Find common fix suggestions across similar issues."""
        all_fixes = []
        for issue in issues:
            all_fixes.extend(issue.suggested_fixes)
        
        # Return most common fixes
        fix_counts = Counter(all_fixes)
        return [fix for fix, count in fix_counts.most_common(3)]
    
    def _estimate_effort(self, issue: IssueAnalysis) -> str:
        """Estimate effort required to fix an issue."""
        if issue.impact_level == ImpactLevel.CRITICAL:
            if issue.error_category == ErrorCategory.IMPORT_ERROR:
                return "15-30 minutes"
            else:
                return "1-2 hours"
        elif issue.impact_level == ImpactLevel.MAJOR:
            return "30-60 minutes"
        else:
            return "10-30 minutes"
    
    def _calculate_total_effort(self, issues: List[IssueAnalysis]) -> str:
        """Calculate total estimated effort for all fixes."""
        total_minutes = 0
        
        for issue in issues:
            if issue.impact_level == ImpactLevel.CRITICAL:
                total_minutes += 90  # Average of 1-2 hours
            elif issue.impact_level == ImpactLevel.MAJOR:
                total_minutes += 45  # Average of 30-60 minutes
            else:
                total_minutes += 20  # Average of 10-30 minutes
        
        hours = total_minutes // 60
        minutes = total_minutes % 60
        
        if hours > 0:
            return f"{hours}h {minutes}m"
        else:
            return f"{minutes}m"
    
    def _recommend_fix_sequence(self, issues: List[IssueAnalysis]) -> List[str]:
        """Recommend sequence for fixing issues."""
        sequence = []
        
        # First: Critical import errors (block everything)
        critical_imports = [
            issue for issue in issues 
            if issue.impact_level == ImpactLevel.CRITICAL 
            and issue.error_category == ErrorCategory.IMPORT_ERROR
        ]
        for issue in critical_imports:
            sequence.append(f"Fix critical import: {issue.test_name}")
        
        # Second: Other critical issues
        other_critical = [
            issue for issue in issues 
            if issue.impact_level == ImpactLevel.CRITICAL 
            and issue.error_category != ErrorCategory.IMPORT_ERROR
        ]
        for issue in other_critical:
            sequence.append(f"Fix critical issue: {issue.test_name}")
        
        # Third: Major issues by component (fix component-wide issues together)
        major_by_component = defaultdict(list)
        for issue in issues:
            if issue.impact_level == ImpactLevel.MAJOR:
                major_by_component[issue.component].append(issue)
        
        for component, comp_issues in major_by_component.items():
            sequence.append(f"Fix all {component} issues ({len(comp_issues)} issues)")
        
        return sequence
    
    def _calculate_confidence_score(self, issues: List[IssueAnalysis]) -> float:
        """Calculate confidence score for component health."""
        if not issues:
            return 1.0
        
        total_weight = 0
        for issue in issues:
            if issue.impact_level == ImpactLevel.CRITICAL:
                total_weight += 4
            elif issue.impact_level == ImpactLevel.MAJOR:
                total_weight += 2
            else:
                total_weight += 1
        
        # Normalize to 0-1 scale (arbitrary scaling)
        max_possible = len(issues) * 4
        confidence = max(0, 1 - (total_weight / max_possible))
        
        return round(confidence, 2)