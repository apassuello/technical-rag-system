#!/usr/bin/env python3
"""
Test Suite 6: Source Attribution Chain Analysis

This test suite provides comprehensive forensic analysis of the source attribution
chain from document processing through retrieval to answer generation.

Critical Focus Areas:
- Citation generation process analysis
- Metadata preservation through entire pipeline
- Source tracking integrity validation
- Page number extraction and preservation
- Citation-answer alignment verification
"""

import sys
import logging
import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass, asdict

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from tests.diagnostic.base_diagnostic import DiagnosticTestBase, DiagnosticResult
from src.core.interfaces import Document, RetrievalResult, Answer
from src.core.platform_orchestrator import PlatformOrchestrator
from src.components.embedders.sentence_transformer_embedder import SentenceTransformerEmbedder
from src.components.retrievers.unified_retriever import UnifiedRetriever
from src.components.generators.adaptive_generator import AdaptiveAnswerGenerator

logger = logging.getLogger(__name__)


@dataclass
class SourceAttributionAnalysis:
    """Analysis results for source attribution chain."""
    total_documents_processed: int
    total_queries_tested: int
    citation_generation_success_rate: float
    metadata_preservation_rate: float
    source_tracking_integrity: float
    page_number_accuracy: float
    citation_answer_alignment: float
    attribution_chain_completeness: float
    issues_found: List[str]
    recommendations: List[str]


class SourceAttributionForensics(DiagnosticTestBase):
    """
    Forensic analysis of source attribution chain.
    
    This class provides comprehensive testing of:
    - Citation generation process
    - Metadata preservation through pipeline
    - Source tracking integrity
    - Page number extraction and preservation
    - Citation-answer alignment
    """
    
    def __init__(self):
        super().__init__()
        self.orchestrator = None
        self.embedder = None
        self.retriever = None
        self.generator = None
        self.test_documents = []
        self.test_corpus_indexed = False
    
    def run_all_source_attribution_tests(self) -> SourceAttributionAnalysis:
        """
        Run comprehensive source attribution forensic tests.
        
        Returns:
            SourceAttributionAnalysis with complete results
        """
        print("=" * 80)
        print("TEST SUITE 6: SOURCE ATTRIBUTION CHAIN ANALYSIS")
        print("=" * 80)
        
        # Initialize components
        self._initialize_attribution_components()
        
        # Test 1: Citation Generation Process Analysis
        print("\n📝 Test 6.1: Citation Generation Process Analysis")
        citation_results = self.safe_execute(
            self._test_citation_generation_process, 
            "Citation_Generation_Process", 
            "adaptive_generator"
        )
        
        # Test 2: Metadata Preservation Chain Validation
        print("\n🔗 Test 6.2: Metadata Preservation Chain Validation")
        metadata_results = self.safe_execute(
            self._test_metadata_preservation_chain,
            "Metadata_Preservation_Chain",
            "platform_orchestrator"
        )
        
        # Test 3: Source Tracking Integrity Verification
        print("\n🎯 Test 6.3: Source Tracking Integrity Verification")
        tracking_results = self.safe_execute(
            self._test_source_tracking_integrity,
            "Source_Tracking_Integrity",
            "unified_retriever"
        )
        
        # Test 4: Page Number Extraction and Preservation
        print("\n📄 Test 6.4: Page Number Extraction and Preservation")
        page_results = self.safe_execute(
            self._test_page_number_extraction,
            "Page_Number_Extraction",
            "pdf_processor"
        )
        
        # Test 5: Citation-Answer Alignment Verification
        print("\n🔍 Test 6.5: Citation-Answer Alignment Verification")
        alignment_results = self.safe_execute(
            self._test_citation_answer_alignment,
            "Citation_Answer_Alignment",
            "adaptive_generator"
        )
        
        # Test 6: End-to-End Attribution Chain Completeness
        print("\n🌐 Test 6.6: End-to-End Attribution Chain Completeness")
        completeness_results = self.safe_execute(
            self._test_attribution_chain_completeness,
            "Attribution_Chain_Completeness",
            "platform_orchestrator"
        )
        
        # Aggregate results
        analysis = self._aggregate_attribution_analysis([
            citation_results, metadata_results, tracking_results,
            page_results, alignment_results, completeness_results
        ])
        
        print(f"\n📊 SOURCE ATTRIBUTION CHAIN ANALYSIS COMPLETE")
        print(f"Total Documents Processed: {analysis.total_documents_processed}")
        print(f"Total Queries Tested: {analysis.total_queries_tested}")
        print(f"Citation Generation Success Rate: {analysis.citation_generation_success_rate:.1%}")
        print(f"Metadata Preservation Rate: {analysis.metadata_preservation_rate:.1%}")
        print(f"Source Tracking Integrity: {analysis.source_tracking_integrity:.1%}")
        print(f"Page Number Accuracy: {analysis.page_number_accuracy:.1%}")
        print(f"Citation-Answer Alignment: {analysis.citation_answer_alignment:.1%}")
        print(f"Attribution Chain Completeness: {analysis.attribution_chain_completeness:.1%}")
        
        if analysis.issues_found:
            print(f"\n🚨 Issues Found ({len(analysis.issues_found)}):")
            for issue in analysis.issues_found:
                print(f"  - {issue}")
        
        if analysis.recommendations:
            print(f"\n💡 Recommendations ({len(analysis.recommendations)}):")
            for rec in analysis.recommendations:
                print(f"  - {rec}")
        
        return analysis
    
    def _initialize_attribution_components(self):
        """Initialize components for attribution testing."""
        print("  Initializing source attribution components...")
        
        # Initialize orchestrator
        self.orchestrator = PlatformOrchestrator("config/default.yaml")
        
        # Get components from orchestrator to ensure they share the same indexed documents
        self.embedder = SentenceTransformerEmbedder()
        self.retriever = self.orchestrator._components['retriever']  # Use orchestrator's retriever
        self.generator = self.orchestrator._components['answer_generator']  # Use orchestrator's generator
        
        # Create test documents with rich metadata
        self.test_documents = self._create_test_documents_with_metadata()
        
        # Index documents if not already done
        if not self.test_corpus_indexed:
            print(f"  Indexing {len(self.test_documents)} test documents...")
            self.orchestrator.index_documents(self.test_documents)
            self.test_corpus_indexed = True
            print("  ✅ Test corpus indexed successfully")
    
    def _create_test_documents_with_metadata(self) -> List[Document]:
        """Create test documents with comprehensive metadata."""
        documents_data = [
            {
                'content': "RISC-V is an open-source instruction set architecture (ISA) based on reduced instruction set computer (RISC) principles. It was originally developed at UC Berkeley in 2010 and has since gained widespread adoption in both academic and commercial settings.",
                'source': 'riscv-specification.pdf',
                'page': 1,
                'section': 'Introduction',
                'chapter': 'Chapter 1: Overview',
                'document_type': 'technical_specification',
                'author': 'RISC-V Foundation',
                'publication_date': '2023-01-15'
            },
            {
                'content': "The RISC-V vector extension (RVV) provides scalable vector processing capabilities that can efficiently handle data-parallel workloads. The extension supports variable-length vectors and includes operations for arithmetic, logical, and memory access patterns.",
                'source': 'riscv-vector-spec.pdf',
                'page': 25,
                'section': 'Vector Extension',
                'chapter': 'Chapter 3: Vector Operations',
                'document_type': 'technical_specification',
                'author': 'RISC-V Foundation',
                'publication_date': '2023-02-20'
            },
            {
                'content': "ARM Cortex-A processors implement the ARMv8 architecture and are designed for high-performance computing applications. These processors feature out-of-order execution, advanced branch prediction, and sophisticated cache hierarchies.",
                'source': 'arm-cortex-manual.pdf',
                'page': 42,
                'section': 'Processor Architecture',
                'chapter': 'Chapter 2: Cortex-A Series',
                'document_type': 'technical_manual',
                'author': 'ARM Limited',
                'publication_date': '2023-03-10'
            },
            {
                'content': "Machine learning accelerators are specialized hardware designed to efficiently execute neural network operations. These accelerators typically include matrix multiplication units, activation function hardware, and optimized memory systems.",
                'source': 'ml-accelerator-guide.pdf',
                'page': 67,
                'section': 'Hardware Acceleration',
                'chapter': 'Chapter 4: Specialized Processors',
                'document_type': 'technical_guide',
                'author': 'Tech Research Institute',
                'publication_date': '2023-04-05'
            }
        ]
        
        documents = []
        for i, data in enumerate(documents_data):
            # Generate embedding
            embedding = self.embedder.embed([data['content']])[0]
            
            document = Document(
                content=data['content'],
                metadata={
                    'source': data['source'],
                    'page': data['page'],
                    'section': data['section'],
                    'chapter': data['chapter'],
                    'document_type': data['document_type'],
                    'author': data['author'],
                    'publication_date': data['publication_date'],
                    'creation_date': datetime.now().isoformat(),
                    'word_count': len(data['content'].split()),
                    'doc_id': f"attribution_doc_{i}",
                    'chunk_id': f"attribution_chunk_{i}",
                    'file_path': f"data/docs/{data['source']}"
                },
                embedding=embedding
            )
            documents.append(document)
        
        return documents
    
    def _test_citation_generation_process(self) -> tuple:
        """Test citation generation process analysis."""
        print("  Testing citation generation process...")
        
        # Test queries that should generate citations
        test_queries = [
            "What is RISC-V architecture?",
            "Explain vector processing in RISC-V",
            "How do ARM Cortex-A processors work?",
            "What are machine learning accelerators?"
        ]
        
        citation_results = []
        
        for query in test_queries:
            try:
                # Get retrieval results
                retrieval_results = self.retriever.retrieve(query, k=3)
                
                # Generate answer with citations
                answer = self.generator.generate(query, retrieval_results)
                
                # Analyze citation generation
                citation_analysis = self._analyze_citation_generation(query, retrieval_results, answer)
                citation_results.append(citation_analysis)
                
                print(f"    Query: '{query[:30]}...' - Citations: {citation_analysis['citations_count']}")
                
            except Exception as e:
                print(f"    Error generating citations for '{query}': {e}")
                citation_results.append({
                    'query': query,
                    'success': False,
                    'issues': [f"Citation generation failed: {str(e)}"]
                })
        
        # Calculate citation generation success rate
        successful_citations = [r for r in citation_results if r.get('success', False)]
        success_rate = len(successful_citations) / len(citation_results) if citation_results else 0
        
        issues_found = []
        for result in citation_results:
            if not result.get('success', False):
                issues_found.extend(result.get('issues', []))
            elif result.get('citations_count', 0) == 0:
                issues_found.append(f"No citations generated for query: {result['query']}")
        
        data_captured = {
            "test_queries": test_queries,
            "total_queries": len(test_queries),
            "successful_citations": len(successful_citations),
            "citation_results": citation_results
        }
        
        analysis_results = {
            "success_rate": success_rate,
            "citation_generation_good": success_rate > 0.8,
            "summary": f"Citation generation success rate: {success_rate:.1%}"
        }
        
        return (
            data_captured,
            analysis_results,
            list(set(issues_found)),
            self._generate_citation_recommendations(citation_results)
        )
    
    def _test_metadata_preservation_chain(self) -> tuple:
        """Test metadata preservation through entire pipeline."""
        print("  Testing metadata preservation chain...")
        
        # Track metadata through pipeline stages
        preservation_results = []
        
        for doc in self.test_documents:
            try:
                # Stage 1: Document Processing (already done)
                original_metadata = doc.metadata.copy()
                
                # Stage 2: Retrieval
                query = doc.content[:50]  # Use content start as query
                retrieval_results = self.retriever.retrieve(query, k=1)
                
                if retrieval_results:
                    retrieved_metadata = retrieval_results[0].document.metadata
                    
                    # Stage 3: Answer Generation
                    answer = self.generator.generate(query, retrieval_results)
                    
                    # Analyze metadata preservation
                    preservation_analysis = self._analyze_metadata_preservation(
                        original_metadata, retrieved_metadata, answer
                    )
                    preservation_results.append(preservation_analysis)
                    
                    print(f"    Document: {doc.metadata['source']} - Preservation: {preservation_analysis['preservation_score']:.2f}")
                
            except Exception as e:
                preservation_results.append({
                    'document': doc.metadata.get('source', 'unknown'),
                    'success': False,
                    'issues': [f"Metadata preservation test failed: {str(e)}"]
                })
        
        # Calculate preservation rate
        successful_preservation = [r for r in preservation_results if r.get('success', False)]
        preservation_rate = sum(r['preservation_score'] for r in successful_preservation) / len(successful_preservation) if successful_preservation else 0
        
        issues_found = []
        for result in preservation_results:
            if not result.get('success', False):
                issues_found.extend(result.get('issues', []))
            elif result.get('preservation_score', 0) < 0.8:
                issues_found.append(f"Poor metadata preservation for {result.get('document', 'unknown')}")
        
        data_captured = {
            "test_documents": [doc.metadata['source'] for doc in self.test_documents],
            "total_documents": len(self.test_documents),
            "successful_preservation": len(successful_preservation),
            "preservation_results": preservation_results
        }
        
        analysis_results = {
            "preservation_rate": preservation_rate,
            "metadata_preservation_good": preservation_rate > 0.8,
            "summary": f"Metadata preservation rate: {preservation_rate:.1%}"
        }
        
        return (
            data_captured,
            analysis_results,
            list(set(issues_found)),
            self._generate_preservation_recommendations(preservation_results)
        )
    
    def _test_source_tracking_integrity(self) -> tuple:
        """Test source tracking integrity verification."""
        print("  Testing source tracking integrity...")
        
        # Test source tracking through retrieval
        tracking_results = []
        
        for doc in self.test_documents:
            try:
                # Use document content as query
                query = doc.content[:100]
                retrieval_results = self.retriever.retrieve(query, k=3)
                
                # Analyze source tracking
                tracking_analysis = self._analyze_source_tracking(doc, retrieval_results)
                tracking_results.append(tracking_analysis)
                
                print(f"    Source: {doc.metadata['source']} - Tracking: {tracking_analysis['tracking_score']:.2f}")
                
            except Exception as e:
                tracking_results.append({
                    'source': doc.metadata.get('source', 'unknown'),
                    'success': False,
                    'issues': [f"Source tracking test failed: {str(e)}"]
                })
        
        # Calculate tracking integrity
        successful_tracking = [r for r in tracking_results if r.get('success', False)]
        tracking_integrity = sum(r['tracking_score'] for r in successful_tracking) / len(successful_tracking) if successful_tracking else 0
        
        issues_found = []
        for result in tracking_results:
            if not result.get('success', False):
                issues_found.extend(result.get('issues', []))
            elif result.get('tracking_score', 0) < 0.8:
                issues_found.append(f"Poor source tracking for {result.get('source', 'unknown')}")
        
        data_captured = {
            "test_sources": [doc.metadata['source'] for doc in self.test_documents],
            "total_sources": len(self.test_documents),
            "successful_tracking": len(successful_tracking),
            "tracking_results": tracking_results
        }
        
        analysis_results = {
            "tracking_integrity": tracking_integrity,
            "source_tracking_good": tracking_integrity > 0.8,
            "summary": f"Source tracking integrity: {tracking_integrity:.1%}"
        }
        
        return (
            data_captured,
            analysis_results,
            list(set(issues_found)),
            self._generate_tracking_recommendations(tracking_results)
        )
    
    def _test_page_number_extraction(self) -> tuple:
        """Test page number extraction and preservation."""
        print("  Testing page number extraction and preservation...")
        
        # Test page number accuracy
        page_results = []
        
        for doc in self.test_documents:
            try:
                # Analyze page number extraction
                page_analysis = self._analyze_page_number_extraction(doc)
                page_results.append(page_analysis)
                
                print(f"    Source: {doc.metadata['source']} - Page: {page_analysis['extracted_page']}")
                
            except Exception as e:
                page_results.append({
                    'source': doc.metadata.get('source', 'unknown'),
                    'success': False,
                    'issues': [f"Page number extraction failed: {str(e)}"]
                })
        
        # Calculate page number accuracy
        successful_extraction = [r for r in page_results if r.get('success', False)]
        page_accuracy = sum(r['page_accuracy'] for r in successful_extraction) / len(successful_extraction) if successful_extraction else 0
        
        issues_found = []
        for result in page_results:
            if not result.get('success', False):
                issues_found.extend(result.get('issues', []))
            elif result.get('page_accuracy', 0) < 1.0:
                issues_found.append(f"Incorrect page number for {result.get('source', 'unknown')}")
        
        data_captured = {
            "test_documents": [doc.metadata['source'] for doc in self.test_documents],
            "total_documents": len(self.test_documents),
            "successful_extraction": len(successful_extraction),
            "page_results": page_results
        }
        
        analysis_results = {
            "page_accuracy": page_accuracy,
            "page_extraction_good": page_accuracy > 0.9,
            "summary": f"Page number accuracy: {page_accuracy:.1%}"
        }
        
        return (
            data_captured,
            analysis_results,
            list(set(issues_found)),
            self._generate_page_recommendations(page_results)
        )
    
    def _test_citation_answer_alignment(self) -> tuple:
        """Test citation-answer alignment verification."""
        print("  Testing citation-answer alignment...")
        
        # Test alignment for different queries
        alignment_queries = [
            "What is RISC-V?",
            "Explain vector processing capabilities",
            "How do ARM processors work?",
            "What are machine learning accelerators?"
        ]
        
        alignment_results = []
        
        for query in alignment_queries:
            try:
                # Get answer with citations
                retrieval_results = self.retriever.retrieve(query, k=3)
                answer = self.generator.generate(query, retrieval_results)
                
                # Analyze alignment
                alignment_analysis = self._analyze_citation_alignment(query, answer, retrieval_results)
                alignment_results.append(alignment_analysis)
                
                print(f"    Query: '{query[:30]}...' - Alignment: {alignment_analysis['alignment_score']:.2f}")
                
            except Exception as e:
                alignment_results.append({
                    'query': query,
                    'success': False,
                    'issues': [f"Citation alignment test failed: {str(e)}"]
                })
        
        # Calculate alignment score
        successful_alignment = [r for r in alignment_results if r.get('success', False)]
        alignment_score = sum(r['alignment_score'] for r in successful_alignment) / len(successful_alignment) if successful_alignment else 0
        
        issues_found = []
        for result in alignment_results:
            if not result.get('success', False):
                issues_found.extend(result.get('issues', []))
            elif result.get('alignment_score', 0) < 0.8:
                issues_found.append(f"Poor citation alignment for query: {result.get('query', 'unknown')}")
        
        data_captured = {
            "alignment_queries": alignment_queries,
            "total_queries": len(alignment_queries),
            "successful_alignment": len(successful_alignment),
            "alignment_results": alignment_results
        }
        
        analysis_results = {
            "alignment_score": alignment_score,
            "citation_alignment_good": alignment_score > 0.8,
            "summary": f"Citation-answer alignment: {alignment_score:.1%}"
        }
        
        return (
            data_captured,
            analysis_results,
            list(set(issues_found)),
            self._generate_alignment_recommendations(alignment_results)
        )
    
    def _test_attribution_chain_completeness(self) -> tuple:
        """Test end-to-end attribution chain completeness."""
        print("  Testing attribution chain completeness...")
        
        # Test complete attribution chain
        completeness_queries = [
            "What is RISC-V architecture?",
            "Explain ARM Cortex-A processors"
        ]
        
        completeness_results = []
        
        for query in completeness_queries:
            try:
                # Execute complete pipeline
                answer = self.orchestrator.process_query(query)
                
                # Analyze completeness
                completeness_analysis = self._analyze_attribution_completeness(query, answer)
                completeness_results.append(completeness_analysis)
                
                print(f"    Query: '{query[:30]}...' - Completeness: {completeness_analysis['completeness_score']:.2f}")
                
            except Exception as e:
                completeness_results.append({
                    'query': query,
                    'success': False,
                    'issues': [f"Attribution chain test failed: {str(e)}"]
                })
        
        # Calculate completeness score
        successful_completeness = [r for r in completeness_results if r.get('success', False)]
        completeness_score = sum(r['completeness_score'] for r in successful_completeness) / len(successful_completeness) if successful_completeness else 0
        
        issues_found = []
        for result in completeness_results:
            if not result.get('success', False):
                issues_found.extend(result.get('issues', []))
            elif result.get('completeness_score', 0) < 0.8:
                issues_found.append(f"Incomplete attribution chain for query: {result.get('query', 'unknown')}")
        
        data_captured = {
            "completeness_queries": completeness_queries,
            "total_queries": len(completeness_queries),
            "successful_completeness": len(successful_completeness),
            "completeness_results": completeness_results
        }
        
        analysis_results = {
            "completeness_score": completeness_score,
            "attribution_completeness_good": completeness_score > 0.8,
            "summary": f"Attribution chain completeness: {completeness_score:.1%}"
        }
        
        return (
            data_captured,
            analysis_results,
            list(set(issues_found)),
            self._generate_completeness_recommendations(completeness_results)
        )
    
    def _analyze_citation_generation(self, query: str, retrieval_results: List[RetrievalResult], answer: Answer) -> Dict[str, Any]:
        """Analyze citation generation quality."""
        issues = []
        
        # Check if answer has citations
        citations = getattr(answer, 'sources', [])
        citations_count = len(citations)
        
        if citations_count == 0:
            issues.append("No citations generated")
            return {
                'query': query,
                'success': False,
                'citations_count': 0,
                'issues': issues
            }
        
        # Check citation quality
        citation_quality = 0
        for citation in citations:
            if hasattr(citation, 'source') and citation.source != 'unknown':
                citation_quality += 0.5
            if hasattr(citation, 'page') and citation.page != 'unknown':
                citation_quality += 0.5
        
        citation_quality = citation_quality / len(citations) if citations else 0
        
        if citation_quality < 0.8:
            issues.append(f"Poor citation quality: {citation_quality:.2f}")
        
        return {
            'query': query,
            'success': True,
            'citations_count': citations_count,
            'citation_quality': citation_quality,
            'issues': issues
        }
    
    def _analyze_metadata_preservation(self, original: Dict, retrieved: Dict, answer: Answer) -> Dict[str, Any]:
        """Analyze metadata preservation through pipeline."""
        issues = []
        
        # Check key metadata fields
        key_fields = ['source', 'page', 'section', 'author']
        preserved_fields = 0
        
        for field in key_fields:
            if field in original and field in retrieved:
                if original[field] == retrieved[field]:
                    preserved_fields += 1
                else:
                    issues.append(f"Field '{field}' changed: {original[field]} -> {retrieved[field]}")
            elif field in original:
                issues.append(f"Field '{field}' lost during retrieval")
        
        preservation_score = preserved_fields / len(key_fields) if key_fields else 0
        
        return {
            'success': True,
            'preservation_score': preservation_score,
            'preserved_fields': preserved_fields,
            'total_fields': len(key_fields),
            'issues': issues
        }
    
    def _analyze_source_tracking(self, original_doc: Document, retrieval_results: List[RetrievalResult]) -> Dict[str, Any]:
        """Analyze source tracking integrity."""
        issues = []
        
        if not retrieval_results:
            issues.append("No retrieval results to analyze")
            return {
                'success': False,
                'tracking_score': 0,
                'issues': issues
            }
        
        # Check if original document is in retrieval results
        original_source = original_doc.metadata.get('source', '')
        found_in_results = False
        
        for result in retrieval_results:
            result_source = result.document.metadata.get('source', '')
            if original_source == result_source:
                found_in_results = True
                break
        
        tracking_score = 1.0 if found_in_results else 0.0
        
        if not found_in_results:
            issues.append(f"Original source '{original_source}' not found in retrieval results")
        
        return {
            'source': original_source,
            'success': True,
            'tracking_score': tracking_score,
            'found_in_results': found_in_results,
            'issues': issues
        }
    
    def _analyze_page_number_extraction(self, document: Document) -> Dict[str, Any]:
        """Analyze page number extraction accuracy."""
        issues = []
        
        expected_page = document.metadata.get('page', 'unknown')
        extracted_page = document.metadata.get('page', 'unknown')
        
        # Check if page number is valid
        page_accuracy = 1.0 if extracted_page != 'unknown' and extracted_page is not None else 0.0
        
        if extracted_page == 'unknown':
            issues.append("Page number is 'unknown'")
        elif extracted_page is None:
            issues.append("Page number is None")
        
        return {
            'source': document.metadata.get('source', 'unknown'),
            'success': True,
            'expected_page': expected_page,
            'extracted_page': extracted_page,
            'page_accuracy': page_accuracy,
            'issues': issues
        }
    
    def _analyze_citation_alignment(self, query: str, answer: Answer, retrieval_results: List[RetrievalResult]) -> Dict[str, Any]:
        """Analyze citation-answer alignment."""
        issues = []
        
        # Check if citations in answer match retrieval results
        answer_citations = getattr(answer, 'sources', [])
        retrieval_sources = [result.document.metadata.get('source', '') for result in retrieval_results]
        
        aligned_citations = 0
        for citation in answer_citations:
            citation_source = getattr(citation, 'source', 'unknown')
            if citation_source in retrieval_sources:
                aligned_citations += 1
            else:
                issues.append(f"Citation source '{citation_source}' not in retrieval results")
        
        alignment_score = aligned_citations / len(answer_citations) if answer_citations else 0
        
        if alignment_score < 0.8:
            issues.append(f"Poor citation alignment: {alignment_score:.2f}")
        
        return {
            'query': query,
            'success': True,
            'alignment_score': alignment_score,
            'aligned_citations': aligned_citations,
            'total_citations': len(answer_citations),
            'issues': issues
        }
    
    def _analyze_attribution_completeness(self, query: str, answer: Answer) -> Dict[str, Any]:
        """Analyze attribution chain completeness."""
        issues = []
        
        # Check if answer has complete attribution
        has_citations = hasattr(answer, 'sources') and len(answer.sources) > 0
        has_confidence = hasattr(answer, 'confidence') and answer.confidence is not None
        has_content = hasattr(answer, 'content') and len(answer.content) > 0
        
        completeness_factors = [has_citations, has_confidence, has_content]
        completeness_score = sum(completeness_factors) / len(completeness_factors)
        
        if not has_citations:
            issues.append("Answer missing citations")
        if not has_confidence:
            issues.append("Answer missing confidence score")
        if not has_content:
            issues.append("Answer missing content")
        
        return {
            'query': query,
            'success': True,
            'completeness_score': completeness_score,
            'has_citations': has_citations,
            'has_confidence': has_confidence,
            'has_content': has_content,
            'issues': issues
        }
    
    def _generate_citation_recommendations(self, results: List[Dict]) -> List[str]:
        """Generate recommendations for citation generation."""
        recommendations = []
        
        if any(not result.get('success', False) for result in results):
            recommendations.append("Fix citation generation failures")
        
        if any(result.get('citations_count', 0) == 0 for result in results):
            recommendations.append("Ensure all answers include proper citations")
        
        return recommendations
    
    def _generate_preservation_recommendations(self, results: List[Dict]) -> List[str]:
        """Generate recommendations for metadata preservation."""
        recommendations = []
        
        if any(not result.get('success', False) for result in results):
            recommendations.append("Fix metadata preservation failures")
        
        if any(result.get('preservation_score', 0) < 0.8 for result in results):
            recommendations.append("Improve metadata preservation through pipeline")
        
        return recommendations
    
    def _generate_tracking_recommendations(self, results: List[Dict]) -> List[str]:
        """Generate recommendations for source tracking."""
        recommendations = []
        
        if any(not result.get('success', False) for result in results):
            recommendations.append("Fix source tracking failures")
        
        if any(result.get('tracking_score', 0) < 0.8 for result in results):
            recommendations.append("Improve source tracking integrity")
        
        return recommendations
    
    def _generate_page_recommendations(self, results: List[Dict]) -> List[str]:
        """Generate recommendations for page number extraction."""
        recommendations = []
        
        if any(not result.get('success', False) for result in results):
            recommendations.append("Fix page number extraction failures")
        
        if any(result.get('page_accuracy', 0) < 1.0 for result in results):
            recommendations.append("Improve page number extraction accuracy")
        
        return recommendations
    
    def _generate_alignment_recommendations(self, results: List[Dict]) -> List[str]:
        """Generate recommendations for citation alignment."""
        recommendations = []
        
        if any(not result.get('success', False) for result in results):
            recommendations.append("Fix citation alignment failures")
        
        if any(result.get('alignment_score', 0) < 0.8 for result in results):
            recommendations.append("Improve citation-answer alignment")
        
        return recommendations
    
    def _generate_completeness_recommendations(self, results: List[Dict]) -> List[str]:
        """Generate recommendations for attribution completeness."""
        recommendations = []
        
        if any(not result.get('success', False) for result in results):
            recommendations.append("Fix attribution chain completeness failures")
        
        if any(result.get('completeness_score', 0) < 0.8 for result in results):
            recommendations.append("Ensure complete attribution chain")
        
        return recommendations
    
    def _aggregate_attribution_analysis(self, results: List[DiagnosticResult]) -> SourceAttributionAnalysis:
        """Aggregate all attribution test results."""
        total_documents = 0
        total_queries = 0
        citation_success_rate = 0
        metadata_preservation_rate = 0
        source_tracking_integrity = 0
        page_number_accuracy = 0
        citation_alignment = 0
        chain_completeness = 0
        
        all_issues = []
        all_recommendations = []
        
        for result in results:
            all_issues.extend(result.issues_found)
            all_recommendations.extend(result.recommendations)
            
            # Extract specific metrics
            if result.test_name == "Citation_Generation_Process":
                total_queries += result.data_captured.get('total_queries', 0)
                citation_success_rate = result.analysis_results.get('success_rate', 0)
            
            elif result.test_name == "Metadata_Preservation_Chain":
                total_documents += result.data_captured.get('total_documents', 0)
                metadata_preservation_rate = result.analysis_results.get('preservation_rate', 0)
            
            elif result.test_name == "Source_Tracking_Integrity":
                source_tracking_integrity = result.analysis_results.get('tracking_integrity', 0)
            
            elif result.test_name == "Page_Number_Extraction":
                page_number_accuracy = result.analysis_results.get('page_accuracy', 0)
            
            elif result.test_name == "Citation_Answer_Alignment":
                citation_alignment = result.analysis_results.get('alignment_score', 0)
            
            elif result.test_name == "Attribution_Chain_Completeness":
                chain_completeness = result.analysis_results.get('completeness_score', 0)
        
        return SourceAttributionAnalysis(
            total_documents_processed=total_documents,
            total_queries_tested=total_queries,
            citation_generation_success_rate=citation_success_rate,
            metadata_preservation_rate=metadata_preservation_rate,
            source_tracking_integrity=source_tracking_integrity,
            page_number_accuracy=page_number_accuracy,
            citation_answer_alignment=citation_alignment,
            attribution_chain_completeness=chain_completeness,
            issues_found=list(set(all_issues)),
            recommendations=list(set(all_recommendations))
        )


def main():
    """Run source attribution forensic tests."""
    forensics = SourceAttributionForensics()
    analysis = forensics.run_all_source_attribution_tests()
    
    # Save results
    results_file = project_root / f"source_attribution_forensics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(results_file, 'w') as f:
        json.dump(asdict(analysis), f, indent=2)
    
    print(f"\n💾 Results saved to: {results_file}")
    return analysis


if __name__ == "__main__":
    main()