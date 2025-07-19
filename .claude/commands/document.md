# Record Verified Session Work

**v2.0 Reality Verification**: Create accurate record of what was actually accomplished based on git analysis and test verification.

## Instructions

**v2.0 Reality-Based Documentation**: Only document work verified by passing tests and git commits - no recording of attempted or partially completed work.

### Core Workflow

1. **Analyze git diff to verify actual work**
   - Run `git diff` and `git log` to see exactly what changed
   - Compare file modifications against claimed accomplishments
   - Identify actual code changes, not just attempts

2. **Run tests to verify claims**
   - Execute validation commands from current_plan.md
   - Only record accomplishments if tests actually pass
   - Document test-verified functionality, not "should work" claims

3. **Update progress tracking based on verification**
   - Calculate real completion percentage from test results
   - Update current_plan.md only with verified progress
   - Record actual blockers from failing tests

4. **Create structured session documentation**
   - Document session accomplishments using existing session template patterns
   - Record progress changes, decisions made, and issues encountered
   - Create comprehensive session record for future reference

5. **Update project progress**
   - Update .claude/current_plan.md with progress changes if applicable
   - Record any new blockers or resolved issues
   - Update last_updated timestamp

6. **Save session record**
   - Save session documentation to .claude/sessions/session-[YYYY-MM-DD-HHMMSS].md
   - Update .claude/sessions/recent-work.md with session summary
   - Ensure session is properly tracked for continuity

## Output Format

**📝 SESSION DOCUMENTED**

**Session Overview**:
- Session Date: [Current date and time]
- Duration: [Estimated session duration]
- Focus: [Primary objectives and activities]
- Status: [COMPLETED/IN_PROGRESS based on session state]

**Git-Verified Work**:
- **Files Changed**: [Actual git diff results]
- **Commits Made**: [git log --oneline results]
- **Code Added/Modified**: [Specific function/class changes]
- **Tests Updated**: [Test file modifications]

**Test-Verified Accomplishments**:
- **Tests Passing**: [Only features with passing tests]
- **Functionality Verified**: [What actually works according to tests]
- **Progress**: [Before → After based on test results]
- **Blockers**: [What's actually broken according to test failures]

**Key Accomplishments**:
- [List major achievements and implementations]
- [Significant decisions made and their rationale]
- [Problems solved and approaches used]
- [Quality improvements and compliance gains]

**Validation Results**:
- **Current State**: [Results from validation commands]
- **Quality Metrics**: [Test results, compliance scores, performance]
- **Issues Identified**: [Any failures or concerns from validation]
- **Compliance Status**: [Architecture and Swiss engineering compliance]

**Technical Decisions**:
- [Important technical decisions made during session]
- [Architecture choices and their justification]
- [Implementation approach decisions]
- [Trade-offs considered and rationale]

**Issues Encountered**:
- [Problems faced during session]
- [Resolution approaches taken]
- [Lessons learned and knowledge gained]
- [Any unresolved issues or blockers]

**Next Steps**:
- [Immediate next actions based on session outcomes]
- [Recommended focus areas for next session]
- [Context requirements for continuing work]

**Session Impact**:
- [Overall significance of session work]
- [Contribution to project milestones]
- [Quality and compliance improvements]

## v2.0 Enhanced Documentation Features

### Reality Verification Rules
- **No aspirational claims**: Only document what tests confirm works
- **Git-verified changes**: Match documentation to actual commits  
- **Test-verified functionality**: Features must pass tests to be recorded
- **Actual blockers**: Based on failing tests, not assumptions

### State Updates
```
📝 Updated: .claude/current_plan.md
   - Progress: [old%] → [new%] (test-verified)
   - Status: [verified current status]
   - Blockers: [actual test failures]

📝 Updated: .claude/sessions/recent-work.md  
   - Added: [git-verified work]
   - Status: [test-confirmed functionality]
```

**Files Updated**:
- Session Record: `.claude/sessions/session-[YYYY-MM-DD-HHMMSS].md`
- Recent Work: `.claude/sessions/recent-work.md` (reality-verified)
- Project Plan: `.claude/current_plan.md` (test-verified progress only)

**Remember**: Only record work that has passing tests. Attempted work without test verification should not be documented as accomplishments.