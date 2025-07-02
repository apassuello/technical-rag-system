# 🎯 NEXT DEBUG SESSION INSTRUCTIONS

**Session Goal**: Fix remaining critical RAG system issues  
**Primary Focus**: Content hallucination prevention  
**Duration**: 6-10 hours estimated  

## 🚨 **CRITICAL CONTEXT FOR NEXT SESSION**

### What We Fixed ✅
- **Number removal bug**: Technical numbers now preserved in answers
- **Basic citation extraction**: [chunk_X] format working

### What's Still Broken ❌
- **CRITICAL**: Model fabricates technical details not in context (99% confidence!)
- **HIGH**: Confidence miscalibration (80% for irrelevant context)
- **MEDIUM**: Over-verbose responses for irrelevant queries
- **MEDIUM**: Inconsistent citation formats

## ⚠️ **AVOID PREVIOUS MISTAKES**

### The Assistant's Previous Error:
**Fixed only 1 issue** → **Declared "production ready"** → **Ignored 4 other critical issues**

### For This Session:
1. **NEVER declare production ready** until ALL critical issues resolved
2. **Manually read every test answer** - don't trust metrics alone
3. **Look for hallucination** - compare context vs output word-by-word
4. **Check confidence appropriateness** - not just pass/fail
5. **Verify behavioral issues** - response length, citation consistency

---

## 🔧 **STEP-BY-STEP DEBUGGING PLAN**

### Phase 1: Content Hallucination Investigation (CRITICAL - 3 hours)

#### Step 1.1: Examine the Hallucination Example
```bash
# Run this specific test case
python -c "
from shared_utils.generation.answer_generator import AnswerGenerator
generator = AnswerGenerator()
chunks = [{
    'content': 'RISC-V ISA specification defines base integer instruction formats including R-type, I-type, S-type, B-type, U-type, and J-type formats with varying immediate field encodings.',
    'metadata': {'page_number': 10, 'source': 'spec.pdf'},
    'score': 0.95,
    'id': 'chunk_1'
}]
result = generator.generate('What are RISC-V instruction formats?', chunks)
print('CONTEXT:', chunks[0]['content'])
print('ANSWER:', result.answer)
print('CONFIDENCE:', result.confidence_score)
"
```

**What to Look For**:
- Does the answer contain specific bit field sizes (8-bit, 4-bit, etc.)?
- Are these details present in the context?
- If not, WHERE did they come from?

#### Step 1.2: Create Hallucination Test Suite
Create `test_hallucination_prevention.py`:
```python
def test_partial_technical_context():
    """Test with incomplete technical information to see if model adds details."""
    test_cases = [
        {
            "context": "RISC-V supports multiple instruction formats",
            "query": "What instruction formats does RISC-V support?",
            "should_not_contain": ["32-bit", "16-bit", "specific", "immediate"]
        },
        {
            "context": "RV32E has fewer registers than standard RISC-V",
            "query": "How many registers does RV32E have?", 
            "should_not_contain": ["16", "32", "exactly", "specifically"]
        }
    ]
```

#### Step 1.3: Strengthen System Prompt Against Hallucination
Current system prompt allows model to "fill in details". Need to strengthen:

```python
# Add to system prompt:
"""
CRITICAL: You must NEVER add technical details not explicitly stated in context.
- Do NOT specify bit widths, register counts, or technical specs unless explicitly provided
- Do NOT use your pre-trained knowledge to "complete" partial information  
- If context is incomplete, state what's missing rather than guessing
- Example: If context says "RISC-V has instruction formats" do NOT list specific formats unless provided
"""
```

### Phase 2: Confidence Calibration Fix (HIGH - 2 hours)

#### Step 2.1: Debug Irrelevant Context Confidence
```bash
# Test the Mars example specifically
python -c "
from src.rag_with_generation import RAGWithGeneration
rag = RAGWithGeneration()
# Load documents first...
result = rag.query_with_answer('What is the capital of Mars?')
print('CONFIDENCE:', result.get('confidence'))
print('ANSWER LENGTH:', len(result['answer'].split()))
"
```

#### Step 2.2: Fix Confidence Calculation
Look at `_calculate_confidence()` method:
- Why does irrelevant context get 80% confidence?
- Add context-query relevance scoring
- Penalize high confidence when context doesn't match query

### Phase 3: Response Behavior Fixes (MEDIUM - 1 hour)

#### Step 3.1: Fix Over-verbose Responses
- Modify system prompt for brief refusals
- Test response length for irrelevant queries
- Ensure appropriate brevity

#### Step 3.2: Citation Format Consistency  
- Strengthen [chunk_X] format requirement
- Test citation extraction with various formats

### Phase 4: Comprehensive Verification (2-3 hours)

#### Step 4.1: Run All Previous Tests
```bash
python comprehensive_verification_test.py
python test_number_preservation_fix.py  # Ensure no regression
python test_hallucination_prevention.py  # New test
```

#### Step 4.2: Manual Content Verification
**For every test answer**:
1. Read the full answer completely
2. Compare technical details with context
3. Verify confidence appropriateness  
4. Check response length and behavior

---

## 🎯 **DEBUGGING METHODOLOGY**

### Always Ask These Questions:
1. **"Where did this technical detail come from?"**
   - If not in context → HALLUCINATION BUG
   
2. **"Is this confidence score appropriate?"**
   - High confidence + irrelevant context → CALIBRATION BUG
   
3. **"Does this response length make sense?"**
   - Long response + irrelevant query → VERBOSITY BUG
   
4. **"Are citations consistent?"**
   - Mixed formats → CONSISTENCY BUG

### Testing Strategy:
1. **Single issue focus**: Fix one critical issue at a time
2. **Immediate verification**: Test fix immediately after implementing
3. **Regression testing**: Ensure previous fixes still work
4. **Manual inspection**: Read every answer, don't trust metrics

---

## 🔍 **CRITICAL TEST CASES TO VERIFY**

### Hallucination Prevention Tests:
```python
# These should NOT contain fabricated details
test_cases = [
    ("RISC-V has instruction formats", "What formats does RISC-V have?"),
    ("RV32E uses fewer registers", "How many registers does RV32E have?"),
    ("Instructions can be variable length", "What are the instruction lengths?")
]
```

### Confidence Calibration Tests:
```python
# These should have LOW confidence (<20%)
irrelevant_tests = [
    ("What is the capital of Mars?", "RISC-V documentation"),
    ("How do you bake bread?", "Software validation guidelines"),
    ("What's the weather like?", "Instruction set manuals")
]
```

### Regression Tests:
```python
# These should still work (number preservation)
regression_tests = [
    ("RV32E has 16 registers", "How many registers does RV32E have?"),
    ("Instructions are 32-bit wide", "What is the instruction width?")
]
```

---

## 📊 **SUCCESS METRICS**

### Must Achieve:
- **0% hallucination rate**: No fabricated technical details
- **<20% confidence** for irrelevant context
- **>60% confidence** for relevant context  
- **<50 words** for irrelevant query responses
- **100% number preservation** (regression test)

### Verification Process:
1. **Automated tests pass**: All test suites green
2. **Manual inspection passes**: Human review confirms content quality
3. **Edge case testing**: Handles unusual scenarios appropriately
4. **Confidence validation**: Scores correlate with answer quality

---

## ⚠️ **FINAL WARNINGS**

### Red Flags to Watch For:
- ❌ Model adding technical specifications not in context
- ❌ High confidence (>50%) for irrelevant context
- ❌ Long explanations for obviously irrelevant queries
- ❌ Technical numbers disappearing (regression)
- ❌ Citations in wrong format

### Green Flags to Confirm:
- ✅ Every technical detail traceable to context
- ✅ Confidence correlates with context relevance
- ✅ Brief refusals for irrelevant queries
- ✅ Consistent [chunk_X] citation format
- ✅ All numbers preserved in technical content

### Session Complete When:
- **ALL critical issues resolved**
- **ALL tests passing with manual verification**
- **NO hallucination detected in comprehensive testing**
- **Confidence scores appropriately calibrated**
- **System ready for production consideration**

---

**Priority Order**: Hallucination → Confidence → Verbosity → Citations  
**Estimated Time**: 6-10 hours  
**Success Criteria**: Zero critical issues remaining  
**Manual Verification**: Required for every test case  

**🎯 Remember: Quality over speed. Fix thoroughly, test comprehensively.**

---

## 📚 **TESTING SCRIPTS REFERENCE**

**Complete usage guide**: See `TESTING_SCRIPTS_USAGE_GUIDE.md` for detailed information on all 14 testing scripts.

### Quick Reference:
```bash
# Primary verification (ALWAYS RUN FIRST)
python comprehensive_verification_test.py

# Quick 4-test check
python final_verification_test.py  

# Number preservation regression test
python test_number_preservation_fix.py

# Citation debugging
python debug_citation_issue.py

# Faithfulness analysis  
python test_rag_faithfulness.py
```

**⚠️ Critical**: Read `TESTING_SCRIPTS_USAGE_GUIDE.md` for complete script descriptions, expected outputs, and red flags to watch for.