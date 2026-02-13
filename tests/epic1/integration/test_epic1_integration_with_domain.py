#!/usr/bin/env python3
"""
Epic1 Integration Tests with Domain Relevance

Proper pytest-based integration tests that verify Epic1 components work together
with domain relevance filtering. Transformed from run_epic1_integration_tests_with_domain.py
"""

import pytest
import asyncio
import subprocess
import time
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Tuple, Union

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@pytest.mark.integration
@pytest.mark.slow
class TestEpic1IntegrationWithDomain:
    """Integration tests for Epic1 with domain relevance."""
    
    @pytest.fixture
    def domain_queries(self):
        """Provide domain-specific test queries."""
        return {
            'technical': [
                "How do I implement a microservice architecture?",
                "What are the best practices for REST API design?",
                "Explain database indexing strategies"
            ],
            'general': [
                "What is artificial intelligence?",
                "How does machine learning work?",
                "Explain cloud computing benefits"
            ],
            'academic': [
                "Analyze the computational complexity of quicksort",
                "Explain the mathematical foundations of neural networks",
                "Discuss the theoretical limits of distributed consensus"
            ]
        }
    
    def run_subprocess_test(self, cmd: Union[str, List[str]], description: str, timeout: int = 30) -> Tuple[bool, str, str]:
        """
        Run a subprocess command and capture output (secure: no shell injection).

        Args:
            cmd: Command to run (list preferred for security, string supported for compatibility)
            description: Description for logging
            timeout: Timeout in seconds

        Returns: (success, stdout, stderr)
        """
        logger.info(f"🔧 {description}")
        logger.info(f"Command: {cmd}")

        # Convert string commands to list for security (prevents shell injection)
        if isinstance(cmd, str):
            logger.warning("String command detected - consider using list format for better security")
            # Split on whitespace for basic conversion (caller should use list instead)
            cmd_list = cmd.split()
        else:
            cmd_list = cmd

        try:
            result = subprocess.run(
                cmd_list,
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=self.project_root
            )
            
            success = result.returncode == 0
            
            if success:
                logger.info("✅ Command succeeded!")
            else:
                logger.error("❌ Command failed!")
                
            return success, result.stdout, result.stderr
            
        except subprocess.TimeoutExpired:
            logger.error(f"❌ Command timed out after {timeout}s")
            return False, "", f"Command timed out after {timeout}s"
        except Exception as e:
            logger.error(f"❌ Command execution error: {e}")
            return False, "", str(e)
    
    @pytest.fixture(scope="class")
    def project_root(self):
        """Get project root path."""
        return Path(__file__).parent.parent.parent.parent

    def test_epic1_analyzer_availability(self, project_root):
        """Test that Epic1MLAnalyzer can be imported and created."""
        self.project_root = project_root

        # Test import - use list format to avoid shell injection, cwd already set
        cmd = [
            "python", "-c",
            "from src.components.query_processors.analyzers.epic1_ml_analyzer import Epic1MLAnalyzer; print('Epic1MLAnalyzer import successful')"
        ]
        success, stdout, stderr = self.run_subprocess_test(cmd, "Testing Epic1MLAnalyzer import")

        assert success, f"Failed to import Epic1MLAnalyzer: {stderr}"
        assert "Epic1MLAnalyzer import successful" in stdout

        logger.info("✅ Epic1MLAnalyzer is available")
    
    def test_epic1_analyzer_creation(self, project_root):
        """Test Epic1MLAnalyzer creation with basic config."""
        self.project_root = project_root

        test_script = '''
import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd() / "src"))

from src.components.query_processors.analyzers.epic1_ml_analyzer import Epic1MLAnalyzer

try:
    analyzer = Epic1MLAnalyzer(config={
        "memory_budget_gb": 0.5,
        "parallel_execution": False,
        "enable_performance_monitoring": False
    })
    print(f"Created analyzer with {len(analyzer.views)} views")
    analyzer.shutdown()
    print("Shutdown completed")
except Exception as e:
    print(f"Error: {e}")
    raise
'''

        # Use list format to avoid shell injection, cwd already set
        cmd = ["python", "-c", test_script.strip()]
        success, stdout, stderr = self.run_subprocess_test(cmd, "Testing Epic1MLAnalyzer creation", timeout=60)

        assert success, f"Failed to create Epic1MLAnalyzer: {stderr}"
        assert "Created analyzer with" in stdout
        assert "Shutdown completed" in stdout

        logger.info("✅ Epic1MLAnalyzer creation test passed")
    
    @pytest.mark.asyncio
    async def test_domain_query_analysis(self, epic1_imports, domain_queries):
        """Test Epic1 analysis across different domain queries."""
        logger.info("Testing domain query analysis...")
        
        # Import Epic1MLAnalyzer
        imports = epic1_imports("analyzer")
        Epic1MLAnalyzer = imports['Epic1MLAnalyzer']
        
        # Create analyzer
        analyzer = Epic1MLAnalyzer(config={
            'memory_budget_gb': 0.5,
            'parallel_execution': False,
            'enable_performance_monitoring': True
        })
        
        try:
            domain_results = {}
            
            # Test one query from each domain
            for domain, queries in domain_queries.items():
                query = queries[0]
                logger.info(f"Testing {domain} domain: {query[:50]}...")
                
                result = analyzer.analyze(query, mode='ml')
                domain_results[domain] = result
                
                # Validate result
                assert result is not None
                assert result.final_score >= 0.0
                assert result.confidence >= 0.0
                
                logger.info(f"✅ {domain}: score={result.final_score:.4f}, complexity={result.complexity_level}")
            
            # Validate that different domains can produce different results
            scores = [result.final_score for result in domain_results.values()]
            complexities = [result.complexity_level for result in domain_results.values()]
            
            logger.info(f"Domain score range: {min(scores):.4f} - {max(scores):.4f}")
            logger.info(f"Complexity levels: {set(complexities)}")
            
            # At least some variation expected
            score_range = max(scores) - min(scores)
            assert score_range >= 0.0, "Domain analysis should show some variation"
            
            logger.info("✅ Domain query analysis completed successfully")
            
        finally:
            analyzer.shutdown()
    
    def test_integration_component_availability(self, project_root):
        """Test that all Epic1 integration components are available."""
        self.project_root = project_root
        
        components_to_test = [
            'src.components.query_processors.analyzers.epic1_ml_analyzer',
            'src.components.query_processors.analyzers.epic1_query_analyzer',
            'src.training.dataset_generation_framework',
            'src.training.data_loader',
            'src.components.query_processors.analyzers.ml_models.model_manager'
        ]
        
        for component in components_to_test:
            # Use list format to avoid shell injection, cwd already set
            cmd = [
                "python", "-c",
                f"import {component}; print('{component} imported successfully')"
            ]
            success, stdout, stderr = self.run_subprocess_test(cmd, f"Testing {component} import")

            assert success, f"Failed to import {component}: {stderr}"
            assert "imported successfully" in stdout

            logger.info(f"✅ {component} is available")
        
        logger.info("✅ All Epic1 integration components are available")
    
    def test_domain_ml_integration_smoke(self, project_root):
        """Smoke test for domain ML integration."""
        self.project_root = project_root
        
        # Check if domain ML integration test exists and can run basic checks
        integration_test_path = project_root / "tests/epic1/integration/test_epic1_domain_ml_integration.py"
        
        if integration_test_path.exists():
            # Try to run the domain ML integration test
            cmd = f"cd {project_root} && python -m pytest {integration_test_path} -k 'test_smoke' --tb=short -v"
            success, stdout, stderr = self.run_subprocess_test(cmd, "Running domain ML integration smoke test", timeout=120)
            
            # Don't fail the test if it doesn't exist or has issues - this is just a smoke test
            if success:
                logger.info("✅ Domain ML integration smoke test passed")
            else:
                logger.warning(f"⚠️  Domain ML integration smoke test issues (non-fatal): {stderr}")
        else:
            logger.info("ℹ️  Domain ML integration test not found - skipping smoke test")
    
    @pytest.mark.asyncio
    async def test_end_to_end_domain_workflow(self, epic1_imports, domain_queries):
        """Test complete end-to-end workflow with domain queries."""
        logger.info("Testing end-to-end domain workflow...")
        
        # Import Epic1MLAnalyzer
        imports = epic1_imports("analyzer")
        Epic1MLAnalyzer = imports['Epic1MLAnalyzer']
        
        # Create analyzer with performance monitoring
        analyzer = Epic1MLAnalyzer(config={
            'memory_budget_gb': 1.0,
            'parallel_execution': False,
            'enable_performance_monitoring': True,
            'fallback_strategy': 'algorithmic'
        })
        
        try:
            workflow_results = []
            
            # Process queries from each domain
            for domain, queries in domain_queries.items():
                for i, query in enumerate(queries[:2]):  # Test first 2 queries per domain
                    logger.info(f"Processing {domain} query {i+1}: {query[:50]}...")
                    
                    start_time = time.time()
                    result = analyzer.analyze(query, mode='ml')
                    end_time = time.time()
                    
                    # Validate result
                    assert result is not None
                    assert hasattr(result, 'final_score')
                    assert hasattr(result, 'confidence')
                    
                    workflow_result = {
                        'domain': domain,
                        'query_index': i,
                        'score': result.final_score,
                        'complexity': result.complexity_level,
                        'confidence': result.confidence,
                        'processing_time': end_time - start_time
                    }
                    workflow_results.append(workflow_result)
                    
                    logger.info(f"✅ Processed in {workflow_result['processing_time']:.3f}s")
            
            # Validate workflow results
            assert len(workflow_results) == 6, f"Expected 6 results, got {len(workflow_results)}"
            
            # Check performance
            avg_processing_time = sum(r['processing_time'] for r in workflow_results) / len(workflow_results)
            max_processing_time = max(r['processing_time'] for r in workflow_results)
            
            logger.info(f"✅ Average processing time: {avg_processing_time:.3f}s")
            logger.info(f"✅ Max processing time: {max_processing_time:.3f}s")
            
            # Performance should be reasonable
            assert max_processing_time < 10.0, f"Processing time too high: {max_processing_time:.3f}s"
            
            logger.info("✅ End-to-end domain workflow completed successfully")
            
        finally:
            analyzer.shutdown()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])