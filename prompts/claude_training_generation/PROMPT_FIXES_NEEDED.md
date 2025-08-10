# Prompt Fixes Needed

## Issues Found in Prompts

### 1. ❌ **Structure Issues in Examples**
- **Files affected**: `claude_prompt_medium_focus_1.md`, `claude_prompt_medium_focus_2.md`, `claude_prompt_complex_focus.md`
- **Problem**: Examples still use old complex structure with nested objects
- **Required structure**:
```json
"view_scores": {
  "technical": 0.42,      // Simple float value
  "linguistic": 0.35,     // NOT nested object
  "task": 0.39,
  "semantic": 0.37,
  "computational": 0.38
}
```

### 2. ❌ **Topic Mismatch in Complex Prompt**
- **File**: `claude_prompt_complex_focus.md`
- **Problem**: Topic focus is RISC-V but examples are about:
  - Byzantine consensus algorithms
  - CRDT-based data stores
  - Quantum-resistant cryptography
- **Solution**: Either:
  - Update examples to RISC-V topics, OR
  - Remove specific RISC-V focus and keep it general

### 3. ⚠️ **Feature Guidelines Still Present**
- **Files affected**: All medium and complex prompts
- **Problem**: Still have detailed "Feature Value Guidelines" sections that reference the old complex structure
- **Solution**: Replace with simpler scoring guidelines like in the simple prompt

## Recommended Fixes

### For All Medium/Complex Prompts:

1. **Fix all JSON examples** to use simple structure:
```json
{
  "query_text": "...",
  "expected_complexity_score": 0.48,
  "expected_complexity_level": "medium",
  "view_scores": {
    "technical": 0.52,
    "linguistic": 0.44,
    "task": 0.50,
    "semantic": 0.47,
    "computational": 0.49
  },
  "confidence": 0.86,
  "metadata": {
    "domain": "technical",
    "query_type": "architecture",
    "generation_timestamp": "2025-08-07T20:00:00Z",
    "base_score": 0.48,
    "template_used": "none - natural generation"
  }
}
```

2. **Remove Feature Value Guidelines sections** and replace with:
```markdown
## Scoring Guidelines for [Complexity Level]

### View Score Ranges:
- **Technical**: [range] - [description]
- **Linguistic**: [range] - [description]
- **Task**: [range] - [description]
- **Semantic**: [range] - [description]
- **Computational**: [range] - [description]

### How to Score Each View:
[Simple instructions without feature details]
```

3. **For Complex Prompt**: Decide on topic focus:
   - Option A: Keep RISC-V focus and update examples
   - Option B: Remove RISC-V focus for general complex queries

## Files to Fix:
1. `claude_prompt_medium_focus_1.md` - 2 examples need structure fix
2. `claude_prompt_medium_focus_2.md` - 3 examples need structure fix  
3. `claude_prompt_complex_focus.md` - 3 examples need structure fix + topic alignment

## Validation
After fixes, all prompts should:
- ✅ Use simple float values in view_scores
- ✅ Have consistent topic focus with examples
- ✅ Not reference complex feature structures
- ✅ Generate data compatible with existing training infrastructure