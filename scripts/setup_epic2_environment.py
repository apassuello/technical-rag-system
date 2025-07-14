#!/usr/bin/env python3
"""
Epic 2 Environment Setup Automation
Complete setup script for Epic 2 Advanced Hybrid Retriever environment.
"""

import os
import sys
import time
import subprocess
import json
import requests
from pathlib import Path
from typing import Dict, List, Any, Optional

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

def log_info(message: str):
    """Log info message with timestamp."""
    print(f"[INFO] {time.strftime('%H:%M:%S')} - {message}")

def log_success(message: str):
    """Log success message."""
    print(f"✅ {message}")

def log_error(message: str):
    """Log error message."""
    print(f"❌ {message}")

def log_warning(message: str):
    """Log warning message."""
    print(f"⚠️  {message}")

def run_command(cmd: List[str], description: str, timeout: int = 300) -> bool:
    """Run a command with timeout and logging."""
    log_info(f"Running: {description}")
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        if result.returncode == 0:
            log_success(f"{description} completed successfully")
            return True
        else:
            log_error(f"{description} failed: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        log_error(f"{description} timed out after {timeout} seconds")
        return False
    except FileNotFoundError:
        log_error(f"Command not found: {cmd[0]}")
        return False

def check_prerequisites() -> Dict[str, bool]:
    """Check system prerequisites."""
    log_info("Checking system prerequisites...")
    
    prereqs = {
        "python": False,
        "pip": False,
        "docker": False,
        "docker_compose": False,
        "git": False
    }
    
    # Check Python
    try:
        result = subprocess.run([sys.executable, "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            version = result.stdout.strip()
            log_success(f"Python available: {version}")
            prereqs["python"] = True
    except Exception:
        log_error("Python not available")
    
    # Check pip
    try:
        result = subprocess.run([sys.executable, "-m", "pip", "--version"], capture_output=True, text=True)
        if result.returncode == 0:
            log_success("pip available")
            prereqs["pip"] = True
    except Exception:
        log_error("pip not available")
    
    # Check Docker
    try:
        result = subprocess.run(["docker", "--version"], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            log_success("Docker available")
            prereqs["docker"] = True
    except Exception:
        log_error("Docker not available")
    
    # Check Docker Compose
    try:
        # Try both docker-compose and docker compose
        compose_cmd = None
        for cmd in [["docker", "compose", "version"], ["docker-compose", "--version"]]:
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    compose_cmd = cmd[0:2] if len(cmd) > 2 else [cmd[0]]
                    break
            except Exception:
                continue
        
        if compose_cmd:
            log_success("Docker Compose available")
            prereqs["docker_compose"] = True
        else:
            log_error("Docker Compose not available")
    except Exception:
        log_error("Docker Compose check failed")
    
    # Check Git
    try:
        result = subprocess.run(["git", "--version"], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            log_success("Git available")
            prereqs["git"] = True
    except Exception:
        log_error("Git not available")
    
    return prereqs

def install_python_dependencies() -> bool:
    """Install Epic 2 Python dependencies."""
    log_info("Installing Epic 2 Python dependencies...")
    
    # Core dependencies for Epic 2
    epic2_dependencies = [
        "weaviate-client>=3.24.0",
        "networkx>=3.1",
        "plotly>=5.17.0", 
        "dash>=2.14.0",
        "sentence-transformers>=2.2.0",
        "transformers>=4.30.0",
        "torch>=2.0.0",
        "faiss-cpu>=1.7.0",
        "requests>=2.31.0",
        "pyyaml>=6.0.0",
        "numpy>=1.24.0",
        "scikit-learn>=1.3.0"
    ]
    
    for dependency in epic2_dependencies:
        log_info(f"Installing {dependency}...")
        if not run_command([sys.executable, "-m", "pip", "install", dependency], 
                          f"pip install {dependency}", timeout=120):
            log_warning(f"Failed to install {dependency}, continuing...")
    
    # Install additional requirements if file exists
    requirements_file = project_root / "requirements.txt"
    if requirements_file.exists():
        log_info("Installing from requirements.txt...")
        return run_command([sys.executable, "-m", "pip", "install", "-r", str(requirements_file)],
                          "pip install requirements.txt")
    
    return True

def start_docker_services() -> Dict[str, bool]:
    """Start Docker services for Epic 2."""
    log_info("Starting Docker services for Epic 2...")
    
    os.chdir(project_root)
    
    services = {
        "weaviate": False,
        "ollama": False
    }
    
    # Check if docker-compose.yml exists
    compose_file = project_root / "docker-compose.yml"
    if not compose_file.exists():
        log_error("docker-compose.yml not found")
        return services
    
    # Determine docker compose command
    compose_cmd = ["docker", "compose"]
    try:
        result = subprocess.run(["docker", "compose", "version"], capture_output=True, timeout=5)
        if result.returncode != 0:
            compose_cmd = ["docker-compose"]
    except Exception:
        compose_cmd = ["docker-compose"]
    
    # Start services
    log_info("Starting Weaviate and Ollama services...")
    if run_command(compose_cmd + ["up", "-d", "weaviate", "ollama"], 
                   "docker-compose up weaviate ollama", timeout=180):
        
        # Wait for services to be ready
        log_info("Waiting for services to be ready...")
        
        # Check Weaviate
        for attempt in range(30):  # 30 attempts, 5 seconds each = 2.5 minutes
            try:
                response = requests.get("http://localhost:8080/v1/.well-known/ready", timeout=5)
                if response.status_code == 200:
                    log_success("Weaviate is ready")
                    services["weaviate"] = True
                    break
            except requests.RequestException:
                pass
            
            if attempt < 29:
                time.sleep(5)
        
        if not services["weaviate"]:
            log_warning("Weaviate did not become ready within timeout")
        
        # Check Ollama
        for attempt in range(20):  # 20 attempts, 3 seconds each = 1 minute
            try:
                response = requests.get("http://localhost:11434/api/version", timeout=5)
                if response.status_code == 200:
                    log_success("Ollama is ready")
                    services["ollama"] = True
                    break
            except requests.RequestException:
                pass
            
            if attempt < 19:
                time.sleep(3)
        
        if not services["ollama"]:
            log_warning("Ollama did not become ready within timeout")
    
    return services

def download_ollama_models() -> bool:
    """Download required Ollama models."""
    log_info("Downloading Ollama models for Epic 2...")
    
    # Check if Ollama is available
    try:
        response = requests.get("http://localhost:11434/api/version", timeout=10)
        if response.status_code != 200:
            log_warning("Ollama not available, skipping model download")
            return False
    except requests.RequestException:
        log_warning("Ollama not accessible, skipping model download")
        return False
    
    # Download llama3.2:3b model (used in Epic 2 configurations)
    log_info("Downloading llama3.2:3b model...")
    return run_command(["docker", "exec", "rag_ollama", "ollama", "pull", "llama3.2:3b"],
                      "ollama pull llama3.2:3b", timeout=600)

def validate_epic2_components() -> Dict[str, bool]:
    """Validate Epic 2 components can be imported and created."""
    log_info("Validating Epic 2 components...")
    
    validation = {
        "component_factory": False,
        "advanced_retriever": False,
        "weaviate_backend": False,
        "neural_reranking": False,
        "graph_components": False
    }
    
    try:
        # Test ComponentFactory
        from src.core.component_factory import ComponentFactory
        factory = ComponentFactory()
        log_success("ComponentFactory imported and created")
        validation["component_factory"] = True
        
        # Test AdvancedRetriever creation
        try:
            config = {
                "backends": {
                    "primary_backend": "faiss",
                    "faiss": {"index_type": "IndexFlatIP", "metric": "cosine"}
                }
            }
            retriever = factory.create_retriever("advanced", config=config)
            if type(retriever).__name__ == "AdvancedRetriever":
                log_success("AdvancedRetriever created successfully")
                validation["advanced_retriever"] = True
        except Exception as e:
            log_warning(f"AdvancedRetriever creation failed: {e}")
        
        # Test Weaviate backend
        try:
            from src.components.retrievers.backends.weaviate_backend import WeaviateBackend
            log_success("WeaviateBackend imported successfully")
            validation["weaviate_backend"] = True
        except Exception as e:
            log_warning(f"WeaviateBackend import failed: {e}")
        
        # Test neural reranking components
        try:
            from src.components.retrievers.rerankers.neural_reranker import NeuralReranker
            log_success("NeuralReranker imported successfully")
            validation["neural_reranking"] = True
        except Exception as e:
            log_warning(f"NeuralReranker import failed: {e}")
        
        # Test graph components
        try:
            from src.components.retrievers.graph.document_graph_builder import DocumentGraphBuilder
            log_success("Graph components imported successfully")
            validation["graph_components"] = True
        except Exception as e:
            log_warning(f"Graph components import failed: {e}")
    
    except Exception as e:
        log_error(f"Component validation failed: {e}")
    
    return validation

def run_epic2_tests() -> Dict[str, Any]:
    """Run Epic 2 validation tests."""
    log_info("Running Epic 2 validation tests...")
    
    test_results = {
        "component_factory": False,
        "configuration_loading": False,
        "epic2_diagnostic": False
    }
    
    # Test component factory validation
    factory_test_script = project_root / "test_component_factory_validation.py"
    if factory_test_script.exists():
        log_info("Running component factory validation...")
        if run_command([sys.executable, str(factory_test_script)], 
                      "Component Factory Validation", timeout=120):
            test_results["component_factory"] = True
    
    # Test configuration loading
    try:
        from src.core.platform_orchestrator import PlatformOrchestrator
        
        # Test Epic 2 configurations
        epic2_configs = [
            "config/epic2_comprehensive_test.yaml",
            "config/epic2_diagnostic_test.yaml",
            "config/advanced_test.yaml"
        ]
        
        config_loaded = False
        for config_file in epic2_configs:
            config_path = project_root / config_file
            if config_path.exists():
                try:
                    po = PlatformOrchestrator(str(config_path))
                    log_success(f"Configuration loaded: {config_file}")
                    config_loaded = True
                    break
                except Exception as e:
                    log_warning(f"Configuration loading failed for {config_file}: {e}")
        
        test_results["configuration_loading"] = config_loaded
    
    except Exception as e:
        log_warning(f"Configuration test failed: {e}")
    
    # Test Epic 2 diagnostic
    diagnostic_test_script = project_root / "epic2_diagnostic_test.py"
    if diagnostic_test_script.exists():
        log_info("Running Epic 2 diagnostic test...")
        if run_command([sys.executable, str(diagnostic_test_script)], 
                      "Epic 2 Diagnostic Test", timeout=180):
            test_results["epic2_diagnostic"] = True
    
    return test_results

def generate_setup_summary(prereqs: Dict[str, bool], services: Dict[str, bool], 
                          validation: Dict[str, bool], tests: Dict[str, Any]) -> str:
    """Generate setup summary report."""
    
    report_lines = [
        "🚀 Epic 2 Environment Setup Summary",
        "=" * 50,
        f"Setup Time: {time.strftime('%Y-%m-%d %H:%M:%S')}",
        ""
    ]
    
    # Prerequisites
    prereq_count = sum(prereqs.values())
    report_lines.extend([
        f"📋 Prerequisites: {prereq_count}/{len(prereqs)}",
        f"   Python: {'✅' if prereqs.get('python') else '❌'}",
        f"   Docker: {'✅' if prereqs.get('docker') else '❌'}",
        f"   Docker Compose: {'✅' if prereqs.get('docker_compose') else '❌'}",
        ""
    ])
    
    # Services
    service_count = sum(services.values())
    report_lines.extend([
        f"🐳 Services: {service_count}/{len(services)}",
        f"   Weaviate: {'✅' if services.get('weaviate') else '❌'}",
        f"   Ollama: {'✅' if services.get('ollama') else '❌'}",
        ""
    ])
    
    # Component Validation
    validation_count = sum(validation.values())
    report_lines.extend([
        f"🔍 Components: {validation_count}/{len(validation)}",
        f"   ComponentFactory: {'✅' if validation.get('component_factory') else '❌'}",
        f"   AdvancedRetriever: {'✅' if validation.get('advanced_retriever') else '❌'}",
        f"   WeaviateBackend: {'✅' if validation.get('weaviate_backend') else '❌'}",
        f"   Neural Reranking: {'✅' if validation.get('neural_reranking') else '❌'}",
        f"   Graph Components: {'✅' if validation.get('graph_components') else '❌'}",
        ""
    ])
    
    # Tests
    test_count = sum(1 for v in tests.values() if v)
    report_lines.extend([
        f"🧪 Tests: {test_count}/{len(tests)}",
        f"   Component Factory: {'✅' if tests.get('component_factory') else '❌'}",
        f"   Configuration Loading: {'✅' if tests.get('configuration_loading') else '❌'}",
        f"   Epic 2 Diagnostic: {'✅' if tests.get('epic2_diagnostic') else '❌'}",
        ""
    ])
    
    # Overall Status
    total_checks = len(prereqs) + len(services) + len(validation) + len(tests)
    passed_checks = prereq_count + service_count + validation_count + test_count
    success_rate = (passed_checks / total_checks) * 100
    
    if success_rate >= 90:
        status = "🎉 EXCELLENT"
    elif success_rate >= 75:
        status = "✅ GOOD"
    elif success_rate >= 50:
        status = "⚠️  PARTIAL"
    else:
        status = "❌ NEEDS WORK"
    
    report_lines.extend([
        f"📊 Overall Status: {status}",
        f"   Success Rate: {success_rate:.1f}% ({passed_checks}/{total_checks})",
        ""
    ])
    
    # Next Steps
    report_lines.extend([
        "🎯 Next Steps:",
    ])
    
    if not services.get("weaviate"):
        report_lines.append("   • Start Weaviate: docker-compose up -d weaviate")
    
    if not services.get("ollama"):
        report_lines.append("   • Start Ollama: docker-compose up -d ollama")
    
    if not validation.get("advanced_retriever"):
        report_lines.append("   • Check Epic 2 component configuration")
    
    if success_rate >= 75:
        report_lines.extend([
            "   • Run Epic 2 tests: python epic2_comprehensive_integration_test.py",
            "   • See docs/WEAVIATE_SETUP.md for detailed guidance"
        ])
    
    return "\\n".join(report_lines)

def main():
    """Main setup function."""
    print("🚀 Epic 2 Environment Setup Automation")
    print("=" * 60)
    
    start_time = time.time()
    
    # Check prerequisites
    prereqs = check_prerequisites()
    
    # Install dependencies
    if prereqs.get("python") and prereqs.get("pip"):
        install_python_dependencies()
    else:
        log_error("Python/pip not available, skipping dependency installation")
    
    # Start services
    services = {"weaviate": False, "ollama": False}
    if prereqs.get("docker") and prereqs.get("docker_compose"):
        services = start_docker_services()
        
        # Download models if Ollama is running
        if services.get("ollama"):
            download_ollama_models()
    else:
        log_error("Docker/Docker Compose not available, skipping service startup")
    
    # Validate components
    validation = validate_epic2_components()
    
    # Run tests
    tests = run_epic2_tests()
    
    # Generate summary
    setup_time = time.time() - start_time
    summary = generate_setup_summary(prereqs, services, validation, tests)
    
    print("\\n" + summary)
    print(f"\\n⏱️  Total setup time: {setup_time:.1f} seconds")
    
    # Save summary to file
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    summary_file = project_root / f"epic2_setup_summary_{timestamp}.txt"
    
    with open(summary_file, 'w') as f:
        f.write(summary.replace("\\n", "\\n"))
    
    log_success(f"Setup summary saved: {summary_file}")
    
    # Exit with appropriate code
    total_success = (
        sum(prereqs.values()) >= len(prereqs) * 0.8 and
        sum(services.values()) >= 1 and  # At least one service
        sum(validation.values()) >= len(validation) * 0.6
    )
    
    sys.exit(0 if total_success else 1)

if __name__ == "__main__":
    main()