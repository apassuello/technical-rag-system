# 🧪 COMPREHENSIVE TESTING SCRIPTS USAGE GUIDE

**Purpose**: Guide to all testing and debugging scripts created during RAG system development  
**Status**: Complete reference for next debug session  
**Last Updated**: July 2, 2025  

---

## 📁 **SCRIPT INVENTORY**

### Core Verification Scripts
1. `comprehensive_verification_test.py` - Main system verification
2. `final_verification_test.py` - Quick 4-test verification  
3. `test_number_preservation_fix.py` - Number preservation testing
4. `test_rag_faithfulness.py` - Original faithfulness testing
5. `test_improved_faithfulness.py` - Enhanced faithfulness testing

### Debugging Scripts  
6. `debug_citation_issue.py` - Citation generation debugging
7. `debug_number_removal.py` - Number removal investigation  

### Analysis Scripts
8. `test_multi_document_support.py` - Multi-document functionality
9. `test_answer_generation.py` - Basic answer generation testing
10. `test_streamlit_functionality.py` - UI testing
11. `demo_streamlit_usage.py` - UI demonstration

### Evaluation Scripts
12. `ragas_evaluation.py` - RAGAS framework implementation  
13. `test_ragas_framework.py` - RAGAS setup verification
14. `rag_faithfulness_suite.py` - Comprehensive faithfulness analysis

---

## 🎯 **SCRIPT USAGE BY PURPOSE**

### For System Verification (Start Here)
```bash
# Primary comprehensive test - RUN THIS FIRST
python comprehensive_verification_test.py

# Quick verification (4 core tests)  
python final_verification_test.py

# Verify number preservation specifically
python test_number_preservation_fix.py
```

### For Debugging Specific Issues
```bash
# Debug citation problems
python debug_citation_issue.py

# Debug number removal (historical - issue fixed)
python debug_number_removal.py

# Test faithfulness behavior
python test_rag_faithfulness.py
python test_improved_faithfulness.py
```

### For Feature Testing
```bash
# Test multi-document processing
python test_multi_document_support.py

# Test answer generation only
python test_answer_generation.py

# Test UI functionality
python test_streamlit_functionality.py
python demo_streamlit_usage.py
```

### For Evaluation
```bash
# Run RAGAS evaluation
python ragas_evaluation.py

# Verify RAGAS setup
python test_ragas_framework.py

# Comprehensive faithfulness analysis
python rag_faithfulness_suite.py
```

---

## 🔧 **DETAILED SCRIPT DESCRIPTIONS**

### 1. `comprehensive_verification_test.py` ⭐ **PRIMARY TEST**
**Purpose**: Complete end-to-end system verification  
**Runtime**: ~2-3 minutes  
**Output**: Detailed verification report + JSON results file  

**What it tests**:
- Standalone answer generator (no context, fake context, good context)
- Full RAG pipeline with real documents (391 chunks)
- Edge cases (empty chunks, contradictory info, technical jargon)
- Generates comprehensive assessment report

**Key outputs to examine**:
- Answer content quality (look for hallucination!)
- Confidence scores (80% for Mars query = BUG)
- Citation generation
- Response appropriateness

**Usage**:
```bash
python comprehensive_verification_test.py
# Check verification_report_YYYYMMDD_HHMMSS.json for details
```

**Critical for**: Overall system health assessment

### 2. `final_verification_test.py` ⚡ **QUICK CHECK**
**Purpose**: Fast 4-test verification for core functionality  
**Runtime**: ~30 seconds  
**Output**: Pass/fail for each core component  

**Tests**:
1. No context handling
2. Good context usage  
3. Fabricated context skepticism
4. Multiple chunks handling

**Usage**:
```bash
python final_verification_test.py
# Returns exit code 0 (success) or 1 (failure)
```

**Critical for**: Quick verification after fixes

### 3. `test_number_preservation_fix.py` 🔢 **NUMBER TESTING**
**Purpose**: Verify technical numbers are preserved in answers  
**Runtime**: ~45 seconds  
**Output**: Pass/fail for number preservation across scenarios  

**Specific tests**:
- RV32E register count (16, 32 preserved?)
- Instruction widths (16-bit, 32-bit, 64-bit preserved?)
- Memory ranges (hex addresses, counts preserved?)

**Usage**:
```bash
python test_number_preservation_fix.py
# Check that technical numbers appear correctly in answers
```

**Critical for**: Ensuring fix didn't break, catching regressions

### 4. `test_rag_faithfulness.py` 🎭 **FAITHFULNESS ANALYSIS**
**Purpose**: Test whether model follows context vs using pre-trained knowledge  
**Runtime**: ~1-2 minutes  
**Output**: Detailed analysis of context following behavior  

**Test scenarios**:
1. No context provided
2. Fabricated/fake context  
3. Real context following
4. Contradictory context handling

**Usage**:
```bash
python test_rag_faithfulness.py
# Examine outputs for pre-trained knowledge usage
```

**Critical for**: Detecting hallucination and inappropriate knowledge use

### 5. `debug_citation_issue.py` 🔍 **CITATION DEBUGGING**
**Purpose**: Step-by-step debugging of citation generation  
**Runtime**: ~30 seconds  
**Output**: Raw model outputs, citation extraction analysis  

**Debugging features**:
- Shows raw model output before citation cleaning
- Tests explicit citation instructions
- Compares different prompt approaches

**Usage**:
```bash
python debug_citation_issue.py
# Examine raw model outputs vs final processed answers
```

**Critical for**: Understanding why citations aren't working

### 6. `debug_number_removal.py` 🔬 **NUMBER REMOVAL ANALYSIS**
**Purpose**: Detailed analysis of number removal patterns  
**Runtime**: ~45 seconds  
**Output**: Step-by-step processing showing where numbers disappear  

**Analysis features**:
- Tests regex patterns on various text
- Shows step-by-step answer processing
- Identifies exact removal points

**Usage**:
```bash
python debug_number_removal.py
# See exactly where and why numbers are removed
```

**Critical for**: Understanding technical content corruption (historical issue)

### 7. `test_multi_document_support.py` 📚 **MULTI-DOC TESTING**
**Purpose**: Test processing and querying across multiple documents  
**Runtime**: ~2-3 minutes (indexing time)  
**Output**: Cross-document retrieval verification  

**Features**:
- Indexes 5 different documents
- Tests cross-document queries
- Verifies source attribution

**Usage**:
```bash
python test_multi_document_support.py
# Verify system works with multiple document sources
```

**Critical for**: Production multi-document scenarios

### 8. `test_answer_generation.py` ⚙️ **BASIC GENERATION TEST**
**Purpose**: Test core answer generation without full RAG pipeline  
**Runtime**: ~20 seconds  
**Output**: Basic generation functionality verification  

**Usage**:
```bash
python test_answer_generation.py
# Test just the answer generation component
```

**Critical for**: Isolating generation issues from retrieval issues

---

## 🚨 **CRITICAL SCRIPTS FOR NEXT SESSION**

### Must Run for Each Fix:
1. **`comprehensive_verification_test.py`** - Always run after changes
2. **`test_number_preservation_fix.py`** - Ensure no regression  
3. **`test_rag_faithfulness.py`** - Check hallucination prevention

### For Specific Issue Debugging:
- **Hallucination**: `debug_citation_issue.py` + `test_rag_faithfulness.py`
- **Confidence issues**: `comprehensive_verification_test.py` (examine Mars query)
- **Citation problems**: `debug_citation_issue.py`
- **Behavioral issues**: `final_verification_test.py`

---

## 📊 **SCRIPT OUTPUT INTERPRETATION**

### ✅ **Good Signs to Look For**:
```
✅ CRITICAL NUMBERS PRESERVED
✅ CITATIONS GENERATED  
✅ APPROPRIATELY LOW CONFIDENCE
✅ ALL TESTS PASSED
Citations: 1, Confidence: 90%+ (good context)
Citations: 0, Confidence: <20% (no/bad context)
```

### ❌ **Red Flags to Watch For**:
```
❌ TECHNICAL NUMBERS REMOVED
❌ Model used fabricated information!
❌ CONFIDENCE TOO HIGH: 80%+ (irrelevant context)
❌ SYSTEM NEEDS FIXES BEFORE PRODUCTION
Answer: "RV32E has registers" (missing number!)
Answer: "R-type uses 8-bit immediate" (not in context!)
```

### 🔍 **What to Examine Manually**:
1. **Answer content**: Every technical detail must be from context
2. **Confidence scores**: Must correlate with context quality  
3. **Response length**: Brief for irrelevant, detailed for relevant
4. **Citation format**: Consistent [chunk_X] usage
5. **Number preservation**: All technical numbers intact

---

## 🎯 **TESTING WORKFLOW FOR NEXT SESSION**

### Phase 1: Baseline Assessment
```bash
# Get current system status
python comprehensive_verification_test.py
python test_number_preservation_fix.py
# Record current issues
```

### Phase 2: Issue-Specific Testing
```bash
# For hallucination debugging
python debug_citation_issue.py
python test_rag_faithfulness.py

# For confidence debugging  
python comprehensive_verification_test.py
# Focus on Mars query confidence score
```

### Phase 3: Fix Verification
```bash
# After each fix attempt
python final_verification_test.py          # Quick check
python test_number_preservation_fix.py     # Regression test
python comprehensive_verification_test.py  # Full verification
```

### Phase 4: Production Readiness
```bash
# Final verification before declaring ready
python comprehensive_verification_test.py
python test_multi_document_support.py
python test_rag_faithfulness.py
# Manual review of ALL test outputs
```

---

## 🛠️ **CREATING NEW TESTS**

### For New Issues:
```python
# Template for new test script
def test_specific_issue():
    """Test description and purpose."""
    generator = AnswerGenerator()
    
    # Test case
    chunks = [{"content": "...", "metadata": {...}, "id": "chunk_1"}]
    result = generator.generate("query", chunks)
    
    # Verification
    assert condition, "Error message"
    print(f"✅ Test passed: {result.answer}")

if __name__ == "__main__":
    test_specific_issue()
```

### Test Naming Convention:
- `test_[feature]_[specific_aspect].py` - Feature testing
- `debug_[issue]_[description].py` - Issue debugging  
- `verify_[component]_[behavior].py` - Verification scripts

---

## 📝 **SCRIPT MAINTENANCE**

### Current Status:
- ✅ **All scripts functional** - paths fixed, imports working
- ✅ **Number preservation test** - reflects current fix
- ✅ **Comprehensive verification** - covers all major issues
- ⚠️ **Some test criteria** - may need adjustment for new fixes

### Future Updates Needed:
1. **Hallucination prevention test** - create specific test for this issue
2. **Confidence calibration test** - specific irrelevant context scenarios  
3. **Response behavior test** - verify appropriate verbosity

### Script Dependencies:
- All scripts require: `shared_utils.generation.answer_generator`
- Pipeline tests require: `src.rag_with_generation`  
- Some tests require: pre-indexed documents in `data/test/`

---

## 🚀 **QUICK REFERENCE**

### Essential Commands:
```bash
# Full system check
python comprehensive_verification_test.py

# Quick verification  
python final_verification_test.py

# Number preservation check
python test_number_preservation_fix.py

# Debug specific issues
python debug_citation_issue.py
```

### Key Files to Monitor:
- `verification_report_*.json` - Detailed test results
- Console output - Manual examination required
- Confidence scores - Must be appropriate for context
- Answer content - Must contain only context information

### Emergency Debugging:
If system appears broken:
1. Run `test_number_preservation_fix.py` - check if regression
2. Run `debug_citation_issue.py` - check basic functionality
3. Run `comprehensive_verification_test.py` - full diagnosis
4. Manually examine answers for content quality issues

---

**📋 Total Scripts**: 14 testing/debugging scripts  
**⏱️ Full Test Suite Runtime**: ~10-15 minutes  
**🎯 Primary Script**: `comprehensive_verification_test.py`  
**🔍 Debugging Entry Point**: `debug_citation_issue.py`  
**✅ Regression Test**: `test_number_preservation_fix.py`