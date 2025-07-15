# CURRENT SESSION CONTEXT: IMPLEMENTER MODE - Component Interface Standardization

## Role Focus: Phase 2 AdvancedRetriever Refactoring Implementation
**Perspective**: Swiss engineering implementation with interface standardization focus
**Key Concerns**: Universal interfaces, service integration, cross-component applicability
**Decision Framework**: Standard interface implementation, comprehensive testing, service usage
**Output Style**: Working interfaces, service integration, universal capabilities
**Constraints**: Maintain Epic 2 features, Apple Silicon optimization, production readiness

## ⚠️ CRITICAL ARCHITECTURAL SAFEGUARDS ⚠️
**MANDATORY**: Consult `.claude/ARCHITECTURE_SAFEGUARDS.md` before ANY implementation
**MANDATORY**: All components must implement STANDARD INTERFACES
**MANDATORY**: Components must USE platform services, not implement them
**MANDATORY**: NO component-specific service implementations

## Implementation Target: Component Interface Standardization
### Current Phase: Phase 2 of 3-phase refactoring
### Interfaces to Implement: Standard interfaces in ALL components
### Priority: HIGH - Enable universal service access
### Success Criteria: All components implement standard interfaces and use platform services

## Specific Standard Interfaces to Implement:

### 1. Component Base Interface (HIGH PRIORITY)
**Purpose**: Universal interface for all components to use platform services
**Target**: All components (Document Processor, Embedder, Retriever, Answer Generator, Query Processor)
**Interface Methods**:
- `get_health_status() -> HealthStatus` - Report component health
- `get_metrics() -> Dict[str, Any]` - Report component metrics
- `get_capabilities() -> List[str]` - Report component capabilities
- `initialize_services(platform: PlatformOrchestrator) -> None` - Initialize platform services

### 2. AdvancedRetriever Interface Implementation (HIGH PRIORITY)
**Purpose**: Convert AdvancedRetriever to use platform services
**Source**: Remove service implementations from `advanced_retriever.py`
**Target**: `advanced_retriever.py` - implement standard interfaces
**Interface Implementation**:
- `get_health_status()` - Use ComponentHealthService
- `get_metrics()` - Use SystemAnalyticsService
- `get_capabilities()` - Report retrieval capabilities
- `initialize_services()` - Connect to platform services

### 3. All Components Interface Implementation (HIGH PRIORITY)
**Purpose**: Implement standard interfaces in ALL components
**Components**: Document Processor, Embedder, Answer Generator, Query Processor
**Interface Implementation**:
- `get_health_status()` - Component-specific health reporting
- `get_metrics()` - Component-specific metrics
- `get_capabilities()` - Component-specific capabilities
- `initialize_services()` - Platform service initialization

### 4. Platform Service Integration (HIGH PRIORITY)
**Purpose**: Enable all components to use platform services
**Integration Points**:
- Health monitoring via ComponentHealthService
- Analytics collection via SystemAnalyticsService
- A/B testing via ABTestingService
- Configuration management via ConfigurationService
- Backend management via BackendManagementService

## Key Files for Implementation:
- `/src/components/retrievers/advanced_retriever.py` - Source code to extract
- `/src/components/query_processors/modular_query_processor.py` - Target implementation
- `/src/core/interfaces.py` - Interface definitions
- `/config/advanced_test.yaml` - Configuration management
- `/tests/` - Comprehensive test validation

## Implementation Strategy:

### Step 1: Extract Query Analytics Collection
- Create `QueryAnalytics` sub-component in Query Processor
- Implement analytics collection interfaces
- Add query performance tracking
- Test analytics accuracy and reporting

### Step 2: Extract Workflow Orchestration Logic
- Create `WorkflowOrchestrator` sub-component in Query Processor
- Implement workflow decision making
- Add pipeline coordination
- Test workflow orchestration functionality

### Step 3: Extract A/B Testing Framework
- Create `ExperimentManager` sub-component in Query Processor
- Implement experiment configuration
- Add assignment and analysis methods
- Test A/B testing functionality

### Step 4: Integrate with Existing Query Processor
- Update `ModularQueryProcessor` to include new sub-components
- Implement proper workflow orchestration
- Add configuration management
- Test complete query processing pipeline

### Step 5: Remove Workflow Logic from AdvancedRetriever
- Remove query analytics from retriever
- Remove workflow orchestration logic
- Remove A/B testing framework
- Test retriever with clean boundaries

## Swiss Engineering Implementation Standards:
### Code Quality: Comprehensive error handling, proper logging, Swiss documentation
### Testing: Unit tests for each extracted component, integration tests
### Performance: Maintain Apple Silicon optimization, <5% performance overhead
### Backward Compatibility: Maintain existing query processing interface
### Architecture Compliance: Clean component boundaries, proper interfaces

## Query Processor Sub-component Architecture:
### Existing Sub-components:
- `QueryAnalyzer` - Query analysis and optimization
- `ContextSelector` - Context selection and ranking
- `ResponseAssembler` - Response formatting and assembly

### New Sub-components (from AdvancedRetriever):
- `QueryAnalytics` - Analytics collection and reporting
- `WorkflowOrchestrator` - Workflow coordination and decision making
- `ExperimentManager` - A/B testing and experimentation

## Success Criteria:
- [ ] All 3 workflow features migrated to Query Processor
- [ ] AdvancedRetriever no longer contains workflow orchestration
- [ ] All existing query processing functionality preserved
- [ ] Comprehensive test coverage for migrated features
- [ ] Performance baseline maintained or improved
- [ ] Backward compatibility validated

## Testing Requirements:
- Unit tests for each new Query Processor sub-component
- Integration tests for workflow orchestration
- Performance tests for query processing pipeline
- Compatibility tests for existing interfaces
- End-to-end tests for complete query processing

## Quality Gates:
- **Architecture Compliance**: Workflow concerns properly isolated in Query Processor
- **Performance**: <5% overhead from migration
- **Testing**: >95% coverage for migrated components
- **Backward Compatibility**: 100% existing functionality preserved
- **Swiss Standards**: Comprehensive documentation and error handling

## Next Session Preparation:
- Validate all migrated components working correctly
- Prepare for Phase 3: Remaining component cleanup
- Update component interfaces for extracted features
- Document migration success and lessons learned