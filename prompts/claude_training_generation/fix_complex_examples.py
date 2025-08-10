#!/usr/bin/env python3
"""
Fix all examples in complex_focus to use simple structure.
"""

import re

file_path = "/Users/apa/ml_projects/rag-portfolio/project-1-technical-rag/prompts/claude_training_generation/claude_prompt_complex_focus.md"

# Fixed examples with simple structure
example1_fixed = '''### Example 1: Complex-Medium Boundary (Score: 0.68)
```json
{
  "query_text": "How can I implement a distributed consensus algorithm with Byzantine fault tolerance that maintains linearizability while optimizing for network partition recovery?",
  "expected_complexity_score": 0.68,
  "expected_complexity_level": "complex",
  "view_scores": {
    "technical": 0.72,
    "linguistic": 0.62,
    "task": 0.71,
    "semantic": 0.69,
    "computational": 0.68
  },
  "confidence": 0.85,
  "metadata": {
    "domain": "academic",
    "query_type": "architecture",
    "generation_timestamp": "2025-08-07T20:00:00Z",
    "base_score": 0.68,
    "template_used": "none - natural generation"
  }
}
```

**Analysis**: Distributed consensus with Byzantine tolerance. Technical (0.72) - advanced distributed systems theory. Linguistic (0.62) - complex technical precision. Task (0.71) - Bloom's Level 5 synthesis. Semantic (0.69) - high conceptual density. Computational (0.68) - complex distributed algorithms.'''

example2_fixed = '''### Example 2: Clearly Complex (Score: 0.81)
```json
{
  "query_text": "What are the theoretical and practical implications of implementing a CRDT-based eventually consistent data store with causal consistency guarantees for a globally distributed collaborative editing system handling millions of concurrent operations with sub-100ms conflict resolution?",
  "expected_complexity_score": 0.81,
  "expected_complexity_level": "complex",
  "view_scores": {
    "technical": 0.86,
    "linguistic": 0.75,
    "task": 0.84,
    "semantic": 0.82,
    "computational": 0.80
  },
  "confidence": 0.82,
  "metadata": {
    "domain": "research",
    "query_type": "evaluation",
    "generation_timestamp": "2025-08-07T20:00:00Z",
    "base_score": 0.81,
    "template_used": "none - natural generation"
  }
}
```

**Analysis**: CRDT-based distributed systems. Technical (0.86) - cutting-edge distributed research. Linguistic (0.75) - highly complex sentence. Task (0.84) - Bloom's Level 6 evaluation. Semantic (0.82) - extreme conceptual density. Computational (0.80) - advanced algorithms with performance constraints.'''

example3_fixed = '''### Example 3: High Complex (Score: 0.87)
```json
{
  "query_text": "How would you architect a quantum-resistant cryptographic protocol for secure multi-party computation that maintains zero-knowledge properties while enabling homomorphic operations on encrypted data at petabyte scale with provable security guarantees against both classical and quantum adversaries?",
  "expected_complexity_score": 0.87,
  "expected_complexity_level": "complex",
  "view_scores": {
    "technical": 0.92,
    "linguistic": 0.80,
    "task": 0.90,
    "semantic": 0.88,
    "computational": 0.86
  },
  "confidence": 0.80,
  "metadata": {
    "domain": "research",
    "query_type": "synthesis",
    "generation_timestamp": "2025-08-07T20:00:00Z",
    "base_score": 0.87,
    "template_used": "none - natural generation"
  }
}
```

**Analysis**: Quantum-resistant cryptography. Technical (0.92) - cutting-edge cryptographic research. Linguistic (0.80) - extremely complex multi-clause. Task (0.90) - Bloom's Level 6 synthesis. Semantic (0.88) - maximum conceptual complexity. Computational (0.86) - novel algorithms with formal verification.'''

# Read the file
with open(file_path, 'r') as f:
    content = f.read()

# Find and replace each example
# Pattern to match Example 1 (everything from ### Example 1 to right before ### Example 2)
pattern1 = r'### Example 1:.*?(?=### Example 2:)'
content = re.sub(pattern1, example1_fixed + '\n\n', content, flags=re.DOTALL)

# Pattern to match Example 2 (everything from ### Example 2 to right before ### Example 3)
pattern2 = r'### Example 2:.*?(?=### Example 3:)'
content = re.sub(pattern2, example2_fixed + '\n\n', content, flags=re.DOTALL)

# Pattern to match Example 3 (everything from ### Example 3 to right before ## Expert-Level)
pattern3 = r'### Example 3:.*?(?=## Expert-Level)'
content = re.sub(pattern3, example3_fixed + '\n\n', content, flags=re.DOTALL)

# Write back
with open(file_path, 'w') as f:
    f.write(content)

print("✅ Fixed all 3 examples in complex_focus.md")