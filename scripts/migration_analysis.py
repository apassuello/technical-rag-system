#!/usr/bin/env python3
"""
Migration Analysis Tool - Phase 6.1

Analyzes current BasicRAG usage patterns throughout the codebase to understand:
1. How BasicRAG is currently being used
2. What methods and configurations are most common
3. How to map old patterns to new modular architecture
4. What migration challenges exist

This tool provides the foundation for automated migration.
"""

import ast
import sys
from pathlib import Path
from typing import Dict, List, Set, Any, Optional, Tuple
import json
from dataclasses import dataclass, asdict
from datetime import datetime
import re

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

@dataclass
class UsagePattern:
    """Represents a pattern of BasicRAG usage found in code."""
    file_path: str
    line_number: int
    method_name: str
    arguments: Dict[str, Any]
    context: str  # Surrounding code context
    complexity: str  # simple, medium, complex
    migration_notes: List[str]

@dataclass
class ImportPattern:
    """Represents how BasicRAG is imported in files."""
    file_path: str
    import_line: str
    import_type: str  # "direct", "from_module", "aliased"
    alias: Optional[str] = None

@dataclass
class ConfigurationPattern:
    """Represents configuration patterns found in BasicRAG usage."""
    initialization_args: Dict[str, Any]
    method_calls: List[str]
    usage_frequency: int
    files_using: List[str]

@dataclass
class MigrationAnalysis:
    """Complete analysis results for migration planning."""
    timestamp: str
    total_files_scanned: int
    files_using_basic_rag: int
    import_patterns: List[ImportPattern]
    usage_patterns: List[UsagePattern]
    configuration_patterns: List[ConfigurationPattern]
    method_usage_stats: Dict[str, int]
    complexity_breakdown: Dict[str, int]
    migration_recommendations: List[str]
    potential_issues: List[str]

class BasicRAGUsageAnalyzer:
    """Analyzes BasicRAG usage patterns for migration planning."""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.basic_rag_methods = {
            # Core methods that need migration
            '__init__', 'index_document', 'query', 'hybrid_query', 'enhanced_hybrid_query',
            'get_stats', 'clear_index', 'save_index', 'load_index',
            # Internal methods that might be referenced
            '_normalize_embeddings', '_create_sparse_matrix', '_get_chunk_text'
        }
        self.import_patterns = []
        self.usage_patterns = []
        
    def analyze_codebase(self) -> MigrationAnalysis:
        """
        Perform comprehensive analysis of BasicRAG usage.
        
        Returns:
            Complete migration analysis results
        """
        print("🔍 Starting BasicRAG migration analysis...")
        
        # Scan all Python files
        python_files = self._find_python_files()
        print(f"Found {len(python_files)} Python files to analyze")
        
        files_with_basic_rag = []
        
        for file_path in python_files:
            try:
                if self._analyze_file(file_path):
                    files_with_basic_rag.append(str(file_path))
                    print(f"✓ Found BasicRAG usage in: {file_path.relative_to(self.project_root)}")
            except Exception as e:
                print(f"⚠️ Error analyzing {file_path}: {e}")
        
        # Analyze patterns and generate recommendations
        config_patterns = self._analyze_configuration_patterns()
        method_stats = self._calculate_method_statistics()
        complexity_breakdown = self._analyze_complexity()
        recommendations = self._generate_migration_recommendations()
        potential_issues = self._identify_potential_issues()
        
        analysis = MigrationAnalysis(
            timestamp=datetime.now().isoformat(),
            total_files_scanned=len(python_files),
            files_using_basic_rag=len(files_with_basic_rag),
            import_patterns=self.import_patterns,
            usage_patterns=self.usage_patterns,
            configuration_patterns=config_patterns,
            method_usage_stats=method_stats,
            complexity_breakdown=complexity_breakdown,
            migration_recommendations=recommendations,
            potential_issues=potential_issues
        )
        
        print(f"\n📊 Analysis complete:")
        print(f"  • Files scanned: {analysis.total_files_scanned}")
        print(f"  • Files using BasicRAG: {analysis.files_using_basic_rag}")
        print(f"  • Usage patterns found: {len(analysis.usage_patterns)}")
        print(f"  • Import patterns found: {len(analysis.import_patterns)}")
        
        return analysis
    
    def _find_python_files(self) -> List[Path]:
        """Find all Python files in the project."""
        python_files = []
        
        # Scan specific directories
        scan_dirs = [
            self.project_root / "src",
            self.project_root / "scripts", 
            self.project_root / "tests",
            self.project_root,  # Root level files
        ]
        
        for scan_dir in scan_dirs:
            if scan_dir.exists():
                python_files.extend(scan_dir.glob("**/*.py"))
        
        # Remove duplicates and __pycache__ files
        unique_files = []
        for f in python_files:
            if "__pycache__" not in str(f) and f not in unique_files:
                unique_files.append(f)
                
        return unique_files
    
    def _analyze_file(self, file_path: Path) -> bool:
        """
        Analyze a single file for BasicRAG usage.
        
        Returns:
            True if BasicRAG usage found, False otherwise
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception:
            return False
        
        # Quick check if file mentions BasicRAG
        if 'BasicRAG' not in content and 'basic_rag' not in content:
            return False
        
        found_usage = False
        
        # Analyze imports
        import_found = self._analyze_imports(file_path, content)
        if import_found:
            found_usage = True
        
        # Analyze AST for method calls
        try:
            tree = ast.parse(content)
            visitor = BasicRAGVisitor(file_path, content)
            visitor.visit(tree)
            
            if visitor.usage_patterns:
                self.usage_patterns.extend(visitor.usage_patterns)
                found_usage = True
                
        except SyntaxError:
            # File has syntax errors, do text-based analysis
            text_usage = self._analyze_with_regex(file_path, content)
            if text_usage:
                found_usage = True
        
        return found_usage
    
    def _analyze_imports(self, file_path: Path, content: str) -> bool:
        """Analyze import patterns for BasicRAG."""
        lines = content.split('\n')
        found_imports = False
        
        for i, line in enumerate(lines):
            line = line.strip()
            
            # Direct import: from src.basic_rag import BasicRAG
            if re.match(r'from\s+.*basic_rag\s+import\s+BasicRAG', line):
                self.import_patterns.append(ImportPattern(
                    file_path=str(file_path),
                    import_line=line,
                    import_type="from_module"
                ))
                found_imports = True
            
            # Module import: import src.basic_rag
            elif re.match(r'import\s+.*basic_rag', line):
                self.import_patterns.append(ImportPattern(
                    file_path=str(file_path),
                    import_line=line,
                    import_type="direct"
                ))
                found_imports = True
            
            # Aliased import: from src.basic_rag import BasicRAG as RAG
            elif re.match(r'from\s+.*basic_rag\s+import\s+BasicRAG\s+as\s+(\w+)', line):
                match = re.search(r'as\s+(\w+)', line)
                alias = match.group(1) if match else None
                self.import_patterns.append(ImportPattern(
                    file_path=str(file_path),
                    import_line=line,
                    import_type="aliased",
                    alias=alias
                ))
                found_imports = True
        
        return found_imports
    
    def _analyze_with_regex(self, file_path: Path, content: str) -> bool:
        """Fallback regex-based analysis for files with syntax errors."""
        patterns_found = []
        
        # Look for BasicRAG instantiation
        rag_init_pattern = r'(\w+)\s*=\s*BasicRAG\s*\('
        matches = re.finditer(rag_init_pattern, content)
        
        for match in matches:
            line_num = content[:match.start()].count('\n') + 1
            patterns_found.append(UsagePattern(
                file_path=str(file_path),
                line_number=line_num,
                method_name="__init__",
                arguments={},
                context=match.group(0),
                complexity="unknown",
                migration_notes=["Parsed with regex - needs manual review"]
            ))
        
        # Look for method calls
        method_call_pattern = r'(\w+)\.(' + '|'.join(self.basic_rag_methods) + r')\s*\('
        matches = re.finditer(method_call_pattern, content)
        
        for match in matches:
            line_num = content[:match.start()].count('\n') + 1
            var_name, method_name = match.groups()
            
            patterns_found.append(UsagePattern(
                file_path=str(file_path),
                line_number=line_num,
                method_name=method_name,
                arguments={},
                context=match.group(0),
                complexity="unknown",
                migration_notes=["Parsed with regex - needs manual review"]
            ))
        
        if patterns_found:
            self.usage_patterns.extend(patterns_found)
            return True
        
        return False
    
    def _analyze_configuration_patterns(self) -> List[ConfigurationPattern]:
        """Analyze common configuration patterns."""
        # Group usage patterns by file to understand configurations
        file_usage = {}
        
        for pattern in self.usage_patterns:
            file_path = pattern.file_path
            if file_path not in file_usage:
                file_usage[file_path] = []
            file_usage[file_path].append(pattern)
        
        # Analyze common patterns
        config_patterns = []
        
        # Pattern 1: Simple usage (init + index + query)
        simple_pattern = ConfigurationPattern(
            initialization_args={},
            method_calls=["__init__", "index_document", "query"],
            usage_frequency=0,
            files_using=[]
        )
        
        # Pattern 2: Hybrid search usage  
        hybrid_pattern = ConfigurationPattern(
            initialization_args={},
            method_calls=["__init__", "index_document", "hybrid_query"],
            usage_frequency=0,
            files_using=[]
        )
        
        # Count patterns
        for file_path, patterns in file_usage.items():
            methods_used = [p.method_name for p in patterns]
            
            if all(m in methods_used for m in simple_pattern.method_calls):
                simple_pattern.usage_frequency += 1
                simple_pattern.files_using.append(file_path)
            
            if "hybrid_query" in methods_used:
                hybrid_pattern.usage_frequency += 1
                hybrid_pattern.files_using.append(file_path)
        
        if simple_pattern.usage_frequency > 0:
            config_patterns.append(simple_pattern)
        if hybrid_pattern.usage_frequency > 0:
            config_patterns.append(hybrid_pattern)
        
        return config_patterns
    
    def _calculate_method_statistics(self) -> Dict[str, int]:
        """Calculate usage statistics for each method."""
        method_counts = {}
        
        for pattern in self.usage_patterns:
            method = pattern.method_name
            method_counts[method] = method_counts.get(method, 0) + 1
        
        return method_counts
    
    def _analyze_complexity(self) -> Dict[str, int]:
        """Analyze complexity distribution of usage patterns."""
        complexity_counts = {"simple": 0, "medium": 0, "complex": 0, "unknown": 0}
        
        for pattern in self.usage_patterns:
            complexity_counts[pattern.complexity] += 1
        
        return complexity_counts
    
    def _generate_migration_recommendations(self) -> List[str]:
        """Generate specific migration recommendations."""
        recommendations = []
        
        method_stats = self._calculate_method_statistics()
        
        # Basic recommendations
        recommendations.append("Replace 'from src.basic_rag import BasicRAG' with 'from src.core.pipeline import RAGPipeline'")
        recommendations.append("Replace 'BasicRAG()' initialization with 'RAGPipeline(config_path)'")
        
        # Method-specific recommendations
        if method_stats.get("query", 0) > 0:
            recommendations.append("Replace 'rag.query()' calls with 'pipeline.query()' (same interface)")
        
        if method_stats.get("hybrid_query", 0) > 0:
            recommendations.append("Replace 'rag.hybrid_query()' with 'pipeline.query()' (hybrid is default in new system)")
        
        if method_stats.get("index_document", 0) > 0:
            recommendations.append("Replace 'rag.index_document()' with 'pipeline.index_document()' (same interface)")
        
        # Configuration recommendations
        if len(self.usage_patterns) > 0:
            recommendations.append("Create YAML configuration file for pipeline settings")
            recommendations.append("Use environment-specific configs (test.yaml, dev.yaml, production.yaml)")
        
        return recommendations
    
    def _identify_potential_issues(self) -> List[str]:
        """Identify potential migration challenges."""
        issues = []
        
        method_stats = self._calculate_method_statistics()
        
        # Check for advanced/deprecated methods
        if method_stats.get("enhanced_hybrid_query", 0) > 0:
            issues.append("enhanced_hybrid_query() method used - this is deprecated and should use standard query()")
        
        if method_stats.get("save_index", 0) > 0:
            issues.append("save_index() method used - new system uses different persistence approach")
        
        if method_stats.get("load_index", 0) > 0:
            issues.append("load_index() method used - new system uses different persistence approach")
        
        # Check for complex configurations
        complex_patterns = [p for p in self.usage_patterns if p.complexity == "complex"]
        if complex_patterns:
            issues.append(f"{len(complex_patterns)} complex usage patterns found - may need manual migration")
        
        # Check for internal method access
        internal_methods = [m for m in method_stats.keys() if m.startswith('_')]
        if internal_methods:
            issues.append(f"Internal methods accessed: {', '.join(internal_methods)} - these may not exist in new system")
        
        return issues

class BasicRAGVisitor(ast.NodeVisitor):
    """AST visitor to analyze BasicRAG usage patterns."""
    
    def __init__(self, file_path: Path, content: str):
        self.file_path = file_path
        self.content = content
        self.lines = content.split('\n')
        self.usage_patterns = []
        self.basic_rag_vars = set()  # Track variables that hold BasicRAG instances
    
    def visit_Assign(self, node):
        """Visit assignment nodes to track BasicRAG instances."""
        if isinstance(node.value, ast.Call):
            if isinstance(node.value.func, ast.Name) and node.value.func.id == 'BasicRAG':
                # Track variables assigned to BasicRAG instances
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        self.basic_rag_vars.add(target.id)
                        
                        # Analyze initialization
                        args = self._extract_call_arguments(node.value)
                        line_num = node.lineno
                        context = self._get_context(line_num, 2)
                        
                        self.usage_patterns.append(UsagePattern(
                            file_path=str(self.file_path),
                            line_number=line_num,
                            method_name="__init__",
                            arguments=args,
                            context=context,
                            complexity=self._assess_complexity(args, context),
                            migration_notes=self._generate_migration_notes("__init__", args)
                        ))
        
        self.generic_visit(node)
    
    def visit_Call(self, node):
        """Visit call nodes to find method calls on BasicRAG instances."""
        if isinstance(node.func, ast.Attribute):
            # Check if this is a method call on a known BasicRAG variable
            if isinstance(node.func.value, ast.Name):
                var_name = node.func.value.id
                method_name = node.func.attr
                
                if var_name in self.basic_rag_vars or method_name in ['query', 'hybrid_query', 'index_document', 'enhanced_hybrid_query']:
                    args = self._extract_call_arguments(node)
                    line_num = node.lineno
                    context = self._get_context(line_num, 2)
                    
                    self.usage_patterns.append(UsagePattern(
                        file_path=str(self.file_path),
                        line_number=line_num,
                        method_name=method_name,
                        arguments=args,
                        context=context,
                        complexity=self._assess_complexity(args, context),
                        migration_notes=self._generate_migration_notes(method_name, args)
                    ))
        
        self.generic_visit(node)
    
    def _extract_call_arguments(self, call_node: ast.Call) -> Dict[str, Any]:
        """Extract arguments from a function call."""
        args = {}
        
        # Positional arguments
        for i, arg in enumerate(call_node.args):
            args[f"arg_{i}"] = self._extract_value(arg)
        
        # Keyword arguments
        for keyword in call_node.keywords:
            args[keyword.arg] = self._extract_value(keyword.value)
        
        return args
    
    def _extract_value(self, node: ast.AST) -> Any:
        """Extract value from an AST node."""
        if isinstance(node, ast.Constant):
            return node.value
        elif isinstance(node, ast.Str):  # For older Python versions
            return node.s
        elif isinstance(node, ast.Num):  # For older Python versions
            return node.n
        elif isinstance(node, ast.Name):
            return f"<variable:{node.id}>"
        elif isinstance(node, ast.Attribute):
            return f"<attribute:{node.attr}>"
        else:
            return f"<complex:{type(node).__name__}>"
    
    def _get_context(self, line_num: int, context_lines: int = 2) -> str:
        """Get surrounding context for a line."""
        start = max(0, line_num - context_lines - 1)
        end = min(len(self.lines), line_num + context_lines)
        
        context_lines = []
        for i in range(start, end):
            prefix = ">>> " if i == line_num - 1 else "    "
            context_lines.append(f"{prefix}{self.lines[i]}")
        
        return "\n".join(context_lines)
    
    def _assess_complexity(self, args: Dict[str, Any], context: str) -> str:
        """Assess the complexity of a usage pattern."""
        # Simple heuristics for complexity assessment
        if not args:
            return "simple"
        elif len(args) <= 2:
            return "simple"
        elif len(args) <= 5:
            return "medium"
        else:
            return "complex"
    
    def _generate_migration_notes(self, method_name: str, args: Dict[str, Any]) -> List[str]:
        """Generate migration notes for specific method usage."""
        notes = []
        
        if method_name == "__init__":
            if args:
                notes.append("BasicRAG initialization with arguments - check if these map to config file settings")
            else:
                notes.append("Simple BasicRAG initialization - direct replacement with RAGPipeline(config_path)")
        
        elif method_name == "query":
            notes.append("Direct replacement: pipeline.query() has same interface")
        
        elif method_name == "hybrid_query":
            notes.append("Replace with pipeline.query() - hybrid search is default in new system")
        
        elif method_name == "enhanced_hybrid_query":
            notes.append("DEPRECATED: Replace with pipeline.query() - enhanced features integrated by default")
        
        elif method_name == "index_document":
            notes.append("Direct replacement: pipeline.index_document() has same interface")
        
        else:
            notes.append(f"Method '{method_name}' needs manual review for migration")
        
        return notes

def main():
    """Main migration analysis workflow."""
    print("🔄 BasicRAG Migration Analysis Tool")
    print("=" * 50)
    
    analyzer = BasicRAGUsageAnalyzer(project_root)
    analysis = analyzer.analyze_codebase()
    
    # Save detailed analysis
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = project_root / f"migration_analysis_report_{timestamp}.json"
    
    # Convert to JSON-serializable format
    report_data = asdict(analysis)
    
    with open(report_path, 'w') as f:
        json.dump(report_data, f, indent=2, default=str)
    
    print(f"\n📄 Detailed report saved to: {report_path}")
    
    # Print summary
    print("\n📊 MIGRATION ANALYSIS SUMMARY")
    print("=" * 50)
    print(f"Files scanned: {analysis.total_files_scanned}")
    print(f"Files using BasicRAG: {analysis.files_using_basic_rag}")
    print(f"Usage patterns found: {len(analysis.usage_patterns)}")
    print(f"Import patterns found: {len(analysis.import_patterns)}")
    
    print("\n🔧 Method Usage Statistics:")
    for method, count in sorted(analysis.method_usage_stats.items(), key=lambda x: x[1], reverse=True):
        print(f"  • {method}: {count} occurrences")
    
    print("\n💡 Migration Recommendations:")
    for i, rec in enumerate(analysis.migration_recommendations, 1):
        print(f"  {i}. {rec}")
    
    if analysis.potential_issues:
        print("\n⚠️ Potential Issues:")
        for i, issue in enumerate(analysis.potential_issues, 1):
            print(f"  {i}. {issue}")
    
    print("\n✅ Analysis complete! Use this data to plan your migration.")
    
    return analysis

if __name__ == "__main__":
    main()