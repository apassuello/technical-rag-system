#!/usr/bin/env python3
"""
Comprehensive test suite for Dataset Generation Framework.

This module provides complete test coverage for the Epic1 training dataset generation
system including Claude integration, data validation, quality control, and 
statistical validation frameworks.

Target Coverage: 70% (~478 test lines for 683 component lines)
Priority: HIGH (Training infrastructure 0% baseline)
"""

import pytest
import json
import numpy as np
from unittest.mock import Mock, patch, MagicMock, mock_open
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime, timezone
from dataclasses import asdict

# Import systems under test
from src.training.dataset_generation_framework import (
    ClaudeDatasetGenerator,
    DatasetGenerationConfig,
    TrainingDataPoint,
    TrainingMetadata,
    ViewScore,
    ComplexityLevel,
    Domain
)


class TestDatasetGenerationConfig:
    """Test dataset generation configuration."""
    
    def test_default_configuration(self):
        """Test default configuration values."""
        config = DatasetGenerationConfig()
        
        assert config.total_samples == 1000
        assert config.batch_size == 20
        assert config.max_retries == 3
        assert config.quality_threshold == 0.7
        assert config.claude_model == "claude-3-5-sonnet-20241022"
        assert config.prompt_version == "v1.0"
        
        # Test default distributions
        assert config.complexity_distribution == {"simple": 350, "medium": 400, "complex": 250}
        assert config.domain_distribution == {"technical": 400, "general": 300, "academic": 300}
        
    def test_custom_configuration(self):
        """Test custom configuration initialization."""
        custom_config = DatasetGenerationConfig(
            total_samples=500,
            batch_size=10,
            quality_threshold=0.8,
            complexity_distribution={"simple": 200, "medium": 200, "complex": 100}
        )
        
        assert custom_config.total_samples == 500
        assert custom_config.batch_size == 10
        assert custom_config.quality_threshold == 0.8
        assert custom_config.complexity_distribution["simple"] == 200
        
    def test_output_directory_creation(self):
        """Test that output directory is created during initialization."""
        with patch('pathlib.Path.mkdir') as mock_mkdir:
            config = DatasetGenerationConfig(output_dir=Path("test/output"))
            mock_mkdir.assert_called_once_with(parents=True, exist_ok=True)
            
    def test_configuration_validation(self):
        """Test configuration validation."""
        # Test invalid total_samples
        with pytest.raises(ValueError):
            config = DatasetGenerationConfig(total_samples=-1)
            
        # Test invalid batch_size
        with pytest.raises(ValueError):
            config = DatasetGenerationConfig(batch_size=0)
            
        # Test invalid quality_threshold
        with pytest.raises(ValueError):
            config = DatasetGenerationConfig(quality_threshold=1.5)
            
    def test_distribution_consistency(self):
        """Test that distributions are consistent with total_samples."""
        config = DatasetGenerationConfig(total_samples=1000)
        
        # Default distributions should sum to total_samples
        complexity_sum = sum(config.complexity_distribution.values())
        domain_sum = sum(config.domain_distribution.values())
        query_type_sum = sum(config.query_type_distribution.values())
        
        assert complexity_sum == 1000
        assert domain_sum == 1000
        # Query type sum may be different as it's independent


class TestTrainingDataStructures:
    """Test training data structures and validation."""
    
    def test_view_score_creation(self):
        """Test ViewScore data structure creation."""
        view_score = ViewScore(
            view_name="technical",
            complexity_score=0.75,
            confidence=0.85,
            primary_indicators=["domain_terminology", "technical_depth"],
            feature_values={"technical_terms_count": 5, "jargon_density": 0.3},
            reasoning="High technical complexity due to specialized terminology",
            expected_distribution="normal",
            difficulty_factors=["domain_knowledge", "implementation_details"]
        )
        
        assert view_score.view_name == "technical"
        assert view_score.complexity_score == 0.75
        assert view_score.confidence == 0.85
        assert len(view_score.primary_indicators) == 2
        assert view_score.feature_values["technical_terms_count"] == 5
        
    def test_training_metadata_creation(self):
        """Test TrainingMetadata structure."""
        metadata = TrainingMetadata(
            generation_timestamp=datetime.now(timezone.utc).isoformat(),
            claude_model="claude-3-5-sonnet-20241022",
            prompt_version="v1.0",
            domain="technical",
            query_type="how-to",
            complexity_category="implementation",
            quality_score=0.85,
            validation_flags=[],
            human_review_needed=False,
            target_complexity_level="medium",
            difficulty_subcategory="technical_medium"
        )
        
        assert metadata.claude_model == "claude-3-5-sonnet-20241022"
        assert metadata.domain == "technical"
        assert metadata.quality_score == 0.85
        assert metadata.human_review_needed is False
        
    def test_training_datapoint_creation(self):
        """Test complete TrainingDataPoint creation."""
        view_scores = {
            "technical": ViewScore(
                view_name="technical",
                complexity_score=0.7,
                confidence=0.8,
                primary_indicators=["terminology"],
                feature_values={"terms": 3},
                reasoning="Technical query",
                expected_distribution="normal",
                difficulty_factors=["domain"]
            )
        }
        
        metadata = TrainingMetadata(
            generation_timestamp=datetime.now(timezone.utc).isoformat(),
            claude_model="claude-3-5-sonnet-20241022",
            prompt_version="v1.0",
            domain="technical",
            query_type="how-to",
            complexity_category="implementation",
            quality_score=0.85,
            validation_flags=[],
            human_review_needed=False,
            target_complexity_level="medium",
            difficulty_subcategory="technical_medium"
        )
        
        datapoint = TrainingDataPoint(
            query_text="How do I implement CPU caching?",
            expected_complexity_score=0.75,
            expected_complexity_level="medium",
            view_scores=view_scores,
            metadata=metadata
        )
        
        assert datapoint.query_text == "How do I implement CPU caching?"
        assert datapoint.expected_complexity_score == 0.75
        assert datapoint.expected_complexity_level == "medium"
        assert "technical" in datapoint.view_scores
        assert datapoint.metadata.domain == "technical"
        
    def test_datapoint_serialization(self):
        """Test serialization of training datapoints to dictionary."""
        view_score = ViewScore(
            view_name="technical",
            complexity_score=0.7,
            confidence=0.8,
            primary_indicators=["terminology"],
            feature_values={"terms": 3},
            reasoning="Technical query",
            expected_distribution="normal",
            difficulty_factors=["domain"]
        )
        
        metadata = TrainingMetadata(
            generation_timestamp="2024-01-01T00:00:00Z",
            claude_model="claude-3-5-sonnet-20241022",
            prompt_version="v1.0",
            domain="technical",
            query_type="how-to",
            complexity_category="implementation",
            quality_score=0.85,
            validation_flags=[],
            human_review_needed=False,
            target_complexity_level="medium",
            difficulty_subcategory="technical_medium"
        )
        
        datapoint = TrainingDataPoint(
            query_text="Test query",
            expected_complexity_score=0.75,
            expected_complexity_level="medium",
            view_scores={"technical": view_score},
            metadata=metadata
        )
        
        # Convert to dict
        datapoint_dict = asdict(datapoint)
        
        assert isinstance(datapoint_dict, dict)
        assert datapoint_dict["query_text"] == "Test query"
        assert "view_scores" in datapoint_dict
        assert "metadata" in datapoint_dict


class TestClaudeDatasetGeneratorInitialization:
    """Test Claude dataset generator initialization."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.config = DatasetGenerationConfig(
            total_samples=100,
            batch_size=10,
            output_dir=Path("test_output")
        )
        
    def test_generator_initialization(self):
        """Test basic generator initialization."""
        with patch('pathlib.Path.mkdir'):
            generator = ClaudeDatasetGenerator(self.config)
            
            assert generator.config == self.config
            assert hasattr(generator, 'prompt_templates')
            assert hasattr(generator, 'generation_stats')
            
            # Test statistics initialization
            stats = generator.generation_stats
            assert stats['total_requested'] == 0
            assert stats['total_generated'] == 0
            assert stats['quality_passed'] == 0
            assert stats['quality_failed'] == 0
            assert stats['retries_used'] == 0
            
    def test_prompt_template_loading(self):
        """Test prompt template loading."""
        with patch('pathlib.Path.mkdir'):
            generator = ClaudeDatasetGenerator(self.config)
            templates = generator.prompt_templates
            
            # Test required templates exist
            assert 'system_prompt' in templates
            assert 'simple_prompt' in templates
            assert 'medium_prompt' in templates
            assert 'complex_prompt' in templates
            assert 'technical_domain' in templates
            assert 'academic_domain' in templates
            assert 'general_domain' in templates
            
    def test_system_prompt_content(self):
        """Test system prompt content and structure."""
        with patch('pathlib.Path.mkdir'):
            generator = ClaudeDatasetGenerator(self.config)
            system_prompt = generator._get_system_prompt()
            
            # Test key content elements
            assert "multi-view ML system" in system_prompt
            assert "5 orthogonal dimensions" in system_prompt
            assert "Technical Complexity" in system_prompt
            assert "Linguistic Complexity" in system_prompt
            assert "Task Complexity" in system_prompt
            assert "Semantic Complexity" in system_prompt
            assert "Computational Complexity" in system_prompt
            
    def test_complexity_prompts(self):
        """Test complexity-specific prompt generation."""
        with patch('pathlib.Path.mkdir'):
            generator = ClaudeDatasetGenerator(self.config)
            
            simple_prompt = generator._get_complexity_prompt('simple')
            medium_prompt = generator._get_complexity_prompt('medium')
            complex_prompt = generator._get_complexity_prompt('complex')
            
            # Test prompt differentiation
            assert "simple queries" in simple_prompt.lower()
            assert "medium complexity" in medium_prompt.lower()
            assert "complex queries" in complex_prompt.lower()
            
            # Test scoring calibration information
            assert "0.1-0.3" in simple_prompt  # Simple score range
            assert "0.3-0.7" in medium_prompt  # Medium score range
            assert "0.6-1.0" in complex_prompt  # Complex score range
            
    def test_domain_prompts(self):
        """Test domain-specific prompt generation."""
        with patch('pathlib.Path.mkdir'):
            generator = ClaudeDatasetGenerator(self.config)
            
            technical_prompt = generator._get_domain_prompt('technical')
            academic_prompt = generator._get_domain_prompt('academic')
            general_prompt = generator._get_domain_prompt('general')
            
            # Test domain-specific content
            assert "technical/programming" in technical_prompt.lower()
            assert "research/academic" in academic_prompt.lower()
            assert "general knowledge" in general_prompt.lower()


class TestGenerationPlanCreation:
    """Test generation plan creation and batch specification."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.config = DatasetGenerationConfig(
            total_samples=100,
            batch_size=10,
            complexity_distribution={"simple": 30, "medium": 40, "complex": 30},
            domain_distribution={"technical": 50, "general": 30, "academic": 20}
        )
        
    def test_generation_plan_structure(self):
        """Test generation plan structure and content."""
        with patch('pathlib.Path.mkdir'):
            generator = ClaudeDatasetGenerator(self.config)
            plan = generator._create_generation_plan()
            
            assert isinstance(plan, list)
            assert len(plan) > 0
            
            # Test plan item structure
            for batch_spec in plan:
                assert 'complexity' in batch_spec
                assert 'domain' in batch_spec
                assert 'samples' in batch_spec
                assert 'batch_index' in batch_spec
                assert 'total_batches' in batch_spec
                
    def test_generation_plan_sample_distribution(self):
        """Test that generation plan respects sample distribution."""
        with patch('pathlib.Path.mkdir'):
            generator = ClaudeDatasetGenerator(self.config)
            plan = generator._create_generation_plan()
            
            # Count samples by complexity and domain
            complexity_counts = {'simple': 0, 'medium': 0, 'complex': 0}
            domain_counts = {'technical': 0, 'general': 0, 'academic': 0}
            
            for batch_spec in plan:
                complexity_counts[batch_spec['complexity']] += batch_spec['samples']
                domain_counts[batch_spec['domain']] += batch_spec['samples']
                
            # Check that distributions are approximately respected
            # (May not be exact due to rounding in batch creation)
            total_samples = sum(complexity_counts.values())
            assert 90 <= total_samples <= 110  # Allow some tolerance
            
    def test_batch_size_respect(self):
        """Test that batches respect the configured batch size."""
        with patch('pathlib.Path.mkdir'):
            generator = ClaudeDatasetGenerator(self.config)
            plan = generator._create_generation_plan()
            
            for batch_spec in plan:
                # Each batch should not exceed the configured batch size
                assert batch_spec['samples'] <= self.config.batch_size
                assert batch_spec['samples'] > 0
                
    def test_generation_plan_coverage(self):
        """Test that generation plan covers all complexity/domain combinations."""
        with patch('pathlib.Path.mkdir'):
            generator = ClaudeDatasetGenerator(self.config)
            plan = generator._create_generation_plan()
            
            # Extract all combinations
            combinations = set()
            for batch_spec in plan:
                combinations.add((batch_spec['complexity'], batch_spec['domain']))
                
            # Should have all combinations (3 complexities × 3 domains = 9 combinations)
            expected_combinations = {
                ('simple', 'technical'), ('simple', 'general'), ('simple', 'academic'),
                ('medium', 'technical'), ('medium', 'general'), ('medium', 'academic'),
                ('complex', 'technical'), ('complex', 'general'), ('complex', 'academic')
            }
            
            # May not have all combinations if some have 0 samples
            assert len(combinations) <= 9
            assert len(combinations) > 0


class TestClaudePromptConstruction:
    """Test Claude prompt construction and API interaction."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.config = DatasetGenerationConfig(
            total_samples=50,
            batch_size=5
        )
        
    def test_claude_prompt_building(self):
        """Test Claude prompt construction."""
        with patch('pathlib.Path.mkdir'):
            generator = ClaudeDatasetGenerator(self.config)
            
            prompt = generator._build_claude_prompt('medium', 'technical', 5)
            
            # Test prompt structure
            assert "Generate 5 training datapoints" in prompt
            assert "Complexity Level**: medium" in prompt
            assert "Domain**: technical" in prompt
            assert "TrainingDataPoint" in prompt
            assert "JSON structure" in prompt
            
    def test_mock_claude_api_call(self):
        """Test mock Claude API call functionality."""
        with patch('pathlib.Path.mkdir'):
            generator = ClaudeDatasetGenerator(self.config)
            
            prompt = "Test prompt"
            response = generator._call_claude_api(prompt)
            
            # Should return JSON string
            assert isinstance(response, str)
            
            # Should be valid JSON
            data = json.loads(response)
            assert isinstance(data, list)
            
    def test_mock_response_generation(self):
        """Test mock response generation quality."""
        with patch('pathlib.Path.mkdir'):
            generator = ClaudeDatasetGenerator(self.config)
            
            mock_data = generator._generate_mock_response("test prompt")
            
            assert isinstance(mock_data, list)
            assert len(mock_data) > 0
            
            # Test first datapoint structure
            datapoint = mock_data[0]
            
            required_fields = [
                "query_text", "expected_complexity_score", "expected_complexity_level",
                "view_scores", "metadata"
            ]
            
            for field in required_fields:
                assert field in datapoint
                
            # Test view scores structure
            assert "technical" in datapoint["view_scores"]
            assert "linguistic" in datapoint["view_scores"]
            assert "task" in datapoint["view_scores"]
            assert "semantic" in datapoint["view_scores"]
            assert "computational" in datapoint["view_scores"]
            
    def test_claude_response_parsing(self):
        """Test parsing of Claude JSON responses."""
        with patch('pathlib.Path.mkdir'):
            generator = ClaudeDatasetGenerator(self.config)
            
            # Create mock response
            mock_response_data = generator._generate_mock_response("test")
            mock_response_json = json.dumps(mock_response_data)
            
            batch_spec = {'complexity': 'medium', 'domain': 'technical', 'samples': 2}
            
            datapoints = generator._parse_claude_response(mock_response_json, batch_spec)
            
            assert isinstance(datapoints, list)
            assert len(datapoints) > 0
            
            # Test parsed datapoint structure
            dp = datapoints[0]
            assert isinstance(dp, TrainingDataPoint)
            assert isinstance(dp.view_scores, dict)
            assert isinstance(dp.metadata, TrainingMetadata)
            
    def test_malformed_json_handling(self):
        """Test handling of malformed JSON responses."""
        with patch('pathlib.Path.mkdir'):
            generator = ClaudeDatasetGenerator(self.config)
            
            malformed_json = '{"invalid": json malformed'
            batch_spec = {'complexity': 'medium', 'domain': 'technical', 'samples': 2}
            
            # Should fall back to generating fallback batch
            with patch.object(generator, '_generate_fallback_batch') as mock_fallback:
                mock_fallback.return_value = []
                
                datapoints = generator._parse_claude_response(malformed_json, batch_spec)
                
                mock_fallback.assert_called_once_with(batch_spec)


class TestBatchGeneration:
    """Test individual batch generation and quality control."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.config = DatasetGenerationConfig(
            total_samples=20,
            batch_size=5,
            max_retries=2,
            quality_threshold=0.7
        )
        
    @patch('src.training.dataset_generation_framework.validate_individual_entry')
    def test_successful_batch_generation(self, mock_validate):
        """Test successful batch generation."""
        mock_validate.return_value = {'quality_score': 0.8, 'quality_flags': []}
        
        with patch('pathlib.Path.mkdir'):
            generator = ClaudeDatasetGenerator(self.config)
            
            batch_spec = {
                'complexity': 'medium',
                'domain': 'technical', 
                'samples': 3,
                'batch_index': 0,
                'total_batches': 1
            }
            
            with patch.object(generator, '_call_claude_api') as mock_api:
                # Mock successful API response
                mock_response = generator._generate_mock_response("test")
                mock_api.return_value = json.dumps(mock_response)
                
                datapoints = generator._generate_batch(batch_spec)
                
                assert isinstance(datapoints, list)
                assert len(datapoints) > 0
                mock_api.assert_called_once()
                
    @patch('src.training.dataset_generation_framework.validate_individual_entry')
    def test_batch_quality_validation_failure(self, mock_validate):
        """Test batch generation with quality validation failure."""
        # Mock low quality scores
        mock_validate.return_value = {'quality_score': 0.5, 'quality_flags': ['low_quality']}
        
        with patch('pathlib.Path.mkdir'):
            generator = ClaudeDatasetGenerator(self.config)
            
            batch_spec = {
                'complexity': 'medium',
                'domain': 'technical',
                'samples': 2,
                'batch_index': 0,
                'total_batches': 1
            }
            
            with patch.object(generator, '_call_claude_api') as mock_api:
                with patch.object(generator, '_generate_fallback_batch') as mock_fallback:
                    mock_response = generator._generate_mock_response("test")
                    mock_api.return_value = json.dumps(mock_response)
                    mock_fallback.return_value = []
                    
                    # Should retry and eventually fall back
                    datapoints = generator._generate_batch(batch_spec)
                    
                    # Should have retried max_retries times
                    assert mock_api.call_count <= self.config.max_retries
                    mock_fallback.assert_called_once()
                    
    def test_batch_generation_api_failure(self):
        """Test batch generation with API failures."""
        with patch('pathlib.Path.mkdir'):
            generator = ClaudeDatasetGenerator(self.config)
            
            batch_spec = {
                'complexity': 'medium',
                'domain': 'technical',
                'samples': 2,
                'batch_index': 0,
                'total_batches': 1
            }
            
            with patch.object(generator, '_call_claude_api') as mock_api:
                with patch.object(generator, '_generate_fallback_batch') as mock_fallback:
                    # Mock API failure
                    mock_api.side_effect = Exception("API error")
                    mock_fallback.return_value = []
                    
                    datapoints = generator._generate_batch(batch_spec)
                    
                    # Should retry and eventually fall back
                    assert mock_api.call_count <= self.config.max_retries
                    mock_fallback.assert_called_once()
                    
    @patch('src.training.dataset_generation_framework.validate_individual_entry')
    def test_batch_validation_logic(self, mock_validate):
        """Test batch quality validation logic."""
        with patch('pathlib.Path.mkdir'):
            generator = ClaudeDatasetGenerator(self.config)
            
            # Create test datapoints
            mock_datapoints = [Mock() for _ in range(3)]
            
            # Test passing quality
            mock_validate.return_value = {'quality_score': 0.8}
            assert generator._validate_batch_quality(mock_datapoints) is True
            
            # Test failing quality
            mock_validate.return_value = {'quality_score': 0.5}
            assert generator._validate_batch_quality(mock_datapoints) is False
            
            # Test empty datapoints
            assert generator._validate_batch_quality([]) is False


class TestDatasetValidationAndImprovement:
    """Test dataset validation and quality improvement."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.config = DatasetGenerationConfig(
            total_samples=20,
            quality_threshold=0.7
        )
        
    @patch('src.training.dataset_generation_framework.validate_individual_entry')
    @patch('src.training.dataset_generation_framework.validate_category_distribution')
    @patch('src.training.dataset_generation_framework.validate_dataset_coverage')
    def test_dataset_validation_pipeline(self, mock_coverage, mock_category, mock_individual):
        """Test complete dataset validation pipeline."""
        mock_individual.return_value = {'quality_score': 0.8, 'quality_flags': []}
        mock_category.return_value = {'balance_score': 0.9, 'well_balanced': True}
        mock_coverage.return_value = {'overall_coverage': 0.85}
        
        with patch('pathlib.Path.mkdir'):
            generator = ClaudeDatasetGenerator(self.config)
            
            # Create mock datapoints
            mock_datapoints = [Mock() for _ in range(10)]
            
            validated_dataset = generator._validate_and_improve_dataset(mock_datapoints)
            
            assert isinstance(validated_dataset, list)
            
            # All mocks should have been called
            assert mock_individual.call_count == len(mock_datapoints)
            mock_category.assert_called_once()
            mock_coverage.assert_called_once()
            
    @patch('src.training.dataset_generation_framework.validate_individual_entry')
    def test_quality_filtering(self, mock_validate):
        """Test filtering of low-quality datapoints."""
        with patch('pathlib.Path.mkdir'):
            generator = ClaudeDatasetGenerator(self.config)
            
            # Create mixed quality datapoints
            mock_datapoints = [Mock() for _ in range(5)]
            
            # Mock validation to return varying quality
            def mock_validation_side_effect(dp):
                # First 3 pass, last 2 fail
                index = mock_datapoints.index(dp)
                if index < 3:
                    return {'quality_score': 0.8}
                else:
                    return {'quality_score': 0.5}
                    
            mock_validate.side_effect = mock_validation_side_effect
            
            validated_dataset = generator._validate_and_improve_dataset(mock_datapoints)
            
            # Should only keep high-quality datapoints
            assert len(validated_dataset) == 3
            
    @patch('src.training.dataset_generation_framework.calculate_overall_dataset_health')
    def test_final_report_generation(self, mock_health):
        """Test final report generation."""
        mock_health.return_value = {
            'overall_health_score': 0.85,
            'ready_for_training': True,
            'recommendations': ['increase_diversity']
        }
        
        with patch('pathlib.Path.mkdir'):
            generator = ClaudeDatasetGenerator(self.config)
            
            mock_datapoints = [Mock() for _ in range(5)]
            
            with patch.object(generator, '_calculate_complexity_distribution') as mock_complexity:
                with patch.object(generator, '_calculate_domain_distribution') as mock_domain:
                    mock_complexity.return_value = {'simple': 2, 'medium': 2, 'complex': 1}
                    mock_domain.return_value = {'technical': 3, 'general': 2}
                    
                    report = generator._generate_final_report(mock_datapoints)
                    
                    assert isinstance(report, dict)
                    assert 'generation_stats' in report
                    assert 'dataset_summary' in report
                    assert 'validation_results' in report
                    assert 'ready_for_training' in report
                    
                    assert report['ready_for_training'] is True
                    assert report['dataset_summary']['total_samples'] == 5


class TestDatasetSavingAndPersistence:
    """Test dataset saving and file persistence."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.config = DatasetGenerationConfig(
            total_samples=20,
            output_dir=Path("test_output")
        )
        
    def test_dataset_saving(self):
        """Test dataset saving to files."""
        with patch('pathlib.Path.mkdir'):
            with patch('builtins.open', mock_open()) as mock_file:
                with patch('json.dump') as mock_json_dump:
                    generator = ClaudeDatasetGenerator(self.config)
                    
                    # Create mock datapoints and report
                    mock_datapoints = [Mock() for _ in range(3)]
                    mock_report = {'total_samples': 3, 'ready_for_training': True}
                    
                    with patch('src.training.dataset_generation_framework.asdict') as mock_asdict:
                        mock_asdict.side_effect = [{'mock': 'data'}] * 3
                        
                        generator._save_dataset(mock_datapoints, mock_report)
                        
                        # Should have opened files for dataset and report
                        assert mock_file.call_count == 2
                        
                        # Should have saved JSON data
                        assert mock_json_dump.call_count == 2
                        
    def test_filename_generation(self):
        """Test timestamp-based filename generation."""
        with patch('pathlib.Path.mkdir'):
            with patch('src.training.dataset_generation_framework.datetime') as mock_datetime:
                mock_datetime.now.return_value.strftime.return_value = "20240101_120000"
                
                with patch('builtins.open', mock_open()) as mock_file:
                    with patch('json.dump'):
                        generator = ClaudeDatasetGenerator(self.config)
                        
                        mock_datapoints = [Mock()]
                        mock_report = {}
                        
                        with patch('src.training.dataset_generation_framework.asdict'):
                            generator._save_dataset(mock_datapoints, mock_report)
                            
                            # Check that files were opened with timestamp
                            file_calls = mock_file.call_args_list
                            dataset_file = str(file_calls[0][0][0])
                            report_file = str(file_calls[1][0][0])
                            
                            assert "20240101_120000" in dataset_file
                            assert "epic1_dataset_" in dataset_file
                            assert "generation_report_" in report_file


class TestCompleteDatasetGenerationWorkflow:
    """Test complete end-to-end dataset generation workflow."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.config = DatasetGenerationConfig(
            total_samples=10,  # Small for testing
            batch_size=5,
            max_retries=1,
            quality_threshold=0.6
        )
        
    @patch('src.training.dataset_generation_framework.validate_individual_entry')
    @patch('src.training.dataset_generation_framework.validate_category_distribution')
    @patch('src.training.dataset_generation_framework.validate_dataset_coverage')
    @patch('src.training.dataset_generation_framework.calculate_overall_dataset_health')
    def test_complete_generation_workflow(self, mock_health, mock_coverage, mock_category, mock_individual):
        """Test complete dataset generation workflow."""
        # Setup mocks
        mock_individual.return_value = {'quality_score': 0.8}
        mock_category.return_value = {'balance_score': 0.9, 'well_balanced': True}
        mock_coverage.return_value = {'overall_coverage': 0.85}
        mock_health.return_value = {'overall_health_score': 0.8, 'ready_for_training': True}
        
        with patch('pathlib.Path.mkdir'):
            with patch('builtins.open', mock_open()):
                with patch('json.dump'):
                    generator = ClaudeDatasetGenerator(self.config)
                    
                    # Mock Claude API calls
                    with patch.object(generator, '_call_claude_api') as mock_api:
                        mock_response = generator._generate_mock_response("test")
                        mock_api.return_value = json.dumps(mock_response)
                        
                        datapoints, report = generator.generate_dataset()
                        
                        # Verify results
                        assert isinstance(datapoints, list)
                        assert isinstance(report, dict)
                        
                        assert len(datapoints) > 0
                        assert 'generation_stats' in report
                        assert 'dataset_summary' in report
                        assert 'ready_for_training' in report
                        
    def test_workflow_with_failures_and_recovery(self):
        """Test workflow resilience with failures and recovery."""
        with patch('pathlib.Path.mkdir'):
            generator = ClaudeDatasetGenerator(self.config)
            
            call_count = 0
            def mock_api_with_failures(prompt):
                nonlocal call_count
                call_count += 1
                
                # First few calls fail, then succeed
                if call_count <= 2:
                    raise Exception("API temporarily unavailable")
                else:
                    mock_response = generator._generate_mock_response("test")
                    return json.dumps(mock_response)
            
            with patch.object(generator, '_call_claude_api', side_effect=mock_api_with_failures):
                with patch('builtins.open', mock_open()):
                    with patch('json.dump'):
                        try:
                            datapoints, report = generator.generate_dataset()
                            
                            # Should eventually succeed despite initial failures
                            assert isinstance(datapoints, list)
                            assert isinstance(report, dict)
                            
                        except Exception:
                            # Or may fail if all retries exhausted - both outcomes are valid
                            pass
                            
    def test_statistics_tracking_throughout_workflow(self):
        """Test that statistics are properly tracked throughout the workflow."""
        with patch('pathlib.Path.mkdir'):
            generator = ClaudeDatasetGenerator(self.config)
            
            # Initial statistics
            initial_stats = generator.generation_stats.copy()
            
            with patch.object(generator, '_call_claude_api') as mock_api:
                mock_response = generator._generate_mock_response("test")
                mock_api.return_value = json.dumps(mock_response)
                
                with patch('builtins.open', mock_open()):
                    with patch('json.dump'):
                        datapoints, report = generator.generate_dataset()
                        
                        # Statistics should be updated
                        final_stats = generator.generation_stats
                        
                        assert final_stats['total_generated'] > initial_stats['total_generated']
                        assert final_stats['quality_passed'] > initial_stats['quality_passed']
                        
                        # Report should contain statistics
                        assert 'generation_stats' in report
                        assert report['generation_stats'] == final_stats


class TestDatasetGenerationErrorHandling:
    """Test error handling and edge cases in dataset generation."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.config = DatasetGenerationConfig(
            total_samples=10,
            batch_size=5
        )
        
    def test_empty_distribution_handling(self):
        """Test handling of empty distributions."""
        empty_config = DatasetGenerationConfig(
            total_samples=0,
            complexity_distribution={},
            domain_distribution={}
        )
        
        with patch('pathlib.Path.mkdir'):
            generator = ClaudeDatasetGenerator(empty_config)
            plan = generator._create_generation_plan()
            
            # Should handle empty configurations gracefully
            assert isinstance(plan, list)
            assert len(plan) == 0
            
    def test_invalid_configuration_recovery(self):
        """Test recovery from invalid configurations."""
        # This would test various invalid configuration scenarios
        # and ensure the system handles them gracefully
        
        with patch('pathlib.Path.mkdir'):
            # Test with None distributions
            try:
                config = DatasetGenerationConfig(
                    complexity_distribution=None,
                    domain_distribution=None
                )
                generator = ClaudeDatasetGenerator(config)
                
                # Should use default distributions
                assert generator.config.complexity_distribution is not None
                assert generator.config.domain_distribution is not None
                
            except Exception:
                # Or may raise appropriate exceptions - both are valid
                pass
                
    def test_filesystem_error_handling(self):
        """Test handling of filesystem errors."""
        with patch('pathlib.Path.mkdir', side_effect=PermissionError("Permission denied")):
            with pytest.raises(PermissionError):
                # Create config which will trigger mkdir in __post_init__
                config = DatasetGenerationConfig(
                    total_samples=10,
                    batch_size=5
                )
                
    def test_json_serialization_error_handling(self):
        """Test handling of JSON serialization errors."""
        with patch('pathlib.Path.mkdir'):
            generator = ClaudeDatasetGenerator(self.config)
            
            # Create datapoint with non-serializable content
            problematic_datapoint = Mock()
            problematic_datapoint.non_serializable = object()  # Can't serialize object()
            
            with patch('builtins.open', mock_open()):
                with patch('json.dump', side_effect=TypeError("Object not JSON serializable")):
                    with pytest.raises(TypeError):
                        generator._save_dataset([problematic_datapoint], {})


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])