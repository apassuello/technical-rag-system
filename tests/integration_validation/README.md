# Integration Validation Tests

This directory contains specialized tests for validating the integration and architecture compliance of the modular Document Processor system.

## Test Files

### `test_factory_integration.py`
**Purpose**: Validates ComponentFactory integration with ModularDocumentProcessor
- Tests processor creation via factory
- Validates interface compliance  
- Checks performance metrics
- Verifies component availability

**Usage**:
```bash
python tests/integration_validation/test_factory_integration.py
```

### `test_legacy_compatibility.py` 
**Purpose**: Validates backwards compatibility with legacy parameters
- Tests legacy parameter acceptance (`chunk_size`, `chunk_overlap`)
- Validates parameter conversion to config format
- Ensures no breaking changes for existing code

**Usage**:
```bash
python tests/integration_validation/test_legacy_compatibility.py
```

### `validate_architecture_compliance.py`
**Purpose**: Comprehensive architecture compliance validation
- Validates against architecture specifications
- Tests adapter pattern implementation  
- Checks interface compliance
- Measures compliance score
- Generates detailed compliance report

**Usage**:
```bash
python tests/integration_validation/validate_architecture_compliance.py
```

## Results Files

### `architecture_compliance_results.json`
Latest architecture compliance validation results showing 91.7% compliance score.

## Regression Testing

These tests are designed for:
- **Pre-deployment validation**: Run before any production deployment
- **Regression testing**: Ensure no functionality is broken by changes
- **Architecture validation**: Verify adherence to design specifications  
- **Performance monitoring**: Track component creation and processing performance

## Integration with CI/CD

Recommended integration:
```bash
# Run all validation tests
python tests/integration_validation/test_factory_integration.py
python tests/integration_validation/test_legacy_compatibility.py  
python tests/integration_validation/validate_architecture_compliance.py

# Check exit codes for automation
if [ $? -eq 0 ]; then
    echo "✅ All validation tests passed"
else
    echo "❌ Validation tests failed"
    exit 1
fi
```

## Future Enhancements

These tests can be extended to validate:
- New document processors
- Additional sub-component implementations
- Performance regression detection
- Security compliance validation