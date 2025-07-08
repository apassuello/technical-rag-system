#!/usr/bin/env python3
"""
Test Suite 3: Embedding and Vector Storage Analysis

This test suite provides comprehensive forensic analysis of the embedding generation
and vector storage components of the RAG system.

Critical Focus Areas:
- Embedding generation quality and consistency
- Vector dimensionality and normalization validation
- Similarity pattern analysis
- Vector storage indexing verification
- Embedding-document alignment integrity
"""

import sys
import logging
import json
import numpy as np
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass, asdict

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from tests.diagnostic.base_diagnostic import DiagnosticTestBase, DiagnosticResult
from src.core.interfaces import Document
from src.components.embedders.sentence_transformer_embedder import SentenceTransformerEmbedder
from src.components.retrievers.unified_retriever import UnifiedRetriever

logger = logging.getLogger(__name__)


@dataclass
class EmbeddingVectorAnalysis:
    """Analysis results for embedding and vector storage pipeline."""
    total_texts_processed: int
    total_embeddings_generated: int
    embedding_generation_success_rate: float
    vector_quality_score: float
    similarity_pattern_score: float
    vector_storage_integrity: float
    embedding_generation_rate: float
    issues_found: List[str]
    recommendations: List[str]


class EmbeddingVectorForensics(DiagnosticTestBase):
    """
    Forensic analysis of embedding generation and vector storage.
    
    This class provides comprehensive testing of:
    - Embedding generation quality and consistency
    - Vector dimensionality and normalization
    - Similarity pattern analysis
    - Vector storage indexing verification
    - Embedding-document alignment integrity
    """
    
    def __init__(self):
        super().__init__()
        self.embedder = None
        self.retriever = None
        self.test_embeddings = []
        self.test_documents = []
    
    def run_all_embedding_vector_tests(self) -> EmbeddingVectorAnalysis:
        """
        Run comprehensive embedding and vector storage forensic tests.
        
        Returns:
            EmbeddingVectorAnalysis with complete results
        """
        print("=" * 80)
        print("TEST SUITE 3: EMBEDDING AND VECTOR STORAGE ANALYSIS")
        print("=" * 80)
        
        # Initialize components
        self.embedder = SentenceTransformerEmbedder()
        self.retriever = UnifiedRetriever(embedder=self.embedder)
        
        # Test 1: Embedding Generation Quality Validation
        print("\n🔢 Test 3.1: Embedding Generation Quality Validation")
        generation_results = self.safe_execute(
            self._test_embedding_generation_quality, 
            "Embedding_Generation_Quality", 
            "sentence_transformer_embedder"
        )
        
        # Test 2: Vector Dimensionality and Normalization Analysis
        print("\n📐 Test 3.2: Vector Dimensionality and Normalization Analysis")
        dimensionality_results = self.safe_execute(
            self._test_vector_dimensionality_normalization,
            "Vector_Dimensionality_Normalization",
            "sentence_transformer_embedder"
        )
        
        # Test 3: Similarity Pattern Analysis
        print("\n🔍 Test 3.3: Similarity Pattern Analysis")
        similarity_results = self.safe_execute(
            self._test_similarity_pattern_analysis,
            "Similarity_Pattern_Analysis",
            "sentence_transformer_embedder"
        )
        
        # Test 4: Vector Storage Indexing Verification
        print("\n🗂️ Test 3.4: Vector Storage Indexing Verification")
        storage_results = self.safe_execute(
            self._test_vector_storage_indexing,
            "Vector_Storage_Indexing",
            "unified_retriever"
        )
        
        # Test 5: Embedding-Document Alignment Integrity
        print("\n🔗 Test 3.5: Embedding-Document Alignment Integrity")
        alignment_results = self.safe_execute(
            self._test_embedding_document_alignment,
            "Embedding_Document_Alignment",
            "unified_retriever"
        )
        
        # Test 6: Embedding Performance Analysis
        print("\n⚡ Test 3.6: Embedding Performance Analysis")
        performance_results = self.safe_execute(
            self._test_embedding_performance,
            "Embedding_Performance",
            "sentence_transformer_embedder"
        )
        
        # Aggregate results
        analysis = self._aggregate_embedding_analysis([
            generation_results, dimensionality_results, similarity_results,
            storage_results, alignment_results, performance_results
        ])
        
        print(f"\n📊 EMBEDDING AND VECTOR STORAGE ANALYSIS COMPLETE")
        print(f"Total Texts Processed: {analysis.total_texts_processed}")
        print(f"Total Embeddings Generated: {analysis.total_embeddings_generated}")
        print(f"Embedding Generation Success Rate: {analysis.embedding_generation_success_rate:.1%}")
        print(f"Vector Quality Score: {analysis.vector_quality_score:.3f}")
        print(f"Similarity Pattern Score: {analysis.similarity_pattern_score:.3f}")
        print(f"Vector Storage Integrity: {analysis.vector_storage_integrity:.1%}")
        
        if analysis.issues_found:
            print(f"\n🚨 Issues Found ({len(analysis.issues_found)}):")
            for issue in analysis.issues_found:
                print(f"  - {issue}")
        
        if analysis.recommendations:
            print(f"\n💡 Recommendations ({len(analysis.recommendations)}):")
            for rec in analysis.recommendations:
                print(f"  - {rec}")
        
        return analysis
    
    def _test_embedding_generation_quality(self) -> tuple:
        """Test embedding generation quality and consistency."""
        print("  Testing embedding generation quality...")
        
        # Test with known text samples
        test_texts = [
            "RISC-V is an open-source instruction set architecture based on RISC principles.",
            "The RISC-V vector extension provides scalable vector processing capabilities.",
            "ARM processors are widely used in mobile and embedded systems.",
            "x86 architecture has been dominant in personal computers and servers.",
            "Machine learning requires large amounts of training data and computational resources.",
            "Natural language processing involves understanding and generating human language.",
            "This is a simple sentence about weather and temperature.",
            "The quick brown fox jumps over the lazy dog multiple times."
        ]
        
        generation_results = []
        
        for text in test_texts:
            try:
                # Generate embedding
                embedding = self.embedder.embed([text])[0]
                
                # Analyze embedding quality
                quality_analysis = self._analyze_embedding_quality(text, embedding)
                generation_results.append(quality_analysis)
                
                print(f"    Generated embedding for: {text[:50]}...")
                
            except Exception as e:
                print(f"    Error generating embedding for text: {e}")
                generation_results.append({
                    'text': text,
                    'success': False,
                    'issues': [f"Generation failed: {str(e)}"]
                })
        
        # Calculate success rate
        total_texts = len(generation_results)
        successful_generations = sum(1 for result in generation_results if result['success'])
        success_rate = successful_generations / total_texts if total_texts > 0 else 0
        
        issues_found = []
        for result in generation_results:
            if not result['success']:
                issues_found.extend(result['issues'])
        
        data_captured = {
            "test_texts": test_texts,
            "total_texts": total_texts,
            "successful_generations": successful_generations,
            "generation_results": generation_results
        }
        
        analysis_results = {
            "success_rate": success_rate,
            "generation_quality_good": success_rate > 0.95,
            "summary": f"Success rate: {success_rate:.1%}"
        }
        
        return (
            data_captured,
            analysis_results,
            list(set(issues_found)),
            self._generate_generation_recommendations(generation_results)
        )
    
    def _test_vector_dimensionality_normalization(self) -> tuple:
        """Test vector dimensionality and normalization."""
        print("  Testing vector dimensionality and normalization...")
        
        # Test with sample texts
        test_texts = [
            "RISC-V instruction set architecture",
            "Vector processing capabilities",
            "Machine learning algorithms"
        ]
        
        dimensionality_results = []
        
        for text in test_texts:
            try:
                embedding = self.embedder.embed([text])[0]
                
                # Analyze dimensionality and normalization
                dim_analysis = self._analyze_vector_properties(text, embedding)
                dimensionality_results.append(dim_analysis)
                
            except Exception as e:
                dimensionality_results.append({
                    'text': text,
                    'success': False,
                    'issues': [f"Vector analysis failed: {str(e)}"]
                })
        
        # Calculate overall quality
        total_vectors = len(dimensionality_results)
        quality_vectors = sum(1 for result in dimensionality_results if result.get('quality_passed', False))
        quality_score = quality_vectors / total_vectors if total_vectors > 0 else 0
        
        issues_found = []
        for result in dimensionality_results:
            if not result.get('quality_passed', False):
                issues_found.extend(result.get('issues', []))
        
        data_captured = {
            "test_texts": test_texts,
            "total_vectors": total_vectors,
            "quality_vectors": quality_vectors,
            "dimensionality_results": dimensionality_results
        }
        
        analysis_results = {
            "quality_score": quality_score,
            "dimensionality_quality_good": quality_score > 0.9,
            "summary": f"Quality score: {quality_score:.3f}"
        }
        
        return (
            data_captured,
            analysis_results,
            list(set(issues_found)),
            self._generate_dimensionality_recommendations(dimensionality_results)
        )
    
    def _test_similarity_pattern_analysis(self) -> tuple:
        """Test similarity pattern analysis."""
        print("  Testing similarity pattern analysis...")
        
        # Test with related and unrelated text pairs
        test_pairs = [
            {
                'text1': "RISC-V is an instruction set architecture",
                'text2': "RISC-V processors implement open-source ISA",
                'expected': 'high_similarity',
                'category': 'related_technical'
            },
            {
                'text1': "Vector processing in RISC-V",
                'text2': "ARM vector extensions",
                'expected': 'medium_similarity',
                'category': 'related_domain'
            },
            {
                'text1': "RISC-V instruction set",
                'text2': "Weather is sunny today",
                'expected': 'low_similarity',
                'category': 'unrelated'
            }
        ]
        
        similarity_results = []
        
        for pair in test_pairs:
            try:
                # Generate embeddings
                embedding1 = self.embedder.embed([pair['text1']])[0]
                embedding2 = self.embedder.embed([pair['text2']])[0]
                
                # Calculate similarity
                similarity = self._calculate_cosine_similarity(embedding1, embedding2)
                
                # Analyze similarity pattern
                pattern_analysis = self._analyze_similarity_pattern(pair, similarity)
                similarity_results.append(pattern_analysis)
                
                print(f"    Similarity: {similarity:.3f} for {pair['category']}")
                
            except Exception as e:
                similarity_results.append({
                    'pair': pair,
                    'success': False,
                    'issues': [f"Similarity analysis failed: {str(e)}"]
                })
        
        # Calculate pattern quality
        total_pairs = len(similarity_results)
        good_patterns = sum(1 for result in similarity_results if result.get('pattern_correct', False))
        pattern_score = good_patterns / total_pairs if total_pairs > 0 else 0
        
        issues_found = []
        for result in similarity_results:
            if not result.get('pattern_correct', False):
                issues_found.extend(result.get('issues', []))
        
        data_captured = {
            "test_pairs": test_pairs,
            "total_pairs": total_pairs,
            "good_patterns": good_patterns,
            "similarity_results": similarity_results
        }
        
        analysis_results = {
            "pattern_score": pattern_score,
            "similarity_patterns_good": pattern_score > 0.8,
            "summary": f"Pattern score: {pattern_score:.3f}"
        }
        
        return (
            data_captured,
            analysis_results,
            list(set(issues_found)),
            self._generate_similarity_recommendations(similarity_results)
        )
    
    def _test_vector_storage_indexing(self) -> tuple:
        """Test vector storage indexing verification."""
        print("  Testing vector storage indexing...")
        
        # Create test documents with embeddings from real PDFs
        test_documents = self._create_test_documents_with_embeddings()
        
        try:
            # Index documents
            print(f"    Indexing {len(test_documents)} documents...")
            self.retriever.index_documents(test_documents)
            
            # Verify indexing
            indexing_analysis = self._analyze_indexing_quality(test_documents)
            
            data_captured = {
                "test_documents_count": len(test_documents),
                "indexing_analysis": indexing_analysis
            }
            
            analysis_results = {
                "indexing_successful": indexing_analysis['success'],
                "storage_integrity": indexing_analysis['integrity_score'],
                "summary": f"Indexing successful: {indexing_analysis['success']}"
            }
            
            issues_found = indexing_analysis.get('issues', [])
            recommendations = self._generate_indexing_recommendations(indexing_analysis)
            
        except Exception as e:
            data_captured = {"error": str(e)}
            analysis_results = {"indexing_successful": False}
            issues_found = [f"Indexing failed: {str(e)}"]
            recommendations = ["Fix indexing errors before proceeding"]
        
        return (
            data_captured,
            analysis_results,
            issues_found,
            recommendations
        )
    
    def _test_embedding_document_alignment(self) -> tuple:
        """Test embedding-document alignment integrity."""
        print("  Testing embedding-document alignment...")
        
        # Create test documents with embeddings from real PDFs
        test_documents = self._create_test_documents_with_embeddings()
        
        alignment_results = []
        
        for doc in test_documents:
            alignment_analysis = self._analyze_embedding_document_alignment(doc)
            alignment_results.append(alignment_analysis)
        
        # Calculate alignment integrity
        total_documents = len(alignment_results)
        aligned_documents = sum(1 for result in alignment_results if result['aligned'])
        alignment_score = aligned_documents / total_documents if total_documents > 0 else 0
        
        issues_found = []
        for result in alignment_results:
            if not result['aligned']:
                issues_found.extend(result['issues'])
        
        data_captured = {
            "total_documents": total_documents,
            "aligned_documents": aligned_documents,
            "alignment_results": alignment_results
        }
        
        analysis_results = {
            "alignment_score": alignment_score,
            "alignment_integrity_good": alignment_score > 0.95,
            "summary": f"Alignment score: {alignment_score:.1%}"
        }
        
        return (
            data_captured,
            analysis_results,
            list(set(issues_found)),
            self._generate_alignment_recommendations(alignment_results)
        )
    
    def _test_embedding_performance(self) -> tuple:
        """Test embedding performance metrics."""
        print("  Testing embedding performance...")
        
        import time
        
        # Test with different text lengths
        test_texts = [
            "Short text",
            "Medium length text about RISC-V instruction set architecture and its applications",
            "Long text describing the comprehensive features of RISC-V vector extension including scalable vector processing capabilities, variable-length vectors, and data-parallel operations that enable efficient computation for machine learning workloads and scientific applications"
        ]
        
        performance_results = []
        
        for text in test_texts:
            try:
                # Measure embedding generation time
                start_time = time.time()
                embedding = self.embedder.embed([text])[0]
                generation_time = time.time() - start_time
                
                performance_analysis = {
                    'text': text,
                    'text_length': len(text),
                    'generation_time': generation_time,
                    'chars_per_second': len(text) / generation_time if generation_time > 0 else 0,
                    'embedding_length': len(embedding),
                    'success': True
                }
                
                performance_results.append(performance_analysis)
                
            except Exception as e:
                performance_results.append({
                    'text': text,
                    'success': False,
                    'issues': [f"Performance test failed: {str(e)}"]
                })
        
        # Calculate performance metrics
        successful_tests = [r for r in performance_results if r['success']]
        avg_generation_time = sum(r['generation_time'] for r in successful_tests) / len(successful_tests) if successful_tests else 0
        avg_chars_per_second = sum(r['chars_per_second'] for r in successful_tests) / len(successful_tests) if successful_tests else 0
        
        issues_found = []
        if avg_chars_per_second < 1000:
            issues_found.append(f"Embedding generation rate {avg_chars_per_second:.0f} chars/sec below target 1000 chars/sec")
        
        data_captured = {
            "test_texts": test_texts,
            "performance_results": performance_results,
            "avg_generation_time": avg_generation_time,
            "avg_chars_per_second": avg_chars_per_second
        }
        
        analysis_results = {
            "performance_target_met": avg_chars_per_second >= 1000,
            "avg_generation_time": avg_generation_time,
            "avg_chars_per_second": avg_chars_per_second,
            "summary": f"{avg_chars_per_second:.0f} chars/sec"
        }
        
        return (
            data_captured,
            analysis_results,
            issues_found,
            self._generate_performance_recommendations(performance_results)
        )
    
    def _create_test_documents_with_embeddings(self) -> List[Document]:
        """Create test documents with embeddings from real PDF processing."""
        from src.components.processors.pdf_processor import HybridPDFProcessor
        
        processor = HybridPDFProcessor()
        
        # Process real PDFs
        test_files = [
            "data/test/riscv-card.pdf",
            "data/test/unpriv-isa-asciidoc.pdf",
            "data/test/RISC-V-VectorExtension-1-1.pdf"
        ]
        
        documents = []
        for pdf_path in test_files:
            pdf_file = project_root / pdf_path
            if pdf_file.exists():
                try:
                    processed_docs = processor.process(pdf_file)
                    if processed_docs:
                        doc = processed_docs[0]  # Take first document
                        # Generate embedding for the document
                        embedding = self.embedder.embed([doc.content])[0]
                        # Create new document with embedding
                        doc_with_embedding = Document(
                            content=doc.content,
                            metadata=doc.metadata,
                            embedding=embedding
                        )
                        documents.append(doc_with_embedding)
                except Exception as e:
                    print(f"    Error processing {pdf_path} for embeddings: {e}")
                    continue
        
        return documents
    
    def _analyze_embedding_quality(self, text: str, embedding: List[float]) -> Dict[str, Any]:
        """Analyze embedding quality."""
        issues = []
        
        # Check embedding exists
        if not embedding:
            issues.append("Embedding is empty")
            return {'text': text, 'success': False, 'issues': issues}
        
        # Check dimensionality
        if len(embedding) != 384:
            issues.append(f"Embedding dimension {len(embedding)} != expected 384")
        
        # Check for NaN or infinite values
        if any(np.isnan(val) or np.isinf(val) for val in embedding):
            issues.append("Embedding contains NaN or infinite values")
        
        # Check value range
        min_val, max_val = min(embedding), max(embedding)
        if min_val < -1.0 or max_val > 1.0:
            issues.append(f"Embedding values outside expected range [-1, 1]: [{min_val:.3f}, {max_val:.3f}]")
        
        return {
            'text': text,
            'success': len(issues) == 0,
            'embedding_dimension': len(embedding),
            'embedding_norm': np.linalg.norm(embedding),
            'min_value': min_val,
            'max_value': max_val,
            'issues': issues
        }
    
    def _analyze_vector_properties(self, text: str, embedding: List[float]) -> Dict[str, Any]:
        """Analyze vector properties."""
        issues = []
        
        # Convert to numpy array for analysis
        vec = np.array(embedding)
        
        # Check dimensionality
        if len(vec) != 384:
            issues.append(f"Vector dimension {len(vec)} != expected 384")
        
        # Check normalization
        norm = np.linalg.norm(vec)
        if abs(norm - 1.0) > 0.1:
            issues.append(f"Vector not normalized, norm: {norm:.3f}")
        
        # Check for zeros
        zero_count = np.sum(vec == 0)
        if zero_count > len(vec) * 0.1:
            issues.append(f"Too many zero values: {zero_count}/{len(vec)}")
        
        return {
            'text': text,
            'quality_passed': len(issues) == 0,
            'dimension': len(vec),
            'norm': norm,
            'zero_count': zero_count,
            'mean_value': np.mean(vec),
            'std_value': np.std(vec),
            'issues': issues
        }
    
    def _calculate_cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        v1 = np.array(vec1)
        v2 = np.array(vec2)
        
        dot_product = np.dot(v1, v2)
        norm_v1 = np.linalg.norm(v1)
        norm_v2 = np.linalg.norm(v2)
        
        if norm_v1 == 0 or norm_v2 == 0:
            return 0.0
        
        return dot_product / (norm_v1 * norm_v2)
    
    def _analyze_similarity_pattern(self, pair: Dict, similarity: float) -> Dict[str, Any]:
        """Analyze similarity pattern correctness."""
        expected = pair['expected']
        issues = []
        
        # Define expected similarity ranges
        if expected == 'high_similarity':
            pattern_correct = similarity > 0.7
            if not pattern_correct:
                issues.append(f"Expected high similarity (>0.7), got {similarity:.3f}")
        elif expected == 'medium_similarity':
            pattern_correct = 0.3 < similarity < 0.7
            if not pattern_correct:
                issues.append(f"Expected medium similarity (0.3-0.7), got {similarity:.3f}")
        elif expected == 'low_similarity':
            pattern_correct = similarity < 0.3
            if not pattern_correct:
                issues.append(f"Expected low similarity (<0.3), got {similarity:.3f}")
        else:
            pattern_correct = False
            issues.append(f"Unknown expected similarity pattern: {expected}")
        
        return {
            'pair': pair,
            'similarity': similarity,
            'pattern_correct': pattern_correct,
            'issues': issues
        }
    
    def _analyze_indexing_quality(self, documents: List[Document]) -> Dict[str, Any]:
        """Analyze indexing quality."""
        issues = []
        
        # Check retriever state
        indexed_count = self.retriever.get_document_count()
        expected_count = len(documents)
        
        if indexed_count != expected_count:
            issues.append(f"Document count mismatch: indexed {indexed_count}, expected {expected_count}")
        
        # Check FAISS index
        faiss_info = self.retriever.get_faiss_info()
        if faiss_info['total_vectors'] != expected_count:
            issues.append(f"FAISS vector count mismatch: {faiss_info['total_vectors']}, expected {expected_count}")
        
        integrity_score = 1.0 - (len(issues) / max(1, expected_count))
        
        return {
            'success': len(issues) == 0,
            'indexed_count': indexed_count,
            'expected_count': expected_count,
            'faiss_info': faiss_info,
            'integrity_score': integrity_score,
            'issues': issues
        }
    
    def _analyze_embedding_document_alignment(self, document: Document) -> Dict[str, Any]:
        """Analyze embedding-document alignment."""
        issues = []
        
        # Check if document has embedding
        if document.embedding is None:
            issues.append("Document missing embedding")
            return {'aligned': False, 'issues': issues}
        
        # Check embedding-content alignment
        embedding_dim = len(document.embedding)
        if embedding_dim != 384:
            issues.append(f"Embedding dimension {embedding_dim} != expected 384")
        
        # Check if embedding represents the content
        content_length = len(document.content)
        if content_length == 0:
            issues.append("Document has empty content")
        
        # Check metadata consistency
        if 'source' not in document.metadata:
            issues.append("Document missing source metadata")
        
        return {
            'aligned': len(issues) == 0,
            'embedding_dimension': embedding_dim,
            'content_length': content_length,
            'metadata_fields': list(document.metadata.keys()),
            'issues': issues
        }
    
    def _generate_generation_recommendations(self, results: List[Dict]) -> List[str]:
        """Generate recommendations for embedding generation."""
        recommendations = []
        
        if any(not result['success'] for result in results):
            recommendations.append("Fix embedding generation failures")
        
        return recommendations
    
    def _generate_dimensionality_recommendations(self, results: List[Dict]) -> List[str]:
        """Generate recommendations for dimensionality."""
        recommendations = []
        
        if any(not result.get('quality_passed', False) for result in results):
            recommendations.append("Ensure consistent vector dimensionality and normalization")
        
        return recommendations
    
    def _generate_similarity_recommendations(self, results: List[Dict]) -> List[str]:
        """Generate recommendations for similarity patterns."""
        recommendations = []
        
        if any(not result.get('pattern_correct', False) for result in results):
            recommendations.append("Investigate similarity pattern discrepancies")
        
        return recommendations
    
    def _generate_indexing_recommendations(self, analysis: Dict) -> List[str]:
        """Generate recommendations for indexing."""
        recommendations = []
        
        if not analysis['success']:
            recommendations.append("Fix vector storage indexing issues")
        
        return recommendations
    
    def _generate_alignment_recommendations(self, results: List[Dict]) -> List[str]:
        """Generate recommendations for alignment."""
        recommendations = []
        
        if any(not result['aligned'] for result in results):
            recommendations.append("Ensure embedding-document alignment integrity")
        
        return recommendations
    
    def _generate_performance_recommendations(self, results: List[Dict]) -> List[str]:
        """Generate recommendations for performance."""
        recommendations = []
        
        successful_results = [r for r in results if r['success']]
        if successful_results:
            avg_rate = sum(r['chars_per_second'] for r in successful_results) / len(successful_results)
            if avg_rate < 1000:
                recommendations.append("Optimize embedding generation for better performance")
        
        return recommendations
    
    def _aggregate_embedding_analysis(self, results: List[DiagnosticResult]) -> EmbeddingVectorAnalysis:
        """Aggregate all embedding test results."""
        total_texts = 0
        total_embeddings = 0
        generation_success_rate = 0
        vector_quality_score = 0
        similarity_pattern_score = 0
        storage_integrity = 0
        embedding_rate = 0
        
        all_issues = []
        all_recommendations = []
        
        for result in results:
            all_issues.extend(result.issues_found)
            all_recommendations.extend(result.recommendations)
            
            # Extract specific metrics
            if result.test_name == "Embedding_Generation_Quality":
                total_texts = result.data_captured.get('total_texts', 0)
                total_embeddings = result.data_captured.get('successful_generations', 0)
                generation_success_rate = result.analysis_results.get('success_rate', 0)
            
            elif result.test_name == "Vector_Dimensionality_Normalization":
                vector_quality_score = result.analysis_results.get('quality_score', 0)
            
            elif result.test_name == "Similarity_Pattern_Analysis":
                similarity_pattern_score = result.analysis_results.get('pattern_score', 0)
            
            elif result.test_name == "Vector_Storage_Indexing":
                storage_integrity = result.analysis_results.get('storage_integrity', 0)
            
            elif result.test_name == "Embedding_Performance":
                embedding_rate = result.analysis_results.get('avg_chars_per_second', 0)
        
        return EmbeddingVectorAnalysis(
            total_texts_processed=total_texts,
            total_embeddings_generated=total_embeddings,
            embedding_generation_success_rate=generation_success_rate,
            vector_quality_score=vector_quality_score,
            similarity_pattern_score=similarity_pattern_score,
            vector_storage_integrity=storage_integrity,
            embedding_generation_rate=embedding_rate,
            issues_found=list(set(all_issues)),
            recommendations=list(set(all_recommendations))
        )


def main():
    """Run embedding and vector storage forensic tests."""
    forensics = EmbeddingVectorForensics()
    analysis = forensics.run_all_embedding_vector_tests()
    
    # Save results
    results_file = project_root / f"embedding_vector_forensics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(results_file, 'w') as f:
        json.dump(asdict(analysis), f, indent=2)
    
    print(f"\n💾 Results saved to: {results_file}")
    return analysis


if __name__ == "__main__":
    main()