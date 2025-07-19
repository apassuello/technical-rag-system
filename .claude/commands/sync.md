# Deep Reality Reconciliation

**Usage**: `/sync`  

Reconcile all state files with git history and comprehensive test results. Use when state feels "off" or after conversation compaction.

## Instructions

**v2.0 Nuclear Option**: Perform complete reality check by analyzing git history, running comprehensive validation, and fixing ALL state discrepancies.

### Core Workflow

1. **Analyze git history**
   - Check git commits from last 24-48 hours
   - Identify actual work completed vs claimed work
   - Note any uncommitted changes or stashed work

2. **Run comprehensive test suite**
   - Execute all validation commands from .claude/current_plan.md
   - Run comprehensive tests: `python tests/run_comprehensive_tests.py`
   - Run diagnostic tests: `python tests/diagnostic/run_all_diagnostics.py`
   - Capture complete test results and performance metrics

3. **Compare all state claims vs reality**
   - Analyze .claude/current_plan.md claimed progress vs actual test results
   - Check .claude/sessions/recent-work.md vs git commit history
   - Identify .claude/sessions/validation-results.md staleness vs fresh test runs
   - Calculate true completion percentages

4. **Fix ALL discrepancies**
   - Update .claude/current_plan.md progress based on test verification
   - Correct .claude/sessions/recent-work.md with git-verified accomplishments
   - Refresh .claude/sessions/validation-results.md with current test output
   - Update task status and blockers based on failing tests

5. **Show complete reconciliation report**
   - Display all files updated with before/after changes
   - Show git analysis vs state file claims
   - Report test-verified reality vs previous claims
   - Provide corrected project status and next actions

## Output Format

```
🔄 REALITY SYNC - Deep State Reconciliation

Analyzing git history...
✓ Found: [N] commits since last sync
✓ Git changes: [summary of actual work done]
✓ Uncommitted: [any pending changes]

Running comprehensive validation...
$ python tests/run_comprehensive_tests.py
[Show actual test results summary]
$ python tests/diagnostic/run_all_diagnostics.py  
[Show diagnostic results]
$ python final_epic2_proof.py
[Show Epic 2 validation results]

Comparing claimed vs actual state:
❌ State drift: [N] discrepancies found
[List each discrepancy with claimed vs actual]

📝 Fixed: .claude/current_plan.md
   - Progress: [old%] → [actual%] (test-verified)
   - Current task: Updated to match reality
   - Blockers: Updated based on failing tests
   - Last sync: [timestamp]

📝 Fixed: .claude/sessions/recent-work.md
   - Added: [git-verified accomplishments]
   - Removed: [unverified claims]
   - Status: Aligned with actual git history

📝 Fixed: .claude/sessions/validation-results.md
   - Test results: [fresh comprehensive results]
   - Performance: [current benchmarks]
   - Architecture: [current compliance status]

✅ Sync complete: State now matches reality
Current verified status: [accurate project state]
Next action: [reality-based next step]
```

## When to Use Sync

- **After conversation compaction**: Restore accurate context
- **When state feels wrong**: Complete reality check
- **Weekly maintenance**: Prevent drift accumulation  
- **Before major work**: Ensure starting from truth
- **After complex sessions**: Verify all claims

## Recovery Scenarios

### After Conversation Compaction
```bash
/sync  # Complete reality reconciliation
```

### State Feels Inaccurate
```bash
/sync  # Fix all discrepancies at once
```

### Weekly Maintenance
```bash
/sync  # Prevent drift accumulation
```

**Remember**: This is the "nuclear option" for reality verification. It analyzes everything and fixes all state files to match actual git history and test results.