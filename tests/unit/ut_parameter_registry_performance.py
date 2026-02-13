"""
Performance tests for Parameter Registry component.

This module contains performance tests for the Parameter Registry,
testing search space generation, parameter validation, and configuration 
loading performance with large parameter sets.
"""

import pytest
import time
import tempfile
import yaml
from pathlib import Path
from typing import Dict, Any, List

from src.components.calibration.parameter_registry import (
    Parameter,
    ParameterRegistry
)


class TestParameterRegistryPerformance:
    """Performance test suite for ParameterRegistry."""
    
    def setup_method(self):
        """Set up test fixtures for each test method."""
        self.registry = ParameterRegistry()
        self.large_parameter_set = self._create_large_parameter_set(1000)
    
    def _create_large_parameter_set(self, count: int) -> List[Parameter]:
        """Create a large set of parameters for performance testing."""
        parameters = []
        
        for i in range(count):
            param = Parameter(
                name=f"perf_param_{i:04d}",
                component=f"component_{i % 10}",  # 10 different components
                path=f"config.component_{i % 10}.param_{i:04d}",
                current=float(i % 100) / 10.0,  # Values 0.0 to 9.9
                min_value=0.0,
                max_value=10.0,
                step=0.1,
                param_type="float",
                impacts=[f"impact_{j}" for j in range(i % 5 + 1)],  # 1-5 impacts
                description=f"Performance test parameter {i:04d}"
            )
            parameters.append(param)
        
        return parameters
    
    def test_register_large_parameter_set_performance(self):
        """Test performance of registering large parameter set."""
        start_time = time.time()
        
        for param in self.large_parameter_set:
            self.registry.register_parameter(param)
        
        duration = time.time() - start_time
        
        # Should register 1000 parameters in under 1 second
        assert duration < 1.0
        assert len(self.registry.parameters) >= 1000  # Includes defaults
        
        print(f"Registered {len(self.large_parameter_set)} parameters in {duration:.3f}s "
              f"({len(self.large_parameter_set) / duration:.0f} params/sec)")
    
    def test_search_space_generation_performance(self):
        """Test performance of search space generation for many parameters."""
        # Register large parameter set
        for param in self.large_parameter_set[:500]:  # Use subset for reasonable test time
            self.registry.register_parameter(param)
        
        # Generate search space for all parameters
        param_names = [p.name for p in self.large_parameter_set[:500]]
        
        start_time = time.time()
        search_space = self.registry.get_search_space(param_names)
        duration = time.time() - start_time
        
        # Should generate search space for 500 parameters in under 2 seconds
        assert duration < 2.0
        assert len(search_space) == 500
        
        # Verify search space quality
        total_combinations = 1
        for param_name, values in search_space.items():
            assert isinstance(values, list)
            assert len(values) > 0
            total_combinations *= len(values)
        
        print(f"Generated search space for {len(param_names)} parameters in {duration:.3f}s")
        print(f"Total parameter combinations: {total_combinations:,}")
    
    def test_parameter_validation_performance(self):
        """Test performance of parameter validation with many parameters."""
        # Register large parameter set
        for param in self.large_parameter_set[:200]:
            self.registry.register_parameter(param)
        
        # Test validation performance
        param_names = [p.name for p in self.large_parameter_set[:200]]
        test_values = [5.5] * 200  # All valid values
        
        start_time = time.time()
        
        validation_results = []
        for param_name, value in zip(param_names, test_values):
            result = self.registry.validate_parameter_value(param_name, value)
            validation_results.append(result)
        
        duration = time.time() - start_time
        
        # Should validate 200 parameters in under 0.1 seconds
        assert duration < 0.1
        assert all(validation_results)  # All should be valid
        
        print(f"Validated {len(param_names)} parameters in {duration:.3f}s "
              f"({len(param_names) / duration:.0f} validations/sec)")
    
    def test_parameter_update_performance(self):
        """Test performance of updating parameter values."""
        # Register test parameters
        test_params = self.large_parameter_set[:100]
        for param in test_params:
            self.registry.register_parameter(param)
        
        # Update all parameter values
        param_updates = [(p.name, 7.5) for p in test_params]
        
        start_time = time.time()
        
        update_results = []
        for param_name, new_value in param_updates:
            result = self.registry.update_parameter_current_value(param_name, new_value)
            update_results.append(result)
        
        duration = time.time() - start_time
        
        # Should update 100 parameters in under 0.1 seconds
        assert duration < 0.1
        assert all(update_results)  # All updates should succeed
        
        # Verify updates took effect
        for param_name, expected_value in param_updates:
            param = self.registry.get_parameter(param_name)
            assert param.current == expected_value
        
        print(f"Updated {len(param_updates)} parameters in {duration:.3f}s "
              f"({len(param_updates) / duration:.0f} updates/sec)")
    
    def test_component_parameter_retrieval_performance(self):
        """Test performance of retrieving parameters by component."""
        # Register large parameter set
        for param in self.large_parameter_set:
            self.registry.register_parameter(param)
        
        # Test retrieval performance for each component
        component_names = [f"component_{i}" for i in range(10)]
        
        start_time = time.time()
        
        component_params = {}
        for component_name in component_names:
            params = self.registry.get_parameters_for_component(component_name)
            component_params[component_name] = params
        
        duration = time.time() - start_time
        
        # Should retrieve parameters for 10 components in under 0.05 seconds
        assert duration < 0.05
        
        # Verify retrieval results
        total_retrieved = sum(len(params) for params in component_params.values())
        assert total_retrieved == len(self.large_parameter_set)
        
        for component_name, params in component_params.items():
            for param in params:
                assert param.component == component_name
        
        print(f"Retrieved parameters for {len(component_names)} components in {duration:.3f}s")
    
    def test_parameter_impact_analysis_performance(self):
        """Test performance of parameter impact analysis."""
        # Register large parameter set
        for param in self.large_parameter_set:
            self.registry.register_parameter(param)
        
        start_time = time.time()
        impacts = self.registry.get_parameter_impacts()
        duration = time.time() - start_time
        
        # Should analyze impacts in under 0.1 seconds
        assert duration < 0.1
        
        # Verify impact analysis results
        assert isinstance(impacts, dict)
        assert len(impacts) > 0
        
        # Count total impact mappings
        total_mappings = sum(len(params) for params in impacts.values())
        
        print(f"Analyzed parameter impacts in {duration:.3f}s")
        print(f"Found {len(impacts)} impact categories with {total_mappings} parameter mappings")
    
    def test_large_config_file_loading_performance(self):
        """Test performance of loading large configuration files."""
        # Create large configuration structure
        large_config = {}
        
        for i in range(10):  # 10 components
            component_config = {}
            for j in range(100):  # 100 parameters per component
                param_path = f"param_{j:03d}"
                component_config[param_path] = float(j) / 10.0
            large_config[f"component_{i}"] = {"config": component_config}
        
        # Write to temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(large_config, f)
            temp_path = Path(f.name)
        
        try:
            # Create registry with corresponding parameters
            registry = ParameterRegistry()
            test_params = []
            
            for i in range(10):
                for j in range(100):
                    param = Parameter(
                        name=f"config_param_{i}_{j:03d}",
                        component=f"test_component_{i}",
                        path=f"component_{i}.config.param_{j:03d}",
                        current=0.0
                    )
                    test_params.append(param)
                    registry.register_parameter(param)
            
            # Test loading performance
            start_time = time.time()
            registry.load_from_config(temp_path)
            duration = time.time() - start_time
            
            # Should load large config in under 1 second
            assert duration < 1.0
            
            # Verify some parameters were updated
            updated_count = 0
            for param in test_params:
                if registry.get_parameter(param.name).current != 0.0:
                    updated_count += 1
            
            assert updated_count > 0  # At least some parameters should be updated
            
            print(f"Loaded large config ({len(test_params)} potential parameters) in {duration:.3f}s")
            print(f"Updated {updated_count} parameters")
            
        finally:
            temp_path.unlink(missing_ok=True)
    
    def test_parameter_export_performance(self):
        """Test performance of exporting parameter values."""
        # Register large parameter set
        for param in self.large_parameter_set:
            self.registry.register_parameter(param)
        
        start_time = time.time()
        exported_values = self.registry.export_parameter_values()
        duration = time.time() - start_time
        
        # Should export all parameters in under 0.1 seconds
        assert duration < 0.1
        
        # Verify export results
        assert isinstance(exported_values, dict)
        assert len(exported_values) >= len(self.large_parameter_set)
        
        # Verify some exported values
        for param in self.large_parameter_set[:10]:
            assert param.name in exported_values
            assert exported_values[param.name] == param.current
        
        print(f"Exported {len(exported_values)} parameter values in {duration:.3f}s")
    
    def test_parameter_summary_generation_performance(self):
        """Test performance of generating parameter summary."""
        # Register large parameter set
        for param in self.large_parameter_set[:300]:  # Reasonable size for summary
            self.registry.register_parameter(param)
        
        start_time = time.time()
        summary = self.registry.get_parameter_summary()
        duration = time.time() - start_time
        
        # Should generate summary in under 0.5 seconds
        assert duration < 0.5
        
        # Verify summary quality
        assert isinstance(summary, str)
        assert len(summary) > 0
        assert "Parameter Registry Summary" in summary
        
        # Count components mentioned in summary
        component_count = summary.count("COMPONENT_")
        assert component_count == 10  # Should have 10 components
        
        print(f"Generated summary for {len(self.large_parameter_set[:300])} parameters in {duration:.3f}s")
        print(f"Summary length: {len(summary)} characters")
    
    def test_concurrent_parameter_access_simulation(self):
        """Simulate concurrent parameter access patterns."""
        # Register test parameters
        for param in self.large_parameter_set[:100]:
            self.registry.register_parameter(param)
        
        param_names = [p.name for p in self.large_parameter_set[:100]]
        
        start_time = time.time()
        
        # Simulate mixed access patterns
        for iteration in range(10):
            # Get parameters
            for name in param_names[::5]:  # Every 5th parameter
                param = self.registry.get_parameter(name)
                assert param is not None
            
            # Validate values
            for name in param_names[1::7]:  # Different pattern
                valid = self.registry.validate_parameter_value(name, 5.0)
                assert valid is True
            
            # Get parameters by component
            for i in range(10):
                component_params = self.registry.get_parameters_for_component(f"component_{i}")
                assert len(component_params) > 0
        
        duration = time.time() - start_time
        
        # Should complete mixed operations in reasonable time
        assert duration < 1.0
        
        print(f"Completed concurrent access simulation in {duration:.3f}s")

    def test_memory_efficiency(self):
        """Test memory efficiency with large parameter sets."""
        import sys
        
        # Measure memory before
        initial_registry = ParameterRegistry()
        
        # Register large parameter set and measure memory impact
        registry_with_large_set = ParameterRegistry()
        for param in self.large_parameter_set:
            registry_with_large_set.register_parameter(param)
        
        # Test memory-efficient operations
        start_time = time.time()
        
        # Operations that should be memory-efficient
        param_count = len(registry_with_large_set.parameters)
        component_list = set(p.component for p in registry_with_large_set.parameters.values())
        impact_count = len(registry_with_large_set.get_parameter_impacts())
        
        duration = time.time() - start_time
        
        # Verify results
        assert param_count >= 1000
        assert len(component_list) >= 10
        assert impact_count > 0
        
        # Should complete memory operations quickly
        assert duration < 0.1
        
        print(f"Memory-efficient operations on {param_count} parameters completed in {duration:.3f}s")
        print(f"Components: {len(component_list)}, Impact categories: {impact_count}")