# Create Next Session Prompt

**v2.0 Session Continuity**: Generate ready-to-use prompt for next session based on verified reality.

## Instructions

**v2.0 Reality-Based Handoff**: Create self-contained session continuation based on actual verified state, not aspirational progress.

### Core Workflow

1. **Analyze current verified state**
   - Read .claude/current_plan.md for reality-verified progress and current task
   - Check .claude/sessions/recent-work.md for git-verified accomplishments
   - Review .claude/sessions/validation-results.md for latest test-verified status
   - Note any git status or uncommitted changes

2. **Identify next logical steps**
   - Determine concrete next actions based on actual state
   - Prioritize based on test results and blockers
   - Ensure next steps are specific and actionable

3. **Create handoff document**
   - Use .claude/session-templates/SESSION_HANDOFF.md format as template
   - Fill in session accomplishments, current state, and next steps
   - Include validation results and quality metrics

4. **Generate next session prompt**
   - Create ready-to-use prompt for next session startup
   - Include context loading instructions and task focus
   - Specify validation commands and success criteria

5. **Save handoff documentation**
   - Save handoff document to .claude/sessions/handoff-[YYYY-MM-DD-HHMMSS].md
   - Update .claude/sessions/recent-work.md with handoff summary
   - Ensure handoff is accessible for next session

## Output Format

**🤝 SESSION HANDOFF CREATED**

**Current Session Summary**:
- Session Focus: [Primary objectives and activities from current session]
- Accomplishments: [Key achievements and progress made]
- Progress: [Before → After progress percentage]
- Status: [Overall session success and outcomes]

**Current Project State**:
- Task: [current_task from current_plan.md]
- Phase: [current_phase from current_plan.md]
- Progress: [progress]% complete
- Next Milestone: [next_milestone from current_plan.md]
- Blockers: [Any current blockers from current_plan.md]

**Validation Status**:
- Last Validation: [Timestamp of most recent validation]
- Test Results: [Summary of test outcomes]
- Compliance: [Architecture and quality compliance status]
- Issues: [Any critical issues requiring attention]

**Next Session Preparation**:
- **Next Task**: [Specific next action for next session]
- **Priority**: [HIGH/MEDIUM/LOW based on project needs]
- **Context Needed**: [context_requirements for next session]
- **Role Recommendation**: [architect/implementer/optimizer/validator]
- **Validation Commands**: [Commands to run at session start]

## v2.0 Handoff Output Format

```
🤝 CREATING HANDOFF

📄 Created: .claude/sessions/handoff-[YYYY-MM-DD-HHMMSS].md

=== COPY THIS PROMPT FOR NEXT SESSION ===

Continue [current_task] development for RAG Portfolio Project 1.

QUICK START (v2.0):
/status              # Verify reality and auto-update state
/focus [area]        # Load minimal context (<500 tokens)

CURRENT VERIFIED STATE:
- Task: [current_task] ([actual%] complete - test verified)
- Focus: [current_focus_area]
- Blocker: [actual blocker based on test results]
- Last Sync: [timestamp]

NEXT ACTION:
[Specific next step based on verified reality]

VALIDATION:
[Specific test command to run]

===
```

## v2.0 Enhanced Features

### Reality Verification Integration
- **Verified Progress**: Only include test-confirmed accomplishments
- **Actual Blockers**: Based on failing tests, not assumptions
- **Git-Verified Work**: Match handoff to actual commit history
- **Fresh Context**: Use `/focus` for minimal token loading

### Self-Contained Continuity  
- **Minimal Context**: Use `/focus [area]` instead of comprehensive loading
- **Reality Check**: Start with `/status` to verify current state
- **Specific Actions**: Concrete next steps, not general directions
- **Token Management**: Prevent conversation compaction with minimal loading

**Handoff Documentation**:
- Handoff File: `.claude/sessions/handoff-[YYYY-MM-DD-HHMMSS].md`
- Session Summary: Updated in `.claude/sessions/recent-work.md`
- Next Session Prompt: Ready for immediate use

**Session Continuity**:
- ✅ Current state documented
- ✅ Next steps identified
- ✅ Context requirements specified
- ✅ Validation strategy defined
- ✅ Ready-to-use prompt prepared

**Handoff complete. Next session can begin immediately with provided prompt.**