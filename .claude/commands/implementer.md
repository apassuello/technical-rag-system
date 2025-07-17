# Implementation Mode with Specific Focus

**Usage**: `/implementer [target]`  
**Examples**:
- `/implementer epic2-demo` - Implementation work for Epic 2 demo
- `/implementer neural-reranker` - Focus on neural reranking implementation
- `/implementer streamlit-ui` - Streamlit interface implementation
- `/implementer tests/diagnostic` - Focus on diagnostic test implementation

## Instructions

Load implementation context and provide implementation guidance for the specified target.

## Context Loading

**Base Implementation Context**:
- @context-templates/IMPLEMENTER_MODE.md - Implementation standards and patterns
- @memory-bank/performance-optimizations.md - Apple Silicon optimization patterns
- @memory-bank/swiss-engineering-standards.md - Code quality standards
- @context/key_files.md - Core system file references

**Key Implementation Areas**:
- `src/components/` - All modular component implementations
- `src/core/component_factory.py` - Component creation with enhanced logging
- `tests/` - Comprehensive test suite and validation
- `config/` - System configuration files

## Output Format

**⚙️ IMPLEMENTER MODE - [Target]**

**Implementation Context Loaded**:
- Code Standards: Swiss engineering with comprehensive error handling
- Performance: Apple Silicon MPS optimization, 48.7x batch speedup
- Quality Gates: Type hints, docstrings, test coverage required
- Architecture: 6-component modular with ComponentFactory patterns

**Target: [Specified implementation target]**

**Implementation Focus**:
[Specific implementation area and requirements]

**Key Implementation Standards**:
- Apple Silicon MPS optimization where applicable
- Comprehensive error handling with actionable messages
- Type hints and comprehensive docstrings
- Performance instrumentation and logging
- Swiss engineering quality standards

**Implementation Approach**:
[Recommended implementation strategy for the target]

**Quality Checklist**:
- [ ] Follows existing architectural patterns
- [ ] Includes comprehensive error handling
- [ ] Maintains backward compatibility
- [ ] Includes performance instrumentation
- [ ] Has corresponding test coverage

**Next Implementation Steps**:
[Specific implementation actions for the target]

Ready for production-quality code implementation with Swiss engineering standards.