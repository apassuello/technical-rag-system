#!/usr/bin/env python3
"""
Dependency Impact Analyzer for Dead Code Removal

Analyzes the dependency chains and import impact of removing dead code modules.
"""

import ast
import os
import time
from pathlib import Path
from typing import Dict, List, Set, Tuple, Any
from collections import defaultdict, deque
import json


class DependencyAnalyzer:
    """Analyzes module dependencies and their performance impact."""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.dependency_graph = defaultdict(set)
        self.reverse_dependencies = defaultdict(set)
        self.module_metrics = {}
        
    def extract_imports_from_file(self, file_path: Path) -> Set[str]:
        """Extract all import statements from a Python file."""
        imports = set()
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                tree = ast.parse(f.read())
                
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.add(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        # Handle "from module import ..." 
                        imports.add(node.module)
                        
        except (SyntaxError, UnicodeDecodeError, FileNotFoundError) as e:
            print(f"Error parsing {file_path}: {e}")
            
        return imports
    
    def build_dependency_graph(self) -> None:
        """Build complete dependency graph for the project."""
        print("Building dependency graph...")
        
        # Find all Python files
        python_files = list(self.project_root.rglob("*.py"))
        
        for file_path in python_files:
            # Convert file path to module name
            relative_path = file_path.relative_to(self.project_root)
            if relative_path.name == "__init__.py":
                module_name = str(relative_path.parent).replace(os.sep, ".")
            else:
                module_name = str(relative_path.with_suffix("")).replace(os.sep, ".")
            
            # Skip __pycache__ and other non-module files
            if "__pycache__" in module_name:
                continue
                
            # Extract imports
            imports = self.extract_imports_from_file(file_path)
            
            # Filter for internal imports (within project)
            internal_imports = set()
            for imp in imports:
                if imp.startswith("src.") or imp.startswith("services.") or imp.startswith("tests."):
                    internal_imports.add(imp)
            
            # Update dependency graph
            self.dependency_graph[module_name] = internal_imports
            
            # Update reverse dependencies
            for imp in internal_imports:
                self.reverse_dependencies[imp].add(module_name)
                
            # Store module metrics
            self.module_metrics[module_name] = {
                "file_path": str(file_path),
                "file_size": file_path.stat().st_size,
                "import_count": len(internal_imports),
                "total_imports": len(imports)
            }
    
    def find_affected_modules(self, target_modules: List[str]) -> Dict[str, Set[str]]:
        """Find all modules that would be affected by removing target modules."""
        affected = {}
        
        for target in target_modules:
            print(f"Analyzing impact of removing: {target}")
            
            # Direct dependents (modules that import this target)
            direct_dependents = self.reverse_dependencies.get(target, set())
            
            # Transitive dependents (modules that depend on direct dependents)
            all_affected = set(direct_dependents)
            queue = deque(direct_dependents)
            
            while queue:
                current = queue.popleft()
                dependents = self.reverse_dependencies.get(current, set())
                for dep in dependents:
                    if dep not in all_affected:
                        all_affected.add(dep)
                        queue.append(dep)
            
            affected[target] = all_affected
            
        return affected
    
    def calculate_import_chains(self, target_modules: List[str]) -> Dict[str, List[List[str]]]:
        """Calculate import chains that would be eliminated."""
        chains = {}
        
        for target in target_modules:
            target_chains = []
            
            # Find all paths from Epic 8 services to this target
            epic8_services = [
                "services.query-analyzer.app.main",
                "services.query-analyzer.app.core.analyzer",
                "services.query-analyzer.app.api.rest"
            ]
            
            for service in epic8_services:
                if service in self.dependency_graph:
                    paths = self._find_import_paths(service, target)
                    target_chains.extend(paths)
            
            chains[target] = target_chains
            
        return chains
    
    def _find_import_paths(self, start: str, target: str, visited: Set[str] = None, path: List[str] = None) -> List[List[str]]:
        """Find all import paths from start module to target module."""
        if visited is None:
            visited = set()
        if path is None:
            path = []
            
        if start in visited:
            return []  # Avoid cycles
            
        visited.add(start)
        path = path + [start]
        
        if start == target:
            return [path]
        
        paths = []
        for neighbor in self.dependency_graph.get(start, set()):
            if neighbor not in visited:
                new_paths = self._find_import_paths(neighbor, target, visited.copy(), path)
                paths.extend(new_paths)
                
        return paths
    
    def estimate_performance_impact(self, target_modules: List[str]) -> Dict[str, Dict[str, float]]:
        """Estimate performance impact of removing target modules."""
        impact = {}
        
        for target in target_modules:
            # Get module metrics
            metrics = self.module_metrics.get(target, {})
            
            # Calculate impact metrics
            file_size_kb = metrics.get("file_size", 0) / 1024
            import_count = metrics.get("import_count", 0)
            
            # Estimate import time reduction (based on file size and complexity)
            # Rough estimate: 0.1ms per KB + 0.5ms per import
            estimated_import_time_reduction_ms = (file_size_kb * 0.1) + (import_count * 0.5)
            
            # Estimate memory reduction (rough estimate: 1MB per 100KB of Python code)
            estimated_memory_reduction_mb = file_size_kb * 0.01
            
            # Find affected modules
            affected_modules = self.find_affected_modules([target])[target]
            affected_count = len(affected_modules)
            
            impact[target] = {
                "file_size_kb": file_size_kb,
                "import_count": import_count,
                "affected_modules_count": affected_count,
                "estimated_import_time_reduction_ms": estimated_import_time_reduction_ms,
                "estimated_memory_reduction_mb": estimated_memory_reduction_mb,
                "risk_level": self._assess_risk_level(affected_count, import_count)
            }
            
        return impact
    
    def _assess_risk_level(self, affected_count: int, import_count: int) -> str:
        """Assess risk level of removing a module."""
        if affected_count == 0:
            return "VERY_LOW"
        elif affected_count <= 2 and import_count <= 5:
            return "LOW"
        elif affected_count <= 5 and import_count <= 10:
            return "MEDIUM"
        elif affected_count <= 10:
            return "HIGH"
        else:
            return "VERY_HIGH"
    
    def analyze_epic8_import_performance(self) -> Dict[str, Any]:
        """Analyze current import performance for Epic 8 services."""
        epic8_services = [
            "services.query-analyzer.app.main",
            "services.query-analyzer.app.core.analyzer", 
            "services.query-analyzer.app.api.rest"
        ]
        
        analysis = {}
        
        for service in epic8_services:
            if service in self.dependency_graph:
                deps = self.dependency_graph[service]
                metrics = self.module_metrics.get(service, {})
                
                # Calculate dependency depth
                total_deps = self._count_transitive_dependencies(service)
                
                analysis[service] = {
                    "direct_dependencies": len(deps),
                    "total_transitive_dependencies": total_deps,
                    "file_size_kb": metrics.get("file_size", 0) / 1024,
                    "estimated_load_time_ms": self._estimate_load_time(service)
                }
        
        return analysis
    
    def _count_transitive_dependencies(self, module: str, visited: Set[str] = None) -> int:
        """Count all transitive dependencies of a module."""
        if visited is None:
            visited = set()
            
        if module in visited:
            return 0
            
        visited.add(module)
        count = 0
        
        for dep in self.dependency_graph.get(module, set()):
            count += 1 + self._count_transitive_dependencies(dep, visited.copy())
            
        return count
    
    def _estimate_load_time(self, module: str) -> float:
        """Estimate load time for a module based on its dependencies."""
        total_deps = self._count_transitive_dependencies(module)
        base_time = 1.0  # Base load time in ms
        dep_time = total_deps * 0.1  # 0.1ms per dependency
        
        return base_time + dep_time
    
    def generate_impact_report(self) -> Dict[str, Any]:
        """Generate comprehensive impact analysis report."""
        print("Generating impact analysis report...")
        
        # Build dependency graph
        self.build_dependency_graph()
        
        # Target modules for removal
        target_modules = [
            "src.testing.cli.test_cli",
            "src.training.dataset_generation_framework"
        ]
        
        # Analyze impacts
        affected_modules = self.find_affected_modules(target_modules)
        import_chains = self.calculate_import_chains(target_modules)
        performance_impact = self.estimate_performance_impact(target_modules)
        epic8_analysis = self.analyze_epic8_import_performance()
        
        report = {
            "analysis_timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "dependency_analysis": {
                "total_modules": len(self.module_metrics),
                "total_dependencies": sum(len(deps) for deps in self.dependency_graph.values()),
                "epic8_services_analysis": epic8_analysis
            },
            "dead_code_impact": {
                "target_modules": target_modules,
                "affected_modules": {k: list(v) for k, v in affected_modules.items()},
                "import_chains": import_chains,
                "performance_impact": performance_impact
            },
            "optimization_assessment": self._generate_optimization_assessment(performance_impact),
            "recommendations": self._generate_detailed_recommendations(performance_impact, affected_modules)
        }
        
        return report
    
    def _generate_optimization_assessment(self, performance_impact: Dict[str, Dict[str, float]]) -> Dict[str, Any]:
        """Generate optimization assessment based on impact analysis."""
        total_time_reduction = sum(
            impact["estimated_import_time_reduction_ms"] 
            for impact in performance_impact.values()
        )
        
        total_memory_reduction = sum(
            impact["estimated_memory_reduction_mb"]
            for impact in performance_impact.values()
        )
        
        total_affected = sum(
            impact["affected_modules_count"]
            for impact in performance_impact.values()
        )
        
        return {
            "total_estimated_import_time_reduction_ms": total_time_reduction,
            "total_estimated_memory_reduction_mb": total_memory_reduction,
            "total_affected_modules": total_affected,
            "overall_risk_assessment": "LOW" if total_affected <= 5 else "MEDIUM",
            "recommendation": "PROCEED" if total_affected <= 10 else "REVIEW_CAREFULLY"
        }
    
    def _generate_detailed_recommendations(self, performance_impact: Dict[str, Dict[str, float]], affected_modules: Dict[str, Set[str]]) -> List[Dict[str, Any]]:
        """Generate detailed optimization recommendations."""
        recommendations = []
        
        for module, impact in performance_impact.items():
            affected = affected_modules.get(module, set())
            
            rec = {
                "module": module,
                "action": "REMOVE" if impact["risk_level"] in ["VERY_LOW", "LOW"] else "REVIEW",
                "risk_level": impact["risk_level"],
                "benefits": {
                    "import_time_reduction_ms": impact["estimated_import_time_reduction_ms"],
                    "memory_reduction_mb": impact["estimated_memory_reduction_mb"],
                    "file_size_reduction_kb": impact["file_size_kb"]
                },
                "risks": {
                    "affected_modules": list(affected),
                    "affected_count": len(affected)
                },
                "priority": "HIGH" if impact["risk_level"] == "VERY_LOW" else "MEDIUM"
            }
            
            recommendations.append(rec)
            
        return recommendations


def main():
    """Main execution function."""
    project_root = Path("/Users/apa/ml_projects/rag-portfolio/project-1-technical-rag")
    
    analyzer = DependencyAnalyzer(project_root)
    report = analyzer.generate_impact_report()
    
    # Save report
    report_file = project_root / "DEPENDENCY_IMPACT_REPORT.json"
    with open(report_file, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n=== Dependency Impact Analysis Complete ===")
    print(f"Report saved to: {report_file}")
    
    # Print summary
    assessment = report["optimization_assessment"]
    print(f"\nOptimization Assessment:")
    print(f"- Estimated import time reduction: {assessment['total_estimated_import_time_reduction_ms']:.2f}ms")
    print(f"- Estimated memory reduction: {assessment['total_estimated_memory_reduction_mb']:.2f}MB")
    print(f"- Total affected modules: {assessment['total_affected_modules']}")
    print(f"- Risk level: {assessment['overall_risk_assessment']}")
    print(f"- Recommendation: {assessment['recommendation']}")


if __name__ == "__main__":
    main()