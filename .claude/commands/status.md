# Status Check + Auto-Update

**Usage**: `/status [area]`  
**Examples**:
- `/status` - Complete reality check with auto-update
- `/status epic2` - Epic 2 reality verification with state updates
- `/status tests` - Test execution with result updates
- `/status migration` - HuggingFace migration progress verification

## Instructions

**v2.0 Reality-Based Status**: Verify current project reality and update state files to match actual test results and git status.

### Core Workflow

1. **Read current state files**
   - Read .claude/current_plan.md for claimed progress and current task
   - Read .claude/sessions/recent-work.md for recent activity
   - Note last update timestamps

2. **Execute validation to verify reality**
   - Run validation commands from current_plan.md
   - Focus on tests for current task area
   - Capture actual pass/fail results with git status

3. **Compare claimed vs actual state**
   - Check if claimed progress matches test results
   - Identify any discrepancies between claims and reality
   - Calculate actual completion percentage

4. **UPDATE state files to match reality**
   - Update progress in .claude/current_plan.md based on test results
   - Update current task description if needed
   - Update blockers based on failing tests
   - Update .claude/sessions/recent-work.md with actual status

5. **Show explicit changes made**
   - Display each file updated with before/after values
   - Show specific discrepancies found and fixed
   - Provide clear next action based on reality

## Status Check Areas

**Overall System Status**:
- Current validation score and test results
- Architecture compliance status
- Performance metrics and benchmarks
- Component health and operational status

**Area-Specific Status**:
- **Epic 2**: Neural reranking, graph enhancement, analytics status
- **Tests**: Test suite results, coverage, quality metrics
- **Architecture**: Component compliance, boundary integrity
- **Performance**: Benchmarks, optimization status, resource usage

## Output Format

```
🔍 STATUS CHECK - Verifying Project Reality

Reading state files...
✓ .claude/current_plan.md (last updated: [time ago])
✓ .claude/sessions/recent-work.md (last session: [when])

Running validation...
$ [validation command from current_plan.md]
[Show actual test output summary]

Comparing claimed vs actual:
[✓ or ❌] [Comparison of each major claim]

📝 Updated: .claude/current_plan.md
   - Progress: [old%] → [new%] (based on actual tests)
   - Current task: "[updated task description]"
   - Blockers: [updated based on failures]

📝 Updated: .claude/sessions/recent-work.md
   - Status: "[actual current status]"
   - Next: "[specific next action]"

Current State:
- Task: [current task with context]
- Actual Progress: [real%] ([x]/[total] components working)
- Blocker: [most critical blocker]
- Next Action: [specific actionable step]
```

## Validation Commands Integration

Execute validation commands defined in current_plan.md:
- **Comprehensive Tests**: python tests/run_comprehensive_tests.py
- **Diagnostic Tests**: python tests/diagnostic/run_all_diagnostics.py  
- **Epic 2 Validation**: python final_epic2_proof.py
- **Architecture Compliance**: Check modular implementation status
- **Git Status**: Check for uncommitted changes and recent commits

## Example Execution

When user types `/status`, the assistant should:

1. Actually read the current state files
2. Show the validation being run with real commands
3. Update files based on test results
4. Display the updates clearly with before/after values
5. Provide actionable next steps based on reality

**Remember**: This command exists to ensure state files ALWAYS reflect reality, not hopes or partial work.