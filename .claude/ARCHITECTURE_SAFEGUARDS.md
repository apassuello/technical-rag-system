# Architecture Safeguards: Preventing Common Violations

## Critical Reminder: These safeguards MUST be consulted before any architectural decision.

## **MANDATORY ARCHITECTURE VALIDATION CHECKLIST**

### Before Making ANY Component Change:

1. **[ ] Read the Master Architecture Document**
   - Location: `docs/architecture/MASTER-ARCHITECTURE.md`
   - Validate against 6-component architecture principles
   - Check adapter pattern vs direct implementation guidelines

2. **[ ] Validate Component Responsibilities**
   - Location: `docs/architecture/components/component-[1-6]-*.md`
   - Confirm feature belongs in target component
   - Check for responsibility overlap

3. **[ ] Apply Platform Orchestrator Service Pattern**
   - Ask: "Is this a system-wide service ALL components need?"
   - If YES: Implement as Platform Orchestrator service
   - If NO: Check if it's component-specific functionality

4. **[ ] Verify Cross-Component Applicability**
   - Ask: "Will other components need this feature?"
   - If YES: Must be Platform Orchestrator service
   - If NO: Can be component-specific if truly isolated

5. **[ ] Check Interface Standardization**
   - Ask: "Does this require new component interfaces?"
   - All components must implement standard interfaces
   - Platform Orchestrator provides services through standard interfaces

## **CRITICAL ARCHITECTURAL VIOLATIONS TO AVOID**

### 🚫 **VIOLATION 1: Platform Orchestrator Feature Dumping**
**Wrong Approach**: Moving component features to Platform Orchestrator
```python
# WRONG: Platform Orchestrator implementing component features
class PlatformOrchestrator:
    def perform_neural_reranking(self):  # VIOLATION: Component feature
        pass
    def extract_document_entities(self):  # VIOLATION: Component feature
        pass
```

**Correct Approach**: Platform Orchestrator provides system-wide services
```python
# CORRECT: Platform Orchestrator provides services
class PlatformOrchestrator:
    def monitor_component_health(self, component: Component):  # Service
        return self.health_service.check_health(component)
    def collect_component_metrics(self, component: Component):  # Service
        return self.analytics_service.collect_metrics(component)
```

### 🚫 **VIOLATION 2: Component Orchestration Logic**
**Wrong Approach**: Components implementing system orchestration
```python
# WRONG: Component implementing orchestration
class AdvancedRetriever:
    def __init__(self):
        self.health_monitor = HealthMonitor()  # VIOLATION: System concern
        self.analytics_collector = Analytics()  # VIOLATION: System concern
        self.ab_testing = ABTesting()  # VIOLATION: System concern
```

**Correct Approach**: Components use Platform Orchestrator services
```python
# CORRECT: Component uses platform services
class AdvancedRetriever:
    def __init__(self, platform: PlatformOrchestrator):
        self.platform = platform  # Uses platform services
    
    def get_health_status(self) -> HealthStatus:
        return HealthStatus(backend_status=self.vector_index.status)
```

### 🚫 **VIOLATION 3: Direct Wiring Pattern Violation**
**Wrong Approach**: Runtime component creation and switching
```python
# WRONG: Runtime component creation
class AdvancedRetriever:
    def _switch_backend(self, backend_name: str):
        new_index = self._create_vector_index(config)  # VIOLATION: Runtime creation
        self.vector_index = new_index  # VIOLATION: Reference switching
```

**Correct Approach**: Component Factory handles all creation
```python
# CORRECT: Component Factory creation
class PlatformOrchestrator:
    def __init__(self):
        self.component_factory = ComponentFactory()
        self.retriever = self.component_factory.create_retriever("advanced")
```

### 🚫 **VIOLATION 4: Query Processor Misuse**
**Wrong Approach**: Moving retrieval features to Query Processor
```python
# WRONG: Query Processor implementing retrieval
class QueryProcessor:
    def perform_document_search(self):  # VIOLATION: Retriever responsibility
        pass
    def rank_documents(self):  # VIOLATION: Retriever responsibility
        pass
```

**Correct Approach**: Query Processor orchestrates workflow
```python
# CORRECT: Query Processor orchestrates workflow
class QueryProcessor:
    def process_query(self, query: str) -> ProcessedQuery:
        # Analyze query
        analyzed = self.query_analyzer.analyze(query)
        # Orchestrate retrieval (doesn't implement it)
        results = self.retriever.retrieve(analyzed)
        # Assemble response
        return self.response_assembler.assemble(results)
```

## **MANDATORY COMPONENT RESPONSIBILITY MATRIX**

### **Platform Orchestrator (C1) - System-Wide Services**
**Responsibilities**:
- ✅ Component health monitoring (as service)
- ✅ System analytics collection (as service)
- ✅ A/B testing framework (as service)
- ✅ Configuration management (as service)
- ✅ Component lifecycle management
- ✅ Cross-cutting concerns coordination

**Anti-Patterns**:
- ❌ Implementing component-specific features
- ❌ Direct document processing
- ❌ Query-specific logic
- ❌ Answer generation logic

### **Document Processor (C2) - Document Enhancement**
**Responsibilities**:
- ✅ Document parsing and cleaning
- ✅ Text chunking and segmentation
- ✅ Graph enhancement (entity extraction, relationships)
- ✅ Document migration between systems
- ✅ Content quality validation

**Anti-Patterns**:
- ❌ System health monitoring
- ❌ Query processing workflow
- ❌ Answer generation
- ❌ System-wide analytics

### **Embedder (C3) - Vector Representation**
**Responsibilities**:
- ✅ Text embedding generation
- ✅ Embedding model management
- ✅ Batch processing optimization
- ✅ Embedding cache management
- ✅ Vector optimization

**Anti-Patterns**:
- ❌ Document search and retrieval
- ❌ Answer generation
- ❌ System orchestration
- ❌ Query workflow management

### **Retriever (C4) - Document Search**
**Responsibilities**:
- ✅ Document search and ranking
- ✅ Vector similarity search
- ✅ Sparse retrieval (BM25)
- ✅ Result fusion strategies
- ✅ Neural reranking (as sub-component)

**Anti-Patterns**:
- ❌ System health monitoring
- ❌ Query workflow orchestration
- ❌ Answer generation
- ❌ System-wide analytics

### **Answer Generator (C5) - Response Generation**
**Responsibilities**:
- ✅ LLM prompt construction
- ✅ Response generation
- ✅ Answer quality scoring
- ✅ Response parsing and formatting
- ✅ Confidence calculation

**Anti-Patterns**:
- ❌ Document retrieval
- ❌ System orchestration
- ❌ Query workflow management
- ❌ System health monitoring

### **Query Processor (C6) - Query Workflow**
**Responsibilities**:
- ✅ Query analysis and optimization
- ✅ Workflow orchestration
- ✅ Context selection
- ✅ Response assembly
- ✅ Query-specific analytics

**Anti-Patterns**:
- ❌ Document search implementation
- ❌ System health monitoring
- ❌ Answer generation implementation
- ❌ System-wide orchestration

## **ARCHITECTURAL DECISION FRAMEWORK**

### **Step 1: Identify the Feature**
- What does this feature do?
- What data does it process?
- What decisions does it make?

### **Step 2: Determine Scope**
- Is this feature needed by ALL components? → Platform Orchestrator service
- Is this feature specific to ONE component? → Component-specific implementation
- Is this feature about query workflow? → Query Processor responsibility

### **Step 3: Validate Responsibility**
- Does this fit the component's core responsibility?
- Does this violate any anti-patterns?
- Does this require new interfaces?

### **Step 4: Check Cross-Component Impact**
- Will other components need this feature?
- Does this create dependencies between components?
- Does this maintain clean boundaries?

## **IMPLEMENTATION SAFEGUARDS**

### **Before Writing ANY Code**:
1. **[ ] Consult this safeguard document**
2. **[ ] Read relevant component specification**
3. **[ ] Validate against master architecture**
4. **[ ] Check for anti-patterns**
5. **[ ] Confirm cross-component applicability**

### **During Implementation**:
1. **[ ] Follow established patterns**
2. **[ ] Implement standard interfaces**
3. **[ ] Use Platform Orchestrator services**
4. **[ ] Avoid component orchestration logic**
5. **[ ] Maintain clean boundaries**

### **After Implementation**:
1. **[ ] Validate architecture compliance**
2. **[ ] Test cross-component applicability**
3. **[ ] Confirm no anti-patterns introduced**
4. **[ ] Update interfaces if needed**
5. **[ ] Document architectural decisions**

## **EMERGENCY ARCHITECTURAL REVIEW**

### **If You're Unsure About ANY Decision**:
1. **STOP** implementation immediately
2. **READ** the master architecture document
3. **VALIDATE** against this safeguard document
4. **CONSULT** component specifications
5. **CONFIRM** cross-component applicability
6. **PROCEED** only after validation

### **Red Flags That Require Immediate Review**:
- ❌ Moving features between components
- ❌ Creating new orchestration logic
- ❌ Implementing system-wide concerns in components
- ❌ Adding cross-component dependencies
- ❌ Violating direct wiring patterns

## **SWISS ENGINEERING STANDARDS COMPLIANCE**

### **Architecture Quality Gates**:
- **[ ] Component Boundary Compliance**: 100% (no violations)
- **[ ] Interface Standardization**: All components implement standard interfaces
- **[ ] Service Pattern Compliance**: Platform Orchestrator provides services only
- **[ ] Cross-Component Applicability**: Features available to all components
- **[ ] Direct Wiring Compliance**: No runtime component creation

### **Quality Validation Commands**:
```bash
# Architecture compliance check
python tests/integration_validation/validate_architecture_compliance.py

# Component boundary validation
python tests/integration_validation/validate_component_boundaries.py

# Interface standardization check
python tests/integration_validation/validate_component_interfaces.py
```

Remember: **Architecture violations are technical debt that compounds exponentially**. Following these safeguards ensures Swiss engineering standards and long-term maintainability.