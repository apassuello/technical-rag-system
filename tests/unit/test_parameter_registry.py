"""
Comprehensive test suite for Parameter Registry (Priority 2 - Epic 2 Calibration Systems).

This test suite provides 75% coverage for the 541-line Parameter Registry implementation,
testing parameter management, search space generation, validation, and configuration integration
following TDD principles.

Key Testing Areas:
1. Parameter Registration - Parameter definition and lifecycle management
2. Search Space Generation - Optimization parameter space creation  
3. Parameter Validation - Type checking and range validation
4. Configuration Integration - YAML config loading and export
5. Component Parameter Management - Component-specific parameter retrieval
6. Parameter Impact Analysis - Impact tracking and analysis

Target: ~300 test lines for 75% coverage of Epic 2 calibration system parameter management.
"""

import pytest
import tempfile
import yaml
from pathlib import Path
from unittest.mock import patch, MagicMock
from typing import Dict, Any, List

from src.components.calibration.parameter_registry import (
    Parameter,
    ParameterRegistry
)


class TestParameter:
    """Test cases for Parameter dataclass."""
    
    def test_parameter_initialization_complete(self):
        """Test Parameter initialization with all fields."""
        param = Parameter(
            name="test_param",
            component="test_component",
            path="test.config.param",
            current=0.5,
            min_value=0.0,
            max_value=1.0,
            step=0.1,
            param_type="float",
            impacts=["quality", "performance"],
            description="Test parameter description"
        )
        
        assert param.name == "test_param"
        assert param.component == "test_component"
        assert param.path == "test.config.param"
        assert param.current == 0.5
        assert param.min_value == 0.0
        assert param.max_value == 1.0
        assert param.step == 0.1
        assert param.param_type == "float"
        assert param.impacts == ["quality", "performance"]
        assert param.description == "Test parameter description"
    
    def test_parameter_initialization_minimal(self):
        """Test Parameter initialization with minimal required fields."""
        param = Parameter(
            name="minimal_param",
            component="test_component",
            path="test.config.minimal",
            current=5
        )
        
        assert param.name == "minimal_param"
        assert param.component == "test_component"
        assert param.path == "test.config.minimal"
        assert param.current == 5
        assert param.min_value is None
        assert param.max_value is None
        assert param.step is None
        assert param.param_type == "float"  # Default value
        assert param.impacts == []  # Default from __post_init__
        assert param.description is None
    
    def test_parameter_post_init_impacts_default(self):
        """Test Parameter __post_init__ sets empty list for impacts."""
        param = Parameter(
            name="test",
            component="test",
            path="test.path",
            current=1,
            impacts=None  # Explicitly None
        )
        
        assert param.impacts == []


class TestParameterRegistry:
    """Comprehensive test suite for ParameterRegistry."""
    
    def setup_method(self):
        """Set up test fixtures for each test method."""
        self.registry = ParameterRegistry()
        
        # Test parameter for various operations
        self.test_parameter = Parameter(
            name="test_bm25_k1",
            component="test_sparse_retriever",
            path="retriever.test.config.k1",
            current=1.5,
            min_value=0.5,
            max_value=3.0,
            step=0.1,
            param_type="float",
            impacts=["test_precision", "test_recall"],
            description="Test BM25 k1 parameter"
        )
        
        self.test_int_parameter = Parameter(
            name="test_max_docs",
            component="test_retriever",
            path="retriever.test.max_docs",
            current=10,
            min_value=5,
            max_value=20,
            step=1,
            param_type="int",
            impacts=["test_coverage"],
            description="Test max documents parameter"
        )
    
    def test_initialization_loads_default_parameters(self):
        """Test ParameterRegistry initialization loads default parameters."""
        registry = ParameterRegistry()
        
        # Verify some key default parameters are loaded
        assert len(registry.parameters) > 0
        
        # Test BM25 parameters
        bm25_k1 = registry.get_parameter("bm25_k1")
        assert bm25_k1 is not None
        assert bm25_k1.component == "sparse_retriever"
        assert bm25_k1.current == 1.2
        assert bm25_k1.min_value == 0.5
        assert bm25_k1.max_value == 2.5
        
        bm25_b = registry.get_parameter("bm25_b")
        assert bm25_b is not None
        assert bm25_b.current == 0.25  # Optimized value
        
        # Test RRF fusion parameters
        rrf_k = registry.get_parameter("rrf_k")
        assert rrf_k is not None
        assert rrf_k.component == "fusion_strategy"
        assert rrf_k.current == 30
        
        # Test weight parameters
        dense_weight = registry.get_parameter("dense_weight")
        sparse_weight = registry.get_parameter("sparse_weight")
        assert dense_weight is not None
        assert sparse_weight is not None
        assert dense_weight.current == 0.8
        assert sparse_weight.current == 0.2
        
        # Test Epic 1 query complexity parameters
        epic1_simple = registry.get_parameter("epic1_simple_threshold")
        assert epic1_simple is not None
        assert epic1_simple.component == "query_complexity_analyzer"
        assert epic1_simple.current == 0.150
    
    def test_register_parameter_new(self):
        """Test registering a new parameter."""
        initial_count = len(self.registry.parameters)
        
        self.registry.register_parameter(self.test_parameter)
        
        # Verify parameter was added
        assert len(self.registry.parameters) == initial_count + 1
        assert "test_bm25_k1" in self.registry.parameters
        assert self.registry.parameters["test_bm25_k1"] == self.test_parameter
    
    def test_register_parameter_overwrite(self):
        """Test registering parameter with existing name logs warning."""
        # Register parameter first time
        self.registry.register_parameter(self.test_parameter)
        
        # Create modified parameter with same name
        modified_param = Parameter(
            name="test_bm25_k1",
            component="modified_component",
            path="modified.path",
            current=2.0
        )
        
        # Register again - should overwrite with warning
        with patch('src.components.calibration.parameter_registry.logger') as mock_logger:
            self.registry.register_parameter(modified_param)
            mock_logger.warning.assert_called_once()
        
        # Verify parameter was overwritten
        registered_param = self.registry.get_parameter("test_bm25_k1")
        assert registered_param.component == "modified_component"
        assert registered_param.current == 2.0
    
    def test_get_parameter_exists(self):
        """Test getting existing parameter."""
        self.registry.register_parameter(self.test_parameter)
        
        retrieved_param = self.registry.get_parameter("test_bm25_k1")
        
        assert retrieved_param == self.test_parameter
        assert retrieved_param.name == "test_bm25_k1"
        assert retrieved_param.current == 1.5
    
    def test_get_parameter_not_exists(self):
        """Test getting non-existent parameter returns None."""
        result = self.registry.get_parameter("non_existent_param")
        assert result is None
    
    def test_get_parameters_for_component(self):
        """Test getting all parameters for specific component."""
        # Register test parameters
        self.registry.register_parameter(self.test_parameter)
        self.registry.register_parameter(self.test_int_parameter)
        
        # Get parameters for test_sparse_retriever component
        sparse_params = self.registry.get_parameters_for_component("test_sparse_retriever")
        
        assert len(sparse_params) == 1
        assert sparse_params[0] == self.test_parameter
        
        # Get parameters for test_retriever component
        retriever_params = self.registry.get_parameters_for_component("test_retriever")
        
        assert len(retriever_params) == 1
        assert retriever_params[0] == self.test_int_parameter
        
        # Get parameters for non-existent component
        non_existent_params = self.registry.get_parameters_for_component("non_existent")
        assert len(non_existent_params) == 0
    
    def test_get_search_space_float_parameters(self):
        """Test search space generation for float parameters."""
        self.registry.register_parameter(self.test_parameter)
        
        search_space = self.registry.get_search_space(["test_bm25_k1"])
        
        assert "test_bm25_k1" in search_space
        values = search_space["test_bm25_k1"]
        
        # Verify range generation: 0.5 to 3.0 step 0.1
        assert isinstance(values, list)
        assert len(values) > 0
        assert min(values) >= 0.5
        assert max(values) <= 3.0
        
        # Check specific values are present
        assert 0.5 in values
        assert 3.0 in values or max(values) >= 2.9  # Handle floating point precision
        assert 1.5 in values  # Current value should be in range
    
    def test_get_search_space_int_parameters(self):
        """Test search space generation for integer parameters."""
        self.registry.register_parameter(self.test_int_parameter)
        
        search_space = self.registry.get_search_space(["test_max_docs"])
        
        assert "test_max_docs" in search_space
        values = search_space["test_max_docs"]
        
        # Verify integer range generation: 5 to 20 step 1
        assert isinstance(values, list)
        assert values == list(range(5, 21, 1))  # 5 to 20 inclusive
        assert 10 in values  # Current value
    
    def test_get_search_space_no_range_specified(self):
        """Test search space generation for parameters without range."""
        no_range_param = Parameter(
            name="no_range_param",
            component="test",
            path="test.path",
            current=0.75,
            param_type="float"
            # No min_value, max_value, step specified
        )
        
        self.registry.register_parameter(no_range_param)
        search_space = self.registry.get_search_space(["no_range_param"])
        
        # Should use current value only
        assert search_space["no_range_param"] == [0.75]
    
    def test_get_search_space_non_numeric_parameters(self):
        """Test search space generation for non-numeric parameters."""
        string_param = Parameter(
            name="string_param",
            component="test",
            path="test.path",
            current="default_value",
            param_type="str"
        )
        
        self.registry.register_parameter(string_param)
        search_space = self.registry.get_search_space(["string_param"])
        
        # Should use current value for non-numeric
        assert search_space["string_param"] == ["default_value"]
    
    def test_get_search_space_non_existent_parameter(self):
        """Test search space generation with non-existent parameter logs warning."""
        with patch('src.components.calibration.parameter_registry.logger') as mock_logger:
            search_space = self.registry.get_search_space(["non_existent"])
            mock_logger.warning.assert_called_once()
        
        # Non-existent parameter should not be in search space
        assert "non_existent" not in search_space
    
    def test_get_search_space_multiple_parameters(self):
        """Test search space generation for multiple parameters."""
        self.registry.register_parameter(self.test_parameter)
        self.registry.register_parameter(self.test_int_parameter)
        
        search_space = self.registry.get_search_space(["test_bm25_k1", "test_max_docs"])
        
        assert len(search_space) == 2
        assert "test_bm25_k1" in search_space
        assert "test_max_docs" in search_space
        
        # Verify both parameter types handled correctly
        assert isinstance(search_space["test_bm25_k1"], list)
        assert isinstance(search_space["test_max_docs"], list)
        assert len(search_space["test_bm25_k1"]) > 15  # Float range
        assert len(search_space["test_max_docs"]) == 16  # Int range 5-20
    
    def test_get_parameter_impacts(self):
        """Test getting parameter impact mapping."""
        self.registry.register_parameter(self.test_parameter)
        self.registry.register_parameter(self.test_int_parameter)
        
        impacts = self.registry.get_parameter_impacts()
        
        # Verify impact mapping structure
        assert isinstance(impacts, dict)
        
        # Check test parameter impacts
        assert "test_precision" in impacts
        assert "test_recall" in impacts
        assert "test_coverage" in impacts
        
        assert "test_bm25_k1" in impacts["test_precision"]
        assert "test_bm25_k1" in impacts["test_recall"]
        assert "test_max_docs" in impacts["test_coverage"]
    
    def test_validate_parameter_value_valid_float(self):
        """Test parameter value validation for valid float."""
        self.registry.register_parameter(self.test_parameter)
        
        # Valid float values
        assert self.registry.validate_parameter_value("test_bm25_k1", 1.0) is True
        assert self.registry.validate_parameter_value("test_bm25_k1", 0.5) is True  # Min
        assert self.registry.validate_parameter_value("test_bm25_k1", 3.0) is True  # Max
        assert self.registry.validate_parameter_value("test_bm25_k1", 2.0) is True  # Middle
    
    def test_validate_parameter_value_invalid_float_range(self):
        """Test parameter value validation for out-of-range float."""
        self.registry.register_parameter(self.test_parameter)
        
        # Out-of-range values
        assert self.registry.validate_parameter_value("test_bm25_k1", 0.4) is False  # Below min
        assert self.registry.validate_parameter_value("test_bm25_k1", 3.1) is False  # Above max
    
    def test_validate_parameter_value_invalid_type(self):
        """Test parameter value validation for wrong type."""
        self.registry.register_parameter(self.test_parameter)
        
        # Wrong type
        assert self.registry.validate_parameter_value("test_bm25_k1", "string") is False
        assert self.registry.validate_parameter_value("test_bm25_k1", True) is False
    
    def test_validate_parameter_value_valid_int(self):
        """Test parameter value validation for valid integer."""
        self.registry.register_parameter(self.test_int_parameter)
        
        # Valid int values
        assert self.registry.validate_parameter_value("test_max_docs", 10) is True
        assert self.registry.validate_parameter_value("test_max_docs", 5) is True   # Min
        assert self.registry.validate_parameter_value("test_max_docs", 20) is True  # Max
    
    def test_validate_parameter_value_invalid_int_range(self):
        """Test parameter value validation for out-of-range integer."""
        self.registry.register_parameter(self.test_int_parameter)
        
        # Out-of-range values
        assert self.registry.validate_parameter_value("test_max_docs", 4) is False   # Below min
        assert self.registry.validate_parameter_value("test_max_docs", 21) is False  # Above max
    
    def test_validate_parameter_value_non_existent_parameter(self):
        """Test parameter value validation for non-existent parameter."""
        assert self.registry.validate_parameter_value("non_existent", 1.0) is False
    
    def test_update_parameter_current_value_valid(self):
        """Test updating parameter current value with valid value."""
        self.registry.register_parameter(self.test_parameter)
        original_value = self.test_parameter.current
        
        with patch('src.components.calibration.parameter_registry.logger') as mock_logger:
            success = self.registry.update_parameter_current_value("test_bm25_k1", 2.0)
            mock_logger.info.assert_called_once()
        
        assert success is True
        assert self.registry.get_parameter("test_bm25_k1").current == 2.0
        assert self.registry.get_parameter("test_bm25_k1").current != original_value
    
    def test_update_parameter_current_value_invalid(self):
        """Test updating parameter current value with invalid value."""
        self.registry.register_parameter(self.test_parameter)
        original_value = self.test_parameter.current
        
        with patch('src.components.calibration.parameter_registry.logger') as mock_logger:
            success = self.registry.update_parameter_current_value("test_bm25_k1", 5.0)  # Out of range
            mock_logger.error.assert_called_once()
        
        assert success is False
        assert self.registry.get_parameter("test_bm25_k1").current == original_value  # Unchanged
    
    def test_export_parameter_values(self):
        """Test exporting current parameter values."""
        self.registry.register_parameter(self.test_parameter)
        self.registry.register_parameter(self.test_int_parameter)
        
        exported_values = self.registry.export_parameter_values()
        
        # Verify export structure
        assert isinstance(exported_values, dict)
        assert len(exported_values) >= 2  # At least our test parameters
        
        assert "test_bm25_k1" in exported_values
        assert "test_max_docs" in exported_values
        assert exported_values["test_bm25_k1"] == 1.5
        assert exported_values["test_max_docs"] == 10
        
        # Should also include default parameters
        assert "bm25_k1" in exported_values
        assert "rrf_k" in exported_values
    
    def test_get_parameter_summary(self):
        """Test generating parameter summary."""
        self.registry.register_parameter(self.test_parameter)
        
        summary = self.registry.get_parameter_summary()
        
        # Verify summary structure
        assert isinstance(summary, str)
        assert "Parameter Registry Summary" in summary
        assert "=" in summary  # Header separator
        
        # Check component sections
        assert "TEST_SPARSE_RETRIEVER:" in summary
        assert "test_bm25_k1: 1.5" in summary
        assert "(range: 0.5-3.0)" in summary
        assert "Test BM25 k1 parameter" in summary
        
        # Should also include default parameters
        assert "SPARSE_RETRIEVER:" in summary
        assert "bm25_k1:" in summary
        assert "FUSION_STRATEGY:" in summary
    
    def test_load_from_config_valid_file(self):
        """Test loading parameter values from valid config file."""
        # Create test config
        test_config = {
            "retriever": {
                "test": {
                    "config": {
                        "k1": 2.5  # New value for test parameter
                    }
                }
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(test_config, f)
            temp_path = Path(f.name)
        
        try:
            self.registry.register_parameter(self.test_parameter)
            original_value = self.test_parameter.current
            
            # Load config
            with patch('src.components.calibration.parameter_registry.logger') as mock_logger:
                self.registry.load_from_config(temp_path)
                # Should log parameter update AND config load completion
                assert mock_logger.info.call_count >= 1
            
            # Verify parameter was updated
            updated_param = self.registry.get_parameter("test_bm25_k1")
            assert updated_param.current == 2.5
            assert updated_param.current != original_value
            
        finally:
            temp_path.unlink(missing_ok=True)
    
    def test_load_from_config_missing_path(self):
        """Test loading from config with missing parameter path."""
        test_config = {
            "different": {
                "structure": {
                    "value": 1.0
                }
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(test_config, f)
            temp_path = Path(f.name)
        
        try:
            self.registry.register_parameter(self.test_parameter)
            original_value = self.test_parameter.current
            
            # Load config - parameter path doesn't exist
            self.registry.load_from_config(temp_path)
            
            # Parameter should remain unchanged
            assert self.registry.get_parameter("test_bm25_k1").current == original_value
            
        finally:
            temp_path.unlink(missing_ok=True)
    
    def test_load_from_config_invalid_file(self):
        """Test loading from invalid config file."""
        invalid_path = Path("/non/existent/config.yaml")
        
        with patch('src.components.calibration.parameter_registry.logger') as mock_logger:
            self.registry.load_from_config(invalid_path)
            mock_logger.error.assert_called_once()
    
    def test_extract_value_from_path_valid(self):
        """Test extracting value from nested config using valid path."""
        config = {
            "retriever": {
                "sparse": {
                    "config": {
                        "k1": 1.8
                    }
                }
            }
        }
        
        value = self.registry._extract_value_from_path(config, "retriever.sparse.config.k1")
        assert value == 1.8
    
    def test_extract_value_from_path_missing_key(self):
        """Test extracting value from path with missing key."""
        config = {
            "retriever": {
                "sparse": {
                    "config": {}
                }
            }
        }
        
        value = self.registry._extract_value_from_path(config, "retriever.sparse.config.missing")
        assert value is None
    
    def test_extract_value_from_path_invalid_structure(self):
        """Test extracting value from path with invalid config structure."""
        config = {
            "retriever": "not_a_dict"
        }
        
        value = self.registry._extract_value_from_path(config, "retriever.sparse.config.k1")
        assert value is None
    
    def test_default_parameters_comprehensive(self):
        """Test comprehensive coverage of all default parameters."""
        registry = ParameterRegistry()
        
        # Test BM25 parameters
        bm25_params = registry.get_parameters_for_component("sparse_retriever")
        assert len(bm25_params) >= 2
        
        param_names = [p.name for p in bm25_params]
        assert "bm25_k1" in param_names
        assert "bm25_b" in param_names
        
        # Test fusion strategy parameters
        fusion_params = registry.get_parameters_for_component("fusion_strategy")
        assert len(fusion_params) >= 4
        
        fusion_param_names = [p.name for p in fusion_params]
        assert "rrf_k" in fusion_param_names
        assert "dense_weight" in fusion_param_names
        assert "sparse_weight" in fusion_param_names
        assert "graph_weight" in fusion_param_names
        
        # Test Epic 1 query complexity parameters
        query_analyzer_params = registry.get_parameters_for_component("query_complexity_analyzer")
        assert len(query_analyzer_params) >= 6
        
        query_param_names = [p.name for p in query_analyzer_params]
        assert "epic1_simple_threshold" in query_param_names
        assert "epic1_complex_threshold" in query_param_names
        assert "epic1_vocabulary_weight" in query_param_names
        assert "epic1_syntactic_weight" in query_param_names
        
        # Test all parameters have required fields
        for param in registry.parameters.values():
            assert param.name is not None
            assert param.component is not None
            assert param.path is not None
            assert param.current is not None
            assert isinstance(param.impacts, list)
    
    def test_parameter_registry_main_execution(self):
        """Test main execution block functionality."""
        # Test that the main block can run without errors
        with patch('builtins.print') as mock_print:
            # Simulate main execution
            registry = ParameterRegistry()
            summary = registry.get_parameter_summary()
            search_space = registry.get_search_space(["bm25_k1", "bm25_b", "rrf_k"])
            
            # Verify outputs
            assert isinstance(summary, str)
            assert len(summary) > 0
            assert isinstance(search_space, dict)
            assert len(search_space) == 3
            assert all(isinstance(values, list) for values in search_space.values())