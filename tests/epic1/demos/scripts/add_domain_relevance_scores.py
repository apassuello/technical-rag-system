#!/usr/bin/env python3
"""
Add Domain Relevance Scores to Epic1 Training Dataset

This script implements the 3-tier domain relevance scoring system:
- High Relevance (0.8-1.0): Clearly RISC-V related
- Medium Relevance (0.3-0.7): General architecture or borderline  
- Low Relevance (0.0-0.2): General technical or non-technical

Usage:
    python add_domain_relevance_scores.py
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Tuple
from collections import Counter
import random

class DomainRelevanceScorer:
    """
    3-tier domain relevance scoring for RISC-V vs general technical queries.
    """
    
    def __init__(self):
        # High relevance indicators - clearly RISC-V specific
        self.high_relevance_keywords = [
            'risc-v', 'riscv', 'risc v', 'risc_v',
            'rv32', 'rv64', 'rv128',
            'vector extension', 'rvv', 'risc-v vector',
            'privileged instruction', 'privileged mode',
            'risc-v specification', 'risc-v isa',
            'risc-v assembly', 'risc-v processor',
            'risc-v architecture', 'risc-v implementation',
            'hart', 'risc-v hart',  # Hardware thread
            'fence instruction', 'fence.i',
            'csr', 'control and status register',
            'mtvec', 'mstatus', 'mcause', 'mtval',  # RISC-V CSRs
            'satp', 'sstatus', 'scause', 'stval',   # Supervisor CSRs
        ]
        
        # RISC-V specific instructions (higher confidence when in context)
        # Split into clear and ambiguous instructions
        self.riscv_clear_instructions = [
            'lui', 'auipc', 'jal', 'jalr',
            'beq', 'bne', 'blt', 'bge', 'bltu', 'bgeu',
            'lb', 'lh', 'lw', 'ld', 'lbu', 'lhu', 'lwu',
            'sb', 'sh', 'sw', 'sd',
            'addi', 'slti', 'sltiu', 'xori', 'ori', 'andi',
            'slli', 'srli', 'srai', 'slliw', 'srliw', 'sraiw',
            'addw', 'subw', 'sllw', 'srlw', 'sraw',
            'fence', 'fence.i', 'ecall', 'ebreak',
            'csrrw', 'csrrs', 'csrrc', 'csrrwi', 'csrrsi', 'csrrci',
            'mul', 'mulh', 'mulhsu', 'mulhu', 'div', 'divu', 'rem', 'remu',
            'mulw', 'divw', 'divuw', 'remw', 'remuw',
        ]
        
        # Ambiguous instructions that could be common words
        self.riscv_ambiguous_instructions = [
            'add', 'sub', 'sll', 'slt', 'sltu', 'xor', 'srl', 'sra', 'or', 'and'
        ]
        
        # Medium relevance indicators - general architecture terms
        self.medium_relevance_keywords = [
            'instruction set', 'isa ', ' isa',
            'processor architecture', 'cpu architecture',
            'assembly language', 'assembly programming',
            'instruction format', 'instruction encoding',
            'memory management unit', 'mmu',
            'virtual memory', 'page table',
            'cache coherence', 'cache hierarchy',
            'pipeline', 'out-of-order execution',
            'branch prediction', 'branch predictor',
            'exception handling', 'interrupt handling',
            'system call', 'syscall',
            'privilege level', 'supervisor mode', 'user mode',
            'atomic operation', 'memory ordering',
            'simd', 'vector processing',
            'floating point unit', 'fpu',
        ]
        
        # Low relevance indicators - general technical domains
        self.low_relevance_domains = [
            'web development', 'frontend', 'backend', 'full stack',
            'database', 'sql', 'nosql', 'mysql', 'postgresql', 'mongodb',
            'api', 'rest api', 'graphql', 'microservices',
            'cloud computing', 'aws', 'azure', 'gcp', 'kubernetes',
            'machine learning', 'ai', 'neural network', 'deep learning',
            'blockchain', 'cryptocurrency', 'smart contract',
            'mobile development', 'android', 'ios', 'react native',
            'cybersecurity', 'penetration testing', 'vulnerability',
            'data science', 'data analysis', 'big data',
            'devops', 'ci/cd', 'docker', 'containerization',
            'network security', 'firewall', 'vpn',
            'software testing', 'unit testing', 'integration testing',
        ]
        
        # Compile regex patterns for efficiency
        self.high_patterns = [re.compile(r'\b' + re.escape(kw) + r'\b', re.IGNORECASE) 
                             for kw in self.high_relevance_keywords]
        self.medium_patterns = [re.compile(r'\b' + re.escape(kw) + r'\b', re.IGNORECASE) 
                               for kw in self.medium_relevance_keywords]
        self.low_patterns = [re.compile(r'\b' + re.escape(kw) + r'\b', re.IGNORECASE) 
                            for kw in self.low_relevance_domains]
        self.clear_instruction_patterns = [re.compile(r'\b' + re.escape(inst) + r'\b', re.IGNORECASE) 
                                         for inst in self.riscv_clear_instructions]
        self.ambiguous_instruction_patterns = [re.compile(r'\b' + re.escape(inst) + r'\b', re.IGNORECASE) 
                                             for inst in self.riscv_ambiguous_instructions]
    
    def score_query(self, query_text: str) -> Tuple[float, str, Dict]:
        """
        Score a query for RISC-V domain relevance.
        
        Args:
            query_text: The query string to analyze
            
        Returns:
            Tuple of (score, tier, details)
        """
        query_lower = query_text.lower()
        details = {
            'high_matches': [],
            'medium_matches': [],
            'low_matches': [],
            'instruction_matches': [],
            'reasoning': ''
        }
        
        # Check for high relevance patterns
        high_matches = []
        for pattern, keyword in zip(self.high_patterns, self.high_relevance_keywords):
            if pattern.search(query_text):
                high_matches.append(keyword)
        details['high_matches'] = high_matches
        
        # Check for clear RISC-V instructions
        clear_instruction_matches = []
        for pattern, instruction in zip(self.clear_instruction_patterns, self.riscv_clear_instructions):
            if pattern.search(query_text):
                clear_instruction_matches.append(instruction)
        
        # Check for ambiguous instructions (only count if in architectural context)
        ambiguous_instruction_matches = []
        has_arch_context = any(word in query_lower for word in 
                              ['instruction', 'assembly', 'processor', 'architecture', 'isa', 'risc'])
        
        if has_arch_context:
            for pattern, instruction in zip(self.ambiguous_instruction_patterns, self.riscv_ambiguous_instructions):
                if pattern.search(query_text):
                    ambiguous_instruction_matches.append(instruction)
        
        # Combine instruction matches
        instruction_matches = clear_instruction_matches + ambiguous_instruction_matches
        details['instruction_matches'] = instruction_matches
        details['clear_instructions'] = clear_instruction_matches
        details['ambiguous_instructions'] = ambiguous_instruction_matches
        
        # Check for medium relevance patterns
        medium_matches = []
        for pattern, keyword in zip(self.medium_patterns, self.medium_relevance_keywords):
            if pattern.search(query_text):
                medium_matches.append(keyword)
        details['medium_matches'] = medium_matches
        
        # Check for low relevance patterns
        low_matches = []
        for pattern, keyword in zip(self.low_patterns, self.low_relevance_domains):
            if pattern.search(query_text):
                low_matches.append(keyword)
        details['low_matches'] = low_matches
        
        # Scoring logic
        if high_matches:
            # Clear RISC-V indicators -> High relevance
            score = 0.9 + min(0.1, len(high_matches) * 0.02)  # 0.9-1.0
            tier = "high_relevance"
            details['reasoning'] = f"Clear RISC-V indicators: {', '.join(high_matches[:3])}"
        
        elif instruction_matches and len(instruction_matches) >= 2:
            # Multiple RISC-V instructions -> High relevance
            score = 0.85 + min(0.15, len(instruction_matches) * 0.03)  # 0.85-1.0
            tier = "high_relevance"
            details['reasoning'] = f"Multiple RISC-V instructions: {', '.join(instruction_matches[:3])}"
        
        elif instruction_matches and any(arch_word in query_lower for arch_word in ['instruction', 'assembly', 'processor', 'architecture']):
            # Single instruction with architectural context -> High relevance
            score = 0.8 + min(0.1, len(instruction_matches) * 0.05)  # 0.8-0.9
            tier = "high_relevance"
            details['reasoning'] = f"RISC-V instruction in architectural context: {instruction_matches[0]}"
        
        elif instruction_matches:
            # Single instruction without clear context -> Medium relevance
            score = 0.5 + min(0.2, len(instruction_matches) * 0.1)  # 0.5-0.7
            tier = "medium_relevance"
            details['reasoning'] = f"Possible RISC-V instruction: {instruction_matches[0]}"
        
        elif medium_matches and not low_matches:
            # General architecture terms without conflicting domains -> Medium relevance
            score = 0.4 + min(0.3, len(medium_matches) * 0.1)  # 0.4-0.7
            tier = "medium_relevance"
            details['reasoning'] = f"General architecture terms: {', '.join(medium_matches[:2])}"
        
        elif medium_matches and low_matches:
            # Architecture terms but also other domain indicators -> Low relevance
            score = 0.1 + min(0.2, len(medium_matches) * 0.05)  # 0.1-0.3
            tier = "low_relevance"
            details['reasoning'] = f"Mixed domains: {', '.join(low_matches[:2])}"
        
        elif low_matches:
            # Clear other technical domains -> Low relevance
            score = 0.05 + min(0.15, len(low_matches) * 0.05)  # 0.05-0.2
            tier = "low_relevance"
            details['reasoning'] = f"Other technical domains: {', '.join(low_matches[:2])}"
        
        else:
            # No clear indicators -> Low relevance (default)
            score = 0.1
            tier = "low_relevance"
            details['reasoning'] = "No clear domain indicators"
        
        return score, tier, details

def process_dataset(input_file: Path, output_file: Path) -> Dict:
    """
    Process Epic1 dataset to add domain relevance scores.
    
    Args:
        input_file: Path to input JSON dataset
        output_file: Path to output JSON dataset with scores
        
    Returns:
        Dictionary with processing statistics
    """
    scorer = DomainRelevanceScorer()
    
    # Load dataset
    with open(input_file, 'r') as f:
        data = json.load(f)
    
    print(f"Processing {len(data)} queries from {input_file}")
    
    # Process each query
    stats = {
        'total_queries': len(data),
        'high_relevance': 0,
        'medium_relevance': 0,
        'low_relevance': 0,
        'score_distribution': [],
        'examples_by_tier': {'high_relevance': [], 'medium_relevance': [], 'low_relevance': []}
    }
    
    for i, item in enumerate(data):
        query_text = item['query_text']
        score, tier, details = scorer.score_query(query_text)
        
        # Add domain relevance fields
        item['domain_relevance_score'] = round(score, 3)
        item['domain_relevance_tier'] = tier
        item['domain_relevance_details'] = details
        
        # Update statistics
        stats[tier] += 1
        stats['score_distribution'].append(score)
        
        # Collect examples for validation
        if len(stats['examples_by_tier'][tier]) < 5:
            stats['examples_by_tier'][tier].append({
                'query': query_text[:100] + '...' if len(query_text) > 100 else query_text,
                'score': score,
                'reasoning': details['reasoning'],
                'complexity': item['expected_complexity_score']
            })
        
        if (i + 1) % 100 == 0:
            print(f"  Processed {i + 1}/{len(data)} queries...")
    
    # Save enhanced dataset
    with open(output_file, 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"Enhanced dataset saved to {output_file}")
    
    # Calculate statistics
    stats['avg_score'] = sum(stats['score_distribution']) / len(stats['score_distribution'])
    stats['high_percentage'] = stats['high_relevance'] / stats['total_queries'] * 100
    stats['medium_percentage'] = stats['medium_relevance'] / stats['total_queries'] * 100
    stats['low_percentage'] = stats['low_relevance'] / stats['total_queries'] * 100
    
    return stats

def print_statistics(stats: Dict):
    """Print processing statistics and examples."""
    print(f"\n{'='*60}")
    print("DOMAIN RELEVANCE SCORING RESULTS")
    print(f"{'='*60}")
    
    print(f"Total queries processed: {stats['total_queries']}")
    print(f"Average domain relevance score: {stats['avg_score']:.3f}")
    
    print(f"\nDistribution by tier:")
    print(f"  High Relevance (RISC-V):    {stats['high_relevance']:3d} ({stats['high_percentage']:5.1f}%)")
    print(f"  Medium Relevance (Border):  {stats['medium_relevance']:3d} ({stats['medium_percentage']:5.1f}%)")
    print(f"  Low Relevance (Other):      {stats['low_relevance']:3d} ({stats['low_percentage']:5.1f}%)")
    
    print(f"\nScore distribution:")
    scores = stats['score_distribution']
    print(f"  Min: {min(scores):.3f}, Max: {max(scores):.3f}")
    print(f"  High tier (0.8-1.0): {len([s for s in scores if s >= 0.8])} queries")
    print(f"  Medium tier (0.3-0.7): {len([s for s in scores if 0.3 <= s < 0.8])} queries")
    print(f"  Low tier (0.0-0.3): {len([s for s in scores if s < 0.3])} queries")
    
    print(f"\nExamples by tier:")
    for tier, examples in stats['examples_by_tier'].items():
        print(f"\n  {tier.upper().replace('_', ' ')}:")
        for ex in examples:
            print(f"    Score: {ex['score']:.3f} | Complexity: {ex['complexity']:.3f}")
            print(f"    Query: {ex['query']}")
            print(f"    Reasoning: {ex['reasoning']}")
            print()

def main():
    """Main processing function."""
    data_dir = Path("data/training")
    
    # Process main Epic1 dataset
    input_file = data_dir / "epic1_training_dataset_679_samples.json"
    output_file = data_dir / "epic1_training_dataset_679_with_domain_scores.json"
    
    if not input_file.exists():
        print(f"Error: Input file not found: {input_file}")
        return
    
    print("Epic 1 Domain Relevance Scoring")
    print("Adding 3-tier domain relevance scores to training dataset")
    print()
    
    # Process dataset
    stats = process_dataset(input_file, output_file)
    
    # Print results
    print_statistics(stats)
    
    # Save statistics
    stats_file = data_dir / "domain_relevance_statistics.json"
    with open(stats_file, 'w') as f:
        json.dump(stats, f, indent=2, default=str)
    
    print(f"\nStatistics saved to {stats_file}")
    
    # Generate validation sample
    validation_file = data_dir / "domain_relevance_validation_sample.json"
    
    # Load the enhanced dataset to create validation sample
    with open(output_file, 'r') as f:
        enhanced_data = json.load(f)
    
    # Stratified sample for manual validation
    validation_sample = []
    
    for tier in ['high_relevance', 'medium_relevance', 'low_relevance']:
        tier_queries = [item for item in enhanced_data if item['domain_relevance_tier'] == tier]
        
        # Sample 17, 17, 16 for 50 total
        sample_size = 17 if tier in ['high_relevance', 'medium_relevance'] else 16
        sample_size = min(sample_size, len(tier_queries))
        
        if tier_queries:
            sampled = random.sample(tier_queries, sample_size)
            for item in sampled:
                validation_sample.append({
                    'query_text': item['query_text'],
                    'predicted_tier': item['domain_relevance_tier'],
                    'predicted_score': item['domain_relevance_score'],
                    'reasoning': item['domain_relevance_details']['reasoning'],
                    'complexity_score': item['expected_complexity_score'],
                    'manual_validation': None,  # To be filled manually
                    'notes': ""  # For validation notes
                })
    
    with open(validation_file, 'w') as f:
        json.dump(validation_sample, f, indent=2)
    
    print(f"\nValidation sample ({len(validation_sample)} queries) saved to {validation_file}")
    print("Please manually validate the sample to check scoring accuracy.")

if __name__ == "__main__":
    main()