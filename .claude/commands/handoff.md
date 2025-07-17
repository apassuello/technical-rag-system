# Create Session Handoff

Create comprehensive session handoff with next session preparation and ready-to-use prompt.

## Instructions

1. **Read session documentation**
   - Read latest session documentation from @sessions/
   - Review @sessions/recent-work.md for current session summary
   - Understand session accomplishments and current state

2. **Analyze current project state**
   - Read @current_plan.md for current task, progress, and next steps
   - Determine next logical work based on session outcomes
   - Identify context requirements for next session

3. **Create handoff document**
   - Use @session-templates/SESSION_HANDOFF.md format as template
   - Fill in session accomplishments, current state, and next steps
   - Include validation results and quality metrics

4. **Generate next session prompt**
   - Create ready-to-use prompt for next session startup
   - Include context loading instructions and task focus
   - Specify validation commands and success criteria

5. **Save handoff documentation**
   - Save handoff document to @sessions/handoff-[YYYY-MM-DD-HHMMSS].md
   - Update @sessions/recent-work.md with handoff summary
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

**Ready-to-Use Next Session Prompt**:
```
Continue [current_task] development for RAG Portfolio Project 1.

CONTEXT SETUP:
1. Run /context to load current project context
2. Run /status to validate current system state
3. Run /[role] to switch to appropriate development mode

CURRENT STATE:
- Task: [current_task] ([progress]% complete)
- Phase: [current_phase]
- Next Milestone: [next_milestone]
- Focus: [next session focus area]

IMMEDIATE OBJECTIVES:
- [Specific next actions for next session]
- [Success criteria and validation requirements]
- [Context requirements and role recommendations]

VALIDATION:
- [Key validation commands to run]
- [Expected outcomes and success criteria]
- [Quality gates and compliance checks]

Please start by running /context and /status to understand current state, then proceed with the planned work.
```

**Handoff Documentation**:
- Handoff File: `sessions/handoff-[YYYY-MM-DD-HHMMSS].md`
- Session Summary: Updated in `sessions/recent-work.md`
- Next Session Prompt: Ready for immediate use

**Session Continuity**:
- ✅ Current state documented
- ✅ Next steps identified
- ✅ Context requirements specified
- ✅ Validation strategy defined
- ✅ Ready-to-use prompt prepared

**Handoff complete. Next session can begin immediately with provided prompt.**