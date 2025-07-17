# Display and Manage Project Plan

Display current development plan with progress visualization and management options.

## Instructions

1. **Read complete project state**
   - Read @current_plan.md for comprehensive project information
   - Review all project fields including tasks, milestones, and progress

2. **Read session history**
   - Read @sessions/recent-work.md for recent progress updates
   - Review session accomplishments and progress changes

3. **Format plan information**
   - Present project plan in clear, structured format
   - Show progress visualization and milestone tracking
   - Include timeline and completion estimates

4. **Provide plan management options**
   - Allow updates to current task, progress, or milestones
   - Support adding or removing blockers
   - Enable context requirements modification

5. **Display actionable next steps**
   - Show immediate next actions based on current state
   - Highlight any blockers or issues requiring attention
   - Provide clear path forward

## Output Format

**📋 CURRENT DEVELOPMENT PLAN**

**Project Overview**:
- Project: Technical Documentation RAG System (Project 1)
- Status: [epic2_status from current_plan.md]
- Portfolio Score: [portfolio_score from current_plan.md]
- Architecture Compliance: [architecture_compliance from current_plan.md]

**Current Task Details**:
- Task: [current_task from current_plan.md]
- Phase: [current_phase from current_plan.md]
- Progress: [progress]% complete
- Next Milestone: [next_milestone from current_plan.md]
- Estimated Completion: [estimated_completion from current_plan.md]

**Progress Visualization**:
```
Task Progress: [████████░░] [progress]%
Milestone: [next_milestone status]
```

**Context Requirements**:
- [List context_requirements from current_plan.md]
- [Explain relevance to current task]

**Validation Framework**:
- [List validation_commands from current_plan.md]
- [Explain validation strategy and frequency]

**Current Blockers**:
- [List blockers from current_plan.md]
- [Describe impact and resolution approach]

**Key System Components**:
- [List core_components from current_plan.md]
- [Show component status and compliance]

**Configuration Status**:
- [List key_configs from current_plan.md]
- [Show configuration validation status]

**Recent Progress**:
- [Summary from recent-work.md]
- [Key accomplishments and changes]
- [Progress updates and milestone achievements]

**Immediate Next Steps**:
- [Specific actions to advance current task]
- [Recommendations based on current progress]
- [Priority items requiring attention]

**Timeline Summary**:
- Last Updated: [last_updated from current_plan.md]
- Progress Rate: [Calculated based on recent progress]
- Projected Completion: [Based on current velocity]

**Plan Management Options**:
- Update current task or progress
- Modify context requirements
- Add/remove blockers
- Adjust milestones or timelines

**Plan display complete. Ready for plan management or task execution.**