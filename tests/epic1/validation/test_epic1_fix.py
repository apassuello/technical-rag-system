#!/usr/bin/env python3
"""
Test file to diagnose Epic1MLAnalyzer compilation issue.
"""

import sys
from typing import Dict, Any, Optional
from pathlib import Path

# Add project paths
project_root = Path(__file__).parent.parent.parent.parent
sys.path.append(str(project_root))

from src.components.query_processors.analyzers.base_analyzer import BaseQueryAnalyzer

class Epic1MLAnalyzer(BaseQueryAnalyzer):
    """Test version of Epic1MLAnalyzer with minimal imports."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize Epic1MLAnalyzer with core functionality only."""
        print("Epic1MLAnalyzer.__init__ starting")
        
        # Call parent constructor first
        super().__init__(config)
        
        # Access config from parent (stored as _config)
        config = self._config
        
        # Core configuration - ALWAYS set these
        self.memory_budget_gb = config.get('memory_budget_gb', 2.0)
        self.enable_performance_monitoring = config.get('enable_performance_monitoring', True)
        self.parallel_execution = config.get('parallel_execution', True)
        self.fallback_strategy = config.get('fallback_strategy', 'algorithmic')
        self.confidence_threshold = config.get('confidence_threshold', 0.6)
        
        # Performance tracking - ALWAYS initialize
        self._analysis_count = 0
        self._total_analysis_time = 0.0
        self._error_count = 0
        self._view_performance = {}
        
        # Initialize core containers - ALWAYS create these
        self.views = {}
        self.trained_view_models = None
        self.neural_fusion_model = None
        self.ensemble_models = None
        self.model_manager = None
        self.performance_monitor = None
        self.memory_monitor = None
        
        # Status tracking
        self._ml_infrastructure_initialized = False
        self._views_initialized = False
        self._meta_classifier_initialized = False
        self._trained_models_loaded = False
        
        print(f"Epic1MLAnalyzer.__init__ completed successfully")
        print(f"Initialized with memory_budget_gb={self.memory_budget_gb}")
        
    def _setup_minimal_infrastructure(self):
        """Setup minimal infrastructure."""
        self.model_manager = None
        self.performance_monitor = None
        self.memory_monitor = None
        print("Minimal infrastructure setup completed")

if __name__ == "__main__":
    print("=== Testing Isolated Epic1MLAnalyzer ===")
    
    # Test class creation
    analyzer = Epic1MLAnalyzer()
    print("✅ Epic1MLAnalyzer created successfully")
    
    # Test attributes
    print(f"_analysis_count: {getattr(analyzer, '_analysis_count', 'MISSING')}")
    print(f"memory_budget_gb: {getattr(analyzer, 'memory_budget_gb', 'MISSING')}")
    print(f"views: {getattr(analyzer, 'views', 'MISSING')}")
    
    # Check if __init__ is in the class dict
    print(f"__init__ in class dict: {'__init__' in Epic1MLAnalyzer.__dict__}")
    print(f"__init__ qualname: {Epic1MLAnalyzer.__init__.__qualname__}")