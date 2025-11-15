#!/usr/bin/env python3
"""
Model Verification Script for RAG Portfolio System

This script verifies that all required models are properly installed and loadable.
It performs comprehensive validation including:
- Model existence checks
- Loading tests
- Basic inference tests
- Size verification

Usage:
    python scripts/verify_models.py                  # Verify all models
    python scripts/verify_models.py --quick          # Quick check only (no loading)
    python scripts/verify_models.py --model spacy   # Verify specific model type
    python scripts/verify_models.py --verbose        # Detailed output
"""

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


class ModelVerifier:
    """Verifies ML models are properly installed and functional."""

    # Model specifications (must match download_models.py)
    MODELS = {
        "sentence_transformers": [
            {
                "name": "sentence-transformers/all-MiniLM-L6-v2",
                "required": True,
                "test_text": "This is a test sentence.",
                "expected_dim": 384,
            },
            {
                "name": "sentence-transformers/multi-qa-MiniLM-L6-cos-v1",
                "required": True,
                "test_text": "What is machine learning?",
                "expected_dim": 384,
            },
        ],
        "cross_encoder": [
            {
                "name": "cross-encoder/ms-marco-MiniLM-L6-v2",
                "required": False,
                "test_pairs": [("query", "relevant document"), ("query", "irrelevant document")],
            },
        ],
        "spacy": [
            {
                "name": "en_core_web_sm",
                "required": False,
                "test_text": "Apple is looking at buying U.K. startup for $1 billion.",
            },
        ],
        "ollama": [
            {
                "name": "llama3.2:3b",
                "required": False,
                "test_prompt": "Hello, world!",
            },
        ],
    }

    def __init__(self, cache_dir: Optional[Path] = None):
        """
        Initialize the model verifier.

        Args:
            cache_dir: Directory where models are cached
        """
        self.cache_dir = cache_dir or Path.home() / ".cache" / "huggingface"
        self.results = {
            "total": 0,
            "passed": 0,
            "failed": 0,
            "warnings": 0,
        }

    def verify_sentence_transformer(self, model_spec: Dict, quick: bool = False) -> Tuple[bool, str]:
        """
        Verify a sentence transformer model.

        Args:
            model_spec: Model specification dictionary
            quick: If True, only check existence, don't load

        Returns:
            Tuple of (success, message)
        """
        model_name = model_spec["name"]

        try:
            # Check cache exists
            model_path = self.cache_dir / "hub" / f"models--{model_name.replace('/', '--')}"
            if not model_path.exists():
                return False, f"Model not found in cache: {model_path}"

            if quick:
                return True, "Model found in cache"

            # Try to load model
            from sentence_transformers import SentenceTransformer

            logger.info(f"  Loading {model_name}...")
            model = SentenceTransformer(model_name)

            # Test embedding generation
            test_text = model_spec.get("test_text", "Test")
            embedding = model.encode(test_text)

            # Verify dimensions
            expected_dim = model_spec.get("expected_dim")
            if expected_dim and len(embedding) != expected_dim:
                return False, f"Dimension mismatch: expected {expected_dim}, got {len(embedding)}"

            return True, f"Model loaded successfully, embedding dim: {len(embedding)}"

        except Exception as e:
            return False, f"Failed to load model: {str(e)}"

    def verify_cross_encoder(self, model_spec: Dict, quick: bool = False) -> Tuple[bool, str]:
        """
        Verify a cross-encoder model.

        Args:
            model_spec: Model specification dictionary
            quick: If True, only check existence, don't load

        Returns:
            Tuple of (success, message)
        """
        model_name = model_spec["name"]

        try:
            # Check cache exists
            model_path = self.cache_dir / "hub" / f"models--{model_name.replace('/', '--')}"
            if not model_path.exists():
                return False, f"Model not found in cache: {model_path}"

            if quick:
                return True, "Model found in cache"

            # Try to load model
            from sentence_transformers import CrossEncoder

            logger.info(f"  Loading {model_name}...")
            model = CrossEncoder(model_name)

            # Test scoring
            test_pairs = model_spec.get("test_pairs", [("query", "document")])
            scores = model.predict(test_pairs)

            if len(scores) != len(test_pairs):
                return False, f"Score count mismatch: expected {len(test_pairs)}, got {len(scores)}"

            return True, f"Model loaded successfully, generated {len(scores)} scores"

        except Exception as e:
            return False, f"Failed to load model: {str(e)}"

    def verify_spacy_model(self, model_spec: Dict, quick: bool = False) -> Tuple[bool, str]:
        """
        Verify a spaCy model.

        Args:
            model_spec: Model specification dictionary
            quick: If True, only check existence, don't load

        Returns:
            Tuple of (success, message)
        """
        model_name = model_spec["name"]

        try:
            import spacy

            if quick:
                # Just check if model is available
                if spacy.util.is_package(model_name):
                    return True, "Model installed"
                else:
                    return False, "Model not installed"

            # Try to load model
            logger.info(f"  Loading {model_name}...")
            nlp = spacy.load(model_name)

            # Test NLP processing
            test_text = model_spec.get("test_text", "This is a test.")
            doc = nlp(test_text)

            # Verify basic functionality
            token_count = len(doc)
            entities = list(doc.ents)

            return True, f"Model loaded, processed {token_count} tokens, found {len(entities)} entities"

        except Exception as e:
            return False, f"Failed to load model: {str(e)}"

    def verify_ollama_model(self, model_spec: Dict, quick: bool = False) -> Tuple[bool, str]:
        """
        Verify an Ollama model.

        Args:
            model_spec: Model specification dictionary
            quick: If True, only check existence, don't test

        Returns:
            Tuple of (success, message)
        """
        model_name = model_spec["name"]

        try:
            # Check if Ollama is installed
            try:
                subprocess.run(["ollama", "--version"], capture_output=True, check=True)
            except (subprocess.CalledProcessError, FileNotFoundError):
                return False, "Ollama not installed"

            # Check if model is available
            result = subprocess.run(
                ["ollama", "list"],
                capture_output=True,
                text=True,
                timeout=10
            )

            if model_name not in result.stdout:
                return False, "Model not pulled"

            if quick:
                return True, "Model available"

            # Test generation (optional, can be slow)
            logger.info(f"  Testing {model_name} generation...")
            test_prompt = model_spec.get("test_prompt", "Hello")

            result = subprocess.run(
                ["ollama", "run", model_name, test_prompt],
                capture_output=True,
                text=True,
                timeout=30
            )

            if result.returncode == 0 and result.stdout.strip():
                return True, f"Model responded successfully ({len(result.stdout)} chars)"
            else:
                return False, "Model failed to generate response"

        except subprocess.TimeoutExpired:
            return False, "Model response timeout"
        except Exception as e:
            return False, f"Failed to verify model: {str(e)}"

    def verify_all(
        self,
        model_types: Optional[List[str]] = None,
        quick: bool = False,
        verbose: bool = False
    ) -> Dict[str, int]:
        """
        Verify all models.

        Args:
            model_types: Specific model types to verify (None = all)
            quick: Quick check only (no loading)
            verbose: Print detailed output

        Returns:
            Dictionary with verification statistics
        """
        logger.info("=" * 70)
        logger.info("MODEL VERIFICATION")
        logger.info("=" * 70)
        logger.info(f"Mode: {'Quick check' if quick else 'Full verification'}")
        logger.info(f"Cache directory: {self.cache_dir}")
        logger.info("=" * 70)

        for model_type, models in self.MODELS.items():
            # Skip if not in requested types
            if model_types and model_type not in model_types:
                continue

            logger.info(f"\n--- {model_type.upper()} MODELS ---")

            for model in models:
                self.results["total"] += 1
                model_name = model["name"]
                required = model.get("required", False)

                logger.info(f"\n[{self.results['total']}] {model_name}")
                if verbose:
                    logger.info(f"  Required: {required}")

                # Verify based on type
                success = False
                message = ""

                try:
                    if model_type == "sentence_transformers":
                        success, message = self.verify_sentence_transformer(model, quick)
                    elif model_type == "cross_encoder":
                        success, message = self.verify_cross_encoder(model, quick)
                    elif model_type == "spacy":
                        success, message = self.verify_spacy_model(model, quick)
                    elif model_type == "ollama":
                        success, message = self.verify_ollama_model(model, quick)

                except Exception as e:
                    success = False
                    message = f"Verification error: {str(e)}"

                # Update results
                if success:
                    self.results["passed"] += 1
                    logger.info(f"  ✓ PASSED: {message}")
                else:
                    if required:
                        self.results["failed"] += 1
                        logger.error(f"  ✗ FAILED: {message}")
                    else:
                        self.results["warnings"] += 1
                        logger.warning(f"  ⚠ OPTIONAL: {message}")

        # Print summary
        logger.info("\n" + "=" * 70)
        logger.info("VERIFICATION SUMMARY")
        logger.info("=" * 70)
        logger.info(f"Total models checked: {self.results['total']}")
        logger.info(f"Passed: {self.results['passed']}")
        logger.info(f"Failed (required): {self.results['failed']}")
        logger.info(f"Warnings (optional): {self.results['warnings']}")

        if self.results["failed"] > 0:
            logger.error(f"\n✗ VERIFICATION FAILED: {self.results['failed']} required models not working")
            logger.error("Run 'python scripts/download_models.py' to download missing models")
        elif self.results["warnings"] > 0:
            logger.warning(f"\n⚠ VERIFICATION PASSED WITH WARNINGS: {self.results['warnings']} optional models missing")
        else:
            logger.info(f"\n✓ ALL MODELS VERIFIED SUCCESSFULLY")

        logger.info("=" * 70)

        return self.results


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Verify ML models for RAG Portfolio System",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        "--model-type",
        choices=["sentence_transformers", "cross_encoder", "spacy", "ollama"],
        help="Verify only specific model type"
    )

    parser.add_argument(
        "--quick",
        action="store_true",
        help="Quick check only (existence, no loading)"
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Print detailed output"
    )

    parser.add_argument(
        "--cache-dir",
        type=Path,
        help="Custom cache directory (default: ~/.cache/huggingface)"
    )

    args = parser.parse_args()

    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Create verifier
    verifier = ModelVerifier(cache_dir=args.cache_dir)

    # Determine model types
    model_types = [args.model_type] if args.model_type else None

    # Verify models
    results = verifier.verify_all(
        model_types=model_types,
        quick=args.quick,
        verbose=args.verbose
    )

    # Exit with error code if any required models failed
    if results["failed"] > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
