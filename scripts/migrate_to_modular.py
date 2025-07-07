#!/usr/bin/env python3
"""
Automated Migration Tool - Phase 6.2

Automates the migration from BasicRAG to the new modular RAGPipeline architecture.
This tool:
1. Analyzes existing BasicRAG usage
2. Creates configuration files based on current usage
3. Transforms Python code to use new modular system
4. Creates backups before changes
5. Provides rollback capability

Usage:
    python migrate_to_modular.py --analyze         # Analyze only, no changes
    python migrate_to_modular.py --migrate         # Perform full migration
    python migrate_to_modular.py --rollback        # Rollback last migration
    python migrate_to_modular.py --file <path>     # Migrate specific file
"""

import sys
import shutil
import ast
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Set
import json
import yaml
from datetime import datetime
from dataclasses import dataclass, asdict
import argparse

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from scripts.migration_analysis import BasicRAGUsageAnalyzer, MigrationAnalysis

@dataclass
class MigrationResult:
    """Result of migrating a single file."""
    file_path: str
    success: bool
    changes_made: List[str]
    issues: List[str]
    backup_path: Optional[str] = None

@dataclass
class MigrationSession:
    """Complete migration session results."""
    timestamp: str
    session_id: str
    files_processed: List[MigrationResult]
    config_files_created: List[str]
    success_rate: float
    rollback_info: Dict[str, str]

class AutomatedMigrator:
    """Handles automated migration from BasicRAG to modular architecture."""
    
    def __init__(self, project_root: Path, dry_run: bool = False):
        self.project_root = project_root
        self.dry_run = dry_run
        self.backup_dir = project_root / "migration_backups"
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.migration_results = []
        
        # Ensure backup directory exists
        if not dry_run:
            self.backup_dir.mkdir(exist_ok=True)
    
    def migrate_codebase(self, target_files: Optional[List[Path]] = None) -> MigrationSession:
        """
        Perform complete codebase migration.
        
        Args:
            target_files: Specific files to migrate (None for all)
            
        Returns:
            Migration session results
        """
        print("🚀 Starting automated migration to modular architecture...")
        print(f"Dry run: {'Yes' if self.dry_run else 'No'}")
        
        # Step 1: Analyze current usage
        analyzer = BasicRAGUsageAnalyzer(self.project_root)
        analysis = analyzer.analyze_codebase()
        
        # Step 2: Create configuration files
        config_files = self._create_configuration_files(analysis)
        
        # Step 3: Identify files to migrate
        if target_files is None:
            files_to_migrate = self._identify_migration_targets(analysis)
        else:
            files_to_migrate = target_files
        
        print(f"\n📝 Migration plan:")
        print(f"  • Files to migrate: {len(files_to_migrate)}")
        print(f"  • Config files to create: {len(config_files)}")
        
        if self.dry_run:
            print("  • DRY RUN: No actual changes will be made")
        
        # Step 4: Migrate each file
        rollback_info = {}
        
        for file_path in files_to_migrate:
            print(f"\n🔧 Migrating: {file_path.relative_to(self.project_root)}")
            
            result = self._migrate_file(file_path)
            self.migration_results.append(result)
            
            if result.success and result.backup_path:
                rollback_info[str(file_path)] = result.backup_path
            
            # Show progress
            status = "✅" if result.success else "❌"
            print(f"  {status} {len(result.changes_made)} changes, {len(result.issues)} issues")
        
        # Step 5: Create migration session record
        success_count = sum(1 for r in self.migration_results if r.success)
        success_rate = success_count / len(self.migration_results) if self.migration_results else 0
        
        session = MigrationSession(
            timestamp=datetime.now().isoformat(),
            session_id=self.session_id,
            files_processed=self.migration_results,
            config_files_created=config_files,
            success_rate=success_rate,
            rollback_info=rollback_info
        )
        
        # Save session record
        if not self.dry_run:
            self._save_migration_session(session)
        
        # Summary
        print(f"\n📊 Migration Summary:")
        print(f"  • Files processed: {len(self.migration_results)}")
        print(f"  • Successful: {success_count}")
        print(f"  • Success rate: {success_rate:.1%}")
        print(f"  • Config files created: {len(config_files)}")
        
        if rollback_info and not self.dry_run:
            print(f"  • Rollback data saved for recovery")
        
        return session
    
    def _create_configuration_files(self, analysis: MigrationAnalysis) -> List[str]:
        """Create configuration files based on current usage patterns."""
        config_files = []
        
        # Check if default config already exists
        default_config_path = self.project_root / "config" / "default.yaml"
        
        if default_config_path.exists():
            print("ℹ️ Configuration files already exist, skipping creation")
            return []
        
        print("📋 Creating configuration files...")
        
        # Ensure config directory exists
        config_dir = self.project_root / "config"
        if not self.dry_run:
            config_dir.mkdir(exist_ok=True)
        
        # Analyze usage to determine optimal configurations
        method_stats = analysis.method_usage_stats
        
        # Default configuration based on most common usage
        default_config = {
            "document_processor": {
                "type": "hybrid_pdf",
                "config": {
                    "chunk_size": 1400,
                    "chunk_overlap": 200
                }
            },
            "embedder": {
                "type": "sentence_transformer", 
                "config": {
                    "model_name": "sentence-transformers/all-MiniLM-L6-v2",
                    "use_mps": True,
                    "batch_size": 16
                }
            },
            "vector_store": {
                "type": "faiss",
                "config": {
                    "index_type": "IndexFlatIP",
                    "normalize_embeddings": True
                }
            },
            "retriever": {
                "type": "hybrid",
                "config": {
                    "dense_weight": 0.7,
                    "top_k": 5,
                    "fusion_method": "reciprocal_rank"
                }
            },
            "answer_generator": {
                "type": "adaptive",
                "config": {
                    "model_name": "deepset/roberta-base-squad2",
                    "api_token": None,
                    "enable_adaptive_prompts": False,
                    "enable_chain_of_thought": False,
                    "confidence_threshold": 0.85,
                    "max_tokens": 512
                }
            }
        }
        
        configs_to_create = [
            ("default.yaml", default_config),
            ("migration.yaml", {**default_config, "_migration_note": "Auto-generated migration config"})
        ]
        
        for filename, config in configs_to_create:
            config_path = config_dir / filename
            
            if not self.dry_run:
                with open(config_path, 'w') as f:
                    yaml.dump(config, f, default_flow_style=False, indent=2)
                print(f"✅ Created: {config_path.relative_to(self.project_root)}")
            else:
                print(f"📝 Would create: {config_path.relative_to(self.project_root)}")
            
            config_files.append(str(config_path))
        
        return config_files
    
    def _identify_migration_targets(self, analysis: MigrationAnalysis) -> List[Path]:
        """Identify files that need migration."""
        target_files = []
        
        # Get files with BasicRAG usage
        files_with_usage = set()
        for pattern in analysis.usage_patterns:
            files_with_usage.add(Path(pattern.file_path))
        
        for import_pattern in analysis.import_patterns:
            files_with_usage.add(Path(import_pattern.file_path))
        
        # Filter out files we shouldn't migrate
        skip_patterns = [
            "migration_analysis.py",  # Our analysis tool
            "migrate_to_modular.py",  # This migration tool
            "basic_rag.py",  # Keep original for comparison
            "__pycache__",
            ".pyc"
        ]
        
        for file_path in files_with_usage:
            # Skip if matches skip patterns
            if any(pattern in str(file_path) for pattern in skip_patterns):
                continue
            
            # Skip if file doesn't exist
            if not file_path.exists():
                continue
                
            target_files.append(file_path)
        
        return target_files
    
    def _migrate_file(self, file_path: Path) -> MigrationResult:
        """Migrate a single file from BasicRAG to modular architecture."""
        try:
            # Read original file
            with open(file_path, 'r', encoding='utf-8') as f:
                original_content = f.read()
            
            # Create backup
            backup_path = None
            if not self.dry_run:
                backup_path = self._create_backup(file_path, original_content)
            
            # Transform content
            transformed_content, changes, issues = self._transform_file_content(original_content, file_path)
            
            # Write transformed content
            if not self.dry_run and changes:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(transformed_content)
            
            return MigrationResult(
                file_path=str(file_path),
                success=len(issues) == 0,
                changes_made=changes,
                issues=issues,
                backup_path=backup_path
            )
            
        except Exception as e:
            return MigrationResult(
                file_path=str(file_path),
                success=False,
                changes_made=[],
                issues=[f"Migration failed: {str(e)}"]
            )
    
    def _create_backup(self, file_path: Path, content: str) -> str:
        """Create backup of file before migration."""
        # Create backup filename with session ID
        relative_path = file_path.relative_to(self.project_root)
        backup_name = f"{self.session_id}_{str(relative_path).replace('/', '_')}"
        backup_path = self.backup_dir / backup_name
        
        # Ensure backup directory structure
        backup_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(backup_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return str(backup_path)
    
    def _transform_file_content(self, content: str, file_path: Path) -> Tuple[str, List[str], List[str]]:
        """Transform file content from BasicRAG to modular architecture."""
        transformed = content
        changes = []
        issues = []
        
        # 1. Transform imports
        import_transformations = [
            (r'from\s+src\.basic_rag\s+import\s+BasicRAG', 'from src.core.pipeline import RAGPipeline'),
            (r'from\s+.*basic_rag\s+import\s+BasicRAG', 'from src.core.pipeline import RAGPipeline'),
            (r'import\s+src\.basic_rag', 'from src.core.pipeline import RAGPipeline'),
        ]
        
        for pattern, replacement in import_transformations:
            if re.search(pattern, transformed):
                transformed = re.sub(pattern, replacement, transformed)
                changes.append(f"Updated import: {pattern} → {replacement}")
        
        # 2. Transform class instantiation
        # BasicRAG() → RAGPipeline(config_path)
        basicrag_init_pattern = r'(\w+)\s*=\s*BasicRAG\s*\(\s*\)'
        matches = re.finditer(basicrag_init_pattern, transformed)
        
        for match in matches:
            var_name = match.group(1)
            # Determine appropriate config file
            config_path = self._determine_config_path(file_path)
            replacement = f'{var_name} = RAGPipeline("{config_path}")'
            
            transformed = transformed.replace(match.group(0), replacement)
            changes.append(f"Updated initialization: {match.group(0)} → {replacement}")
        
        # 3. Transform method calls
        method_transformations = [
            # hybrid_query → query (hybrid is default)
            (r'\.hybrid_query\s*\(', '.query(', "hybrid_query → query (hybrid is default in new system)"),
            # enhanced_hybrid_query → query  
            (r'\.enhanced_hybrid_query\s*\(', '.query(', "enhanced_hybrid_query → query (deprecated method)"),
            # index_documents → index_document (if exists)
            (r'\.index_documents\s*\(', '.index_document(', "index_documents → index_document"),
        ]
        
        for pattern, replacement, description in method_transformations:
            if re.search(pattern, transformed):
                transformed = re.sub(pattern, replacement, transformed)
                changes.append(f"Updated method call: {description}")
        
        # 4. Add configuration import if needed
        if 'RAGPipeline' in transformed and 'from src.core.pipeline import RAGPipeline' in transformed:
            # Check if we need to add Path import
            if 'from pathlib import Path' not in transformed and 'import Path' not in transformed:
                # Add Path import after other imports
                lines = transformed.split('\n')
                import_end = 0
                for i, line in enumerate(lines):
                    if line.strip().startswith(('import ', 'from ')) and not line.strip().startswith('#'):
                        import_end = i
                
                if import_end > 0:
                    lines.insert(import_end + 1, 'from pathlib import Path')
                    transformed = '\n'.join(lines)
                    changes.append("Added Path import for configuration")
        
        # 5. Check for potential issues
        potential_issues = [
            (r'\.save_index\s*\(', "save_index() method used - not available in new system"),
            (r'\.load_index\s*\(', "load_index() method used - not available in new system"),
            (r'\.get_stats\s*\(', "get_stats() method used - use pipeline.get_component() to access stats"),
            (r'\.clear_index\s*\(', "clear_index() method used - use pipeline.clear_index()"),
        ]
        
        for pattern, issue_description in potential_issues:
            if re.search(pattern, transformed):
                issues.append(issue_description)
        
        return transformed, changes, issues
    
    def _determine_config_path(self, file_path: Path) -> str:
        """Determine appropriate config file path for a given file."""
        relative_path = file_path.relative_to(self.project_root)
        
        # Choose config based on file location/purpose
        if 'test' in str(relative_path).lower():
            return "config/test.yaml"
        elif 'demo' in str(relative_path).lower():
            return "config/dev.yaml"
        elif 'production' in str(relative_path).lower():
            return "config/production.yaml"
        else:
            return "config/default.yaml"
    
    def _save_migration_session(self, session: MigrationSession):
        """Save migration session for rollback purposes."""
        session_file = self.backup_dir / f"migration_session_{self.session_id}.json"
        
        with open(session_file, 'w') as f:
            json.dump(asdict(session), f, indent=2, default=str)
        
        print(f"💾 Migration session saved: {session_file}")
    
    def rollback_migration(self, session_id: Optional[str] = None) -> bool:
        """Rollback a previous migration."""
        if session_id is None:
            # Find latest migration session
            session_files = list(self.backup_dir.glob("migration_session_*.json"))
            if not session_files:
                print("❌ No migration sessions found to rollback")
                return False
            
            latest_session = max(session_files, key=lambda p: p.stat().st_mtime)
        else:
            latest_session = self.backup_dir / f"migration_session_{session_id}.json"
            if not latest_session.exists():
                print(f"❌ Migration session {session_id} not found")
                return False
        
        print(f"🔄 Rolling back migration: {latest_session.name}")
        
        # Load session data
        with open(latest_session, 'r') as f:
            session_data = json.load(f)
        
        rollback_info = session_data.get('rollback_info', {})
        
        if not rollback_info:
            print("❌ No rollback information found")
            return False
        
        # Restore each file
        restored_count = 0
        for file_path, backup_path in rollback_info.items():
            try:
                if Path(backup_path).exists():
                    shutil.copy2(backup_path, file_path)
                    print(f"✅ Restored: {Path(file_path).relative_to(self.project_root)}")
                    restored_count += 1
                else:
                    print(f"⚠️ Backup not found: {backup_path}")
            except Exception as e:
                print(f"❌ Failed to restore {file_path}: {e}")
        
        print(f"\n📊 Rollback complete: {restored_count} files restored")
        return restored_count > 0

def main():
    """Main migration workflow."""
    parser = argparse.ArgumentParser(description="Automated BasicRAG to Modular Architecture Migration")
    parser.add_argument("--analyze", action="store_true", help="Analyze only, no changes")
    parser.add_argument("--migrate", action="store_true", help="Perform full migration")
    parser.add_argument("--rollback", action="store_true", help="Rollback last migration")
    parser.add_argument("--session-id", type=str, help="Specific session ID to rollback")
    parser.add_argument("--file", type=str, help="Migrate specific file")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be done without making changes")
    
    args = parser.parse_args()
    
    if not any([args.analyze, args.migrate, args.rollback, args.file]):
        parser.print_help()
        sys.exit(1)
    
    migrator = AutomatedMigrator(project_root, dry_run=args.dry_run or args.analyze)
    
    if args.rollback:
        success = migrator.rollback_migration(args.session_id)
        sys.exit(0 if success else 1)
    
    elif args.file:
        file_path = Path(args.file)
        if not file_path.exists():
            print(f"❌ File not found: {file_path}")
            sys.exit(1)
        
        session = migrator.migrate_codebase([file_path])
        
    elif args.migrate or args.analyze:
        session = migrator.migrate_codebase()
    
    # Show final results
    if session.success_rate == 1.0:
        print("\n🎉 Migration completed successfully!")
    elif session.success_rate > 0.5:
        print(f"\n⚠️ Migration partially successful ({session.success_rate:.1%})")
        print("Review issues and consider manual fixes for failed files")
    else:
        print("\n❌ Migration had significant issues")
        print("Consider rollback and manual review")
    
    if not args.dry_run and not args.analyze:
        print(f"\n💡 To rollback: python {__file__} --rollback --session-id {session.session_id}")

if __name__ == "__main__":
    main()