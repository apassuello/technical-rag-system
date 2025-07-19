# Critical Analysis Mode

**Usage**: `/debug`

Activate extreme skepticism for systematic debugging of difficult problems.

## Instructions

**v2.0 Systematic Skepticism**: Challenge all assumptions and enable methodical investigation for complex problems where normal development approaches fail.

### Core Debug Philosophy

**"Test passed" messages are lies until proven otherwise**

1. **Activate extreme skepticism**
   - Question EVERYTHING that seems to work
   - Verify character by character
   - Check for silent failures and edge cases
   - Assume error messages are misleading

2. **Load minimal debug context**
   - Current failing system (specific function/component)
   - Exact error symptoms and reproduction steps
   - Related test cases and their current status
   - Recent changes that might be related

3. **Apply systematic investigation**
   - Isolate the problem to smallest possible scope
   - Add extensive logging and print statements
   - Run components in isolation
   - Verify all assumptions with actual tests

4. **Update debug tracking**
   - Record investigation findings in sessions/debug-log.md
   - Track what was tested and ruled out
   - Document actual root causes when found

## Debug Reflexes to Activate

### Mental Model Shifts
- **"It's working" → "Prove it's working"**
- **"Tests pass" → "Show me the exact output"**
- **"Should work" → "Make it fail first, then fix"**
- **"Simple fix" → "What else could break?"**

### Systematic Investigation Steps
1. **Reproduce the issue in isolation**
2. **Add logging everywhere relevant**
3. **Test edge cases and boundary conditions**
4. **Verify all dependencies and configurations**
5. **Check for race conditions and timing issues**
6. **Validate all assumptions with print statements**

## Output Format

```
🔍 DEBUG MODE ACTIVATED - Trust Nothing

⚠️ Debug Reflexes Active:
✓ Question EVERYTHING
✓ Verify character by character  
✓ Check for silent failures
✓ Assume errors are misleading

Loading debug context...
📄 Loaded ([X] tokens):
   1. Problem: "[specific issue description]"
   2. [failing_component] (lines X-Y)
   3. [test_file]::test_method (current status)
   4. Recent changes: [git log --oneline -5]

📝 Updated: sessions/debug-log.md
   - Investigation started: "[timestamp]"
   - Problem scope: "[specific component/function]"
   - Hypothesis: "[initial theory]"

Systematic Investigation Plan:
1. [Specific step to isolate problem]
2. [Logging/print statements to add]
3. [Edge case to test]
4. [Assumption to verify]

🎯 First Debug Action: [Concrete next step]

Remember: Nothing works until you prove it works.
```

## Debug Investigation Strategies

### For Failing Tests
```
1. Run test in isolation with maximum verbosity
2. Add print statements before/after each assertion
3. Check test data and mock configurations
4. Verify test environment matches expectations
5. Compare with working similar tests
```

### For Silent Failures
```
1. Add logging to every function entry/exit
2. Check return values at every step
3. Verify error handling actually triggers
4. Test with invalid inputs to ensure failure
5. Check for swallowed exceptions
```

### For Configuration Issues
```
1. Print actual config values being used
2. Verify file paths exist and are readable
3. Check environment variables and defaults
4. Test with minimal configuration first
5. Compare working vs broken config files
```

### For Integration Problems
```
1. Test each component in isolation
2. Verify interface contracts are met
3. Check data types and formats at boundaries
4. Test with mock components
5. Validate timing and order of operations
```

## When to Use Debug Mode

- **Tests pass but system doesn't work**
- **Intermittent failures that are hard to reproduce**
- **Complex integration issues across components**
- **Performance problems with unclear causes**
- **Configuration issues that "should work"**
- **After making changes that break seemingly unrelated things**

## Debug Session Documentation

All debug findings get recorded in `sessions/debug-log.md`:

```markdown
# Debug Session: [Timestamp]

## Problem
[Exact description of what's broken]

## Investigation
[What was tested, what was ruled out]

## Root Cause
[Actual cause when found]

## Solution
[How it was fixed]

## Prevention
[How to avoid this in future]
```

**Remember**: The goal is not to fix quickly, but to understand completely. Rushing leads to more bugs.