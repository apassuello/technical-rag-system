# Restore Context After Compaction

**Usage**: `/restore [work-area]`  
**Purpose**: Quickly restore context and working state after automatic conversation compaction

## Quick Restoration Commands

### **For Epic 2 Demo Work**
```bash
/restore epic2-demo
# Executes:
# /context epic2-demo
# /implementer streamlit-ui  
# /status epic2
```

### **For Neural Reranker Work**
```bash
/restore neural-reranker
# Executes:
# /context neural-reranker
# /implementer neural-reranker
# /status performance
```

### **For Architecture Review**
```bash
/restore architecture
# Executes:
# /context component-boundaries
# /architect epic2-demo
# /status architecture
```

### **For Testing Work**
```bash
/restore testing
# Executes:
# /context validation
# /validator diagnostic
# /status tests
```

## Instructions

Load context restoration guidance and provide quick restart commands for the specified work area.

## Context Recovery Strategy

**Immediate Actions** (execute automatically):
1. **Load Context**: Restore context for the specified work area
2. **Set Role**: Switch to appropriate role for the work area
3. **Check Status**: Validate current system state
4. **Verify Health**: Quick system health check

**Recovery Areas**:
- **epic2-demo**: Epic 2 demo development and Streamlit UI
- **neural-reranker**: Neural reranking implementation and optimization
- **architecture**: System architecture review and component design
- **testing**: Test suite validation and quality assurance
- **performance**: Performance optimization and benchmarking

## Output Format

**🔄 CONTEXT RESTORED - [Work Area]**

**Post-Compaction Recovery Complete**:
- **Context**: Loaded for [work area] development
- **Role**: Set to appropriate mode for [work area]
- **Status**: System validated and operational
- **Health**: Epic 2 features and core system verified

**Work Area Focus**: [Specific work area and current objectives]

**Quick Validation Results**:
- **Epic 2 Status**: [Neural reranking, graph enhancement operational]
- **System Health**: [90.2% validation score, architecture compliance]
- **Performance**: [565K chars/sec, 48.7x speedup verified]

**Current System State**:
- **Task**: [current_task from current_plan.md]
- **Progress**: [progress]% complete  
- **Phase**: [current_phase from current_plan.md]
- **Next Milestone**: [next_milestone from current_plan.md]

**Ready to Continue**:
- [Specific actions you can take in this work area]
- [Files and components relevant to current focus]
- [Recommended next steps based on work area]

**Context restoration complete. Ready to continue development work seamlessly.**

## Emergency Recovery

If unsure of previous work area:
1. Check `@current_plan.md` for current task
2. Check `@sessions/recent-work.md` for latest activity  
3. Use `/status` for overall system state
4. Use `/context` for general project context

Context restored. Development work can continue without interruption.