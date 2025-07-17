# Load Task-Specific Context

**Usage**: `/context [task-area]`  
**Examples**:
- `/context epic2-demo` - Load context for Epic 2 demo development
- `/context neural-reranker` - Load context for neural reranking work
- `/context streamlit-ui` - Load context for UI development
- `/context validation` - Load context for testing and validation work

## Instructions

Load appropriate context fragments based on the specified task area or current project needs.

## Context Loading Strategy

**Base Project Context** (always loaded):
- @memory-bank/portfolio-insights.md - Project overview and Swiss tech market positioning
- @memory-bank/swiss-engineering-standards.md - Quality standards and requirements
- @context/key_files.md - Core system file references

**Task-Specific Context** (based on task area):
- **Epic 2 Demo**: Epic 2 features, demo requirements, Streamlit patterns
- **Neural Reranker**: Reranking algorithms, cross-encoder models, performance optimization
- **UI Development**: Streamlit patterns, user experience, demo presentation
- **Validation**: Test suites, quality metrics, validation frameworks

## Output Format

**📚 CONTEXT LOADED - [Task Area]**

**Base Context Summary**:
- **Project**: RAG Portfolio Project 1 - Technical Documentation System
- **Status**: 90.2% validation score, 100% architecture compliance
- **Architecture**: 6-component modular system with Epic 2 enhancements
- **Performance**: 565K chars/sec, 48.7x speedup, <10ms retrieval

**Task-Specific Context**:
- **Focus Area**: [Specified task area or current project needs]
- **Key Files**: [Relevant files and directories for the task]
- **Success Criteria**: [Quality gates and completion criteria]
- **Context Requirements**: [Loaded context fragments and their relevance]

**Current System State**:
- **Epic 2 Features**: Neural reranking, graph enhancement, analytics operational
- **Test Suite**: 122 test cases with formal acceptance criteria
- **Configurations**: Basic (default.yaml) and Epic 2 (advanced_test.yaml)
- **Data**: RISC-V technical documentation corpus for testing

**Ready For**:
- [Specific development actions enabled by loaded context]
- [Work areas appropriate for current task focus]
- [Next steps based on task area and project state]

Context loading complete. Ready for focused development work.