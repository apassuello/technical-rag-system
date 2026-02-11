#!/usr/bin/env python3
"""
Deployment Validation Framework
Epic 8 Cloud-Native RAG Platform

This module provides comprehensive deployment validation for Kubernetes deployments,
following test-driven development principles for cloud-native applications.

Validation Categories:
1. Service Readiness Validation
2. Pod Health Check Testing
3. Network Connectivity Testing
4. Resource Allocation Validation
5. Performance Baseline Testing
6. Security Configuration Validation
"""

import os
import sys
import json
import time
import asyncio
import subprocess
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass, asdict
import yaml
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class ValidationResult:
    """Result of a deployment validation test"""
    test_name: str
    passed: bool
    message: str
    duration_seconds: float
    severity: str = "error"  # error, warning, info
    component: Optional[str] = None
    details: Optional[Dict[str, Any]] = None

@dataclass
class ServiceEndpoint:
    """Service endpoint configuration"""
    name: str
    namespace: str
    port: int
    path: str = "/health"
    expected_status: int = 200
    timeout: int = 30

class KubernetesDeploymentValidator:
    """
    Comprehensive Kubernetes deployment validation framework

    Validates deployments against:
    - Service readiness and availability
    - Pod health and resource allocation
    - Network connectivity and service mesh
    - Performance baselines
    - Security configurations
    """

    def __init__(self, namespace: str = "epic8", timeout: int = 300):
        self.namespace = namespace
        self.timeout = timeout
        self.results: List[ValidationResult] = []

        # Epic 8 service configuration
        self.epic8_services = [
            ServiceEndpoint("epic8-api-gateway", namespace, 8080, "/health"),
            ServiceEndpoint("epic8-query-analyzer", namespace, 8082, "/health/live"),
            ServiceEndpoint("epic8-generator", namespace, 8081, "/health/live"),
            ServiceEndpoint("epic8-retriever", namespace, 8083, "/health/live"),
            ServiceEndpoint("epic8-cache", namespace, 8084, "/health/live"),
            ServiceEndpoint("epic8-analytics", namespace, 8085, "/health/live"),
        ]

        # Required deployments for Epic 8
        self.required_deployments = [
            "epic8-api-gateway",
            "epic8-query-analyzer",
            "epic8-generator",
            "epic8-retriever",
            "epic8-cache",
            "epic8-analytics"
        ]

    def validate_all(self) -> List[ValidationResult]:
        """
        Run all deployment validation tests

        Returns:
            List[ValidationResult]: Comprehensive validation results
        """
        self.results.clear()
        start_time = time.time()

        logger.info(f"Starting Epic 8 deployment validation in namespace: {self.namespace}")

        # 1. Namespace and RBAC validation
        self._validate_namespace()

        # 2. Deployment readiness validation
        self._validate_deployments()

        # 3. Pod health validation
        self._validate_pods()

        # 4. Service connectivity validation
        self._validate_services()

        # 5. Network connectivity testing
        self._validate_network_connectivity()

        # 6. Resource allocation validation
        self._validate_resource_allocation()

        # 7. Performance baseline testing
        self._validate_performance_baselines()

        # 8. Security configuration validation
        self._validate_security_configuration()

        total_duration = time.time() - start_time
        self.results.append(ValidationResult(
            test_name="complete_validation",
            passed=all(r.passed for r in self.results if r.severity == "error"),
            message=f"Complete validation finished in {total_duration:.2f}s",
            duration_seconds=total_duration,
            severity="info",
            details={
                "total_tests": len(self.results),
                "passed": len([r for r in self.results if r.passed]),
                "failed": len([r for r in self.results if not r.passed])
            }
        ))

        return self.results

    def _validate_namespace(self) -> None:
        """Validate namespace exists and has proper configuration"""
        start_time = time.time()

        try:
            # Check if namespace exists
            result = subprocess.run(
                ["kubectl", "get", "namespace", self.namespace],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode != 0:
                self.results.append(ValidationResult(
                    test_name="namespace_exists",
                    passed=False,
                    message=f"Namespace {self.namespace} does not exist",
                    duration_seconds=time.time() - start_time,
                    severity="error",
                    details={"error": result.stderr}
                ))
                return

            # Get namespace details
            result = subprocess.run(
                ["kubectl", "get", "namespace", self.namespace, "-o", "yaml"],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0:
                namespace_data = yaml.safe_load(result.stdout)
                labels = namespace_data.get("metadata", {}).get("labels", {})

                # Check for Epic 8 label
                if labels.get("app.kubernetes.io/part-of") == "epic8-rag-platform":
                    self.results.append(ValidationResult(
                        test_name="namespace_labels",
                        passed=True,
                        message=f"Namespace {self.namespace} has correct Epic 8 labels",
                        duration_seconds=time.time() - start_time,
                        severity="info"
                    ))
                else:
                    self.results.append(ValidationResult(
                        test_name="namespace_labels",
                        passed=False,
                        message=f"Namespace {self.namespace} missing Epic 8 labels",
                        duration_seconds=time.time() - start_time,
                        severity="warning",
                        details={"labels": labels}
                    ))

            # Check service account
            result = subprocess.run(
                ["kubectl", "get", "serviceaccount", "epic8-service-account", "-n", self.namespace],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0:
                self.results.append(ValidationResult(
                    test_name="service_account_exists",
                    passed=True,
                    message="Epic 8 service account exists",
                    duration_seconds=time.time() - start_time,
                    severity="info"
                ))
            else:
                self.results.append(ValidationResult(
                    test_name="service_account_exists",
                    passed=False,
                    message="Epic 8 service account not found",
                    duration_seconds=time.time() - start_time,
                    severity="warning"
                ))

        except Exception as e:
            self.results.append(ValidationResult(
                test_name="namespace_validation",
                passed=False,
                message=f"Namespace validation failed: {str(e)}",
                duration_seconds=time.time() - start_time,
                severity="error",
                details={"error": str(e)}
            ))

    def _validate_deployments(self) -> None:
        """Validate deployment readiness and rollout status"""
        start_time = time.time()

        try:
            # Get all deployments in namespace
            result = subprocess.run(
                ["kubectl", "get", "deployments", "-n", self.namespace, "-o", "json"],
                capture_output=True,
                text=True,
                timeout=60
            )

            if result.returncode != 0:
                self.results.append(ValidationResult(
                    test_name="deployments_list",
                    passed=False,
                    message=f"Failed to list deployments in namespace {self.namespace}",
                    duration_seconds=time.time() - start_time,
                    severity="error",
                    details={"error": result.stderr}
                ))
                return

            deployments_data = json.loads(result.stdout)
            deployments = deployments_data.get("items", [])

            if not deployments:
                self.results.append(ValidationResult(
                    test_name="deployments_exist",
                    passed=False,
                    message=f"No deployments found in namespace {self.namespace}",
                    duration_seconds=time.time() - start_time,
                    severity="error"
                ))
                return

            # Check each required deployment
            found_deployments = [dep["metadata"]["name"] for dep in deployments]

            for required_deployment in self.required_deployments:
                if required_deployment in found_deployments:
                    self._validate_single_deployment(required_deployment)
                else:
                    self.results.append(ValidationResult(
                        test_name=f"deployment_{required_deployment}_exists",
                        passed=False,
                        message=f"Required deployment {required_deployment} not found",
                        duration_seconds=time.time() - start_time,
                        severity="error",
                        component=required_deployment
                    ))

            # Summary result
            self.results.append(ValidationResult(
                test_name="deployments_summary",
                passed=len(found_deployments) >= len(self.required_deployments),
                message=f"Found {len(found_deployments)}/{len(self.required_deployments)} required deployments",
                duration_seconds=time.time() - start_time,
                severity="info",
                details={
                    "found": found_deployments,
                    "required": self.required_deployments
                }
            ))

        except Exception as e:
            self.results.append(ValidationResult(
                test_name="deployments_validation",
                passed=False,
                message=f"Deployment validation failed: {str(e)}",
                duration_seconds=time.time() - start_time,
                severity="error",
                details={"error": str(e)}
            ))

    def _validate_single_deployment(self, deployment_name: str) -> None:
        """Validate a single deployment's readiness"""
        start_time = time.time()

        try:
            # Get deployment status
            result = subprocess.run(
                ["kubectl", "get", "deployment", deployment_name, "-n", self.namespace, "-o", "json"],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode != 0:
                self.results.append(ValidationResult(
                    test_name=f"deployment_{deployment_name}_status",
                    passed=False,
                    message=f"Failed to get deployment {deployment_name} status",
                    duration_seconds=time.time() - start_time,
                    severity="error",
                    component=deployment_name,
                    details={"error": result.stderr}
                ))
                return

            deployment_data = json.loads(result.stdout)
            status = deployment_data.get("status", {})

            # Check replicas
            replicas = status.get("replicas", 0)
            ready_replicas = status.get("readyReplicas", 0)
            available_replicas = status.get("availableReplicas", 0)

            if ready_replicas == replicas and available_replicas == replicas:
                self.results.append(ValidationResult(
                    test_name=f"deployment_{deployment_name}_ready",
                    passed=True,
                    message=f"Deployment {deployment_name} is ready ({ready_replicas}/{replicas} replicas)",
                    duration_seconds=time.time() - start_time,
                    severity="info",
                    component=deployment_name,
                    details={
                        "replicas": replicas,
                        "ready_replicas": ready_replicas,
                        "available_replicas": available_replicas
                    }
                ))
            else:
                self.results.append(ValidationResult(
                    test_name=f"deployment_{deployment_name}_ready",
                    passed=False,
                    message=f"Deployment {deployment_name} not ready ({ready_replicas}/{replicas} replicas)",
                    duration_seconds=time.time() - start_time,
                    severity="error",
                    component=deployment_name,
                    details={
                        "replicas": replicas,
                        "ready_replicas": ready_replicas,
                        "available_replicas": available_replicas
                    }
                ))

            # Check conditions
            conditions = status.get("conditions", [])
            for condition in conditions:
                condition_type = condition.get("type")
                condition_status = condition.get("status")

                if condition_type == "Available" and condition_status == "True":
                    self.results.append(ValidationResult(
                        test_name=f"deployment_{deployment_name}_available",
                        passed=True,
                        message=f"Deployment {deployment_name} is available",
                        duration_seconds=time.time() - start_time,
                        severity="info",
                        component=deployment_name
                    ))
                elif condition_type == "Progressing" and condition_status == "True":
                    reason = condition.get("reason", "")
                    if reason == "NewReplicaSetAvailable":
                        self.results.append(ValidationResult(
                            test_name=f"deployment_{deployment_name}_progressing",
                            passed=True,
                            message=f"Deployment {deployment_name} rollout completed",
                            duration_seconds=time.time() - start_time,
                            severity="info",
                            component=deployment_name
                        ))

        except Exception as e:
            self.results.append(ValidationResult(
                test_name=f"deployment_{deployment_name}_validation",
                passed=False,
                message=f"Deployment {deployment_name} validation failed: {str(e)}",
                duration_seconds=time.time() - start_time,
                severity="error",
                component=deployment_name,
                details={"error": str(e)}
            ))

    def _validate_pods(self) -> None:
        """Validate pod health and resource usage"""
        start_time = time.time()

        try:
            # Get all pods in namespace
            result = subprocess.run(
                ["kubectl", "get", "pods", "-n", self.namespace, "-o", "json"],
                capture_output=True,
                text=True,
                timeout=60
            )

            if result.returncode != 0:
                self.results.append(ValidationResult(
                    test_name="pods_list",
                    passed=False,
                    message=f"Failed to list pods in namespace {self.namespace}",
                    duration_seconds=time.time() - start_time,
                    severity="error",
                    details={"error": result.stderr}
                ))
                return

            pods_data = json.loads(result.stdout)
            pods = pods_data.get("items", [])

            if not pods:
                self.results.append(ValidationResult(
                    test_name="pods_exist",
                    passed=False,
                    message=f"No pods found in namespace {self.namespace}",
                    duration_seconds=time.time() - start_time,
                    severity="error"
                ))
                return

            # Validate each pod
            running_pods = 0
            total_pods = len(pods)

            for pod in pods:
                pod_name = pod["metadata"]["name"]
                pod_status = pod.get("status", {})
                phase = pod_status.get("phase", "Unknown")

                if phase == "Running":
                    running_pods += 1
                    self._validate_single_pod(pod)
                else:
                    self.results.append(ValidationResult(
                        test_name=f"pod_{pod_name}_running",
                        passed=False,
                        message=f"Pod {pod_name} is not running (phase: {phase})",
                        duration_seconds=time.time() - start_time,
                        severity="error",
                        component=pod_name,
                        details={"phase": phase}
                    ))

            # Summary result
            self.results.append(ValidationResult(
                test_name="pods_summary",
                passed=running_pods == total_pods,
                message=f"{running_pods}/{total_pods} pods are running",
                duration_seconds=time.time() - start_time,
                severity="info",
                details={
                    "running_pods": running_pods,
                    "total_pods": total_pods
                }
            ))

        except Exception as e:
            self.results.append(ValidationResult(
                test_name="pods_validation",
                passed=False,
                message=f"Pod validation failed: {str(e)}",
                duration_seconds=time.time() - start_time,
                severity="error",
                details={"error": str(e)}
            ))

    def _validate_single_pod(self, pod_data: Dict) -> None:
        """Validate a single pod's health"""
        start_time = time.time()

        pod_name = pod_data["metadata"]["name"]
        pod_status = pod_data.get("status", {})

        # Check container statuses
        container_statuses = pod_status.get("containerStatuses", [])
        ready_containers = 0
        total_containers = len(container_statuses)

        for container_status in container_statuses:
            container_name = container_status["name"]
            ready = container_status.get("ready", False)
            restart_count = container_status.get("restartCount", 0)

            if ready:
                ready_containers += 1

            if restart_count > 5:  # High restart count warning
                self.results.append(ValidationResult(
                    test_name=f"container_{container_name}_restarts",
                    passed=False,
                    message=f"Container {container_name} has high restart count: {restart_count}",
                    duration_seconds=time.time() - start_time,
                    severity="warning",
                    component=pod_name,
                    details={"restart_count": restart_count}
                ))

        # Check readiness
        if ready_containers == total_containers:
            self.results.append(ValidationResult(
                test_name=f"pod_{pod_name}_containers_ready",
                passed=True,
                message=f"Pod {pod_name} all containers ready ({ready_containers}/{total_containers})",
                duration_seconds=time.time() - start_time,
                severity="info",
                component=pod_name
            ))
        else:
            self.results.append(ValidationResult(
                test_name=f"pod_{pod_name}_containers_ready",
                passed=False,
                message=f"Pod {pod_name} containers not ready ({ready_containers}/{total_containers})",
                duration_seconds=time.time() - start_time,
                severity="error",
                component=pod_name,
                details={
                    "ready_containers": ready_containers,
                    "total_containers": total_containers
                }
            ))

    def _validate_services(self) -> None:
        """Validate service availability and endpoints"""
        start_time = time.time()

        try:
            # Get all services in namespace
            result = subprocess.run(
                ["kubectl", "get", "services", "-n", self.namespace, "-o", "json"],
                capture_output=True,
                text=True,
                timeout=60
            )

            if result.returncode != 0:
                self.results.append(ValidationResult(
                    test_name="services_list",
                    passed=False,
                    message=f"Failed to list services in namespace {self.namespace}",
                    duration_seconds=time.time() - start_time,
                    severity="error",
                    details={"error": result.stderr}
                ))
                return

            services_data = json.loads(result.stdout)
            services = services_data.get("items", [])

            # Check each Epic 8 service
            for service_endpoint in self.epic8_services:
                service_found = any(
                    svc["metadata"]["name"] == service_endpoint.name
                    for svc in services
                )

                if service_found:
                    self.results.append(ValidationResult(
                        test_name=f"service_{service_endpoint.name}_exists",
                        passed=True,
                        message=f"Service {service_endpoint.name} exists",
                        duration_seconds=time.time() - start_time,
                        severity="info",
                        component=service_endpoint.name
                    ))

                    # Check service endpoints
                    self._validate_service_endpoints(service_endpoint.name)
                else:
                    self.results.append(ValidationResult(
                        test_name=f"service_{service_endpoint.name}_exists",
                        passed=False,
                        message=f"Service {service_endpoint.name} not found",
                        duration_seconds=time.time() - start_time,
                        severity="error",
                        component=service_endpoint.name
                    ))

        except Exception as e:
            self.results.append(ValidationResult(
                test_name="services_validation",
                passed=False,
                message=f"Service validation failed: {str(e)}",
                duration_seconds=time.time() - start_time,
                severity="error",
                details={"error": str(e)}
            ))

    def _validate_service_endpoints(self, service_name: str) -> None:
        """Validate service endpoints"""
        start_time = time.time()

        try:
            # Get service endpoints
            result = subprocess.run(
                ["kubectl", "get", "endpoints", service_name, "-n", self.namespace, "-o", "json"],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode != 0:
                self.results.append(ValidationResult(
                    test_name=f"service_{service_name}_endpoints",
                    passed=False,
                    message=f"Service {service_name} has no endpoints",
                    duration_seconds=time.time() - start_time,
                    severity="error",
                    component=service_name,
                    details={"error": result.stderr}
                ))
                return

            endpoints_data = json.loads(result.stdout)
            subsets = endpoints_data.get("subsets", [])

            if not subsets:
                self.results.append(ValidationResult(
                    test_name=f"service_{service_name}_endpoints",
                    passed=False,
                    message=f"Service {service_name} has no endpoint subsets",
                    duration_seconds=time.time() - start_time,
                    severity="error",
                    component=service_name
                ))
                return

            # Count ready endpoints
            total_endpoints = 0
            for subset in subsets:
                addresses = subset.get("addresses", [])
                total_endpoints += len(addresses)

            if total_endpoints > 0:
                self.results.append(ValidationResult(
                    test_name=f"service_{service_name}_endpoints",
                    passed=True,
                    message=f"Service {service_name} has {total_endpoints} ready endpoints",
                    duration_seconds=time.time() - start_time,
                    severity="info",
                    component=service_name,
                    details={"endpoint_count": total_endpoints}
                ))
            else:
                self.results.append(ValidationResult(
                    test_name=f"service_{service_name}_endpoints",
                    passed=False,
                    message=f"Service {service_name} has no ready endpoints",
                    duration_seconds=time.time() - start_time,
                    severity="error",
                    component=service_name
                ))

        except Exception as e:
            self.results.append(ValidationResult(
                test_name=f"service_{service_name}_endpoints",
                passed=False,
                message=f"Service {service_name} endpoint validation failed: {str(e)}",
                duration_seconds=time.time() - start_time,
                severity="error",
                component=service_name,
                details={"error": str(e)}
            ))

    def _validate_network_connectivity(self) -> None:
        """Validate network connectivity between services"""
        start_time = time.time()

        try:
            # Test connectivity using a test pod
            test_pod_name = "epic8-network-test"

            # Create test pod if it doesn't exist
            self._ensure_test_pod_exists(test_pod_name)

            # Wait for test pod to be ready
            time.sleep(5)

            # Test connectivity to each service
            for service_endpoint in self.epic8_services:
                self._test_service_connectivity(test_pod_name, service_endpoint)

            # Cleanup test pod
            subprocess.run(
                ["kubectl", "delete", "pod", test_pod_name, "-n", self.namespace, "--ignore-not-found"],
                capture_output=True,
                timeout=30
            )

        except Exception as e:
            self.results.append(ValidationResult(
                test_name="network_connectivity",
                passed=False,
                message=f"Network connectivity validation failed: {str(e)}",
                duration_seconds=time.time() - start_time,
                severity="error",
                details={"error": str(e)}
            ))

    def _ensure_test_pod_exists(self, pod_name: str) -> None:
        """Ensure test pod exists for connectivity testing"""
        # Check if pod already exists
        result = subprocess.run(
            ["kubectl", "get", "pod", pod_name, "-n", self.namespace],
            capture_output=True,
            timeout=30
        )

        if result.returncode != 0:
            # Create test pod
            subprocess.run([
                "kubectl", "run", pod_name,
                "--image=curlimages/curl:latest",
                "--restart=Never",
                "--command", "--",
                "sleep", "300",
                "-n", self.namespace
            ], timeout=60)

    def _test_service_connectivity(self, test_pod_name: str, service_endpoint: ServiceEndpoint) -> None:
        """Test connectivity to a specific service"""
        start_time = time.time()

        try:
            # Test HTTP connectivity
            url = f"http://{service_endpoint.name}:{service_endpoint.port}{service_endpoint.path}"

            result = subprocess.run([
                "kubectl", "exec", test_pod_name, "-n", self.namespace, "--",
                "curl", "-s", "-o", "/dev/null", "-w", "%{http_code}",
                "--connect-timeout", "10",
                "--max-time", "30",
                url
            ], capture_output=True, text=True, timeout=60)

            if result.returncode == 0:
                status_code = result.stdout.strip()
                if status_code == str(service_endpoint.expected_status):
                    self.results.append(ValidationResult(
                        test_name=f"connectivity_{service_endpoint.name}",
                        passed=True,
                        message=f"Service {service_endpoint.name} connectivity OK (HTTP {status_code})",
                        duration_seconds=time.time() - start_time,
                        severity="info",
                        component=service_endpoint.name,
                        details={"status_code": status_code}
                    ))
                else:
                    self.results.append(ValidationResult(
                        test_name=f"connectivity_{service_endpoint.name}",
                        passed=False,
                        message=f"Service {service_endpoint.name} unexpected status (HTTP {status_code})",
                        duration_seconds=time.time() - start_time,
                        severity="warning",
                        component=service_endpoint.name,
                        details={"status_code": status_code, "expected": service_endpoint.expected_status}
                    ))
            else:
                self.results.append(ValidationResult(
                    test_name=f"connectivity_{service_endpoint.name}",
                    passed=False,
                    message=f"Service {service_endpoint.name} connectivity failed",
                    duration_seconds=time.time() - start_time,
                    severity="error",
                    component=service_endpoint.name,
                    details={"error": result.stderr}
                ))

        except Exception as e:
            self.results.append(ValidationResult(
                test_name=f"connectivity_{service_endpoint.name}",
                passed=False,
                message=f"Service {service_endpoint.name} connectivity test failed: {str(e)}",
                duration_seconds=time.time() - start_time,
                severity="error",
                component=service_endpoint.name,
                details={"error": str(e)}
            ))

    def _validate_resource_allocation(self) -> None:
        """Validate resource allocation and usage"""
        start_time = time.time()

        try:
            # Get pod resource usage
            result = subprocess.run(
                ["kubectl", "top", "pods", "-n", self.namespace],
                capture_output=True,
                text=True,
                timeout=60
            )

            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')[1:]  # Skip header
                total_cpu = 0
                total_memory = 0

                for line in lines:
                    if line.strip():
                        parts = line.split()
                        if len(parts) >= 3:
                            cpu_str = parts[1]
                            memory_str = parts[2]

                            # Parse CPU (remove 'm' for millicores)
                            if cpu_str.endswith('m'):
                                total_cpu += int(cpu_str[:-1])

                            # Parse memory (convert to MB)
                            if memory_str.endswith('Mi'):
                                total_memory += int(memory_str[:-2])
                            elif memory_str.endswith('Ki'):
                                total_memory += int(memory_str[:-2]) / 1024

                self.results.append(ValidationResult(
                    test_name="resource_usage",
                    passed=True,
                    message=f"Resource usage - CPU: {total_cpu}m, Memory: {total_memory:.1f}Mi",
                    duration_seconds=time.time() - start_time,
                    severity="info",
                    details={
                        "total_cpu_millicores": total_cpu,
                        "total_memory_mb": total_memory
                    }
                ))

                # Check if usage is reasonable (not too high)
                if total_cpu > 2000:  # 2 CPU cores
                    self.results.append(ValidationResult(
                        test_name="resource_usage_cpu",
                        passed=False,
                        message=f"High CPU usage detected: {total_cpu}m",
                        duration_seconds=time.time() - start_time,
                        severity="warning",
                        details={"cpu_usage": total_cpu}
                    ))

                if total_memory > 4096:  # 4GB
                    self.results.append(ValidationResult(
                        test_name="resource_usage_memory",
                        passed=False,
                        message=f"High memory usage detected: {total_memory:.1f}Mi",
                        duration_seconds=time.time() - start_time,
                        severity="warning",
                        details={"memory_usage": total_memory}
                    ))

            else:
                self.results.append(ValidationResult(
                    test_name="resource_usage",
                    passed=False,
                    message="Failed to get resource usage (metrics-server may not be available)",
                    duration_seconds=time.time() - start_time,
                    severity="warning",
                    details={"error": result.stderr}
                ))

        except Exception as e:
            self.results.append(ValidationResult(
                test_name="resource_allocation",
                passed=False,
                message=f"Resource allocation validation failed: {str(e)}",
                duration_seconds=time.time() - start_time,
                severity="error",
                details={"error": str(e)}
            ))

    def _validate_performance_baselines(self) -> None:
        """Validate performance baselines"""
        start_time = time.time()

        # This is a placeholder for performance testing
        # In a real implementation, you would run load tests here
        self.results.append(ValidationResult(
            test_name="performance_baselines",
            passed=True,
            message="Performance baseline validation - placeholder (implement load testing)",
            duration_seconds=time.time() - start_time,
            severity="info",
            details={"note": "Implement actual performance tests"}
        ))

    def _validate_security_configuration(self) -> None:
        """Validate security configuration"""
        start_time = time.time()

        try:
            # Check pod security contexts
            result = subprocess.run(
                ["kubectl", "get", "pods", "-n", self.namespace, "-o", "json"],
                capture_output=True,
                text=True,
                timeout=60
            )

            if result.returncode == 0:
                pods_data = json.loads(result.stdout)
                pods = pods_data.get("items", [])

                pods_with_security_context = 0
                total_pods = len(pods)

                for pod in pods:
                    spec = pod.get("spec", {})
                    security_context = spec.get("securityContext", {})

                    if security_context:
                        pods_with_security_context += 1

                        # Check specific security settings
                        run_as_non_root = security_context.get("runAsNonRoot", False)
                        if not run_as_non_root:
                            pod_name = pod["metadata"]["name"]
                            self.results.append(ValidationResult(
                                test_name=f"security_{pod_name}_non_root",
                                passed=False,
                                message=f"Pod {pod_name} not configured to run as non-root",
                                duration_seconds=time.time() - start_time,
                                severity="warning",
                                component=pod_name
                            ))

                self.results.append(ValidationResult(
                    test_name="security_contexts",
                    passed=pods_with_security_context == total_pods,
                    message=f"{pods_with_security_context}/{total_pods} pods have security contexts",
                    duration_seconds=time.time() - start_time,
                    severity="info" if pods_with_security_context == total_pods else "warning",
                    details={
                        "pods_with_security_context": pods_with_security_context,
                        "total_pods": total_pods
                    }
                ))

        except Exception as e:
            self.results.append(ValidationResult(
                test_name="security_configuration",
                passed=False,
                message=f"Security configuration validation failed: {str(e)}",
                duration_seconds=time.time() - start_time,
                severity="error",
                details={"error": str(e)}
            ))

def generate_validation_report(results: List[ValidationResult], output_file: Optional[Path] = None) -> str:
    """Generate a comprehensive validation report"""

    # Calculate summary statistics
    total_tests = len(results)
    passed_tests = len([r for r in results if r.passed])
    failed_tests = total_tests - passed_tests
    error_tests = len([r for r in results if not r.passed and r.severity == "error"])
    warning_tests = len([r for r in results if not r.passed and r.severity == "warning"])

    total_duration = sum(r.duration_seconds for r in results)

    # Generate report
    report_lines = [
        "# Epic 8 Kubernetes Deployment Validation Report",
        f"**Generated**: {time.strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "## Summary",
        f"- **Total Tests**: {total_tests}",
        f"- **Passed**: {passed_tests} ({passed_tests/total_tests*100:.1f}%)",
        f"- **Failed**: {failed_tests} ({failed_tests/total_tests*100:.1f}%)",
        f"- **Errors**: {error_tests}",
        f"- **Warnings**: {warning_tests}",
        f"- **Total Duration**: {total_duration:.2f} seconds",
        "",
        "## Test Results",
        ""
    ]

    # Group results by component
    components = set([r.component for r in results if r.component])
    components.add(None)  # For general tests

    for component in sorted(components, key=lambda x: x or "zzz_general"):
        component_results = [r for r in results if r.component == component]

        if component:
            report_lines.append(f"### Component: {component}")
        else:
            report_lines.append("### General Tests")

        report_lines.append("")

        for result in component_results:
            status_icon = "✅" if result.passed else "❌"
            severity_icon = {"info": "ℹ️", "warning": "⚠️", "error": "🚨"}[result.severity]

            report_lines.append(f"- {status_icon} {severity_icon} **{result.test_name}**: {result.message} ({result.duration_seconds:.2f}s)")

            if result.details:
                report_lines.append(f"  - Details: `{result.details}`")

        report_lines.append("")

    # Overall assessment
    report_lines.extend([
        "## Overall Assessment",
        ""
    ])

    if error_tests == 0:
        report_lines.append("✅ **DEPLOYMENT READY** - No critical errors found")
    else:
        report_lines.append("❌ **DEPLOYMENT NOT READY** - Critical errors must be resolved")

    if warning_tests > 0:
        report_lines.append(f"⚠️ {warning_tests} warnings found - review recommended")

    report_content = "\n".join(report_lines)

    # Save to file if specified
    if output_file:
        with open(output_file, 'w') as f:
            f.write(report_content)
        logger.info(f"Validation report saved to {output_file}")

    return report_content

if __name__ == "__main__":
    """Command-line interface for deployment validation"""

    import argparse

    parser = argparse.ArgumentParser(description="Validate Epic 8 Kubernetes deployments")
    parser.add_argument(
        "--namespace",
        default="epic8",
        help="Kubernetes namespace to validate (default: epic8)"
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=300,
        help="Timeout for validation tests in seconds (default: 300)"
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Output file for validation report"
    )
    parser.add_argument(
        "--output-format",
        choices=["text", "json", "markdown"],
        default="markdown",
        help="Output format for results (default: markdown)"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Run validation
    validator = KubernetesDeploymentValidator(
        namespace=args.namespace,
        timeout=args.timeout
    )

    logger.info(f"Starting deployment validation for namespace: {args.namespace}")
    results = validator.validate_all()

    # Output results
    if args.output_format == "json":
        output = {
            "summary": {
                "total_tests": len(results),
                "passed": len([r for r in results if r.passed]),
                "failed": len([r for r in results if not r.passed]),
                "errors": len([r for r in results if not r.passed and r.severity == "error"]),
                "warnings": len([r for r in results if not r.passed and r.severity == "warning"]),
                "total_duration": sum(r.duration_seconds for r in results)
            },
            "results": [asdict(r) for r in results]
        }
        output_content = json.dumps(output, indent=2)
    elif args.output_format == "markdown":
        output_content = generate_validation_report(results, args.output)
    else:
        # Text output
        output_lines = []
        for result in results:
            status = "PASS" if result.passed else "FAIL"
            output_lines.append(f"[{status}] {result.test_name}: {result.message} ({result.duration_seconds:.2f}s)")
        output_content = "\n".join(output_lines)

    if args.output:
        with open(args.output, 'w') as f:
            f.write(output_content)
        print(f"Results saved to {args.output}")
    else:
        print(output_content)

    # Exit with error code if there are critical failures
    error_count = len([r for r in results if not r.passed and r.severity == "error"])
    sys.exit(1 if error_count > 0 else 0)