# Processed Data Directory

This directory contains validated and preprocessed documents ready for RAG system.

## Contents

All files here have been:
- Validated for quality
- Extracted for text content
- Cataloged with metadata
- Checked for duplicates

## Regeneration

All processed files can be regenerated from `raw/` directory:

```bash
python scripts/process_documents.py --input data/raw/ --batch --output data/processed/
```
