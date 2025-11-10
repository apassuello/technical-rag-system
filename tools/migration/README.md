# Migration Tools

This directory contains operational utilities for migrating RAG system data between different vector database backends.

## Overview

These tools were moved from `src/components/retrievers/backends/migration/` to properly organize them as operational utilities rather than core application components.

## Available Tools

### FAISSToWeaviateMigrator (`faiss_to_weaviate.py`)
- **Purpose**: Migrate document data from FAISS to Weaviate vector database
- **Features**: Data validation, backup creation, progress tracking, rollback capabilities
- **Usage**: For system administrators migrating between vector database backends

### DataValidator (`data_validator.py`)  
- **Purpose**: Comprehensive validation of document data during migrations
- **Features**: Document structure validation, embedding quality checks, metadata consistency
- **Usage**: Used by migration tools to ensure data integrity

## Usage Example

```python
from tools.migration import FAISSToWeaviateMigrator, DataValidator

# Initialize migrator
migrator = FAISSToWeaviateMigrator(
    faiss_config=faiss_config,
    weaviate_config=weaviate_config
)

# Run migration with validation
migrator.migrate(
    validate_before=True,
    create_backup=True,
    batch_size=100
)
```

## Coverage Exclusion

These operational tools are excluded from core application coverage metrics via the `.coveragerc` configuration:

```ini
# Operational tools and utilities (not core application code)
*/tools/*
```

This ensures that coverage reports focus on the core RAG application functionality.

## Migration History

- **Original Location**: `src/components/retrievers/backends/migration/`
- **New Location**: `tools/migration/` 
- **Migration Date**: August 30, 2025
- **Reason**: Separate operational utilities from core application components for cleaner coverage metrics