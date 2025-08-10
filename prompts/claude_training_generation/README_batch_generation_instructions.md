# Epic 1 Training Data Generation - Complete Instructions

## Overview

This directory contains comprehensive prompts for generating high-quality training data for the Epic 1 multi-view ML query complexity analyzer. The system generates data in focused batches to maintain quality while ensuring proper distribution across complexity levels.

## Generation Strategy

### 4-Batch Approach with Overlap Zones

The generation uses a **modified single-complexity approach** with boundary samples to ensure smooth transitions and consistent calibration:

1. **Simple Focus Batch** (25 samples)
2. **Medium Focus Batch 1** (25 samples) 
3. **Medium Focus Batch 2** (25 samples)
4. **Complex Focus Batch** (25 samples)

**Total Output**: 100 high-quality training samples

### Distribution Design

```
Simple Batch:        [0.10────────0.25]──[0.26─0.35] (boundary)
                                         ↓
Medium Batch 1:         [0.32─0.40]──[0.41────0.55]──[0.56─0.66] (boundary)
                                                         ↓
Medium Batch 2:         [0.32─0.40]──[0.41────0.55]──[0.56─0.66] (boundary)
                                                         ↓
Complex Batch:                        [0.64─0.72]──[0.73────────0.90]
```

**Overlap zones** ensure consistent calibration between batches and validate scoring accuracy.

## File Structure

```
prompts/claude_training_generation/
├── claude_prompt_simple_focus.md      # 25 samples: 20 simple + 5 boundary
├── claude_prompt_medium_focus_1.md    # 25 samples: 5 + 15 + 5 distribution  
├── claude_prompt_medium_focus_2.md    # 25 samples: 5 + 15 + 5 distribution
├── claude_prompt_complex_focus.md     # 25 samples: 5 boundary + 20 complex
└── README_batch_generation_instructions.md
```

## Step-by-Step Generation Process

### Phase 1: Simple Complexity Batch
1. **Use**: `claude_prompt_simple_focus.md`
2. **Expected Output**: JSON array with 25 samples
3. **Target Distribution**:
   - 20 samples: 0.10-0.25 (clearly simple)
   - 5 samples: 0.26-0.35 (simple-medium boundary)
4. **Focus Areas**: Basic programming, simple tools, fundamental concepts

### Phase 2: Medium Complexity Batch 1  
1. **Use**: `claude_prompt_medium_focus_1.md`
2. **Expected Output**: JSON array with 25 samples
3. **Target Distribution**:
   - 5 samples: 0.32-0.40 (medium-simple boundary)
   - 15 samples: 0.41-0.55 (clearly medium)
   - 5 samples: 0.56-0.66 (medium-complex boundary)
4. **Focus Areas**: Web development, APIs, backend systems, databases

### Phase 3: Medium Complexity Batch 2
1. **Use**: `claude_prompt_medium_focus_2.md`
2. **Expected Output**: JSON array with 25 samples
3. **Target Distribution**: Same as Batch 1
4. **Focus Areas**: Data engineering, mobile development, testing, infrastructure

### Phase 4: Complex Complexity Batch
1. **Use**: `claude_prompt_complex_focus.md`
2. **Expected Output**: JSON array with 25 samples
3. **Target Distribution**:
   - 5 samples: 0.64-0.72 (complex-medium boundary)
   - 20 samples: 0.73-0.90 (clearly complex)
4. **Focus Areas**: Distributed systems, advanced algorithms, research problems

## Quality Validation Between Batches

### Overlap Zone Validation
After generating each batch, validate boundary samples:

1. **Simple → Medium Overlap (0.26-0.40)**:
   - Simple batch boundary samples (0.26-0.35) should have similar scores
   - Medium batch boundary samples (0.32-0.40) should be slightly higher
   - Correlation should be 0.8+ between similar complexity levels

2. **Medium → Complex Overlap (0.56-0.72)**:
   - Medium batch boundary samples (0.56-0.66) should align
   - Complex batch boundary samples (0.64-0.72) should be slightly higher
   - Validate progression is smooth and logical

### Consistency Checks
- **Feature Values**: Similar complexity queries should have similar feature values
- **View Correlations**: All batches should maintain 0.6-0.9 view correlations  
- **Reasoning Quality**: Explanations should reference specific query elements
- **Natural Language**: All queries must sound like genuine user questions

## Dataset Assembly Process

### Step 1: Generate All Batches
1. Run each prompt through Claude individually
2. Save outputs as:
   - `simple_batch_25_samples.json`
   - `medium_batch1_25_samples.json`
   - `medium_batch2_25_samples.json`
   - `complex_batch_25_samples.json`

### Step 2: Combine Batches
```python
import json
from pathlib import Path

# Load all batch files
batches = []
for file in ['simple_batch_25_samples.json', 'medium_batch1_25_samples.json', 
             'medium_batch2_25_samples.json', 'complex_batch_25_samples.json']:
    with open(file, 'r') as f:
        batches.extend(json.load(f))

# Shuffle combined dataset
import random
random.shuffle(batches)

# Save final dataset
with open('epic1_claude_generated_dataset_100_samples.json', 'w') as f:
    json.dump(batches, f, indent=2)
```

### Step 3: Final Validation
Run complete dataset through validation:
1. **Distribution Check**: ~25% simple, ~50% medium, ~25% complex
2. **Score Progression**: Smooth distribution across 0.10-0.90 range
3. **Quality Metrics**: All samples pass validation checklist
4. **Feature Consistency**: Features derivable from query text

## Expected Final Distribution

```
Complexity Level Distribution:
┌─────────────────────────────────────────────────────────┐
│ Simple (0.10-0.35):   25 samples (25%)                 │
│ Medium (0.32-0.66):   50 samples (50%)                 │ 
│ Complex (0.64-0.90):  25 samples (25%)                 │
└─────────────────────────────────────────────────────────┘

Score Distribution:
 0.1    0.2    0.3    0.4    0.5    0.6    0.7    0.8    0.9
  │      │      │      │      │      │      │      │      │
  ████   ████   ████   ████   ████   ████   ████   ████   ████
 Simple    │   Medium        │              │   Complex
           └─ Boundary ──────┘              └─ Boundary
```

## Quality Targets

### Individual Sample Quality
- ✅ **Natural Language**: Grammatically correct, realistic user questions
- ✅ **Feature Accuracy**: All numerical values derivable from query text  
- ✅ **Score Consistency**: View scores correlate (0.6-0.9) and match expected complexity
- ✅ **Reasoning Quality**: Clear explanations referencing specific query elements
- ✅ **Technical Accuracy**: All technical concepts are current and correct

### Dataset Quality  
- ✅ **Distribution Balance**: Proper complexity level distribution
- ✅ **Topic Diversity**: Wide coverage of technical domains
- ✅ **Query Variety**: Different question types and patterns
- ✅ **Progression Smoothness**: Gradual complexity increase
- ✅ **Calibration Consistency**: Boundary samples validate scoring accuracy

## Troubleshooting Common Issues

### Issue: Inconsistent Scoring Across Batches
**Solution**: Use overlap zone samples to recalibrate. Regenerate problematic batches with adjusted examples.

### Issue: Unrealistic Queries
**Solution**: Emphasize natural language requirements. Add more "sounds like a real user" validation.

### Issue: Feature Value Mismatches  
**Solution**: Verify features can be extracted from query text. Update examples to show proper feature derivation.

### Issue: Low View Correlations
**Solution**: Ensure view scores reflect same underlying complexity. Adjust individual view assessments to maintain correlation.

### Issue: Repetitive Query Patterns
**Solution**: Use different topic areas per batch. Emphasize diversity requirements in prompts.

## Final Integration

Once all batches are generated and combined:

1. **Validate Dataset**: Run through `Epic1DataLoader` to ensure compatibility
2. **Extract Features**: Verify all 5 views have proper feature extraction
3. **Train Models**: Use with existing Epic 1 training pipeline
4. **Evaluate Quality**: Compare against target >85% ensemble accuracy

The resulting dataset should provide high-quality training data enabling the Epic 1 ML analyzer to achieve its target performance goals.

## Usage Example

```bash
# Generate each batch using Claude
# Then combine using Python:

python -c "
import json, random
batches = []
for file in ['simple_batch.json', 'medium1_batch.json', 'medium2_batch.json', 'complex_batch.json']:
    with open(file) as f: batches.extend(json.load(f))
random.shuffle(batches)
with open('final_dataset.json', 'w') as f: json.dump(batches, f, indent=2)
print(f'Combined {len(batches)} samples into final dataset')
"
```

This approach ensures high-quality, well-calibrated training data that will enable the Epic 1 ML system to achieve its target accuracy goals.