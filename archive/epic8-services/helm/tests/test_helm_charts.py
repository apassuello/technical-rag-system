#!/usr/bin/env python3
"""
Helm Chart Testing Framework
Epic 8 Cloud-Native RAG Platform

This module provides comprehensive testing for Helm charts following
test-driven development principles for cloud-native deployment.

Test Categories:
1. Chart Structure and Syntax Validation
2. Template Rendering Validation
3. Values File Validation
4. Chart Dependency Testing
5. Multi-Environment Testing
6. Security and Best Practices Validation
"""

import os
import sys
import yaml
import json
import subprocess
import pytest
import tempfile
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass
import re

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

@dataclass
class HelmTestResult:
    """Result of a Helm chart test"""
    passed: bool
    message: str
    severity: str = "error"  # error, warning, info
    chart: Optional[str] = None
    details: Optional[Dict[str, Any]] = None

class HelmChartValidator:
    """
    Comprehensive Helm chart validation framework

    Validates charts against:
    - Chart.yaml structure and metadata
    - Template syntax and rendering
    - Values file structure and validation
    - Chart dependencies
    - Security best practices
    - Multi-environment compatibility
    """

    def __init__(self, chart_dir: Path):
        self.chart_dir = Path(chart_dir)
        self.results: List[HelmTestResult] = []

        # Epic 8 specific configuration
        self.epic8_services = {
            "api-gateway", "query-analyzer", "generator",
            "retriever", "cache", "analytics"
        }

        # Expected Helm chart structure
        self.required_chart_files = {
            "Chart.yaml", "values.yaml", "templates"
        }

        # Required Chart.yaml fields
        self.required_chart_metadata = {
            "apiVersion", "name", "description", "version", "appVersion"
        }

        # Environment configurations to test
        self.test_environments = ["development", "staging", "production"]

    def validate_all_charts(self) -> List[HelmTestResult]:
        """
        Run all validation tests on Helm charts

        Returns:
            List[HelmTestResult]: Comprehensive validation results
        """
        self.results.clear()

        if not self.chart_dir.exists():
            self.results.append(HelmTestResult(
                passed=False,
                message=f"Chart directory {self.chart_dir} does not exist",
                severity="error"
            ))
            return self.results

        # Find all Helm charts (directories with Chart.yaml)
        chart_dirs = []
        for item in self.chart_dir.iterdir():
            if item.is_dir() and (item / "Chart.yaml").exists():
                chart_dirs.append(item)

        if not chart_dirs:
            self.results.append(HelmTestResult(
                passed=False,
                message=f"No Helm charts found in {self.chart_dir}",
                severity="warning"
            ))
            return self.results

        # Run validation on each chart
        for chart_path in chart_dirs:
            self._validate_chart(chart_path)

        return self.results

    def _validate_chart(self, chart_path: Path) -> None:
        """Validate a single Helm chart"""
        chart_name = chart_path.name

        # 1. Chart Structure Validation
        self._validate_chart_structure(chart_path, chart_name)

        # 2. Chart.yaml Validation
        self._validate_chart_metadata(chart_path, chart_name)

        # 3. Values File Validation
        self._validate_values_files(chart_path, chart_name)

        # 4. Template Validation
        self._validate_templates(chart_path, chart_name)

        # 5. Chart Dependencies
        self._validate_dependencies(chart_path, chart_name)

        # 6. Multi-Environment Testing
        self._validate_multi_environment(chart_path, chart_name)

        # 7. Security Validation
        self._validate_chart_security(chart_path, chart_name)

    def _validate_chart_structure(self, chart_path: Path, chart_name: str) -> None:
        """Validate Helm chart directory structure"""

        # Check required files and directories
        missing_items = []
        for required_item in self.required_chart_files:
            item_path = chart_path / required_item
            if not item_path.exists():
                missing_items.append(required_item)

        if missing_items:
            self.results.append(HelmTestResult(
                passed=False,
                message=f"Chart {chart_name} missing required items: {missing_items}",
                severity="error",
                chart=chart_name,
                details={"missing_items": missing_items}
            ))
        else:
            self.results.append(HelmTestResult(
                passed=True,
                message=f"Chart {chart_name} has valid structure",
                severity="info",
                chart=chart_name
            ))

        # Check templates directory structure
        templates_dir = chart_path / "templates"
        if templates_dir.exists() and templates_dir.is_dir():
            template_files = list(templates_dir.glob("*.yaml")) + list(templates_dir.glob("*.yml"))

            if not template_files:
                self.results.append(HelmTestResult(
                    passed=False,
                    message=f"Chart {chart_name} templates directory is empty",
                    severity="warning",
                    chart=chart_name
                ))
            else:
                self.results.append(HelmTestResult(
                    passed=True,
                    message=f"Chart {chart_name} has {len(template_files)} template files",
                    severity="info",
                    chart=chart_name,
                    details={"template_count": len(template_files)}
                ))

    def _validate_chart_metadata(self, chart_path: Path, chart_name: str) -> None:
        """Validate Chart.yaml metadata"""

        chart_yaml_path = chart_path / "Chart.yaml"

        try:
            with open(chart_yaml_path, 'r') as f:
                chart_metadata = yaml.safe_load(f)

            if not isinstance(chart_metadata, dict):
                self.results.append(HelmTestResult(
                    passed=False,
                    message=f"Chart {chart_name} Chart.yaml is not a valid YAML object",
                    severity="error",
                    chart=chart_name
                ))
                return

            # Check required fields
            missing_fields = []
            for field in self.required_chart_metadata:
                if field not in chart_metadata:
                    missing_fields.append(field)

            if missing_fields:
                self.results.append(HelmTestResult(
                    passed=False,
                    message=f"Chart {chart_name} Chart.yaml missing required fields: {missing_fields}",
                    severity="error",
                    chart=chart_name,
                    details={"missing_fields": missing_fields}
                ))
            else:
                self.results.append(HelmTestResult(
                    passed=True,
                    message=f"Chart {chart_name} Chart.yaml has all required fields",
                    severity="info",
                    chart=chart_name
                ))

            # Validate API version
            api_version = chart_metadata.get("apiVersion")
            if api_version not in ["v1", "v2"]:
                self.results.append(HelmTestResult(
                    passed=False,
                    message=f"Chart {chart_name} has invalid apiVersion: {api_version}",
                    severity="error",
                    chart=chart_name,
                    details={"api_version": api_version}
                ))

            # Validate version format (should be semver)
            version = chart_metadata.get("version", "")
            if not re.match(r'^\d+\.\d+\.\d+', version):
                self.results.append(HelmTestResult(
                    passed=False,
                    message=f"Chart {chart_name} version should follow semver format: {version}",
                    severity="warning",
                    chart=chart_name,
                    details={"version": version}
                ))

            # Check Epic 8 specific metadata
            if any(service in chart_name for service in self.epic8_services):
                # Check if description mentions Epic 8
                description = chart_metadata.get("description", "")
                if "epic8" not in description.lower() and "rag" not in description.lower():
                    self.results.append(HelmTestResult(
                        passed=False,
                        message=f"Epic 8 chart {chart_name} description should mention Epic 8 or RAG",
                        severity="warning",
                        chart=chart_name,
                        details={"description": description}
                    ))

        except yaml.YAMLError as e:
            self.results.append(HelmTestResult(
                passed=False,
                message=f"Chart {chart_name} Chart.yaml has invalid YAML: {str(e)}",
                severity="error",
                chart=chart_name,
                details={"yaml_error": str(e)}
            ))
        except Exception as e:
            self.results.append(HelmTestResult(
                passed=False,
                message=f"Error reading Chart {chart_name} Chart.yaml: {str(e)}",
                severity="error",
                chart=chart_name,
                details={"error": str(e)}
            ))

    def _validate_values_files(self, chart_path: Path, chart_name: str) -> None:
        """Validate values.yaml and environment-specific values files"""

        # Validate main values.yaml
        values_yaml_path = chart_path / "values.yaml"
        if values_yaml_path.exists():
            self._validate_single_values_file(values_yaml_path, chart_name, "values.yaml")

        # Validate environment-specific values files
        for env in self.test_environments:
            env_values_path = chart_path / f"values-{env}.yaml"
            if env_values_path.exists():
                self._validate_single_values_file(env_values_path, chart_name, f"values-{env}.yaml")

    def _validate_single_values_file(self, values_path: Path, chart_name: str, file_name: str) -> None:
        """Validate a single values file"""

        try:
            with open(values_path, 'r') as f:
                values_data = yaml.safe_load(f)

            if values_data is None:
                self.results.append(HelmTestResult(
                    passed=True,
                    message=f"Chart {chart_name} {file_name} is empty (acceptable)",
                    severity="info",
                    chart=chart_name
                ))
                return

            if not isinstance(values_data, dict):
                self.results.append(HelmTestResult(
                    passed=False,
                    message=f"Chart {chart_name} {file_name} is not a valid YAML object",
                    severity="error",
                    chart=chart_name,
                    details={"file": file_name}
                ))
                return

            # Check Epic 8 specific values structure
            if any(service in chart_name for service in self.epic8_services):
                self._validate_epic8_values(values_data, chart_name, file_name)

            self.results.append(HelmTestResult(
                passed=True,
                message=f"Chart {chart_name} {file_name} is valid",
                severity="info",
                chart=chart_name,
                details={"file": file_name, "keys": list(values_data.keys()) if values_data else []}
            ))

        except yaml.YAMLError as e:
            self.results.append(HelmTestResult(
                passed=False,
                message=f"Chart {chart_name} {file_name} has invalid YAML: {str(e)}",
                severity="error",
                chart=chart_name,
                details={"file": file_name, "yaml_error": str(e)}
            ))
        except Exception as e:
            self.results.append(HelmTestResult(
                passed=False,
                message=f"Error reading Chart {chart_name} {file_name}: {str(e)}",
                severity="error",
                chart=chart_name,
                details={"file": file_name, "error": str(e)}
            ))

    def _validate_epic8_values(self, values_data: Dict, chart_name: str, file_name: str) -> None:
        """Validate Epic 8 specific values structure"""

        # Expected Epic 8 values sections
        expected_sections = ["image", "service", "resources"]

        for section in expected_sections:
            if section not in values_data:
                self.results.append(HelmTestResult(
                    passed=False,
                    message=f"Epic 8 chart {chart_name} {file_name} missing {section} section",
                    severity="warning",
                    chart=chart_name,
                    details={"file": file_name, "missing_section": section}
                ))

        # Validate image section
        image_config = values_data.get("image", {})
        if image_config:
            required_image_fields = ["repository", "tag"]
            for field in required_image_fields:
                if field not in image_config:
                    self.results.append(HelmTestResult(
                        passed=False,
                        message=f"Epic 8 chart {chart_name} {file_name} image section missing {field}",
                        severity="warning",
                        chart=chart_name,
                        details={"file": file_name, "missing_field": field}
                    ))

        # Validate resources section
        resources_config = values_data.get("resources", {})
        if resources_config:
            if "requests" not in resources_config and "limits" not in resources_config:
                self.results.append(HelmTestResult(
                    passed=False,
                    message=f"Epic 8 chart {chart_name} {file_name} resources section should have requests or limits",
                    severity="warning",
                    chart=chart_name,
                    details={"file": file_name}
                ))

    def _validate_templates(self, chart_path: Path, chart_name: str) -> None:
        """Validate Helm templates"""

        templates_dir = chart_path / "templates"
        if not templates_dir.exists():
            return

        template_files = list(templates_dir.glob("*.yaml")) + list(templates_dir.glob("*.yml"))

        for template_file in template_files:
            self._validate_single_template(template_file, chart_name)

    def _validate_single_template(self, template_path: Path, chart_name: str) -> None:
        """Validate a single Helm template"""

        try:
            with open(template_path, 'r') as f:
                template_content = f.read()

            # Check for basic Helm template syntax
            if "{{" not in template_content and "}}" not in template_content:
                self.results.append(HelmTestResult(
                    passed=False,
                    message=f"Chart {chart_name} template {template_path.name} has no Helm template syntax",
                    severity="warning",
                    chart=chart_name,
                    details={"template": template_path.name}
                ))
                return

            # Check for common template functions
            common_functions = [".Values", ".Release", ".Chart"]
            used_functions = [func for func in common_functions if func in template_content]

            if not used_functions:
                self.results.append(HelmTestResult(
                    passed=False,
                    message=f"Chart {chart_name} template {template_path.name} doesn't use common Helm functions",
                    severity="warning",
                    chart=chart_name,
                    details={"template": template_path.name}
                ))
            else:
                self.results.append(HelmTestResult(
                    passed=True,
                    message=f"Chart {chart_name} template {template_path.name} uses Helm functions: {used_functions}",
                    severity="info",
                    chart=chart_name,
                    details={"template": template_path.name, "functions": used_functions}
                ))

            # Check for Epic 8 specific template patterns
            if any(service in chart_name for service in self.epic8_services):
                self._validate_epic8_template_patterns(template_content, chart_name, template_path.name)

        except Exception as e:
            self.results.append(HelmTestResult(
                passed=False,
                message=f"Error reading Chart {chart_name} template {template_path.name}: {str(e)}",
                severity="error",
                chart=chart_name,
                details={"template": template_path.name, "error": str(e)}
            ))

    def _validate_epic8_template_patterns(self, template_content: str, chart_name: str, template_name: str) -> None:
        """Validate Epic 8 specific template patterns"""

        # Check for Epic 8 labeling patterns
        if "app.kubernetes.io" in template_content:
            self.results.append(HelmTestResult(
                passed=True,
                message=f"Chart {chart_name} template {template_name} uses Kubernetes standard labels",
                severity="info",
                chart=chart_name,
                details={"template": template_name}
            ))

        # Check for environment variable templating
        if "env:" in template_content and ".Values" in template_content:
            self.results.append(HelmTestResult(
                passed=True,
                message=f"Chart {chart_name} template {template_name} uses templated environment variables",
                severity="info",
                chart=chart_name,
                details={"template": template_name}
            ))

    def _validate_dependencies(self, chart_path: Path, chart_name: str) -> None:
        """Validate chart dependencies"""

        chart_yaml_path = chart_path / "Chart.yaml"

        try:
            with open(chart_yaml_path, 'r') as f:
                chart_metadata = yaml.safe_load(f)

            dependencies = chart_metadata.get("dependencies", [])

            if dependencies:
                self.results.append(HelmTestResult(
                    passed=True,
                    message=f"Chart {chart_name} has {len(dependencies)} dependencies",
                    severity="info",
                    chart=chart_name,
                    details={"dependency_count": len(dependencies)}
                ))

                # Validate each dependency
                for i, dep in enumerate(dependencies):
                    required_dep_fields = ["name", "version", "repository"]
                    missing_dep_fields = [field for field in required_dep_fields if field not in dep]

                    if missing_dep_fields:
                        self.results.append(HelmTestResult(
                            passed=False,
                            message=f"Chart {chart_name} dependency {i} missing fields: {missing_dep_fields}",
                            severity="error",
                            chart=chart_name,
                            details={"dependency_index": i, "missing_fields": missing_dep_fields}
                        ))
            else:
                self.results.append(HelmTestResult(
                    passed=True,
                    message=f"Chart {chart_name} has no dependencies",
                    severity="info",
                    chart=chart_name
                ))

        except Exception as e:
            self.results.append(HelmTestResult(
                passed=False,
                message=f"Error checking Chart {chart_name} dependencies: {str(e)}",
                severity="error",
                chart=chart_name,
                details={"error": str(e)}
            ))

    def _validate_multi_environment(self, chart_path: Path, chart_name: str) -> None:
        """Validate multi-environment support"""

        base_values_path = chart_path / "values.yaml"

        # Check if base values exist
        if not base_values_path.exists():
            self.results.append(HelmTestResult(
                passed=False,
                message=f"Chart {chart_name} missing base values.yaml file",
                severity="error",
                chart=chart_name
            ))
            return

        # Check for environment-specific values files
        env_files_found = []
        for env in self.test_environments:
            env_values_path = chart_path / f"values-{env}.yaml"
            if env_values_path.exists():
                env_files_found.append(env)

        if env_files_found:
            self.results.append(HelmTestResult(
                passed=True,
                message=f"Chart {chart_name} supports environments: {env_files_found}",
                severity="info",
                chart=chart_name,
                details={"environments": env_files_found}
            ))
        else:
            self.results.append(HelmTestResult(
                passed=True,
                message=f"Chart {chart_name} uses single values.yaml (environment-agnostic)",
                severity="info",
                chart=chart_name
            ))

    def _validate_chart_security(self, chart_path: Path, chart_name: str) -> None:
        """Validate chart security best practices"""

        # Check for security context in templates
        templates_dir = chart_path / "templates"
        if not templates_dir.exists():
            return

        template_files = list(templates_dir.glob("*.yaml")) + list(templates_dir.glob("*.yml"))
        security_contexts_found = 0

        for template_file in template_files:
            try:
                with open(template_file, 'r') as f:
                    content = f.read()

                if "securityContext" in content:
                    security_contexts_found += 1

            except Exception:
                continue

        if security_contexts_found > 0:
            self.results.append(HelmTestResult(
                passed=True,
                message=f"Chart {chart_name} has security contexts in {security_contexts_found} templates",
                severity="info",
                chart=chart_name,
                details={"security_contexts": security_contexts_found}
            ))
        else:
            self.results.append(HelmTestResult(
                passed=False,
                message=f"Chart {chart_name} has no security contexts defined",
                severity="warning",
                chart=chart_name
            ))

def run_helm_lint(chart_path: Path) -> List[HelmTestResult]:
    """
    Run helm lint validation on chart

    Returns:
        List[HelmTestResult]: Results from helm lint
    """
    results = []

    try:
        cmd = ["helm", "lint", str(chart_path)]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60
        )

        chart_name = chart_path.name

        if result.returncode == 0:
            results.append(HelmTestResult(
                passed=True,
                message=f"helm lint passed for chart {chart_name}",
                severity="info",
                chart=chart_name,
                details={"output": result.stdout}
            ))
        else:
            results.append(HelmTestResult(
                passed=False,
                message=f"helm lint failed for chart {chart_name}: {result.stderr}",
                severity="error",
                chart=chart_name,
                details={"error": result.stderr}
            ))

    except FileNotFoundError:
        results.append(HelmTestResult(
            passed=False,
            message="helm not found - install Helm for complete validation",
            severity="warning"
        ))
    except subprocess.TimeoutExpired:
        results.append(HelmTestResult(
            passed=False,
            message=f"helm lint timeout for chart {chart_path.name}",
            severity="error",
            chart=chart_path.name
        ))
    except Exception as e:
        results.append(HelmTestResult(
            passed=False,
            message=f"helm lint error for chart {chart_path.name}: {str(e)}",
            severity="error",
            chart=chart_path.name,
            details={"error": str(e)}
        ))

    return results

def run_helm_template_test(chart_path: Path, values_file: Optional[Path] = None) -> List[HelmTestResult]:
    """
    Run helm template rendering test

    Returns:
        List[HelmTestResult]: Results from helm template
    """
    results = []

    try:
        cmd = ["helm", "template", "test-release", str(chart_path)]

        if values_file and values_file.exists():
            cmd.extend(["-f", str(values_file)])

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60
        )

        chart_name = chart_path.name

        if result.returncode == 0:
            # Try to parse the rendered YAML
            try:
                rendered_docs = list(yaml.safe_load_all(result.stdout))
                valid_docs = [doc for doc in rendered_docs if doc is not None]

                results.append(HelmTestResult(
                    passed=True,
                    message=f"helm template rendered {len(valid_docs)} valid documents for chart {chart_name}",
                    severity="info",
                    chart=chart_name,
                    details={
                        "document_count": len(valid_docs),
                        "values_file": str(values_file) if values_file else "default"
                    }
                ))

            except yaml.YAMLError as e:
                results.append(HelmTestResult(
                    passed=False,
                    message=f"helm template generated invalid YAML for chart {chart_name}: {str(e)}",
                    severity="error",
                    chart=chart_name,
                    details={"yaml_error": str(e)}
                ))

        else:
            results.append(HelmTestResult(
                passed=False,
                message=f"helm template failed for chart {chart_name}: {result.stderr}",
                severity="error",
                chart=chart_name,
                details={"error": result.stderr}
            ))

    except FileNotFoundError:
        results.append(HelmTestResult(
            passed=False,
            message="helm not found - install Helm for template testing",
            severity="warning"
        ))
    except subprocess.TimeoutExpired:
        results.append(HelmTestResult(
            passed=False,
            message=f"helm template timeout for chart {chart_path.name}",
            severity="error",
            chart=chart_path.name
        ))
    except Exception as e:
        results.append(HelmTestResult(
            passed=False,
            message=f"helm template error for chart {chart_path.name}: {str(e)}",
            severity="error",
            chart=chart_path.name,
            details={"error": str(e)}
        ))

    return results

# Pytest test cases

class TestHelmChartValidation:
    """Test suite for Helm chart validation"""

    @pytest.fixture
    def chart_dir(self):
        """Fixture providing chart directory path"""
        return PROJECT_ROOT / "helm" / "charts"

    @pytest.fixture
    def validator(self, chart_dir):
        """Fixture providing configured validator"""
        return HelmChartValidator(chart_dir)

    def test_chart_structure_validation(self, validator):
        """Test Helm chart structure validation"""
        results = validator.validate_all_charts()

        # Check that we have some results
        assert len(results) > 0, "No validation results returned"

        # Check for structure errors
        structure_errors = [r for r in results if "structure" in r.message.lower() and not r.passed]
        assert len(structure_errors) == 0, f"Chart structure errors found: {[r.message for r in structure_errors]}"

    def test_chart_metadata_validation(self, validator):
        """Test Chart.yaml metadata validation"""
        results = validator.validate_all_charts()

        # Check for metadata errors
        metadata_errors = [r for r in results if "chart.yaml" in r.message.lower() and not r.passed and r.severity == "error"]
        assert len(metadata_errors) == 0, f"Chart metadata errors: {[r.message for r in metadata_errors]}"

    def test_values_file_validation(self, validator):
        """Test values.yaml validation"""
        results = validator.validate_all_charts()

        # Check for values file errors
        values_errors = [r for r in results if "values" in r.message.lower() and not r.passed and r.severity == "error"]
        assert len(values_errors) == 0, f"Values file errors: {[r.message for r in values_errors]}"

    def test_template_validation(self, validator):
        """Test Helm template validation"""
        results = validator.validate_all_charts()

        # Check for template errors
        template_errors = [r for r in results if "template" in r.message.lower() and not r.passed and r.severity == "error"]

        # Print template issues for review
        if template_errors:
            print(f"Template issues: {len(template_errors)}")
            for error in template_errors[:5]:
                print(f"  - {error.message}")

    def test_helm_lint_validation(self, chart_dir):
        """Test helm lint validation"""
        # Find all chart directories
        chart_dirs = [item for item in chart_dir.iterdir() if item.is_dir() and (item / "Chart.yaml").exists()]

        for chart_path in chart_dirs:
            results = run_helm_lint(chart_path)

            # Check for critical lint errors
            critical_errors = [r for r in results if not r.passed and r.severity == "error"]

            if critical_errors:
                print(f"Helm lint errors for {chart_path.name}: {len(critical_errors)}")
                for error in critical_errors:
                    print(f"  - {error.message}")

    def test_helm_template_rendering(self, chart_dir):
        """Test helm template rendering"""
        # Find all chart directories
        chart_dirs = [item for item in chart_dir.iterdir() if item.is_dir() and (item / "Chart.yaml").exists()]

        for chart_path in chart_dirs:
            # Test with default values
            results = run_helm_template_test(chart_path)

            # Check for template rendering errors
            template_errors = [r for r in results if not r.passed and r.severity == "error"]

            if template_errors:
                print(f"Template rendering errors for {chart_path.name}: {len(template_errors)}")
                for error in template_errors:
                    print(f"  - {error.message}")

            # Test with environment-specific values if they exist
            for env in ["development", "staging", "production"]:
                env_values = chart_path / f"values-{env}.yaml"
                if env_values.exists():
                    env_results = run_helm_template_test(chart_path, env_values)

                    env_errors = [r for r in env_results if not r.passed and r.severity == "error"]
                    if env_errors:
                        print(f"Template rendering errors for {chart_path.name} with {env} values: {len(env_errors)}")

    def test_multi_environment_support(self, validator):
        """Test multi-environment support"""
        results = validator.validate_all_charts()

        # Check environment support
        env_results = [r for r in results if "environment" in r.message.lower()]

        print(f"Environment support results: {len(env_results)}")
        for result in env_results:
            print(f"  - {result.message}")

    def test_security_validation(self, validator):
        """Test security best practices"""
        results = validator.validate_all_charts()

        # Check security warnings
        security_warnings = [r for r in results if "security" in r.message.lower() and not r.passed]

        print(f"Security warnings: {len(security_warnings)}")
        for warning in security_warnings:
            print(f"  - {warning.message}")

if __name__ == "__main__":
    """Command-line interface for Helm chart validation"""

    import argparse

    parser = argparse.ArgumentParser(description="Validate Helm charts for Epic 8")
    parser.add_argument(
        "--chart-dir",
        type=Path,
        default=PROJECT_ROOT / "helm" / "charts",
        help="Directory containing Helm charts"
    )
    parser.add_argument(
        "--output-format",
        choices=["text", "json"],
        default="text",
        help="Output format for results"
    )
    parser.add_argument(
        "--severity",
        choices=["error", "warning", "info"],
        default="warning",
        help="Minimum severity level to report"
    )
    parser.add_argument(
        "--run-helm-tests",
        action="store_true",
        help="Run helm lint and template tests (requires helm CLI)"
    )

    args = parser.parse_args()

    # Run validation
    validator = HelmChartValidator(args.chart_dir)
    results = validator.validate_all_charts()

    # Run helm tests if requested
    if args.run_helm_tests:
        if args.chart_dir.exists():
            chart_dirs = [item for item in args.chart_dir.iterdir() if item.is_dir() and (item / "Chart.yaml").exists()]

            for chart_path in chart_dirs:
                results.extend(run_helm_lint(chart_path))
                results.extend(run_helm_template_test(chart_path))

    # Filter by severity
    severity_levels = {"info": 0, "warning": 1, "error": 2}
    min_level = severity_levels[args.severity]
    filtered_results = [r for r in results if severity_levels[r.severity] >= min_level]

    # Output results
    if args.output_format == "json":
        import json
        output = {
            "total_results": len(filtered_results),
            "passed": len([r for r in filtered_results if r.passed]),
            "failed": len([r for r in filtered_results if not r.passed]),
            "charts": list(set([r.chart for r in filtered_results if r.chart])),
            "results": [
                {
                    "passed": r.passed,
                    "message": r.message,
                    "severity": r.severity,
                    "chart": r.chart,
                    "details": r.details
                }
                for r in filtered_results
            ]
        }
        print(json.dumps(output, indent=2))
    else:
        # Text output
        print(f"\n=== Epic 8 Helm Chart Validation Results ===")
        print(f"Total results: {len(filtered_results)}")
        print(f"Passed: {len([r for r in filtered_results if r.passed])}")
        print(f"Failed: {len([r for r in filtered_results if not r.passed])}")
        print(f"Charts tested: {list(set([r.chart for r in filtered_results if r.chart]))}")
        print(f"Minimum severity: {args.severity}")
        print()

        # Group results by chart
        charts = set([r.chart for r in filtered_results if r.chart])
        for chart in sorted(charts):
            chart_results = [r for r in filtered_results if r.chart == chart]
            print(f"\n--- Chart: {chart} ---")

            for result in chart_results:
                icon = "✅" if result.passed else "❌"
                severity_icon = {"info": "ℹ️", "warning": "⚠️", "error": "🚨"}[result.severity]

                print(f"{icon} {severity_icon} {result.message}")
                if result.details and args.severity == "info":
                    print(f"   Details: {result.details}")

        # Summary
        error_count = len([r for r in filtered_results if not r.passed and r.severity == "error"])
        warning_count = len([r for r in filtered_results if not r.passed and r.severity == "warning"])

        print(f"\n=== Summary ===")
        print(f"🚨 Errors: {error_count}")
        print(f"⚠️  Warnings: {warning_count}")

        if error_count == 0:
            print("✅ No critical errors found - charts are valid for deployment!")
        else:
            print("❌ Critical errors found - please fix before deployment")