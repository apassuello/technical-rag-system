# Guide Comprehensive Checkpoint Process

Guide comprehensive checkpoint process for clean session transition and project milestone validation.

## Instructions

1. **Read current project state**
   - Read @current_plan.md for current task, progress, and validation requirements
   - Review session context and milestone status

2. **Use checkpoint template**
   - Load @session-templates/PROGRESS_CHECKPOINT.md as checklist template
   - Follow established checkpoint procedures and quality gates
   - Ensure all checkpoint criteria are met

3. **Guide validation process**
   - Execute all validation commands from current_plan.md
   - Verify system state and quality metrics
   - Ensure all tests pass before checkpoint completion

4. **Guide documentation process**
   - Ensure session is properly documented
   - Verify handoff documentation if session ending
   - Confirm all work is tracked and recorded

5. **Guide backup process**
   - Create git backup checkpoint for current state
   - Ensure recovery procedures are available
   - Verify backup integrity and accessibility

6. **Provide completion status**
   - Track checkpoint completion progress
   - Identify any incomplete items requiring attention
   - Confirm checkpoint readiness for transition

## Output Format

**✅ CHECKPOINT PROCESS GUIDE**

**Checkpoint Overview**:
- Process: Comprehensive checkpoint for session transition
- Target: Clean state validation and documentation
- Scope: Current task, validation, documentation, and backup

**Checkpoint Criteria**:

**1. Current Work Validation**
- [ ] **Execute validation commands**
  - Command: `python tests/run_comprehensive_tests.py`
  - Status: [PENDING/RUNNING/COMPLETE]
  - Result: [PASS/FAIL/ERROR]
  
- [ ] **Run diagnostic tests**
  - Command: `python tests/diagnostic/run_all_diagnostics.py`
  - Status: [PENDING/RUNNING/COMPLETE]
  - Result: [PASS/FAIL/ERROR]
  
- [ ] **Check architecture compliance**
  - Command: `python tests/integration_validation/validate_architecture_compliance.py`
  - Status: [PENDING/RUNNING/COMPLETE]
  - Result: [PASS/FAIL/ERROR]

**2. Progress Documentation**
- [ ] **Session documentation created**
  - Command: Use `/document` command
  - Status: [PENDING/COMPLETE]
  - Location: `sessions/session-[timestamp].md`
  
- [ ] **Progress updated in plan**
  - Target: Update @current_plan.md with current progress
  - Status: [PENDING/COMPLETE]
  - Changes: [Progress percentage and milestone updates]

**3. Backup Creation**
- [ ] **Git backup created**
  - Command: Use `/backup` command
  - Status: [PENDING/COMPLETE]
  - Branch: `backup-[current_task]-[timestamp]`
  
- [ ] **Backup verified**
  - Verification: Check backup branch exists and is complete
  - Status: [PENDING/COMPLETE]
  - Recovery: Instructions available and tested

**4. Session Handoff (if ending session)**
- [ ] **Handoff document created**
  - Command: Use `/handoff` command
  - Status: [PENDING/COMPLETE]
  - Location: `sessions/handoff-[timestamp].md`
  
- [ ] **Next session prompt prepared**
  - Ready-to-use prompt for next session startup
  - Status: [PENDING/COMPLETE]
  - Context: Requirements and validation specified

**5. Context State Management**
- [ ] **Context requirements updated**
  - Current context needs documented in @current_plan.md
  - Status: [PENDING/COMPLETE]
  - Requirements: [List current context_requirements]
  
- [ ] **Session tracking updated**
  - Recent work documented in @sessions/recent-work.md
  - Status: [PENDING/COMPLETE]
  - Summary: Session outcomes and next steps

**Checkpoint Status**: [COMPLETE/IN_PROGRESS/BLOCKED]

**Completion Summary**:
- **Validation**: [All tests passing/Issues identified]
- **Documentation**: [Session documented/Handoff prepared]
- **Backup**: [Backup created/Recovery verified]
- **Continuity**: [Next session ready/Context prepared]

**Next Steps**:
- [If checkpoint complete: Ready for session transition]
- [If issues found: Specific actions to resolve problems]
- [If blocked: Blocker identification and resolution approach]

**Checkpoint Quality Gates**:
- ✅ All validation commands pass
- ✅ Session work properly documented
- ✅ Git backup created and verified
- ✅ Next session preparation complete
- ✅ No blocking issues identified

**Checkpoint process complete. Ready for clean session transition.**