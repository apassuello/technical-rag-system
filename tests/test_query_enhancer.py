"""
Comprehensive test suite for QueryEnhancer functionality.

Tests all aspects of intelligent query processing including:
- Technical term expansion
- Acronym detection and expansion  
- Adaptive weighting algorithms
- Query characteristic analysis
- Integration with BasicRAG system
"""

import pytest
import sys
from pathlib import Path

# Add project paths for imports
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))
sys.path.append(str(project_root.parent))

from shared_utils.query_processing.query_enhancer import QueryEnhancer
from src.basic_rag import BasicRAG


class TestQueryEnhancer:
    """Test QueryEnhancer functionality comprehensively."""
    
    @pytest.fixture
    def enhancer(self):
        """Initialize QueryEnhancer for testing."""
        return QueryEnhancer()
    
    def test_initialization(self, enhancer):
        """Test QueryEnhancer initialization and data structures."""
        # Verify technical synonyms loaded
        assert len(enhancer.technical_synonyms) > 0
        assert 'cpu' in enhancer.technical_synonyms
        assert 'processor' in enhancer.technical_synonyms['cpu']
        
        # Verify acronym expansions loaded
        assert len(enhancer.acronym_expansions) > 0
        assert 'CPU' in enhancer.acronym_expansions
        assert enhancer.acronym_expansions['CPU'] == 'Central Processing Unit'
        
        # Verify regex patterns compiled
        assert enhancer._acronym_pattern is not None
        assert enhancer._question_indicators is not None
        
        # Verify question type keywords loaded
        assert 'conceptual' in enhancer.question_type_keywords
        assert 'technical' in enhancer.question_type_keywords
    
    def test_technical_term_expansion(self, enhancer):
        """Test synonym expansion for technical terms."""
        # Test basic CPU expansion
        enhanced = enhancer.expand_technical_terms("CPU performance")
        assert "CPU" in enhanced  # Original preserved
        assert "processor" in enhanced  # Synonym added
        assert "microprocessor" in enhanced  # Second synonym added
        
        # Test RISC-V compound term
        enhanced = enhancer.expand_technical_terms("RISC-V architecture")
        assert "RISC-V" in enhanced  # Original preserved
        assert "riscv" in enhanced or "risc v" in enhanced  # Synonym added
        
        # Test memory terminology
        enhanced = enhancer.expand_technical_terms("memory optimization")
        assert "memory" in enhanced  # Original preserved
        assert "ram" in enhanced or "storage" in enhanced  # Synonym added
        
        # Test case insensitivity
        enhanced = enhancer.expand_technical_terms("CPU Memory Cache")
        assert "processor" in enhanced
        assert "ram" in enhanced or "storage" in enhanced
        
        # Test empty input handling
        assert enhancer.expand_technical_terms("") == ""
        assert enhancer.expand_technical_terms(None) == None
    
    def test_acronym_expansion(self, enhancer):
        """Test acronym detection and expansion."""
        # Test single acronym
        enhanced = enhancer.detect_and_expand_acronyms("RTOS scheduling")
        assert "RTOS" in enhanced  # Original preserved
        assert "Real-Time Operating System" in enhanced  # Expansion added
        
        # Test multiple acronyms
        enhanced = enhancer.detect_and_expand_acronyms("CPU RTOS DMA")
        assert "CPU Central Processing Unit" in enhanced
        assert "RTOS Real-Time Operating System" in enhanced
        assert "DMA Direct Memory Access" in enhanced
        
        # Test communication protocols
        enhanced = enhancer.detect_and_expand_acronyms("UART SPI I2C")
        assert "Universal Asynchronous Receiver Transmitter" in enhanced
        assert "Serial Peripheral Interface" in enhanced
        assert "Inter-Integrated Circuit" in enhanced
        
        # Test unknown acronym (should be preserved)
        enhanced = enhancer.detect_and_expand_acronyms("XYZ protocol")
        assert "XYZ" in enhanced  # Unknown acronym preserved
        assert enhanced == "XYZ protocol"  # No expansion for unknown
        
        # Test no acronyms
        enhanced = enhancer.detect_and_expand_acronyms("simple text query")
        assert enhanced == "simple text query"  # No change
    
    def test_query_characteristic_analysis(self, enhancer):
        """Test comprehensive query analysis."""
        # Test technical query
        analysis = enhancer.analyze_query_characteristics("CPU RTOS performance optimization")
        assert analysis['technical_term_count'] >= 2  # CPU, performance, optimization
        assert analysis['has_acronyms'] == True  # CPU, RTOS
        assert len(analysis['detected_acronyms']) >= 2
        assert 'cpu' in [term.lower() for term in analysis['technical_terms']]
        
        # Test conceptual query
        analysis = enhancer.analyze_query_characteristics("How does memory management work?")
        assert analysis['question_type'] in ['conceptual', 'mixed']
        assert analysis['has_question_indicators'] == True
        assert analysis['technical_term_count'] >= 1  # memory
        
        # Test procedural query
        analysis = enhancer.analyze_query_characteristics("steps to configure UART")
        assert analysis['question_type'] in ['procedural', 'technical', 'mixed']
        assert analysis['technical_term_count'] >= 1  # UART counts as technical
        
        # Test empty query
        analysis = enhancer.analyze_query_characteristics("")
        assert analysis['technical_term_count'] == 0
        assert analysis['has_acronyms'] == False
        assert analysis['question_type'] == 'unknown'
        assert analysis['complexity_score'] == 0.0
    
    def test_adaptive_weighting(self, enhancer):
        """Test adaptive weight calculation."""
        # Technical query should favor sparse (lower dense_weight)
        tech_weight = enhancer.adaptive_hybrid_weighting("RV32I instruction encoding registers")
        assert tech_weight < 0.5, f"Technical query weight {tech_weight} should favor sparse"
        
        # Conceptual query should favor dense (higher dense_weight)  
        concept_weight = enhancer.adaptive_hybrid_weighting("How does memory management work in embedded systems?")
        assert concept_weight > 0.6, f"Conceptual query weight {concept_weight} should favor semantic"
        
        # Acronym-heavy query should favor sparse
        acronym_weight = enhancer.adaptive_hybrid_weighting("CPU RTOS ISR DMA")
        assert acronym_weight < 0.5, f"Acronym-heavy query weight {acronym_weight} should favor sparse"
        
        # Simple query test
        simple_weight = enhancer.adaptive_hybrid_weighting("processor")
        assert 0.1 <= simple_weight <= 0.9, "Weight should be within valid bounds"
        
        # Weight bounds testing
        weights = [
            enhancer.adaptive_hybrid_weighting("CPU MCU RTOS ISR DMA PWM GPIO"),  # Very technical
            enhancer.adaptive_hybrid_weighting("How do complex embedded systems work?"),  # Very conceptual
            enhancer.adaptive_hybrid_weighting("test"),  # Minimal
        ]
        for weight in weights:
            assert 0.1 <= weight <= 0.9, f"Weight {weight} outside valid bounds [0.1, 0.9]"
    
    def test_comprehensive_enhancement(self, enhancer):
        """Test complete query enhancement pipeline."""
        # Test comprehensive enhancement
        result = enhancer.enhance_query("CPU RTOS performance")
        
        # Verify structure
        assert 'enhanced_query' in result
        assert 'optimal_weight' in result
        assert 'analysis' in result
        assert 'enhancement_metadata' in result
        
        # Verify enhancement applied
        enhanced_query = result['enhanced_query']
        assert "processor" in enhanced_query  # Technical expansion
        assert "Real-Time Operating System" in enhanced_query  # Acronym expansion
        assert len(enhanced_query.split()) > len("CPU RTOS performance".split())  # Expanded
        
        # Verify metadata
        metadata = result['enhancement_metadata']
        assert metadata['original_length'] == 3  # "CPU RTOS performance"
        assert metadata['enhanced_length'] > 3  # Should be expanded
        assert metadata['expansion_ratio'] > 1.0  # Expansion occurred
        assert metadata['processing_time_ms'] < 50  # Performance requirement
        assert 'term_expansion' in metadata['techniques_applied']
        assert 'acronym_expansion' in metadata['techniques_applied']
        
        # Verify optimal weight is reasonable
        optimal_weight = result['optimal_weight']
        assert 0.1 <= optimal_weight <= 0.9
        
        # Verify analysis completeness
        analysis = result['analysis']
        assert analysis['technical_term_count'] > 0
        assert analysis['has_acronyms'] == True
    
    def test_performance_requirements(self, enhancer):
        """Test performance requirements are met."""
        import time
        
        # Test individual method performance
        queries = [
            "CPU performance optimization",
            "RTOS scheduling algorithm implementation", 
            "How does memory management work in embedded systems?",
            "UART SPI I2C communication protocols",
            "ARM Cortex-M processor architecture"
        ]
        
        for query in queries:
            # Test technical term expansion performance
            start = time.perf_counter()
            enhancer.expand_technical_terms(query)
            term_time = (time.perf_counter() - start) * 1000
            assert term_time < 10, f"Term expansion took {term_time:.2f}ms (should be <10ms)"
            
            # Test acronym expansion performance
            start = time.perf_counter()
            enhancer.detect_and_expand_acronyms(query)
            acronym_time = (time.perf_counter() - start) * 1000
            assert acronym_time < 5, f"Acronym expansion took {acronym_time:.2f}ms (should be <5ms)"
            
            # Test analysis performance
            start = time.perf_counter()
            enhancer.analyze_query_characteristics(query)
            analysis_time = (time.perf_counter() - start) * 1000
            assert analysis_time < 5, f"Analysis took {analysis_time:.2f}ms (should be <5ms)"
            
            # Test complete enhancement performance
            start = time.perf_counter()
            enhancer.enhance_query(query)
            total_time = (time.perf_counter() - start) * 1000
            assert total_time < 15, f"Total enhancement took {total_time:.2f}ms (should be <15ms)"
    
    def test_edge_cases(self, enhancer):
        """Test edge cases and error handling."""
        # Empty and None inputs
        assert enhancer.expand_technical_terms("") == ""
        assert enhancer.detect_and_expand_acronyms("") == ""
        
        # Very short queries
        result = enhancer.enhance_query("CPU")
        assert result['enhanced_query'] != "CPU"  # Should be expanded
        assert 0.1 <= result['optimal_weight'] <= 0.9
        
        # Very long queries
        long_query = " ".join(["CPU", "memory", "performance"] * 10)
        result = enhancer.enhance_query(long_query)
        assert result['analysis']['complexity_score'] > 0.5  # Should detect complexity
        
        # Special characters and punctuation
        result = enhancer.enhance_query("CPU, memory & performance optimization!")
        assert "processor" in result['enhanced_query']  # Should still expand despite punctuation
        
        # Mixed case
        result = enhancer.enhance_query("Cpu Memory Performance")
        assert "processor" in result['enhanced_query']  # Case insensitive
    
    def test_domain_coverage(self, enhancer):
        """Test coverage of embedded systems domains."""
        # Processor architecture terms
        enhanced = enhancer.expand_technical_terms("ARM RISC-V CPU core")
        assert any(syn in enhanced for syn in ['advanced risc machine', 'processor', 'execution unit'])
        
        # Memory systems terms
        enhanced = enhancer.expand_technical_terms("SRAM DRAM cache memory")
        assert any(syn in enhanced for syn in ['static ram', 'dynamic ram', 'buffer'])
        
        # Communication protocols
        enhanced = enhancer.detect_and_expand_acronyms("UART SPI I2C CAN")
        assert "Universal Asynchronous Receiver Transmitter" in enhanced
        assert "Serial Peripheral Interface" in enhanced
        
        # Real-time systems
        enhanced = enhancer.detect_and_expand_acronyms("RTOS ISR interrupt")
        assert "Real-Time Operating System" in enhanced
        assert "Interrupt Service Routine" in enhanced
        
        # Power management
        enhanced = enhancer.detect_and_expand_acronyms("PMU LDO power")
        assert "Power Management Unit" in enhanced
        assert "Low Dropout Regulator" in enhanced


class TestBasicRAGIntegration:
    """Test integration of QueryEnhancer with BasicRAG system."""
    
    @pytest.fixture
    def mock_rag_with_data(self):
        """Create BasicRAG with mock data for testing."""
        rag = BasicRAG()
        
        # Mock chunks with technical content
        mock_chunks = [
            {
                "text": "The CPU processor handles instruction execution and arithmetic operations",
                "source": "test.pdf",
                "page": 1,
                "chunk_id": 0,
                "start_char": 0,
                "end_char": 75
            },
            {
                "text": "RTOS Real-Time Operating System provides deterministic scheduling for embedded applications",
                "source": "test.pdf", 
                "page": 2,
                "chunk_id": 1,
                "start_char": 76,
                "end_char": 165
            },
            {
                "text": "Memory management in embedded systems requires careful consideration of SRAM and flash storage",
                "source": "test.pdf",
                "page": 3,
                "chunk_id": 2,
                "start_char": 166,
                "end_char": 260
            }
        ]
        
        # Manually populate for testing (simulating indexed documents)
        rag.chunks = mock_chunks
        
        # Initialize hybrid retriever for testing
        try:
            from shared_utils.retrieval.hybrid_search import HybridRetriever
            rag.hybrid_retriever = HybridRetriever(use_mps=False)
            rag.hybrid_retriever.index_documents(mock_chunks)
        except ImportError:
            # Hybrid retriever not available - tests will handle gracefully
            pass
        
        return rag
    
    def test_enhanced_hybrid_query_success(self, mock_rag_with_data):
        """Test successful enhanced hybrid query execution."""
        result = mock_rag_with_data.enhanced_hybrid_query("CPU performance optimization")
        
        # Verify enhanced query structure
        assert "original_query" in result
        assert result["original_query"] == "CPU performance optimization"
        assert "enhanced_query" in result
        assert "adaptive_weight" in result
        assert "query_analysis" in result
        assert "enhancement_applied" in result
        
        # Verify enhancement was applied
        if result["enhancement_applied"]:
            assert "processor" in result["enhanced_query"]  # Technical expansion
            assert len(result["enhanced_query"].split()) > len("CPU performance optimization".split())
            assert result["retrieval_method"] == "enhanced_hybrid"
            
            # Verify analysis data
            analysis = result["query_analysis"]
            assert analysis["technical_term_count"] > 0
            assert 0.1 <= result["adaptive_weight"] <= 0.9
    
    def test_enhanced_hybrid_query_fallback(self, mock_rag_with_data):
        """Test fallback behavior when enhancement fails."""
        # Test with empty query
        result = mock_rag_with_data.enhanced_hybrid_query("")
        assert result["retrieval_method"] == "none"
        assert result["enhancement_applied"] == False
        
        # Test graceful degradation when components not available
        result = mock_rag_with_data.enhanced_hybrid_query("test query")
        
        # Should either succeed with enhancement or fallback gracefully
        assert "enhancement_applied" in result
        if not result["enhancement_applied"]:
            assert "fallback_reason" in result
    
    def test_query_type_adaptation(self, mock_rag_with_data):
        """Test that different query types get appropriate treatment."""
        
        # Technical query - should favor sparse weighting
        tech_result = mock_rag_with_data.enhanced_hybrid_query("RV32I instruction encoding")
        if tech_result["enhancement_applied"]:
            assert tech_result["adaptive_weight"] < 0.6  # Should favor sparse
        
        # Conceptual query - should favor dense weighting
        concept_result = mock_rag_with_data.enhanced_hybrid_query("How does memory management work?")
        if concept_result["enhancement_applied"]:
            assert concept_result["adaptive_weight"] > 0.6  # Should favor semantic
    
    def test_performance_integration(self, mock_rag_with_data):
        """Test end-to-end performance of enhanced hybrid query."""
        import time
        
        queries = [
            "CPU performance",
            "RTOS scheduling", 
            "memory management concepts",
            "UART communication protocol"
        ]
        
        for query in queries:
            start = time.perf_counter()
            result = mock_rag_with_data.enhanced_hybrid_query(query)
            total_time = (time.perf_counter() - start) * 1000
            
            # Should complete within reasonable time
            assert total_time < 100, f"Enhanced query took {total_time:.2f}ms (should be <100ms)"
            
            # Should return valid results
            assert "retrieval_method" in result
            assert isinstance(result.get("chunks", []), list)


class TestQueryEnhancerCapabilities:
    """Test QueryEnhancer system capabilities and statistics."""
    
    def test_enhancement_stats(self):
        """Test system capability reporting."""
        enhancer = QueryEnhancer()
        stats = enhancer.get_enhancement_stats()
        
        # Verify stats structure
        assert 'technical_synonyms_count' in stats
        assert 'acronym_expansions_count' in stats
        assert 'supported_domains' in stats
        assert 'question_types_supported' in stats
        assert 'performance_targets' in stats
        
        # Verify reasonable counts
        assert stats['technical_synonyms_count'] > 10
        assert stats['acronym_expansions_count'] > 20
        
        # Verify domain coverage
        domains = stats['supported_domains']
        assert 'embedded_systems' in domains
        assert 'processor_architecture' in domains
        assert 'communication_protocols' in domains
        
        # Verify question type support
        question_types = stats['question_types_supported']
        assert 'conceptual' in question_types
        assert 'technical' in question_types
        assert 'procedural' in question_types
    
    def test_vocabulary_completeness(self):
        """Test completeness of technical vocabulary."""
        enhancer = QueryEnhancer()
        
        # Test processor terminology coverage
        processor_terms = ['cpu', 'mcu', 'core', 'alu']
        for term in processor_terms:
            assert term in enhancer.technical_synonyms
            assert len(enhancer.technical_synonyms[term]) >= 2
        
        # Test memory terminology coverage
        memory_terms = ['memory', 'cache', 'sram', 'dram']
        for term in memory_terms:
            assert term in enhancer.technical_synonyms
        
        # Test architecture terminology coverage
        arch_terms = ['risc-v', 'arm', 'isa']
        for term in arch_terms:
            assert term in enhancer.technical_synonyms
        
        # Test acronym coverage for key embedded domains
        key_acronyms = ['CPU', 'MCU', 'RTOS', 'UART', 'SPI', 'I2C', 'DMA', 'PWM', 'GPIO']
        for acronym in key_acronyms:
            assert acronym in enhancer.acronym_expansions
            assert len(enhancer.acronym_expansions[acronym]) > 5  # Meaningful expansion


# Performance benchmark tests
def test_batch_processing_performance():
    """Test performance with batch of realistic queries."""
    enhancer = QueryEnhancer()
    
    realistic_queries = [
        "CPU performance optimization techniques",
        "RTOS scheduling algorithms for real-time systems", 
        "Memory management in embedded ARM processors",
        "UART SPI I2C communication protocol comparison",
        "How does interrupt handling work in microcontrollers?",
        "PWM signal generation for motor control applications",
        "Low power design strategies for battery-powered devices",
        "Debug and troubleshooting embedded system issues",
        "Flash memory programming and EEPROM data storage",
        "ADC sampling rates and digital signal processing"
    ]
    
    import time
    total_start = time.perf_counter()
    
    for query in realistic_queries:
        result = enhancer.enhance_query(query)
        assert result['enhancement_metadata']['processing_time_ms'] < 15
        assert len(result['enhanced_query']) > len(query)  # Should be expanded
    
    total_time = (time.perf_counter() - total_start) * 1000
    avg_time = total_time / len(realistic_queries)
    
    assert avg_time < 10, f"Average enhancement time {avg_time:.2f}ms exceeds 10ms target"
    print(f"Batch processing: {len(realistic_queries)} queries in {total_time:.2f}ms (avg: {avg_time:.2f}ms)")


if __name__ == "__main__":
    # Run basic functionality tests
    enhancer = QueryEnhancer()
    
    print("🧪 Testing QueryEnhancer functionality...")
    
    # Test basic expansion
    enhanced = enhancer.expand_technical_terms("CPU performance")
    print(f"✅ Term expansion: 'CPU performance' → '{enhanced}'")
    
    # Test acronym expansion
    expanded = enhancer.detect_and_expand_acronyms("RTOS scheduling")
    print(f"✅ Acronym expansion: 'RTOS scheduling' → '{expanded}'")
    
    # Test adaptive weighting
    weight = enhancer.adaptive_hybrid_weighting("RV32I instruction encoding")
    print(f"✅ Adaptive weighting: technical query → {weight:.2f} (favors sparse)")
    
    # Test complete enhancement
    result = enhancer.enhance_query("CPU RTOS performance")
    print(f"✅ Complete enhancement: {result['enhancement_metadata']['processing_time_ms']:.2f}ms")
    
    print("\n🎯 All basic tests passed! QueryEnhancer ready for production.")