# Create Git Backup Checkpoint

Create a git backup checkpoint with descriptive naming and recovery instructions.

## Instructions

1. **Read current project state**
   - Read @current_plan.md for current task context and progress
   - Review current_task and progress for backup naming

2. **Create backup branch**
   - Generate descriptive branch name using format: `backup-[current_task]-[timestamp]`
   - Create backup branch from current state
   - Ensure branch name is unique and descriptive

3. **Commit current state**
   - Stage all current changes including work in progress
   - Create commit with meaningful message describing current state
   - Include progress percentage and task context in commit message

4. **Provide recovery instructions**
   - Generate clear recovery commands for restoring backup
   - Include both branch checkout and commit recovery options
   - Provide verification steps to confirm backup success

5. **Update session tracking**
   - Update @sessions/recent-work.md with backup information
   - Record backup timestamp, branch name, and recovery commands
   - Track backup history for session management

## Output Format

**💾 BACKUP CHECKPOINT CREATED**

**Backup Details**:
- Branch Name: `backup-[current_task]-[YYYY-MM-DD-HHMMSS]`
- Timestamp: [Current backup creation time]
- Current Task: [current_task from current_plan.md]
- Progress: [progress]% at backup time
- Phase: [current_phase from current_plan.md]

**Git Operations Executed**:
```bash
git checkout -b backup-[current_task]-[timestamp]
git add .
git commit -m "Backup: [current_task] - [progress]% complete - [timestamp]"
git checkout [original_branch]
```

**Backup Contents**:
- All current work in progress
- Configuration files and project state
- Session tracking and validation results
- Context management system files

**Recovery Instructions**:

**To restore complete backup**:
```bash
git checkout backup-[current_task]-[timestamp]
```

**To restore specific files**:
```bash
git checkout backup-[current_task]-[timestamp] -- [specific_file_path]
```

**To view backup contents**:
```bash
git show backup-[current_task]-[timestamp] --stat
```

**Verification Steps**:
1. Verify backup branch exists: `git branch | grep backup-[current_task]`
2. Check commit message: `git log --oneline -1 backup-[current_task]-[timestamp]`
3. Confirm all files backed up: `git diff backup-[current_task]-[timestamp]`

**Backup Safety**:
- ✅ All work in progress preserved
- ✅ Configuration state captured
- ✅ Session context maintained
- ✅ Recovery instructions provided
- ✅ Session tracking updated

**Next Steps**:
- Continue current work with backup safety net
- Use recovery commands if needed
- Create additional backups at key milestones

**Backup created successfully. Continue development with confidence.**