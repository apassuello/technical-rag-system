# CURRENT SESSION CONTEXT: IMPLEMENTER MODE - Query Processor Workflow Enhancement

## Role Focus: Phase 3 AdvancedRetriever Refactoring Implementation
**Perspective**: Swiss engineering implementation with query workflow focus
**Key Concerns**: Query workflow orchestration, platform service usage, Epic 2 features
**Decision Framework**: Clean workflow implementation, comprehensive testing, 100% compliance
**Output Style**: Working workflow, service integration, architecture compliance evidence
**Constraints**: Maintain Epic 2 features, Apple Silicon optimization, production readiness

## ⚠️ CRITICAL ARCHITECTURAL SAFEGUARDS ⚠️
**MANDATORY**: Consult `.claude/ARCHITECTURE_SAFEGUARDS.md` before ANY implementation
**MANDATORY**: Query Processor orchestrates workflow, does NOT implement component features
**MANDATORY**: Use platform services for system-wide concerns
**MANDATORY**: NO component-specific logic in Query Processor

## Implementation Target: Query Processor Workflow Enhancement
### Current Phase: Phase 3 of 3-phase refactoring
### Features to Implement: Query workflow orchestration using platform services
### Priority: MEDIUM - Clean query processing workflow
### Success Criteria: Query Processor orchestrates workflow using platform services

## Specific Query Workflow Features to Implement:

### 1. Query Analysis and Optimization (HIGH PRIORITY)
**Purpose**: Analyze queries and optimize for Epic 2 features
**Source**: Extract query-related logic from `advanced_retriever.py`
**Target**: `query_processor.py` - enhance existing QueryAnalyzer
**Features**:
- Query complexity analysis
- Epic 2 feature selection (neural reranking, graph enhancement)
- Query optimization strategies
- Performance prediction

### 2. Workflow Orchestration with Platform Services (HIGH PRIORITY)
**Purpose**: Orchestrate query workflow using platform services
**Source**: Extract workflow logic from `advanced_retriever.py:260-306`
**Target**: `query_processor.py` - enhance existing WorkflowOrchestrator
**Features**:
- A/B testing assignment via ABTestingService
- Health monitoring via ComponentHealthService
- Analytics collection via SystemAnalyticsService
- Configuration management via ConfigurationService

### 3. Response Assembly with Epic 2 Features (HIGH PRIORITY)
**Purpose**: Assemble responses with Epic 2 enhancements
**Source**: Extract response logic from `advanced_retriever.py`
**Target**: `query_processor.py` - enhance existing ResponseAssembler
**Features**:
- Neural reranking integration (via Answer Generator)
- Graph enhancement integration (via Document Processor)
- Advanced analytics integration
- Epic 2 feature coordination

### 4. Remaining Component Feature Placement (MEDIUM PRIORITY)
**Purpose**: Move remaining features to proper components
**Features to Move**:
- **Neural Reranking**: `advanced_retriever.py:124-150` → Enhanced Retriever sub-component
- **Graph Enhancement**: `advanced_retriever.py:96-103, 203-228` → Document Processor sub-component
- **Embedding Configuration**: `advanced_retriever.py:170-190` → Embedder sub-component
- **Document Migration**: `advanced_retriever.py:393-402` → Document Processor sub-component

## Key Files for Implementation:
- `/src/components/retrievers/advanced_retriever.py` - Source code to extract
- `/src/components/generators/answer_generator.py` - Target for neural reranking
- `/src/components/processors/document_processor.py` - Target for graph enhancement
- `/src/components/embedders/modular_embedder.py` - Target for embedding config
- `/config/advanced_test.yaml` - Configuration management
- `/tests/` - Comprehensive test validation

## Implementation Strategy:

### Step 1: Extract Neural Reranking Configuration
- Create `NeuralReranker` sub-component in Answer Generator
- Implement score fusion logic
- Add adaptive reranking configuration
- Test neural reranking functionality

### Step 2: Extract Graph Enhancement Logic
- Create `GraphEnhancer` sub-component in Document Processor
- Implement entity extraction and relationship mapping
- Add graph building logic
- Test graph enhancement functionality

### Step 3: Extract Document Migration
- Create `DocumentMigrator` sub-component in Document Processor
- Implement re-indexing and migration logic
- Add document lifecycle management
- Test migration functionality

### Step 4: Extract Embedding Configuration
- Create `EmbeddingConfigurator` sub-component in Embedder
- Implement backend-specific configuration
- Add optimization settings
- Test embedding configuration

### Step 5: Finalize AdvancedRetriever Cleanup
- Remove all extracted features from AdvancedRetriever
- Clean up remaining architecture violations
- Validate clean component boundaries
- Test complete system functionality

## Swiss Engineering Implementation Standards:
### Code Quality: Comprehensive error handling, proper logging, Swiss documentation
### Testing: Unit tests for each extracted component, integration tests
### Performance: Maintain Apple Silicon optimization, <5% performance overhead
### Backward Compatibility: Maintain existing component interfaces
### Architecture Compliance: 100% clean component boundaries

## Component Integration Strategy:

### Answer Generator Integration:
- Add `NeuralReranker` to existing sub-components
- Integrate with `SemanticScorer` for comprehensive scoring
- Maintain existing Answer Generator interface
- Test neural reranking integration

### Document Processor Integration:
- Add `GraphEnhancer` and `DocumentMigrator` to existing sub-components
- Integrate with existing document processing pipeline
- Maintain existing Document Processor interface
- Test graph enhancement and migration integration

### Embedder Integration:
- Add `EmbeddingConfigurator` to existing sub-components
- Integrate with existing embedding pipeline
- Maintain existing Embedder interface
- Test embedding configuration integration

## Success Criteria:
- [ ] All 4 remaining features migrated to proper components
- [ ] AdvancedRetriever contains only retrieval-specific functionality
- [ ] 100% component boundary compliance achieved
- [ ] All existing functionality preserved
- [ ] Comprehensive test coverage for migrated features
- [ ] Performance baseline maintained or improved
- [ ] Backward compatibility validated

## Testing Requirements:
- Unit tests for each new component sub-component
- Integration tests for component interactions
- Performance tests for complete system
- Compatibility tests for existing interfaces
- End-to-end tests for full system operation

## Quality Gates:
- **Architecture Compliance**: 100% component boundary compliance
- **Performance**: <5% overhead from complete migration
- **Testing**: >95% coverage for all migrated components
- **Backward Compatibility**: 100% existing functionality preserved
- **Swiss Standards**: Comprehensive documentation and error handling

## Final Architecture Validation:
- [ ] Platform Orchestrator: System-wide concerns only
- [ ] Document Processor: Document enhancement and migration
- [ ] Embedder: Embedding configuration and optimization
- [ ] Retriever: Document retrieval and ranking only
- [ ] Answer Generator: Neural reranking and answer generation
- [ ] Query Processor: Workflow orchestration and analytics

## Next Session Preparation:
- Validate complete system functionality
- Run comprehensive architecture compliance tests
- Document complete refactoring success
- Prepare Epic 2 demo with clean architecture