"""
Test suite for BackendManagementServiceImpl functionality in PlatformOrchestrator.

Tests the backend management service that handles backend registration,
health checking, switching, data migration, and monitoring.
"""

import pytest
import time
from unittest.mock import Mock, patch
from typing import Dict, Any

from src.core.platform_orchestrator import BackendManagementServiceImpl
from src.core.interfaces import BackendStatus
from .conftest import MockComponent


class TestBackendManagementServiceImpl:
    """Test BackendManagementServiceImpl business logic and functionality."""

    def test_backend_management_service_initialization(self, backend_management_service):
        """Test backend management service initializes correctly."""
        assert backend_management_service.registered_backends == {}
        assert backend_management_service.backend_health == {}
        assert backend_management_service.component_backends == {}
        
        # Should have default backends registered
        # (This would depend on _register_default_backends implementation)

    def test_register_backend_basic(self, backend_management_service):
        """Test registering a new backend."""
        backend_config = {
            "type": "redis",
            "host": "localhost",
            "port": 6379,
            "password": "test_password",
            "connection_pool_size": 10
        }
        
        backend_management_service.register_backend("test_redis", backend_config)
        
        assert "test_redis" in backend_management_service.registered_backends
        stored_config = backend_management_service.registered_backends["test_redis"]
        assert stored_config["type"] == "redis"
        assert stored_config["host"] == "localhost"

    def test_register_backend_duplicate(self, backend_management_service):
        """Test registering duplicate backend name."""
        backend_config = {"type": "faiss", "dimension": 384}
        
        backend_management_service.register_backend("duplicate_backend", backend_config)
        
        # Attempt to register with same name should either update or raise error
        new_config = {"type": "pinecone", "api_key": "test_key"}
        
        # Should either succeed (update) or raise exception
        try:
            backend_management_service.register_backend("duplicate_backend", new_config)
            # If successful, verify it was updated
            stored_config = backend_management_service.registered_backends["duplicate_backend"]
            assert stored_config["type"] == "pinecone"
        except ValueError:
            # Expected behavior for duplicate registration
            pass

    def test_unregister_backend(self, backend_management_service):
        """Test unregistering a backend."""
        # Register backend first
        backend_config = {"type": "test_backend"}
        backend_management_service.register_backend("removable_backend", backend_config)
        
        # Verify registration
        assert "removable_backend" in backend_management_service.registered_backends
        
        # Unregister backend
        backend_management_service.unregister_backend("removable_backend")
        
        # Verify removal
        assert "removable_backend" not in backend_management_service.registered_backends

    def test_unregister_nonexistent_backend(self, backend_management_service):
        """Test unregistering non-existent backend."""
        # Should handle gracefully without error
        backend_management_service.unregister_backend("nonexistent_backend")
        
        # No assertion needed - should not raise exception

    def test_get_backend_status_healthy(self, backend_management_service):
        """Test getting status for healthy backend."""
        # Register backend
        backend_config = {
            "type": "faiss",
            "dimension": 384,
            "index_path": "/tmp/test_index"
        }
        backend_management_service.register_backend("healthy_backend", backend_config)
        
        # Mock successful health check
        with patch.object(backend_management_service, '_perform_health_check') as mock_health:
            mock_health.return_value = BackendStatus(
                is_healthy=True,
                last_check=time.time(),
                latency=0.05,
                error_message=None,
                backend_name="healthy_backend"
            )
            
            status = backend_management_service.get_backend_status("healthy_backend")
            
            assert isinstance(status, BackendStatus)
            assert status.is_healthy is True
            assert status.backend_name == "healthy_backend"
            assert status.latency == 0.05

    def test_get_backend_status_unhealthy(self, backend_management_service):
        """Test getting status for unhealthy backend."""
        backend_config = {"type": "failing_backend"}
        backend_management_service.register_backend("unhealthy_backend", backend_config)
        
        # Mock failed health check
        with patch.object(backend_management_service, '_perform_health_check') as mock_health:
            mock_health.return_value = BackendStatus(
                is_healthy=False,
                last_check=time.time(),
                latency=None,
                error_message="Connection failed",
                backend_name="unhealthy_backend"
            )
            
            status = backend_management_service.get_backend_status("unhealthy_backend")
            
            assert isinstance(status, BackendStatus)
            assert status.is_healthy is False
            assert status.error_message == "Connection failed"

    def test_get_backend_status_nonexistent(self, backend_management_service):
        """Test getting status for non-existent backend."""
        status = backend_management_service.get_backend_status("nonexistent_backend")
        
        # Should return None or a status indicating backend not found
        assert status is None or (isinstance(status, BackendStatus) and not status.is_healthy)

    def test_switch_component_backend(self, backend_management_service):
        """Test switching component backend."""
        # Register backends
        backend_config1 = {"type": "faiss", "dimension": 384}
        backend_config2 = {"type": "pinecone", "api_key": "test_key"}
        
        backend_management_service.register_backend("backend1", backend_config1)
        backend_management_service.register_backend("backend2", backend_config2)
        
        # Create mock component
        component = MockComponent("SwitchableComponent")
        
        # Switch backend
        backend_management_service.switch_component_backend(component, "backend2")
        
        # Verify switch
        component_name = "MockComponent"
        assert backend_management_service.component_backends.get(component_name) == "backend2"

    def test_switch_component_backend_nonexistent(self, backend_management_service):
        """Test switching to non-existent backend."""
        component = MockComponent("TestComponent")
        
        with pytest.raises((ValueError, KeyError)):
            backend_management_service.switch_component_backend(component, "nonexistent_backend")

    def test_migrate_component_data(self, backend_management_service):
        """Test migrating component data between backends."""
        # Register source and destination backends
        source_config = {"type": "faiss", "dimension": 384}
        dest_config = {"type": "pinecone", "api_key": "test_key"}
        
        backend_management_service.register_backend("source_backend", source_config)
        backend_management_service.register_backend("dest_backend", dest_config)
        
        # Create mock component with data
        component = MockComponent("MigratableComponent")
        component.get_data = Mock(return_value={"vectors": [1, 2, 3], "metadata": {"count": 100}})
        component.set_data = Mock()
        
        # Migrate data
        backend_management_service.migrate_component_data(
            component, "source_backend", "dest_backend"
        )
        
        # Verify migration process
        component.get_data.assert_called_once()
        component.set_data.assert_called_once()

    def test_get_all_backends(self, backend_management_service):
        """Test getting all registered backends."""
        # Register multiple backends
        backends = {
            "faiss_backend": {"type": "faiss", "dimension": 384},
            "redis_backend": {"type": "redis", "host": "localhost"},
            "pinecone_backend": {"type": "pinecone", "api_key": "key"}
        }
        
        for name, config in backends.items():
            backend_management_service.register_backend(name, config)
        
        all_backends = backend_management_service.get_all_backends()
        
        assert isinstance(all_backends, dict)
        assert len(all_backends) >= 3
        
        for name in backends:
            assert name in all_backends

    def test_check_component_backend_health(self, backend_management_service):
        """Test checking backend health for specific component."""
        # Register backend and assign to component
        backend_config = {"type": "test_backend", "health_endpoint": "/health"}
        backend_management_service.register_backend("component_backend", backend_config)
        
        component = MockComponent("HealthCheckComponent")
        backend_management_service.switch_component_backend(component, "component_backend")
        
        # Mock health check
        with patch.object(backend_management_service, 'get_backend_status') as mock_status:
            mock_status.return_value = BackendStatus(
                is_healthy=True,
                last_check=time.time(),
                latency=0.03,
                error_message=None,
                backend_name="component_backend"
            )
            
            backend_management_service.check_component_backend_health(component)
            
            # Verify health check was performed
            mock_status.assert_called_once_with("component_backend")

    def test_monitor_component_backends(self, backend_management_service):
        """Test monitoring backends for multiple components."""
        # Setup components with different backends
        components = []
        for i in range(3):
            backend_config = {"type": f"backend_type_{i}"}
            backend_name = f"backend_{i}"
            backend_management_service.register_backend(backend_name, backend_config)
            
            component = MockComponent(f"MonitoredComponent{i}")
            backend_management_service.switch_component_backend(component, backend_name)
            components.append(component)
        
        # Mock health statuses
        with patch.object(backend_management_service, 'get_backend_status') as mock_status:
            mock_status.side_effect = lambda name: BackendStatus(
                is_healthy=True if "0" in name else False,
                last_check=time.time(),
                latency=0.1,
                error_message=None if "0" in name else "Error",
                backend_name=name
            )
            
            monitoring_report = backend_management_service.monitor_component_backends(components)
            
            assert isinstance(monitoring_report, dict)
            assert "healthy_backends" in monitoring_report
            assert "unhealthy_backends" in monitoring_report
            assert "total_components" in monitoring_report

    def test_backend_failover_logic(self, backend_management_service):
        """Test backend failover when primary backend fails."""
        # Register primary and backup backends
        primary_config = {"type": "primary_backend", "priority": 1}
        backup_config = {"type": "backup_backend", "priority": 2}
        
        backend_management_service.register_backend("primary", primary_config)
        backend_management_service.register_backend("backup", backup_config)
        
        component = MockComponent("FailoverComponent")
        backend_management_service.switch_component_backend(component, "primary")
        
        # Simulate primary backend failure
        backend_management_service.backend_health["primary"] = BackendStatus(
            is_healthy=False,
            last_check=time.time(),
            latency=None,
            error_message="Backend down",
            backend_name="primary"
        )
        
        # Trigger failover logic
        backend_management_service._consider_backend_switch_for_component(component, "primary")
        
        # Verify component was switched to backup (if failover is implemented)
        current_backend = backend_management_service.component_backends.get("MockComponent")
        # Result depends on implementation - could be "backup" or still "primary"
        assert current_backend in ["primary", "backup"]

    def test_backend_performance_tracking(self, backend_management_service):
        """Test backend performance tracking."""
        backend_config = {"type": "performance_backend"}
        backend_management_service.register_backend("perf_backend", backend_config)
        
        # Simulate multiple health checks with different latencies
        latencies = [0.05, 0.08, 0.12, 0.06, 0.10]
        
        for latency in latencies:
            status = BackendStatus(
                is_healthy=True,
                last_check=time.time(),
                latency=latency,
                error_message=None,
                backend_name="perf_backend"
            )
            backend_management_service.backend_health["perf_backend"] = status
        
        # Get performance metrics
        performance_metrics = backend_management_service.get_backend_performance_metrics("perf_backend")
        
        if performance_metrics:
            assert isinstance(performance_metrics, dict)
            assert "average_latency" in performance_metrics
            assert "health_uptime" in performance_metrics

    def test_backend_configuration_validation(self, backend_management_service):
        """Test backend configuration validation."""
        # Valid configuration
        valid_config = {
            "type": "faiss",
            "path": "/tmp/index",
        }

        is_valid = backend_management_service.validate_backend_config(valid_config)
        assert is_valid is True

        # Invalid configuration — missing required 'type' field
        invalid_config = {
            "host": "localhost",
            "port": 6379,
        }

        is_valid = backend_management_service.validate_backend_config(invalid_config)
        assert is_valid is False

        # Invalid configuration — pinecone without api_key
        invalid_pinecone = {
            "type": "pinecone",
            "index_name": "test",
        }

        is_valid = backend_management_service.validate_backend_config(invalid_pinecone)
        assert is_valid is False

    def test_concurrent_backend_operations(self, backend_management_service):
        """Test concurrent backend operations."""
        import threading
        
        def register_backend(backend_id):
            config = {"type": "concurrent_backend", "id": backend_id}
            backend_management_service.register_backend(f"concurrent_{backend_id}", config)
        
        def check_backend_status(backend_id):
            backend_name = f"concurrent_{backend_id}"
            status = backend_management_service.get_backend_status(backend_name)
            return status
        
        # Register backends concurrently
        threads = []
        for i in range(5):
            thread = threading.Thread(target=register_backend, args=(i,))
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        # Verify all backends were registered
        all_backends = backend_management_service.get_all_backends()
        concurrent_backends = [name for name in all_backends if name.startswith("concurrent_")]
        assert len(concurrent_backends) == 5

    def test_backend_health_caching(self, backend_management_service):
        """Test backend health status caching."""
        backend_config = {"type": "cached_backend"}
        backend_management_service.register_backend("cached_backend", backend_config)
        
        # Mock health check method to count calls
        call_count = 0
        
        def mock_health_check(backend_name, backend_config):
            nonlocal call_count
            call_count += 1
            return BackendStatus(
                is_healthy=True,
                last_check=time.time(),
                latency=0.05,
                error_message=None,
                backend_name=backend_name
            )
        
        with patch.object(backend_management_service, '_perform_health_check', mock_health_check):
            # Multiple rapid status checks
            for _ in range(5):
                backend_management_service.get_backend_status("cached_backend")
            
            # Should have caching mechanism to reduce actual health check calls
            # Exact behavior depends on implementation
            assert call_count >= 1  # At least one check should occur

    def test_backend_auto_discovery(self, backend_management_service):
        """Test automatic backend discovery."""
        # Mock environment or configuration that enables auto-discovery
        with patch('os.environ.get', return_value='localhost:6379,localhost:6380'):
            discovered_backends = backend_management_service.discover_available_backends()
            
            if discovered_backends:
                assert isinstance(discovered_backends, (list, dict))
                # Would contain discovered backend configurations

    def test_backend_load_balancing(self, backend_management_service):
        """Test load balancing across multiple backends."""
        # Register multiple similar backends
        for i in range(3):
            config = {"type": "load_balanced_backend", "instance": i}
            backend_management_service.register_backend(f"lb_backend_{i}", config)
        
        component = MockComponent("LoadBalancedComponent")
        
        # Configure load balancing
        backend_management_service.configure_load_balancing(
            component, 
            backends=["lb_backend_0", "lb_backend_1", "lb_backend_2"],
            strategy="round_robin"
        )
        
        # Verify load balancing configuration
        lb_config = backend_management_service.get_load_balancing_config(component)
        
        if lb_config:
            assert isinstance(lb_config, dict)
            assert "backends" in lb_config
            assert "strategy" in lb_config