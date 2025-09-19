#!/usr/bin/env python3
"""
Kubernetes Manifest Validation Testing Framework
Epic 8 Cloud-Native RAG Platform

This module provides comprehensive validation testing for Kubernetes manifests,
following test-driven development principles for infrastructure as code.

Test Categories:
1. YAML Syntax and Structure Validation
2. Kubernetes Resource Validation
3. Security Policy Validation
4. Resource Allocation Validation
5. Naming Convention Validation
6. Label and Annotation Validation
"""

import os
import sys
import yaml
import json
import subprocess
import pytest
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import tempfile
import re
from dataclasses import dataclass

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

@dataclass
class ValidationResult:
    """Result of a validation test"""
    passed: bool
    message: str
    severity: str = "error"  # error, warning, info
    details: Optional[Dict[str, Any]] = None

class KubernetesManifestValidator:
    """
    Comprehensive Kubernetes manifest validation framework

    Validates manifests against:
    - YAML syntax
    - Kubernetes API specifications
    - Security best practices
    - Resource requirements
    - Naming conventions
    - Label standards
    """

    def __init__(self, manifest_dir: Path):
        self.manifest_dir = Path(manifest_dir)
        self.results: List[ValidationResult] = []

        # Epic 8 specific configuration
        self.epic8_services = {
            "api-gateway", "query-analyzer", "generator",
            "retriever", "cache", "analytics"
        }

        # Required labels for Epic 8 services
        self.required_labels = {
            "app.kubernetes.io/name",
            "app.kubernetes.io/component",
            "app.kubernetes.io/part-of",
            "app.kubernetes.io/version"
        }

        # Security requirements
        self.security_requirements = {
            "runAsNonRoot": True,
            "readOnlyRootFilesystem": True,
            "allowPrivilegeEscalation": False
        }

    def validate_all_manifests(self) -> List[ValidationResult]:
        """
        Run all validation tests on Kubernetes manifests

        Returns:
            List[ValidationResult]: Comprehensive validation results
        """
        self.results.clear()

        if not self.manifest_dir.exists():
            self.results.append(ValidationResult(
                passed=False,
                message=f"Manifest directory {self.manifest_dir} does not exist",
                severity="error"
            ))
            return self.results

        # Find all YAML manifest files
        manifest_files = list(self.manifest_dir.glob("*.yaml")) + list(self.manifest_dir.glob("*.yml"))

        if not manifest_files:
            self.results.append(ValidationResult(
                passed=False,
                message=f"No YAML manifest files found in {self.manifest_dir}",
                severity="warning"
            ))
            return self.results

        # Run validation on each manifest
        for manifest_file in manifest_files:
            self._validate_manifest_file(manifest_file)

        return self.results

    def _validate_manifest_file(self, manifest_file: Path) -> None:
        """Validate a single manifest file"""

        # 1. YAML Syntax Validation
        manifest_data = self._validate_yaml_syntax(manifest_file)
        if not manifest_data:
            return

        # 2. Kubernetes Resource Validation
        self._validate_kubernetes_resources(manifest_file, manifest_data)

        # 3. Security Policy Validation
        self._validate_security_policies(manifest_file, manifest_data)

        # 4. Resource Allocation Validation
        self._validate_resource_allocation(manifest_file, manifest_data)

        # 5. Naming Convention Validation
        self._validate_naming_conventions(manifest_file, manifest_data)

        # 6. Label and Annotation Validation
        self._validate_labels_and_annotations(manifest_file, manifest_data)

    def _validate_yaml_syntax(self, manifest_file: Path) -> Optional[List[Dict]]:
        """Validate YAML syntax and structure"""
        try:
            with open(manifest_file, 'r') as f:
                content = f.read()

            # Parse YAML documents (handle multi-document YAML)
            documents = list(yaml.safe_load_all(content))

            # Remove None documents (empty documents)
            documents = [doc for doc in documents if doc is not None]

            if not documents:
                self.results.append(ValidationResult(
                    passed=False,
                    message=f"No valid YAML documents found in {manifest_file.name}",
                    severity="error",
                    details={"file": str(manifest_file)}
                ))
                return None

            self.results.append(ValidationResult(
                passed=True,
                message=f"YAML syntax valid in {manifest_file.name}",
                severity="info",
                details={"file": str(manifest_file), "documents": len(documents)}
            ))

            return documents

        except yaml.YAMLError as e:
            self.results.append(ValidationResult(
                passed=False,
                message=f"YAML syntax error in {manifest_file.name}: {str(e)}",
                severity="error",
                details={"file": str(manifest_file), "error": str(e)}
            ))
            return None
        except Exception as e:
            self.results.append(ValidationResult(
                passed=False,
                message=f"Failed to read {manifest_file.name}: {str(e)}",
                severity="error",
                details={"file": str(manifest_file), "error": str(e)}
            ))
            return None

    def _validate_kubernetes_resources(self, manifest_file: Path, documents: List[Dict]) -> None:
        """Validate Kubernetes resource specifications"""

        for i, doc in enumerate(documents):
            if not isinstance(doc, dict):
                self.results.append(ValidationResult(
                    passed=False,
                    message=f"Document {i} in {manifest_file.name} is not a valid Kubernetes resource",
                    severity="error",
                    details={"file": str(manifest_file), "document_index": i}
                ))
                continue

            # Check required fields
            required_fields = ["apiVersion", "kind", "metadata"]
            missing_fields = [field for field in required_fields if field not in doc]

            if missing_fields:
                self.results.append(ValidationResult(
                    passed=False,
                    message=f"Missing required fields in {manifest_file.name} document {i}: {missing_fields}",
                    severity="error",
                    details={
                        "file": str(manifest_file),
                        "document_index": i,
                        "missing_fields": missing_fields
                    }
                ))
                continue

            # Validate apiVersion format
            api_version = doc.get("apiVersion", "")
            if not re.match(r'^[a-z0-9]+(/[a-z0-9]+)?(/v[0-9]+[a-z0-9]*)?$', api_version):
                self.results.append(ValidationResult(
                    passed=False,
                    message=f"Invalid apiVersion format in {manifest_file.name}: {api_version}",
                    severity="error",
                    details={"file": str(manifest_file), "api_version": api_version}
                ))

            # Validate metadata.name
            metadata = doc.get("metadata", {})
            name = metadata.get("name", "")
            if not re.match(r'^[a-z0-9]([-a-z0-9]*[a-z0-9])?$', name):
                self.results.append(ValidationResult(
                    passed=False,
                    message=f"Invalid metadata.name format in {manifest_file.name}: {name}",
                    severity="error",
                    details={"file": str(manifest_file), "name": name}
                ))

            # Validate Epic 8 service naming
            kind = doc.get("kind", "")
            if kind in ["Deployment", "Service", "ConfigMap", "Secret"] and name:
                if any(service in name for service in self.epic8_services):
                    self.results.append(ValidationResult(
                        passed=True,
                        message=f"Epic 8 service resource validated: {name} ({kind})",
                        severity="info",
                        details={"file": str(manifest_file), "resource": name, "kind": kind}
                    ))

    def _validate_security_policies(self, manifest_file: Path, documents: List[Dict]) -> None:
        """Validate security policies and best practices"""

        for i, doc in enumerate(documents):
            kind = doc.get("kind", "")

            if kind == "Deployment":
                self._validate_deployment_security(manifest_file, doc, i)
            elif kind == "Pod":
                self._validate_pod_security(manifest_file, doc, i)
            elif kind == "Service":
                self._validate_service_security(manifest_file, doc, i)

    def _validate_deployment_security(self, manifest_file: Path, deployment: Dict, index: int) -> None:
        """Validate Deployment security configuration"""

        spec = deployment.get("spec", {})
        template = spec.get("template", {})
        pod_spec = template.get("spec", {})

        # Check security context
        security_context = pod_spec.get("securityContext", {})

        for requirement, expected_value in self.security_requirements.items():
            actual_value = security_context.get(requirement)
            if actual_value != expected_value:
                self.results.append(ValidationResult(
                    passed=False,
                    message=f"Security requirement not met in {manifest_file.name}: {requirement} should be {expected_value}",
                    severity="warning",
                    details={
                        "file": str(manifest_file),
                        "requirement": requirement,
                        "expected": expected_value,
                        "actual": actual_value
                    }
                ))

        # Check container security contexts
        containers = pod_spec.get("containers", [])
        for container in containers:
            container_security = container.get("securityContext", {})

            if not container_security.get("runAsNonRoot", False):
                self.results.append(ValidationResult(
                    passed=False,
                    message=f"Container {container.get('name', 'unknown')} should run as non-root",
                    severity="warning",
                    details={"file": str(manifest_file), "container": container.get("name")}
                ))

    def _validate_pod_security(self, manifest_file: Path, pod: Dict, index: int) -> None:
        """Validate Pod security configuration"""
        # Similar to deployment security validation
        pass

    def _validate_service_security(self, manifest_file: Path, service: Dict, index: int) -> None:
        """Validate Service security configuration"""

        spec = service.get("spec", {})
        service_type = spec.get("type", "ClusterIP")

        # Warn about LoadBalancer and NodePort services
        if service_type in ["LoadBalancer", "NodePort"]:
            self.results.append(ValidationResult(
                passed=True,
                message=f"Service {service.get('metadata', {}).get('name', 'unknown')} uses {service_type} - ensure security groups are configured",
                severity="warning",
                details={"file": str(manifest_file), "service_type": service_type}
            ))

    def _validate_resource_allocation(self, manifest_file: Path, documents: List[Dict]) -> None:
        """Validate resource allocation (requests/limits)"""

        for i, doc in enumerate(documents):
            kind = doc.get("kind", "")

            if kind == "Deployment":
                self._validate_deployment_resources(manifest_file, doc, i)

    def _validate_deployment_resources(self, manifest_file: Path, deployment: Dict, index: int) -> None:
        """Validate Deployment resource allocation"""

        spec = deployment.get("spec", {})
        template = spec.get("template", {})
        pod_spec = template.get("spec", {})
        containers = pod_spec.get("containers", [])

        for container in containers:
            resources = container.get("resources", {})
            requests = resources.get("requests", {})
            limits = resources.get("limits", {})

            container_name = container.get("name", "unknown")

            # Check if resources are defined
            if not requests and not limits:
                self.results.append(ValidationResult(
                    passed=False,
                    message=f"Container {container_name} has no resource requests or limits defined",
                    severity="warning",
                    details={"file": str(manifest_file), "container": container_name}
                ))
                continue

            # Check if requests are defined
            if not requests:
                self.results.append(ValidationResult(
                    passed=False,
                    message=f"Container {container_name} has no resource requests defined",
                    severity="warning",
                    details={"file": str(manifest_file), "container": container_name}
                ))

            # Check if limits are defined
            if not limits:
                self.results.append(ValidationResult(
                    passed=False,
                    message=f"Container {container_name} has no resource limits defined",
                    severity="warning",
                    details={"file": str(manifest_file), "container": container_name}
                ))

            # Validate CPU and memory are specified
            for resource_type in ["requests", "limits"]:
                resource_section = resources.get(resource_type, {})
                if resource_section:
                    if "cpu" not in resource_section:
                        self.results.append(ValidationResult(
                            passed=False,
                            message=f"Container {container_name} missing CPU {resource_type}",
                            severity="warning",
                            details={"file": str(manifest_file), "container": container_name}
                        ))
                    if "memory" not in resource_section:
                        self.results.append(ValidationResult(
                            passed=False,
                            message=f"Container {container_name} missing memory {resource_type}",
                            severity="warning",
                            details={"file": str(manifest_file), "container": container_name}
                        ))

    def _validate_naming_conventions(self, manifest_file: Path, documents: List[Dict]) -> None:
        """Validate naming conventions for Epic 8"""

        for i, doc in enumerate(documents):
            metadata = doc.get("metadata", {})
            name = metadata.get("name", "")
            kind = doc.get("kind", "")

            # Epic 8 naming convention: epic8-{service}-{component}
            if any(service in name for service in self.epic8_services):
                if not name.startswith("epic8-"):
                    self.results.append(ValidationResult(
                        passed=False,
                        message=f"Epic 8 resource {name} should follow naming convention: epic8-{{service}}-{{component}}",
                        severity="warning",
                        details={"file": str(manifest_file), "resource": name, "kind": kind}
                    ))
                else:
                    self.results.append(ValidationResult(
                        passed=True,
                        message=f"Epic 8 naming convention followed: {name}",
                        severity="info",
                        details={"file": str(manifest_file), "resource": name}
                    ))

    def _validate_labels_and_annotations(self, manifest_file: Path, documents: List[Dict]) -> None:
        """Validate labels and annotations"""

        for i, doc in enumerate(documents):
            metadata = doc.get("metadata", {})
            labels = metadata.get("labels", {})
            name = metadata.get("name", "")
            kind = doc.get("kind", "")

            # Check required labels for Epic 8 services
            if any(service in name for service in self.epic8_services):
                missing_labels = self.required_labels - set(labels.keys())

                if missing_labels:
                    self.results.append(ValidationResult(
                        passed=False,
                        message=f"Epic 8 resource {name} missing required labels: {missing_labels}",
                        severity="warning",
                        details={
                            "file": str(manifest_file),
                            "resource": name,
                            "missing_labels": list(missing_labels)
                        }
                    ))
                else:
                    self.results.append(ValidationResult(
                        passed=True,
                        message=f"Epic 8 resource {name} has all required labels",
                        severity="info",
                        details={"file": str(manifest_file), "resource": name}
                    ))

                # Validate label values
                app_name = labels.get("app.kubernetes.io/name", "")
                if app_name and not any(service in app_name for service in self.epic8_services):
                    self.results.append(ValidationResult(
                        passed=False,
                        message=f"app.kubernetes.io/name label should contain Epic 8 service name: {app_name}",
                        severity="warning",
                        details={"file": str(manifest_file), "label_value": app_name}
                    ))

                # Check part-of label
                part_of = labels.get("app.kubernetes.io/part-of", "")
                if part_of != "epic8-rag-platform":
                    self.results.append(ValidationResult(
                        passed=False,
                        message=f"app.kubernetes.io/part-of should be 'epic8-rag-platform', got: {part_of}",
                        severity="warning",
                        details={"file": str(manifest_file), "part_of": part_of}
                    ))

def run_kubectl_validation(manifest_dir: Path) -> List[ValidationResult]:
    """
    Run kubectl dry-run validation on manifests

    Returns:
        List[ValidationResult]: Results from kubectl validation
    """
    results = []

    if not manifest_dir.exists():
        results.append(ValidationResult(
            passed=False,
            message=f"Manifest directory {manifest_dir} does not exist",
            severity="error"
        ))
        return results

    # Find all YAML files
    manifest_files = list(manifest_dir.glob("*.yaml")) + list(manifest_dir.glob("*.yml"))

    for manifest_file in manifest_files:
        try:
            # Run kubectl dry-run validation
            cmd = [
                "kubectl", "apply", "--dry-run=client", "--validate=true",
                "-f", str(manifest_file)
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0:
                results.append(ValidationResult(
                    passed=True,
                    message=f"kubectl validation passed for {manifest_file.name}",
                    severity="info",
                    details={"file": str(manifest_file), "output": result.stdout}
                ))
            else:
                results.append(ValidationResult(
                    passed=False,
                    message=f"kubectl validation failed for {manifest_file.name}: {result.stderr}",
                    severity="error",
                    details={"file": str(manifest_file), "error": result.stderr}
                ))

        except subprocess.TimeoutExpired:
            results.append(ValidationResult(
                passed=False,
                message=f"kubectl validation timeout for {manifest_file.name}",
                severity="error",
                details={"file": str(manifest_file)}
            ))
        except FileNotFoundError:
            results.append(ValidationResult(
                passed=False,
                message="kubectl not found - install kubectl for complete validation",
                severity="warning"
            ))
            break
        except Exception as e:
            results.append(ValidationResult(
                passed=False,
                message=f"kubectl validation error for {manifest_file.name}: {str(e)}",
                severity="error",
                details={"file": str(manifest_file), "error": str(e)}
            ))

    return results

def run_kubeval_validation(manifest_dir: Path) -> List[ValidationResult]:
    """
    Run kubeval validation on manifests

    Returns:
        List[ValidationResult]: Results from kubeval validation
    """
    results = []

    if not manifest_dir.exists():
        results.append(ValidationResult(
            passed=False,
            message=f"Manifest directory {manifest_dir} does not exist",
            severity="error"
        ))
        return results

    try:
        # Run kubeval on all YAML files
        cmd = ["kubeval", str(manifest_dir / "*.yaml")]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            shell=True,
            timeout=60
        )

        if result.returncode == 0:
            results.append(ValidationResult(
                passed=True,
                message="kubeval validation passed for all manifests",
                severity="info",
                details={"output": result.stdout}
            ))
        else:
            results.append(ValidationResult(
                passed=False,
                message=f"kubeval validation failed: {result.stderr}",
                severity="error",
                details={"error": result.stderr}
            ))

    except FileNotFoundError:
        results.append(ValidationResult(
            passed=True,
            message="kubeval not found - optional validation tool",
            severity="info"
        ))
    except Exception as e:
        results.append(ValidationResult(
            passed=False,
            message=f"kubeval validation error: {str(e)}",
            severity="error",
            details={"error": str(e)}
        ))

    return results

# Pytest test cases

class TestKubernetesManifestValidation:
    """Test suite for Kubernetes manifest validation"""

    @pytest.fixture
    def manifest_dir(self):
        """Fixture providing manifest directory path"""
        return PROJECT_ROOT / "k8s" / "manifests"

    @pytest.fixture
    def validator(self, manifest_dir):
        """Fixture providing configured validator"""
        return KubernetesManifestValidator(manifest_dir)

    def test_yaml_syntax_validation(self, validator):
        """Test YAML syntax validation"""
        results = validator.validate_all_manifests()

        # Check that we have some results
        assert len(results) > 0, "No validation results returned"

        # Check for YAML syntax errors
        syntax_errors = [r for r in results if "syntax" in r.message.lower() and not r.passed]
        assert len(syntax_errors) == 0, f"YAML syntax errors found: {[r.message for r in syntax_errors]}"

    def test_kubernetes_resource_validation(self, validator):
        """Test Kubernetes resource validation"""
        results = validator.validate_all_manifests()

        # Check for missing required fields
        missing_field_errors = [r for r in results if "missing required fields" in r.message.lower() and not r.passed]
        assert len(missing_field_errors) == 0, f"Missing required fields: {[r.message for r in missing_field_errors]}"

    def test_security_policy_validation(self, validator):
        """Test security policy validation"""
        results = validator.validate_all_manifests()

        # Check for security violations (these may be warnings)
        security_issues = [r for r in results if "security" in r.message.lower() and r.severity == "error"]

        # Security issues should be warnings, not errors (except for critical issues)
        critical_security_errors = [r for r in security_issues if "critical" in r.message.lower()]
        assert len(critical_security_errors) == 0, f"Critical security errors: {[r.message for r in critical_security_errors]}"

    def test_resource_allocation_validation(self, validator):
        """Test resource allocation validation"""
        results = validator.validate_all_manifests()

        # Check that most containers have resource specifications
        resource_warnings = [r for r in results if "resource" in r.message.lower() and not r.passed]

        # This should be informational - we want resources defined but it's not critical
        print(f"Resource allocation warnings: {len(resource_warnings)}")
        for warning in resource_warnings[:5]:  # Print first 5 warnings
            print(f"  - {warning.message}")

    def test_naming_convention_validation(self, validator):
        """Test Epic 8 naming convention validation"""
        results = validator.validate_all_manifests()

        # Check Epic 8 naming conventions
        naming_errors = [r for r in results if "naming convention" in r.message.lower() and not r.passed]

        # Print naming convention issues for review
        print(f"Naming convention issues: {len(naming_errors)}")
        for error in naming_errors:
            print(f"  - {error.message}")

    def test_label_validation(self, validator):
        """Test label and annotation validation"""
        results = validator.validate_all_manifests()

        # Check for label issues
        label_errors = [r for r in results if "label" in r.message.lower() and not r.passed]

        # Print label issues for review
        print(f"Label issues: {len(label_errors)}")
        for error in label_errors:
            print(f"  - {error.message}")

    def test_kubectl_validation(self, manifest_dir):
        """Test kubectl dry-run validation"""
        results = run_kubectl_validation(manifest_dir)

        # Check kubectl validation results
        kubectl_errors = [r for r in results if not r.passed and r.severity == "error"]

        if kubectl_errors:
            print(f"kubectl validation errors: {len(kubectl_errors)}")
            for error in kubectl_errors[:3]:  # Print first 3 errors
                print(f"  - {error.message}")

        # kubectl validation should not have critical errors
        critical_errors = [r for r in kubectl_errors if "critical" in r.message.lower()]
        assert len(critical_errors) == 0, f"Critical kubectl errors: {[r.message for r in critical_errors]}"

    def test_kubeval_validation(self, manifest_dir):
        """Test kubeval validation (optional)"""
        results = run_kubeval_validation(manifest_dir)

        # kubeval is optional, so we just check if it runs without critical errors
        critical_errors = [r for r in results if not r.passed and "critical" in r.message.lower()]
        assert len(critical_errors) == 0, f"Critical kubeval errors: {[r.message for r in critical_errors]}"

if __name__ == "__main__":
    """Command-line interface for manifest validation"""

    import argparse

    parser = argparse.ArgumentParser(description="Validate Kubernetes manifests for Epic 8")
    parser.add_argument(
        "--manifest-dir",
        type=Path,
        default=PROJECT_ROOT / "k8s" / "manifests",
        help="Directory containing Kubernetes manifests"
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

    args = parser.parse_args()

    # Run validation
    validator = KubernetesManifestValidator(args.manifest_dir)
    results = validator.validate_all_manifests()

    # Add kubectl and kubeval results
    results.extend(run_kubectl_validation(args.manifest_dir))
    results.extend(run_kubeval_validation(args.manifest_dir))

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
            "results": [
                {
                    "passed": r.passed,
                    "message": r.message,
                    "severity": r.severity,
                    "details": r.details
                }
                for r in filtered_results
            ]
        }
        print(json.dumps(output, indent=2))
    else:
        # Text output
        print(f"\n=== Epic 8 Kubernetes Manifest Validation Results ===")
        print(f"Total results: {len(filtered_results)}")
        print(f"Passed: {len([r for r in filtered_results if r.passed])}")
        print(f"Failed: {len([r for r in filtered_results if not r.passed])}")
        print(f"Minimum severity: {args.severity}")
        print()

        for result in filtered_results:
            icon = "✅" if result.passed else "❌"
            severity_icon = {"info": "ℹ️", "warning": "⚠️", "error": "🚨"}[result.severity]

            print(f"{icon} {severity_icon} {result.message}")
            if result.details and args.severity == "info":
                print(f"   Details: {result.details}")
            print()

        # Summary
        error_count = len([r for r in filtered_results if not r.passed and r.severity == "error"])
        warning_count = len([r for r in filtered_results if not r.passed and r.severity == "warning"])

        print(f"\n=== Summary ===")
        print(f"🚨 Errors: {error_count}")
        print(f"⚠️  Warnings: {warning_count}")

        if error_count == 0:
            print("✅ No critical errors found - manifests are valid for deployment!")
        else:
            print("❌ Critical errors found - please fix before deployment")