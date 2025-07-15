# AdvancedRetriever Refactoring: Session Implementation Guide

## **🚨 MANDATORY PRE-SESSION READING**
```bash
# CRITICAL: Read this before starting ANY session
cat .claude/ARCHITECTURE_SAFEGUARDS.md
```

**This document contains the architectural safeguards that prevent the violations identified in the original analysis.**

---

## **📋 Context Management for Long Tasks**

### **Context Extension Strategy**
For complex refactoring sessions that span multiple conversations, use the session handoff system:

```bash
# After each session, create a handoff document
cp .claude/session-templates/REFACTORING_SESSION_HANDOFF.md session-1-handoff.md

# Fill in the handoff template with:
# - Session accomplishments
# - Architecture compliance status
# - Performance metrics
# - Issues encountered
# - Next session context setup

# For next session, reference the handoff:
# "Read session-1-handoff.md for context on previous session results"
```

### **Context Continuity Commands**
```bash
# Start new session with context from previous
claude code

# First prompt in new session:
"Please read session-X-handoff.md to understand the current state from the previous session, then read .claude/claude.md for the current session objectives."
```

---

## **SESSION 1: Platform Orchestrator System Services**

### **📁 Setup Instructions**
```bash
# 1. Create backup branch
git checkout -b backup-before-session-1

# 2. Copy context template
cp .claude/context-templates/IMPLEMENTER_MODE_PLATFORM_ORCHESTRATOR_MIGRATION.md .claude/claude.md

# 3. Start Claude Code
claude code
```

### **🎯 Initial Prompt for Claude Code**
```
I'm starting Session 1 of the AdvancedRetriever refactoring. Please:

1. Read the current context from .claude/claude.md to understand the session objectives
2. Read .claude/ARCHITECTURE_SAFEGUARDS.md to understand the critical architectural requirements
3. Analyze the current AdvancedRetriever implementation in src/components/retrievers/advanced_retriever.py
4. Create the 5 universal system services in the Platform Orchestrator:
   - ComponentHealthService (universal health monitoring for ALL components)
   - SystemAnalyticsService (universal analytics collection for ALL components)
   - ABTestingService (universal A/B testing for ALL components)
   - ConfigurationService (universal configuration management for ALL components)
   - BackendManagementService (universal backend management for ALL components)

CRITICAL: These must be SERVICES that ALL components can use, not feature containers. Follow the service interface patterns specified in the context.

Start by confirming you understand the session objectives and architectural requirements.
```

### **✅ Success Criteria**
- [ ] 5 universal system services created in Platform Orchestrator
- [ ] Services follow standard interface patterns
- [ ] Services are usable by ALL components
- [ ] No component-specific logic in Platform Orchestrator
- [ ] <5% performance overhead

### **🔍 Key Files to Monitor**
- `src/core/platform_orchestrator.py` (target for services)
- `src/components/retrievers/advanced_retriever.py` (source of violations)

---

## **SESSION 2: Component Interface Standardization**

### **📁 Setup Instructions**
```bash
# 1. Create backup branch
git checkout -b backup-before-session-2

# 2. Copy context template
cp .claude/context-templates/IMPLEMENTER_MODE_QUERY_PROCESSOR_MIGRATION.md .claude/claude.md

# 3. If continuing from previous session, create handoff
cp .claude/session-templates/REFACTORING_SESSION_HANDOFF.md session-1-handoff.md
# Fill in session-1-handoff.md with results from Session 1

# 4. Start Claude Code
claude code
```

### **🎯 Initial Prompt for Claude Code**
```
I'm starting Session 2 of the AdvancedRetriever refactoring. Please:

1. ReadSESSION_1_HANDOFF_DOCUMENT.md to understand the current state from Session 1
2. Read the current context from .claude/claude.md to understand the session objectives
3. Read .claude/ARCHITECTURE_SAFEGUARDS.md to understand the critical architectural requirements
4. Validate that Session 1 services are properly implemented in the Platform Orchestrator
5. Implement standard interfaces in ALL components:
   - Component Base Interface (get_health_status, get_metrics, get_capabilities, initialize_services)
   - Update AdvancedRetriever to use platform services instead of implementing its own
   - Update ALL other components (Document Processor, Embedder, Answer Generator, Query Processor)
   - Enable platform service integration across all components

CRITICAL: Components must USE platform services, not implement their own. All components must implement the same standard interfaces for cross-component applicability.

Start by confirming you understand the session objectives and validating Session 1 results.
```

### **✅ Success Criteria**
- [ ] Standard interfaces implemented in ALL components
- [ ] AdvancedRetriever uses platform services
- [ ] All components use platform services
- [ ] Cross-component feature applicability achieved
- [ ] <5% performance overhead

### **🔍 Key Files to Monitor**
- All component files (implementing standard interfaces)
- `src/core/interfaces.py` (interface definitions)

---

## **SESSION 3: Query Processor Workflow Enhancement**

### **📁 Setup Instructions**
```bash
# 1. Create backup branch
git checkout -b backup-before-session-3

# 2. Copy context template
cp .claude/context-templates/IMPLEMENTER_MODE_COMPONENT_CLEANUP.md .claude/claude.md

# 3. If continuing from previous session, create handoff
cp .claude/session-templates/REFACTORING_SESSION_HANDOFF.md session-2-handoff.md
# Fill in session-2-handoff.md with results from Session 2

# 4. Start Claude Code
claude code
```

### **🎯 Initial Prompt for Claude Code**
```
I'm starting Session 3 of the AdvancedRetriever refactoring. Please:

1. Read session-2-handoff.md (if exists) to understand the current state from Session 2
2. Read the current context from .claude/claude.md to understand the session objectives
3. Read .claude/ARCHITECTURE_SAFEGUARDS.md to understand the critical architectural requirements
4. Validate that Session 2 interfaces are properly implemented in all components
5. Enhance the Query Processor workflow to use platform services:
   - Enhanced QueryAnalyzer with Epic 2 feature selection
   - Enhanced WorkflowOrchestrator using platform services (ABTestingService, ComponentHealthService, SystemAnalyticsService)
   - Enhanced ResponseAssembler with Epic 2 integration
   - Move remaining component features to their proper locations:
     * Neural reranking → Enhanced Retriever sub-component
     * Graph enhancement → Document Processor sub-component
     * Embedding configuration → Embedder sub-component
     * Document migration → Document Processor sub-component

CRITICAL: Query Processor must ORCHESTRATE workflow using platform services, not implement component features. Maintain Epic 2 functionality while achieving 100% component boundary compliance.

Start by confirming you understand the session objectives and validating Session 2 results.
```

### **✅ Success Criteria**
- [ ] Query Processor orchestrates workflow using platform services
- [ ] Epic 2 features properly integrated
- [ ] 100% component boundary compliance
- [ ] All remaining features moved to proper components
- [ ] <5% performance overhead

### **🔍 Key Files to Monitor**
- `src/components/query_processors/modular_query_processor.py` (workflow orchestration)
- `src/components/retrievers/advanced_retriever.py` (final cleanup)

---

## **📊 Session Validation Commands**

### **Pre-Session Validation**
```bash
# Validate system baseline
python tests/run_comprehensive_tests.py
python tests/diagnostic/run_all_diagnostics.py
python tests/integration_validation/validate_architecture_compliance.py

# Check current performance
python epic2_performance_analysis.py  # Add your performance measurement commands
```

### **Post-Session Validation**
```bash
# Validate functionality
python tests/run_comprehensive_tests.py

# Check architecture compliance
python tests/integration_validation/validate_architecture_compliance.py

# Measure performance impact
python epic2_performance_analysis.py  # Add your performance measurement commands

# Commit session results
git add .
git commit -m "Session X: [Description] - [Architecture compliance improvement]"
```

---

## **📋 Session Progress Tracking**

### **Session 1 Progress Checklist**
- [ ] ComponentHealthService created and tested
- [ ] SystemAnalyticsService created and tested
- [ ] ABTestingService created and tested
- [ ] ConfigurationService created and tested
- [ ] BackendManagementService created and tested
- [ ] All services follow standard interface patterns
- [ ] Performance impact measured and documented
- [ ] Session handoff document created

### **Session 2 Progress Checklist**
- [ ] Component base interface defined
- [ ] AdvancedRetriever implements standard interface
- [ ] Document Processor implements standard interface
- [ ] Embedder implements standard interface
- [ ] Answer Generator implements standard interface
- [ ] Query Processor implements standard interface
- [ ] All components use platform services
- [ ] Cross-component applicability validated
- [ ] Performance impact measured and documented
- [ ] Session handoff document created

### **Session 3 Progress Checklist**
- [ ] QueryAnalyzer enhanced with Epic 2 features
- [ ] WorkflowOrchestrator uses platform services
- [ ] ResponseAssembler integrates Epic 2 features
- [ ] Neural reranking moved to Retriever sub-component
- [ ] Graph enhancement moved to Document Processor
- [ ] Embedding configuration moved to Embedder
- [ ] Document migration moved to Document Processor
- [ ] 100% component boundary compliance achieved
- [ ] Performance impact measured and documented
- [ ] Final validation completed

---

## **🚨 Emergency Procedures**

### **If Session Goes Wrong**
```bash
# 1. Stop immediately
# 2. Read the safeguards
cat .claude/ARCHITECTURE_SAFEGUARDS.md

# 3. Rollback to backup
git checkout backup-before-session-X

# 4. Review architectural violations
# 5. Restart with corrected approach
```

### **If Claude Makes Architectural Errors**
```bash
# 1. Stop Claude immediately (Escape key)
# 2. Point Claude to specific safeguard violations
# 3. Reference the specific anti-pattern from ARCHITECTURE_SAFEGUARDS.md
# 4. Restart with corrected approach
```

### **Common Error Recovery**
```bash
# If Claude tries to move features to Platform Orchestrator:
"Stop. Read .claude/ARCHITECTURE_SAFEGUARDS.md section on 'VIOLATION 1: Platform Orchestrator Feature Dumping'. Platform Orchestrator provides SERVICES, not features."

# If Claude tries to implement orchestration in components:
"Stop. Read .claude/ARCHITECTURE_SAFEGUARDS.md section on 'VIOLATION 2: Component Orchestration Logic'. Components USE services, not implement them."

# If Claude violates direct wiring pattern:
"Stop. Read .claude/ARCHITECTURE_SAFEGUARDS.md section on 'VIOLATION 3: Direct Wiring Pattern Violation'. No runtime component creation."
```

---

## **📈 Architecture Compliance Progression**

### **Expected Compliance Progression**
- **Initial**: 40% (Critical violations)
- **After Session 1**: 60% (System services established)
- **After Session 2**: 80% (Interface standardization complete)
- **After Session 3**: 100% (Complete boundary compliance)

### **Performance Impact Expectations**
- **Session 1**: <5% overhead (service architecture)
- **Session 2**: <5% overhead (interface standardization)
- **Session 3**: <5% overhead (workflow enhancement)
- **Total**: <10% architectural overhead (Swiss engineering acceptable)

---

## **🔄 Context Continuity Best Practices**

### **Between Sessions**
1. **Create detailed handoff documents** using the template
2. **Document all architectural decisions** and rationale
3. **Record performance metrics** before and after
4. **Note any issues or deviations** from the plan

### **Starting New Sessions**
1. **Always read previous session handoff** first
2. **Validate previous session results** before proceeding
3. **Confirm architectural compliance** from previous session
4. **Check performance baselines** are maintained

### **Long Task Management**
1. **Use session templates** for consistent context
2. **Create backup branches** before each session
3. **Document progress** in handoff templates
4. **Validate architecture compliance** after each session

---

## **📚 Key Documents Reference**

### **Architecture Documents**
- `.claude/ARCHITECTURE_SAFEGUARDS.md` - Critical safeguards (READ FIRST)
- `docs/architecture/MASTER-ARCHITECTURE.md` - Complete system specification
- `docs/architecture/components/component-*.md` - Component specifications

### **Context Templates**
- `IMPLEMENTER_MODE_PLATFORM_ORCHESTRATOR_MIGRATION.md` - Session 1
- `IMPLEMENTER_MODE_QUERY_PROCESSOR_MIGRATION.md` - Session 2
- `IMPLEMENTER_MODE_COMPONENT_CLEANUP.md` - Session 3

### **Session Management**
- `REFACTORING_SESSION_HANDOFF.md` - Session handoff template
- `ADVANCED_RETRIEVER_REFACTORING_PLAN.md` - Complete strategy
- `SESSION_IMPLEMENTATION_GUIDE.md` - This document

---

## **🎯 Final Success Validation**

### **Complete Refactoring Success**
- [ ] All 5 platform services implemented and tested
- [ ] All 6 components implement standard interfaces
- [ ] All components use platform services
- [ ] Query Processor orchestrates workflow properly
- [ ] Epic 2 features properly integrated
- [ ] 100% component boundary compliance
- [ ] <10% total performance overhead
- [ ] Swiss engineering standards maintained

### **Epic 2 Feature Validation**
- [ ] Multi-backend support working
- [ ] Neural reranking functional
- [ ] Graph enhancement operational
- [ ] A/B testing framework active
- [ ] Analytics collection working
- [ ] Health monitoring operational

Each session builds upon the previous one, progressively restoring proper component boundaries while maintaining all Epic 2 features and Swiss engineering standards.