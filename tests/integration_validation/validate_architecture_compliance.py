#!/usr/bin/env python3
"""
Validate architecture compliance against the specification documents.
"""

import sys
from pathlib import Path
import json
from typing import Dict, Any, List

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.append(str(project_root))

from src.core.platform_orchestrator import PlatformOrchestrator
from src.core.component_factory import ComponentFactory

class ArchitectureValidator:
    """Validates implementation against architecture specifications."""
    
    def __init__(self):
        self.config_path = "config/default.yaml"
        self.validation_results = {}
        
    def validate_architecture_compliance(self) -> Dict[str, Any]:
        """Validate complete architecture compliance."""
        print("🔍 Validating Architecture Compliance...")
        
        results = {
            "timestamp": "2025-07-10T09:04:30",
            "validation_results": {},
            "compliance_score": 0,
            "critical_issues": [],
            "recommendations": []
        }
        
        try:
            # Test 1: Component Factory Integration
            print("\n1. Testing Component Factory Integration...")
            factory_results = self._validate_component_factory()
            results["validation_results"]["component_factory"] = factory_results
            
            # Test 2: Modular Document Processor Architecture
            print("\n2. Validating Modular Document Processor Architecture...")
            processor_results = self._validate_modular_processor()
            results["validation_results"]["modular_processor"] = processor_results
            
            # Test 3: Interface Compliance
            print("\n3. Testing Interface Compliance...")
            interface_results = self._validate_interface_compliance()
            results["validation_results"]["interface_compliance"] = interface_results
            
            # Test 4: Adapter Pattern Implementation
            print("\n4. Validating Adapter Pattern Implementation...")
            adapter_results = self._validate_adapter_pattern()
            results["validation_results"]["adapter_pattern"] = adapter_results
            
            # Test 5: Configuration Schema Compliance
            print("\n5. Testing Configuration Schema Compliance...")
            config_results = self._validate_configuration_schema()
            results["validation_results"]["configuration_schema"] = config_results
            
            # Test 6: System Integration
            print("\n6. Testing System Integration...")
            integration_results = self._validate_system_integration()
            results["validation_results"]["system_integration"] = integration_results
            
            # Calculate compliance score
            results["compliance_score"] = self._calculate_compliance_score(results["validation_results"])
            
            # Generate summary
            self._generate_compliance_summary(results)
            
        except Exception as e:
            results["critical_issues"].append(f"Architecture validation failed: {str(e)}")
            
        return results
    
    def _validate_component_factory(self) -> Dict[str, Any]:
        """Validate component factory correctly maps to modular processor."""
        results = {
            "passed": True,
            "tests": [],
            "issues": []
        }
        
        try:
            # Test factory mapping
            available_components = ComponentFactory.get_available_components()
            
            # Check that hybrid_pdf maps to ModularDocumentProcessor
            processor = ComponentFactory.create_processor("hybrid_pdf")
            is_modular = processor.__class__.__name__ == "ModularDocumentProcessor"
            
            results["tests"].append({
                "name": "Component factory uses ModularDocumentProcessor",
                "passed": is_modular,
                "details": f"Created: {processor.__class__.__name__}"
            })
            
            # Test legacy compatibility
            legacy_processor = ComponentFactory.create_processor("legacy_pdf")
            is_legacy = legacy_processor.__class__.__name__ == "HybridPDFProcessor"
            
            results["tests"].append({
                "name": "Legacy processor still available",
                "passed": is_legacy,
                "details": f"Legacy: {legacy_processor.__class__.__name__}"
            })
            
            # Test backwards compatibility
            compatible_processor = ComponentFactory.create_processor("hybrid_pdf", chunk_size=1024)
            works_with_legacy_params = compatible_processor.__class__.__name__ == "ModularDocumentProcessor"
            
            results["tests"].append({
                "name": "Backwards compatibility with legacy parameters",
                "passed": works_with_legacy_params,
                "details": f"Accepts legacy params: {works_with_legacy_params}"
            })
            
            results["passed"] = all(test["passed"] for test in results["tests"])
            
        except Exception as e:
            results["passed"] = False
            results["issues"].append(f"Component factory validation failed: {str(e)}")
            
        return results
    
    def _validate_modular_processor(self) -> Dict[str, Any]:
        """Validate modular processor architecture."""
        results = {
            "passed": True,
            "tests": [],
            "issues": []
        }
        
        try:
            processor = ComponentFactory.create_processor("hybrid_pdf")
            
            # Test sub-component structure
            component_info = processor.get_component_info()
            
            has_parser = "parser" in component_info
            has_chunker = "chunker" in component_info
            has_cleaner = "cleaner" in component_info
            has_pipeline = "pipeline" in component_info
            
            results["tests"].append({
                "name": "Has parser sub-component",
                "passed": has_parser,
                "details": f"Parser: {component_info.get('parser', {}).get('class', 'None')}"
            })
            
            results["tests"].append({
                "name": "Has chunker sub-component",
                "passed": has_chunker,
                "details": f"Chunker: {component_info.get('chunker', {}).get('class', 'None')}"
            })
            
            results["tests"].append({
                "name": "Has cleaner sub-component",
                "passed": has_cleaner,
                "details": f"Cleaner: {component_info.get('cleaner', {}).get('class', 'None')}"
            })
            
            results["tests"].append({
                "name": "Has pipeline orchestrator",
                "passed": has_pipeline,
                "details": f"Pipeline: {component_info.get('pipeline', {}).get('class', 'None')}"
            })
            
            # Test adapter pattern compliance
            uses_adapter = component_info.get('parser', {}).get('class') == 'PyMuPDFAdapter'
            results["tests"].append({
                "name": "Uses adapter pattern for external libraries",
                "passed": uses_adapter,
                "details": f"Parser uses adapter: {uses_adapter}"
            })
            
            # Test direct implementation
            direct_chunker = component_info.get('chunker', {}).get('class') == 'SentenceBoundaryChunker'
            results["tests"].append({
                "name": "Uses direct implementation for algorithms",
                "passed": direct_chunker,
                "details": f"Chunker is direct implementation: {direct_chunker}"
            })
            
            results["passed"] = all(test["passed"] for test in results["tests"])
            
        except Exception as e:
            results["passed"] = False
            results["issues"].append(f"Modular processor validation failed: {str(e)}")
            
        return results
    
    def _validate_interface_compliance(self) -> Dict[str, Any]:
        """Validate interface compliance."""
        results = {
            "passed": True,
            "tests": [],
            "issues": []
        }
        
        try:
            processor = ComponentFactory.create_processor("hybrid_pdf")
            
            # Test DocumentProcessor interface methods
            has_process = hasattr(processor, 'process')
            has_supported_formats = hasattr(processor, 'supported_formats')
            has_validate_document = hasattr(processor, 'validate_document')
            
            results["tests"].append({
                "name": "Implements process method",
                "passed": has_process,
                "details": f"Has process method: {has_process}"
            })
            
            results["tests"].append({
                "name": "Implements supported_formats method",
                "passed": has_supported_formats,
                "details": f"Has supported_formats method: {has_supported_formats}"
            })
            
            results["tests"].append({
                "name": "Implements validate_document method",
                "passed": has_validate_document,
                "details": f"Has validate_document method: {has_validate_document}"
            })
            
            # Test method signatures
            try:
                formats = processor.supported_formats()
                formats_valid = isinstance(formats, list) and all(isinstance(f, str) for f in formats)
                
                results["tests"].append({
                    "name": "supported_formats returns List[str]",
                    "passed": formats_valid,
                    "details": f"Returns: {formats}"
                })
                
            except Exception as e:
                results["tests"].append({
                    "name": "supported_formats callable",
                    "passed": False,
                    "details": f"Error: {str(e)}"
                })
            
            results["passed"] = all(test["passed"] for test in results["tests"])
            
        except Exception as e:
            results["passed"] = False
            results["issues"].append(f"Interface compliance validation failed: {str(e)}")
            
        return results
    
    def _validate_adapter_pattern(self) -> Dict[str, Any]:
        """Validate adapter pattern implementation."""
        results = {
            "passed": True,
            "tests": [],
            "issues": []
        }
        
        try:
            processor = ComponentFactory.create_processor("hybrid_pdf")
            component_info = processor.get_component_info()
            
            # According to architecture spec, adapters should be used for external libraries
            # Direct implementation should be used for algorithms
            
            # Parser should use adapter (external library: PyMuPDF)
            parser_uses_adapter = component_info.get('parser', {}).get('class') == 'PyMuPDFAdapter'
            
            results["tests"].append({
                "name": "Parser uses adapter pattern (external library)",
                "passed": parser_uses_adapter,
                "details": f"Parser class: {component_info.get('parser', {}).get('class')}"
            })
            
            # Chunker should use direct implementation (algorithm)
            chunker_direct = component_info.get('chunker', {}).get('class') == 'SentenceBoundaryChunker'
            
            results["tests"].append({
                "name": "Chunker uses direct implementation (algorithm)",
                "passed": chunker_direct,
                "details": f"Chunker class: {component_info.get('chunker', {}).get('class')}"
            })
            
            # Cleaner should use direct implementation (algorithm)
            cleaner_direct = component_info.get('cleaner', {}).get('class') == 'TechnicalContentCleaner'
            
            results["tests"].append({
                "name": "Cleaner uses direct implementation (algorithm)",
                "passed": cleaner_direct,
                "details": f"Cleaner class: {component_info.get('cleaner', {}).get('class')}"
            })
            
            results["passed"] = all(test["passed"] for test in results["tests"])
            
        except Exception as e:
            results["passed"] = False
            results["issues"].append(f"Adapter pattern validation failed: {str(e)}")
            
        return results
    
    def _validate_configuration_schema(self) -> Dict[str, Any]:
        """Validate configuration schema compliance."""
        results = {
            "passed": True,
            "tests": [],
            "issues": []
        }
        
        try:
            processor = ComponentFactory.create_processor("hybrid_pdf", chunk_size=1024, chunk_overlap=200)
            config = processor.get_config()
            
            # Test configuration structure
            has_parser_config = "parser" in config
            has_chunker_config = "chunker" in config
            has_cleaner_config = "cleaner" in config
            has_pipeline_config = "pipeline" in config
            
            results["tests"].append({
                "name": "Configuration has parser section",
                "passed": has_parser_config,
                "details": f"Has parser config: {has_parser_config}"
            })
            
            results["tests"].append({
                "name": "Configuration has chunker section",
                "passed": has_chunker_config,
                "details": f"Has chunker config: {has_chunker_config}"
            })
            
            results["tests"].append({
                "name": "Configuration has cleaner section",
                "passed": has_cleaner_config,
                "details": f"Has cleaner config: {has_cleaner_config}"
            })
            
            results["tests"].append({
                "name": "Configuration has pipeline section",
                "passed": has_pipeline_config,
                "details": f"Has pipeline config: {has_pipeline_config}"
            })
            
            # Test legacy parameter handling
            chunk_size_applied = config.get('chunker', {}).get('config', {}).get('chunk_size') == 1024
            chunk_overlap_applied = config.get('chunker', {}).get('config', {}).get('overlap') == 200
            
            results["tests"].append({
                "name": "Legacy chunk_size parameter applied",
                "passed": chunk_size_applied,
                "details": f"Chunk size: {config.get('chunker', {}).get('config', {}).get('chunk_size')}"
            })
            
            results["tests"].append({
                "name": "Legacy chunk_overlap parameter applied",
                "passed": chunk_overlap_applied,
                "details": f"Chunk overlap: {config.get('chunker', {}).get('config', {}).get('overlap')}"
            })
            
            results["passed"] = all(test["passed"] for test in results["tests"])
            
        except Exception as e:
            results["passed"] = False
            results["issues"].append(f"Configuration schema validation failed: {str(e)}")
            
        return results
    
    def _validate_system_integration(self) -> Dict[str, Any]:
        """Validate system integration."""
        results = {
            "passed": True,
            "tests": [],
            "issues": []
        }
        
        try:
            # Test platform orchestrator can create system with modular processor
            orchestrator = PlatformOrchestrator(self.config_path)
            
            # Test system health
            health = orchestrator.get_system_health()
            # Check if system is properly initialized with modular processor
            processor = orchestrator._components.get('document_processor')
            is_modular = processor.__class__.__name__ == 'ModularDocumentProcessor'
            system_initialized = health.get('initialized', False) or len(health.get('components', {})) > 0
            
            results["tests"].append({
                "name": "Platform orchestrator initializes with modular processor",
                "passed": is_modular and system_initialized,
                "details": f"Processor: {processor.__class__.__name__}, Initialized: {system_initialized}"
            })
            
            # Test processor functionality without requiring actual PDF
            try:
                # Test supported formats
                formats = processor.supported_formats()
                formats_valid = isinstance(formats, list) and len(formats) > 0
                
                # Test component info
                component_info = processor.get_component_info()
                has_all_components = all(comp in component_info for comp in ['parser', 'chunker', 'cleaner', 'pipeline'])
                
                # Test validation (should work without actual file)
                fake_pdf = Path("nonexistent.pdf")
                validation = processor.validate_document(fake_pdf)
                validation_works = hasattr(validation, 'valid') and hasattr(validation, 'errors')
                
                functionality_works = formats_valid and has_all_components and validation_works
                
                results["tests"].append({
                    "name": "Document processor functionality verified",
                    "passed": functionality_works,
                    "details": f"Formats: {len(formats)}, Components: {len(component_info)}, Validation: {validation_works}"
                })
                
            except Exception as e:
                results["tests"].append({
                    "name": "Document processor functionality verified",
                    "passed": False,
                    "details": f"Error: {str(e)}"
                })
            
            results["passed"] = all(test["passed"] for test in results["tests"])
            
        except Exception as e:
            results["passed"] = False
            results["issues"].append(f"System integration validation failed: {str(e)}")
            
        return results
    
    def _calculate_compliance_score(self, validation_results: Dict[str, Any]) -> float:
        """Calculate overall compliance score."""
        total_tests = 0
        passed_tests = 0
        
        for component, results in validation_results.items():
            if "tests" in results:
                total_tests += len(results["tests"])
                passed_tests += sum(1 for test in results["tests"] if test["passed"])
        
        return (passed_tests / total_tests * 100) if total_tests > 0 else 0
    
    def _generate_compliance_summary(self, results: Dict[str, Any]) -> None:
        """Generate compliance summary."""
        print(f"\n" + "="*80)
        print("ARCHITECTURE COMPLIANCE VALIDATION SUMMARY")
        print("="*80)
        
        print(f"📊 Overall Compliance Score: {results['compliance_score']:.1f}%")
        
        for component, component_results in results["validation_results"].items():
            status = "✅ PASSED" if component_results["passed"] else "❌ FAILED"
            print(f"  {component.replace('_', ' ').title()}: {status}")
            
            if component_results.get("issues"):
                for issue in component_results["issues"]:
                    print(f"    ⚠️  {issue}")
        
        if results["compliance_score"] >= 95:
            print("\n🎉 EXCELLENT: Architecture fully compliant with specifications!")
        elif results["compliance_score"] >= 80:
            print("\n✅ GOOD: Architecture mostly compliant, minor issues to address")
        elif results["compliance_score"] >= 60:
            print("\n⚠️  FAIR: Architecture partially compliant, significant improvements needed")
        else:
            print("\n❌ POOR: Architecture non-compliant, major rework required")
        
        print("="*80)


def main():
    """Run architecture compliance validation."""
    validator = ArchitectureValidator()
    results = validator.validate_architecture_compliance()
    
    # Save results
    results_file = Path("architecture_compliance_results.json")
    with open(results_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"\n📁 Detailed results saved to: {results_file}")
    
    # Return exit code based on compliance
    compliance_score = results["compliance_score"]
    if compliance_score >= 95:
        return 0  # Excellent
    elif compliance_score >= 80:
        return 0  # Good enough
    else:
        return 1  # Needs improvement


if __name__ == "__main__":
    sys.exit(main())