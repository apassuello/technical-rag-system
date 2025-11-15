# Raw Data Directory

This directory contains original, unmodified source documents.

## Guidelines

- **Never modify files in this directory**
- Original files serve as source of truth
- All processing should output to `processed/` directory
- Keep file naming consistent and descriptive

## Adding New Documents

```bash
# Copy new documents here
cp /path/to/new_doc.pdf data/raw/

# Process them
python scripts/process_documents.py --input data/raw/ --batch
```
