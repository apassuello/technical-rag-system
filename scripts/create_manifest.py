#!/usr/bin/env python3
"""
Data Manifest Generator
Creates comprehensive catalog of all data assets with metadata

Features:
- Document catalog with categories
- Version tracking and checksums
- Quality metrics
- Evaluation dataset information
- Dependency tracking
"""

import argparse
import sys
from pathlib import Path
from typing import Dict, List
from datetime import datetime
import json
import hashlib

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class ManifestGenerator:
    """Generate comprehensive data manifest"""

    def __init__(self, data_root: Path):
        self.data_root = data_root
        self.manifest = {
            'manifest_version': '1.0',
            'generated_timestamp': datetime.now().isoformat(),
            'data_root': str(data_root),
            'categories': {},
            'documents': [],
            'evaluation_datasets': [],
            'statistics': {
                'total_documents': 0,
                'total_size_mb': 0,
                'total_pages': 0,
                'categories': {}
            }
        }

    def categorize_document(self, filename: str) -> str:
        """Categorize document based on filename"""
        filename_lower = filename.lower()

        if 'riscv' in filename_lower or 'risc-v' in filename_lower or 'vext' in filename_lower:
            return 'riscv_technical'
        elif 'eecs-' in filename_lower or any(c.isdigit() for c in filename[:10]):
            return 'research_papers'
        elif any(kw in filename_lower for kw in ['fda', 'validation', 'guidance', 'samd', 'aiml', 'gmlp', 'premarket']):
            return 'regulatory_medical'
        else:
            return 'general'

    def compute_hash(self, filepath: Path) -> str:
        """Compute file hash"""
        hash_obj = hashlib.sha256()
        with open(filepath, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                hash_obj.update(chunk)
        return hash_obj.hexdigest()

    def process_pdf(self, filepath: Path) -> Dict:
        """Process PDF and extract information"""
        doc_info = {
            'filename': filepath.name,
            'relative_path': str(filepath.relative_to(self.data_root)),
            'absolute_path': str(filepath),
            'category': self.categorize_document(filepath.name)
        }

        # File stats
        stats = filepath.stat()
        doc_info['size_bytes'] = stats.st_size
        doc_info['size_mb'] = round(stats.st_size / (1024 * 1024), 2)
        doc_info['last_modified'] = datetime.fromtimestamp(stats.st_mtime).isoformat()
        doc_info['checksum_sha256'] = self.compute_hash(filepath)

        # Try to extract PDF metadata
        try:
            import fitz
            pdf = fitz.open(filepath)

            doc_info['pages'] = len(pdf)
            doc_info['format'] = 'PDF'

            # PDF metadata
            metadata = pdf.metadata
            doc_info['metadata'] = {
                'title': metadata.get('title', ''),
                'author': metadata.get('author', ''),
                'subject': metadata.get('subject', ''),
                'creator': metadata.get('creator', ''),
            }

            # Remove empty metadata fields
            doc_info['metadata'] = {k: v for k, v in doc_info['metadata'].items() if v}

            # Text statistics
            sample_pages = min(3, len(pdf))
            total_chars = sum(len(pdf[i].get_text()) for i in range(sample_pages))
            doc_info['text_quality'] = {
                'sample_pages': sample_pages,
                'avg_chars_per_page': total_chars // sample_pages if sample_pages > 0 else 0,
                'has_text': total_chars > 100
            }

            pdf.close()

        except ImportError:
            doc_info['format'] = 'PDF (PyMuPDF unavailable)'
        except Exception as e:
            doc_info['processing_error'] = str(e)

        return doc_info

    def scan_directory(self, directory: Path, category: str = None):
        """Scan directory for documents"""
        if not directory.exists():
            return

        # Find all PDFs
        for pdf_file in sorted(directory.glob('*.pdf')):
            doc_info = self.process_pdf(pdf_file)

            if category:
                doc_info['directory_category'] = category

            self.manifest['documents'].append(doc_info)

            # Update statistics
            self.manifest['statistics']['total_documents'] += 1
            self.manifest['statistics']['total_size_mb'] += doc_info.get('size_mb', 0)
            self.manifest['statistics']['total_pages'] += doc_info.get('pages', 0)

            # Category statistics
            cat = doc_info['category']
            if cat not in self.manifest['statistics']['categories']:
                self.manifest['statistics']['categories'][cat] = {
                    'count': 0,
                    'total_pages': 0,
                    'total_size_mb': 0
                }
            self.manifest['statistics']['categories'][cat]['count'] += 1
            self.manifest['statistics']['categories'][cat]['total_pages'] += doc_info.get('pages', 0)
            self.manifest['statistics']['categories'][cat]['total_size_mb'] += doc_info.get('size_mb', 0)

    def scan_evaluation_data(self):
        """Scan evaluation directory for datasets"""
        eval_dir = self.data_root / 'evaluation'
        if not eval_dir.exists():
            return

        # Look for YAML files
        for yaml_file in sorted(eval_dir.glob('*.yaml')) + sorted(eval_dir.glob('*.yml')):
            dataset_info = {
                'filename': yaml_file.name,
                'path': str(yaml_file.relative_to(self.data_root)),
                'type': 'evaluation_dataset',
                'format': 'YAML'
            }

            # Read YAML content
            try:
                import yaml
                with open(yaml_file, 'r') as f:
                    data = yaml.safe_load(f)

                if 'queries' in data:
                    dataset_info['query_count'] = len(data['queries'])

                    # Analyze query distribution
                    if isinstance(data['queries'], list) and len(data['queries']) > 0:
                        difficulties = {}
                        categories = {}

                        for query in data['queries']:
                            # Difficulty distribution
                            diff = query.get('difficulty', 'unknown')
                            difficulties[diff] = difficulties.get(diff, 0) + 1

                            # Category distribution
                            cat = query.get('category', 'unknown')
                            categories[cat] = categories.get(cat, 0) + 1

                        dataset_info['difficulty_distribution'] = difficulties
                        dataset_info['category_distribution'] = categories

                if 'evaluation_metadata' in data:
                    dataset_info['metadata'] = data['evaluation_metadata']

            except Exception as e:
                dataset_info['error'] = str(e)

            self.manifest['evaluation_datasets'].append(dataset_info)

    def generate_manifest(self) -> Dict:
        """Generate complete manifest"""
        print(f"🔍 Scanning data directory: {self.data_root}")

        # Scan all data directories
        directories_to_scan = [
            ('test', 'test_data'),
            ('raw', 'raw_sources'),
            ('processed', 'processed_data'),
            ('samples', 'sample_data')
        ]

        for dir_name, category in directories_to_scan:
            dir_path = self.data_root / dir_name
            if dir_path.exists():
                print(f"  Scanning: {dir_name}/")
                self.scan_directory(dir_path, category)

        # Scan evaluation data
        print("  Scanning: evaluation/")
        self.scan_evaluation_data()

        # Round statistics
        self.manifest['statistics']['total_size_mb'] = round(
            self.manifest['statistics']['total_size_mb'], 2
        )

        for cat_stats in self.manifest['statistics']['categories'].values():
            cat_stats['total_size_mb'] = round(cat_stats['total_size_mb'], 2)

        print(f"\n✅ Manifest generated:")
        print(f"   Documents: {self.manifest['statistics']['total_documents']}")
        print(f"   Total size: {self.manifest['statistics']['total_size_mb']} MB")
        print(f"   Categories: {len(self.manifest['statistics']['categories'])}")

        return self.manifest

    def save_manifest(self, output_path: Path):
        """Save manifest to file"""
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w') as f:
            json.dump(self.manifest, f, indent=2)

        print(f"\n📝 Manifest saved to: {output_path}")


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description='Generate data manifest for RAG system',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        '--data-root', '-d',
        type=Path,
        default=None,
        help='Data root directory (default: data/)'
    )

    parser.add_argument(
        '--output', '-o',
        type=Path,
        default=None,
        help='Output manifest file (default: data/metadata/data_manifest.json)'
    )

    args = parser.parse_args()

    # Set defaults
    if args.data_root is None:
        args.data_root = project_root / 'data'

    if args.output is None:
        args.output = args.data_root / 'metadata' / 'data_manifest.json'

    # Validate data root
    if not args.data_root.exists():
        print(f"❌ Error: Data root not found: {args.data_root}")
        return 1

    # Generate manifest
    try:
        generator = ManifestGenerator(args.data_root)
        manifest = generator.generate_manifest()
        generator.save_manifest(args.output)

        print("\n" + "="*60)
        print("MANIFEST SUMMARY")
        print("="*60)
        print(f"Total Documents: {manifest['statistics']['total_documents']}")
        print(f"Total Size: {manifest['statistics']['total_size_mb']} MB")
        print(f"Total Pages: {manifest['statistics']['total_pages']}")
        print(f"\nCategories:")
        for category, stats in manifest['statistics']['categories'].items():
            print(f"  {category}: {stats['count']} docs, {stats['total_pages']} pages")
        print("="*60)

        return 0

    except Exception as e:
        print(f"❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
