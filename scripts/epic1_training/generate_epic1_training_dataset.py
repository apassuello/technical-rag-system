#!/usr/bin/env python3
"""
Epic 1 Training Dataset Generator

Generates a balanced, high-quality training dataset for the Epic 1 multi-view 
ML query complexity analyzer with consistent scoring across all views.
"""

import json
import random
import numpy as np
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, asdict
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class TrainingSample:
    """Single training sample with query and view scores."""
    query_text: str
    expected_complexity_score: float
    expected_complexity_level: str
    view_scores: Dict[str, float]
    confidence: float
    metadata: Dict[str, any]


class Epic1DatasetGenerator:
    """Generates consistent training data for Epic 1 ML models."""
    
    def __init__(self, seed: int = 42):
        """Initialize generator with reproducible randomness."""
        random.seed(seed)
        np.random.seed(seed)
        
        # Query templates for different complexity levels
        self.simple_templates = [
            "How do I {action} in {language}?",
            "What is {concept}?",
            "How to {task}?",
            "What does {term} mean?",
            "Can you explain {concept}?",
            "Show me how to {action}",
            "Where do I find {resource}?",
            "What's the syntax for {operation}?",
            "How to install {tool}?",
            "What is the purpose of {feature}?"
        ]
        
        self.medium_templates = [
            "What's the best approach to {problem} when {constraint}?",
            "How do I optimize {process} for {metric}?",
            "What are the differences between {option1} and {option2}?",
            "How to implement {feature} with {requirement}?",
            "Why does {issue} occur when {condition}?",
            "How can I integrate {system1} with {system2}?",
            "What's the trade-off between {factor1} and {factor2}?",
            "How to debug {problem} in {context}?",
            "What pattern should I use for {scenario}?",
            "How to handle {edge_case} in {system}?"
        ]
        
        self.complex_templates = [
            "How would you design {system} that {requirements} while {constraints}?",
            "What's the architectural approach for {distributed_system} with {guarantees}?",
            "How to implement {algorithm} optimized for {performance_metric} under {constraints}?",
            "Design a solution for {problem} considering {factors} and {trade_offs}",
            "How to achieve {property} in {distributed_context} with {fault_tolerance}?",
            "What's the best strategy for {complex_problem} given {multiple_constraints}?",
            "How to ensure {quality_attribute} while maintaining {other_attribute} in {system}?",
            "Explain the implementation of {advanced_concept} with {theoretical_backing}",
            "How would you scale {system} to handle {load} with {latency_requirements}?",
            "Design {infrastructure} supporting {requirements} with {cost_constraints}"
        ]
        
        # Vocabulary pools for different complexity levels
        self.simple_vocab = {
            'action': ['create', 'delete', 'update', 'read', 'write', 'open', 'close', 'start', 'stop', 'run'],
            'language': ['Python', 'JavaScript', 'Java', 'C++', 'SQL', 'HTML', 'CSS', 'Ruby', 'Go', 'Rust'],
            'concept': ['variable', 'function', 'loop', 'array', 'list', 'dictionary', 'class', 'object', 'method', 'parameter'],
            'task': ['sort a list', 'read a file', 'parse JSON', 'connect to database', 'make HTTP request', 'validate input'],
            'term': ['API', 'REST', 'JSON', 'XML', 'HTTP', 'URL', 'CLI', 'GUI', 'IDE', 'SDK'],
            'resource': ['documentation', 'tutorials', 'examples', 'libraries', 'packages', 'modules'],
            'operation': ['for loop', 'if statement', 'function call', 'array indexing', 'string concatenation'],
            'tool': ['Node.js', 'Docker', 'Git', 'npm', 'pip', 'Maven', 'webpack', 'VSCode', 'pytest'],
            'feature': ['inheritance', 'polymorphism', 'encapsulation', 'recursion', 'iteration', 'exception handling']
        }
        
        self.medium_vocab = {
            'problem': ['memory leak', 'race condition', 'deadlock', 'bottleneck', 'scaling issue', 'security vulnerability', 'performance degradation'],
            'constraint': ['limited memory', 'high concurrency', 'real-time requirements', 'budget limitations', 'legacy systems', 'network latency'],
            'process': ['database queries', 'API calls', 'data pipeline', 'build process', 'deployment pipeline', 'test suite'],
            'metric': ['throughput', 'latency', 'memory usage', 'CPU utilization', 'response time', 'error rate'],
            'option1': ['REST API', 'microservices', 'SQL database', 'synchronous processing', 'client-side rendering', 'monolithic architecture'],
            'option2': ['GraphQL', 'monolith', 'NoSQL database', 'asynchronous processing', 'server-side rendering', 'serverless'],
            'feature': ['authentication system', 'caching layer', 'search functionality', 'recommendation engine', 'payment processing'],
            'requirement': ['ACID compliance', 'horizontal scaling', 'fault tolerance', 'backward compatibility', 'GDPR compliance'],
            'issue': ['timeout error', 'memory overflow', 'connection refused', 'data inconsistency', 'performance regression'],
            'system1': ['Kafka', 'Redis', 'Elasticsearch', 'MongoDB', 'PostgreSQL', 'RabbitMQ'],
            'system2': ['Spring Boot', 'Django', 'Express.js', 'Flask', 'FastAPI', 'Rails'],
            'factor1': ['consistency', 'performance', 'security', 'simplicity', 'cost', 'flexibility'],
            'factor2': ['availability', 'scalability', 'usability', 'complexity', 'speed', 'maintainability'],
            'edge_case': ['network partition', 'concurrent updates', 'circular dependencies', 'overflow conditions', 'race conditions'],
            'scenario': ['multi-tenant application', 'real-time chat', 'e-commerce checkout', 'data synchronization', 'user authentication'],
            'condition': ['under load', 'during deployment', 'after restart', 'with concurrent users', 'in production'],
            'context': ['distributed system', 'production environment', 'containerized application', 'cloud deployment', 'microservices']
        }
        
        self.complex_vocab = {
            'system': ['distributed consensus mechanism', 'real-time streaming platform', 'ML inference pipeline', 'blockchain network', 'IoT data platform'],
            'requirements': ['exactly-once delivery', 'linearizable consistency', 'sub-millisecond latency', 'five nines availability', 'ACID guarantees'],
            'constraints': ['CAP theorem limitations', 'network partitions', 'Byzantine failures', 'resource constraints', 'regulatory compliance'],
            'distributed_system': ['multi-region database', 'global CDN', 'distributed cache', 'service mesh', 'event-driven architecture'],
            'guarantees': ['strong consistency', 'eventual consistency', 'causal consistency', 'read-after-write consistency', 'monotonic reads'],
            'algorithm': ['consensus protocol', 'distributed hash table', 'vector clock synchronization', 'two-phase commit', 'Paxos algorithm'],
            'performance_metric': ['p99 latency', 'throughput per node', 'write amplification', 'read amplification', 'network overhead'],
            'problem': ['distributed transaction management', 'global state synchronization', 'leader election', 'partition tolerance', 'conflict resolution'],
            'factors': ['data locality', 'network topology', 'failure modes', 'recovery strategies', 'consistency models'],
            'trade_offs': ['latency vs consistency', 'throughput vs durability', 'complexity vs maintainability', 'cost vs performance'],
            'property': ['linearizability', 'serializability', 'idempotency', 'commutativity', 'determinism'],
            'distributed_context': ['geo-replicated systems', 'edge computing', 'federated learning', 'multi-cloud deployment', 'hybrid cloud'],
            'fault_tolerance': ['Byzantine fault tolerance', 'crash fault tolerance', 'network partition tolerance', 'cascading failure prevention'],
            'complex_problem': ['distributed consensus', 'global ordering', 'distributed deadlock detection', 'distributed garbage collection'],
            'multiple_constraints': ['regulatory requirements, cost limits, and performance SLAs', 'security, scalability, and maintainability'],
            'quality_attribute': ['security', 'reliability', 'performance', 'scalability', 'maintainability'],
            'other_attribute': ['cost-effectiveness', 'developer productivity', 'operational simplicity', 'user experience'],
            'advanced_concept': ['CRDT implementation', 'Raft consensus', 'vector clocks', 'Merkle trees', 'bloom filters'],
            'theoretical_backing': ['CAP theorem', 'FLP impossibility', 'PACELC theorem', 'Lamport timestamps', 'happened-before relation'],
            'infrastructure': ['multi-region active-active setup', 'service mesh architecture', 'event sourcing system', 'CQRS implementation'],
            'load': ['millions of requests per second', 'petabytes of data', 'billions of events per day', 'thousands of concurrent connections'],
            'latency_requirements': ['single-digit millisecond p99', 'sub-100ms globally', 'microsecond-level processing'],
            'cost_constraints': ['optimize for spot instances', 'minimize data transfer costs', 'reduce operational overhead']
        }
    
    def _fill_template(self, template: str, vocab: Dict[str, List[str]]) -> str:
        """Fill a template with random vocabulary."""
        query = template
        for placeholder in vocab.keys():
            if f"{{{placeholder}}}" in query:
                value = random.choice(vocab[placeholder])
                query = query.replace(f"{{{placeholder}}}", value)
        return query
    
    def _generate_base_score(self, complexity_level: str) -> float:
        """Generate base complexity score for given level."""
        if complexity_level == "simple":
            # Simple: 0.10-0.33 with peak around 0.20
            return np.clip(np.random.normal(0.20, 0.06), 0.10, 0.33)
        elif complexity_level == "medium":
            # Medium: 0.34-0.66 with peak around 0.50
            return np.clip(np.random.normal(0.50, 0.08), 0.34, 0.66)
        else:  # complex
            # Complex: 0.67-0.90 with peak around 0.78
            return np.clip(np.random.normal(0.78, 0.07), 0.67, 0.90)
    
    def _generate_view_scores(self, base_score: float, query_text: str) -> Dict[str, float]:
        """Generate individual view scores with controlled variation."""
        view_scores = {}
        
        # Define view characteristics and their sensitivity to different aspects
        view_modifiers = {
            'technical': {
                'variance': 0.15,  # Higher variance for technical terms
                'bias': 0.0,  # No systematic bias
                'keywords': ['algorithm', 'optimization', 'architecture', 'protocol', 'implementation']
            },
            'linguistic': {
                'variance': 0.10,  # Lower variance, more consistent
                'bias': -0.02,  # Slightly lower on average (simpler language)
                'keywords': ['complex', 'analyze', 'considering', 'furthermore', 'implications']
            },
            'task': {
                'variance': 0.12,
                'bias': 0.0,
                'keywords': ['design', 'implement', 'optimize', 'evaluate', 'compare']
            },
            'semantic': {
                'variance': 0.10,
                'bias': 0.01,  # Slightly higher for abstract concepts
                'keywords': ['relationship', 'concept', 'abstraction', 'pattern', 'model']
            },
            'computational': {
                'variance': 0.15,  # Higher variance for algorithmic content
                'bias': 0.02,  # Slightly higher for technical queries
                'keywords': ['O(n)', 'complexity', 'performance', 'latency', 'throughput']
            }
        }
        
        # Generate correlated scores for each view
        for view_name, modifiers in view_modifiers.items():
            # Start with base score
            view_score = base_score
            
            # Add systematic bias
            view_score += modifiers['bias']
            
            # Add controlled random variation
            variation = np.random.normal(0, modifiers['variance'])
            view_score += variation
            
            # Apply keyword boost/penalty
            keyword_boost = 0
            for keyword in modifiers['keywords']:
                if keyword.lower() in query_text.lower():
                    keyword_boost += 0.02
            view_score += min(keyword_boost, 0.08)  # Cap keyword boost
            
            # Ensure correlation with base score (0.6-0.9)
            # Mix view-specific score with base score to maintain correlation
            correlation_factor = 0.7  # How much to preserve base score
            view_score = correlation_factor * base_score + (1 - correlation_factor) * view_score
            
            # Clip to valid range
            view_scores[view_name] = np.clip(view_score, 0.0, 1.0)
        
        # Ensure adjacent views have higher correlation
        # Technical <-> Computational (high correlation)
        if abs(view_scores['technical'] - view_scores['computational']) > 0.25:
            avg = (view_scores['technical'] + view_scores['computational']) / 2
            view_scores['technical'] = avg + np.random.normal(0, 0.05)
            view_scores['computational'] = avg + np.random.normal(0, 0.05)
        
        # Task <-> Semantic (moderate correlation)
        if abs(view_scores['task'] - view_scores['semantic']) > 0.30:
            avg = (view_scores['task'] + view_scores['semantic']) / 2
            view_scores['task'] = avg + np.random.normal(0, 0.08)
            view_scores['semantic'] = avg + np.random.normal(0, 0.08)
        
        # Final clipping
        for view in view_scores:
            view_scores[view] = round(np.clip(view_scores[view], 0.0, 1.0), 3)
        
        return view_scores
    
    def _calculate_fusion_score(self, view_scores: Dict[str, float]) -> float:
        """Calculate final complexity score from view scores."""
        # Weighted average with technical and task views having higher weight
        weights = {
            'technical': 0.30,
            'linguistic': 0.15,
            'task': 0.25,
            'semantic': 0.15,
            'computational': 0.15
        }
        
        fusion_score = sum(view_scores[view] * weights[view] for view in view_scores)
        return round(fusion_score, 3)
    
    def _calculate_confidence(self, view_scores: Dict[str, float]) -> float:
        """Calculate confidence based on view agreement."""
        scores = list(view_scores.values())
        std_dev = np.std(scores)
        
        # Map standard deviation to confidence
        # Low std dev (high agreement) -> high confidence
        if std_dev < 0.10:
            confidence = 0.85 + random.uniform(0, 0.10)  # 0.85-0.95
        elif std_dev < 0.20:
            confidence = 0.70 + random.uniform(0, 0.15)  # 0.70-0.85
        elif std_dev < 0.30:
            confidence = 0.55 + random.uniform(0, 0.15)  # 0.55-0.70
        else:
            confidence = 0.40 + random.uniform(0, 0.15)  # 0.40-0.55
        
        return round(min(confidence, 0.95), 3)
    
    def generate_sample(self, complexity_level: str, domain: str = "technical") -> TrainingSample:
        """Generate a single training sample."""
        # Select and fill template
        if complexity_level == "simple":
            template = random.choice(self.simple_templates)
            query_text = self._fill_template(template, self.simple_vocab)
        elif complexity_level == "medium":
            template = random.choice(self.medium_templates)
            query_text = self._fill_template(template, self.medium_vocab)
        else:  # complex
            template = random.choice(self.complex_templates)
            query_text = self._fill_template(template, self.complex_vocab)
        
        # Generate scores
        base_score = self._generate_base_score(complexity_level)
        view_scores = self._generate_view_scores(base_score, query_text)
        final_score = self._calculate_fusion_score(view_scores)
        confidence = self._calculate_confidence(view_scores)
        
        # Determine query type based on template
        query_type = "how-to"
        if "What" in query_text or "What's" in query_text:
            query_type = random.choice(["definition", "comparison", "analysis"])
        elif "Why" in query_text:
            query_type = "troubleshooting"
        elif "design" in query_text.lower() or "implement" in query_text.lower():
            query_type = "design"
        elif "optimize" in query_text.lower():
            query_type = "optimization"
        
        return TrainingSample(
            query_text=query_text,
            expected_complexity_score=final_score,
            expected_complexity_level=complexity_level,
            view_scores=view_scores,
            confidence=confidence,
            metadata={
                "domain": domain,
                "query_type": query_type,
                "generation_timestamp": datetime.now(timezone.utc).isoformat(),
                "base_score": round(base_score, 3),
                "template_used": template
            }
        )
    
    def generate_dataset(self, num_samples: int = 1000) -> List[TrainingSample]:
        """Generate complete dataset with balanced distribution."""
        dataset = []
        
        # Distribution targets
        distribution = {
            "simple": int(num_samples * 0.35),     # 350 samples
            "medium": int(num_samples * 0.40),     # 400 samples
            "complex": int(num_samples * 0.25)     # 250 samples
        }
        
        # Generate samples for each complexity level
        for complexity_level, count in distribution.items():
            logger.info(f"Generating {count} {complexity_level} samples...")
            for i in range(count):
                # Vary domains for diversity
                domain = random.choices(
                    ["technical", "academic", "general"],
                    weights=[0.6, 0.2, 0.2]
                )[0]
                
                sample = self.generate_sample(complexity_level, domain)
                dataset.append(sample)
                
                if (i + 1) % 50 == 0:
                    logger.info(f"  Generated {i + 1}/{count} {complexity_level} samples")
        
        # Shuffle dataset
        random.shuffle(dataset)
        
        return dataset
    
    def validate_dataset(self, dataset: List[TrainingSample]) -> Dict[str, any]:
        """Validate dataset quality and consistency."""
        validation_results = {
            "total_samples": len(dataset),
            "complexity_distribution": {},
            "score_statistics": {},
            "view_correlations": {},
            "quality_checks": {}
        }
        
        # Count distribution
        for level in ["simple", "medium", "complex"]:
            count = sum(1 for s in dataset if s.expected_complexity_level == level)
            validation_results["complexity_distribution"][level] = {
                "count": count,
                "percentage": round(count / len(dataset) * 100, 1)
            }
        
        # Calculate score statistics
        all_scores = [s.expected_complexity_score for s in dataset]
        validation_results["score_statistics"] = {
            "mean": round(np.mean(all_scores), 3),
            "std": round(np.std(all_scores), 3),
            "min": round(min(all_scores), 3),
            "max": round(max(all_scores), 3)
        }
        
        # Calculate view correlations
        view_names = ["technical", "linguistic", "task", "semantic", "computational"]
        view_scores_lists = {view: [] for view in view_names}
        base_scores = []
        
        for sample in dataset:
            for view in view_names:
                view_scores_lists[view].append(sample.view_scores[view])
            base_scores.append(sample.metadata.get("base_score", sample.expected_complexity_score))
        
        # Calculate correlation between each view and base score
        for view in view_names:
            correlation = np.corrcoef(view_scores_lists[view], base_scores)[0, 1]
            validation_results["view_correlations"][view] = round(correlation, 3)
        
        # Quality checks
        validation_results["quality_checks"]["score_consistency"] = True
        validation_results["quality_checks"]["correlation_check"] = True
        validation_results["quality_checks"]["distribution_balance"] = True
        
        # Check score consistency (std dev < 0.25 for each sample)
        high_variance_samples = 0
        for sample in dataset:
            scores = list(sample.view_scores.values())
            if np.std(scores) > 0.25:
                high_variance_samples += 1
        
        validation_results["quality_checks"]["high_variance_samples"] = high_variance_samples
        validation_results["quality_checks"]["score_consistency"] = high_variance_samples < len(dataset) * 0.05
        
        # Check correlations (all should be > 0.6)
        for view, corr in validation_results["view_correlations"].items():
            if corr < 0.6:
                validation_results["quality_checks"]["correlation_check"] = False
                break
        
        # Check distribution balance (within 5% of target)
        expected = {"simple": 35, "medium": 40, "complex": 25}
        for level, expected_pct in expected.items():
            actual_pct = validation_results["complexity_distribution"][level]["percentage"]
            if abs(actual_pct - expected_pct) > 5:
                validation_results["quality_checks"]["distribution_balance"] = False
                break
        
        # Overall quality score
        quality_score = sum([
            validation_results["quality_checks"]["score_consistency"] * 0.4,
            validation_results["quality_checks"]["correlation_check"] * 0.4,
            validation_results["quality_checks"]["distribution_balance"] * 0.2
        ])
        validation_results["overall_quality_score"] = round(quality_score, 2)
        
        return validation_results


def main():
    """Generate and save the Epic 1 training dataset."""
    # Initialize generator
    generator = Epic1DatasetGenerator(seed=42)
    
    # Generate dataset
    logger.info("Starting dataset generation...")
    dataset = generator.generate_dataset(num_samples=1000)
    
    # Validate dataset
    logger.info("Validating dataset...")
    validation_results = generator.validate_dataset(dataset)
    
    # Convert to serializable format
    dataset_json = []
    for sample in dataset:
        dataset_json.append({
            "query_text": sample.query_text,
            "expected_complexity_score": sample.expected_complexity_score,
            "expected_complexity_level": sample.expected_complexity_level,
            "view_scores": sample.view_scores,
            "confidence": sample.confidence,
            "metadata": sample.metadata
        })
    
    # Save dataset
    output_dir = Path("data/training")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    dataset_path = output_dir / f"epic1_dataset_{timestamp}.json"
    validation_path = output_dir / f"validation_report_{timestamp}.json"
    
    with open(dataset_path, 'w') as f:
        json.dump(dataset_json, f, indent=2)
    
    with open(validation_path, 'w') as f:
        json.dump(validation_results, f, indent=2)
    
    # Print summary
    logger.info(f"\nDataset generation complete!")
    logger.info(f"Dataset saved to: {dataset_path}")
    logger.info(f"Validation report saved to: {validation_path}")
    logger.info(f"\nDataset Summary:")
    logger.info(f"  Total samples: {validation_results['total_samples']}")
    logger.info(f"  Distribution:")
    for level, stats in validation_results['complexity_distribution'].items():
        logger.info(f"    {level}: {stats['count']} ({stats['percentage']}%)")
    logger.info(f"  Overall quality score: {validation_results['overall_quality_score']}")
    logger.info(f"  View correlations:")
    for view, corr in validation_results['view_correlations'].items():
        logger.info(f"    {view}: {corr}")


if __name__ == "__main__":
    main()