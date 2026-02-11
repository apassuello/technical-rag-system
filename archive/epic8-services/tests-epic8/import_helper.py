"""
Robust import helper for Epic 8 tests.

This module provides utilities to safely import Epic 8 services
with proper isolation and conflict resolution.
"""

import sys
import importlib
import importlib.util
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
import contextlib


class ServiceImporter:
    """
    Manages safe importing of Epic 8 services with proper isolation.
    """
    
    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = project_root or Path(__file__).resolve().parents[2]
        self._original_paths = []
        self._imported_modules = set()
    
    def clean_app_modules(self):
        """Remove all service app modules from sys.modules to prevent conflicts."""
        service_prefixes = ['app.', 'generator_app.', 'cache_app.', 'retriever_app.', 
                           'analyzer_app.', 'gateway_app.', 'analytics_app.']
        modules_to_remove = []
        for prefix in service_prefixes:
            modules_to_remove.extend([key for key in sys.modules.keys() if key.startswith(prefix)])
        
        for module in modules_to_remove:
            if module in sys.modules:
                del sys.modules[module]
    
    @contextlib.contextmanager
    def isolated_import(self, service_name: str):
        """
        Context manager for isolated service importing.
        
        Usage:
            with importer.isolated_import('generator') as imports:
                if imports.available:
                    GeneratorService = imports.classes['GeneratorService']
        """
        # Store original state
        original_path = sys.path.copy()
        
        try:
            # Clean existing modules
            self.clean_app_modules()
            
            # Set up service path
            service_path = self.project_root / "services" / service_name
            
            if not service_path.exists():
                yield ImportResult(False, f"Service path not found: {service_path}")
                return
            
            # Add service path
            service_path_str = str(service_path)
            if service_path_str not in sys.path:
                sys.path.insert(0, service_path_str)
            
            # Attempt imports
            result = self._import_service(service_name, service_path)
            yield result
            
        finally:
            # Restore original path
            sys.path = original_path
            # Clean up modules again
            self.clean_app_modules()
    
    def _import_service(self, service_name: str, service_path: Path) -> 'ImportResult':
        """Import a specific service and return result."""
        try:
            imports = {}
            
            # Check required files exist - map service names to app directories
            service_app_mapping = {
                "generator": "generator_app",
                "query-analyzer": "analyzer_app", 
                "retriever": "retriever_app",
                "cache": "cache_app",
                "api-gateway": "gateway_app",
                "analytics": "analytics_app"
            }
            
            app_dir = service_app_mapping.get(service_name, "app")
            app_init = service_path / app_dir / "__init__.py"
            core_init = service_path / app_dir / "core" / "__init__.py"
            
            if not app_init.exists() or not core_init.exists():
                return ImportResult(
                    False, 
                    f"Missing __init__.py files in {service_name} service structure"
                )
            
            # Service-specific imports with new namespaces
            if service_name == "generator":
                from generator_app.core.generator import GeneratorService
                from generator_app.schemas.requests import GenerateRequest
                imports = {
                    'GeneratorService': GeneratorService,
                    'GenerateRequest': GenerateRequest
                }
                
            elif service_name == "query-analyzer":
                from analyzer_app.core.analyzer import QueryAnalyzerService
                imports = {'QueryAnalyzerService': QueryAnalyzerService}
                
            elif service_name == "retriever":
                from retriever_app.core.retriever import RetrieverService
                imports = {'RetrieverService': RetrieverService}
                
            elif service_name == "cache":
                from cache_app.core.cache import CacheService, InMemoryCache
                imports = {
                    'CacheService': CacheService,
                    'InMemoryCache': InMemoryCache
                }
                
            elif service_name == "api-gateway":
                from gateway_app.core.gateway import APIGatewayService
                imports = {'APIGatewayService': APIGatewayService}
                
            elif service_name == "analytics":
                from analytics_app.core.analytics import AnalyticsService
                imports = {'AnalyticsService': AnalyticsService}
                
            return ImportResult(True, None, imports)
            
        except ImportError as e:
            return ImportResult(False, f"Import failed for {service_name}: {str(e)}")


class ImportResult:
    """Result of a service import attempt."""
    
    def __init__(self, available: bool, error: Optional[str] = None, classes: Optional[Dict[str, Any]] = None):
        self.available = available
        self.error = error
        self.classes = classes or {}
    
    def __bool__(self):
        return self.available


# Global importer instance
_importer = ServiceImporter()


def get_service_imports(service_name: str) -> Tuple[bool, Optional[str], Dict[str, Any]]:
    """
    Get service imports in a simple function call.
    
    Returns:
        Tuple of (available, error_message, imported_classes)
    """
    with _importer.isolated_import(service_name) as result:
        return result.available, result.error, result.classes


def safe_import_generator():
    """Safely import generator service."""
    return get_service_imports('generator')


def safe_import_query_analyzer():
    """Safely import query analyzer service."""
    return get_service_imports('query-analyzer')


def safe_import_retriever():
    """Safely import retriever service."""
    return get_service_imports('retriever')


def safe_import_cache():
    """Safely import cache service."""
    return get_service_imports('cache')


def safe_import_api_gateway():
    """Safely import API gateway service."""
    return get_service_imports('api-gateway')


def safe_import_analytics():
    """Safely import analytics service."""
    return get_service_imports('analytics')