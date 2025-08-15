# Statistical Validation Framework for Epic 1 Training Dataset

## Overview
This document defines comprehensive statistical methods to evaluate the quality of Claude-generated training data for the Epic 1 multi-view ML query complexity analyzer.

## Validation Hierarchy

### 1. Individual Entry Validation
**Purpose**: Validate each TrainingDataPoint for internal consistency and quality

### 2. Category-Level Validation  
**Purpose**: Ensure proper distribution and balance within complexity levels and domains

### 3. Dataset-Level Validation
**Purpose**: Validate overall dataset quality, coverage, and statistical properties

## 1. Individual Entry Validation

### Core Consistency Metrics

#### View Score Consistency
```python
def validate_view_score_consistency(datapoint: TrainingDataPoint) -> Dict[str, float]:
    """Validate consistency between individual view scores."""
    
    view_scores = [v.complexity_score for v in datapoint.view_scores.values()]
    expected_score = datapoint.expected_complexity_score
    
    metrics = {
        'view_score_variance': np.var(view_scores),
        'expected_vs_mean_diff': abs(expected_score - np.mean(view_scores)),
        'max_deviation': max(abs(score - expected_score) for score in view_scores),
        'coefficient_of_variation': np.std(view_scores) / np.mean(view_scores) if np.mean(view_scores) > 0 else 0
    }
    
    # Quality thresholds
    quality_flags = []
    if metrics['view_score_variance'] > 0.16:  # std > 0.4
        quality_flags.append('high_view_disagreement')
    if metrics['expected_vs_mean_diff'] > 0.2:
        quality_flags.append('expected_score_mismatch')
    if metrics['max_deviation'] > 0.3:
        quality_flags.append('outlier_view_score')
        
    return {**metrics, 'quality_flags': quality_flags}
```

#### Feature-Score Alignment
```python
def validate_feature_score_alignment(datapoint: TrainingDataPoint) -> Dict[str, Any]:
    """Validate alignment between extracted features and complexity scores."""
    
    alignments = {}
    
    for view_name, view_score in datapoint.view_scores.items():
        features = view_score.feature_values
        score = view_score.complexity_score
        
        # View-specific validation
        if view_name == 'technical':
            predicted_score = predict_technical_score_from_features(features)
        elif view_name == 'linguistic':
            predicted_score = predict_linguistic_score_from_features(features)
        elif view_name == 'task':
            predicted_score = predict_task_score_from_features(features)
        elif view_name == 'semantic':
            predicted_score = predict_semantic_score_from_features(features)
        elif view_name == 'computational':
            predicted_score = predict_computational_score_from_features(features)
        
        alignment_error = abs(score - predicted_score)
        alignments[view_name] = {
            'score': score,
            'predicted_score': predicted_score,
            'alignment_error': alignment_error,
            'well_aligned': alignment_error < 0.15
        }
    
    overall_alignment = np.mean([a['alignment_error'] for a in alignments.values()])
    
    return {
        'view_alignments': alignments,
        'overall_alignment_error': overall_alignment,
        'quality_flag': 'poor_feature_alignment' if overall_alignment > 0.2 else None
    }
```

#### Confidence Calibration
```python
def validate_confidence_calibration(datapoint: TrainingDataPoint) -> Dict[str, float]:
    """Validate if confidence scores are well-calibrated."""
    
    confidences = [v.confidence for v in datapoint.view_scores.values()]
    view_agreements = []
    
    # Calculate pairwise view agreements
    view_scores = [v.complexity_score for v in datapoint.view_scores.values()]
    for i in range(len(view_scores)):
        for j in range(i+1, len(view_scores)):
            agreement = 1 - abs(view_scores[i] - view_scores[j])
            view_agreements.append(agreement)
    
    avg_agreement = np.mean(view_agreements)
    avg_confidence = np.mean(confidences)
    
    # Well-calibrated confidence should correlate with agreement
    calibration_error = abs(avg_confidence - avg_agreement)
    
    return {
        'avg_confidence': avg_confidence,
        'avg_agreement': avg_agreement, 
        'calibration_error': calibration_error,
        'well_calibrated': calibration_error < 0.15,
        'confidence_variance': np.var(confidences)
    }
```

### Query Quality Assessment

#### Linguistic Realism
```python
def assess_query_realism(query_text: str) -> Dict[str, Any]:
    """Assess if query represents realistic user need."""
    
    # Linguistic patterns indicating artificial generation
    artificial_patterns = [
        r'^(Please\s+)?(tell me|explain|describe)\s+how\s+to',  # Overly formal
        r'comprehensive\s+(guide|overview|explanation)',        # Too academic
        r'step-by-step\s+instructions',                         # Too structured
        r'detailed\s+analysis\s+of',                           # Too formal
    ]
    
    realism_score = 1.0
    flags = []
    
    # Check for artificial patterns
    for pattern in artificial_patterns:
        if re.search(pattern, query_text, re.IGNORECASE):
            realism_score -= 0.2
            flags.append(f'artificial_pattern: {pattern}')
    
    # Check length distribution (real queries tend to be shorter)
    if len(query_text.split()) > 20:
        realism_score -= 0.1
        flags.append('unusually_long')
    
    # Check for overly perfect grammar (real queries often have minor issues)
    grammar_score = assess_grammar_perfection(query_text)
    if grammar_score > 0.98:  # Too perfect
        realism_score -= 0.1  
        flags.append('overly_perfect_grammar')
    
    return {
        'realism_score': max(0, realism_score),
        'quality_flags': flags,
        'realistic': realism_score > 0.7
    }
```

#### Domain Appropriateness
```python
def validate_domain_consistency(datapoint: TrainingDataPoint) -> Dict[str, Any]:
    """Validate query matches declared domain and complexity level."""
    
    query = datapoint.query_text
    declared_domain = datapoint.metadata.domain
    declared_complexity = datapoint.expected_complexity_level
    
    # Domain classification using keyword analysis
    domain_indicators = {
        'technical': ['code', 'programming', 'algorithm', 'database', 'API', 'function'],
        'academic': ['research', 'study', 'theory', 'analysis', 'methodology', 'literature'],
        'general': ['how to', 'what is', 'why does', 'can I', 'should I']
    }
    
    detected_domains = []
    for domain, keywords in domain_indicators.items():
        if any(keyword in query.lower() for keyword in keywords):
            detected_domains.append(domain)
    
    domain_consistent = declared_domain in detected_domains or len(detected_domains) == 0
    
    # Complexity level validation through heuristics
    complexity_indicators = {
        'simple': ['basic', 'simple', 'how do I', 'what is', 'beginner'],
        'medium': ['optimize', 'implement', 'design', 'configure', 'integrate'],
        'complex': ['architecture', 'distributed', 'scalable', 'fault-tolerant', 'enterprise']
    }
    
    detected_complexity = 'medium'  # Default
    for level, indicators in complexity_indicators.items():
        if any(indicator in query.lower() for indicator in indicators):
            detected_complexity = level
            break
    
    complexity_consistent = detected_complexity == declared_complexity
    
    return {
        'declared_domain': declared_domain,
        'detected_domains': detected_domains,
        'domain_consistent': domain_consistent,
        'declared_complexity': declared_complexity,
        'detected_complexity': detected_complexity,
        'complexity_consistent': complexity_consistent,
        'quality_flags': [] if domain_consistent and complexity_consistent else ['domain_mismatch']
    }
```

## 2. Category-Level Validation

### Complexity Distribution Analysis
```python
def validate_complexity_distribution(datapoints: List[TrainingDataPoint]) -> Dict[str, Any]:
    """Validate distribution balance across complexity levels."""
    
    # Group by complexity level
    by_complexity = {}
    for point in datapoints:
        level = point.expected_complexity_level
        if level not in by_complexity:
            by_complexity[level] = []
        by_complexity[level].append(point)
    
    # Calculate distribution metrics
    total_samples = len(datapoints)
    distribution = {level: len(points)/total_samples for level, points in by_complexity.items()}
    
    # Expected balanced distribution (adjustable)
    target_distribution = {'simple': 0.35, 'medium': 0.4, 'complex': 0.25}
    
    # Calculate distribution quality
    distribution_errors = {}
    for level, target_pct in target_distribution.items():
        actual_pct = distribution.get(level, 0)
        distribution_errors[level] = abs(actual_pct - target_pct)
    
    overall_balance_score = 1 - np.mean(list(distribution_errors.values()))
    
    # Statistical tests for distribution quality
    chi_square_stat, p_value = stats.chisquare(
        [len(by_complexity.get(level, [])) for level in target_distribution.keys()],
        [target_distribution[level] * total_samples for level in target_distribution.keys()]
    )
    
    return {
        'actual_distribution': distribution,
        'target_distribution': target_distribution,
        'distribution_errors': distribution_errors,
        'balance_score': overall_balance_score,
        'chi_square_stat': chi_square_stat,
        'chi_square_p_value': p_value,
        'well_balanced': overall_balance_score > 0.8 and p_value > 0.05
    }
```

### View Score Distribution Analysis
```python
def validate_view_score_distributions(datapoints: List[TrainingDataPoint]) -> Dict[str, Any]:
    """Validate that view scores follow expected statistical distributions."""
    
    view_names = ['technical', 'linguistic', 'task', 'semantic', 'computational']
    view_analyses = {}
    
    for view_name in view_names:
        scores = [dp.view_scores[view_name].complexity_score for dp in datapoints]
        
        # Distribution tests
        shapiro_stat, shapiro_p = stats.shapiro(scores)
        kstest_stat, kstest_p = stats.kstest(scores, 'norm')
        
        # Descriptive statistics
        analysis = {
            'mean': np.mean(scores),
            'std': np.std(scores),
            'min': np.min(scores),
            'max': np.max(scores),
            'median': np.median(scores),
            'skewness': stats.skew(scores),
            'kurtosis': stats.kurtosis(scores),
            'shapiro_stat': shapiro_stat,
            'shapiro_p_value': shapiro_p,
            'kstest_stat': kstest_stat,
            'kstest_p_value': kstest_p,
            'normal_distribution': shapiro_p > 0.05,
            'full_range_coverage': (np.max(scores) - np.min(scores)) > 0.7,
            'reasonable_variance': 0.05 < np.std(scores) < 0.3
        }
        
        view_analyses[view_name] = analysis
    
    # Cross-view correlation analysis
    correlation_matrix = np.corrcoef([
        [dp.view_scores[view].complexity_score for dp in datapoints] 
        for view in view_names
    ])
    
    return {
        'view_analyses': view_analyses,
        'cross_view_correlations': {
            view_names[i]: {view_names[j]: correlation_matrix[i][j] for j in range(len(view_names))}
            for i in range(len(view_names))
        },
        'correlation_health': validate_correlation_health(correlation_matrix)
    }
```

### Feature Distribution Validation
```python
def validate_feature_distributions(datapoints: List[TrainingDataPoint]) -> Dict[str, Any]:
    """Validate that extracted features have realistic distributions."""
    
    feature_analyses = {}
    
    # Collect all features across views
    all_features = {}
    for dp in datapoints:
        for view_name, view_data in dp.view_scores.items():
            for feature_name, feature_value in view_data.feature_values.items():
                full_feature_name = f"{view_name}_{feature_name}"
                if full_feature_name not in all_features:
                    all_features[full_feature_name] = []
                all_features[full_feature_name].append(feature_value)
    
    # Analyze each feature
    for feature_name, values in all_features.items():
        if len(values) < 10:  # Skip features with too few samples
            continue
            
        # Remove None/invalid values
        clean_values = [v for v in values if v is not None and not np.isnan(v)]
        
        if not clean_values:
            continue
            
        analysis = {
            'count': len(clean_values),
            'mean': np.mean(clean_values),
            'std': np.std(clean_values),
            'min': np.min(clean_values),
            'max': np.max(clean_values),
            'zeros_percentage': sum(1 for v in clean_values if v == 0) / len(clean_values),
            'outliers_percentage': detect_outlier_percentage(clean_values)
        }
        
        # Feature-specific validation
        analysis['realistic_range'] = validate_feature_range(feature_name, clean_values)
        analysis['distribution_quality'] = assess_feature_distribution_quality(clean_values)
        
        feature_analyses[feature_name] = analysis
    
    return feature_analyses
```

## 3. Dataset-Level Validation

### Coverage Analysis
```python
def validate_dataset_coverage(datapoints: List[TrainingDataPoint]) -> Dict[str, Any]:
    """Validate comprehensive coverage of feature space and query types."""
    
    # Domain coverage
    domains = [dp.metadata.domain for dp in datapoints]
    domain_distribution = {domain: domains.count(domain)/len(domains) for domain in set(domains)}
    
    # Query type coverage  
    query_types = [dp.metadata.query_type for dp in datapoints]
    query_type_distribution = {qtype: query_types.count(qtype)/len(query_types) for qtype in set(query_types)}
    
    # Complexity category coverage
    complexity_categories = [dp.metadata.complexity_category for dp in datapoints]
    category_distribution = {cat: complexity_categories.count(cat)/len(complexity_categories) for cat in set(complexity_categories)}
    
    # Feature space coverage (using clustering)
    feature_vectors = extract_feature_vectors_for_clustering(datapoints)
    coverage_score = calculate_feature_space_coverage(feature_vectors)
    
    return {
        'domain_coverage': {
            'distribution': domain_distribution,
            'entropy': stats.entropy(list(domain_distribution.values())),
            'well_covered': len(domain_distribution) >= 3 and min(domain_distribution.values()) > 0.15
        },
        'query_type_coverage': {
            'distribution': query_type_distribution,
            'entropy': stats.entropy(list(query_type_distribution.values())),
            'well_covered': len(query_type_distribution) >= 4 and min(query_type_distribution.values()) > 0.1
        },
        'complexity_category_coverage': {
            'distribution': category_distribution,
            'entropy': stats.entropy(list(category_distribution.values()))
        },
        'feature_space_coverage': coverage_score
    }
```

### Dataset Health Metrics
```python
def calculate_overall_dataset_health(validation_results: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate overall dataset health score and recommendations."""
    
    health_components = {
        'individual_entry_quality': 0.0,
        'category_balance': 0.0, 
        'feature_distribution_health': 0.0,
        'coverage_completeness': 0.0,
        'statistical_validity': 0.0
    }
    
    # Individual entry quality (from validation results)
    individual_scores = [entry['quality_score'] for entry in validation_results.get('individual_entries', [])]
    health_components['individual_entry_quality'] = np.mean(individual_scores) if individual_scores else 0
    
    # Category balance
    balance_score = validation_results.get('complexity_distribution', {}).get('balance_score', 0)
    health_components['category_balance'] = balance_score
    
    # Feature distribution health
    feature_health_scores = []
    for feature_analysis in validation_results.get('feature_distributions', {}).values():
        if feature_analysis.get('realistic_range', False) and feature_analysis.get('distribution_quality', 0) > 0.7:
            feature_health_scores.append(1.0)
        else:
            feature_health_scores.append(0.5)
    health_components['feature_distribution_health'] = np.mean(feature_health_scores) if feature_health_scores else 0
    
    # Coverage completeness
    coverage = validation_results.get('coverage_analysis', {})
    coverage_scores = []
    for coverage_type in ['domain_coverage', 'query_type_coverage']:
        if coverage.get(coverage_type, {}).get('well_covered', False):
            coverage_scores.append(1.0)
        else:
            coverage_scores.append(0.5)
    health_components['coverage_completeness'] = np.mean(coverage_scores)
    
    # Statistical validity
    view_dist = validation_results.get('view_score_distributions', {})
    valid_distributions = sum(1 for analysis in view_dist.get('view_analyses', {}).values() 
                             if analysis.get('reasonable_variance', False))
    health_components['statistical_validity'] = valid_distributions / 5 if view_dist else 0
    
    # Overall health score (weighted)
    weights = {
        'individual_entry_quality': 0.3,
        'category_balance': 0.2,
        'feature_distribution_health': 0.2, 
        'coverage_completeness': 0.2,
        'statistical_validity': 0.1
    }
    
    overall_health = sum(health_components[component] * weights[component] 
                        for component in health_components)
    
    # Generate recommendations
    recommendations = generate_improvement_recommendations(health_components, validation_results)
    
    return {
        'overall_health_score': overall_health,
        'health_components': health_components,
        'health_grade': assign_health_grade(overall_health),
        'recommendations': recommendations,
        'ready_for_training': overall_health > 0.8
    }
```

## Quality Thresholds and Standards

### Acceptance Criteria
```python
QUALITY_THRESHOLDS = {
    'individual_entry': {
        'view_score_variance': 0.16,       # std <= 0.4
        'expected_score_diff': 0.2,        # |expected - mean_views| <= 0.2
        'feature_alignment_error': 0.15,   # Feature-score alignment
        'confidence_calibration_error': 0.15,
        'realism_score': 0.7
    },
    'category_level': {
        'balance_score': 0.8,              # Distribution balance
        'feature_variance_min': 0.05,      # Minimum feature variance
        'feature_variance_max': 0.3,       # Maximum feature variance
        'cross_correlation_max': 0.85      # Max view correlation
    },
    'dataset_level': {
        'overall_health': 0.8,             # Overall quality
        'domain_entropy_min': 1.0,         # Domain diversity
        'feature_coverage': 0.8,           # Feature space coverage
        'sample_size_min': 500             # Minimum total samples
    }
}
```

This framework provides comprehensive validation at three levels:
1. **Individual entries** - Internal consistency and realism
2. **Categories** - Distribution balance and statistical properties  
3. **Dataset-wide** - Coverage, diversity, and overall quality

The framework ensures the Claude-generated training data meets rigorous statistical standards suitable for training robust ML models.