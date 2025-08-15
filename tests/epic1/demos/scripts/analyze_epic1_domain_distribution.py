#!/usr/bin/env python3
"""
Epic1 Domain Distribution Analysis

Analyzes training datasets to understand domain distribution and design
domain relevance scoring schema for multi-model routing.
"""

import json
import os
import re
from collections import defaultdict, Counter
from pathlib import Path
from typing import Dict, List, Tuple, Set
import statistics

def load_json_file(filepath: str) -> List[Dict]:
    """Load JSON training data file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except Exception as e:
        print(f"Error loading {filepath}: {e}")
        return []

def extract_domain_keywords(query_text: str) -> Set[str]:
    """Extract domain-specific keywords and technical terms."""
    # Convert to lowercase for analysis
    text = query_text.lower()
    
    # Define domain keyword patterns
    domain_patterns = {
        'riscv': [
            'risc-v', 'riscv', 'rv32', 'rv64', 'privileged', 'unprivileged',
            'instruction set', 'isa', 'vector extension', 'compressed',
            'atomic', 'fence', 'csr', 'control status register', 'hart',
            'ecall', 'ebreak', 'mret', 'sret', 'wfi', 'machine mode',
            'supervisor mode', 'user mode', 'page table', 'satp',
            'mstatus', 'mtvec', 'mie', 'mip', 'mcause', 'mtval',
            'misa', 'mvendorid', 'marchid', 'mimpid', 'mhartid',
            'zifencei', 'zicsr', 'zba', 'zbb', 'zbc', 'zbs',
            'floating point', 'fp', 'double precision', 'single precision',
            'amo', 'load reserve', 'store conditional', 'lr', 'sc'
        ],
        'web_dev': [
            'javascript', 'react', 'angular', 'vue', 'node.js', 'express',
            'html', 'css', 'dom', 'api', 'rest', 'graphql', 'json',
            'http', 'https', 'ssl', 'tls', 'cors', 'csrf', 'xss',
            'authentication', 'authorization', 'jwt', 'oauth', 'session',
            'cookie', 'local storage', 'webpack', 'babel', 'typescript',
            'npm', 'yarn', 'package.json', 'bootstrap', 'sass', 'less'
        ],
        'databases': [
            'sql', 'mysql', 'postgresql', 'mongodb', 'redis', 'nosql',
            'database', 'query', 'index', 'primary key', 'foreign key',
            'join', 'select', 'insert', 'update', 'delete', 'transaction',
            'acid', 'normalization', 'schema', 'table', 'collection',
            'document', 'relational', 'orm', 'migration', 'backup'
        ],
        'ai_ml': [
            'machine learning', 'deep learning', 'neural network', 'cnn',
            'rnn', 'lstm', 'transformer', 'attention', 'bert', 'gpt',
            'pytorch', 'tensorflow', 'keras', 'scikit-learn', 'pandas',
            'numpy', 'gradient descent', 'backpropagation', 'loss function',
            'optimizer', 'regularization', 'overfitting', 'cross validation',
            'feature engineering', 'classification', 'regression', 'clustering'
        ],
        'systems': [
            'operating system', 'kernel', 'process', 'thread', 'memory',
            'virtual memory', 'cache', 'cpu', 'scheduling', 'synchronization',
            'mutex', 'semaphore', 'deadlock', 'file system', 'i/o',
            'interrupt', 'system call', 'driver', 'dma', 'buffer',
            'pipeline', 'concurrency', 'parallelism', 'multicore'
        ],
        'security': [
            'security', 'encryption', 'decryption', 'cryptography', 'hash',
            'digital signature', 'certificate', 'pki', 'vulnerability',
            'exploit', 'buffer overflow', 'injection', 'malware',
            'firewall', 'intrusion detection', 'penetration testing',
            'authentication', 'authorization', 'access control'
        ],
        'compilers': [
            'compiler', 'optimization', 'parsing', 'lexer', 'ast',
            'intermediate representation', 'code generation', 'register allocation',
            'instruction scheduling', 'loop optimization', 'vectorization',
            'inlining', 'dead code elimination', 'constant folding',
            'gcc', 'llvm', 'clang', 'assembly', 'linker', 'loader'
        ],
        'cloud_devops': [
            'docker', 'kubernetes', 'container', 'orchestration', 'microservices',
            'devops', 'ci/cd', 'jenkins', 'github actions', 'terraform',
            'ansible', 'aws', 'azure', 'gcp', 'cloud', 'serverless',
            'lambda', 'scaling', 'load balancer', 'monitoring', 'logging'
        ]
    }
    
    found_keywords = set()
    for domain, keywords in domain_patterns.items():
        for keyword in keywords:
            if keyword in text:
                found_keywords.add(f"{domain}:{keyword}")
    
    return found_keywords

def classify_query_domain(query_text: str, metadata: Dict = None) -> str:
    """Classify query into primary domain based on content analysis."""
    keywords = extract_domain_keywords(query_text)
    
    # Count keywords by domain
    domain_counts = defaultdict(int)
    for keyword in keywords:
        domain = keyword.split(':')[0]
        domain_counts[domain] += 1
    
    # Check metadata domain if available
    metadata_domain = None
    if metadata and 'domain' in metadata:
        metadata_domain = metadata['domain']
    
    # Determine primary domain
    if domain_counts:
        primary_domain = max(domain_counts.items(), key=lambda x: x[1])[0]
        return primary_domain
    elif metadata_domain in ['academic', 'technical']:
        # For generic metadata, try to infer from content
        text_lower = query_text.lower()
        if any(term in text_lower for term in ['risc', 'rv32', 'rv64', 'instruction']):
            return 'riscv'
        elif any(term in text_lower for term in ['web', 'javascript', 'react', 'api']):
            return 'web_dev'
        elif any(term in text_lower for term in ['database', 'sql', 'query']):
            return 'databases'
        elif any(term in text_lower for term in ['machine learning', 'neural', 'model']):
            return 'ai_ml'
        else:
            return 'general_technical'
    else:
        return metadata_domain or 'general_technical'

def analyze_complexity_distribution(queries: List[Dict]) -> Dict:
    """Analyze complexity level distribution."""
    complexity_counts = Counter()
    complexity_scores = []
    
    for query in queries:
        level = query.get('expected_complexity_level', 'unknown')
        score = query.get('expected_complexity_score', 0)
        
        complexity_counts[level] += 1
        if score > 0:
            complexity_scores.append(score)
    
    return {
        'counts': dict(complexity_counts),
        'scores': {
            'mean': statistics.mean(complexity_scores) if complexity_scores else 0,
            'median': statistics.median(complexity_scores) if complexity_scores else 0,
            'std': statistics.stdev(complexity_scores) if len(complexity_scores) > 1 else 0,
            'min': min(complexity_scores) if complexity_scores else 0,
            'max': max(complexity_scores) if complexity_scores else 0
        }
    }

def analyze_domain_patterns(queries: List[Dict]) -> Dict:
    """Analyze domain distribution and patterns."""
    domain_counts = Counter()
    domain_complexity = defaultdict(list)
    domain_examples = defaultdict(list)
    riscv_queries = []
    
    for query in queries:
        query_text = query.get('query_text', '')
        metadata = query.get('metadata', {})
        complexity_score = query.get('expected_complexity_score', 0)
        
        domain = classify_query_domain(query_text, metadata)
        domain_counts[domain] += 1
        domain_complexity[domain].append(complexity_score)
        
        # Store examples (limit per domain)
        if len(domain_examples[domain]) < 3:
            domain_examples[domain].append({
                'query': query_text[:100] + '...' if len(query_text) > 100 else query_text,
                'complexity': complexity_score,
                'level': query.get('expected_complexity_level', 'unknown')
            })
        
        # Collect RISC-V specific queries
        if domain == 'riscv':
            riscv_queries.append(query)
    
    # Calculate domain complexity statistics
    domain_stats = {}
    for domain, scores in domain_complexity.items():
        if scores:
            domain_stats[domain] = {
                'count': len(scores),
                'avg_complexity': statistics.mean(scores),
                'complexity_range': (min(scores), max(scores))
            }
    
    return {
        'domain_counts': dict(domain_counts),
        'domain_stats': domain_stats,
        'domain_examples': dict(domain_examples),
        'riscv_queries': riscv_queries
    }

def main():
    """Main analysis function."""
    data_dir = Path("data/training")
    
    # Training dataset files to analyze
    dataset_files = [
        "epic1_training_dataset_679_samples.json",
        "epic1/epic1_training_dataset_215_samples.json",
        "epic1/epic1_claude_generated_dataset_215_samples.json"
    ]
    
    # Additional training files in subdirectories
    views_training_dir = data_dir / "views_training_queries"
    if views_training_dir.exists():
        for file in views_training_dir.glob("*.json"):
            dataset_files.append(f"views_training_queries/{file.name}")
    
    all_queries = []
    file_analysis = {}
    
    # Load and analyze each dataset
    print("🔍 Loading Epic1 Training Datasets...")
    print("=" * 60)
    
    for dataset_file in dataset_files:
        filepath = data_dir / dataset_file
        if filepath.exists():
            queries = load_json_file(str(filepath))
            if queries:
                all_queries.extend(queries)
                
                # Analyze this specific file
                domain_analysis = analyze_domain_patterns(queries)
                complexity_analysis = analyze_complexity_distribution(queries)
                
                file_analysis[dataset_file] = {
                    'query_count': len(queries),
                    'domains': domain_analysis['domain_counts'],
                    'complexity': complexity_analysis['counts'],
                    'riscv_count': len(domain_analysis['riscv_queries'])
                }
                
                print(f"📁 {dataset_file}")
                print(f"   Queries: {len(queries)}")
                print(f"   RISC-V queries: {len(domain_analysis['riscv_queries'])}")
                print(f"   Top domains: {dict(Counter(domain_analysis['domain_counts']).most_common(3))}")
                print()
    
    # Overall analysis
    print("📊 OVERALL DOMAIN DISTRIBUTION ANALYSIS")
    print("=" * 60)
    
    total_queries = len(all_queries)
    print(f"Total queries analyzed: {total_queries}")
    
    # Domain analysis
    overall_domain_analysis = analyze_domain_patterns(all_queries)
    overall_complexity_analysis = analyze_complexity_distribution(all_queries)
    
    print(f"\n🎯 DOMAIN BREAKDOWN:")
    print("-" * 30)
    domain_counts = overall_domain_analysis['domain_counts']
    for domain, count in sorted(domain_counts.items(), key=lambda x: x[1], reverse=True):
        percentage = (count / total_queries) * 100
        print(f"{domain:20} {count:4d} ({percentage:5.1f}%)")
    
    print(f"\n🔬 RISC-V ANALYSIS:")
    print("-" * 30)
    riscv_queries = overall_domain_analysis['riscv_queries']
    riscv_count = len(riscv_queries)
    riscv_percentage = (riscv_count / total_queries) * 100
    print(f"RISC-V queries: {riscv_count} ({riscv_percentage:.1f}%)")
    
    if riscv_queries:
        riscv_complexity = [q.get('expected_complexity_score', 0) for q in riscv_queries]
        riscv_levels = Counter([q.get('expected_complexity_level', 'unknown') for q in riscv_queries])
        print(f"RISC-V complexity distribution: {dict(riscv_levels)}")
        print(f"RISC-V avg complexity: {statistics.mean(riscv_complexity):.3f}")
    
    print(f"\n⚡ COMPLEXITY ANALYSIS:")
    print("-" * 30)
    complexity_counts = overall_complexity_analysis['counts']
    for level, count in complexity_counts.items():
        percentage = (count / total_queries) * 100
        print(f"{level:15} {count:4d} ({percentage:5.1f}%)")
    
    scores = overall_complexity_analysis['scores']
    print(f"\nComplexity scores - Mean: {scores['mean']:.3f}, Range: [{scores['min']:.3f}, {scores['max']:.3f}]")
    
    print(f"\n🔍 DOMAIN EXAMPLES:")
    print("-" * 30)
    for domain, examples in overall_domain_analysis['domain_examples'].items():
        print(f"\n{domain.upper()}:")
        for i, example in enumerate(examples, 1):
            print(f"  {i}. [{example['level']}] {example['query']}")
    
    # Domain relevance scoring recommendations
    print(f"\n💡 DOMAIN RELEVANCE SCORING RECOMMENDATIONS:")
    print("=" * 60)
    
    print("1. RISC-V DOMAIN DETECTION:")
    print("   - Primary indicators: 'risc-v', 'riscv', 'rv32', 'rv64'")
    print("   - Secondary indicators: 'instruction set', 'isa', 'hart', 'csr'")
    print("   - Context indicators: 'privileged mode', 'vector extension'")
    
    print("\n2. SCORING SCHEMA RECOMMENDATIONS:")
    print("   - RISC-V Relevant (0.8-1.0): Direct RISC-V content")
    print("   - Systems/Architecture (0.6-0.8): General systems concepts")
    print("   - Technical Adjacent (0.4-0.6): Related technical domains")
    print("   - General Technical (0.2-0.4): Generic technical content")
    print("   - Non-Technical (0.0-0.2): Unrelated content")
    
    print("\n3. COVERAGE GAPS IDENTIFIED:")
    non_riscv_percentage = 100 - riscv_percentage
    print(f"   - Non-RISC-V content: {non_riscv_percentage:.1f}%")
    print(f"   - Need more RISC-V specific queries for balanced training")
    print(f"   - Current dataset has good technical diversity")
    
    # Save detailed analysis
    analysis_results = {
        'summary': {
            'total_queries': total_queries,
            'riscv_queries': riscv_count,
            'riscv_percentage': riscv_percentage,
            'domain_distribution': domain_counts,
            'complexity_distribution': complexity_counts
        },
        'domain_analysis': overall_domain_analysis,
        'complexity_analysis': overall_complexity_analysis,
        'file_breakdown': file_analysis,
        'recommendations': {
            'domain_scoring_schema': {
                'riscv_relevant': {'range': [0.8, 1.0], 'description': 'Direct RISC-V content'},
                'systems_architecture': {'range': [0.6, 0.8], 'description': 'General systems concepts'},
                'technical_adjacent': {'range': [0.4, 0.6], 'description': 'Related technical domains'},
                'general_technical': {'range': [0.2, 0.4], 'description': 'Generic technical content'},
                'non_technical': {'range': [0.0, 0.2], 'description': 'Unrelated content'}
            }
        }
    }
    
    output_file = "epic1_domain_analysis_results.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(analysis_results, f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Detailed analysis saved to: {output_file}")

if __name__ == "__main__":
    main()