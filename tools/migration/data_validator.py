"""
Data validation for backend migrations.

This module provides comprehensive validation tools for ensuring
data integrity during backend migrations, including document
validation, embedding verification, and consistency checks.
"""

import logging
from typing import List, Dict, Any, Set, Optional
import numpy as np
from collections import Counter

from src.core.interfaces import Document

logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Raised when validation fails."""
    pass


class DataValidator:
    """
    Comprehensive data validator for backend migrations.
    
    This validator performs multiple levels of validation to ensure
    data integrity during migration between different vector database
    backends. It checks document structure, embedding quality,
    metadata consistency, and content integrity.
    
    Validation Categories:
    - Document Structure: Content, metadata, embedding presence
    - Embedding Quality: Dimension consistency, value ranges, NaN/inf checks
    - Metadata Consistency: Required fields, data types, value ranges
    - Content Integrity: Text quality, encoding issues, length validation
    - Statistical Analysis: Distribution analysis, outlier detection
    """
    
    def __init__(self, strict_mode: bool = False):
        """
        Initialize the data validator.
        
        Args:
            strict_mode: Whether to use strict validation criteria
        """
        self.strict_mode = strict_mode
        
        # Validation thresholds
        self.thresholds = {
            "min_content_length": 10 if not strict_mode else 50,
            "max_content_length": 100000,
            "min_embedding_dim": 50,
            "max_embedding_dim": 4096,
            "max_embedding_value": 10.0,
            "min_embedding_norm": 0.01,
            "max_nan_ratio": 0.0,
            "max_duplicate_ratio": 0.1 if not strict_mode else 0.05
        }
        
        logger.info(f"Data validator initialized (strict_mode={strict_mode})")
    
    def validate_documents(self, documents: List[Document]) -> Dict[str, Any]:
        """
        Perform comprehensive validation of document list.
        
        Args:
            documents: List of documents to validate
            
        Returns:
            Dictionary with validation results
        """
        logger.info(f"Validating {len(documents)} documents...")
        
        validation_result = {
            "is_valid": True,
            "total_documents": len(documents),
            "issues": [],
            "warnings": [],
            "statistics": {},
            "validation_details": {}
        }
        
        try:
            # Basic document validation
            self._validate_document_structure(documents, validation_result)
            
            # Embedding validation
            self._validate_embeddings(documents, validation_result)
            
            # Metadata validation
            self._validate_metadata(documents, validation_result)
            
            # Content validation
            self._validate_content(documents, validation_result)
            
            # Statistical analysis
            self._perform_statistical_analysis(documents, validation_result)
            
            # Duplicate detection
            self._detect_duplicates(documents, validation_result)
            
            # Final validation status
            validation_result["is_valid"] = len(validation_result["issues"]) == 0
            
            if validation_result["is_valid"]:
                logger.info("Document validation passed")
            else:
                logger.warning(f"Document validation failed with {len(validation_result['issues'])} issues")
            
            return validation_result
            
        except Exception as e:
            logger.error(f"Validation failed with exception: {str(e)}")
            validation_result["is_valid"] = False
            validation_result["issues"].append(f"Validation exception: {str(e)}")
            return validation_result
    
    def _validate_document_structure(self, documents: List[Document], result: Dict[str, Any]) -> None:
        """Validate basic document structure."""
        issues = []
        
        for i, doc in enumerate(documents):
            try:
                # Check content presence
                if not doc.content:
                    issues.append(f"Document {i}: Empty content")
                
                # Check content type
                if not isinstance(doc.content, str):
                    issues.append(f"Document {i}: Content is not string")
                
                # Check metadata presence
                if not hasattr(doc, 'metadata') or doc.metadata is None:
                    issues.append(f"Document {i}: Missing metadata")
                elif not isinstance(doc.metadata, dict):
                    issues.append(f"Document {i}: Metadata is not dictionary")
                
                # Check embedding presence
                if not hasattr(doc, 'embedding') or doc.embedding is None:
                    issues.append(f"Document {i}: Missing embedding")
                
            except Exception as e:
                issues.append(f"Document {i}: Structure validation error - {str(e)}")
        
        result["issues"].extend(issues)
        result["validation_details"]["structure"] = {
            "checked_documents": len(documents),
            "structure_issues": len(issues)
        }
    
    def _validate_embeddings(self, documents: List[Document], result: Dict[str, Any]) -> None:
        """Validate embedding quality and consistency."""
        issues = []
        warnings = []
        embedding_dims = []
        embedding_norms = []
        
        for i, doc in enumerate(documents):
            if doc.embedding is None:
                continue
            
            try:
                embedding = np.array(doc.embedding)
                
                # Check dimension
                dim = len(embedding)
                embedding_dims.append(dim)
                
                if dim < self.thresholds["min_embedding_dim"]:
                    issues.append(f"Document {i}: Embedding dimension too small ({dim})")
                elif dim > self.thresholds["max_embedding_dim"]:
                    issues.append(f"Document {i}: Embedding dimension too large ({dim})")
                
                # Check for NaN or infinite values
                if np.any(np.isnan(embedding)):
                    issues.append(f"Document {i}: NaN values in embedding")
                if np.any(np.isinf(embedding)):
                    issues.append(f"Document {i}: Infinite values in embedding")
                
                # Check value ranges
                max_val = np.max(np.abs(embedding))
                if max_val > self.thresholds["max_embedding_value"]:
                    warnings.append(f"Document {i}: Large embedding values (max: {max_val:.2f})")
                
                # Check embedding norm
                norm = np.linalg.norm(embedding)
                embedding_norms.append(norm)
                
                if norm < self.thresholds["min_embedding_norm"]:
                    warnings.append(f"Document {i}: Very small embedding norm ({norm:.6f})")
                
                # Check for zero embeddings
                if np.all(embedding == 0):
                    issues.append(f"Document {i}: Zero embedding vector")
                
            except Exception as e:
                issues.append(f"Document {i}: Embedding validation error - {str(e)}")
        
        # Check dimension consistency
        if embedding_dims:
            dim_counts = Counter(embedding_dims)
            if len(dim_counts) > 1:
                issues.append(f"Inconsistent embedding dimensions: {dict(dim_counts)}")
        
        result["issues"].extend(issues)
        result["warnings"].extend(warnings)
        result["validation_details"]["embeddings"] = {
            "checked_embeddings": len(embedding_dims),
            "embedding_issues": len(issues),
            "dimension_consistency": len(set(embedding_dims)) <= 1,
            "common_dimension": max(embedding_dims, default=0) if embedding_dims else 0,
            "norm_statistics": {
                "mean": np.mean(embedding_norms) if embedding_norms else 0,
                "std": np.std(embedding_norms) if embedding_norms else 0,
                "min": np.min(embedding_norms) if embedding_norms else 0,
                "max": np.max(embedding_norms) if embedding_norms else 0
            }
        }
    
    def _validate_metadata(self, documents: List[Document], result: Dict[str, Any]) -> None:
        """Validate metadata consistency and completeness."""
        issues = []
        warnings = []
        metadata_keys = set()
        source_files = set()
        
        for i, doc in enumerate(documents):
            if doc.metadata is None:
                continue
            
            try:
                # Collect metadata keys
                metadata_keys.update(doc.metadata.keys())
                
                # Check for source information
                if "source" in doc.metadata:
                    source_files.add(doc.metadata["source"])
                elif self.strict_mode:
                    warnings.append(f"Document {i}: Missing source metadata")
                
                # Check for chunk information
                if "chunk_index" in doc.metadata:
                    chunk_idx = doc.metadata["chunk_index"]
                    if not isinstance(chunk_idx, int) or chunk_idx < 0:
                        issues.append(f"Document {i}: Invalid chunk_index: {chunk_idx}")
                
                # Check for page information
                if "page" in doc.metadata:
                    page_num = doc.metadata["page"]
                    if not isinstance(page_num, (int, float)) or page_num < 0:
                        warnings.append(f"Document {i}: Invalid page number: {page_num}")
                
            except Exception as e:
                issues.append(f"Document {i}: Metadata validation error - {str(e)}")
        
        result["issues"].extend(issues)
        result["warnings"].extend(warnings)
        result["validation_details"]["metadata"] = {
            "unique_metadata_keys": list(metadata_keys),
            "unique_sources": len(source_files),
            "metadata_issues": len(issues)
        }
    
    def _validate_content(self, documents: List[Document], result: Dict[str, Any]) -> None:
        """Validate document content quality."""
        issues = []
        warnings = []
        content_lengths = []
        
        for i, doc in enumerate(documents):
            if not doc.content:
                continue
            
            try:
                content = doc.content
                content_length = len(content)
                content_lengths.append(content_length)
                
                # Check content length
                if content_length < self.thresholds["min_content_length"]:
                    warnings.append(f"Document {i}: Very short content ({content_length} chars)")
                elif content_length > self.thresholds["max_content_length"]:
                    warnings.append(f"Document {i}: Very long content ({content_length} chars)")
                
                # Check for encoding issues
                try:
                    content.encode('utf-8')
                except UnicodeEncodeError:
                    issues.append(f"Document {i}: Encoding issues detected")
                
                # Check for suspicious characters
                if '\x00' in content:
                    issues.append(f"Document {i}: Null bytes in content")
                
                # Check content quality
                if content.strip() != content:
                    warnings.append(f"Document {i}: Leading/trailing whitespace")
                
                if content.count('\n\n\n') > content_length / 100:
                    warnings.append(f"Document {i}: Excessive empty lines")
                
            except Exception as e:
                issues.append(f"Document {i}: Content validation error - {str(e)}")
        
        result["issues"].extend(issues)
        result["warnings"].extend(warnings)
        result["validation_details"]["content"] = {
            "checked_documents": len(content_lengths),
            "content_issues": len(issues),
            "length_statistics": {
                "mean": np.mean(content_lengths) if content_lengths else 0,
                "std": np.std(content_lengths) if content_lengths else 0,
                "min": np.min(content_lengths) if content_lengths else 0,
                "max": np.max(content_lengths) if content_lengths else 0
            }
        }
    
    def _perform_statistical_analysis(self, documents: List[Document], result: Dict[str, Any]) -> None:
        """Perform statistical analysis of the document collection."""
        stats = {}
        
        try:
            # Basic statistics
            stats["total_documents"] = len(documents)
            stats["documents_with_embeddings"] = sum(1 for doc in documents if doc.embedding)
            stats["documents_with_metadata"] = sum(1 for doc in documents if doc.metadata)
            
            # Content statistics
            content_lengths = [len(doc.content) for doc in documents if doc.content]
            if content_lengths:
                stats["content_length"] = {
                    "mean": np.mean(content_lengths),
                    "median": np.median(content_lengths),
                    "std": np.std(content_lengths),
                    "min": np.min(content_lengths),
                    "max": np.max(content_lengths)
                }
            
            # Embedding statistics
            embeddings = [doc.embedding for doc in documents if doc.embedding]
            if embeddings:
                embedding_matrix = np.array(embeddings)
                stats["embeddings"] = {
                    "dimension": embedding_matrix.shape[1],
                    "mean_norm": np.mean(np.linalg.norm(embedding_matrix, axis=1)),
                    "value_range": {
                        "min": np.min(embedding_matrix),
                        "max": np.max(embedding_matrix),
                        "mean": np.mean(embedding_matrix),
                        "std": np.std(embedding_matrix)
                    }
                }
            
            # Source distribution
            sources = [doc.metadata.get("source", "unknown") for doc in documents if doc.metadata]
            if sources:
                source_counts = Counter(sources)
                stats["sources"] = {
                    "unique_sources": len(source_counts),
                    "documents_per_source": dict(source_counts.most_common(10))
                }
            
        except Exception as e:
            result["warnings"].append(f"Statistical analysis failed: {str(e)}")
        
        result["statistics"] = stats
    
    def _detect_duplicates(self, documents: List[Document], result: Dict[str, Any]) -> None:
        """Detect potential duplicate documents."""
        issues = []
        warnings = []
        
        try:
            # Content-based duplicate detection
            content_hashes = {}
            embedding_similarities = []
            
            for i, doc in enumerate(documents):
                if doc.content:
                    # Simple hash-based duplicate detection
                    content_hash = hash(doc.content.strip().lower())
                    if content_hash in content_hashes:
                        warnings.append(f"Potential duplicate content: documents {content_hashes[content_hash]} and {i}")
                    else:
                        content_hashes[content_hash] = i
            
            # Embedding-based similarity (sample check for performance)
            embeddings = [(i, doc.embedding) for i, doc in enumerate(documents) if doc.embedding]
            
            if len(embeddings) > 1:
                # Sample for performance
                sample_size = min(100, len(embeddings))
                sample_indices = np.random.choice(len(embeddings), sample_size, replace=False)
                
                for i in range(len(sample_indices)):
                    for j in range(i + 1, len(sample_indices)):
                        idx1, emb1 = embeddings[sample_indices[i]]
                        idx2, emb2 = embeddings[sample_indices[j]]
                        
                        similarity = np.dot(emb1, emb2) / (np.linalg.norm(emb1) * np.linalg.norm(emb2))
                        
                        if similarity > 0.99:  # Very high similarity threshold
                            warnings.append(f"Very similar embeddings: documents {idx1} and {idx2} (similarity: {similarity:.3f})")
            
            # Check duplicate ratio
            unique_content = len(content_hashes)
            total_with_content = sum(1 for doc in documents if doc.content)
            
            if total_with_content > 0:
                duplicate_ratio = 1 - (unique_content / total_with_content)
                if duplicate_ratio > self.thresholds["max_duplicate_ratio"]:
                    issues.append(f"High duplicate ratio: {duplicate_ratio:.2%}")
        
        except Exception as e:
            warnings.append(f"Duplicate detection failed: {str(e)}")
        
        result["issues"].extend(issues)
        result["warnings"].extend(warnings)
        result["validation_details"]["duplicates"] = {
            "duplicate_issues": len([issue for issue in issues if "duplicate" in issue.lower()]),
            "similarity_warnings": len([warning for warning in warnings if "similar" in warning.lower()])
        }
    
    def validate_migration_consistency(self, 
                                     source_documents: List[Document], 
                                     target_count: int) -> Dict[str, Any]:
        """
        Validate consistency between source and target after migration.
        
        Args:
            source_documents: Original documents
            target_count: Number of documents in target system
            
        Returns:
            Dictionary with consistency validation results
        """
        result = {
            "is_consistent": True,
            "issues": [],
            "warnings": [],
            "comparison": {}
        }
        
        try:
            source_count = len(source_documents)
            
            # Count consistency
            if source_count != target_count:
                result["is_consistent"] = False
                result["issues"].append(f"Document count mismatch: source={source_count}, target={target_count}")
            
            # Additional consistency checks would go here
            # (e.g., sampling documents and comparing content)
            
            result["comparison"] = {
                "source_count": source_count,
                "target_count": target_count,
                "count_match": source_count == target_count
            }
            
        except Exception as e:
            result["is_consistent"] = False
            result["issues"].append(f"Consistency validation failed: {str(e)}")
        
        return result