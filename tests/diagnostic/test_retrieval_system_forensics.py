#!/usr/bin/env python3
"""
Test Suite 4: Retrieval System Forensics

This test suite provides comprehensive forensic analysis of the retrieval system
including dense retrieval, sparse retrieval, and hybrid fusion components.

Critical Focus Areas:
- Dense semantic retrieval quality and accuracy
- Sparse BM25 keyword retrieval effectiveness
- Hybrid fusion (RRF) implementation verification
- Score distribution and ranking analysis
- Retrieval performance and latency analysis
"""

import sys
import logging
import json
import time
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass, asdict

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from tests.diagnostic.base_diagnostic import DiagnosticTestBase, DiagnosticResult
from src.core.interfaces import Document, RetrievalResult
from src.components.embedders.sentence_transformer_embedder import SentenceTransformerEmbedder
from src.components.retrievers.unified_retriever import UnifiedRetriever

logger = logging.getLogger(__name__)


@dataclass
class RetrievalSystemAnalysis:
    """Analysis results for retrieval system forensics."""
    total_queries_tested: int
    total_results_retrieved: int
    dense_retrieval_accuracy: float
    sparse_retrieval_effectiveness: float
    hybrid_fusion_quality: float
    average_retrieval_latency: float
    score_distribution_quality: float
    ranking_accuracy: float
    issues_found: List[str]
    recommendations: List[str]


class RetrievalSystemForensics(DiagnosticTestBase):
    """
    Forensic analysis of retrieval system components.
    
    This class provides comprehensive testing of:
    - Dense semantic retrieval quality
    - Sparse BM25 keyword retrieval
    - Hybrid fusion (RRF) implementation
    - Score distribution analysis
    - Retrieval performance metrics
    """
    
    def __init__(self):
        super().__init__()
        self.embedder = None
        self.retriever = None
        self.test_documents = []
        self.test_corpus_indexed = False
    
    def run_all_retrieval_system_tests(self) -> RetrievalSystemAnalysis:
        """
        Run comprehensive retrieval system forensic tests.
        
        Returns:
            RetrievalSystemAnalysis with complete results
        """
        print("=" * 80)
        print("TEST SUITE 4: RETRIEVAL SYSTEM FORENSICS")
        print("=" * 80)
        
        # Initialize components and test corpus
        self._initialize_retrieval_components()
        
        # Test 1: Dense Semantic Retrieval Quality
        print("\n🔍 Test 4.1: Dense Semantic Retrieval Quality")
        dense_results = self.safe_execute(
            self._test_dense_retrieval_quality, 
            "Dense_Retrieval_Quality", 
            "unified_retriever"
        )
        
        # Test 2: Sparse BM25 Retrieval Effectiveness
        print("\n🔤 Test 4.2: Sparse BM25 Retrieval Effectiveness")
        sparse_results = self.safe_execute(
            self._test_sparse_retrieval_effectiveness,
            "Sparse_Retrieval_Effectiveness",
            "unified_retriever"
        )
        
        # Test 3: Hybrid Fusion (RRF) Implementation
        print("\n🔀 Test 4.3: Hybrid Fusion (RRF) Implementation")
        hybrid_results = self.safe_execute(
            self._test_hybrid_fusion_implementation,
            "Hybrid_Fusion_Implementation",
            "unified_retriever"
        )
        
        # Test 4: Score Distribution Analysis
        print("\n📊 Test 4.4: Score Distribution Analysis")
        score_results = self.safe_execute(
            self._test_score_distribution_analysis,
            "Score_Distribution_Analysis",
            "unified_retriever"
        )
        
        # Test 5: Ranking Accuracy Validation
        print("\n🎯 Test 4.5: Ranking Accuracy Validation")
        ranking_results = self.safe_execute(
            self._test_ranking_accuracy_validation,
            "Ranking_Accuracy_Validation",
            "unified_retriever"
        )
        
        # Test 6: Retrieval Performance Analysis
        print("\n⚡ Test 4.6: Retrieval Performance Analysis")
        performance_results = self.safe_execute(
            self._test_retrieval_performance_analysis,
            "Retrieval_Performance_Analysis",
            "unified_retriever"
        )
        
        # Aggregate results
        analysis = self._aggregate_retrieval_analysis([
            dense_results, sparse_results, hybrid_results,
            score_results, ranking_results, performance_results
        ])
        
        print(f"\n📊 RETRIEVAL SYSTEM ANALYSIS COMPLETE")
        print(f"Total Queries Tested: {analysis.total_queries_tested}")
        print(f"Total Results Retrieved: {analysis.total_results_retrieved}")
        print(f"Dense Retrieval Accuracy: {analysis.dense_retrieval_accuracy:.1%}")
        print(f"Sparse Retrieval Effectiveness: {analysis.sparse_retrieval_effectiveness:.1%}")
        print(f"Hybrid Fusion Quality: {analysis.hybrid_fusion_quality:.1%}")
        print(f"Average Retrieval Latency: {analysis.average_retrieval_latency:.3f}s")
        print(f"Ranking Accuracy: {analysis.ranking_accuracy:.1%}")
        
        if analysis.issues_found:
            print(f"\n🚨 Issues Found ({len(analysis.issues_found)}):")
            for issue in analysis.issues_found:
                print(f"  - {issue}")
        
        if analysis.recommendations:
            print(f"\n💡 Recommendations ({len(analysis.recommendations)}):")
            for rec in analysis.recommendations:
                print(f"  - {rec}")
        
        return analysis
    
    def _initialize_retrieval_components(self):
        """Initialize retrieval components with test corpus."""
        print("  Initializing retrieval components...")
        
        # Initialize embedder and retriever
        self.embedder = SentenceTransformerEmbedder()
        self.retriever = UnifiedRetriever(embedder=self.embedder)
        
        # Create comprehensive test corpus
        self.test_documents = self._create_test_corpus()
        
        # Index documents if not already done
        if not self.test_corpus_indexed:
            print(f"  Indexing {len(self.test_documents)} test documents...")
            self.retriever.index_documents(self.test_documents)
            self.test_corpus_indexed = True
            print("  ✅ Test corpus indexed successfully")
    
    def _create_test_corpus(self) -> List[Document]:
        """Create a comprehensive test corpus from real PDF processing."""
        from src.core.component_factory import ComponentFactory
        
        processor = ComponentFactory.create_processor("hybrid_pdf")
        
        # Process real PDFs to create test corpus
        test_files = [
            "data/test/riscv-card.pdf",
            "data/test/unpriv-isa-asciidoc.pdf", 
            "data/test/RISC-V-VectorExtension-1-1.pdf",
            "data/test/riscv-privileged.pdf",
            "data/test/riscv-base-instructions.pdf"
        ]
        
        documents = []
        for pdf_path in test_files:
            pdf_file = project_root / pdf_path
            if pdf_file.exists():
                try:
                    processed_docs = processor.process(pdf_file)
                    if processed_docs:
                        # Take first few documents from each PDF for corpus
                        for doc in processed_docs[:2]:  # Take first 2 documents per PDF
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
                    print(f"    Error processing {pdf_path} for corpus: {e}")
                    continue
        
        return documents
    
    def _test_dense_retrieval_quality(self) -> tuple:
        """Test dense semantic retrieval quality."""
        print("  Testing dense semantic retrieval quality...")
        
        # Define test queries with expected relevant documents
        test_queries = [
            {
                'query': 'What is RISC-V architecture?',
                'query_type': 'definition',
                'expected_topics': ['RISC-V', 'ISA', 'instruction set', 'architecture'],
                'expected_sources': ['riscv-intro.pdf'],
                'difficulty': 'easy'
            },
            {
                'query': 'vector processing capabilities',
                'query_type': 'technical_detail',
                'expected_topics': ['vector', 'extension', 'scalable', 'parallel'],
                'expected_sources': ['vector-spec.pdf'],
                'difficulty': 'medium'
            },
            {
                'query': 'machine learning computational requirements',
                'query_type': 'specific_feature',
                'expected_topics': ['machine learning', 'computational resources', 'training data'],
                'expected_sources': ['ml-handbook.pdf'],
                'difficulty': 'medium'
            },
            {
                'query': 'database ACID properties',
                'query_type': 'technical_concept',
                'expected_topics': ['database', 'ACID', 'integrity'],
                'expected_sources': ['database-book.pdf'],
                'difficulty': 'hard'
            }
        ]
        
        dense_results = []
        
        for query_data in test_queries:
            try:
                # Retrieve results
                results = self.retriever.retrieve(query_data['query'], k=5)
                
                # Analyze retrieval quality
                quality_analysis = self._analyze_retrieval_quality(query_data, results, 'dense')
                dense_results.append(quality_analysis)
                
                print(f"    Query: '{query_data['query'][:30]}...' - Relevance: {quality_analysis['relevance_score']:.2f}")
                
            except Exception as e:
                print(f"    Error retrieving for query '{query_data['query']}': {e}")
                dense_results.append({
                    'query': query_data['query'],
                    'success': False,
                    'issues': [f"Retrieval failed: {str(e)}"]
                })
        
        # Calculate overall dense retrieval accuracy
        successful_queries = [r for r in dense_results if r.get('success', False)]
        accuracy = sum(r['relevance_score'] for r in successful_queries) / len(successful_queries) if successful_queries else 0
        
        issues_found = []
        for result in dense_results:
            if not result.get('success', False) or result.get('relevance_score', 0) < 0.7:
                issues_found.extend(result.get('issues', []))
        
        data_captured = {
            "test_queries": test_queries,
            "total_queries": len(test_queries),
            "successful_queries": len(successful_queries),
            "dense_results": dense_results
        }
        
        analysis_results = {
            "accuracy": accuracy,
            "dense_retrieval_good": accuracy > 0.7,
            "summary": f"Dense retrieval accuracy: {accuracy:.1%}"
        }
        
        return (
            data_captured,
            analysis_results,
            list(set(issues_found)),
            self._generate_dense_recommendations(dense_results)
        )
    
    def _test_sparse_retrieval_effectiveness(self) -> tuple:
        """Test sparse BM25 retrieval effectiveness."""
        print("  Testing sparse BM25 retrieval effectiveness...")
        
        # Define keyword-focused queries
        keyword_queries = [
            {
                'query': 'RISC-V instruction set architecture',
                'keywords': ['RISC-V', 'instruction', 'set', 'architecture'],
                'expected_source': 'riscv-intro.pdf'
            },
            {
                'query': 'vector extension scalable',
                'keywords': ['vector', 'extension', 'scalable'],
                'expected_source': 'vector-spec.pdf'
            },
            {
                'query': 'ARM processors mobile embedded',
                'keywords': ['ARM', 'processors', 'mobile', 'embedded'],
                'expected_source': 'arm-reference.pdf'
            },
            {
                'query': 'database ACID properties',
                'keywords': ['database', 'ACID', 'properties'],
                'expected_source': 'database-book.pdf'
            }
        ]
        
        sparse_results = []
        
        for query_data in keyword_queries:
            try:
                # Retrieve results
                results = self.retriever.retrieve(query_data['query'], k=5)
                
                # Analyze keyword matching effectiveness
                effectiveness_analysis = self._analyze_keyword_effectiveness(query_data, results)
                sparse_results.append(effectiveness_analysis)
                
                print(f"    Keywords: {query_data['keywords']} - Effectiveness: {effectiveness_analysis['effectiveness_score']:.2f}")
                
            except Exception as e:
                sparse_results.append({
                    'query': query_data['query'],
                    'success': False,
                    'issues': [f"Keyword retrieval failed: {str(e)}"]
                })
        
        # Calculate overall sparse retrieval effectiveness
        successful_queries = [r for r in sparse_results if r.get('success', False)]
        effectiveness = sum(r['effectiveness_score'] for r in successful_queries) / len(successful_queries) if successful_queries else 0
        
        issues_found = []
        for result in sparse_results:
            if not result.get('success', False) or result.get('effectiveness_score', 0) < 0.6:
                issues_found.extend(result.get('issues', []))
        
        data_captured = {
            "keyword_queries": keyword_queries,
            "total_queries": len(keyword_queries),
            "successful_queries": len(successful_queries),
            "sparse_results": sparse_results
        }
        
        analysis_results = {
            "effectiveness": effectiveness,
            "sparse_retrieval_good": effectiveness > 0.6,
            "summary": f"Sparse retrieval effectiveness: {effectiveness:.1%}"
        }
        
        return (
            data_captured,
            analysis_results,
            list(set(issues_found)),
            self._generate_sparse_recommendations(sparse_results)
        )
    
    def _test_hybrid_fusion_implementation(self) -> tuple:
        """Test hybrid fusion (RRF) implementation."""
        print("  Testing hybrid fusion (RRF) implementation...")
        
        # Test queries that should benefit from hybrid approach
        hybrid_queries = [
            {
                'query': 'RISC-V vector processing',
                'benefits_from': 'both',  # Should benefit from both dense and sparse
                'expected_improvement': 'high'
            },
            {
                'query': 'machine learning algorithms computational',
                'benefits_from': 'dense',  # Should benefit more from semantic similarity
                'expected_improvement': 'medium'
            },
            {
                'query': 'x86 architecture compatibility',
                'benefits_from': 'sparse',  # Should benefit more from keyword matching
                'expected_improvement': 'medium'
            }
        ]
        
        hybrid_results = []
        
        for query_data in hybrid_queries:
            try:
                # Get hybrid results
                hybrid_results_data = self.retriever.retrieve(query_data['query'], k=5)
                
                # Analyze hybrid fusion quality
                fusion_analysis = self._analyze_hybrid_fusion_quality(query_data, hybrid_results_data)
                hybrid_results.append(fusion_analysis)
                
                print(f"    Query: '{query_data['query'][:30]}...' - Fusion Quality: {fusion_analysis['fusion_quality']:.2f}")
                
            except Exception as e:
                hybrid_results.append({
                    'query': query_data['query'],
                    'success': False,
                    'issues': [f"Hybrid fusion failed: {str(e)}"]
                })
        
        # Calculate overall hybrid fusion quality
        successful_queries = [r for r in hybrid_results if r.get('success', False)]
        fusion_quality = sum(r['fusion_quality'] for r in successful_queries) / len(successful_queries) if successful_queries else 0
        
        issues_found = []
        for result in hybrid_results:
            if not result.get('success', False) or result.get('fusion_quality', 0) < 0.7:
                issues_found.extend(result.get('issues', []))
        
        data_captured = {
            "hybrid_queries": hybrid_queries,
            "total_queries": len(hybrid_queries),
            "successful_queries": len(successful_queries),
            "hybrid_results": hybrid_results
        }
        
        analysis_results = {
            "fusion_quality": fusion_quality,
            "hybrid_fusion_good": fusion_quality > 0.7,
            "summary": f"Hybrid fusion quality: {fusion_quality:.1%}"
        }
        
        return (
            data_captured,
            analysis_results,
            list(set(issues_found)),
            self._generate_hybrid_recommendations(hybrid_results)
        )
    
    def _test_score_distribution_analysis(self) -> tuple:
        """Test score distribution analysis."""
        print("  Testing score distribution analysis...")
        
        # Test with queries that should show good score distribution
        test_queries = [
            "RISC-V instruction set",
            "vector processing capabilities",
            "machine learning algorithms"
        ]
        
        distribution_results = []
        
        for query in test_queries:
            try:
                # Get results with scores
                results = self.retriever.retrieve(query, k=5)
                
                # Analyze score distribution
                distribution_analysis = self._analyze_score_distribution(query, results)
                distribution_results.append(distribution_analysis)
                
                print(f"    Query: '{query}' - Distribution Quality: {distribution_analysis['distribution_quality']:.2f}")
                
            except Exception as e:
                distribution_results.append({
                    'query': query,
                    'success': False,
                    'issues': [f"Score distribution analysis failed: {str(e)}"]
                })
        
        # Calculate overall distribution quality
        successful_queries = [r for r in distribution_results if r.get('success', False)]
        distribution_quality = sum(r['distribution_quality'] for r in successful_queries) / len(successful_queries) if successful_queries else 0
        
        issues_found = []
        for result in distribution_results:
            if not result.get('success', False) or result.get('distribution_quality', 0) < 0.7:
                issues_found.extend(result.get('issues', []))
        
        data_captured = {
            "test_queries": test_queries,
            "total_queries": len(test_queries),
            "successful_queries": len(successful_queries),
            "distribution_results": distribution_results
        }
        
        analysis_results = {
            "distribution_quality": distribution_quality,
            "score_distribution_good": distribution_quality > 0.7,
            "summary": f"Score distribution quality: {distribution_quality:.1%}"
        }
        
        return (
            data_captured,
            analysis_results,
            list(set(issues_found)),
            self._generate_distribution_recommendations(distribution_results)
        )
    
    def _test_ranking_accuracy_validation(self) -> tuple:
        """Test ranking accuracy validation."""
        print("  Testing ranking accuracy validation...")
        
        # Test with queries where we know the expected ranking
        ranking_queries = [
            {
                'query': 'RISC-V open source architecture',
                'expected_top_source': 'riscv-intro.pdf',
                'expected_ranking_quality': 'high'
            },
            {
                'query': 'database ACID properties data integrity',
                'expected_top_source': 'database-book.pdf',
                'expected_ranking_quality': 'high'
            }
        ]
        
        ranking_results = []
        
        for query_data in ranking_queries:
            try:
                # Get ranked results
                results = self.retriever.retrieve(query_data['query'], k=5)
                
                # Analyze ranking accuracy
                ranking_analysis = self._analyze_ranking_accuracy(query_data, results)
                ranking_results.append(ranking_analysis)
                
                print(f"    Query: '{query_data['query'][:30]}...' - Ranking Accuracy: {ranking_analysis['ranking_accuracy']:.2f}")
                
            except Exception as e:
                ranking_results.append({
                    'query': query_data['query'],
                    'success': False,
                    'issues': [f"Ranking analysis failed: {str(e)}"]
                })
        
        # Calculate overall ranking accuracy
        successful_queries = [r for r in ranking_results if r.get('success', False)]
        ranking_accuracy = sum(r['ranking_accuracy'] for r in successful_queries) / len(successful_queries) if successful_queries else 0
        
        issues_found = []
        for result in ranking_results:
            if not result.get('success', False) or result.get('ranking_accuracy', 0) < 0.7:
                issues_found.extend(result.get('issues', []))
        
        data_captured = {
            "ranking_queries": ranking_queries,
            "total_queries": len(ranking_queries),
            "successful_queries": len(successful_queries),
            "ranking_results": ranking_results
        }
        
        analysis_results = {
            "ranking_accuracy": ranking_accuracy,
            "ranking_accuracy_good": ranking_accuracy > 0.7,
            "summary": f"Ranking accuracy: {ranking_accuracy:.1%}"
        }
        
        return (
            data_captured,
            analysis_results,
            list(set(issues_found)),
            self._generate_ranking_recommendations(ranking_results)
        )
    
    def _test_retrieval_performance_analysis(self) -> tuple:
        """Test retrieval performance analysis."""
        print("  Testing retrieval performance analysis...")
        
        # Test with different query types and complexities
        performance_queries = [
            "RISC-V",  # Simple query
            "vector processing capabilities",  # Medium query
            "machine learning algorithms computational resources training data"  # Complex query
        ]
        
        performance_results = []
        
        for query in performance_queries:
            try:
                # Measure retrieval time
                start_time = time.time()
                results = self.retriever.retrieve(query, k=10)
                retrieval_time = time.time() - start_time
                
                # Analyze performance
                performance_analysis = {
                    'query': query,
                    'query_length': len(query),
                    'retrieval_time': retrieval_time,
                    'results_count': len(results),
                    'avg_time_per_result': retrieval_time / len(results) if results else 0,
                    'performance_target_met': retrieval_time < 0.1,  # 100ms target
                    'success': True
                }
                
                performance_results.append(performance_analysis)
                
                print(f"    Query: '{query[:30]}...' - Time: {retrieval_time:.3f}s")
                
            except Exception as e:
                performance_results.append({
                    'query': query,
                    'success': False,
                    'issues': [f"Performance test failed: {str(e)}"]
                })
        
        # Calculate performance metrics
        successful_queries = [r for r in performance_results if r['success']]
        avg_retrieval_time = sum(r['retrieval_time'] for r in successful_queries) / len(successful_queries) if successful_queries else 0
        
        issues_found = []
        for result in performance_results:
            if not result['success'] or result.get('retrieval_time', 0) > 0.1:
                if not result['success']:
                    issues_found.extend(result.get('issues', []))
                else:
                    issues_found.append(f"Query '{result['query'][:30]}...' took {result['retrieval_time']:.3f}s (>0.1s target)")
        
        data_captured = {
            "performance_queries": performance_queries,
            "total_queries": len(performance_queries),
            "successful_queries": len(successful_queries),
            "performance_results": performance_results,
            "avg_retrieval_time": avg_retrieval_time
        }
        
        analysis_results = {
            "avg_retrieval_time": avg_retrieval_time,
            "performance_target_met": avg_retrieval_time < 0.1,
            "summary": f"Average retrieval time: {avg_retrieval_time:.3f}s"
        }
        
        return (
            data_captured,
            analysis_results,
            list(set(issues_found)),
            self._generate_performance_recommendations(performance_results)
        )
    
    def _analyze_retrieval_quality(self, query_data: Dict, results: List[RetrievalResult], retrieval_type: str) -> Dict[str, Any]:
        """Analyze retrieval quality for a query."""
        if not results:
            return {
                'query': query_data['query'],
                'success': False,
                'relevance_score': 0,
                'issues': ['No results returned']
            }
        
        # Check if expected topics are covered
        expected_topics = query_data.get('expected_topics', [])
        found_topics = []
        
        for result in results:
            result_topics = result.document.metadata.get('topics', [])
            for topic in expected_topics:
                if any(topic.lower() in str(rt).lower() for rt in result_topics):
                    found_topics.append(topic)
        
        topic_coverage = len(set(found_topics)) / len(expected_topics) if expected_topics else 0
        
        # Check if expected sources are present
        expected_sources = query_data.get('expected_sources', [])
        found_sources = []
        
        for result in results:
            source = result.document.metadata.get('source', '')
            if any(exp_src in source for exp_src in expected_sources):
                found_sources.append(source)
        
        source_coverage = len(set(found_sources)) / len(expected_sources) if expected_sources else 0
        
        # Calculate relevance score
        relevance_score = (topic_coverage + source_coverage) / 2
        
        issues = []
        if relevance_score < 0.7:
            issues.append(f"Low relevance score: {relevance_score:.2f}")
        if topic_coverage < 0.5:
            issues.append(f"Poor topic coverage: {topic_coverage:.2f}")
        if source_coverage < 0.5:
            issues.append(f"Poor source coverage: {source_coverage:.2f}")
        
        return {
            'query': query_data['query'],
            'success': True,
            'relevance_score': relevance_score,
            'topic_coverage': topic_coverage,
            'source_coverage': source_coverage,
            'found_topics': found_topics,
            'found_sources': found_sources,
            'issues': issues
        }
    
    def _analyze_keyword_effectiveness(self, query_data: Dict, results: List[RetrievalResult]) -> Dict[str, Any]:
        """Analyze keyword matching effectiveness."""
        if not results:
            return {
                'query': query_data['query'],
                'success': False,
                'effectiveness_score': 0,
                'issues': ['No results returned']
            }
        
        keywords = query_data.get('keywords', [])
        keyword_matches = []
        
        for result in results:
            content = result.document.content.lower()
            matches = sum(1 for keyword in keywords if keyword.lower() in content)
            keyword_matches.append(matches)
        
        # Calculate effectiveness based on keyword matches
        avg_matches = sum(keyword_matches) / len(keyword_matches) if keyword_matches else 0
        effectiveness_score = avg_matches / len(keywords) if keywords else 0
        
        issues = []
        if effectiveness_score < 0.6:
            issues.append(f"Low keyword effectiveness: {effectiveness_score:.2f}")
        
        return {
            'query': query_data['query'],
            'success': True,
            'effectiveness_score': effectiveness_score,
            'keyword_matches': keyword_matches,
            'avg_matches': avg_matches,
            'issues': issues
        }
    
    def _analyze_hybrid_fusion_quality(self, query_data: Dict, results: List[RetrievalResult]) -> Dict[str, Any]:
        """Analyze hybrid fusion quality."""
        if not results:
            return {
                'query': query_data['query'],
                'success': False,
                'fusion_quality': 0,
                'issues': ['No results returned']
            }
        
        # Check if results show proper fusion characteristics
        scores = [result.score for result in results]
        
        # Check score distribution (should be diverse from fusion)
        score_diversity = max(scores) - min(scores) if scores else 0
        
        # Check if retrieval method indicates hybrid fusion
        retrieval_methods = [result.retrieval_method for result in results]
        uses_hybrid = any('hybrid' in method for method in retrieval_methods)
        
        # Calculate fusion quality
        fusion_quality = 0.8 if uses_hybrid else 0.3
        if score_diversity > 0.1:
            fusion_quality += 0.2
        
        issues = []
        if not uses_hybrid:
            issues.append("Results don't indicate hybrid fusion")
        if score_diversity < 0.1:
            issues.append("Poor score diversity indicating limited fusion")
        
        return {
            'query': query_data['query'],
            'success': True,
            'fusion_quality': fusion_quality,
            'score_diversity': score_diversity,
            'uses_hybrid': uses_hybrid,
            'issues': issues
        }
    
    def _analyze_score_distribution(self, query: str, results: List[RetrievalResult]) -> Dict[str, Any]:
        """Analyze score distribution quality."""
        if not results:
            return {
                'query': query,
                'success': False,
                'distribution_quality': 0,
                'issues': ['No results returned']
            }
        
        scores = [result.score for result in results]
        
        # Check if scores are in descending order
        descending_order = all(scores[i] >= scores[i+1] for i in range(len(scores)-1))
        
        # Check score range
        score_range = max(scores) - min(scores) if scores else 0
        
        # Check for reasonable score values
        reasonable_scores = all(0 <= score <= 1 for score in scores)
        
        # Calculate distribution quality
        distribution_quality = 0.4 if descending_order else 0.1
        if score_range > 0.1:
            distribution_quality += 0.3
        if reasonable_scores:
            distribution_quality += 0.3
        
        issues = []
        if not descending_order:
            issues.append("Scores not in descending order")
        if score_range < 0.1:
            issues.append("Poor score range diversity")
        if not reasonable_scores:
            issues.append("Unreasonable score values")
        
        return {
            'query': query,
            'success': True,
            'distribution_quality': distribution_quality,
            'descending_order': descending_order,
            'score_range': score_range,
            'reasonable_scores': reasonable_scores,
            'scores': scores,
            'issues': issues
        }
    
    def _analyze_ranking_accuracy(self, query_data: Dict, results: List[RetrievalResult]) -> Dict[str, Any]:
        """Analyze ranking accuracy."""
        if not results:
            return {
                'query': query_data['query'],
                'success': False,
                'ranking_accuracy': 0,
                'issues': ['No results returned']
            }
        
        expected_top_source = query_data.get('expected_top_source', '')
        
        # Check if expected source is in top results
        top_result_source = results[0].document.metadata.get('source', '')
        correct_top_result = expected_top_source in top_result_source
        
        # Calculate ranking accuracy
        ranking_accuracy = 1.0 if correct_top_result else 0.5
        
        issues = []
        if not correct_top_result:
            issues.append(f"Expected '{expected_top_source}' in top result, got '{top_result_source}'")
        
        return {
            'query': query_data['query'],
            'success': True,
            'ranking_accuracy': ranking_accuracy,
            'correct_top_result': correct_top_result,
            'expected_top_source': expected_top_source,
            'actual_top_source': top_result_source,
            'issues': issues
        }
    
    def _generate_dense_recommendations(self, results: List[Dict]) -> List[str]:
        """Generate recommendations for dense retrieval."""
        recommendations = []
        
        if any(not result.get('success', False) for result in results):
            recommendations.append("Fix dense retrieval failures")
        
        low_relevance = [r for r in results if r.get('relevance_score', 0) < 0.7]
        if low_relevance:
            recommendations.append("Improve dense retrieval relevance scoring")
        
        return recommendations
    
    def _generate_sparse_recommendations(self, results: List[Dict]) -> List[str]:
        """Generate recommendations for sparse retrieval."""
        recommendations = []
        
        if any(not result.get('success', False) for result in results):
            recommendations.append("Fix sparse retrieval failures")
        
        low_effectiveness = [r for r in results if r.get('effectiveness_score', 0) < 0.6]
        if low_effectiveness:
            recommendations.append("Tune BM25 parameters for better keyword matching")
        
        return recommendations
    
    def _generate_hybrid_recommendations(self, results: List[Dict]) -> List[str]:
        """Generate recommendations for hybrid fusion."""
        recommendations = []
        
        if any(not result.get('success', False) for result in results):
            recommendations.append("Fix hybrid fusion implementation")
        
        low_fusion = [r for r in results if r.get('fusion_quality', 0) < 0.7]
        if low_fusion:
            recommendations.append("Optimize RRF parameters for better fusion")
        
        return recommendations
    
    def _generate_distribution_recommendations(self, results: List[Dict]) -> List[str]:
        """Generate recommendations for score distribution."""
        recommendations = []
        
        if any(not result.get('success', False) for result in results):
            recommendations.append("Fix score distribution calculation")
        
        poor_distribution = [r for r in results if r.get('distribution_quality', 0) < 0.7]
        if poor_distribution:
            recommendations.append("Improve score normalization and distribution")
        
        return recommendations
    
    def _generate_ranking_recommendations(self, results: List[Dict]) -> List[str]:
        """Generate recommendations for ranking accuracy."""
        recommendations = []
        
        if any(not result.get('success', False) for result in results):
            recommendations.append("Fix ranking accuracy calculation")
        
        poor_ranking = [r for r in results if r.get('ranking_accuracy', 0) < 0.7]
        if poor_ranking:
            recommendations.append("Improve ranking algorithm for better accuracy")
        
        return recommendations
    
    def _generate_performance_recommendations(self, results: List[Dict]) -> List[str]:
        """Generate recommendations for performance."""
        recommendations = []
        
        if any(not result.get('success', False) for result in results):
            recommendations.append("Fix performance measurement issues")
        
        slow_queries = [r for r in results if r.get('retrieval_time', 0) > 0.1]
        if slow_queries:
            recommendations.append("Optimize retrieval performance for <0.1s target")
        
        return recommendations
    
    def _aggregate_retrieval_analysis(self, results: List[DiagnosticResult]) -> RetrievalSystemAnalysis:
        """Aggregate all retrieval test results."""
        total_queries = 0
        total_results = 0
        dense_accuracy = 0
        sparse_effectiveness = 0
        hybrid_fusion_quality = 0
        avg_latency = 0
        score_distribution_quality = 0
        ranking_accuracy = 0
        
        all_issues = []
        all_recommendations = []
        
        for result in results:
            all_issues.extend(result.issues_found)
            all_recommendations.extend(result.recommendations)
            
            # Extract specific metrics
            if result.test_name == "Dense_Retrieval_Quality":
                total_queries += result.data_captured.get('total_queries', 0)
                dense_accuracy = result.analysis_results.get('accuracy', 0)
            
            elif result.test_name == "Sparse_Retrieval_Effectiveness":
                sparse_effectiveness = result.analysis_results.get('effectiveness', 0)
            
            elif result.test_name == "Hybrid_Fusion_Implementation":
                hybrid_fusion_quality = result.analysis_results.get('fusion_quality', 0)
            
            elif result.test_name == "Score_Distribution_Analysis":
                score_distribution_quality = result.analysis_results.get('distribution_quality', 0)
            
            elif result.test_name == "Ranking_Accuracy_Validation":
                ranking_accuracy = result.analysis_results.get('ranking_accuracy', 0)
            
            elif result.test_name == "Retrieval_Performance_Analysis":
                avg_latency = result.analysis_results.get('avg_retrieval_time', 0)
                total_results += sum(len(r.get('results', [])) for r in result.data_captured.get('performance_results', []) if r.get('success', False))
        
        return RetrievalSystemAnalysis(
            total_queries_tested=total_queries,
            total_results_retrieved=total_results,
            dense_retrieval_accuracy=dense_accuracy,
            sparse_retrieval_effectiveness=sparse_effectiveness,
            hybrid_fusion_quality=hybrid_fusion_quality,
            average_retrieval_latency=avg_latency,
            score_distribution_quality=score_distribution_quality,
            ranking_accuracy=ranking_accuracy,
            issues_found=list(set(all_issues)),
            recommendations=list(set(all_recommendations))
        )


def main():
    """Run retrieval system forensic tests."""
    forensics = RetrievalSystemForensics()
    analysis = forensics.run_all_retrieval_system_tests()
    
    # Save results
    results_file = project_root / f"retrieval_system_forensics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(results_file, 'w') as f:
        json.dump(asdict(analysis), f, indent=2)
    
    print(f"\n💾 Results saved to: {results_file}")
    return analysis


if __name__ == "__main__":
    main()