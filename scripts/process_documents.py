#!/usr/bin/env python3
"""
Document Processing Pipeline
Validates, preprocesses, and prepares documents for RAG system

Features:
- PDF validation and quality checks
- Text extraction and preprocessing
- Metadata generation
- Batch processing support
- Quality metrics and statistics
"""

import argparse
import sys
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import hashlib
import shutil

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


class DocumentProcessor:
    """Process and validate documents for RAG system"""

    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.stats = {
            'total_processed': 0,
            'successful': 0,
            'failed': 0,
            'total_pages': 0,
            'total_size_mb': 0,
            'processing_errors': []
        }

    def log(self, message: str, level: str = 'INFO'):
        """Log message if verbose mode enabled"""
        if self.verbose or level in ['ERROR', 'WARNING']:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            print(f"[{timestamp}] [{level}] {message}")

    def validate_pdf(self, filepath: Path) -> Tuple[bool, Optional[str]]:
        """
        Validate PDF file
        Returns: (is_valid, error_message)
        """
        # Check file exists
        if not filepath.exists():
            return False, f"File not found: {filepath}"

        # Check file size (warn if > 50MB)
        size_mb = filepath.stat().st_size / (1024 * 1024)
        if size_mb > 50:
            self.log(f"Warning: Large file ({size_mb:.2f}MB): {filepath.name}", 'WARNING')

        # Try to open with PyMuPDF
        try:
            import fitz  # PyMuPDF
            doc = fitz.open(filepath)
            page_count = len(doc)

            if page_count == 0:
                doc.close()
                return False, "PDF has no pages"

            # Check for text content (at least first 3 pages)
            has_text = False
            for page_num in range(min(3, page_count)):
                text = doc[page_num].get_text().strip()
                if len(text) > 100:  # At least 100 chars
                    has_text = True
                    break

            doc.close()

            if not has_text:
                return False, "PDF appears to be scanned images without text (OCR may be needed)"

            return True, None

        except ImportError:
            self.log("PyMuPDF not installed, skipping PDF validation", 'WARNING')
            return True, None  # Assume valid if we can't check
        except Exception as e:
            return False, f"PDF validation error: {str(e)}"

    def extract_metadata(self, filepath: Path) -> Dict:
        """Extract comprehensive metadata from document"""
        stats = filepath.stat()

        metadata = {
            'filename': filepath.name,
            'original_path': str(filepath),
            'file_size_bytes': stats.st_size,
            'file_size_mb': round(stats.st_size / (1024 * 1024), 2),
            'file_hash': self.compute_file_hash(filepath),
            'processed_timestamp': datetime.now().isoformat(),
            'last_modified': datetime.fromtimestamp(stats.st_mtime).isoformat()
        }

        # Try to extract PDF-specific metadata
        try:
            import fitz
            doc = fitz.open(filepath)

            metadata.update({
                'page_count': len(doc),
                'pdf_metadata': {
                    'title': doc.metadata.get('title', ''),
                    'author': doc.metadata.get('author', ''),
                    'subject': doc.metadata.get('subject', ''),
                    'creator': doc.metadata.get('creator', ''),
                    'producer': doc.metadata.get('producer', ''),
                },
                'format': 'PDF'
            })

            # Extract text statistics from first few pages
            total_chars = 0
            total_words = 0
            for page_num in range(min(5, len(doc))):
                text = doc[page_num].get_text()
                total_chars += len(text)
                total_words += len(text.split())

            metadata['text_statistics'] = {
                'sample_chars': total_chars,
                'sample_words': total_words,
                'avg_chars_per_page': round(total_chars / min(5, len(doc))) if len(doc) > 0 else 0
            }

            doc.close()

        except ImportError:
            metadata['format'] = 'PDF (metadata extraction unavailable)'
        except Exception as e:
            self.log(f"Metadata extraction error: {e}", 'WARNING')
            metadata['extraction_error'] = str(e)

        return metadata

    def compute_file_hash(self, filepath: Path, algorithm: str = 'sha256') -> str:
        """Compute file hash for deduplication and verification"""
        hash_obj = hashlib.new(algorithm)
        with open(filepath, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                hash_obj.update(chunk)
        return hash_obj.hexdigest()

    def process_document(
        self,
        input_path: Path,
        output_dir: Path,
        metadata_dir: Path,
        skip_validation: bool = False
    ) -> Tuple[bool, Optional[Dict]]:
        """
        Process a single document
        Returns: (success, metadata)
        """
        self.log(f"Processing: {input_path.name}")

        # Validate if not skipped
        if not skip_validation:
            is_valid, error = self.validate_pdf(input_path)
            if not is_valid:
                self.log(f"Validation failed: {error}", 'ERROR')
                self.stats['failed'] += 1
                self.stats['processing_errors'].append({
                    'file': str(input_path),
                    'error': error
                })
                return False, None

        # Extract metadata
        try:
            metadata = self.extract_metadata(input_path)
        except Exception as e:
            self.log(f"Metadata extraction failed: {e}", 'ERROR')
            self.stats['failed'] += 1
            return False, None

        # Copy to processed directory with preserved name
        try:
            output_path = output_dir / input_path.name
            shutil.copy2(input_path, output_path)
            metadata['processed_path'] = str(output_path)
            self.log(f"Copied to: {output_path}")
        except Exception as e:
            self.log(f"Copy failed: {e}", 'ERROR')
            self.stats['failed'] += 1
            return False, None

        # Save metadata
        try:
            metadata_file = metadata_dir / f"{input_path.stem}_metadata.json"
            with open(metadata_file, 'w') as f:
                json.dump(metadata, f, indent=2)
            self.log(f"Metadata saved: {metadata_file}")
        except Exception as e:
            self.log(f"Metadata save failed: {e}", 'WARNING')

        # Update stats
        self.stats['successful'] += 1
        self.stats['total_pages'] += metadata.get('page_count', 0)
        self.stats['total_size_mb'] += metadata.get('file_size_mb', 0)

        return True, metadata

    def process_batch(
        self,
        input_paths: List[Path],
        output_dir: Path,
        metadata_dir: Path,
        skip_validation: bool = False
    ) -> Dict:
        """
        Process multiple documents
        Returns: processing statistics
        """
        # Ensure output directories exist
        output_dir.mkdir(parents=True, exist_ok=True)
        metadata_dir.mkdir(parents=True, exist_ok=True)

        self.log(f"Processing {len(input_paths)} documents...")

        processed_docs = []
        for input_path in input_paths:
            self.stats['total_processed'] += 1
            success, metadata = self.process_document(
                input_path, output_dir, metadata_dir, skip_validation
            )
            if success and metadata:
                processed_docs.append(metadata)

        # Generate batch summary
        summary = {
            'processing_timestamp': datetime.now().isoformat(),
            'statistics': self.stats,
            'processed_documents': processed_docs,
            'output_directory': str(output_dir),
            'metadata_directory': str(metadata_dir)
        }

        # Save batch summary
        summary_file = metadata_dir / f"batch_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)

        self.log(f"\n{'='*60}")
        self.log(f"Processing complete!")
        self.log(f"  Total processed: {self.stats['total_processed']}")
        self.log(f"  Successful: {self.stats['successful']}")
        self.log(f"  Failed: {self.stats['failed']}")
        self.log(f"  Total pages: {self.stats['total_pages']}")
        self.log(f"  Total size: {self.stats['total_size_mb']:.2f} MB")
        self.log(f"  Summary saved: {summary_file}")
        self.log(f"{'='*60}\n")

        return summary


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description='Process documents for RAG system',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process a single document
  python process_documents.py --input data/raw/document.pdf

  # Process all PDFs in a directory
  python process_documents.py --input data/raw/ --batch

  # Skip validation (faster, use with trusted sources)
  python process_documents.py --input data/raw/ --batch --skip-validation

  # Custom output directory
  python process_documents.py --input data/raw/ --output data/custom_output/
        """
    )

    parser.add_argument(
        '--input', '-i',
        type=Path,
        required=True,
        help='Input file or directory'
    )

    parser.add_argument(
        '--output', '-o',
        type=Path,
        default=None,
        help='Output directory (default: data/processed/)'
    )

    parser.add_argument(
        '--batch', '-b',
        action='store_true',
        help='Process all PDFs in input directory'
    )

    parser.add_argument(
        '--skip-validation',
        action='store_true',
        help='Skip PDF validation (faster)'
    )

    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Verbose output'
    )

    args = parser.parse_args()

    # Set default output directories
    if args.output is None:
        args.output = project_root / 'data' / 'processed'

    metadata_dir = project_root / 'data' / 'metadata' / 'manifests'

    # Create processor
    processor = DocumentProcessor(verbose=args.verbose)

    # Determine input files
    if args.input.is_file():
        if args.batch:
            print("❌ Error: --batch flag used with single file input")
            return 1
        input_files = [args.input]
    elif args.input.is_dir():
        if not args.batch:
            print("❌ Error: Input is directory, use --batch flag")
            return 1
        input_files = list(args.input.glob('*.pdf'))
        if not input_files:
            print(f"❌ Error: No PDF files found in {args.input}")
            return 1
    else:
        print(f"❌ Error: Input path not found: {args.input}")
        return 1

    # Process documents
    try:
        summary = processor.process_batch(
            input_files,
            args.output,
            metadata_dir,
            skip_validation=args.skip_validation
        )

        # Return exit code based on results
        if processor.stats['failed'] > 0:
            return 1 if processor.stats['successful'] == 0 else 0
        return 0

    except Exception as e:
        print(f"❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
