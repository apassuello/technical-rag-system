# Data Directory Structure

This directory contains all data assets for the RAG Portfolio Project 1.

## Directory Organization

```
data/
├── raw/                # Original, unmodified source documents
├── processed/          # Preprocessed and validated documents ready for RAG
├── samples/            # Small sample datasets for demos and testing
├── test/               # Test documents (LEGACY - being reorganized)
├── evaluation/         # Ground truth queries and evaluation datasets
├── metadata/           # Data manifests, catalogs, and metadata
│   └── manifests/      # Document manifests and version tracking
└── cache/              # Temporary processing cache (git-ignored)
```

## Data Categories

### RISC-V Technical (7 documents, ~15MB)
- RISC-V specifications and vector extensions
- Implementation guides and reference cards
- Signal processing applications

### Research Papers (9 documents, ~8MB)
- EECS papers from UC Berkeley
- arXiv papers on RISC-V architecture
- Performance and optimization studies

### Regulatory Medical (4 documents, ~3MB)
- FDA guidance documents
- Software validation principles
- AI/ML in medical devices (SaMD)

### General Technical (2 documents, ~15MB)
- RISC-V ISA specifications
- Unprivileged instruction set documentation

## Current Status

- **Total Documents**: 22 PDFs + 1 MD + 1 YAML
- **Total Size**: ~39 MB
- **Evaluation Queries**: 31 ground truth queries with relevance judgments
- **Organization**: Migration from `test/` to structured directories in progress

## Usage

### Adding New Documents
```bash
# Place raw documents in raw/ directory
cp new_document.pdf data/raw/

# Run processing pipeline
python scripts/process_documents.py --input data/raw/new_document.pdf
```

### Creating Sample Datasets
```bash
# Create sample dataset for demos
python scripts/create_sample_dataset.py --size small --output data/samples/
```

### Validating Data Quality
```bash
# Run data quality checks
python scripts/validate_data.py --directory data/processed/
```

## Data Management

- **Inventory**: `metadata/data_inventory.json` - Complete data catalog
- **Manifests**: `metadata/manifests/` - Document version tracking
- **Quality Metrics**: Tracked in processing scripts and manifests

## Notes

- The `test/` directory contains legacy data being reorganized
- All raw data should be preserved in `raw/` directory
- Processed data in `processed/` can be regenerated from raw sources
- Cache directory is excluded from git (temporary processing artifacts)
