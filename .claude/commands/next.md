# Determine Next Logical Development Task

Determine the next logical development task based on current project state and progress.

## Instructions

1. **Read current project state**
   - Read .claude/current_plan.md for current task, progress, and milestone information
   - Review current_task completion status and progress percentage

2. **Read recent session activity**
   - Read .claude/sessions/recent-work.md for recent development activity
   - Understand what work has been completed recently

3. **Execute validation commands**
   - Run validation commands from current_plan.md to check current system state
   - Assess completion status of current task based on validation results

4. **Analyze task progression**
   - Determine if current task is complete or needs additional work
   - Identify logical next task based on project milestones and dependencies

5. **Update project plan if transitioning**
   - If current task is complete, update .claude/current_plan.md with next task
   - Update progress, current_phase, and next_milestone as appropriate
   - Specify new context_requirements for next task

## Output Format

**🎯 NEXT TASK ANALYSIS**

**Current Task Assessment**:
- Task: [current_task from current_plan.md]
- Progress: [progress]% complete
- Current Phase: [current_phase from current_plan.md]
- Status: [COMPLETE/IN_PROGRESS/BLOCKED based on validation]

**Validation Results**:
- [Key validation outcomes that inform task completion]
- [Any issues or blockers identified]
- [Quality metrics and compliance status]

**Task Completion Analysis**:
- [Detailed assessment of current task completion]
- [What criteria determine task completion]
- [Any remaining work or issues to address]

**Next Milestone**: [next_milestone from current_plan.md]

**Recommended Next Task**:
- Task Name: [specific next task description]
- Objective: [clear goal and success criteria]
- Priority: [HIGH/MEDIUM/LOW based on project needs]
- Dependencies: [any prerequisites or dependencies]

**Context Requirements for Next Task**:
- [List of context_requirements needed for next task]
- [Specific templates, knowledge areas, or focus areas]
- [Role recommendations (architect/implementer/optimizer/validator)]

**Estimated Completion**: [time estimate for next task]

**Transition Plan**:
- [If transitioning, describe steps to move to next task]
- [Any cleanup or handoff work needed]
- [Context switching requirements]

**Blockers**: [any blockers preventing next task execution]

**Ready to proceed with next task or continue current work based on analysis.**