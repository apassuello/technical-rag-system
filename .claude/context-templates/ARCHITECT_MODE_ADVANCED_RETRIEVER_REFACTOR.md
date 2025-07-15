# CURRENT SESSION CONTEXT: ARCHITECT MODE - AdvancedRetriever Refactoring

## Role Focus: Critical Architecture Violation Remediation
**Perspective**: Swiss engineering standards applied to component boundary restoration
**Key Concerns**: 8 major architectural violations across all 6 components
**Decision Framework**: Component responsibility matrix, Swiss quality standards, clean architecture
**Output Style**: System service definitions, interface standardization, architectural compliance
**Constraints**: Zero functionality loss, maintain Epic 2 features, backward compatibility

## ⚠️ CRITICAL ARCHITECTURAL SAFEGUARDS ⚠️
**MANDATORY**: Consult `.claude/ARCHITECTURE_SAFEGUARDS.md` before ANY architectural decision
**MANDATORY**: Platform Orchestrator provides SERVICES, not feature containers
**MANDATORY**: Components use services through STANDARD INTERFACES
**MANDATORY**: NO component implements system orchestration logic

## Critical Architecture Status
### Current Issue: AdvancedRetriever violates 6-component architecture
### Violation Impact: 40% architecture compliance, 300% testing complexity increase
### Refactoring Priority: HIGH - Critical architectural violations identified
### Swiss Engineering Impact: Clean architecture principles severely compromised

## Key Violations Identified (From Analysis):

### 1. Platform Orchestrator Violations (HIGH PRIORITY)
- **System Health Monitoring** (Lines 254-259, 308-339)
- **Backend Management** (Lines 340-413)
- **System Statistics** (Lines 83-91)
- **Configuration Management** (Lines 119-229)
- **Analytics Framework** (Lines 92-94, 142-172)
- **Feature Flag Management** (Lines 234-250)

### 2. Query Processor Violations (HIGH PRIORITY)
- **Query Analytics Collection** (Lines 94, 289)
- **Workflow Orchestration Logic** (Lines 260-306)
- **A/B Testing Framework** (Lines 175-210)

### 3. Answer Generator Violations (MEDIUM PRIORITY)
- **Neural Reranking Configuration** (Lines 124-150)
- **Performance Analytics** (Lines 137-149)

### 4. Document Processor Violations (MEDIUM PRIORITY)
- **Graph Enhancement Logic** (Lines 96-103, 203-228)
- **Document Migration** (Lines 393-402)

### 5. Embedder Violations (LOW PRIORITY)
- **Embedding Configuration** (Lines 170-190)

## 3-Phase Refactoring Strategy (CORRECTED)

### Phase 1: Platform Orchestrator System Services (Session 1)
**Focus**: Create universal system services in Platform Orchestrator
**Services**: ComponentHealthService, SystemAnalyticsService, ABTestingService
**Priority**: Critical - establish service-based architecture
**Success Criteria**: Platform Orchestrator provides system-wide services that ALL components can use

### Phase 2: Component Interface Standardization (Session 2)
**Focus**: Implement standard interfaces in ALL components
**Interfaces**: get_health_status(), get_metrics(), get_capabilities()
**Priority**: High - enable universal service access
**Success Criteria**: All components implement standard interfaces and use platform services

### Phase 3: Query Processor Workflow Enhancement (Session 3)
**Focus**: Implement proper query workflow orchestration
**Features**: Query analysis, workflow coordination, response assembly using platform services
**Priority**: Medium - clean query processing workflow
**Success Criteria**: Query Processor orchestrates workflow using platform services

## Key Files for This Session:
- `/src/components/retrievers/advanced_retriever.py` - Source of violations
- `/src/core/platform_orchestrator.py` - Target for system-wide features
- `/src/components/query_processors/` - Target for workflow features
- `/docs/architecture/MASTER-ARCHITECTURE.md` - Architecture compliance reference
- `/docs/architecture/components/component-*.md` - Component specifications

## Swiss Engineering Architecture Principles:
### Single Responsibility Principle: Each component has one clear purpose
### Clean Architecture: Dependencies flow inward, no circular dependencies
### Interface Segregation: Components interact through well-defined interfaces
### Dependency Inversion: High-level components don't depend on implementation details
### Swiss Quality Standards: Quantified compliance metrics, comprehensive testing

## Session Success Criteria:
- [ ] Architectural violations categorized and prioritized
- [ ] Component responsibility matrix defined
- [ ] Interface contracts specified for component interactions
- [ ] Migration plan with zero functionality loss
- [ ] Backward compatibility strategy defined
- [ ] Performance impact assessment completed

## Architecture Compliance Metrics:
- **Target**: 100% component boundary compliance (from current 40%)
- **Testing Complexity**: Reduce from 300% to 110% (10% acceptable overhead)
- **Maintenance Burden**: Reduce from 250% to 120% (Swiss engineering standards)
- **Performance Impact**: Reduce from 40% overhead to <5% (embedded systems efficiency)

## Avoid in This Mode:
- Implementation details and specific code changes
- Test implementation (validation mode concern)
- Timeline and project management (portfolio curator concern)
- Performance optimization (optimizer mode concern)

## Next Session Preparation:
- Document component migration plan with specific interfaces
- Define backward compatibility requirements
- Establish performance baseline for refactoring validation
- Create architectural compliance testing criteria