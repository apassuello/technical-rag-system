"""
Test Configuration Management

Handles test suite definitions and execution parameters.
Built on existing configuration patterns with Epic-specific enhancements.
"""

import yaml
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass


@dataclass
class TestSuiteConfig:
    """Configuration for a test suite."""
    name: str
    description: str
    patterns: List[str]
    markers: List[str] = None
    timeout: int = 300
    parallel: bool = False
    coverage: bool = False
    epic: Optional[str] = None


@dataclass
class TestRunConfig:
    """Configuration for a test run."""
    suites: List[TestSuiteConfig]
    output_format: str = "terminal"
    verbose: bool = True
    fail_fast: bool = False
    capture: str = "no"


class TestConfig:
    """Test configuration manager."""
    
    def __init__(self, config_file: Optional[Path] = None):
        """Initialize test configuration."""
        self.config_file = config_file or self._find_default_config()
        self._config_data = self._load_config()
        
    def _find_default_config(self) -> Path:
        """Find default test configuration file."""
        # Look for test config in multiple locations
        candidates = [
            Path("tests/runner/test_config.yaml"),
            Path("tests/test_config.yaml"),
            Path("config/test_config.yaml")
        ]
        
        for candidate in candidates:
            if candidate.exists():
                return candidate
                
        # Create minimal default config
        return self._create_default_config()
    
    def _create_default_config(self) -> Path:
        """Create minimal default test configuration."""
        config_path = Path("tests/runner/test_config.yaml")
        config_path.parent.mkdir(exist_ok=True)
        
        default_config = {
            'suites': {
                'epic1_unit': {
                    'name': 'Epic 1 Unit Tests',
                    'description': 'Unit tests for Epic 1 components',
                    'patterns': ['tests/unit/test_*.py'],
                    'markers': ['epic1'],
                    'epic': 'epic1'
                },
                'epic1_integration': {
                    'name': 'Epic 1 Integration Tests', 
                    'description': 'Integration tests for Epic 1 system',
                    'patterns': ['tests/epic1/integration/test_*.py'],
                    'markers': ['integration', 'epic1'],
                    'epic': 'epic1'
                },
                'epic1_phase2': {
                    'name': 'Epic 1 Phase 2 Tests',
                    'description': 'Phase 2 multi-model tests', 
                    'patterns': ['tests/epic1/phase2/test_*.py'],
                    'markers': ['epic1', 'phase2'],
                    'epic': 'epic1'
                },
                'epic1_all': {
                    'name': 'All Epic 1 Tests',
                    'description': 'Complete Epic 1 test suite',
                    'patterns': [
                        'tests/epic1/**/*.py',
                        'tests/unit/test_*epic*.py',
                        'tests/integration/*epic*.py'
                    ],
                    'markers': ['epic1'],
                    'epic': 'epic1',
                    'timeout': 600
                },
                'smoke': {
                    'name': 'Smoke Tests',
                    'description': 'Quick health checks',
                    'patterns': [
                        'tests/epic1/smoke/test_*.py',
                        'tests/smoke/test_*.py'
                    ],
                    'markers': ['smoke'],
                    'timeout': 60
                },
                'regression': {
                    'name': 'Regression Tests',
                    'description': 'Bug fix validation',
                    'patterns': [
                        'tests/epic1/regression/test_*.py',
                        'tests/regression/test_*.py'
                    ],
                    'markers': ['regression']
                }
            },
            'defaults': {
                'output_format': 'terminal',
                'verbose': True,
                'fail_fast': False,
                'capture': 'no',
                'parallel': False
            }
        }
        
        with open(config_path, 'w') as f:
            yaml.dump(default_config, f, default_flow_style=False, indent=2)
            
        return config_path
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file."""
        try:
            with open(self.config_file, 'r') as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            print(f"Warning: Could not load config from {self.config_file}: {e}")
            return {'suites': {}, 'defaults': {}}
    
    def get_suite(self, name: str) -> Optional[TestSuiteConfig]:
        """Get test suite configuration by name."""
        suite_data = self._config_data.get('suites', {}).get(name)
        if not suite_data:
            return None
            
        return TestSuiteConfig(
            name=suite_data.get('name', name),
            description=suite_data.get('description', ''),
            patterns=suite_data.get('patterns', []),
            markers=suite_data.get('markers', []),
            timeout=suite_data.get('timeout', 300),
            parallel=suite_data.get('parallel', False),
            coverage=suite_data.get('coverage', False),
            epic=suite_data.get('epic')
        )
    
    def list_suites(self) -> List[str]:
        """List available test suite names."""
        return list(self._config_data.get('suites', {}).keys())
    
    def get_defaults(self) -> Dict[str, Any]:
        """Get default run configuration."""
        return self._config_data.get('defaults', {})
    
    def create_run_config(self, suite_names: List[str], **overrides) -> TestRunConfig:
        """Create test run configuration."""
        suites = []
        for name in suite_names:
            suite = self.get_suite(name)
            if suite:
                suites.append(suite)
            else:
                print(f"Warning: Unknown test suite '{name}'")
        
        defaults = self.get_defaults()
        defaults.update(overrides)
        
        return TestRunConfig(
            suites=suites,
            output_format=defaults.get('output_format', 'terminal'),
            verbose=defaults.get('verbose', True),
            fail_fast=defaults.get('fail_fast', False),
            capture=defaults.get('capture', 'no')
        )