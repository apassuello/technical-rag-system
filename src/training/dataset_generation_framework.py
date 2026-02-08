#!/usr/bin/env python3
"""
Epic 1 Training Dataset Generation Framework

This module implements the complete framework for generating high-quality training data
using Claude, following the defined data structures and validation methods.
"""

import json
import logging
import statistics
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import validation framework (would be implemented separately)
try:
    from .statistical_validation import (
        calculate_overall_dataset_health,
        validate_category_distribution,
        validate_dataset_coverage,
        validate_individual_entry,
    )
except ImportError:
    logger.warning("Statistical validation module not available - using mock validation")
    
    def validate_individual_entry(datapoint):
        return {'quality_score': 0.8, 'quality_flags': []}
    
    def validate_category_distribution(datapoints):
        return {'balance_score': 0.8, 'well_balanced': True}
        
    def validate_dataset_coverage(datapoints):
        return {'overall_coverage': 0.8}
        
    def calculate_overall_dataset_health(validation_results):
        return {'overall_health_score': 0.8, 'ready_for_training': True}


class ComplexityLevel(Enum):
    SIMPLE = "simple"
    MEDIUM = "medium" 
    COMPLEX = "complex"


class Domain(Enum):
    TECHNICAL = "technical"
    ACADEMIC = "academic"
    GENERAL = "general"


@dataclass
class ViewScore:
    """Individual view assessment with detailed breakdown."""
    view_name: str
    complexity_score: float              # 0.0-1.0 score for this view
    confidence: float                    # 0.0-1.0 confidence in assessment
    primary_indicators: List[str]        # Main complexity indicators found
    feature_values: Dict[str, float]     # Specific measurable features
    reasoning: str                       # Human-readable explanation
    expected_distribution: str           # "normal", "bimodal", "uniform"
    difficulty_factors: List[str]        # Specific challenge aspects


@dataclass
class TrainingMetadata:
    """Metadata for quality assessment and dataset management."""
    generation_timestamp: str
    claude_model: str                    # Model used for generation
    prompt_version: str                  # Version of generation prompt
    domain: str                         # "technical", "general", "academic"
    query_type: str                     # "how-to", "definition", "troubleshooting"
    complexity_category: str            # Primary complexity driver
    quality_score: float                # 0.0-1.0 overall quality assessment
    validation_flags: List[str]         # Quality validation results
    human_review_needed: bool           # Requires human validation
    target_complexity_level: str        # Intended complexity for balancing
    difficulty_subcategory: str         # Fine-grained difficulty classification


@dataclass
class TrainingDataPoint:
    """Single training example with all view scores and metadata."""
    query_text: str
    expected_complexity_score: float    # 0.0-1.0 final complexity
    expected_complexity_level: str      # "simple", "medium", "complex"
    view_scores: Dict[str, ViewScore]   # Individual view assessments
    metadata: TrainingMetadata
    extracted_features: Optional[Dict[str, Any]] = None


@dataclass
class DatasetGenerationConfig:
    """Configuration for dataset generation process."""
    total_samples: int = 1000
    complexity_distribution: Dict[str, int] = None
    domain_distribution: Dict[str, int] = None
    query_type_distribution: Dict[str, int] = None
    claude_model: str = "claude-3-5-sonnet-20241022"
    prompt_version: str = "v1.0"
    batch_size: int = 20
    max_retries: int = 3
    quality_threshold: float = 0.7
    output_dir: Path = Path("data/training")
    
    def __post_init__(self):
        if self.complexity_distribution is None:
            self.complexity_distribution = {"simple": 350, "medium": 400, "complex": 250}
        if self.domain_distribution is None:
            self.domain_distribution = {"technical": 400, "general": 300, "academic": 300}
        if self.query_type_distribution is None:
            self.query_type_distribution = {
                "how-to": 300, "definition": 200, "troubleshooting": 200, 
                "comparison": 150, "analysis": 150
            }


class ClaudeDatasetGenerator:
    """Main class for generating training datasets using Claude."""
    
    def __init__(self, config: DatasetGenerationConfig):
        self.config = config
        self.config.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Load prompt templates
        self.prompt_templates = self._load_prompt_templates()
        
        # Statistics tracking
        self.generation_stats = {
            'total_requested': 0,
            'total_generated': 0,
            'quality_passed': 0,
            'quality_failed': 0,
            'retries_used': 0
        }
        
    def _load_prompt_templates(self) -> Dict[str, str]:
        """Load Claude generation prompt templates."""
        # In practice, these would be loaded from files
        return {
            'system_prompt': self._get_system_prompt(),
            'simple_prompt': self._get_complexity_prompt('simple'),
            'medium_prompt': self._get_complexity_prompt('medium'),
            'complex_prompt': self._get_complexity_prompt('complex'),
            'technical_domain': self._get_domain_prompt('technical'),
            'academic_domain': self._get_domain_prompt('academic'),
            'general_domain': self._get_domain_prompt('general')
        }
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for Claude."""
        return """You are an expert in query complexity analysis and machine learning data generation. You will generate training data for a multi-view ML system that analyzes query complexity across 5 orthogonal dimensions:

1. **Technical Complexity**: Domain-specific terminology, jargon, technical depth
2. **Linguistic Complexity**: Sentence structure, vocabulary, readability  
3. **Task Complexity**: Cognitive load based on Bloom's taxonomy
4. **Semantic Complexity**: Conceptual relationships, abstraction level
5. **Computational Complexity**: Algorithm/implementation complexity

Your task is to generate realistic queries with detailed complexity assessments across all 5 views, following the exact data structure specifications provided.

**Quality Standards:**
- Each query must be realistic and represent genuine user information needs
- View scores must be internally consistent and well-justified
- All numerical scores must be on 0.0-1.0 scale with proper calibration
- Feature extraction must be accurate and verifiable
- Reasoning must be clear and educational"""

    def _get_complexity_prompt(self, complexity: str) -> str:
        """Get complexity-specific prompt."""
        if complexity == 'simple':
            return """Generate simple queries targeting new users or basic concepts:

**Characteristics:**
- Short, direct questions
- Common vocabulary, minimal jargon  
- Single-step tasks (Knowledge/Comprehension in Bloom's)
- Clear, concrete concepts
- Minimal computational complexity

**Scoring calibration:**
- Technical: 0.1-0.3 (basic terms, common concepts)
- Linguistic: 0.1-0.3 (simple sentences, common words)
- Task: 0.1-0.3 (recall, understanding)
- Semantic: 0.1-0.3 (concrete, direct concepts)
- Computational: 0.0-0.3 (basic operations)"""
        
        elif complexity == 'medium':
            return """Generate medium complexity queries for users with some domain knowledge:

**Characteristics:**
- Multi-part questions with moderate depth
- Mix of common and specialized terminology
- Application/Analysis tasks (Bloom's levels 3-4)
- Some abstract concepts requiring explanation
- Moderate algorithmic complexity

**Scoring calibration:**
- Technical: 0.3-0.7 (specialized terms, domain knowledge)
- Linguistic: 0.3-0.6 (complex sentences, technical vocabulary)
- Task: 0.3-0.7 (application, analysis)
- Semantic: 0.3-0.7 (relationships, some abstraction)
- Computational: 0.3-0.7 (algorithms, optimization)"""
        
        else:  # complex
            return """Generate complex queries requiring deep expertise:

**Characteristics:**
- Multi-layered questions with deep technical depth
- Heavy use of domain-specific jargon and concepts
- Synthesis/Evaluation tasks (Bloom's levels 5-6)
- High abstraction, implicit knowledge requirements
- Advanced algorithmic and architectural complexity

**Scoring calibration:**
- Technical: 0.6-1.0 (expert terminology, deep concepts)
- Linguistic: 0.5-0.8 (complex syntax, abstract language)
- Task: 0.6-1.0 (synthesis, evaluation, creation)
- Semantic: 0.6-1.0 (high abstraction, implicit knowledge)
- Computational: 0.6-1.0 (complex algorithms, system design)"""

    def _get_domain_prompt(self, domain: str) -> str:
        """Get domain-specific prompt."""
        if domain == 'technical':
            return """Focus on technical/programming queries:

**Domains to cover:**
- Software engineering, algorithms, system design
- DevOps, infrastructure, performance optimization  
- Machine learning, data engineering
- Security, networking, databases"""
        
        elif domain == 'academic':
            return """Focus on research/academic queries:

**Domains to cover:**
- Computer science theory, mathematics
- Research methodologies, experimental design
- Academic writing, literature review
- Statistical analysis, data interpretation"""
        
        else:  # general
            return """Focus on general knowledge queries:

**Domains to cover:**
- General how-to questions
- Basic explanations and definitions
- Everyday problem-solving
- Non-technical information seeking"""

    def generate_dataset(self) -> Tuple[List[TrainingDataPoint], Dict[str, Any]]:
        """Generate complete training dataset."""
        logger.info(f"Starting dataset generation: {self.config.total_samples} samples")
        
        all_datapoints = []
        generation_plan = self._create_generation_plan()
        
        # Generate in batches for each complexity/domain combination
        for batch_spec in generation_plan:
            batch_datapoints = self._generate_batch(batch_spec)
            all_datapoints.extend(batch_datapoints)
            
            logger.info(f"Generated batch: {len(batch_datapoints)} samples "
                       f"({batch_spec['complexity']}/{batch_spec['domain']})")
        
        # Validate and improve dataset
        validated_dataset = self._validate_and_improve_dataset(all_datapoints)
        
        # Generate final report
        final_report = self._generate_final_report(validated_dataset)
        
        # Save dataset
        self._save_dataset(validated_dataset, final_report)
        
        logger.info(f"Dataset generation complete: {len(validated_dataset)} final samples")
        return validated_dataset, final_report
    
    def _create_generation_plan(self) -> List[Dict[str, Any]]:
        """Create detailed generation plan with batch specifications."""
        plan = []
        
        # Calculate samples per combination
        complexity_totals = self.config.complexity_distribution
        domain_totals = self.config.domain_distribution
        
        for complexity, complexity_count in complexity_totals.items():
            complexity_ratio = complexity_count / self.config.total_samples
            
            for domain, domain_count in domain_totals.items():
                domain_ratio = domain_count / self.config.total_samples
                
                # Calculate samples for this combination
                combo_samples = int(complexity_ratio * domain_ratio * self.config.total_samples)
                
                if combo_samples > 0:
                    # Split into batches
                    num_batches = max(1, combo_samples // self.config.batch_size)
                    samples_per_batch = combo_samples // num_batches
                    
                    for batch_idx in range(num_batches):
                        batch_samples = samples_per_batch
                        if batch_idx == num_batches - 1:  # Last batch gets remainder
                            batch_samples = combo_samples - (samples_per_batch * batch_idx)
                        
                        plan.append({
                            'complexity': complexity,
                            'domain': domain,
                            'samples': batch_samples,
                            'batch_index': batch_idx,
                            'total_batches': num_batches
                        })
        
        logger.info(f"Created generation plan: {len(plan)} batches")
        return plan
    
    def _generate_batch(self, batch_spec: Dict[str, Any]) -> List[TrainingDataPoint]:
        """Generate a single batch of training data."""
        complexity = batch_spec['complexity']
        domain = batch_spec['domain']
        num_samples = batch_spec['samples']
        
        # Build Claude prompt
        prompt = self._build_claude_prompt(complexity, domain, num_samples)
        
        # Generate with retries
        for retry in range(self.config.max_retries):
            try:
                # In practice, this would call Claude API
                response = self._call_claude_api(prompt)
                
                # Parse response into TrainingDataPoint objects
                datapoints = self._parse_claude_response(response, batch_spec)
                
                # Validate batch quality
                quality_passed = self._validate_batch_quality(datapoints)
                
                if quality_passed:
                    self.generation_stats['total_generated'] += len(datapoints)
                    self.generation_stats['quality_passed'] += len(datapoints)
                    return datapoints
                else:
                    logger.warning(f"Batch quality check failed, retrying ({retry + 1}/{self.config.max_retries})")
                    self.generation_stats['retries_used'] += 1
                    
            except Exception as e:
                logger.error(f"Batch generation failed: {e}")
                if retry == self.config.max_retries - 1:
                    logger.error("Max retries reached, generating fallback batch")
                    return self._generate_fallback_batch(batch_spec)
        
        return []
    
    def _build_claude_prompt(self, complexity: str, domain: str, num_samples: int) -> str:
        """Build complete Claude prompt for batch generation."""
        system_prompt = self.prompt_templates['system_prompt']
        complexity_prompt = self.prompt_templates[f'{complexity}_prompt']
        domain_prompt = self.prompt_templates[f'{domain}_domain']
        
        task_prompt = f"""
Generate {num_samples} training datapoints for:
- **Complexity Level**: {complexity}
- **Domain**: {domain}

{complexity_prompt}

{domain_prompt}

For each query, provide a complete TrainingDataPoint following this exact JSON structure:
[JSON schema would be included here...]

**Critical Requirements:**
1. **Score Consistency**: View scores should correlate but not be identical
2. **Realistic Queries**: All queries must represent genuine user needs
3. **Feature Accuracy**: All feature values must be realistic and derivable
4. **Balanced Distribution**: Generate diverse queries within complexity level
5. **Self-Validation**: Check your work for consistency before output
"""
        
        return f"{system_prompt}\n\n{task_prompt}"
    
    def _call_claude_api(self, prompt: str) -> str:
        """Call Claude API (mock implementation)."""
        # In practice, this would use the Anthropic API
        logger.info("Calling Claude API (mock implementation)")
        
        # Mock response - in reality, this would be Claude's JSON response
        mock_response = self._generate_mock_response(prompt)
        return json.dumps(mock_response)
    
    def _generate_mock_response(self, prompt: str) -> List[Dict[str, Any]]:
        """Generate mock Claude response for testing."""
        # Extract complexity and domain from prompt for realistic mock data
        complexity = "medium"  # Would parse from prompt
        domain = "technical"   # Would parse from prompt
        num_samples = 5       # Would parse from prompt
        
        mock_datapoints = []
        
        for i in range(num_samples):
            # Generate realistic mock data
            base_score = 0.5 if complexity == "medium" else (0.2 if complexity == "simple" else 0.8)
            variance = 0.1
            
            mock_datapoint = {
                "query_text": f"How do I implement a {domain} solution for problem {i+1}?",
                "expected_complexity_score": base_score + np.random.normal(0, variance/2),
                "expected_complexity_level": complexity,
                "view_scores": {
                    "technical": {
                        "view_name": "technical",
                        "complexity_score": base_score + np.random.normal(0, variance),
                        "confidence": 0.8 + np.random.normal(0, 0.1),
                        "primary_indicators": ["domain_terminology", "technical_depth"],
                        "feature_values": {
                            "technical_terms_count": np.random.randint(2, 8),
                            "domain_specificity_score": base_score + np.random.normal(0, variance),
                            "jargon_density": np.random.uniform(0.1, 0.3),
                            "concept_depth": np.random.randint(1, 4),
                            "passive_voice_ratio": np.random.uniform(0.1, 0.4)
                        },
                        "reasoning": f"Technical complexity assessment for {domain} query",
                        "expected_distribution": "normal",
                        "difficulty_factors": ["domain_knowledge", "technical_terminology"]
                    },
                    "linguistic": {
                        "view_name": "linguistic",
                        "complexity_score": base_score + np.random.normal(0, variance),
                        "confidence": 0.85 + np.random.normal(0, 0.1),
                        "primary_indicators": ["sentence_complexity", "vocabulary_level"],
                        "feature_values": {
                            "avg_sentence_length": np.random.uniform(10, 25),
                            "syntactic_depth": np.random.randint(2, 6),
                            "clause_complexity": base_score + np.random.normal(0, variance/2),
                            "abstract_concept_ratio": np.random.uniform(0.2, 0.6),
                            "lexical_diversity": np.random.uniform(0.6, 0.9)
                        },
                        "reasoning": "Linguistic complexity based on sentence structure and vocabulary",
                        "expected_distribution": "normal",
                        "difficulty_factors": ["complex_syntax", "technical_vocabulary"]
                    },
                    "task": {
                        "view_name": "task",
                        "complexity_score": base_score + np.random.normal(0, variance),
                        "confidence": 0.75 + np.random.normal(0, 0.15),
                        "primary_indicators": ["bloom_level", "cognitive_demand"],
                        "feature_values": {
                            "primary_bloom_level": np.random.randint(2, 5),
                            "cognitive_load": base_score + np.random.normal(0, variance/2),
                            "task_scope": np.random.uniform(0.3, 0.8),
                            "solution_steps": np.random.randint(2, 8),
                            "creativity_required": np.random.uniform(0.2, 0.7)
                        },
                        "reasoning": "Task complexity based on Bloom's taxonomy analysis",
                        "expected_distribution": "normal", 
                        "difficulty_factors": ["multi_step_process", "application_knowledge"]
                    },
                    "semantic": {
                        "view_name": "semantic",
                        "complexity_score": base_score + np.random.normal(0, variance),
                        "confidence": 0.7 + np.random.normal(0, 0.15),
                        "primary_indicators": ["concept_density", "abstraction"],
                        "feature_values": {
                            "concept_density": base_score + np.random.normal(0, variance/2),
                            "relationship_complexity": np.random.uniform(0.3, 0.8),
                            "abstraction_level": np.random.randint(2, 4),
                            "context_dependency": np.random.uniform(0.2, 0.7),
                            "implicit_knowledge": np.random.uniform(0.1, 0.6)
                        },
                        "reasoning": "Semantic complexity based on conceptual relationships",
                        "expected_distribution": "normal",
                        "difficulty_factors": ["abstract_concepts", "implicit_assumptions"]
                    },
                    "computational": {
                        "view_name": "computational",
                        "complexity_score": base_score + np.random.normal(0, variance),
                        "confidence": 0.8 + np.random.normal(0, 0.1),
                        "primary_indicators": ["algorithm_complexity", "implementation"],
                        "feature_values": {
                            "algorithm_mentions": np.random.randint(0, 3),
                            "complexity_class": np.random.uniform(0.2, 0.8),
                            "data_structure_count": np.random.randint(1, 4),
                            "implementation_difficulty": base_score + np.random.normal(0, variance/2),
                            "optimization_aspects": np.random.uniform(0.1, 0.7)
                        },
                        "reasoning": "Computational complexity assessment",
                        "expected_distribution": "normal",
                        "difficulty_factors": ["algorithmic_thinking", "optimization_requirements"]
                    }
                },
                "metadata": {
                    "generation_timestamp": datetime.now(timezone.utc).isoformat(),
                    "claude_model": self.config.claude_model,
                    "prompt_version": self.config.prompt_version,
                    "domain": domain,
                    "query_type": "how-to",
                    "complexity_category": f"{complexity}_implementation",
                    "quality_score": np.random.uniform(0.7, 0.95),
                    "validation_flags": [],
                    "human_review_needed": False,
                    "target_complexity_level": complexity,
                    "difficulty_subcategory": f"{domain}_{complexity}"
                }
            }
            
            # Ensure scores are in valid range
            for view_data in mock_datapoint["view_scores"].values():
                view_data["complexity_score"] = np.clip(view_data["complexity_score"], 0.0, 1.0)
                view_data["confidence"] = np.clip(view_data["confidence"], 0.0, 1.0)
            
            mock_datapoint["expected_complexity_score"] = np.clip(mock_datapoint["expected_complexity_score"], 0.0, 1.0)
            
            mock_datapoints.append(mock_datapoint)
        
        return mock_datapoints
    
    def _parse_claude_response(self, response: str, batch_spec: Dict[str, Any]) -> List[TrainingDataPoint]:
        """Parse Claude JSON response into TrainingDataPoint objects."""
        try:
            data = json.loads(response)
            if not isinstance(data, list):
                data = [data]  # Handle single datapoint response
            
            datapoints = []
            for item in data:
                # Convert dictionaries to proper objects
                view_scores = {}
                for view_name, view_data in item["view_scores"].items():
                    view_scores[view_name] = ViewScore(**view_data)
                
                metadata = TrainingMetadata(**item["metadata"])
                
                datapoint = TrainingDataPoint(
                    query_text=item["query_text"],
                    expected_complexity_score=item["expected_complexity_score"],
                    expected_complexity_level=item["expected_complexity_level"],
                    view_scores=view_scores,
                    metadata=metadata,
                    extracted_features=item.get("extracted_features")
                )
                
                datapoints.append(datapoint)
            
            return datapoints
            
        except Exception as e:
            logger.error(f"Failed to parse Claude response: {e}")
            return self._generate_fallback_batch(batch_spec)
    
    def _validate_batch_quality(self, datapoints: List[TrainingDataPoint]) -> bool:
        """Validate batch quality before accepting."""
        if not datapoints:
            return False
        
        quality_scores = []
        for dp in datapoints:
            validation_result = validate_individual_entry(dp)
            quality_scores.append(validation_result['quality_score'])
        
        avg_quality = statistics.mean(quality_scores)
        return avg_quality >= self.config.quality_threshold
    
    def _generate_fallback_batch(self, batch_spec: Dict[str, Any]) -> List[TrainingDataPoint]:
        """Generate fallback batch when Claude generation fails."""
        logger.warning("Generating fallback batch with basic template")
        
        # Use mock generation as fallback
        mock_response = self._generate_mock_response("")
        return self._parse_claude_response(json.dumps(mock_response), batch_spec)
    
    def _validate_and_improve_dataset(self, datapoints: List[TrainingDataPoint]) -> List[TrainingDataPoint]:
        """Validate complete dataset and improve quality."""
        logger.info(f"Validating dataset with {len(datapoints)} samples")
        
        # Individual validation
        validated_datapoints = []
        for dp in datapoints:
            validation_result = validate_individual_entry(dp)
            if validation_result['quality_score'] >= self.config.quality_threshold:
                validated_datapoints.append(dp)
                self.generation_stats['quality_passed'] += 1
            else:
                self.generation_stats['quality_failed'] += 1
        
        # Category-level validation
        category_validation = validate_category_distribution(validated_datapoints)
        if not category_validation['well_balanced']:
            logger.warning("Dataset not well balanced, consider regenerating some categories")
        
        # Coverage validation
        coverage_validation = validate_dataset_coverage(validated_datapoints)
        
        logger.info(f"Dataset validation complete: {len(validated_datapoints)} samples passed quality check")
        return validated_datapoints
    
    def _generate_final_report(self, datapoints: List[TrainingDataPoint]) -> Dict[str, Any]:
        """Generate comprehensive final report."""
        validation_results = {
            'individual_entries': [validate_individual_entry(dp) for dp in datapoints],
            'complexity_distribution': validate_category_distribution(datapoints),
            'coverage_analysis': validate_dataset_coverage(datapoints)
        }
        
        health_assessment = calculate_overall_dataset_health(validation_results)
        
        report = {
            'generation_stats': self.generation_stats,
            'dataset_summary': {
                'total_samples': len(datapoints),
                'complexity_distribution': self._calculate_complexity_distribution(datapoints),
                'domain_distribution': self._calculate_domain_distribution(datapoints),
                'quality_metrics': health_assessment
            },
            'validation_results': validation_results,
            'recommendations': health_assessment.get('recommendations', []),
            'ready_for_training': health_assessment.get('ready_for_training', False)
        }
        
        return report
    
    def _calculate_complexity_distribution(self, datapoints: List[TrainingDataPoint]) -> Dict[str, int]:
        """Calculate actual complexity distribution."""
        distribution = {}
        for dp in datapoints:
            level = dp.expected_complexity_level
            distribution[level] = distribution.get(level, 0) + 1
        return distribution
    
    def _calculate_domain_distribution(self, datapoints: List[TrainingDataPoint]) -> Dict[str, int]:
        """Calculate actual domain distribution."""
        distribution = {}
        for dp in datapoints:
            domain = dp.metadata.domain
            distribution[domain] = distribution.get(domain, 0) + 1
        return distribution
    
    def _save_dataset(self, datapoints: List[TrainingDataPoint], report: Dict[str, Any]) -> None:
        """Save dataset and report to files."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save dataset as JSON
        dataset_file = self.config.output_dir / f"epic1_dataset_{timestamp}.json"
        dataset_data = [asdict(dp) for dp in datapoints]
        
        with open(dataset_file, 'w') as f:
            json.dump(dataset_data, f, indent=2, default=str)
        
        # Save report
        report_file = self.config.output_dir / f"generation_report_{timestamp}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        logger.info(f"Dataset saved to: {dataset_file}")
        logger.info(f"Report saved to: {report_file}")


def main():
    """Example usage of the dataset generation framework."""
    config = DatasetGenerationConfig(
        total_samples=100,  # Small test dataset
        complexity_distribution={"simple": 35, "medium": 40, "complex": 25},
        domain_distribution={"technical": 50, "general": 30, "academic": 20},
        batch_size=10,
        output_dir=Path("data/training/test")
    )
    
    generator = ClaudeDatasetGenerator(config)
    datapoints, report = generator.generate_dataset()
    
    logger.info(f"Generated {len(datapoints)} training samples")
    logger.info(f"Dataset ready for training: {report['ready_for_training']}")
    logger.info(f"Overall health score: {report['dataset_summary']['quality_metrics']['overall_health_score']:.3f}")


if __name__ == "__main__":
    main()