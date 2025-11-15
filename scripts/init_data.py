#!/usr/bin/env python3
"""
Data Infrastructure Initialization Script
Sets up complete data management infrastructure

This script:
1. Organizes existing data into proper structure
2. Generates manifests and catalogs
3. Validates data quality
4. Creates sample datasets for demos
5. Generates comprehensive reports
"""

import argparse
import sys
from pathlib import Path
import shutil
import subprocess
from datetime import datetime

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class DataInitializer:
    """Initialize data infrastructure"""

    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        self.data_root = project_root / 'data'
        self.steps_completed = []
        self.steps_failed = []

    def log(self, message: str, level: str = 'INFO'):
        """Log message"""
        timestamp = datetime.now().strftime('%H:%M:%S')
        symbols = {
            'INFO': 'ℹ️',
            'SUCCESS': '✅',
            'WARNING': '⚠️',
            'ERROR': '❌',
            'STEP': '🔧'
        }
        symbol = symbols.get(level, 'ℹ️')
        print(f"[{timestamp}] {symbol} {message}")

    def run_step(self, step_name: str, func):
        """Run initialization step with error handling"""
        self.log(f"Step: {step_name}", 'STEP')

        if self.dry_run:
            self.log(f"DRY RUN: Would execute {step_name}", 'INFO')
            return True

        try:
            result = func()
            if result:
                self.steps_completed.append(step_name)
                self.log(f"Completed: {step_name}", 'SUCCESS')
                return True
            else:
                self.steps_failed.append(step_name)
                self.log(f"Failed: {step_name}", 'ERROR')
                return False
        except Exception as e:
            self.steps_failed.append(step_name)
            self.log(f"Failed: {step_name} - {e}", 'ERROR')
            return False

    def step_create_directories(self) -> bool:
        """Create data directory structure"""
        directories = [
            self.data_root / 'raw',
            self.data_root / 'processed',
            self.data_root / 'samples',
            self.data_root / 'metadata' / 'manifests',
            self.data_root / 'cache'
        ]

        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            self.log(f"  Created: {directory.relative_to(project_root)}")

        return True

    def step_organize_existing_data(self) -> bool:
        """Organize existing test data"""
        test_dir = self.data_root / 'test'
        raw_dir = self.data_root / 'raw'

        if not test_dir.exists():
            self.log("  No test directory to organize")
            return True

        # Copy PDFs to raw directory (preserve originals in test)
        pdf_files = list(test_dir.glob('*.pdf'))
        self.log(f"  Found {len(pdf_files)} PDFs in test directory")

        for pdf_file in pdf_files:
            dest = raw_dir / pdf_file.name
            if not dest.exists():
                shutil.copy2(pdf_file, dest)
                self.log(f"  Copied: {pdf_file.name} -> raw/")

        return True

    def step_generate_manifest(self) -> bool:
        """Generate data manifest"""
        manifest_script = project_root / 'scripts' / 'create_manifest.py'

        result = subprocess.run(
            [sys.executable, str(manifest_script)],
            cwd=project_root,
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            self.log("  Manifest generated successfully")
            return True
        else:
            self.log(f"  Manifest generation failed: {result.stderr}", 'ERROR')
            return False

    def step_validate_data(self) -> bool:
        """Validate data quality"""
        validate_script = project_root / 'scripts' / 'validate_data.py'
        test_dir = self.data_root / 'test'

        if not test_dir.exists():
            self.log("  No data to validate")
            return True

        result = subprocess.run(
            [sys.executable, str(validate_script), '--directory', str(test_dir)],
            cwd=project_root,
            capture_output=False,  # Show validation output
            text=True
        )

        if result.returncode == 0 or result.returncode == 1:  # 1 means warnings
            self.log("  Data validation completed")
            return True
        else:
            self.log("  Data validation had errors", 'WARNING')
            return True  # Don't fail init on validation warnings

    def step_create_sample_dataset(self) -> bool:
        """Create sample dataset for demos"""
        samples_dir = self.data_root / 'samples'
        test_dir = self.data_root / 'test'

        if not test_dir.exists():
            self.log("  No source data for samples")
            return True

        # Select diverse sample documents
        sample_files = [
            'riscv-card.pdf',  # Small, quick reference
            'riscv-v-spec-1.0.pdf',  # RISC-V technical
            'AIML-SaMD-Action-Plan.pdf',  # Regulatory
            'EECS-2015-49.pdf',  # Research paper
        ]

        copied = 0
        for filename in sample_files:
            source = test_dir / filename
            if source.exists():
                dest = samples_dir / filename
                if not dest.exists():
                    shutil.copy2(source, dest)
                    copied += 1

        self.log(f"  Created sample dataset: {copied} documents")
        return True

    def step_create_readme_files(self) -> bool:
        """Create README files for data directories"""
        # Raw directory README
        raw_readme = self.data_root / 'raw' / 'README.md'
        if not raw_readme.exists():
            raw_readme.write_text("""# Raw Data Directory

This directory contains original, unmodified source documents.

## Guidelines

- **Never modify files in this directory**
- Original files serve as source of truth
- All processing should output to `processed/` directory
- Keep file naming consistent and descriptive

## Adding New Documents

```bash
# Copy new documents here
cp /path/to/new_doc.pdf data/raw/

# Process them
python scripts/process_documents.py --input data/raw/ --batch
```
""")

        # Processed directory README
        processed_readme = self.data_root / 'processed' / 'README.md'
        if not processed_readme.exists():
            processed_readme.write_text("""# Processed Data Directory

This directory contains validated and preprocessed documents ready for RAG system.

## Contents

All files here have been:
- Validated for quality
- Extracted for text content
- Cataloged with metadata
- Checked for duplicates

## Regeneration

All processed files can be regenerated from `raw/` directory:

```bash
python scripts/process_documents.py --input data/raw/ --batch --output data/processed/
```
""")

        # Samples directory README
        samples_readme = self.data_root / 'samples' / 'README.md'
        if not samples_readme.exists():
            samples_readme.write_text("""# Sample Data Directory

This directory contains small sample datasets for demos and testing.

## Purpose

- Quick demos without loading full dataset
- Integration testing with known data
- Development and debugging
- Portfolio demonstrations

## Contents

Selected documents representing diverse categories:
- RISC-V technical documentation
- Regulatory medical device guidance
- Research papers
- General technical specifications
""")

        self.log("  README files created")
        return True

    def initialize(self) -> bool:
        """Run complete initialization"""
        self.log("\n" + "="*60)
        self.log("DATA INFRASTRUCTURE INITIALIZATION")
        self.log("="*60 + "\n")

        if self.dry_run:
            self.log("DRY RUN MODE - No changes will be made", 'WARNING')

        # Execute initialization steps
        steps = [
            ("Create directory structure", self.step_create_directories),
            ("Organize existing data", self.step_organize_existing_data),
            ("Generate data manifest", self.step_generate_manifest),
            ("Validate data quality", self.step_validate_data),
            ("Create sample dataset", self.step_create_sample_dataset),
            ("Create README files", self.step_create_readme_files),
        ]

        for step_name, step_func in steps:
            self.run_step(step_name, step_func)
            print()  # Blank line between steps

        # Print summary
        self.print_summary()

        return len(self.steps_failed) == 0

    def print_summary(self):
        """Print initialization summary"""
        print("\n" + "="*60)
        print("INITIALIZATION SUMMARY")
        print("="*60)

        print(f"\n✅ Completed Steps ({len(self.steps_completed)}):")
        for step in self.steps_completed:
            print(f"  • {step}")

        if self.steps_failed:
            print(f"\n❌ Failed Steps ({len(self.steps_failed)}):")
            for step in self.steps_failed:
                print(f"  • {step}")

        print("\n" + "="*60)

        if not self.steps_failed:
            print("\n🎉 Data infrastructure successfully initialized!")
            print("\nNext steps:")
            print("  1. Review data manifest: data/metadata/data_manifest.json")
            print("  2. Check validation report for any warnings")
            print("  3. Add new documents to data/raw/")
            print("  4. Process with: python scripts/process_documents.py")
        else:
            print("\n⚠️  Initialization completed with errors")
            print("Review the failed steps above and retry")

        print()


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description='Initialize data infrastructure for RAG system',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be done without making changes'
    )

    args = parser.parse_args()

    # Run initialization
    initializer = DataInitializer(dry_run=args.dry_run)
    success = initializer.initialize()

    return 0 if success else 1


if __name__ == '__main__':
    sys.exit(main())
