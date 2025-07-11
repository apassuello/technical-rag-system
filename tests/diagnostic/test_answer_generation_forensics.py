"""
Test Suite 5: Answer Generation Deep Analysis (CRITICAL)

This test suite provides forensic-level analysis of the answer generation pipeline,
focusing on model behavior, confidence calculation, and response quality issues.
"""

import os
import sys
import json
import time
import traceback
from pathlib import Path
from typing import Any, Dict, List, Tuple, Optional

from base_diagnostic import DiagnosticTestBase, DataValidator

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

try:
    from src.core.platform_orchestrator import PlatformOrchestrator
    from src.components.generators.adaptive_generator import AdaptiveAnswerGenerator
    from shared_utils.generation.hf_answer_generator import HuggingFaceAnswerGenerator
    from src.core.interfaces import Document, Answer
except ImportError as e:
    print(f"Import error (expected during analysis): {e}")


class AnswerGenerationForensics(DiagnosticTestBase):
    """
    Critical forensic analysis of answer generation pipeline.
    
    This class performs deep analysis of:
    - Model configuration and behavior (Squad2 vs generative)
    - Prompt construction and formatting
    - API request/response processing
    - Confidence calculation mechanisms
    - Response quality and fragment issues
    """
    
    def __init__(self, output_dir: Path = None):
        super().__init__(output_dir)
        self.test_queries = [
            {
                "query": "What is RISC-V?",
                "expected_behavior": "comprehensive_answer",
                "min_length": 100,
                "expected_confidence_range": (0.3, 0.8)
            },
            {
                "query": "Who am I?",
                "expected_behavior": "refuse_answer",
                "max_confidence": 0.3
            },
            {
                "query": "Where is Paris?",
                "expected_behavior": "refuse_answer", 
                "max_confidence": 0.3
            }
        ]
    
    def run_all_tests(self) -> List[Dict[str, Any]]:
        """Execute all answer generation forensics tests."""
        tests = [
            (self.test_model_configuration_analysis, "model_configuration", "generator"),
            (self.test_prompt_construction_forensics, "prompt_construction", "generator"),
            (self.test_model_inference_analysis, "model_inference", "generator"),
            (self.test_confidence_calculation_forensics, "confidence_calculation", "generator"),
            (self.test_response_processing_analysis, "response_processing", "generator"),
            (self.test_answer_quality_analysis, "answer_quality", "generator")
        ]
        
        results = []
        for test_func, test_name, component in tests:
            result = self.safe_execute(test_func, test_name, component)
            self.save_result(result)
            results.append(result)
        
        return results
    
    def test_model_configuration_analysis(self) -> Tuple[Dict, Dict, List[str], List[str]]:
        """Complete analysis of model configuration and expected behavior."""
        data_captured = {
            "generator_configuration": {},
            "model_analysis": {},
            "adapter_analysis": {},
            "underlying_model_details": {}
        }
        
        analysis_results = {}
        issues_found = []
        recommendations = []
        
        try:
            # Initialize generator through orchestrator
            config_path = self.get_absolute_config_path("config/default.yaml")
            orchestrator = PlatformOrchestrator(config_path)
            
            # Analyze generator configuration
            generator = orchestrator.get_component('answer_generator')
            if generator:
                generator_config = self._analyze_generator_configuration(generator)
                data_captured["generator_configuration"] = generator_config
                
                # Deep analysis of modular sub-components
                sub_component_analysis = self._analyze_modular_subcomponents(generator)
                data_captured["sub_components"] = sub_component_analysis
                
                # Analyze LLM adapter (OllamaAdapter for current setup)
                llm_adapter_analysis = self._analyze_llm_adapter(generator)
                data_captured["llm_adapter_analysis"] = llm_adapter_analysis
                
                # Analyze prompt builder and response parser
                prompt_parser_analysis = self._analyze_prompt_and_parser(generator)
                data_captured["prompt_parser_analysis"] = prompt_parser_analysis
                
                analysis_results = {
                    "model_name": generator_config.get("model_name", "unknown"),
                    "model_type": llm_adapter_analysis.get("adapter_type", "unknown"),
                    "is_modular": sub_component_analysis.get("is_modular", False),
                    "architecture_compliant": sub_component_analysis.get("architecture_compliant", False),
                    "sub_component_count": len(sub_component_analysis.get("components", {})),
                    "expected_output_format": "generated_text"
                }
                
                # Critical issue detection for modular AnswerGenerator
                if analysis_results["model_type"] == "ollama":
                    print("    ✅ Using Ollama adapter for local LLM generation")
                elif analysis_results["model_type"] == "unknown":
                    issues_found.append("WARNING: Unknown model type - verify LLM adapter configuration")
                
                # Check for modular architecture compliance
                if "sub_components" in data_captured:
                    sub_components = data_captured["sub_components"]
                    expected_components = ['prompt_builder', 'llm_client', 'response_parser', 'confidence_scorer']
                    missing_components = [comp for comp in expected_components if comp not in sub_components]
                    if missing_components:
                        issues_found.append(f"Missing sub-components: {missing_components}")
                        recommendations.append("Ensure all required sub-components are present in modular AnswerGenerator")
                
            else:
                issues_found.append("CRITICAL: Unable to access generator from orchestrator")
                
        except Exception as e:
            issues_found.append(f"Model configuration analysis failed: {str(e)}")
            data_captured["error"] = {
                "error_message": str(e),
                "traceback": traceback.format_exc()
            }
        
        return data_captured, analysis_results, issues_found, recommendations
    
    def test_prompt_construction_forensics(self) -> Tuple[Dict, Dict, List[str], List[str]]:
        """Detailed analysis of prompt construction and formatting."""
        data_captured = {
            "prompt_construction_tests": {},
            "context_formatting": {},
            "model_specific_formatting": {},
            "prompt_variations": {}
        }
        
        analysis_results = {}
        issues_found = []
        recommendations = []
        
        try:
            # Create test context documents
            test_documents = self._create_test_documents()
            
            # Test prompt construction for each test query
            for i, test_case in enumerate(self.test_queries):
                query = test_case["query"]
                prompt_analysis = self._analyze_prompt_construction(query, test_documents)
                data_captured["prompt_construction_tests"][f"query_{i}"] = prompt_analysis
            
            # Analyze context formatting specifically
            context_analysis = self._analyze_context_formatting(test_documents)
            data_captured["context_formatting"] = context_analysis
            
            # Test model-specific prompt formatting
            model_formatting = self._test_model_specific_formatting()
            data_captured["model_specific_formatting"] = model_formatting
            
            analysis_results = {
                "prompt_format_consistency": all(
                    test.get("format_valid", False) 
                    for test in data_captured["prompt_construction_tests"].values()
                ),
                "context_preservation": context_analysis.get("metadata_preserved", False),
                "model_format_compatibility": model_formatting.get("squad2_format_detected", False)
            }
            
            # Check for issues
            if analysis_results["model_format_compatibility"]:
                issues_found.append("Squad2 question/context format detected - confirms extractive QA usage")
            
            if not analysis_results["context_preservation"]:
                issues_found.append("Context metadata not properly preserved in prompt construction")
                
        except Exception as e:
            issues_found.append(f"Prompt construction analysis failed: {str(e)}")
            data_captured["error"] = str(e)
        
        return data_captured, analysis_results, issues_found, recommendations
    
    def test_model_inference_analysis(self) -> Tuple[Dict, Dict, List[str], List[str]]:
        """Forensic analysis of model inference process."""
        data_captured = {
            "inference_tests": {},
            "api_communication": {},
            "response_formats": {},
            "model_outputs": {}
        }
        
        analysis_results = {}
        issues_found = []
        recommendations = []
        
        try:
            # Test model inference with controlled inputs
            test_query = "What is RISC-V?"
            test_documents = self._create_test_documents()
            
            # Trace inference process step by step
            inference_trace = self._trace_model_inference(test_query, test_documents)
            data_captured["inference_tests"]["risc_v_query"] = inference_trace
            
            # Analyze API communication
            api_analysis = self._analyze_api_communication(inference_trace)
            data_captured["api_communication"] = api_analysis
            
            # Analyze response formats
            response_analysis = self._analyze_response_formats(inference_trace)
            data_captured["response_formats"] = response_analysis
            
            # Test different query types
            for test_case in self.test_queries:
                query_trace = self._trace_model_inference(test_case["query"], test_documents)
                data_captured["inference_tests"][test_case["query"]] = query_trace
            
            analysis_results = {
                "api_requests_successful": api_analysis.get("success_rate", 0) > 0.5,
                "response_format_consistent": response_analysis.get("format_consistent", False),
                "model_response_type": response_analysis.get("primary_response_type", "unknown")
            }
            
            # Check for critical issues
            if analysis_results["model_response_type"] == "extractive_span":
                issues_found.append("CONFIRMED: Model returning extractive spans, not generative responses")
                recommendations.append("Switch to generative model to get complete answers")
            
        except Exception as e:
            issues_found.append(f"Model inference analysis failed: {str(e)}")
            data_captured["error"] = str(e)
        
        return data_captured, analysis_results, issues_found, recommendations
    
    def test_confidence_calculation_forensics(self) -> Tuple[Dict, Dict, List[str], List[str]]:
        """Critical analysis of confidence calculation mechanisms."""
        data_captured = {
            "confidence_calculation_trace": {},
            "hardcoded_value_detection": {},
            "confidence_variations": {},
            "calculation_method_analysis": {}
        }
        
        analysis_results = {}
        issues_found = []
        recommendations = []
        
        try:
            # Test confidence calculation for various queries
            confidence_tests = {}
            
            for test_case in self.test_queries:
                confidence_trace = self._trace_confidence_calculation(test_case["query"])
                confidence_tests[test_case["query"]] = confidence_trace
                
                # Check for hardcoded values
                confidence_value = confidence_trace.get("final_confidence", 0)
                if confidence_value == 0.8:
                    issues_found.append(f"HARDCODED CONFIDENCE DETECTED: {test_case['query']} returned exactly 0.8")
                elif confidence_value == 0.1:
                    issues_found.append(f"HARDCODED CONFIDENCE DETECTED: {test_case['query']} returned exactly 0.1")
            
            data_captured["confidence_calculation_trace"] = confidence_tests
            
            # Analyze confidence calculation method
            calculation_method = self._analyze_confidence_calculation_method()
            data_captured["calculation_method_analysis"] = calculation_method
            
            # Test for hardcoded values specifically
            hardcoded_detection = self._detect_hardcoded_confidence_values()
            data_captured["hardcoded_value_detection"] = hardcoded_detection
            
            # Test confidence variations
            variation_tests = self._test_confidence_variations()
            data_captured["confidence_variations"] = variation_tests
            
            analysis_results = {
                "confidence_range": self._calculate_confidence_range(confidence_tests),
                "has_hardcoded_values": hardcoded_detection.get("hardcoded_detected", False),
                "confidence_calculation_working": calculation_method.get("method_identified", False),
                "confidence_varies_appropriately": variation_tests.get("shows_variation", False)
            }
            
            # Critical issue detection
            if analysis_results["has_hardcoded_values"]:
                issues_found.append("CRITICAL: Hardcoded confidence values detected")
                recommendations.append("Fix confidence calculation to use actual model uncertainty")
            
            if not analysis_results["confidence_varies_appropriately"]:
                issues_found.append("Confidence scores not varying appropriately with answer quality")
                recommendations.append("Implement proper confidence calibration based on context quality")
                
        except Exception as e:
            issues_found.append(f"Confidence calculation analysis failed: {str(e)}")
            data_captured["error"] = str(e)
        
        return data_captured, analysis_results, issues_found, recommendations
    
    def test_response_processing_analysis(self) -> Tuple[Dict, Dict, List[str], List[str]]:
        """Analysis of response processing and answer extraction."""
        data_captured = {
            "response_processing_trace": {},
            "answer_extraction": {},
            "citation_processing": {},
            "metadata_handling": {}
        }
        
        analysis_results = {}
        issues_found = []
        recommendations = []
        
        try:
            # Test response processing pipeline
            test_query = "What is RISC-V?"
            test_documents = self._create_test_documents()
            
            # Trace complete response processing
            processing_trace = self._trace_response_processing(test_query, test_documents)
            data_captured["response_processing_trace"] = processing_trace
            
            # Analyze answer extraction specifically
            extraction_analysis = self._analyze_answer_extraction(processing_trace)
            data_captured["answer_extraction"] = extraction_analysis
            
            # Analyze citation processing
            citation_analysis = self._analyze_citation_processing(processing_trace)
            data_captured["citation_processing"] = citation_analysis
            
            # Analyze metadata handling
            metadata_analysis = self._analyze_metadata_handling(processing_trace)
            data_captured["metadata_handling"] = metadata_analysis
            
            analysis_results = {
                "answer_extraction_working": extraction_analysis.get("extraction_successful", False),
                "citations_generated": citation_analysis.get("citations_present", False),
                "metadata_preserved": metadata_analysis.get("metadata_intact", False),
                "source_attribution_working": citation_analysis.get("source_attribution_working", False)
            }
            
            # Check for source attribution issues
            if not analysis_results["source_attribution_working"]:
                issues_found.append("Source attribution showing 'unknown' values - metadata propagation broken")
                recommendations.append("Fix metadata propagation from PDF processing to citation generation")
            
        except Exception as e:
            issues_found.append(f"Response processing analysis failed: {str(e)}")
            data_captured["error"] = str(e)
        
        return data_captured, analysis_results, issues_found, recommendations
    
    def test_answer_quality_analysis(self) -> Tuple[Dict, Dict, List[str], List[str]]:
        """Comprehensive analysis of answer quality and fragment issues."""
        data_captured = {
            "quality_tests": {},
            "fragment_analysis": {},
            "length_analysis": {},
            "coherence_analysis": {}
        }
        
        analysis_results = {}
        issues_found = []
        recommendations = []
        
        try:
            # DISABLED: Quality analysis was too shallow
            # Instead, collect raw data for manual analysis
            quality_results = {}
            
            for test_case in self.test_queries:
                # Collect raw answer data instead of scoring
                raw_data = self._collect_answer_data(test_case)
                quality_results[test_case["query"]] = raw_data
                
                # Note: Not analyzing quality here - data collection only
                # But we can flag obvious issues for manual review
                citation_issues = raw_data.get("raw_answer_data", {}).get("citation_analysis", {})
                if citation_issues.get("has_broken_citations", False):
                    issues_found.append(f"BROKEN CITATIONS detected in '{test_case['query']}' - manual review needed")
                    
                if citation_issues.get("repetitive_citation_text", False):
                    issues_found.append(f"REPETITIVE TEXT detected in '{test_case['query']}' - manual review needed")
            
            # DISABLED: Quality analysis was too shallow
            # Just store raw data for manual analysis
            data_captured["quality_tests"] = quality_results
            
            # Disable automatic scoring
            analysis_results = {
                "total_responses": len(quality_results),
                "quality_analysis_disabled": True,
                "message": "Quality analysis disabled - use manual analysis of raw data"
            }
            
            # Add note about disabled analysis
            recommendations.append("Review raw answer data manually for quality assessment")
            recommendations.append("Check citation_analysis field for broken citations")
            recommendations.append("Check repetition_analysis field for repetitive text")
            recommendations.append("Check format_analysis field for template structure issues")
            
        except Exception as e:
            issues_found.append(f"Answer quality analysis failed: {str(e)}")
            data_captured["error"] = str(e)
        
        return data_captured, analysis_results, issues_found, recommendations
    
    # Helper methods for detailed analysis
    
    def _analyze_generator_configuration(self, generator) -> Dict[str, Any]:
        """Analyze generator configuration and setup."""
        config = {
            "generator_class": type(generator).__name__,
            "generator_module": type(generator).__module__,
            "attributes": {},
            "configuration": {}
        }
        
        # Capture key attributes
        for attr in ["model_name", "temperature", "max_tokens", "confidence_threshold"]:
            if hasattr(generator, attr):
                config["attributes"][attr] = getattr(generator, attr)
        
        # Get generator info if available
        if hasattr(generator, 'get_generator_info'):
            try:
                config["configuration"] = generator.get_generator_info()
            except:
                config["configuration"] = "unable_to_access"
        
        return config
    
    def _analyze_modular_subcomponents(self, generator) -> Dict[str, Any]:
        """Analyze modular sub-components of the AnswerGenerator."""
        sub_component_analysis = {
            "is_modular": False,
            "architecture_compliant": False,
            "components": {},
            "missing_components": []
        }
        
        # Check if generator has get_component_info method (indicates modular architecture)
        if hasattr(generator, 'get_component_info'):
            try:
                component_info = generator.get_component_info()
                sub_component_analysis["is_modular"] = True
                sub_component_analysis["components"] = component_info
                
                # Expected components for modular AnswerGenerator
                expected_components = ['prompt_builder', 'llm_client', 'response_parser', 'confidence_scorer']
                present_components = [comp for comp in expected_components if comp in component_info]
                missing_components = [comp for comp in expected_components if comp not in component_info]
                
                sub_component_analysis["missing_components"] = missing_components
                sub_component_analysis["architecture_compliant"] = len(missing_components) == 0
                
                print(f"    Sub-components found: {list(component_info.keys())}")
                
            except Exception as e:
                sub_component_analysis["error"] = str(e)
        
        return sub_component_analysis
    
    def _analyze_llm_adapter(self, generator) -> Dict[str, Any]:
        """Analyze the LLM adapter (OllamaAdapter for current setup)."""
        adapter_analysis = {
            "adapter_type": "unknown",
            "adapter_present": False,
            "adapter_configuration": {}
        }
        
        # Check for LLM client adapter
        if hasattr(generator, 'llm_client'):
            llm_client = generator.llm_client
            adapter_analysis["adapter_present"] = True
            adapter_analysis["adapter_type"] = type(llm_client).__name__
            
            # Get adapter info if available
            if hasattr(llm_client, 'get_adapter_info'):
                try:
                    adapter_info = llm_client.get_adapter_info()
                    adapter_analysis["adapter_configuration"] = adapter_info
                except Exception as e:
                    adapter_analysis["adapter_configuration"] = {"error": str(e)}
            
            # Check for Ollama-specific attributes
            if hasattr(llm_client, 'model_name') and hasattr(llm_client, 'ollama_url'):
                adapter_analysis["adapter_type"] = "ollama"
                adapter_analysis["adapter_configuration"].update({
                    "model_name": getattr(llm_client, 'model_name', 'unknown'),
                    "ollama_url": getattr(llm_client, 'ollama_url', 'unknown')
                })
        
        return adapter_analysis
    
    def _analyze_prompt_and_parser(self, generator) -> Dict[str, Any]:
        """Analyze prompt builder and response parser components."""
        prompt_parser_analysis = {
            "prompt_builder": {"present": False, "type": "unknown"},
            "response_parser": {"present": False, "type": "unknown"},
            "confidence_scorer": {"present": False, "type": "unknown"}
        }
        
        # Check prompt builder
        if hasattr(generator, 'prompt_builder'):
            prompt_builder = generator.prompt_builder
            prompt_parser_analysis["prompt_builder"] = {
                "present": True,
                "type": type(prompt_builder).__name__
            }
            
            # Get builder info if available
            if hasattr(prompt_builder, 'get_builder_info'):
                try:
                    builder_info = prompt_builder.get_builder_info()
                    prompt_parser_analysis["prompt_builder"]["info"] = builder_info
                except Exception as e:
                    prompt_parser_analysis["prompt_builder"]["info"] = {"error": str(e)}
        
        # Check response parser
        if hasattr(generator, 'response_parser'):
            response_parser = generator.response_parser
            prompt_parser_analysis["response_parser"] = {
                "present": True,
                "type": type(response_parser).__name__
            }
            
            # Get parser info if available
            if hasattr(response_parser, 'get_parser_info'):
                try:
                    parser_info = response_parser.get_parser_info()
                    prompt_parser_analysis["response_parser"]["info"] = parser_info
                except Exception as e:
                    prompt_parser_analysis["response_parser"]["info"] = {"error": str(e)}
        
        # Check confidence scorer
        if hasattr(generator, 'confidence_scorer'):
            confidence_scorer = generator.confidence_scorer
            prompt_parser_analysis["confidence_scorer"] = {
                "present": True,
                "type": type(confidence_scorer).__name__
            }
            
            # Get scorer info if available
            if hasattr(confidence_scorer, 'get_scorer_info'):
                try:
                    scorer_info = confidence_scorer.get_scorer_info()
                    prompt_parser_analysis["confidence_scorer"]["info"] = scorer_info
                except Exception as e:
                    prompt_parser_analysis["confidence_scorer"]["info"] = {"error": str(e)}
        
        return prompt_parser_analysis
    
    def _create_test_documents(self) -> List[Document]:
        """Create test documents for analysis."""
        return [
            Document(
                content="RISC-V is an open-source instruction set architecture (ISA) based on reduced instruction set computer (RISC) principles.",
                metadata={
                    "source": "riscv-card.pdf",
                    "page": 1,
                    "chunk_id": "chunk_1"
                }
            ),
            Document(
                content="The RISC-V ISA is defined as a base integer ISA, which must be present in any implementation, plus optional standard extensions.",
                metadata={
                    "source": "riscv-spec.pdf", 
                    "page": 15,
                    "chunk_id": "chunk_2"
                }
            )
        ]
    
    def _analyze_prompt_construction(self, query: str, documents: List[Document]) -> Dict[str, Any]:
        """Analyze prompt construction for specific query and documents."""
        prompt_analysis = {
            "query": query,
            "documents_count": len(documents),
            "prompt_construction_trace": {},
            "format_analysis": {}
        }
        
        try:
            # Try to get the generator
            config_path = self.get_absolute_config_path("config/default.yaml")
            orchestrator = PlatformOrchestrator(config_path)
            generator = orchestrator.get_component('answer_generator')
            
            if hasattr(generator, '_documents_to_chunks'):
                # Convert documents to chunks format
                chunks = generator._documents_to_chunks(documents)
                prompt_analysis["chunks_created"] = len(chunks)
                prompt_analysis["chunk_format"] = chunks[0] if chunks else {}
            
            # Try to trace prompt construction if possible
            if hasattr(generator, 'generator') and hasattr(generator.generator, '_format_context'):
                context = generator.generator._format_context(chunks)
                prompt_analysis["context_formatted"] = context[:500]  # First 500 chars
                
                # Check for Squad2 format indicators
                if "Context:" in context and "Question:" in context:
                    prompt_analysis["format_analysis"]["squad2_format_detected"] = True
                
        except Exception as e:
            prompt_analysis["error"] = str(e)
        
        return prompt_analysis
    
    def _analyze_context_formatting(self, documents: List[Document]) -> Dict[str, Any]:
        """Analyze how context is formatted from documents."""
        context_analysis = {
            "documents_processed": len(documents),
            "metadata_preservation": {},
            "formatting_quality": {}
        }
        
        # Check metadata preservation
        for i, doc in enumerate(documents):
            context_analysis["metadata_preservation"][f"doc_{i}"] = {
                "source_present": "source" in doc.metadata,
                "page_present": "page" in doc.metadata,
                "source_value": doc.metadata.get("source", "missing"),
                "page_value": doc.metadata.get("page", "missing")
            }
        
        # Overall metadata preservation
        context_analysis["metadata_preserved"] = all(
            meta.get("source_present", False) and meta.get("page_present", False)
            for meta in context_analysis["metadata_preservation"].values()
        )
        
        return context_analysis
    
    def _test_model_specific_formatting(self) -> Dict[str, Any]:
        """Test model-specific prompt formatting."""
        formatting_test = {
            "squad2_format_test": {},
            "generative_format_test": {},
            "format_compatibility": {}
        }
        
        try:
            # Get generator and test formatting
            config_path = self.get_absolute_config_path("config/default.yaml")
            orchestrator = PlatformOrchestrator(config_path)
            generator = orchestrator.get_component('answer_generator')
            
            if hasattr(generator, 'generator') and hasattr(generator.generator, 'model_name'):
                model_name = generator.generator.model_name
                
                # Check if Squad2 formatting is being used
                if "squad" in model_name.lower():
                    formatting_test["squad2_format_detected"] = True
                    formatting_test["expected_format"] = "question/context"
                else:
                    formatting_test["squad2_format_detected"] = False
                    formatting_test["expected_format"] = "generative_prompt"
        
        except Exception as e:
            formatting_test["error"] = str(e)
        
        return formatting_test
    
    def _trace_model_inference(self, query: str, documents: List[Document]) -> Dict[str, Any]:
        """Trace the complete model inference process."""
        inference_trace = {
            "query": query,
            "input_preparation": {},
            "model_call": {},
            "response_processing": {},
            "timing": {}
        }
        
        try:
            start_time = time.time()
            
            # Get answer through orchestrator
            config_path = self.get_absolute_config_path("config/default.yaml")
            orchestrator = PlatformOrchestrator(config_path)
            
            # Process documents first
            orchestrator.index_documents(documents)
            
            prep_time = time.time()
            inference_trace["timing"]["preparation_time"] = prep_time - start_time
            
            # Generate answer
            answer = orchestrator.process_query(query)
            
            end_time = time.time()
            inference_trace["timing"]["generation_time"] = end_time - prep_time
            inference_trace["timing"]["total_time"] = end_time - start_time
            
            # Capture answer details
            inference_trace["response_processing"] = {
                "answer_text": answer.text,
                "answer_length": len(answer.text),
                "confidence": answer.confidence,
                "sources_count": len(answer.sources),
                "metadata": answer.metadata
            }
            
        except Exception as e:
            inference_trace["error"] = str(e)
            inference_trace["traceback"] = traceback.format_exc()
        
        return inference_trace
    
    def _analyze_api_communication(self, inference_trace: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze API communication patterns."""
        api_analysis = {
            "success_rate": 0,
            "response_time_analysis": {},
            "error_patterns": {}
        }
        
        if "error" not in inference_trace:
            api_analysis["success_rate"] = 1.0
            
            timing = inference_trace.get("timing", {})
            api_analysis["response_time_analysis"] = {
                "total_time": timing.get("total_time", 0),
                "generation_time": timing.get("generation_time", 0),
                "preparation_time": timing.get("preparation_time", 0)
            }
        else:
            api_analysis["success_rate"] = 0.0
            api_analysis["error_patterns"]["error_message"] = inference_trace.get("error", "")
        
        return api_analysis
    
    def _analyze_response_formats(self, inference_trace: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze response format patterns."""
        response_analysis = {
            "format_consistent": False,
            "response_characteristics": {},
            "primary_response_type": "unknown"
        }
        
        response_data = inference_trace.get("response_processing", {})
        if response_data:
            answer_text = response_data.get("answer_text", "")
            
            # Analyze response characteristics
            response_analysis["response_characteristics"] = {
                "length": len(answer_text),
                "is_single_word": len(answer_text.split()) == 1,
                "is_fragment": len(answer_text.split()) < 5,
                "has_complete_sentences": "." in answer_text,
                "answer_preview": answer_text[:100]
            }
            
            # Determine response type
            if response_analysis["response_characteristics"]["is_fragment"]:
                response_analysis["primary_response_type"] = "extractive_span"
            elif response_analysis["response_characteristics"]["has_complete_sentences"]:
                response_analysis["primary_response_type"] = "generative_text"
            else:
                response_analysis["primary_response_type"] = "unknown"
        
        return response_analysis
    
    def _trace_confidence_calculation(self, query: str) -> Dict[str, Any]:
        """Trace confidence calculation for specific query."""
        confidence_trace = {
            "query": query,
            "confidence_calculation_steps": {},
            "final_confidence": None,
            "calculation_method": "unknown"
        }
        
        try:
            # Get answer and trace confidence
            config_path = self.get_absolute_config_path("config/default.yaml")
            orchestrator = PlatformOrchestrator(config_path)
            documents = self._create_test_documents()
            orchestrator.index_documents(documents)
            
            answer = orchestrator.process_query(query)
            confidence_trace["final_confidence"] = answer.confidence
            
            # Try to identify calculation method
            if answer.confidence == 0.8:
                confidence_trace["calculation_method"] = "hardcoded_default_0.8"
            elif answer.confidence == 0.1:
                confidence_trace["calculation_method"] = "hardcoded_default_0.1"
            elif 0.0 < answer.confidence < 1.0:
                confidence_trace["calculation_method"] = "calculated"
            else:
                confidence_trace["calculation_method"] = "invalid_range"
            
        except Exception as e:
            confidence_trace["error"] = str(e)
        
        return confidence_trace
    
    def _analyze_confidence_calculation_method(self) -> Dict[str, Any]:
        """Analyze the confidence calculation method in detail."""
        method_analysis = {
            "method_identified": False,
            "code_inspection": {},
            "default_values_found": []
        }
        
        try:
            # Try to inspect HuggingFaceAnswerGenerator code
            import inspect
            
            # Look for confidence calculation in HF generator
            if 'HuggingFaceAnswerGenerator' in globals():
                hf_gen_source = inspect.getsource(HuggingFaceAnswerGenerator._calculate_confidence)
                method_analysis["code_inspection"]["hf_calculate_confidence"] = hf_gen_source[:500]
                
                # Look for hardcoded values in the source
                if "0.8" in hf_gen_source:
                    method_analysis["default_values_found"].append("0.8_in_hf_generator")
                if "0.1" in hf_gen_source:
                    method_analysis["default_values_found"].append("0.1_in_hf_generator")
                
                method_analysis["method_identified"] = True
        
        except Exception as e:
            method_analysis["error"] = str(e)
        
        return method_analysis
    
    def _detect_hardcoded_confidence_values(self) -> Dict[str, Any]:
        """Detect hardcoded confidence values."""
        detection = {
            "hardcoded_detected": False,
            "hardcoded_values": [],
            "test_results": {}
        }
        
        # Test multiple queries to see if confidence varies
        test_queries = ["What is RISC-V?", "Who am I?", "Where is Paris?", "Invalid query xyz"]
        confidence_values = []
        
        try:
            config_path = self.get_absolute_config_path("config/default.yaml")
            orchestrator = PlatformOrchestrator(config_path)
            documents = self._create_test_documents()
            orchestrator.index_documents(documents)
            
            for query in test_queries:
                try:
                    answer = orchestrator.process_query(query)
                    confidence = answer.confidence
                    confidence_values.append(confidence)
                    detection["test_results"][query] = confidence
                except:
                    continue
            
            # Check for hardcoded values
            unique_confidences = set(confidence_values)
            
            if len(unique_confidences) == 1:
                detection["hardcoded_detected"] = True
                detection["hardcoded_values"] = list(unique_confidences)
            elif 0.8 in confidence_values or 0.1 in confidence_values:
                detection["hardcoded_detected"] = True
                detection["hardcoded_values"] = [v for v in unique_confidences if v in [0.8, 0.1]]
        
        except Exception as e:
            detection["error"] = str(e)
        
        return detection
    
    def _test_confidence_variations(self) -> Dict[str, Any]:
        """Test if confidence varies appropriately."""
        variation_test = {
            "shows_variation": False,
            "confidence_range": {},
            "variation_analysis": {}
        }
        
        try:
            # Test with queries of different quality
            queries = [
                "What is RISC-V?",  # Should be high confidence
                "How does RISC-V work?",  # Should be medium confidence
                "Where is Paris?"  # Should be low confidence
            ]
            
            confidences = []
            config_path = self.get_absolute_config_path("config/default.yaml")
            orchestrator = PlatformOrchestrator(config_path)
            documents = self._create_test_documents()
            orchestrator.index_documents(documents)
            
            for query in queries:
                try:
                    answer = orchestrator.process_query(query)
                    confidences.append(answer.confidence)
                except:
                    continue
            
            if confidences:
                variation_test["confidence_range"] = {
                    "min": min(confidences),
                    "max": max(confidences),
                    "range": max(confidences) - min(confidences)
                }
                
                variation_test["shows_variation"] = variation_test["confidence_range"]["range"] > 0.1
        
        except Exception as e:
            variation_test["error"] = str(e)
        
        return variation_test
    
    def _calculate_confidence_range(self, confidence_tests: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate confidence range across all tests."""
        confidences = []
        
        for test in confidence_tests.values():
            if "final_confidence" in test and test["final_confidence"] is not None:
                confidences.append(test["final_confidence"])
        
        if confidences:
            return {
                "min": min(confidences),
                "max": max(confidences),
                "range": max(confidences) - min(confidences),
                "average": sum(confidences) / len(confidences),
                "all_values": confidences
            }
        else:
            return {"error": "No valid confidence values found"}
    
    def _trace_response_processing(self, query: str, documents: List[Document]) -> Dict[str, Any]:
        """Trace complete response processing pipeline."""
        processing_trace = {
            "input_query": query,
            "input_documents": len(documents),
            "processing_steps": {},
            "output_analysis": {}
        }
        
        try:
            # Process through orchestrator
            config_path = self.get_absolute_config_path("config/default.yaml")
            orchestrator = PlatformOrchestrator(config_path)
            orchestrator.index_documents(documents)
            
            answer = orchestrator.process_query(query)
            
            # Analyze output
            processing_trace["output_analysis"] = {
                "answer_text": answer.text,
                "answer_length": len(answer.text),
                "confidence": answer.confidence,
                "sources_count": len(answer.sources),
                "citations_present": len(answer.sources) > 0,
                "metadata_keys": list(answer.metadata.keys()) if answer.metadata else []
            }
            
        except Exception as e:
            processing_trace["error"] = str(e)
        
        return processing_trace
    
    def _analyze_answer_extraction(self, processing_trace: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze answer extraction process."""
        extraction_analysis = {
            "extraction_successful": False,
            "answer_characteristics": {},
            "extraction_quality": {}
        }
        
        output = processing_trace.get("output_analysis", {})
        if output and "answer_text" in output:
            answer_text = output["answer_text"]
            
            extraction_analysis["extraction_successful"] = len(answer_text) > 0
            extraction_analysis["answer_characteristics"] = {
                "length": len(answer_text),
                "word_count": len(answer_text.split()),
                "is_fragment": len(answer_text.split()) < 5,
                "has_sentences": "." in answer_text
            }
        
        return extraction_analysis
    
    def _analyze_citation_processing(self, processing_trace: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze citation processing and source attribution."""
        citation_analysis = {
            "citations_present": False,
            "source_attribution_working": False,
            "citation_quality": {}
        }
        
        output = processing_trace.get("output_analysis", {})
        if output:
            citation_analysis["citations_present"] = output.get("sources_count", 0) > 0
            
            # Check source attribution quality
            if citation_analysis["citations_present"]:
                # This would need to be expanded based on actual source data
                citation_analysis["source_attribution_working"] = True
        
        return citation_analysis
    
    def _analyze_metadata_handling(self, processing_trace: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze metadata handling throughout processing."""
        metadata_analysis = {
            "metadata_intact": False,
            "metadata_fields": {},
            "metadata_quality": {}
        }
        
        output = processing_trace.get("output_analysis", {})
        if output and "metadata_keys" in output:
            metadata_keys = output["metadata_keys"]
            
            metadata_analysis["metadata_intact"] = len(metadata_keys) > 0
            metadata_analysis["metadata_fields"]["present_keys"] = metadata_keys
        
        return metadata_analysis
    
    def _collect_answer_data(self, test_case: Dict[str, Any]) -> Dict[str, Any]:
        """Collect raw answer data for manual analysis (replaces shallow quality analysis)."""
        answer_data = {
            "query": test_case["query"],
            "expected_behavior": test_case["expected_behavior"],
            "raw_answer_data": {},
            "collection_note": "Data collected for manual analysis"
        }
        
        try:
            # Get answer
            config_path = self.get_absolute_config_path("config/default.yaml")
            orchestrator = PlatformOrchestrator(config_path)
            documents = self._create_test_documents()
            orchestrator.index_documents(documents)
            
            answer = orchestrator.process_query(test_case["query"])
            
            # Collect raw answer data for manual analysis
            answer_data["raw_answer_data"] = {
                "answer_text": answer.text,
                "answer_length": len(answer.text),
                "word_count": len(answer.text.split()),
                "confidence": answer.confidence,
                "sources_count": len(answer.sources) if hasattr(answer, 'sources') else 0,
                "metadata": answer.metadata if hasattr(answer, 'metadata') else {},
                "citation_analysis": self._analyze_citation_format(answer.text),
                "repetition_analysis": self._analyze_text_repetition(answer.text),
                "format_analysis": self._analyze_answer_format(answer.text)
            }
            
            # Note: No quality scoring here - just data collection
            
        except Exception as e:
            answer_data["error"] = str(e)
        
        return answer_data
    
    def _analyze_citation_format(self, answer_text: str) -> Dict[str, Any]:
        """Analyze citation format issues that current tests miss."""
        citation_analysis = {
            "has_broken_citations": False,
            "broken_citation_examples": [],
            "citation_format_issues": [],
            "repetitive_citation_text": False
        }
        
        # Check for broken citations
        if "Page unknown from unknown" in answer_text:
            citation_analysis["has_broken_citations"] = True
            citation_analysis["broken_citation_examples"].append("Page unknown from unknown")
            citation_analysis["citation_format_issues"].append("Contains 'Page unknown from unknown' instead of proper citations")
        
        # Check for repetitive "the documentation" text
        doc_count = answer_text.count("the documentation")
        if doc_count > 5:
            citation_analysis["repetitive_citation_text"] = True
            citation_analysis["citation_format_issues"].append(f"'the documentation' appears {doc_count} times (repetitive)")
        
        return citation_analysis
    
    def _analyze_text_repetition(self, answer_text: str) -> Dict[str, Any]:
        """Analyze text repetition issues that current tests miss."""
        repetition_analysis = {
            "has_repetitive_patterns": False,
            "repetitive_phrases": [],
            "repetition_count": 0
        }
        
        # Check for common repetitive patterns
        patterns_to_check = [
            "the documentation",
            "based on the provided documentation",
            "according to the documentation"
        ]
        
        for pattern in patterns_to_check:
            count = answer_text.count(pattern)
            if count > 3:
                repetition_analysis["has_repetitive_patterns"] = True
                repetition_analysis["repetitive_phrases"].append({
                    "phrase": pattern,
                    "count": count
                })
                repetition_analysis["repetition_count"] += count
        
        return repetition_analysis
    
    def _analyze_answer_format(self, answer_text: str) -> Dict[str, Any]:
        """Analyze answer format issues that current tests miss."""
        format_analysis = {
            "has_template_structure": False,
            "format_issues": [],
            "professional_formatting": True
        }
        
        # Check for template-like structure
        template_patterns = [
            "1. Primary definition:",
            "2. Technical details:",
            "3. Related concepts:",
            "4. Any relevant acronyms:"
        ]
        
        template_count = sum(1 for pattern in template_patterns if pattern in answer_text)
        if template_count > 1:
            format_analysis["has_template_structure"] = True
            format_analysis["format_issues"].append(f"Contains template structure ({template_count} template patterns)")
            format_analysis["professional_formatting"] = False
        
        return format_analysis
    
    def _analyze_fragment_patterns(self, quality_results: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze fragment response patterns."""
        fragment_analysis = {
            "total_responses": len(quality_results),
            "fragment_count": 0,
            "fragment_examples": [],
            "fragment_percentage": 0
        }
        
        for result in quality_results.values():
            if result.get("answer_quality", {}).get("is_fragment", False):
                fragment_analysis["fragment_count"] += 1
                fragment_analysis["fragment_examples"].append({
                    "query": result["query"],
                    "answer": result.get("answer_quality", {}).get("answer_text", "")[:100]
                })
        
        if fragment_analysis["total_responses"] > 0:
            fragment_analysis["fragment_percentage"] = (
                fragment_analysis["fragment_count"] / fragment_analysis["total_responses"]
            )
        
        return fragment_analysis
    
    def _analyze_answer_lengths(self, quality_results: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze answer length patterns."""
        lengths = []
        
        for result in quality_results.values():
            length = result.get("answer_quality", {}).get("answer_length", 0)
            if length > 0:
                lengths.append(length)
        
        length_analysis = {
            "lengths": lengths,
            "average_length": sum(lengths) / len(lengths) if lengths else 0,
            "min_length": min(lengths) if lengths else 0,
            "max_length": max(lengths) if lengths else 0
        }
        
        return length_analysis
    
    def _analyze_answer_coherence(self, quality_results: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze answer coherence and completeness."""
        coherence_analysis = {
            "responses_with_sentences": 0,
            "total_responses": len(quality_results),
            "coherence_score": 0
        }
        
        for result in quality_results.values():
            has_sentences = result.get("answer_quality", {}).get("has_complete_sentences", False)
            if has_sentences:
                coherence_analysis["responses_with_sentences"] += 1
        
        if coherence_analysis["total_responses"] > 0:
            coherence_analysis["coherence_score"] = (
                coherence_analysis["responses_with_sentences"] / coherence_analysis["total_responses"]
            )
        
        return coherence_analysis


if __name__ == "__main__":
    # Run answer generation forensics tests
    forensics = AnswerGenerationForensics()
    results = forensics.run_all_tests()
    forensics.print_summary()