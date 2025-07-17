# Validation Mode with Specific Focus

**Usage**: `/validator [test-suite]`  
**Examples**:
- `/validator epic2` - Focus on Epic 2 feature validation
- `/validator diagnostic` - Run diagnostic test suite
- `/validator architecture` - Architecture compliance validation
- `/validator tests/component_specific_tests.py` - Specific test file validation

## Instructions

Load validation context and provide testing guidance for the specified test suite or validation area.

## Context Loading

**Base Validation Context**:
- @context-templates/VALIDATOR_MODE.md - Testing and validation patterns
- @memory-bank/swiss-engineering-standards.md - Quality standards and metrics
- @memory-bank/architecture-patterns.md - Architecture compliance patterns

**Key Validation Areas**:
- `tests/run_comprehensive_tests.py` - Complete system validation
- `tests/diagnostic/run_all_diagnostics.py` - System health diagnostics
- `tests/integration_validation/validate_architecture_compliance.py` - Architecture compliance
- `final_epic2_proof.py` - Epic 2 vs basic component differentiation

## Output Format

**🔍 VALIDATOR MODE - [Test Suite]**

**Validation Context Loaded**:
- Quality Standards: Swiss engineering with 122 test cases
- Current Status: 90.2% validation score, 0 test failures
- Test Framework: Multi-layered validation with acceptance criteria
- Architecture: 100% compliance with modular patterns

**Test Suite: [Specified test suite or validation area]**

**Validation Focus**:
[Specific testing area and requirements]

**Key Quality Standards**:
- 100% test coverage for critical paths
- Real-world data testing with RISC-V documentation
- Performance validation against targets
- Swiss market readiness assessment
- Production deployment validation

**Available Validation Commands**:
- `python tests/run_comprehensive_tests.py`
- `python tests/diagnostic/run_all_diagnostics.py`
- `python tests/integration_validation/validate_architecture_compliance.py`
- `python final_epic2_proof.py`

**Validation Strategy**:
[Recommended testing approach for the specified area]

**Success Criteria**:
[Specific pass/fail criteria and quality gates]

**Next Validation Steps**:
[Specific validation actions for the test suite]

Ready for comprehensive testing, validation, and quality assurance with Swiss engineering standards.