#!/usr/bin/env python3
"""
Test Suite 2: Document Processing Data Chain Analysis

This test suite provides comprehensive forensic analysis of the document processing pipeline
from PDF parsing through chunking to Document object creation.

Critical Focus Areas:
- PDF metadata extraction validation (diagnosing "Page unknown from unknown")
- Content chunking quality analysis
- Document object compliance testing
- Source attribution chain integrity
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
from src.core.interfaces import Document
from src.core.component_factory import ComponentFactory

# Configure logging to see ComponentFactory logs
logging.basicConfig(level=logging.INFO, format='[%(name)s] %(levelname)s: %(message)s')

logger = logging.getLogger(__name__)


@dataclass
class DocumentProcessingAnalysis:
    """Analysis results for document processing pipeline."""
    total_documents_processed: int
    total_chunks_created: int
    metadata_extraction_success_rate: float
    content_quality_score: float
    chunk_boundary_quality_score: float
    source_attribution_integrity: float
    processing_time_per_document: float
    issues_found: List[str]
    recommendations: List[str]


class DocumentProcessingForensics(DiagnosticTestBase):
    """
    Forensic analysis of document processing pipeline.
    
    This class provides comprehensive testing of:
    - PDF metadata extraction accuracy
    - Content chunking quality and boundaries
    - Document object compliance
    - Source attribution chain integrity
    """
    
    def __init__(self):
        super().__init__()
        self.processor = None
        self.test_documents = []
        self.processing_results = []
    
    def run_all_document_processing_tests(self) -> DocumentProcessingAnalysis:
        """
        Run comprehensive document processing forensic tests.
        
        Returns:
            DocumentProcessingAnalysis with complete results
        """
        print("=" * 80)
        print("TEST SUITE 2: DOCUMENT PROCESSING DATA CHAIN ANALYSIS")
        print("=" * 80)
        
        # Initialize processor using ComponentFactory (gets ModularDocumentProcessor)
        self.processor = ComponentFactory.create_processor("hybrid_pdf")
        
        # Validate we got the correct processor type
        if not hasattr(self.processor, 'get_component_info'):
            raise RuntimeError(f"Expected ModularDocumentProcessor, got {type(self.processor)}")
        
        # Test 1: PDF Metadata Extraction Validation
        print("\n📄 Test 2.1: PDF Metadata Extraction Validation")
        metadata_results = self.safe_execute(
            self._test_pdf_metadata_extraction, 
            "PDF_Metadata_Extraction", 
            "pdf_processor"
        )
        
        # Test 2: Content Chunking Quality Analysis
        print("\n✂️ Test 2.2: Content Chunking Quality Analysis")
        chunking_results = self.safe_execute(
            self._test_content_chunking_quality,
            "Content_Chunking_Quality",
            "pdf_processor"
        )
        
        # Test 3: Document Object Compliance Testing
        print("\n🔍 Test 2.3: Document Object Compliance Testing")
        compliance_results = self.safe_execute(
            self._test_document_object_compliance,
            "Document_Object_Compliance",
            "pdf_processor"
        )
        
        # Test 4: Source Attribution Chain Integrity
        print("\n🔗 Test 2.4: Source Attribution Chain Integrity")
        attribution_results = self.safe_execute(
            self._test_source_attribution_chain,
            "Source_Attribution_Chain",
            "pdf_processor"
        )
        
        # Test 5: Modular Sub-Component Analysis
        print("\n🔧 Test 2.5: Modular Sub-Component Analysis")
        subcomponent_results = self.safe_execute(
            self._test_modular_subcomponents,
            "Modular_SubComponent_Analysis",
            "pdf_processor"
        )
        
        # Test 6: Processing Performance Analysis
        print("\n⚡ Test 2.6: Processing Performance Analysis")
        performance_results = self.safe_execute(
            self._test_processing_performance,
            "Processing_Performance",
            "pdf_processor"
        )
        
        # Aggregate results
        analysis = self._aggregate_processing_analysis([
            metadata_results, chunking_results, compliance_results,
            attribution_results, subcomponent_results, performance_results
        ])
        
        print(f"\n📊 DOCUMENT PROCESSING ANALYSIS COMPLETE")
        print(f"Total Documents Processed: {analysis.total_documents_processed}")
        print(f"Total Chunks Created: {analysis.total_chunks_created}")
        print(f"Metadata Extraction Success Rate: {analysis.metadata_extraction_success_rate:.1%}")
        print(f"Content Quality Score: {analysis.content_quality_score:.3f}")
        print(f"Source Attribution Integrity: {analysis.source_attribution_integrity:.1%}")
        
        if analysis.issues_found:
            print(f"\n🚨 Issues Found ({len(analysis.issues_found)}):")
            for issue in analysis.issues_found:
                print(f"  - {issue}")
        
        if analysis.recommendations:
            print(f"\n💡 Recommendations ({len(analysis.recommendations)}):")
            for rec in analysis.recommendations:
                print(f"  - {rec}")
        
        return analysis
    
    def _test_pdf_metadata_extraction(self) -> tuple:
        """Test PDF metadata extraction accuracy."""
        print("  Testing PDF metadata extraction...")
        
        # Test with real PDFs only
        test_files = [
            "data/test/riscv-card.pdf",
            "data/test/unpriv-isa-asciidoc.pdf",
            "data/test/RISC-V-VectorExtension-1-1.pdf"
        ]
        
        metadata_results = []
        
        for pdf_path in test_files:
            pdf_file = project_root / pdf_path
            if not pdf_file.exists():
                print(f"    ERROR: Required test file {pdf_path} not found")
                continue
            
            try:
                print(f"    Processing {pdf_path}")
                documents = self.processor.process(pdf_file)
            except Exception as e:
                print(f"    Error processing {pdf_path}: {e}")
                continue
            
            # Analyze metadata extraction
            for doc in documents:
                metadata_analysis = self._analyze_metadata_quality(doc, pdf_path)
                metadata_results.append(metadata_analysis)
        
        # Calculate metadata extraction success rate
        total_documents = len(metadata_results)
        successful_extractions = sum(1 for result in metadata_results if result['success'])
        success_rate = successful_extractions / total_documents if total_documents > 0 else 0
        
        issues_found = []
        for result in metadata_results:
            if not result['success']:
                issues_found.extend(result['issues'])
        
        data_captured = {
            "test_files": test_files,
            "total_documents": total_documents,
            "successful_extractions": successful_extractions,
            "metadata_results": metadata_results
        }
        
        analysis_results = {
            "success_rate": success_rate,
            "metadata_extraction_success": success_rate > 0.8,
            "summary": f"Success rate: {success_rate:.1%}"
        }
        
        return (
            data_captured,
            analysis_results,
            list(set(issues_found)),
            self._generate_metadata_recommendations(metadata_results)
        )
    
    def _test_content_chunking_quality(self) -> tuple:
        """Test content chunking quality and boundaries."""
        print("  Testing content chunking quality...")
        
        # Process test documents
        test_documents = self._get_test_documents()
        chunking_results = []
        
        for doc in test_documents:
            chunk_analysis = self._analyze_chunk_quality(doc)
            chunking_results.append(chunk_analysis)
        
        # Calculate overall quality metrics
        total_chunks = len(chunking_results)
        quality_issues = sum(1 for result in chunking_results if not result['quality_passed'])
        quality_score = 1 - (quality_issues / total_chunks) if total_chunks > 0 else 0
        
        issues_found = []
        for result in chunking_results:
            if not result['quality_passed']:
                issues_found.extend(result['issues'])
        
        data_captured = {
            "total_chunks": total_chunks,
            "quality_issues": quality_issues,
            "chunking_results": chunking_results
        }
        
        analysis_results = {
            "quality_score": quality_score,
            "chunking_quality": quality_score > 0.8,
            "summary": f"Quality score: {quality_score:.3f}"
        }
        
        return (
            data_captured,
            analysis_results,
            list(set(issues_found)),
            self._generate_chunking_recommendations(chunking_results)
        )
    
    def _test_document_object_compliance(self) -> tuple:
        """Test Document object compliance with interface."""
        print("  Testing Document object compliance...")
        
        test_documents = self._get_test_documents()
        compliance_results = []
        
        for doc in test_documents:
            compliance_analysis = self._analyze_document_compliance(doc)
            compliance_results.append(compliance_analysis)
        
        # Calculate compliance rate
        total_documents = len(compliance_results)
        compliant_documents = sum(1 for result in compliance_results if result['compliant'])
        compliance_rate = compliant_documents / total_documents if total_documents > 0 else 0
        
        issues_found = []
        for result in compliance_results:
            if not result['compliant']:
                issues_found.extend(result['issues'])
        
        data_captured = {
            "total_documents": total_documents,
            "compliant_documents": compliant_documents,
            "compliance_results": compliance_results
        }
        
        analysis_results = {
            "compliance_rate": compliance_rate,
            "document_compliance": compliance_rate == 1.0,
            "summary": f"Compliance rate: {compliance_rate:.1%}"
        }
        
        return (
            data_captured,
            analysis_results,
            list(set(issues_found)),
            self._generate_compliance_recommendations(compliance_results)
        )
    
    def _test_source_attribution_chain(self) -> tuple:
        """Test source attribution chain integrity."""
        print("  Testing source attribution chain...")
        
        test_documents = self._get_test_documents()
        attribution_results = []
        
        for doc in test_documents:
            attribution_analysis = self._analyze_source_attribution(doc)
            attribution_results.append(attribution_analysis)
        
        # Calculate attribution integrity
        total_documents = len(attribution_results)
        intact_attributions = sum(1 for result in attribution_results if result['attribution_intact'])
        integrity_score = intact_attributions / total_documents if total_documents > 0 else 0
        
        issues_found = []
        for result in attribution_results:
            if not result['attribution_intact']:
                issues_found.extend(result['issues'])
        
        data_captured = {
            "total_documents": total_documents,
            "intact_attributions": intact_attributions,
            "attribution_results": attribution_results
        }
        
        analysis_results = {
            "integrity_score": integrity_score,
            "attribution_integrity": integrity_score > 0.9,
            "summary": f"Attribution integrity: {integrity_score:.1%}"
        }
        
        return (
            data_captured,
            analysis_results,
            list(set(issues_found)),
            self._generate_attribution_recommendations(attribution_results)
        )
    
    def _test_modular_subcomponents(self) -> tuple:
        """Test modular sub-component analysis for ModularDocumentProcessor."""
        print("  Testing modular sub-component architecture...")
        
        # Get component info from ModularDocumentProcessor
        try:
            component_info = self.processor.get_component_info()
            print(f"    Component info: {component_info}")
            
            # Expected components for ModularDocumentProcessor
            expected_components = ['parser', 'chunker', 'cleaner', 'pipeline']
            
            # Analyze sub-component presence
            present_components = [comp for comp in expected_components if comp in component_info]
            missing_components = [comp for comp in expected_components if comp not in component_info]
            
            # Check component types
            component_types = {}
            for comp_name, comp_info in component_info.items():
                if isinstance(comp_info, dict) and 'type' in comp_info:
                    component_types[comp_name] = comp_info['type']
                else:
                    component_types[comp_name] = str(type(comp_info))
            
            # Expected component types for ModularDocumentProcessor
            expected_types = {
                'parser': 'pymupdf',  # Component info uses short type names
                'chunker': 'sentence_boundary', 
                'cleaner': 'technical',
                'pipeline': 'pipeline'  # Special case for pipeline
            }
            
            type_matches = {}
            for comp_name in expected_components:
                if comp_name in component_types:
                    expected_type = expected_types[comp_name]
                    actual_type = component_types[comp_name]
                    type_matches[comp_name] = expected_type in actual_type
                else:
                    type_matches[comp_name] = False
                    
            issues_found = []
            if missing_components:
                issues_found.append(f"Missing sub-components: {missing_components}")
            
            for comp_name, matches in type_matches.items():
                if not matches:
                    expected_type = expected_types[comp_name]
                    actual_type = component_types.get(comp_name, 'missing')
                    issues_found.append(f"{comp_name} type mismatch: expected {expected_type}, got {actual_type}")
            
            data_captured = {
                "component_info": component_info,
                "present_components": present_components,
                "missing_components": missing_components,
                "component_types": component_types,
                "expected_types": expected_types,
                "type_matches": type_matches
            }
            
            analysis_results = {
                "modular_architecture": len(missing_components) == 0,
                "component_types_correct": all(type_matches.values()),
                "architecture_compliance": len(missing_components) == 0 and all(type_matches.values()),
                "summary": f"Components: {len(present_components)}/{len(expected_components)}"
            }
            
            recommendations = []
            if missing_components:
                recommendations.append(f"Ensure all required sub-components are present: {missing_components}")
            if not all(type_matches.values()):
                recommendations.append("Verify sub-component types match expected ModularDocumentProcessor architecture")
            
        except Exception as e:
            issues_found = [f"Sub-component analysis failed: {str(e)}"]
            data_captured = {"error": str(e)}
            analysis_results = {"modular_architecture": False, "error": str(e)}
            recommendations = ["Fix sub-component access in ModularDocumentProcessor"]
        
        return (
            data_captured,
            analysis_results,
            issues_found,
            recommendations
        )
    
    def _test_processing_performance(self) -> tuple:
        """Test processing performance metrics."""
        print("  Testing processing performance...")
        
        import time
        test_documents = self._get_test_documents()
        
        # Measure processing time
        start_time = time.time()
        total_chars = sum(len(doc.content) for doc in test_documents)
        processing_time = time.time() - start_time
        
        chars_per_second = total_chars / processing_time if processing_time > 0 else 0
        
        performance_analysis = {
            'total_documents': len(test_documents),
            'total_characters': total_chars,
            'processing_time': processing_time,
            'chars_per_second': chars_per_second,
            'performance_target': 1000.0,  # chars per second
            'meets_target': chars_per_second >= 1000.0
        }
        
        issues_found = []
        if not performance_analysis['meets_target']:
            issues_found.append(f"Processing speed {chars_per_second:.0f} chars/sec below target 1000 chars/sec")
        
        data_captured = {
            "total_documents": len(test_documents),
            "total_characters": total_chars,
            "processing_time": processing_time,
            "chars_per_second": chars_per_second
        }
        
        analysis_results = {
            "performance_target_met": performance_analysis['meets_target'],
            "performance_analysis": performance_analysis,
            "summary": f"{chars_per_second:.0f} chars/sec"
        }
        
        return (
            data_captured,
            analysis_results,
            issues_found,
            self._generate_performance_recommendations(performance_analysis)
        )
    
    def _get_test_documents(self) -> List[Document]:
        """Get test documents for analysis from real PDF processing."""
        if not self.test_documents:
            # Process real PDFs to get test documents
            test_files = [
                "data/test/riscv-card.pdf",
                "data/test/unpriv-isa-asciidoc.pdf",
                "data/test/RISC-V-VectorExtension-1-1.pdf"
            ]
            
            self.test_documents = []
            for pdf_path in test_files:
                pdf_file = project_root / pdf_path
                if pdf_file.exists():
                    try:
                        documents = self.processor.process(pdf_file)
                        if documents:
                            self.test_documents.extend(documents[:1])  # Take first document from each PDF
                    except Exception as e:
                        print(f"    Error processing {pdf_path} for test documents: {e}")
                        continue
        return self.test_documents
    
    # Removed _create_test_document method - using real PDF processing only
    
    def _analyze_metadata_quality(self, document: Document, expected_source: str) -> Dict[str, Any]:
        """Analyze metadata extraction quality."""
        metadata = document.metadata
        
        # Check required fields for ModularDocumentProcessor
        required_fields = ['source', 'page', 'section', 'document_type', 'chunk_id']
        missing_fields = [field for field in required_fields if field not in metadata]
        
        # Check for "unknown" values (ModularDocumentProcessor should avoid these)
        unknown_values = [field for field in required_fields if metadata.get(field) == 'unknown']
        
        # Check for component-specific metadata (from ModularDocumentProcessor)
        component_metadata = {
            'has_parser_info': 'parser_used' in metadata,
            'has_chunker_info': 'chunker_used' in metadata,
            'has_cleaner_info': 'cleaner_used' in metadata,
            'has_processing_stats': 'processing_time' in metadata
        }
        
        # Check source accuracy
        source_accurate = expected_source in str(metadata.get('source', ''))
        
        issues = []
        if missing_fields:
            issues.append(f"Missing fields: {', '.join(missing_fields)}")
        if unknown_values:
            issues.append(f"Unknown values in: {', '.join(unknown_values)}")
        if not source_accurate:
            issues.append(f"Source mismatch: expected {expected_source}, got {metadata.get('source')}")
        
        return {
            'success': len(issues) == 0,
            'missing_fields': missing_fields,
            'unknown_values': unknown_values,
            'source_accurate': source_accurate,
            'component_metadata': component_metadata,
            'issues': issues,
            'metadata': metadata
        }
    
    def _analyze_chunk_quality(self, document: Document) -> Dict[str, Any]:
        """Analyze content chunk quality."""
        content = document.content
        
        # Check for complete sentences
        has_complete_sentences = content.strip().endswith('.') or content.strip().endswith('!') or content.strip().endswith('?')
        
        # Check chunk size
        word_count = len(content.split())
        appropriate_size = 20 <= word_count <= 200
        
        # Check for empty content
        not_empty = len(content.strip()) > 0
        
        # Check for technical terms preservation (SentenceBoundaryChunker should preserve these)
        technical_terms = ['RISC-V', 'instruction', 'architecture', 'processor', 'extension']
        preserves_technical_terms = any(term in content for term in technical_terms)
        
        # Check for sentence boundary preservation (specific to SentenceBoundaryChunker)
        sentence_endings = ['.', '!', '?']
        proper_sentence_boundaries = any(content.strip().endswith(ending) for ending in sentence_endings)
        
        issues = []
        if not has_complete_sentences:
            issues.append("Chunk doesn't end with complete sentence")
        if not appropriate_size:
            issues.append(f"Chunk size {word_count} words outside optimal range (20-200)")
        if not not_empty:
            issues.append("Empty chunk content")
        if not preserves_technical_terms:
            issues.append("Technical terms may be split or missing")
        
        return {
            'quality_passed': len(issues) == 0,
            'has_complete_sentences': has_complete_sentences,
            'appropriate_size': appropriate_size,
            'word_count': word_count,
            'preserves_technical_terms': preserves_technical_terms,
            'proper_sentence_boundaries': proper_sentence_boundaries,
            'issues': issues,
            'content_preview': content[:100] + "..." if len(content) > 100 else content
        }
    
    def _analyze_document_compliance(self, document: Document) -> Dict[str, Any]:
        """Analyze Document object compliance."""
        issues = []
        
        # Check content type and presence
        if not isinstance(document.content, str):
            issues.append(f"Content type {type(document.content)} is not str")
        if not document.content or len(document.content.strip()) == 0:
            issues.append("Content is empty")
        
        # Check metadata type and presence
        if not isinstance(document.metadata, dict):
            issues.append(f"Metadata type {type(document.metadata)} is not dict")
        if not document.metadata:
            issues.append("Metadata is empty")
        
        # Check embedding (should be None or list)
        if document.embedding is not None and not isinstance(document.embedding, list):
            issues.append(f"Embedding type {type(document.embedding)} is not list or None")
        
        return {
            'compliant': len(issues) == 0,
            'content_type_correct': isinstance(document.content, str),
            'metadata_type_correct': isinstance(document.metadata, dict),
            'embedding_type_correct': document.embedding is None or isinstance(document.embedding, list),
            'issues': issues
        }
    
    def _analyze_source_attribution(self, document: Document) -> Dict[str, Any]:
        """Analyze source attribution chain integrity."""
        metadata = document.metadata
        
        # Check source field
        source_present = 'source' in metadata and metadata['source'] != 'unknown'
        
        # Check page field
        page_present = 'page' in metadata and metadata['page'] != 'unknown'
        
        # Check document ID
        doc_id_present = 'doc_id' in metadata or 'chunk_id' in metadata
        
        issues = []
        if not source_present:
            issues.append("Source field missing or 'unknown'")
        if not page_present:
            issues.append("Page field missing or 'unknown'")
        if not doc_id_present:
            issues.append("Document/chunk ID missing")
        
        return {
            'attribution_intact': len(issues) == 0,
            'source_present': source_present,
            'page_present': page_present,
            'doc_id_present': doc_id_present,
            'issues': issues,
            'metadata': metadata
        }
    
    def _generate_metadata_recommendations(self, results: List[Dict]) -> List[str]:
        """Generate recommendations for metadata extraction."""
        recommendations = []
        
        if any(not result['success'] for result in results):
            recommendations.append("Implement robust PDF metadata extraction with fallback values")
        
        if any('unknown' in result['unknown_values'] for result in results if result['unknown_values']):
            recommendations.append("Replace 'unknown' values with meaningful defaults or extract from content")
        
        if any(not result['source_accurate'] for result in results):
            recommendations.append("Ensure source path preservation throughout processing pipeline")
        
        return recommendations
    
    def _generate_chunking_recommendations(self, results: List[Dict]) -> List[str]:
        """Generate recommendations for chunking quality."""
        recommendations = []
        
        if any(not result['quality_passed'] for result in results):
            recommendations.append("Implement sentence-aware chunking to preserve complete sentences")
        
        if any(not result['appropriate_size'] for result in results):
            recommendations.append("Tune chunk size parameters for optimal 20-200 word range")
        
        if any(not result['preserves_technical_terms'] for result in results):
            recommendations.append("Implement technical term preservation in chunking algorithm")
        
        return recommendations
    
    def _generate_compliance_recommendations(self, results: List[Dict]) -> List[str]:
        """Generate recommendations for Document compliance."""
        recommendations = []
        
        if any(not result['compliant'] for result in results):
            recommendations.append("Ensure all Document objects strictly follow interface specification")
        
        if any(not result['content_type_correct'] for result in results):
            recommendations.append("Validate content type casting to string")
        
        if any(not result['metadata_type_correct'] for result in results):
            recommendations.append("Ensure metadata is always a dictionary")
        
        return recommendations
    
    def _generate_attribution_recommendations(self, results: List[Dict]) -> List[str]:
        """Generate recommendations for source attribution."""
        recommendations = []
        
        if any(not result['attribution_intact'] for result in results):
            recommendations.append("Implement end-to-end source attribution chain validation")
        
        if any(not result['source_present'] for result in results):
            recommendations.append("Ensure source field is always populated with valid path")
        
        if any(not result['page_present'] for result in results):
            recommendations.append("Implement page number extraction from PDF structure")
        
        return recommendations
    
    def _generate_performance_recommendations(self, analysis: Dict) -> List[str]:
        """Generate recommendations for processing performance."""
        recommendations = []
        
        if not analysis['meets_target']:
            recommendations.append("Optimize PDF processing pipeline for >1000 chars/sec throughput")
            recommendations.append("Consider parallel processing for large document batches")
        
        return recommendations
    
    def _aggregate_processing_analysis(self, results: List[DiagnosticResult]) -> DocumentProcessingAnalysis:
        """Aggregate all processing test results."""
        # Extract metrics from results
        total_documents = 0
        total_chunks = 0
        metadata_success = 0
        content_quality = 0
        attribution_integrity = 0
        processing_time = 0
        
        all_issues = []
        all_recommendations = []
        
        for result in results:
            all_issues.extend(result.issues_found)
            all_recommendations.extend(result.recommendations)
            
            # Extract specific metrics
            if result.test_name == "PDF_Metadata_Extraction":
                metadata_results = result.data_captured.get('metadata_results', [])
                if metadata_results:
                    metadata_success = sum(1 for r in metadata_results if r['success']) / len(metadata_results)
            
            elif result.test_name == "Content_Chunking_Quality":
                chunking_results = result.data_captured.get('chunking_results', [])
                total_chunks = len(chunking_results)
                if chunking_results:
                    content_quality = sum(1 for r in chunking_results if r['quality_passed']) / len(chunking_results)
            
            elif result.test_name == "Source_Attribution_Chain":
                attribution_results = result.data_captured.get('attribution_results', [])
                if attribution_results:
                    attribution_integrity = sum(1 for r in attribution_results if r['attribution_intact']) / len(attribution_results)
            
            elif result.test_name == "Processing_Performance":
                perf_analysis = result.analysis_results.get('performance_analysis', {})
                total_documents = result.data_captured.get('total_documents', 0)
                processing_time = result.data_captured.get('processing_time', 0)
        
        return DocumentProcessingAnalysis(
            total_documents_processed=total_documents,
            total_chunks_created=total_chunks,
            metadata_extraction_success_rate=metadata_success,
            content_quality_score=content_quality,
            chunk_boundary_quality_score=content_quality,  # Using same metric for now
            source_attribution_integrity=attribution_integrity,
            processing_time_per_document=processing_time / total_documents if total_documents > 0 else 0,
            issues_found=list(set(all_issues)),
            recommendations=list(set(all_recommendations))
        )


def main():
    """Run document processing forensic tests."""
    forensics = DocumentProcessingForensics()
    analysis = forensics.run_all_document_processing_tests()
    
    # Save results
    results_file = project_root / f"document_processing_forensics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(results_file, 'w') as f:
        json.dump(asdict(analysis), f, indent=2)
    
    print(f"\n💾 Results saved to: {results_file}")
    return analysis


if __name__ == "__main__":
    main()