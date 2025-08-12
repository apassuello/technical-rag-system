#!/usr/bin/env python3
"""
Comprehensive Query Corpus Feature Analysis.

This script analyzes the ground truth query corpus to understand feature score
distributions across complexity levels and assess whether current feature extraction
can distinguish between simple/medium/complex queries.
"""

import sys
import yaml
import logging
from pathlib import Path
from typing import Dict, List, Any, Tuple
import statistics
from collections import defaultdict
import json

# Add project paths
project_root = Path(__file__).parent
sys.path.append(str(project_root))

from src.components.query_processors.analyzers.epic1_query_analyzer import Epic1QueryAnalyzer

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CorpusFeatureAnalyzer:
    """Comprehensive analyzer for query corpus feature distributions."""
    
    def __init__(self):
        """Initialize analyzer with Epic 1 components."""
        self.analyzer = Epic1QueryAnalyzer()
        self.feature_extractor = self.analyzer.feature_extractor
        self.complexity_classifier = self.analyzer.complexity_classifier
        
        # Storage for analysis results
        self.query_features = {}
        self.complexity_distributions = defaultdict(list)
        self.feature_stats = {}
        
    def load_ground_truth_queries(self) -> List[Dict[str, Any]]:
        """Load and parse ground truth query dataset."""
        ground_truth_path = project_root / "data" / "evaluation" / "ground_truth_queries.yaml"
        
        with open(ground_truth_path, 'r') as f:
            data = yaml.safe_load(f)
        
        return data['queries']
    
    def extract_detailed_features(self, query: str) -> Dict[str, Any]:
        """Extract comprehensive feature breakdown for a single query."""
        # Get raw features from feature extractor
        features = self.feature_extractor.extract(query)
        
        # Get complexity classification breakdown
        classification = self.complexity_classifier.classify(features)
        
        # Build comprehensive feature analysis
        detailed_features = {
            'query': query,
            'raw_features': features,
            'category_scores': classification['breakdown'],
            'final_score': classification['complexity_score'],
            'classified_level': classification['complexity_level'],
            
            # Extract key individual features for analysis
            'individual_features': {
                # Length features
                'word_count': features['length_features']['word_count'],
                'char_count': features['length_features']['char_count'], 
                'word_count_norm': features['length_features']['word_count_norm'],
                'char_count_norm': features['length_features']['char_count_norm'],
                
                # Vocabulary features
                'technical_term_count': features['vocabulary_features']['technical_term_count'],
                'technical_density': features['vocabulary_features']['technical_density'],
                'technical_term_norm': features['vocabulary_features']['technical_term_norm'],
                'vocabulary_richness': features['vocabulary_features']['vocabulary_richness'],
                
                # Syntactic features
                'syntactic_complexity': features['syntactic_features']['syntactic_complexity'],
                'clause_count': features['syntactic_features'].get('clause_count', 0),
                'has_conditionals': features['syntactic_features'].get('has_conditionals', False),
                
                # Question features
                'question_type': features['question_features'].get('question_type', 'unknown'),
                'has_comparatives': features['question_features'].get('has_comparatives', False),
                'question_complexity': features['question_features'].get('question_complexity', 0.0),
                
                # Ambiguity features
                'ambiguity_score': features['ambiguity_features']['ambiguity_score'],
                'has_ambiguous_terms': features['ambiguity_features'].get('has_ambiguous_terms', False),
            }
        }
        
        return detailed_features
    
    def analyze_corpus(self) -> Dict[str, Any]:
        """Perform comprehensive corpus analysis."""
        queries = self.load_ground_truth_queries()
        
        print("🔍 Comprehensive Corpus Feature Analysis")
        print("=" * 70)
        print(f"📊 Analyzing {len(queries)} ground truth queries")
        
        # Process each query
        for i, query_data in enumerate(queries):
            query = query_data['query']
            expected_difficulty = query_data['difficulty']
            query_id = query_data['id']
            
            # Handle difficulty label mapping
            if expected_difficulty == 'moderate':
                expected_difficulty = 'medium'
            
            features = self.extract_detailed_features(query)
            features['expected_complexity'] = expected_difficulty
            features['query_id'] = query_id
            
            self.query_features[query_id] = features
            self.complexity_distributions[expected_difficulty].append(features)
            
            # Progress indicator
            if (i + 1) % 10 == 0:
                print(f"  Processed {i + 1}/{len(queries)} queries...")
        
        print(f"✅ Feature extraction complete!")
        
        # Compute statistics
        self._compute_feature_statistics()
        
        return self._generate_analysis_report()
    
    def _compute_feature_statistics(self):
        """Compute statistical distributions for all features by complexity level."""
        
        # Define features to analyze
        features_to_analyze = [
            'final_score',
            'word_count', 'char_count', 'word_count_norm', 'char_count_norm',
            'technical_term_count', 'technical_density', 'technical_term_norm',
            'vocabulary_richness', 'syntactic_complexity', 'ambiguity_score'
        ]
        
        category_features = ['length', 'syntactic', 'vocabulary', 'question', 'ambiguity']
        
        self.feature_stats = {}
        
        for complexity_level in ['simple', 'medium', 'complex']:
            level_queries = self.complexity_distributions[complexity_level]
            if not level_queries:
                continue
                
            self.feature_stats[complexity_level] = {}
            
            # Analyze individual features
            for feature in features_to_analyze:
                values = []
                for query_features in level_queries:
                    if feature == 'final_score':
                        values.append(query_features[feature])
                    else:
                        values.append(query_features['individual_features'][feature])
                
                if values:
                    self.feature_stats[complexity_level][feature] = {
                        'count': len(values),
                        'mean': statistics.mean(values),
                        'median': statistics.median(values),
                        'min': min(values),
                        'max': max(values),
                        'std': statistics.stdev(values) if len(values) > 1 else 0.0,
                        'values': values
                    }
            
            # Analyze category scores
            for category in category_features:
                values = [q['category_scores'][category] for q in level_queries]
                if values:
                    self.feature_stats[complexity_level][f'{category}_category'] = {
                        'count': len(values),
                        'mean': statistics.mean(values),
                        'median': statistics.median(values),
                        'min': min(values),
                        'max': max(values),
                        'std': statistics.stdev(values) if len(values) > 1 else 0.0,
                        'values': values
                    }
    
    def _calculate_feature_discrimination(self, feature_name: str) -> Dict[str, float]:
        """Calculate discrimination power of a feature between complexity levels."""
        if feature_name not in self.feature_stats.get('simple', {}):
            return {}
        
        simple_values = self.feature_stats['simple'][feature_name]['values']
        medium_values = self.feature_stats['medium'][feature_name]['values']  
        complex_values = self.feature_stats['complex'][feature_name]['values']
        
        def cohens_d(group1, group2):
            """Calculate Cohen's d effect size."""
            if len(group1) < 2 or len(group2) < 2:
                return 0.0
            
            n1, n2 = len(group1), len(group2)
            mean1, mean2 = statistics.mean(group1), statistics.mean(group2)
            var1, var2 = statistics.variance(group1), statistics.variance(group2)
            
            # Pooled standard deviation
            pooled_std = ((n1 - 1) * var1 + (n2 - 1) * var2) / (n1 + n2 - 2)
            pooled_std = pooled_std ** 0.5
            
            if pooled_std == 0:
                return 0.0
                
            return (mean2 - mean1) / pooled_std
        
        return {
            'simple_vs_medium': cohens_d(simple_values, medium_values),
            'medium_vs_complex': cohens_d(medium_values, complex_values),
            'simple_vs_complex': cohens_d(simple_values, complex_values)
        }
    
    def _generate_analysis_report(self) -> Dict[str, Any]:
        """Generate comprehensive analysis report."""
        
        # Distribution summary
        distribution_summary = {}
        for level in ['simple', 'medium', 'complex']:
            queries = self.complexity_distributions[level]
            distribution_summary[level] = {
                'count': len(queries),
                'percentage': len(queries) / len(self.query_features) * 100
            }
        
        # Feature discrimination analysis
        key_features = ['final_score', 'technical_density', 'syntactic_complexity', 
                       'vocabulary_category', 'word_count_norm']
        
        discrimination_analysis = {}
        for feature in key_features:
            if feature in self.feature_stats.get('simple', {}):
                discrimination_analysis[feature] = self._calculate_feature_discrimination(feature)
        
        return {
            'corpus_distribution': distribution_summary,
            'feature_statistics': self.feature_stats,
            'discrimination_analysis': discrimination_analysis,
            'detailed_queries': self.query_features
        }
    
    def print_detailed_report(self, analysis: Dict[str, Any]):
        """Print comprehensive analysis report."""
        
        print("\n" + "=" * 70)
        print("📊 CORPUS DISTRIBUTION ANALYSIS")
        print("=" * 70)
        
        for level, stats in analysis['corpus_distribution'].items():
            print(f"{level.upper():>8}: {stats['count']:2d} queries ({stats['percentage']:4.1f}%)")
        
        print("\n" + "=" * 70) 
        print("📈 FEATURE STATISTICS BY COMPLEXITY LEVEL")
        print("=" * 70)
        
        # Key features to highlight
        key_features = ['final_score', 'technical_density', 'syntactic_complexity', 'word_count_norm']
        
        for feature in key_features:
            print(f"\n🔍 {feature.upper().replace('_', ' ')}:")
            print("-" * 50)
            
            for level in ['simple', 'medium', 'complex']:
                if level in self.feature_stats and feature in self.feature_stats[level]:
                    stats = self.feature_stats[level][feature]
                    print(f"  {level:>8}: μ={stats['mean']:.3f} σ={stats['std']:.3f} "
                          f"range=[{stats['min']:.3f}, {stats['max']:.3f}] n={stats['count']}")
        
        print("\n" + "=" * 70)
        print("🎯 FEATURE DISCRIMINATION ANALYSIS") 
        print("=" * 70)
        
        for feature, discrimination in analysis['discrimination_analysis'].items():
            print(f"\n📏 {feature.upper().replace('_', ' ')} - Effect Sizes (Cohen's d):")
            print("-" * 55)
            for comparison, effect_size in discrimination.items():
                interpretation = "negligible"
                if abs(effect_size) > 0.8: interpretation = "large"
                elif abs(effect_size) > 0.5: interpretation = "medium" 
                elif abs(effect_size) > 0.2: interpretation = "small"
                
                print(f"  {comparison:>18}: {effect_size:+6.3f} ({interpretation})")
        
        print("\n" + "=" * 70)
        print("🔍 DETAILED QUERY ANALYSIS")
        print("=" * 70)
        
        # Show examples of potential misclassifications
        misclassifications = []
        for query_id, features in analysis['detailed_queries'].items():
            expected = features['expected_complexity']
            classified = features['classified_level']
            score = features['final_score']
            
            if expected != classified:
                misclassifications.append((query_id, expected, classified, score, features['query']))
        
        print(f"\n❌ Misclassified Queries: {len(misclassifications)}/{len(analysis['detailed_queries'])}")
        print("-" * 70)
        
        for query_id, expected, classified, score, query in misclassifications[:10]:  # Show first 10
            print(f"  {query_id}: {expected} → {classified} (score: {score:.3f})")
            print(f"    '{query[:80]}{'...' if len(query) > 80 else ''}'")
    
    def save_analysis(self, analysis: Dict[str, Any], filename: str = "corpus_feature_analysis.json"):
        """Save detailed analysis to JSON file."""
        output_path = project_root / filename
        
        # Convert for JSON serialization
        serializable_analysis = {}
        for key, value in analysis.items():
            if key == 'detailed_queries':
                # Simplify detailed queries for JSON
                serializable_analysis[key] = {
                    qid: {
                        'query': q['query'],
                        'expected_complexity': q['expected_complexity'], 
                        'classified_level': q['classified_level'],
                        'final_score': q['final_score'],
                        'category_scores': q['category_scores'],
                        'key_features': {
                            k: v for k, v in q['individual_features'].items()
                            if k in ['word_count', 'technical_term_count', 'technical_density', 'syntactic_complexity']
                        }
                    }
                    for qid, q in value.items()
                }
            else:
                serializable_analysis[key] = value
        
        with open(output_path, 'w') as f:
            json.dump(serializable_analysis, f, indent=2)
        
        print(f"\n💾 Detailed analysis saved to: {output_path}")


def main():
    """Main analysis execution."""
    
    analyzer = CorpusFeatureAnalyzer()
    
    # Perform comprehensive analysis
    analysis_results = analyzer.analyze_corpus()
    
    # Print detailed report
    analyzer.print_detailed_report(analysis_results)
    
    # Save results
    analyzer.save_analysis(analysis_results)
    
    # Generate summary conclusions
    print("\n" + "=" * 70)
    print("🎯 ANALYSIS CONCLUSIONS")
    print("=" * 70)
    
    # Calculate overall discrimination quality
    discrimination_scores = []
    for feature, discrimination in analysis_results['discrimination_analysis'].items():
        for comparison, effect_size in discrimination.items():
            discrimination_scores.append(abs(effect_size))
    
    avg_discrimination = statistics.mean(discrimination_scores) if discrimination_scores else 0.0
    
    print(f"\n📊 Average Feature Discrimination (Cohen's d): {avg_discrimination:.3f}")
    
    if avg_discrimination > 0.8:
        print("✅ STRONG discrimination - Features can distinguish complexity levels well")
        print("   Recommendation: Focus on calibration optimization only")
    elif avg_discrimination > 0.5:
        print("⚠️  MODERATE discrimination - Features partially distinguish complexity")
        print("   Recommendation: Combine calibration with feature weight optimization")
    elif avg_discrimination > 0.2:
        print("❌ WEAK discrimination - Features struggle to distinguish complexity")
        print("   Recommendation: Feature engineering needed alongside calibration")
    else:
        print("🚫 POOR discrimination - Features cannot reliably distinguish complexity")
        print("   Recommendation: Major feature engineering and corpus review required")
    
    # Classification accuracy analysis
    total_queries = len(analysis_results['detailed_queries'])
    misclassified = sum(1 for q in analysis_results['detailed_queries'].values() 
                       if q['expected_complexity'] != q['classified_level'])
    accuracy = (total_queries - misclassified) / total_queries
    
    print(f"\n🎯 Current Classification Accuracy: {accuracy:.1%} ({total_queries - misclassified}/{total_queries})")
    
    if accuracy < 0.60:
        print("❌ Below target accuracy - Systematic improvements needed")
    elif accuracy < 0.75:
        print("⚠️  Moderate accuracy - Calibration optimization recommended") 
    else:
        print("✅ Good accuracy - Fine-tuning through calibration sufficient")


if __name__ == "__main__":
    main()