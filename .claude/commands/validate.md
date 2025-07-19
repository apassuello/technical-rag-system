# Execute Validation Commands

Execute validation commands to assess current project state and quality.

## Instructions

1. **Read validation configuration**
   - Read .claude/current_plan.md for validation_commands array
   - Review validation commands specified for current project state

2. **Execute validation commands**
   - Run each validation command listed in validation_commands
   - Capture output, exit codes, and any error messages
   - Handle timeouts and command failures gracefully

3. **Interpret validation results**
   - Analyze output from each validation command
   - Determine pass/fail status and quality metrics
   - Identify any critical issues or failures

4. **Update validation tracking**
   - Update .claude/sessions/validation-results.md with current validation status
   - Record timestamp, commands executed, and results summary
   - Track validation history and trends

5. **Provide actionable summary**
   - Summarize validation results with clear pass/fail status
   - Highlight critical issues that need attention
   - Recommend next actions based on validation outcomes

## Output Format

**🔍 VALIDATION RESULTS**

**Validation Configuration**:
- Source: [validation_commands from current_plan.md]
- Commands: [List of validation commands to execute]
- Timestamp: [Current validation execution time]

**Execution Results**:

**1. Comprehensive Tests**
- Command: `python tests/run_comprehensive_tests.py`
- Status: [PASS/FAIL/ERROR]
- Summary: [Key test results and metrics]
- Issues: [Any test failures or critical issues]

**2. Diagnostic Tests**
- Command: `python tests/diagnostic/run_all_diagnostics.py`
- Status: [PASS/FAIL/ERROR]
- Summary: [Diagnostic test results and scores]
- Issues: [Any diagnostic failures or warnings]

**3. Architecture Compliance**
- Command: `python tests/integration_validation/validate_architecture_compliance.py`
- Status: [PASS/FAIL/ERROR]
- Summary: [Architecture compliance results]
- Issues: [Any compliance violations or concerns]

**4. Epic 2 Validation**
- Command: `python final_epic2_proof.py`
- Status: [PASS/FAIL/ERROR]
- Summary: [Epic 2 vs basic component differentiation proof]
- Issues: [Any Epic 2 feature validation failures]

**Overall Validation Status**: [PASS/FAIL/MIXED based on all results]

**Critical Issues**:
- [List any critical failures or blocking issues]
- [Prioritize by severity and impact]
- [Provide specific error messages and context]

**Performance Metrics**:
- [Key performance indicators from validation]
- [Benchmark results and compliance with targets]
- [Any performance regressions or improvements]

**Quality Scores**:
- Portfolio Score: [If available from diagnostic tests]
- Architecture Compliance: [Percentage from compliance tests]
- Test Coverage: [If available from comprehensive tests]

**Recommendations**:
- [Immediate actions needed to address failures]
- [Priority order for resolving issues]
- [Next steps based on validation outcomes]

**Validation complete. Results recorded in validation-results.md.**