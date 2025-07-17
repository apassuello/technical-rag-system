# Post-Compaction Actions

## AUTOMATIC ACTIONS AFTER CONVERSATION COMPACTION

When Claude Code automatically compacts the conversation, follow these steps to restore context and continue work seamlessly:

### **Step 1: Immediate Context Restoration**
```bash
/context [last-work-area]       # Load context for the area you were working on
/status [relevant-area]         # Check current system state
```

### **Step 2: Role and Focus Restoration**
```bash
/[role] [focus-area]           # Restore your working role and focus
```
**Examples:**
- `/implementer epic2-demo` - If you were working on Epic 2 demo implementation
- `/architect component-boundaries` - If you were doing architectural review
- `/validator diagnostic` - If you were running validation tests

### **Step 3: Work Area Validation**
```bash
# Quick validation to ensure system is still operational
python final_epic2_proof.py                    # Verify Epic 2 features working
python tests/diagnostic/run_all_diagnostics.py # Check system health
```

### **Step 4: Session Documentation** (if significant work was done)
```bash
# Document the work completed before compaction
/document                      # Record session accomplishments
/checkpoint                    # Create development checkpoint
```

## **QUICK RESTART TEMPLATES**

### **For Epic 2 Demo Work**
```bash
/context epic2-demo
/implementer streamlit-ui
/status epic2
```

### **For Neural Reranker Development**
```bash
/context neural-reranker
/implementer neural-reranker
/status performance
```

### **For Architecture Review**
```bash
/context component-boundaries
/architect epic2-demo
/status architecture
```

### **For Testing and Validation**
```bash
/context validation
/validator diagnostic
/status tests
```

## **CONTEXT CONTINUITY CHECKLIST**

After compaction, verify:
- [ ] Context loaded for current work area
- [ ] Role and focus restored
- [ ] System health validated
- [ ] Work progress documented (if needed)
- [ ] Ready to continue where you left off

## **EMERGENCY CONTEXT RECOVERY**

If you're unsure what you were working on:

1. **Check current plan**: Look at `current_plan.md` for current task
2. **Check recent work**: Look at `.claude/sessions/recent-work.md` for latest activity
3. **Run full status**: `/status` to see overall system state
4. **Load general context**: `/context` for general project context

## **SESSION HANDOFF INTEGRATION**

For planned session endings (before compaction):
1. **Create handoff**: `/handoff` - Creates ready-to-use restart prompt
2. **Use handoff prompt**: Copy the generated prompt for easy restart

## **COMPACTION-SAFE WORKFLOW**

To minimize context loss during compaction:
1. **Work in focused sessions** - Use specific role/focus combinations
2. **Document frequently** - Use `/document` for significant progress
3. **Create checkpoints** - Use `/checkpoint` at major milestones
4. **Use handoffs** - Use `/handoff` when switching major work areas

**This system ensures seamless continuation after automatic conversation compaction while maintaining full context and work continuity.**