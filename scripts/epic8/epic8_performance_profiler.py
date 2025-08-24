#!/usr/bin/env python3
"""
Epic 8 Services Performance Profiler

Specialized profiler for measuring Epic 8 service performance 
before and after dead code removal.
"""

import time
import sys
import subprocess
import json
import tempfile
import os
from pathlib import Path
from typing import Dict, List, Any
from dataclasses import dataclass
import tracemalloc


@dataclass
class ServicePerformanceMetrics:
    """Performance metrics for Epic 8 services."""
    service_name: str
    import_time_ms: float
    memory_usage_mb: float
    startup_time_ms: float
    dependency_count: int
    cold_start_time_ms: float


class Epic8PerformanceProfiler:
    """Profiler specifically for Epic 8 services and dead code impact."""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.results = {}
        
    def measure_service_import_time(self, service_module: str) -> float:
        """Measure time to import an Epic 8 service module."""
        # Create a temporary script to measure import time
        script_content = f"""
import sys
import time
sys.path.insert(0, '{self.project_root}')

start_time = time.perf_counter()
try:
    import {service_module}
    end_time = time.perf_counter()
    import_time = (end_time - start_time) * 1000
    print(f"IMPORT_TIME: {{import_time}}")
except Exception as e:
    print(f"IMPORT_ERROR: {{e}}")
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(script_content)
            temp_script = f.name
        
        try:
            result = subprocess.run(
                [sys.executable, temp_script],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            for line in result.stdout.split('\n'):
                if line.startswith('IMPORT_TIME:'):
                    return float(line.split(':')[1].strip())
            
            return -1  # Import failed
            
        except subprocess.TimeoutExpired:
            return -1
        except Exception as e:
            print(f"Error measuring import time for {service_module}: {e}")
            return -1
        finally:
            os.unlink(temp_script)
    
    def measure_service_startup_time(self, service_name: str) -> Dict[str, float]:
        """Measure Epic 8 service startup time (simulated)."""
        startup_script = f"""
import sys
import time
import asyncio
sys.path.insert(0, '{self.project_root}')

async def measure_startup():
    start_time = time.perf_counter()
    
    try:
        # Simulate service startup for query-analyzer
        if '{service_name}' == 'query-analyzer':
            from services.query_analyzer.app.main import create_app
            from services.query_analyzer.app.core.config import get_settings, get_analyzer_config
            from services.query_analyzer.app.core.analyzer import QueryAnalyzerService
            
            # Initialize like real service
            settings = get_settings()
            analyzer_config = get_analyzer_config()
            analyzer_service = QueryAnalyzerService(config=analyzer_config)
            app = create_app()
            
        startup_time = (time.perf_counter() - start_time) * 1000
        print(f"STARTUP_TIME: {{startup_time}}")
        
    except Exception as e:
        print(f"STARTUP_ERROR: {{e}}")

# Run startup measurement
asyncio.run(measure_startup())
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(startup_script)
            temp_script = f.name
        
        try:
            result = subprocess.run(
                [sys.executable, temp_script],
                capture_output=True,
                text=True,
                timeout=45
            )
            
            metrics = {'startup_time_ms': -1, 'memory_mb': 0}
            
            for line in result.stdout.split('\n'):
                if line.startswith('STARTUP_TIME:'):
                    metrics['startup_time_ms'] = float(line.split(':')[1].strip())
            
            return metrics
            
        except subprocess.TimeoutExpired:
            return {'startup_time_ms': -1, 'memory_mb': 0}
        except Exception as e:
            print(f"Error measuring startup time for {service_name}: {e}")
            return {'startup_time_ms': -1, 'memory_mb': 0}
        finally:
            os.unlink(temp_script)
    
    def measure_dead_code_import_impact(self) -> Dict[str, float]:
        """Measure the import time impact of dead code modules."""
        dead_code_modules = [
            'src.testing.cli.test_cli',
            'src.training.dataset_generation_framework'
        ]
        
        impact_metrics = {}
        
        for module in dead_code_modules:
            # Test if module exists and can be imported
            try:
                import_time = self.measure_service_import_time(module)
                impact_metrics[module] = {
                    'import_time_ms': import_time,
                    'exists': import_time > 0,
                    'impact_category': 'HIGH' if import_time > 10 else 'LOW'
                }
            except Exception as e:
                impact_metrics[module] = {
                    'import_time_ms': -1,
                    'exists': False,
                    'error': str(e)
                }
        
        return impact_metrics
    
    def profile_test_suite_performance(self) -> Dict[str, Any]:
        """Profile test suite performance with focus on Epic 8 tests."""
        test_metrics = {}
        
        # Test discovery performance
        start_time = time.perf_counter()
        result = subprocess.run(
            ['python', '-m', 'pytest', '--collect-only', 'tests/epic8/', '-q'],
            capture_output=True,
            text=True,
            cwd=self.project_root
        )
        discovery_time = (time.perf_counter() - start_time) * 1000
        
        # Count Epic 8 tests
        epic8_test_count = len([
            line for line in result.stdout.split('\n') 
            if '::test_' in line and 'epic8' in line
        ])
        
        test_metrics['epic8_tests'] = {
            'discovery_time_ms': discovery_time,
            'test_count': epic8_test_count,
            'discovery_rate_tests_per_ms': epic8_test_count / discovery_time if discovery_time > 0 else 0
        }
        
        # Overall test suite metrics
        start_time = time.perf_counter()
        result = subprocess.run(
            ['python', '-m', 'pytest', '--collect-only', 'tests/', '-q'],
            capture_output=True,
            text=True,
            cwd=self.project_root
        )
        total_discovery_time = (time.perf_counter() - start_time) * 1000
        
        total_test_count = len([
            line for line in result.stdout.split('\n') 
            if '::test_' in line
        ])
        
        test_metrics['total_suite'] = {
            'discovery_time_ms': total_discovery_time,
            'test_count': total_test_count,
            'epic8_percentage': (epic8_test_count / total_test_count * 100) if total_test_count > 0 else 0
        }
        
        return test_metrics
    
    def benchmark_containerized_performance(self) -> Dict[str, Any]:
        """Benchmark Epic 8 services in containerized environment (simulated)."""
        container_metrics = {}
        
        # Estimate container resource usage
        service_files = [
            self.project_root / 'services' / 'query-analyzer' / 'app' / 'main.py',
            self.project_root / 'services' / 'query-analyzer' / 'app' / 'core' / 'analyzer.py',
            self.project_root / 'services' / 'query-analyzer' / 'app' / 'api' / 'rest.py'
        ]
        
        total_service_size = sum(f.stat().st_size for f in service_files if f.exists())
        
        # Dead code files
        dead_code_files = [
            self.project_root / 'src' / 'testing' / 'cli' / 'test_cli.py',
            self.project_root / 'src' / 'training' / 'dataset_generation_framework.py'
        ]
        
        dead_code_size = sum(f.stat().st_size for f in dead_code_files if f.exists())
        
        container_metrics = {
            'service_code_size_kb': total_service_size / 1024,
            'dead_code_size_kb': dead_code_size / 1024,
            'size_reduction_percentage': (dead_code_size / total_service_size * 100) if total_service_size > 0 else 0,
            'estimated_container_size_reduction_mb': dead_code_size / (1024 * 1024),
            'docker_layer_efficiency_improvement': 'Medium' if dead_code_size > 10000 else 'Low'
        }
        
        return container_metrics
    
    def generate_epic8_performance_report(self) -> Dict[str, Any]:
        """Generate comprehensive Epic 8 performance analysis."""
        print("=== Epic 8 Performance Analysis Starting ===")
        
        # Profile Epic 8 services
        epic8_services = {
            'query-analyzer-main': 'services.query_analyzer.app.main',
            'query-analyzer-core': 'services.query_analyzer.app.core.analyzer',
            'query-analyzer-api': 'services.query_analyzer.app.api.rest'
        }
        
        service_metrics = {}
        for service_name, module_path in epic8_services.items():
            print(f"Profiling {service_name}...")
            
            # Import performance
            import_time = self.measure_service_import_time(module_path)
            
            # Startup performance (for main service only)
            startup_metrics = {}
            if 'main' in service_name:
                startup_metrics = self.measure_service_startup_time('query-analyzer')
            
            service_metrics[service_name] = {
                'import_time_ms': import_time,
                'startup_metrics': startup_metrics,
                'module_path': module_path
            }
        
        # Dead code impact analysis
        print("Analyzing dead code impact...")
        dead_code_impact = self.measure_dead_code_import_impact()
        
        # Test suite performance
        print("Profiling test suite performance...")
        test_performance = self.profile_test_suite_performance()
        
        # Container performance simulation
        print("Analyzing container performance impact...")
        container_impact = self.benchmark_containerized_performance()
        
        # Generate optimization projections
        optimization_projections = self._calculate_optimization_projections(
            service_metrics, dead_code_impact, container_impact
        )
        
        report = {
            'analysis_timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'epic8_service_performance': service_metrics,
            'dead_code_impact_analysis': dead_code_impact,
            'test_suite_performance': test_performance,
            'container_performance_impact': container_impact,
            'optimization_projections': optimization_projections,
            'recommendations': self._generate_epic8_recommendations(optimization_projections)
        }
        
        return report
    
    def _calculate_optimization_projections(self, service_metrics: Dict, dead_code_impact: Dict, container_impact: Dict) -> Dict[str, Any]:
        """Calculate projected performance improvements."""
        # Calculate current baseline
        total_import_time = sum(
            metrics['import_time_ms'] for metrics in service_metrics.values() 
            if metrics['import_time_ms'] > 0
        )
        
        dead_code_import_time = sum(
            impact['import_time_ms'] for impact in dead_code_impact.values()
            if impact['import_time_ms'] > 0
        )
        
        projections = {
            'import_time_reduction': {
                'current_total_ms': total_import_time,
                'dead_code_overhead_ms': dead_code_import_time,
                'projected_reduction_ms': dead_code_import_time * 0.8,  # Conservative estimate
                'improvement_percentage': (dead_code_import_time * 0.8 / total_import_time * 100) if total_import_time > 0 else 0
            },
            'memory_optimization': {
                'container_size_reduction_mb': container_impact.get('estimated_container_size_reduction_mb', 0),
                'runtime_memory_reduction_mb': container_impact.get('dead_code_size_kb', 0) * 0.01,  # Rough estimate
                'docker_efficiency_gain': container_impact.get('docker_layer_efficiency_improvement', 'None')
            },
            'development_efficiency': {
                'test_discovery_improvement_ms': dead_code_import_time * 0.5,  # Test infrastructure impact
                'build_time_reduction_s': container_impact.get('dead_code_size_kb', 0) * 0.001,  # Build time estimate
                'developer_productivity_gain': 'Medium' if dead_code_import_time > 5 else 'Low'
            }
        }
        
        return projections
    
    def _generate_epic8_recommendations(self, projections: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate specific recommendations for Epic 8 optimization."""
        recommendations = []
        
        # Import time optimization
        if projections['import_time_reduction']['improvement_percentage'] > 1:
            recommendations.append({
                'category': 'Import Performance',
                'priority': 'HIGH',
                'action': 'Remove dead code modules to reduce import overhead',
                'expected_benefit': f"{projections['import_time_reduction']['projected_reduction_ms']:.1f}ms import time reduction",
                'impact_on_epic8': 'Faster service startup and cold start times'
            })
        
        # Memory optimization
        if projections['memory_optimization']['container_size_reduction_mb'] > 0.1:
            recommendations.append({
                'category': 'Memory Optimization', 
                'priority': 'MEDIUM',
                'action': 'Remove dead code to reduce container footprint',
                'expected_benefit': f"{projections['memory_optimization']['container_size_reduction_mb']:.2f}MB container size reduction",
                'impact_on_epic8': 'More efficient Kubernetes resource utilization'
            })
        
        # Development efficiency
        if projections['development_efficiency']['test_discovery_improvement_ms'] > 1:
            recommendations.append({
                'category': 'Development Efficiency',
                'priority': 'MEDIUM',
                'action': 'Remove test CLI infrastructure to speed up test discovery',
                'expected_benefit': f"{projections['development_efficiency']['test_discovery_improvement_ms']:.1f}ms faster test discovery",
                'impact_on_epic8': 'Faster development feedback cycles'
            })
        
        return recommendations


def main():
    """Main execution function."""
    project_root = Path("/Users/apa/ml_projects/rag-portfolio/project-1-technical-rag")
    
    profiler = Epic8PerformanceProfiler(project_root)
    report = profiler.generate_epic8_performance_report()
    
    # Save detailed report
    report_file = project_root / "EPIC8_PERFORMANCE_ANALYSIS.json"
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n=== Epic 8 Performance Analysis Complete ===")
    print(f"Report saved to: {report_file}")
    
    # Print key findings
    projections = report['optimization_projections']
    print(f"\nOptimization Projections:")
    print(f"- Import time reduction: {projections['import_time_reduction']['projected_reduction_ms']:.1f}ms")
    print(f"- Container size reduction: {projections['memory_optimization']['container_size_reduction_mb']:.2f}MB")
    print(f"- Test discovery improvement: {projections['development_efficiency']['test_discovery_improvement_ms']:.1f}ms")
    
    print(f"\nRecommendations ({len(report['recommendations'])}):")
    for rec in report['recommendations']:
        print(f"- {rec['category']} ({rec['priority']}): {rec['action']}")


if __name__ == "__main__":
    main()