#!/usr/bin/env python3
"""
Fix all examples in medium_focus_2 to use simple structure.
"""

import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
file_path = str(PROJECT_ROOT / "prompts/claude_training_generation/claude_prompt_medium_focus_2.md")

# Fixed examples with simple structure
example1_fixed = '''### Example 1: Medium-Simple Boundary (Score: 0.36) - Data Engineering Focus
```json
{
  "query_text": "How can I optimize my ETL pipeline to handle large CSV files without running out of memory?",
  "expected_complexity_score": 0.36,
  "expected_complexity_level": "medium",
  "view_scores": {
    "technical": 0.40,
    "linguistic": 0.33,
    "task": 0.37,
    "semantic": 0.35,
    "computational": 0.36
  },
  "confidence": 0.88,
  "metadata": {
    "domain": "technical",
    "query_type": "optimization",
    "generation_timestamp": "2025-08-07T20:00:00Z",
    "base_score": 0.36,
    "template_used": "none - natural generation"
  }
}
```

**Analysis**: ETL optimization question. Technical (0.40) - ETL and memory management concepts. Linguistic (0.33) - clear technical question. Task (0.37) - Bloom's Level 3 application. Semantic (0.35) - data flow and constraints. Computational (0.36) - memory optimization strategies.'''

example2_fixed = '''### Example 2: Clear Medium (Score: 0.49) - Mobile Development Focus
```json
{
  "query_text": "What's the best strategy for managing state between native modules and React Native JavaScript code in a hybrid mobile app?",
  "expected_complexity_score": 0.49,
  "expected_complexity_level": "medium",
  "view_scores": {
    "technical": 0.53,
    "linguistic": 0.45,
    "task": 0.51,
    "semantic": 0.48,
    "computational": 0.48
  },
  "confidence": 0.85,
  "metadata": {
    "domain": "technical",
    "query_type": "architecture",
    "generation_timestamp": "2025-08-07T20:00:00Z",
    "base_score": 0.49,
    "template_used": "none - natural generation"
  }
}
```

**Analysis**: Cross-platform state management. Technical (0.53) - native bridge concepts. Linguistic (0.45) - complex multi-layer question. Task (0.51) - Bloom's Level 4 analysis. Semantic (0.48) - runtime environment interactions. Computational (0.48) - state synchronization patterns.'''

example3_fixed = '''### Example 3: Medium-Complex Boundary (Score: 0.64) - Testing & Quality Focus
```json
{
  "query_text": "How do I implement contract testing for microservices with consumer-driven contracts while maintaining backward compatibility during API evolution?",
  "expected_complexity_score": 0.64,
  "expected_complexity_level": "medium",
  "view_scores": {
    "technical": 0.67,
    "linguistic": 0.60,
    "task": 0.66,
    "semantic": 0.63,
    "computational": 0.65
  },
  "confidence": 0.82,
  "metadata": {
    "domain": "technical",
    "query_type": "implementation",
    "generation_timestamp": "2025-08-07T20:00:00Z",
    "base_score": 0.64,
    "template_used": "none - natural generation"
  }
}
```

**Analysis**: Contract testing architecture. Technical (0.67) - advanced testing patterns. Linguistic (0.60) - complex multi-clause sentence. Task (0.66) - Bloom's Level 5 synthesis. Semantic (0.63) - multiple interrelated concepts. Computational (0.65) - contract validation algorithms.'''

# Read the file
with open(file_path, 'r') as f:
    content = f.read()

# Find and replace each example
# We need to find the entire example blocks and replace them

# Pattern to match Example 1 (everything from ### Example 1 to right before ### Example 2)
pattern1 = r'### Example 1:.*?(?=### Example 2:)'
content = re.sub(pattern1, example1_fixed + '\n\n', content, flags=re.DOTALL)

# Pattern to match Example 2 (everything from ### Example 2 to right before ### Example 3)
pattern2 = r'### Example 2:.*?(?=### Example 3:)'
content = re.sub(pattern2, example2_fixed + '\n\n', content, flags=re.DOTALL)

# Pattern to match Example 3 (everything from ### Example 3 to right before ## Domain)
pattern3 = r'### Example 3:.*?(?=## Domain)'
content = re.sub(pattern3, example3_fixed + '\n\n', content, flags=re.DOTALL)

# Write back
with open(file_path, 'w') as f:
    f.write(content)

print("✅ Fixed all 3 examples in medium_focus_2.md")