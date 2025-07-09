#!/usr/bin/env python3
"""
Comprehensive Integration Test Suite

This test provides complete visibility into all system components and data flow,
allowing full control over component behavior and capturing all relevant metrics.

Features:
- Complete end-to-end workflow with data capture at each stage
- Full visibility into chunks, embeddings, prompts, answers, sources
- Comprehensive metrics for all components
- Component behavior control and validation
- Production-ready integration testing
"""

import sys
import time
import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from src.core.platform_orchestrator import PlatformOrchestrator
from src.core.interfaces import Document, Answer
from src.components.processors.pdf_processor import HybridPDFProcessor
from src.components.embedders.sentence_transformer_embedder import SentenceTransformerEmbedder
from src.components.retrievers.unified_retriever import UnifiedRetriever
from src.components.generators.adaptive_generator import AdaptiveAnswerGenerator

logger = logging.getLogger(__name__)


class ComprehensiveIntegrationTest:
    """
    Comprehensive integration test with full data visibility and component control.
    
    This test provides complete transparency into:
    - Document processing pipeline (PDF → chunks → metadata)
    - Embedding generation (text → vectors → similarity)
    - Retrieval system (query → candidates → ranking)
    - Answer generation (query + context → answer + confidence)
    - System health and performance metrics
    """
    
    def __init__(self, config_path: str = "config/default.yaml"):
        """Initialize comprehensive integration test."""
        self.config_path = config_path
        self.orchestrator = None
        self.test_results = {
            'timestamp': datetime.now().isoformat(),
            'test_id': f"integration_test_{int(time.time())}",
            'config_path': config_path,
            'document_processing': {},
            'embedding_generation': {},
            'retrieval_system': {},
            'answer_generation': {},
            'system_metrics': {},
            'component_health': {},
            'full_data_capture': {}
        }
        self.test_documents = []
        self.processed_chunks = []
        self.embeddings_data = []
        self.retrieval_results = []
        self.generation_results = []
    
    def _count_actual_citations(self, answer) -> int:
        """Count actual chunk citations in answer text."""
        import re
        pattern = r'\[chunk_\d+\]'
        citations = re.findall(pattern, answer.text)
        return len(set(citations))  # Count unique citations
    
    def _validate_citations(self, answer, retrieved_chunks_count) -> Dict[str, Any]:
        """Validate that citations don't exceed available chunks."""
        import re
        cited_chunks = re.findall(r'\[chunk_(\d+)\]', answer.text)
        cited_numbers = [int(num) for num in cited_chunks]
        
        max_cited = max(cited_numbers) if cited_numbers else 0
        invalid_citations = [num for num in cited_numbers if num > retrieved_chunks_count]
        
        return {
            'total_citations': len(cited_numbers),
            'unique_citations': len(set(cited_numbers)), 
            'max_chunk_cited': max_cited,
            'retrieved_chunks': retrieved_chunks_count,
            'invalid_citations': invalid_citations,
            'citation_valid': len(invalid_citations) == 0,
            'validation_message': f"Citations valid: {len(invalid_citations) == 0}" if len(invalid_citations) == 0 else f"INVALID: Found citations to chunks {invalid_citations} but only {retrieved_chunks_count} chunks retrieved"
        }
    
    def run_comprehensive_test(self) -> Dict[str, Any]:
        """
        Run comprehensive integration test with full data capture.
        
        Returns:
            Complete test results with all data and metrics
        """
        print("=" * 100)
        print("COMPREHENSIVE INTEGRATION TEST - FULL DATA VISIBILITY")
        print(f"Timestamp: {self.test_results['timestamp']}")
        print("=" * 100)
        
        try:
            # Phase 1: System initialization with health check
            print("\n🚀 PHASE 1: SYSTEM INITIALIZATION")
            self._test_system_initialization()
            
            # Phase 2: Document processing with full data capture
            print("\n📄 PHASE 2: DOCUMENT PROCESSING PIPELINE")
            self._test_document_processing()
            
            # Phase 3: Embedding generation with vector analysis
            print("\n🔢 PHASE 3: EMBEDDING GENERATION AND ANALYSIS")
            self._test_embedding_generation()
            
            # Phase 4: Retrieval system with ranking analysis
            print("\n🔍 PHASE 4: RETRIEVAL SYSTEM ANALYSIS")
            self._test_retrieval_system()
            
            # Phase 5: Answer generation with confidence analysis
            print("\n🎯 PHASE 5: ANSWER GENERATION ANALYSIS")
            self._test_answer_generation()
            
            # Phase 6: System health and performance metrics
            print("\n📊 PHASE 6: SYSTEM HEALTH AND PERFORMANCE")
            self._test_system_health()
            
            # Phase 7: Component behavior validation
            print("\n🔧 PHASE 7: COMPONENT BEHAVIOR VALIDATION")
            self._test_component_behavior()
            
            # Phase 8: Data integrity validation
            print("\n✅ PHASE 8: DATA INTEGRITY VALIDATION")
            self._validate_data_integrity()
            
            # Generate comprehensive report
            print("\n📋 GENERATING COMPREHENSIVE REPORT")
            self._generate_comprehensive_report()
            
            return self.test_results
            
        except Exception as e:
            print(f"❌ COMPREHENSIVE TEST FAILED: {str(e)}")
            import traceback
            traceback.print_exc()
            self.test_results['fatal_error'] = str(e)
            return self.test_results
    
    def _test_system_initialization(self):
        """Test system initialization with health monitoring."""
        print("  • Initializing system...")
        start_time = time.time()
        
        self.orchestrator = PlatformOrchestrator(self.config_path)
        initialization_time = time.time() - start_time
        
        # Capture system health
        health = self.orchestrator.get_system_health()
        
        self.test_results['system_metrics']['initialization'] = {
            'initialization_time': initialization_time,
            'status': health.get('status'),
            'architecture': health.get('architecture'),
            'components_count': len(health.get('components', {})),
            'factory_info': health.get('factory_info', {}),
            'performance_metrics': health.get('performance_metrics', {}),
            'cache_stats': health.get('cache_stats', {}),
            'deployment_readiness': health.get('deployment_readiness', {})
        }
        
        print(f"    ✅ System initialized in {initialization_time:.3f}s")
        print(f"    ✅ Architecture: {health.get('architecture')}")
        print(f"    ✅ Components: {len(health.get('components', {}))}")
        print(f"    ✅ Deployment ready: {health.get('deployment_readiness', {}).get('ready', False)}")
    
    def _test_document_processing(self):
        """Test document processing with full chunk visibility."""
        print("  • Testing document processing pipeline...")
        
        # Create test documents with rich metadata
        test_docs = [
            Document(
                content="RISC-V is an open-source instruction set architecture (ISA) based on reduced instruction set computer (RISC) principles. It originated at UC Berkeley and has gained significant adoption in academia and industry.",
                metadata={
                    'source': 'riscv-intro.pdf',
                    'page': 1,
                    'section': 'Introduction',
                    'chunk_id': 'intro_1',
                    'document_type': 'technical_specification',
                    'word_count': 32,
                    'creation_date': datetime.now().isoformat()
                }
            ),
            Document(
                content="The RISC-V instruction set includes base integer instructions (RV32I, RV64I) and optional standard extensions: M (multiplication), A (atomic), F (single-precision floating-point), D (double-precision floating-point), and C (compressed instructions).",
                metadata={
                    'source': 'riscv-spec.pdf',
                    'page': 15,
                    'section': 'Instruction Set Extensions',
                    'chunk_id': 'extensions_1',
                    'document_type': 'technical_specification',
                    'word_count': 35,
                    'creation_date': datetime.now().isoformat()
                }
            ),
            Document(
                content="RISC-V provides a modular approach to processor design, allowing implementations to select only the extensions they need. This modularity enables efficient designs for different application domains, from embedded systems to high-performance computing.",
                metadata={
                    'source': 'riscv-design.pdf',
                    'page': 8,
                    'section': 'Design Philosophy',
                    'chunk_id': 'design_1',
                    'document_type': 'technical_specification',
                    'word_count': 38,
                    'creation_date': datetime.now().isoformat()
                }
            )
        ]
        
        # Process documents with timing
        start_time = time.time()
        indexed_count = self.orchestrator.index_documents(test_docs)
        processing_time = time.time() - start_time
        
        # Capture processing metrics
        self.test_results['document_processing'] = {
            'documents_processed': len(test_docs),
            'documents_indexed': indexed_count,
            'processing_time': processing_time,
            'processing_rate': len(test_docs) / processing_time if processing_time > 0 else 0,
            'success_rate': indexed_count / len(test_docs) if test_docs else 0,
            'chunk_analysis': self._analyze_chunks(test_docs)
        }
        
        # Store for later analysis
        self.test_documents = test_docs
        self.processed_chunks = test_docs  # In this case, documents are pre-chunked
        
        print(f"    ✅ Processed {len(test_docs)} documents in {processing_time:.3f}s")
        print(f"    ✅ Indexed {indexed_count} documents")
        print(f"    ✅ Processing rate: {len(test_docs) / processing_time:.2f} docs/sec")
        
        # Capture full chunk data
        self.test_results['full_data_capture']['chunks'] = [
            {
                'chunk_id': doc.metadata.get('chunk_id'),
                'content': doc.content,
                'content_length': len(doc.content),
                'word_count': len(doc.content.split()),
                'metadata': doc.metadata,
                'has_embedding': doc.embedding is not None
            }
            for doc in test_docs
        ]
    
    def _test_embedding_generation(self):
        """Test embedding generation with vector analysis."""
        print("  • Testing embedding generation and analysis...")
        
        # Get embedder component
        embedder = self.orchestrator.get_component('embedder')
        if not embedder:
            print("    ❌ Embedder component not available")
            return
        
        # Generate embeddings for test texts
        test_texts = [doc.content for doc in self.test_documents]
        
        start_time = time.time()
        embeddings = embedder.embed(test_texts)
        embedding_time = time.time() - start_time
        
        # Analyze embeddings
        embedding_analysis = self._analyze_embeddings(embeddings, test_texts)
        
        self.test_results['embedding_generation'] = {
            'texts_processed': len(test_texts),
            'embeddings_generated': len(embeddings),
            'generation_time': embedding_time,
            'embedding_rate': len(test_texts) / embedding_time if embedding_time > 0 else 0,
            'embedding_dimension': len(embeddings[0]) if embeddings else 0,
            'embedding_analysis': embedding_analysis
        }
        
        # Store embeddings data
        self.embeddings_data = [
            {
                'text': text,
                'embedding': embedding.tolist() if hasattr(embedding, 'tolist') else embedding,
                'embedding_norm': float(sum(x*x for x in embedding)**0.5),
                'text_length': len(text),
                'word_count': len(text.split())
            }
            for text, embedding in zip(test_texts, embeddings)
        ]
        
        print(f"    ✅ Generated {len(embeddings)} embeddings in {embedding_time:.3f}s")
        print(f"    ✅ Embedding dimension: {len(embeddings[0]) if embeddings else 0}")
        print(f"    ✅ Average similarity: {embedding_analysis.get('average_similarity', 0):.3f}")
        
        # Capture full embedding data
        self.test_results['full_data_capture']['embeddings'] = self.embeddings_data
    
    def _test_retrieval_system(self):
        """Test retrieval system with ranking analysis."""
        print("  • Testing retrieval system with ranking analysis...")
        
        # Test queries with expected results
        test_queries = [
            {
                'query': 'What is RISC-V?',
                'expected_chunks': ['intro_1'],
                'query_type': 'definition'
            },
            {
                'query': 'What are RISC-V extensions?',
                'expected_chunks': ['extensions_1'],
                'query_type': 'technical_detail'
            },
            {
                'query': 'How does RISC-V modularity work?',
                'expected_chunks': ['design_1'],
                'query_type': 'conceptual'
            }
        ]
        
        retrieval_results = []
        
        for query_info in test_queries:
            query = query_info['query']
            print(f"    • Testing query: '{query}'")
            
            # Get retriever component
            retriever = self.orchestrator.get_component('retriever')
            if not retriever:
                print("      ❌ Retriever component not available")
                continue
            
            # Perform retrieval with timing
            start_time = time.time()
            results = retriever.retrieve(query, k=5)
            retrieval_time = time.time() - start_time
            
            # Analyze retrieval results
            result_analysis = self._analyze_retrieval_results(results, query_info)
            
            query_result = {
                'query': query,
                'query_type': query_info['query_type'],
                'expected_chunks': query_info['expected_chunks'],
                'retrieval_time': retrieval_time,
                'results_count': len(results),
                'result_analysis': result_analysis,
                'results': [
                    {
                        'document_id': r.document.metadata.get('chunk_id'),
                        'content': r.document.content,
                        'score': r.score,
                        'retrieval_method': r.retrieval_method,
                        'metadata': r.document.metadata
                    }
                    for r in results
                ]
            }
            
            retrieval_results.append(query_result)
            print(f"      ✅ Retrieved {len(results)} results in {retrieval_time:.3f}s")
            print(f"      ✅ Top score: {results[0].score:.3f}" if results else "      ❌ No results")
            
            # Display retrieval preview for each chunk
            print(f"      📄 Retrieval preview ({len(results)} chunks):")
            for i, result in enumerate(results):
                chunk_preview = result.document.content[:100]
                if len(result.document.content) > 100:
                    chunk_preview += "..."
                print(f"        {i+1}. {chunk_preview}")
                print(f"           Score: {result.score:.3f}, Method: {result.retrieval_method}")
                print(f"           Source: {result.document.metadata.get('source', 'unknown')}")
        
        self.test_results['retrieval_system'] = {
            'queries_tested': len(test_queries),
            'total_results': sum(len(r['results']) for r in retrieval_results),
            'average_retrieval_time': sum(r['retrieval_time'] for r in retrieval_results) / len(retrieval_results),
            'retrieval_analysis': self._analyze_retrieval_performance(retrieval_results),
            'query_results': retrieval_results
        }
        
        # Store retrieval results
        self.retrieval_results = retrieval_results
        
        # Capture full retrieval data
        self.test_results['full_data_capture']['retrieval'] = retrieval_results
    
    def _test_answer_generation(self):
        """Test answer generation with confidence analysis."""
        print("  • Testing answer generation with confidence analysis...")
        
        # Test queries for answer generation
        test_queries = [
            {
                'query': 'What is RISC-V and why is it important?',
                'expected_length': 200,
                'expected_confidence': 0.7,
                'query_category': 'comprehensive'
            },
            {
                'query': 'List the main RISC-V extensions',
                'expected_length': 150,
                'expected_confidence': 0.8,
                'query_category': 'factual'
            },
            {
                'query': 'How does RISC-V modularity benefit processor design?',
                'expected_length': 180,
                'expected_confidence': 0.7,
                'query_category': 'analytical'
            }
        ]
        
        generation_results = []
        
        for query_info in test_queries:
            query = query_info['query']
            print(f"    • Testing query: '{query}'")
            print(f"      🔍 Query preview: Category={query_info['query_category']}, Expected length={query_info['expected_length']}, Expected confidence={query_info['expected_confidence']:.1f}")
            
            # Process query with full timing
            start_time = time.time()
            answer = self.orchestrator.process_query(query)
            generation_time = time.time() - start_time
            
            # Get retrieval information from answer metadata
            retrieved_chunks_count = answer.metadata.get('retrieved_docs', 0)
            
            # Analyze answer quality
            answer_analysis = self._analyze_answer_quality(answer, query_info)
            
            # Check if fallback was used
            fallback_used = self._check_if_fallback_used(answer)
            
            query_result = {
                'query': query,
                'query_category': query_info['query_category'],
                'expected_length': query_info['expected_length'],
                'expected_confidence': query_info['expected_confidence'],
                'generation_time': generation_time,
                'answer_length': len(answer.text),
                'answer_confidence': answer.confidence,
                'sources_count': len(answer.sources),
                'answer_analysis': answer_analysis,
                'answer_text': answer.text,
                'answer_metadata': answer.metadata,
                'fallback_used': fallback_used,
                'sources': [
                    {
                        'source': src.metadata.get('source'),
                        'chunk_id': src.metadata.get('chunk_id'),
                        'content': src.content,
                        'metadata': src.metadata
                    }
                    for src in answer.sources
                ]
            }
            
            generation_results.append(query_result)
            print(f"      ✅ Generated answer in {generation_time:.3f}s")
            print(f"      ✅ Answer length: {len(answer.text)} chars")
            print(f"      ✅ Confidence: {answer.confidence:.3f}")
            actual_citations_count = self._count_actual_citations(answer)
            print(f"      📊 Retrieved chunks: {retrieved_chunks_count}, Cited sources: {actual_citations_count}")
            
            # Show which chunks were cited
            import re
            cited_chunks = re.findall(r'\[chunk_\d+\]', answer.text)
            if cited_chunks:
                print(f"      📋 Citations found: {list(set(cited_chunks))}")
            else:
                print(f"      📋 Citations found: []")
            
            # Validate citations
            citation_validation = self._validate_citations(answer, retrieved_chunks_count)
            if not citation_validation['citation_valid']:
                print(f"      ⚠️ CITATION VALIDATION: {citation_validation['validation_message']}")
            else:
                print(f"      ✅ Citation validation: All citations valid")
            
            # Check if fallback was used and show appropriate display
            fallback_used = self._check_if_fallback_used(answer)
            citations_invalid = not citation_validation['citation_valid']
            
            if fallback_used or citations_invalid:
                if citations_invalid:
                    print(f"      ⚠️ INVALID CITATIONS - Showing full answer:")
                    print(f"      💥 CITATION FAILURE: {citation_validation['validation_message']}")
                if fallback_used:
                    print(f"      ⚠️ FALLBACK DETECTED - Showing full answer:")
                print(f"      📝 Full Answer: {answer.text}")
                if fallback_used:
                    print(f"      🔍 Fallback reason: {fallback_used}")
            else:
                print(f"      📝 Answer preview: {answer.text[:200]}...")
                if len(answer.text) > 200:
                    print(f"      📊 Full answer length: {len(answer.text)} characters")
        
        self.test_results['answer_generation'] = {
            'queries_tested': len(test_queries),
            'average_generation_time': sum(r['generation_time'] for r in generation_results) / len(generation_results),
            'average_answer_length': sum(r['answer_length'] for r in generation_results) / len(generation_results),
            'average_confidence': sum(r['answer_confidence'] for r in generation_results) / len(generation_results),
            'generation_analysis': self._analyze_generation_performance(generation_results),
            'query_results': generation_results
        }
        
        # Store generation results
        self.generation_results = generation_results
        
        # Capture full generation data
        self.test_results['full_data_capture']['answers'] = generation_results
    
    def _test_system_health(self):
        """Test system health and performance metrics."""
        print("  • Testing system health and performance...")
        
        # Get comprehensive system health
        health = self.orchestrator.get_system_health()
        
        # Analyze component health
        component_health = {}
        for name, component_info in health.get('components', {}).items():
            component_health[name] = {
                'type': component_info.get('type'),
                'healthy': component_info.get('healthy'),
                'health_checks': component_info.get('health_checks', {}),
                'config': component_info.get('config', {}),
                'stats': component_info.get('stats', {})
            }
        
        self.test_results['system_metrics']['health'] = {
            'overall_status': health.get('status'),
            'architecture': health.get('architecture'),
            'deployment_readiness': health.get('deployment_readiness', {}),
            'factory_info': health.get('factory_info', {}),
            'performance_metrics': health.get('performance_metrics', {}),
            'cache_stats': health.get('cache_stats', {}),
            'components': component_health
        }
        
        self.test_results['component_health'] = component_health
        
        print(f"    ✅ Overall status: {health.get('status')}")
        print(f"    ✅ Architecture: {health.get('architecture')}")
        print(f"    ✅ Deployment ready: {health.get('deployment_readiness', {}).get('ready', False)}")
        print(f"    ✅ Components healthy: {sum(1 for c in component_health.values() if c.get('healthy'))}/{len(component_health)}")
    
    def _test_component_behavior(self):
        """Test individual component behavior with control."""
        print("  • Testing individual component behavior...")
        
        component_tests = {}
        
        # Test each component individually
        for component_name in ['document_processor', 'embedder', 'retriever', 'answer_generator']:
            component = self.orchestrator.get_component(component_name)
            if component:
                component_tests[component_name] = self._test_individual_component(component, component_name)
        
        self.test_results['component_behavior'] = component_tests
        
        print(f"    ✅ Tested {len(component_tests)} components")
    
    def _validate_data_integrity(self):
        """Validate data integrity across all components."""
        print("  • Validating data integrity...")
        
        integrity_checks = {
            'chunk_embedding_consistency': self._check_chunk_embedding_consistency(),
            'retrieval_source_consistency': self._check_retrieval_source_consistency(),
            'answer_source_consistency': self._check_answer_source_consistency(),
            'metadata_preservation': self._check_metadata_preservation(),
            'confidence_calibration': self._check_confidence_calibration()
        }
        
        self.test_results['data_integrity'] = integrity_checks
        
        passed_checks = sum(1 for check in integrity_checks.values() if check.get('passed', False))
        print(f"    ✅ Data integrity: {passed_checks}/{len(integrity_checks)} checks passed")
    
    def _analyze_chunks(self, documents: List[Document]) -> Dict[str, Any]:
        """Analyze document chunks for coverage and quality."""
        if not documents:
            return {}
        
        total_content_length = sum(len(doc.content) for doc in documents)
        total_word_count = sum(len(doc.content.split()) for doc in documents)
        
        return {
            'total_chunks': len(documents),
            'total_content_length': total_content_length,
            'total_word_count': total_word_count,
            'average_chunk_length': total_content_length / len(documents),
            'average_word_count': total_word_count / len(documents),
            'chunk_length_distribution': [len(doc.content) for doc in documents],
            'sources_covered': len(set(doc.metadata.get('source', 'unknown') for doc in documents)),
            'metadata_fields': list(set().union(*(doc.metadata.keys() for doc in documents)))
        }
    
    def _analyze_embeddings(self, embeddings: List, texts: List[str]) -> Dict[str, Any]:
        """Analyze embedding quality and relationships."""
        if not embeddings or not texts:
            return {}
        
        # Calculate pairwise similarities
        similarities = []
        for i in range(len(embeddings)):
            for j in range(i + 1, len(embeddings)):
                emb1, emb2 = embeddings[i], embeddings[j]
                # Cosine similarity
                dot_product = sum(a * b for a, b in zip(emb1, emb2))
                norm1 = sum(a * a for a in emb1) ** 0.5
                norm2 = sum(b * b for b in emb2) ** 0.5
                similarity = dot_product / (norm1 * norm2) if norm1 * norm2 > 0 else 0
                similarities.append(similarity)
        
        return {
            'embedding_dimension': len(embeddings[0]) if embeddings else 0,
            'embeddings_generated': len(embeddings),
            'average_similarity': sum(similarities) / len(similarities) if similarities else 0,
            'min_similarity': min(similarities) if similarities else 0,
            'max_similarity': max(similarities) if similarities else 0,
            'similarity_distribution': similarities
        }
    
    def _analyze_retrieval_results(self, results: List, query_info: Dict) -> Dict[str, Any]:
        """Analyze retrieval results for quality and relevance."""
        if not results:
            return {'no_results': True}
        
        expected_chunks = query_info.get('expected_chunks', [])
        found_expected = sum(1 for r in results if r.document.metadata.get('chunk_id') in expected_chunks)
        
        return {
            'results_count': len(results),
            'expected_chunks_found': found_expected,
            'expected_chunks_total': len(expected_chunks),
            'precision_at_k': found_expected / min(len(results), len(expected_chunks)) if expected_chunks else 0,
            'top_score': results[0].score if results else 0,
            'score_distribution': [r.score for r in results],
            'retrieval_methods': list(set(r.retrieval_method for r in results)),
            'unique_sources': len(set(r.document.metadata.get('source', 'unknown') for r in results))
        }
    
    def _analyze_retrieval_performance(self, retrieval_results: List) -> Dict[str, Any]:
        """Analyze overall retrieval performance."""
        if not retrieval_results:
            return {}
        
        total_precision = sum(r['result_analysis'].get('precision_at_k', 0) for r in retrieval_results)
        
        return {
            'average_precision': total_precision / len(retrieval_results),
            'average_results_per_query': sum(r['results_count'] for r in retrieval_results) / len(retrieval_results),
            'average_top_score': sum(r['results'][0]['score'] for r in retrieval_results if r['results']) / len(retrieval_results),
            'retrieval_methods_used': list(set().union(*(r['result_analysis'].get('retrieval_methods', []) for r in retrieval_results)))
        }
    
    def _analyze_answer_quality(self, answer: Answer, query_info: Dict) -> Dict[str, Any]:
        """Analyze answer quality and appropriateness."""
        expected_length = query_info.get('expected_length', 0)
        expected_confidence = query_info.get('expected_confidence', 0)
        
        return {
            'length_appropriate': abs(len(answer.text) - expected_length) < expected_length * 0.5,
            'confidence_appropriate': abs(answer.confidence - expected_confidence) < 0.2,
            'has_sources': len(answer.sources) > 0,
            'source_diversity': len(set(src.metadata.get('source', 'unknown') for src in answer.sources)),
            'answer_coherence': self._assess_answer_coherence(answer.text),
            'technical_accuracy': self._assess_technical_accuracy(answer.text, query_info['query_category'])
        }
    
    def _analyze_generation_performance(self, generation_results: List) -> Dict[str, Any]:
        """Analyze overall generation performance."""
        if not generation_results:
            return {}
        
        length_appropriate = sum(1 for r in generation_results if r['answer_analysis'].get('length_appropriate', False))
        confidence_appropriate = sum(1 for r in generation_results if r['answer_analysis'].get('confidence_appropriate', False))
        
        return {
            'length_appropriateness_rate': length_appropriate / len(generation_results),
            'confidence_appropriateness_rate': confidence_appropriate / len(generation_results),
            'average_source_count': sum(r['sources_count'] for r in generation_results) / len(generation_results),
            'average_source_diversity': sum(r['answer_analysis'].get('source_diversity', 0) for r in generation_results) / len(generation_results)
        }
    
    def _test_individual_component(self, component: Any, component_name: str) -> Dict[str, Any]:
        """Test individual component behavior."""
        component_test = {
            'component_name': component_name,
            'component_type': type(component).__name__,
            'tests_performed': []
        }
        
        # Test based on component type
        if hasattr(component, 'embed') and component_name == 'embedder':
            # Test embedder
            test_text = "Test embedding generation"
            start_time = time.time()
            embedding = component.embed([test_text])
            test_time = time.time() - start_time
            
            component_test['tests_performed'].append({
                'test_type': 'embedding_generation',
                'test_time': test_time,
                'input': test_text,
                'output_dimension': len(embedding[0]) if embedding else 0,
                'success': len(embedding) > 0
            })
        
        elif hasattr(component, 'retrieve') and component_name == 'retriever':
            # Test retriever
            test_query = "Test retrieval query"
            start_time = time.time()
            try:
                results = component.retrieve(test_query, k=3)
                test_time = time.time() - start_time
                
                component_test['tests_performed'].append({
                    'test_type': 'retrieval',
                    'test_time': test_time,
                    'input': test_query,
                    'results_count': len(results),
                    'success': True
                })
            except Exception as e:
                test_time = time.time() - start_time
                component_test['tests_performed'].append({
                    'test_type': 'retrieval',
                    'test_time': test_time,
                    'input': test_query,
                    'error': str(e),
                    'success': False
                })
        
        elif hasattr(component, 'generate') and component_name == 'answer_generator':
            # Test answer generator
            test_query = "Test answer generation"
            test_context = [Document(content="Test context document", metadata={'source': 'test'})]
            start_time = time.time()
            try:
                answer = component.generate(test_query, test_context)
                test_time = time.time() - start_time
                
                component_test['tests_performed'].append({
                    'test_type': 'answer_generation',
                    'test_time': test_time,
                    'input': test_query,
                    'answer_length': len(answer.text),
                    'confidence': answer.confidence,
                    'success': True
                })
            except Exception as e:
                test_time = time.time() - start_time
                component_test['tests_performed'].append({
                    'test_type': 'answer_generation',
                    'test_time': test_time,
                    'input': test_query,
                    'error': str(e),
                    'success': False
                })
        
        return component_test
    
    def _check_chunk_embedding_consistency(self) -> Dict[str, Any]:
        """Check consistency between chunks and embeddings."""
        if not self.processed_chunks or not self.embeddings_data:
            return {'passed': False, 'reason': 'No data available'}
        
        consistency_check = {
            'chunk_count': len(self.processed_chunks),
            'embedding_count': len(self.embeddings_data),
            'counts_match': len(self.processed_chunks) == len(self.embeddings_data),
            'passed': len(self.processed_chunks) == len(self.embeddings_data)
        }
        
        return consistency_check
    
    def _check_retrieval_source_consistency(self) -> Dict[str, Any]:
        """Check consistency between retrieval results and source documents."""
        if not self.retrieval_results or not self.processed_chunks:
            return {'passed': False, 'reason': 'No data available'}
        
        source_chunk_ids = set(doc.metadata.get('chunk_id') for doc in self.processed_chunks)
        retrieved_chunk_ids = set()
        
        for result in self.retrieval_results:
            for res in result['results']:
                retrieved_chunk_ids.add(res['document_id'])
        
        consistency_check = {
            'source_chunks': len(source_chunk_ids),
            'retrieved_chunks': len(retrieved_chunk_ids),
            'valid_retrievals': len(retrieved_chunk_ids.intersection(source_chunk_ids)),
            'invalid_retrievals': len(retrieved_chunk_ids - source_chunk_ids),
            'passed': len(retrieved_chunk_ids - source_chunk_ids) == 0
        }
        
        return consistency_check
    
    def _check_answer_source_consistency(self) -> Dict[str, Any]:
        """Check consistency between answer sources and available documents."""
        if not self.generation_results or not self.processed_chunks:
            return {'passed': False, 'reason': 'No data available'}
        
        source_chunk_ids = set(doc.metadata.get('chunk_id') for doc in self.processed_chunks)
        answer_source_ids = set()
        
        for result in self.generation_results:
            for source in result['sources']:
                answer_source_ids.add(source['chunk_id'])
        
        consistency_check = {
            'source_chunks': len(source_chunk_ids),
            'answer_sources': len(answer_source_ids),
            'valid_sources': len(answer_source_ids.intersection(source_chunk_ids)),
            'invalid_sources': len(answer_source_ids - source_chunk_ids),
            'passed': len(answer_source_ids - source_chunk_ids) == 0
        }
        
        return consistency_check
    
    def _check_metadata_preservation(self) -> Dict[str, Any]:
        """Check metadata preservation through the pipeline."""
        if not self.processed_chunks:
            return {'passed': False, 'reason': 'No data available'}
        
        required_fields = ['source', 'chunk_id', 'page']
        metadata_preservation = {}
        
        for field in required_fields:
            field_present = sum(1 for doc in self.processed_chunks if field in doc.metadata)
            metadata_preservation[field] = {
                'present_count': field_present,
                'total_count': len(self.processed_chunks),
                'preservation_rate': field_present / len(self.processed_chunks)
            }
        
        overall_passed = all(
            metadata_preservation[field]['preservation_rate'] >= 0.8
            for field in required_fields
        )
        
        return {
            'field_preservation': metadata_preservation,
            'overall_preservation_rate': sum(
                metadata_preservation[field]['preservation_rate']
                for field in required_fields
            ) / len(required_fields),
            'passed': overall_passed
        }
    
    def _check_confidence_calibration(self) -> Dict[str, Any]:
        """Check confidence score calibration."""
        if not self.generation_results:
            return {'passed': False, 'reason': 'No data available'}
        
        confidences = [r['answer_confidence'] for r in self.generation_results]
        
        calibration_check = {
            'confidence_count': len(confidences),
            'average_confidence': sum(confidences) / len(confidences),
            'min_confidence': min(confidences),
            'max_confidence': max(confidences),
            'reasonable_range': all(0.0 <= c <= 1.0 for c in confidences),
            'not_too_low': all(c >= 0.1 for c in confidences),
            'not_too_high': all(c <= 0.95 for c in confidences),
            'passed': all(0.1 <= c <= 0.95 for c in confidences)
        }
        
        return calibration_check
    
    def _assess_answer_coherence(self, answer_text: str) -> float:
        """Assess answer coherence (simplified)."""
        # Simple coherence assessment based on text properties
        sentences = answer_text.split('.')
        if len(sentences) < 2:
            return 0.5
        
        # Check for reasonable sentence length distribution
        sentence_lengths = [len(s.strip()) for s in sentences if s.strip()]
        if not sentence_lengths:
            return 0.3
        
        avg_length = sum(sentence_lengths) / len(sentence_lengths)
        
        # Coherence score based on average sentence length and count
        if 20 <= avg_length <= 150 and 2 <= len(sentences) <= 10:
            return 0.8
        elif 10 <= avg_length <= 200 and 1 <= len(sentences) <= 15:
            return 0.6
        else:
            return 0.4
    
    def _assess_technical_accuracy(self, answer_text: str, query_category: str) -> float:
        """Assess technical accuracy (simplified)."""
        # Simple accuracy assessment based on content
        technical_terms = ['risc-v', 'isa', 'instruction', 'architecture', 'extension', 'processor']
        
        answer_lower = answer_text.lower()
        terms_found = sum(1 for term in technical_terms if term in answer_lower)
        
        # Accuracy score based on technical term presence
        if query_category == 'comprehensive':
            return min(terms_found / 4, 1.0)  # Expect 4+ terms
        elif query_category == 'factual':
            return min(terms_found / 3, 1.0)  # Expect 3+ terms
        elif query_category == 'analytical':
            return min(terms_found / 2, 1.0)  # Expect 2+ terms
        else:
            return 0.5
    
    def _generate_comprehensive_report(self):
        """Generate comprehensive test report."""
        report = {
            'test_summary': {
                'total_phases': 8,
                'documents_processed': len(self.test_documents),
                'embeddings_generated': len(self.embeddings_data),
                'queries_tested': len(self.retrieval_results),
                'answers_generated': len(self.generation_results),
                'overall_success': True  # Will be updated based on checks
            },
            'performance_summary': {
                'document_processing_time': self.test_results.get('document_processing', {}).get('processing_time', 0),
                'embedding_generation_time': self.test_results.get('embedding_generation', {}).get('generation_time', 0),
                'average_retrieval_time': self.test_results.get('retrieval_system', {}).get('average_retrieval_time', 0),
                'average_generation_time': self.test_results.get('answer_generation', {}).get('average_generation_time', 0)
            },
            'quality_summary': {
                'retrieval_precision': self.test_results.get('retrieval_system', {}).get('retrieval_analysis', {}).get('average_precision', 0),
                'answer_length_appropriateness': self.test_results.get('answer_generation', {}).get('generation_analysis', {}).get('length_appropriateness_rate', 0),
                'confidence_appropriateness': self.test_results.get('answer_generation', {}).get('generation_analysis', {}).get('confidence_appropriateness_rate', 0),
                'data_integrity_checks': sum(1 for check in self.test_results.get('data_integrity', {}).values() if check.get('passed', False))
            }
        }
        
        self.test_results['comprehensive_report'] = report
        
        print("\n" + "=" * 80)
        print("COMPREHENSIVE TEST REPORT")
        print("=" * 80)
        print(f"✅ Documents processed: {report['test_summary']['documents_processed']}")
        print(f"✅ Embeddings generated: {report['test_summary']['embeddings_generated']}")
        print(f"✅ Queries tested: {report['test_summary']['queries_tested']}")
        print(f"✅ Answers generated: {report['test_summary']['answers_generated']}")
        print(f"✅ Data integrity checks: {report['quality_summary']['data_integrity_checks']}")
        print(f"✅ Average retrieval precision: {report['quality_summary']['retrieval_precision']:.3f}")
        print(f"✅ Answer quality rates: {report['quality_summary']['answer_length_appropriateness']:.3f}")
        print("=" * 80)
    
    def save_results(self, filename: str = None):
        """Save comprehensive test results to file."""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"comprehensive_integration_test_{timestamp}.json"
        
        with open(filename, 'w') as f:
            json.dump(self.test_results, f, indent=2, default=str)
        
        print(f"\n💾 Comprehensive test results saved to: {filename}")
        return filename
    
    def _check_if_fallback_used(self, answer):
        """Check if fallback citations were used in the answer."""
        # Check metadata for fallback indicators
        if hasattr(answer, 'metadata') and answer.metadata:
            if 'fallback_used' in answer.metadata:
                return answer.metadata['fallback_used']
            if 'citation_method' in answer.metadata and answer.metadata['citation_method'] == 'fallback':
                return 'Fallback citations created (no chunk references found)'
        
        # Check answer text for fallback patterns
        answer_text = answer.text.lower()
        
        # Look for fallback citation patterns
        fallback_patterns = [
            'fallback: creating',
            'creating 2 citations',
            'no explicit [chunk_',
            'fallback citations'
        ]
        
        for pattern in fallback_patterns:
            if pattern in answer_text:
                return f'Fallback detected: {pattern}'
        
        # Check if citations look like fallback format
        if len(answer.sources) > 0:
            # Check if all sources have generic metadata (typical of fallback)
            fallback_indicators = 0
            for source in answer.sources:
                if hasattr(source, 'metadata') and source.metadata:
                    # Generic chunk IDs or source names indicate fallback
                    if (source.metadata.get('chunk_id', '').startswith('fallback_') or 
                        source.metadata.get('source', '') == 'fallback'):
                        fallback_indicators += 1
            
            if fallback_indicators > 0:
                return f'Fallback sources detected ({fallback_indicators}/{len(answer.sources)})'
        
        return False


def main():
    """Main execution function."""
    test = ComprehensiveIntegrationTest()
    results = test.run_comprehensive_test()
    
    # Save results
    test.save_results()
    
    return results


if __name__ == "__main__":
    main()