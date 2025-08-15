# Enhanced Usage Guide - Flexible Training Data Scripts

## ✅ **Major Improvements Completed**

### 1. **Fixed JSON Structure** 
- ✅ Prompts now generate the **exact structure** needed by existing training infrastructure
- ✅ Simple `view_scores` format: `"technical": 0.18` instead of complex nested objects
- ✅ Compatible with `Epic1DataLoader` and existing training pipeline

### 2. **Flexible Validation Script** 
- ✅ Can validate **single files** or **entire directories**
- ✅ Elegant fallback for non-training JSON files
- ✅ Handles both old and new data formats

### 3. **Smart Combination Script**
- ✅ Can combine from **directories** automatically 
- ✅ Only processes valid training datasets
- ✅ Skips non-training JSON files gracefully

## 🔧 **New Usage Patterns**

### Validation Script (`validate_batch.py`)

```bash
# Single file validation
python validate_batch.py simple_batch_25_samples.json

# Validate all JSON files in current directory  
python validate_batch.py .

# Validate all JSON files in specific directory
python validate_batch.py /path/to/batch/files/

# Validate files in subdirectory
python validate_batch.py ../../data/training/test/
```

**Example Output:**
```
🔍 Validating directory: ../../data/training/test
============================================================
🔍 Checking: epic1_dataset_20250807_214311.json
   ✅ Valid training data (50 samples)
🔍 Checking: generation_report_20250807_215541.json
   ❌ File does not contain a valid training dataset

📊 Directory Summary:
   Total JSON files: 6
   Valid training files: 3
   Valid files: epic1_dataset_20250807_214311.json, ...

🎯 OVERALL DIRECTORY SUMMARY
========================================
   Total valid files: 3
   Total samples: 100
   Excellent quality: 0 files
   Good quality: 0 files
   Files needing improvement: 3 files
```

### Combination Script (`combine_batches.py`)

```bash
# Use current directory (finds all valid JSON files)
python combine_batches.py

# Use specific directory
python combine_batches.py /path/to/batch/files/

# Use specific files
python combine_batches.py file1.json file2.json file3.json

# Example with actual directory
python combine_batches.py ../../data/training/test/
```

**Example Output:**
```
🔄 Epic 1 Training Dataset Assembly
==================================================
📁 Using directory: ../../data/training/test

🔍 Found 3 potential training files
✅ Loaded 50 samples from epic1_dataset_20250807_214311.json
✅ Loaded 25 samples from epic1_dataset_20250807_215527.json
✅ Loaded 25 samples from epic1_dataset_20250807_215541.json

📊 Loaded 100 total samples
💾 Saved final dataset: epic1_claude_generated_dataset_100_samples.json
💾 Saved samples only: epic1_training_dataset_100_samples.json
```

## 🚀 **Complete Workflow**

### Step 1: Generate Batches Using Claude
Copy each prompt and generate:
- `simple_batch_25_samples.json` (from simple focus prompt)
- `medium_batch1_25_samples.json` (from medium focus 1 prompt)  
- `medium_batch2_25_samples.json` (from medium focus 2 prompt)
- `complex_batch_25_samples.json` (from complex focus prompt)

### Step 2: Validate All Batches
```bash
# Validate all files in current directory
python validate_batch.py .
```

### Step 3: Combine Into Final Dataset
```bash  
# Automatically find and combine all valid training files
python combine_batches.py
```

### Step 4: Use in Training Pipeline
The output `epic1_training_dataset_100_samples.json` is ready for:
```python
from src.training.data_loader import Epic1DataLoader

# Load with existing training infrastructure
loader = Epic1DataLoader("epic1_training_dataset_100_samples.json")
loader.load_dataset()
view_examples = loader.preprocess_data()
```

## 🛡️ **Error Handling**

### Validation Script Handles:
- ✅ Invalid JSON files → Skipped with warning
- ✅ Non-training JSON files → Detected and skipped  
- ✅ Missing files → Clear error messages
- ✅ Corrupted data structures → Graceful fallback
- ✅ Both old and new data formats → Automatic detection

### Combination Script Handles:
- ✅ Mixed file types → Only processes valid training data
- ✅ Empty directories → Clear error message
- ✅ Invalid file paths → Warnings, continues with valid files
- ✅ Duplicate detection → Warns about duplicate queries
- ✅ Data validation → Comprehensive quality checks

## 📊 **Quality Metrics**

Both scripts provide detailed quality assessment:
- **Excellent**: No issues, high correlations
- **Good**: Minor issues, acceptable quality  
- **Acceptable**: Some issues but usable
- **Needs Improvement**: Significant issues, consider regenerating

### Key Metrics Tracked:
- View score correlations (should be >0.6)
- Score consistency between views and expected
- Distribution balance across complexity levels
- Natural language quality (grammar, question marks)
- Duplicate detection
- Statistical validation

## ✨ **Benefits**

1. **Flexible**: Works with any directory structure
2. **Robust**: Handles mixed file types gracefully
3. **Informative**: Detailed quality reporting
4. **Compatible**: Works with existing training infrastructure  
5. **Scalable**: Can process hundreds of files easily

The enhanced scripts make it much easier to manage training data generation and ensure high-quality datasets for the Epic 1 ML training pipeline! 🎉