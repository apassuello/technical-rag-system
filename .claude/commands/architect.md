# Architecture Mode with Specific Focus

**Usage**: `/architect [focus-area]`  
**Examples**: 
- `/architect epic2-demo` - Architecture review for Epic 2 demo
- `/architect component-boundaries` - Focus on component boundary analysis
- `/architect performance` - Architecture performance analysis

## Instructions

Load architectural context and provide architectural guidance for the specified focus area.

## Context Loading

**Base Architectural Context**:
- .claude/context-templates/ARCHITECT_MODE.md - Architectural thinking patterns
- .claude/memory-bank/architecture-patterns.md - 6-component modular architecture patterns
- .claude/memory-bank/swiss-engineering-standards.md - Quality and compliance standards
- .claude/ARCHITECTURE_SAFEGUARDS.md - Critical architectural violation prevention

**Key Architecture Files**:
- `docs/architecture/MASTER-ARCHITECTURE.md` - Complete system specification
- `src/core/platform_orchestrator.py` - System orchestration
- `src/core/component_factory.py` - Component creation patterns
- `src/core/interfaces.py` - Component interfaces and contracts

## Output Format

**🏗️ ARCHITECT MODE - [Focus Area]**

**Architectural Context Loaded**:
- System Architecture: 6-component modular with adapter patterns
- Quality Standards: Swiss engineering precision and reliability
- Current State: 90.2% validation, 100% architecture compliance
- Performance: 565K chars/sec, 48.7x speedup, <10ms retrieval

**Focus Area: [Specified focus or current task]**

**Architectural Analysis**:
[Provide architectural perspective on the specified focus area]

**Key Architectural Principles**:
- Component boundary integrity and separation of concerns
- Adapter pattern for external integrations only
- Direct wiring for performance with proper abstraction
- Configuration-driven behavior without code changes

**Recommendations**:
[Specific architectural guidance for the focus area]

**Next Architectural Actions**:
[Recommended next steps from architectural perspective]

Ready for architectural design, component boundary analysis, and compliance validation.