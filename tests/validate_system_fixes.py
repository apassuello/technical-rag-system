#!/usr/bin/env python3
"""
Comprehensive System Validation Script

This script validates all the fixes implemented for the RAG system:
- Fix 1: Local Ollama integration
- Fix 2: Phase 4 unified architecture  
- Fix 3: Component integration repair

Run this script to verify the system is portfolio-ready.
"""

import sys
import time
import yaml
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from src.core.platform_orchestrator import PlatformOrchestrator
from src.core.interfaces import Document


class SystemValidator:
    """Comprehensive system validation for portfolio readiness."""
    
    def __init__(self):
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'configuration_validation': {},
            'system_initialization': {},
            'component_integration': {},
            'end_to_end_functionality': {},
            'portfolio_readiness': {}
        }
        self.orchestrator = None
    
    def run_all_validations(self) -> Dict[str, Any]:
        """Run all validation tests and return comprehensive results."""
        print("=" * 80)
        print("RAG SYSTEM COMPREHENSIVE VALIDATION")
        print(f"Timestamp: {self.results['timestamp']}")
        print("=" * 80)
        
        try:
            # Test 1: Configuration validation
            print("\n🔧 VALIDATING CONFIGURATION CHANGES...")
            self.validate_configuration()
            
            # Test 2: System initialization 
            print("\n🚀 VALIDATING SYSTEM INITIALIZATION...")
            self.validate_system_initialization()
            
            # Test 3: Component integration
            print("\n🔗 VALIDATING COMPONENT INTEGRATION...")
            self.validate_component_integration()
            
            # Test 4: End-to-end functionality
            print("\n🎯 VALIDATING END-TO-END FUNCTIONALITY...")
            self.validate_end_to_end_functionality()
            
            # Test 5: Portfolio readiness assessment
            print("\n📊 ASSESSING PORTFOLIO READINESS...")
            self.assess_portfolio_readiness()
            
            # Generate summary
            self.print_validation_summary()
            
        except Exception as e:
            print(f"❌ VALIDATION FAILED: {str(e)}")
            import traceback
            traceback.print_exc()
            self.results['fatal_error'] = str(e)
        
        return self.results
    
    def validate_configuration(self):
        """Validate all configuration changes are correct."""
        try:
            with open('config/default.yaml', 'r') as f:
                config = yaml.safe_load(f)
            
            # Check Fix 1: Ollama configuration
            generator_config = config.get('answer_generator', {}).get('config', {})
            ollama_checks = {
                'model_name_is_ollama': generator_config.get('model_name') == 'llama3.2:3b',
                'use_ollama_enabled': generator_config.get('use_ollama') is True,
                'ollama_url_configured': generator_config.get('ollama_url') == 'http://localhost:11434'
            }
            
            # Check Fix 2: Phase 4 architecture
            architecture_checks = {
                'vector_store_removed': 'vector_store' not in config,
                'retriever_is_unified': config.get('retriever', {}).get('type') == 'unified',
                'unified_config_present': 'embedding_dim' in config.get('retriever', {}).get('config', {})
            }
            
            self.results['configuration_validation'] = {
                'ollama_configuration': ollama_checks,
                'architecture_configuration': architecture_checks,
                'all_ollama_checks_passed': all(ollama_checks.values()),
                'all_architecture_checks_passed': all(architecture_checks.values())
            }
            
            print(f"  Ollama configuration: {'✅' if all(ollama_checks.values()) else '❌'}")
            print(f"  Architecture configuration: {'✅' if all(architecture_checks.values()) else '❌'}")
            
        except Exception as e:
            self.results['configuration_validation']['error'] = str(e)
            print(f"  ❌ Configuration validation failed: {str(e)}")
    
    def validate_system_initialization(self):
        """Validate system initializes correctly with new configuration."""
        try:
            # Test system initialization
            self.orchestrator = PlatformOrchestrator('config/default.yaml')
            
            # Check system health
            health = self.orchestrator.get_system_health()
            
            # Validate architecture detection
            architecture_correct = health.get('architecture') == 'unified'
            
            # Check component access
            has_retriever = hasattr(self.orchestrator, '_components') and 'retriever' in self.orchestrator._components
            has_generator = hasattr(self.orchestrator, '_components') and 'answer_generator' in self.orchestrator._components
            
            if has_retriever:
                retriever_type = type(self.orchestrator._components['retriever']).__name__
            else:
                retriever_type = None
                
            if has_generator:
                generator_type = type(self.orchestrator._components['answer_generator']).__name__
            else:
                generator_type = None
            
            self.results['system_initialization'] = {
                'initialization_successful': True,
                'architecture_display': health.get('architecture'),
                'architecture_correct': architecture_correct,
                'components_accessible': has_retriever and has_generator,
                'retriever_type': retriever_type,
                'generator_type': generator_type,
                'system_health': health
            }
            
            print(f"  System initialization: ✅")
            print(f"  Architecture display: {health.get('architecture')} {'✅' if architecture_correct else '❌'}")
            print(f"  Components accessible: {'✅' if has_retriever and has_generator else '❌'}")
            
        except Exception as e:
            self.results['system_initialization'] = {
                'initialization_successful': False,
                'error': str(e)
            }
            print(f"  ❌ System initialization failed: {str(e)}")
            raise
    
    def validate_component_integration(self):
        """Validate Fix 3: Component integration works correctly."""
        try:
            if not self.orchestrator:
                raise RuntimeError("System not initialized")
            
            # Create test documents
            test_documents = [
                Document(
                    content='RISC-V is an open-source instruction set architecture (ISA) based on reduced instruction set computer (RISC) principles. It originated at UC Berkeley.',
                    metadata={'source': 'riscv-card.pdf', 'page': 1, 'chunk_id': 'chunk_1'}
                ),
                Document(
                    content='The RISC-V ISA includes optional standard extensions for integer multiplication, atomic instructions, and floating-point operations.',
                    metadata={'source': 'riscv-spec.pdf', 'page': 15, 'chunk_id': 'chunk_2'}
                )
            ]
            
            # Test the new index_documents method (Fix 3)
            start_time = time.time()
            indexed_count = self.orchestrator.index_documents(test_documents)
            indexing_time = time.time() - start_time
            
            self.results['component_integration'] = {
                'documents_created': len(test_documents),
                'documents_indexed': indexed_count,
                'indexing_successful': indexed_count == len(test_documents),
                'indexing_time_seconds': indexing_time,
                'integration_method_working': True
            }
            
            print(f"  Document indexing: {'✅' if indexed_count == len(test_documents) else '❌'}")
            print(f"  Documents indexed: {indexed_count}/{len(test_documents)}")
            print(f"  Indexing time: {indexing_time:.3f}s")
            
        except Exception as e:
            self.results['component_integration'] = {
                'integration_method_working': False,
                'error': str(e)
            }
            print(f"  ❌ Component integration failed: {str(e)}")
            raise
    
    def validate_end_to_end_functionality(self):
        """Validate complete end-to-end query processing."""
        try:
            if not self.orchestrator:
                raise RuntimeError("System not initialized")
            
            # Test queries with different expectations
            test_queries = [
                {
                    'query': 'What is RISC-V?',
                    'expected_type': 'comprehensive_answer',
                    'min_length': 200,
                    'should_contain': ['risc-v', 'isa', 'architecture']
                },
                {
                    'query': 'What are RISC-V extensions?',
                    'expected_type': 'technical_answer', 
                    'min_length': 150,
                    'should_contain': ['extension', 'risc-v']
                },
                {
                    'query': 'Where is Paris?',
                    'expected_type': 'out_of_scope',
                    'max_confidence': 0.7,
                    'should_contain': ['not contain', 'not available', 'documentation']
                }
            ]
            
            query_results = []
            
            for test in test_queries:
                query = test['query']
                print(f"  Testing: \"{query}\"")
                
                try:
                    start_time = time.time()
                    answer = self.orchestrator.process_query(query)
                    response_time = time.time() - start_time
                    
                    # Quality assessment
                    length_check = len(answer.text) >= test.get('min_length', 0)
                    confidence_check = (
                        answer.confidence <= test.get('max_confidence', 1.0) and
                        answer.confidence >= test.get('min_confidence', 0.0)
                    )
                    
                    content_check = True
                    if 'should_contain' in test:
                        content_check = any(
                            term.lower() in answer.text.lower() 
                            for term in test['should_contain']
                        )
                    
                    result = {
                        'query': query,
                        'expected_type': test['expected_type'],
                        'answer_length': len(answer.text),
                        'answer_preview': answer.text[:150] + '...',
                        'confidence': answer.confidence,
                        'sources_count': len(answer.sources),
                        'response_time': response_time,
                        'quality_checks': {
                            'length_adequate': length_check,
                            'confidence_appropriate': confidence_check,
                            'content_relevant': content_check
                        },
                        'overall_success': length_check and confidence_check and content_check
                    }
                    
                    query_results.append(result)
                    
                    status = "✅" if result['overall_success'] else "⚠️"
                    print(f"    {status} Length: {len(answer.text)}, Confidence: {answer.confidence:.3f}")
                    
                except Exception as e:
                    query_results.append({
                        'query': query,
                        'error': str(e),
                        'overall_success': False
                    })
                    print(f"    ❌ Query failed: {str(e)}")
            
            successful_queries = sum(1 for r in query_results if r.get('overall_success', False))
            
            self.results['end_to_end_functionality'] = {
                'total_queries_tested': len(test_queries),
                'successful_queries': successful_queries,
                'success_rate': successful_queries / len(test_queries),
                'query_results': query_results,
                'pipeline_working': successful_queries > 0
            }
            
            print(f"  Query success rate: {successful_queries}/{len(test_queries)} ({successful_queries/len(test_queries)*100:.1f}%)")
            
        except Exception as e:
            self.results['end_to_end_functionality'] = {
                'pipeline_working': False,
                'error': str(e)
            }
            print(f"  ❌ End-to-end validation failed: {str(e)}")
    
    def assess_portfolio_readiness(self):
        """Assess overall portfolio readiness based on all tests."""
        try:
            # Quality gates
            config_valid = self.results.get('configuration_validation', {}).get('all_ollama_checks_passed', False) and \
                          self.results.get('configuration_validation', {}).get('all_architecture_checks_passed', False)
            
            system_init = self.results.get('system_initialization', {}).get('initialization_successful', False) and \
                         self.results.get('system_initialization', {}).get('architecture_correct', False)
            
            integration_works = self.results.get('component_integration', {}).get('integration_method_working', False)
            
            pipeline_works = self.results.get('end_to_end_functionality', {}).get('pipeline_working', False)
            
            success_rate = self.results.get('end_to_end_functionality', {}).get('success_rate', 0)
            
            # Calculate readiness score
            quality_gates = {
                'configuration_correct': config_valid,
                'system_initialization': system_init,
                'component_integration': integration_works,
                'end_to_end_pipeline': pipeline_works,
                'query_success_rate_acceptable': success_rate >= 0.75
            }
            
            passed_gates = sum(1 for gate in quality_gates.values() if gate)
            readiness_score = (passed_gates / len(quality_gates)) * 100
            
            # Determine readiness level
            if readiness_score >= 90:
                readiness_level = "PORTFOLIO_READY"
            elif readiness_score >= 70:
                readiness_level = "STAGING_READY"
            elif readiness_score >= 50:
                readiness_level = "DEVELOPMENT_READY"
            else:
                readiness_level = "NOT_READY"
            
            self.results['portfolio_readiness'] = {
                'quality_gates': quality_gates,
                'gates_passed': passed_gates,
                'total_gates': len(quality_gates),
                'readiness_score': readiness_score,
                'readiness_level': readiness_level,
                'ready_for_portfolio': readiness_level == "PORTFOLIO_READY"
            }
            
            print(f"  Readiness score: {readiness_score:.1f}%")
            print(f"  Readiness level: {readiness_level}")
            
        except Exception as e:
            self.results['portfolio_readiness'] = {
                'error': str(e),
                'ready_for_portfolio': False
            }
            print(f"  ❌ Portfolio assessment failed: {str(e)}")
    
    def print_validation_summary(self):
        """Print comprehensive validation summary."""
        print("\n" + "=" * 80)
        print("VALIDATION SUMMARY")
        print("=" * 80)
        
        readiness = self.results.get('portfolio_readiness', {})
        
        print(f"\n🎯 PORTFOLIO READINESS: {readiness.get('readiness_level', 'UNKNOWN')}")
        print(f"📊 Overall Score: {readiness.get('readiness_score', 0):.1f}%")
        
        quality_gates = readiness.get('quality_gates', {})
        print(f"\n✅ QUALITY GATES:")
        for gate, status in quality_gates.items():
            status_icon = "✅" if status else "❌"
            print(f"   {status_icon} {gate.replace('_', ' ').title()}")
        
        # Key metrics
        config = self.results.get('configuration_validation', {})
        system = self.results.get('system_initialization', {})
        integration = self.results.get('component_integration', {})
        e2e = self.results.get('end_to_end_functionality', {})
        
        print(f"\n📋 KEY METRICS:")
        print(f"   Architecture: {system.get('architecture_display', 'unknown')}")
        print(f"   Components: {system.get('retriever_type', 'unknown')} + {system.get('generator_type', 'unknown')}")
        print(f"   Documents indexed: {integration.get('documents_indexed', 0)}")
        print(f"   Query success rate: {e2e.get('success_rate', 0)*100:.1f}%")
        
        # Next steps
        if readiness.get('ready_for_portfolio', False):
            print(f"\n🚀 SYSTEM IS PORTFOLIO READY!")
            print(f"   ✅ All fixes implemented successfully")
            print(f"   ✅ End-to-end pipeline functional")
            print(f"   ✅ Quality meets Swiss market standards")
        else:
            print(f"\n⚠️  SYSTEM NEEDS ATTENTION")
            failed_gates = [gate for gate, status in quality_gates.items() if not status]
            print(f"   Failed gates: {', '.join(failed_gates)}")
        
        print("=" * 80)
    
    def save_results(self, filename: str = None):
        """Save validation results to file."""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"validation_results_{timestamp}.json"
        
        import json
        with open(filename, 'w') as f:
            json.dump(self.results, f, indent=2, default=str)
        
        print(f"\n💾 Results saved to: {filename}")


def main():
    """Main execution function."""
    validator = SystemValidator()
    results = validator.run_all_validations()
    
    # Save results
    validator.save_results()
    
    # Return results for programmatic access
    return results


if __name__ == "__main__":
    main()