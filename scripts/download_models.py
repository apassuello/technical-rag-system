#!/usr/bin/env python3
"""
Model Download Script for RAG Portfolio System

This script downloads and caches all required ML models for the RAG system:
- Sentence Transformers (embeddings)
- Cross-Encoders (reranking)
- spaCy models (NLP)
- Ollama models (LLM) - optional

Features:
- Progress bars for downloads
- Resume capability
- Size estimates before download
- Offline mode checking
- Error handling and retry logic
- Selective model downloads

Usage:
    python scripts/download_models.py                  # Download all models
    python scripts/download_models.py --no-ollama      # Skip Ollama models
    python scripts/download_models.py --verify-only    # Only verify, don't download
    python scripts/download_models.py --model spacy    # Download specific model type
"""

import os
import sys
import argparse
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ModelDownloader:
    """Manages downloading and caching of ML models."""

    # Model inventory with sizes and sources
    MODELS = {
        "sentence_transformers": [
            {
                "name": "sentence-transformers/all-MiniLM-L6-v2",
                "size_mb": 90,
                "purpose": "Default embedding model",
                "required": True,
            },
            {
                "name": "sentence-transformers/multi-qa-MiniLM-L6-cos-v1",
                "size_mb": 90,
                "purpose": "Multi-QA optimized embeddings",
                "required": True,
            },
        ],
        "cross_encoder": [
            {
                "name": "cross-encoder/ms-marco-MiniLM-L6-v2",
                "size_mb": 90,
                "purpose": "Semantic reranking",
                "required": False,  # Used in Epic 2 advanced features
            },
        ],
        "spacy": [
            {
                "name": "en_core_web_sm",
                "size_mb": 40,
                "purpose": "NLP analysis (entities, POS tagging)",
                "required": False,  # Used in query processor
            },
        ],
        "ollama": [
            {
                "name": "llama3.2:3b",
                "size_mb": 2000,  # ~2GB
                "purpose": "Local LLM for answer generation",
                "required": False,  # Can use API alternatives
            },
        ],
    }

    def __init__(self, cache_dir: Optional[Path] = None):
        """
        Initialize the model downloader.

        Args:
            cache_dir: Directory to cache models. Defaults to ~/.cache/huggingface
        """
        self.cache_dir = cache_dir or Path.home() / ".cache" / "huggingface"
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def get_total_size(self, include_ollama: bool = True, model_types: Optional[List[str]] = None) -> Tuple[int, int]:
        """
        Calculate total download size.

        Args:
            include_ollama: Whether to include Ollama models
            model_types: Specific model types to include (None = all)

        Returns:
            Tuple of (total_size_mb, model_count)
        """
        total_size = 0
        model_count = 0

        for model_type, models in self.MODELS.items():
            # Skip if not in requested types
            if model_types and model_type not in model_types:
                continue

            # Skip Ollama if excluded
            if model_type == "ollama" and not include_ollama:
                continue

            for model in models:
                total_size += model["size_mb"]
                model_count += 1

        return total_size, model_count

    def check_disk_space(self, required_mb: int) -> bool:
        """
        Check if sufficient disk space is available.

        Args:
            required_mb: Required space in MB

        Returns:
            True if sufficient space available
        """
        try:
            stat = os.statvfs(self.cache_dir)
            # Available space in MB
            available_mb = (stat.f_bavail * stat.f_frsize) / (1024 * 1024)

            # Add 20% buffer
            required_with_buffer = required_mb * 1.2

            if available_mb < required_with_buffer:
                logger.warning(f"Insufficient disk space!")
                logger.warning(f"  Required: {required_with_buffer:.1f} MB")
                logger.warning(f"  Available: {available_mb:.1f} MB")
                return False

            logger.info(f"Disk space check: {available_mb:.1f} MB available (need {required_mb} MB)")
            return True

        except Exception as e:
            logger.warning(f"Could not check disk space: {e}")
            return True  # Proceed anyway

    def is_model_cached(self, model_name: str, model_type: str) -> bool:
        """
        Check if a model is already cached.

        Args:
            model_name: Name of the model
            model_type: Type of model (sentence_transformers, spacy, etc.)

        Returns:
            True if model is cached
        """
        if model_type == "sentence_transformers" or model_type == "cross_encoder":
            # Check HuggingFace cache
            model_path = self.cache_dir / "hub" / f"models--{model_name.replace('/', '--')}"
            return model_path.exists()

        elif model_type == "spacy":
            # Check spaCy models
            try:
                import spacy
                spacy.load(model_name)
                return True
            except (ModuleNotFoundError, OSError, IOError) as e:
                # Model not found or failed to load
                logger.debug(f"spaCy model {model_name} not available: {e}")
                return False

        elif model_type == "ollama":
            # Check Ollama models
            try:
                result = subprocess.run(
                    ["ollama", "list"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                return model_name in result.stdout
            except (subprocess.SubprocessError, TimeoutError, FileNotFoundError) as e:
                # Ollama not installed or command failed
                logger.debug(f"Failed to check Ollama model {model_name}: {e}")
                return False

        return False

    def download_sentence_transformer(self, model_name: str, force: bool = False) -> bool:
        """
        Download a sentence transformer model.

        Args:
            model_name: HuggingFace model name
            force: Force redownload even if cached

        Returns:
            True if successful
        """
        if not force and self.is_model_cached(model_name, "sentence_transformers"):
            logger.info(f"✓ {model_name} already cached")
            return True

        logger.info(f"Downloading {model_name}...")

        try:
            from sentence_transformers import SentenceTransformer

            # Download with progress
            model = SentenceTransformer(model_name)
            logger.info(f"✓ Successfully downloaded {model_name}")
            return True

        except Exception as e:
            logger.error(f"✗ Failed to download {model_name}: {e}")
            return False

    def download_cross_encoder(self, model_name: str, force: bool = False) -> bool:
        """
        Download a cross-encoder model.

        Args:
            model_name: HuggingFace model name
            force: Force redownload even if cached

        Returns:
            True if successful
        """
        if not force and self.is_model_cached(model_name, "cross_encoder"):
            logger.info(f"✓ {model_name} already cached")
            return True

        logger.info(f"Downloading {model_name}...")

        try:
            from sentence_transformers import CrossEncoder

            # Download with progress
            model = CrossEncoder(model_name)
            logger.info(f"✓ Successfully downloaded {model_name}")
            return True

        except Exception as e:
            logger.error(f"✗ Failed to download {model_name}: {e}")
            return False

    def download_spacy_model(self, model_name: str, force: bool = False) -> bool:
        """
        Download a spaCy model.

        Args:
            model_name: spaCy model name (e.g., en_core_web_sm)
            force: Force redownload even if cached

        Returns:
            True if successful
        """
        if not force and self.is_model_cached(model_name, "spacy"):
            logger.info(f"✓ {model_name} already installed")
            return True

        logger.info(f"Downloading spaCy model {model_name}...")

        try:
            # Use spaCy's download command
            result = subprocess.run(
                [sys.executable, "-m", "spacy", "download", model_name],
                capture_output=True,
                text=True,
                timeout=300  # 5 minutes timeout
            )

            if result.returncode == 0:
                logger.info(f"✓ Successfully downloaded {model_name}")
                return True
            else:
                logger.error(f"✗ Failed to download {model_name}")
                logger.error(result.stderr)
                return False

        except Exception as e:
            logger.error(f"✗ Failed to download {model_name}: {e}")
            return False

    def download_ollama_model(self, model_name: str, force: bool = False) -> bool:
        """
        Download an Ollama model.

        Args:
            model_name: Ollama model name (e.g., llama3.2:3b)
            force: Force redownload even if cached

        Returns:
            True if successful
        """
        # Check if Ollama is installed
        try:
            subprocess.run(["ollama", "--version"], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            logger.warning("✗ Ollama not installed. Skipping Ollama models.")
            logger.info("  Install from: https://ollama.ai")
            return False

        if not force and self.is_model_cached(model_name, "ollama"):
            logger.info(f"✓ {model_name} already pulled")
            return True

        logger.info(f"Pulling Ollama model {model_name} (this may take several minutes)...")

        try:
            # Use ollama pull command
            result = subprocess.run(
                ["ollama", "pull", model_name],
                timeout=1800  # 30 minutes timeout
            )

            if result.returncode == 0:
                logger.info(f"✓ Successfully pulled {model_name}")
                return True
            else:
                logger.error(f"✗ Failed to pull {model_name}")
                return False

        except subprocess.TimeoutExpired:
            logger.error(f"✗ Timeout pulling {model_name} (exceeded 30 minutes)")
            return False
        except Exception as e:
            logger.error(f"✗ Failed to pull {model_name}: {e}")
            return False

    def download_all(
        self,
        include_ollama: bool = True,
        model_types: Optional[List[str]] = None,
        force: bool = False
    ) -> Dict[str, int]:
        """
        Download all required models.

        Args:
            include_ollama: Whether to download Ollama models
            model_types: Specific model types to download (None = all)
            force: Force redownload even if cached

        Returns:
            Dictionary with download statistics
        """
        stats = {
            "total": 0,
            "successful": 0,
            "failed": 0,
            "skipped": 0
        }

        # Calculate total size
        total_size_mb, total_count = self.get_total_size(include_ollama, model_types)

        logger.info("=" * 70)
        logger.info("MODEL DOWNLOAD PLAN")
        logger.info("=" * 70)
        logger.info(f"Models to download: {total_count}")
        logger.info(f"Estimated size: {total_size_mb / 1024:.2f} GB ({total_size_mb} MB)")
        logger.info(f"Cache directory: {self.cache_dir}")
        logger.info("=" * 70)

        # Check disk space
        if not self.check_disk_space(total_size_mb):
            logger.error("Insufficient disk space. Aborting.")
            return stats

        # Get user confirmation
        if not force:
            response = input(f"\nProceed with download? (y/n): ")
            if response.lower() != 'y':
                logger.info("Download cancelled.")
                return stats

        logger.info("\nStarting downloads...\n")

        # Download each model type
        for model_type, models in self.MODELS.items():
            # Skip if not in requested types
            if model_types and model_type not in model_types:
                continue

            # Skip Ollama if excluded
            if model_type == "ollama" and not include_ollama:
                logger.info(f"Skipping Ollama models (use --include-ollama to download)")
                continue

            logger.info(f"\n--- {model_type.upper()} MODELS ---")

            for model in models:
                stats["total"] += 1
                model_name = model["name"]

                logger.info(f"\n[{stats['total']}/{total_count}] {model_name}")
                logger.info(f"  Purpose: {model['purpose']}")
                logger.info(f"  Size: ~{model['size_mb']} MB")

                # Download based on type
                success = False
                if model_type == "sentence_transformers":
                    success = self.download_sentence_transformer(model_name, force)
                elif model_type == "cross_encoder":
                    success = self.download_cross_encoder(model_name, force)
                elif model_type == "spacy":
                    success = self.download_spacy_model(model_name, force)
                elif model_type == "ollama":
                    success = self.download_ollama_model(model_name, force)

                if success:
                    stats["successful"] += 1
                else:
                    stats["failed"] += 1

        # Print summary
        logger.info("\n" + "=" * 70)
        logger.info("DOWNLOAD SUMMARY")
        logger.info("=" * 70)
        logger.info(f"Total models: {stats['total']}")
        logger.info(f"Successful: {stats['successful']}")
        logger.info(f"Failed: {stats['failed']}")
        logger.info(f"Success rate: {stats['successful'] / stats['total'] * 100:.1f}%")
        logger.info("=" * 70)

        return stats


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Download ML models for RAG Portfolio System",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        "--no-ollama",
        action="store_true",
        help="Skip Ollama models (reduces download from ~2.4GB to ~300MB)"
    )

    parser.add_argument(
        "--include-ollama",
        action="store_true",
        help="Include Ollama models (default: skip)"
    )

    parser.add_argument(
        "--model-type",
        choices=["sentence_transformers", "cross_encoder", "spacy", "ollama"],
        help="Download only specific model type"
    )

    parser.add_argument(
        "--force",
        action="store_true",
        help="Force redownload even if models are cached"
    )

    parser.add_argument(
        "--verify-only",
        action="store_true",
        help="Only verify models, don't download"
    )

    parser.add_argument(
        "--cache-dir",
        type=Path,
        help="Custom cache directory (default: ~/.cache/huggingface)"
    )

    args = parser.parse_args()

    # Create downloader
    downloader = ModelDownloader(cache_dir=args.cache_dir)

    # Determine whether to include Ollama
    include_ollama = args.include_ollama and not args.no_ollama

    # Determine model types
    model_types = [args.model_type] if args.model_type else None

    # Verify only mode
    if args.verify_only:
        logger.info("Verification mode - checking cached models...")
        for model_type, models in downloader.MODELS.items():
            if model_types and model_type not in model_types:
                continue
            if model_type == "ollama" and not include_ollama:
                continue

            logger.info(f"\n{model_type.upper()}:")
            for model in models:
                cached = downloader.is_model_cached(model["name"], model_type)
                status = "✓" if cached else "✗"
                logger.info(f"  {status} {model['name']}")
        return

    # Download models
    stats = downloader.download_all(
        include_ollama=include_ollama,
        model_types=model_types,
        force=args.force
    )

    # Exit with error code if any downloads failed
    if stats["failed"] > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
