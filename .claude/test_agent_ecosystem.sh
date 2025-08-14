#!/bin/bash

# Agent Ecosystem Test Suite
# This script tests that your Claude Code agents are properly configured and working

echo "========================================="
echo "Claude Code Agent Ecosystem Test Suite"
echo "========================================="
echo ""

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counter
TESTS_PASSED=0
TESTS_FAILED=0

# Function to check if file exists
check_agent_file() {
    agent_name=$1
    file_path=".claude/agents/${agent_name}.md"
    
    if [ -f "$file_path" ]; then
        echo -e "${GREEN}✓${NC} Agent found: ${agent_name}"
        ((TESTS_PASSED++))
        return 0
    else
        echo -e "${RED}✗${NC} Agent missing: ${agent_name}"
        ((TESTS_FAILED++))
        return 1
    fi
}

# Function to validate agent structure
validate_agent_structure() {
    agent_name=$1
    file_path=".claude/agents/${agent_name}.md"
    
    if [ -f "$file_path" ]; then
        # Check for required YAML frontmatter
        if head -1 "$file_path" | grep -q "^---$"; then
            echo -e "${GREEN}✓${NC} Valid structure: ${agent_name}"
            ((TESTS_PASSED++))
            
            # Check for required fields
            if grep -q "^name:" "$file_path" && \
               grep -q "^description:" "$file_path"; then
                echo -e "${GREEN}✓${NC} Required fields present: ${agent_name}"
                ((TESTS_PASSED++))
            else
                echo -e "${YELLOW}⚠${NC} Missing required fields: ${agent_name}"
                ((TESTS_FAILED++))
            fi
        else
            echo -e "${RED}✗${NC} Invalid structure: ${agent_name}"
            ((TESTS_FAILED++))
        fi
    fi
}

# Function to check for proactive triggers
check_proactive_triggers() {
    agent_name=$1
    file_path=".claude/agents/${agent_name}.md"
    
    if [ -f "$file_path" ]; then
        if grep -q "PROACTIVELY\|MUST BE USED" "$file_path"; then
            echo -e "${GREEN}✓${NC} Has proactive triggers: ${agent_name}"
            ((TESTS_PASSED++))
        else
            echo -e "${YELLOW}⚠${NC} No proactive triggers: ${agent_name}"
        fi
    fi
}

echo "1. Checking Core Agents..."
echo "----------------------------"

# List of core agents
CORE_AGENTS=(
    "test-driven-developer"
    "component-implementer"
    "test-runner"
    "software-architect"
    "root-cause-analyzer"
    "system-optimizer"
    "documentation-validator"
    "implementation-validator"
)

for agent in "${CORE_AGENTS[@]}"; do
    check_agent_file "$agent"
done

echo ""
echo "2. Checking Specialist Agents..."
echo "----------------------------"

SPECIALIST_AGENTS=(
    "rag-specialist"
    "security-auditor"
    "documentation-specialist"
    "performance-profiler"
    "code-reviewer"
)

for agent in "${SPECIALIST_AGENTS[@]}"; do
    check_agent_file "$agent"
done

echo ""
echo "3. Validating Agent Structures..."
echo "----------------------------"

ALL_AGENTS=("${CORE_AGENTS[@]}" "${SPECIALIST_AGENTS[@]}")

for agent in "${ALL_AGENTS[@]}"; do
    validate_agent_structure "$agent"
done

echo ""
echo "4. Checking Proactive Triggers..."
echo "----------------------------"

PROACTIVE_AGENTS=(
    "test-runner"
    "root-cause-analyzer"
    "test-driven-developer"
    "documentation-validator"
    "security-auditor"
)

for agent in "${PROACTIVE_AGENTS[@]}"; do
    check_proactive_triggers "$agent"
done

echo ""
echo "5. Checking Documentation..."
echo "----------------------------"

REQUIRED_DOCS=(
    "AGENT_WORKFLOW_DOCUMENTATION.md"
    "AGENT_QUICK_REFERENCE.md"
    "AGENT_ECOSYSTEM_COMPLETE.md"
    "PRACTICAL_AGENT_WORKFLOWS.md"
)

for doc in "${REQUIRED_DOCS[@]}"; do
    if [ -f ".claude/$doc" ]; then
        echo -e "${GREEN}✓${NC} Documentation found: ${doc}"
        ((TESTS_PASSED++))
    else
        echo -e "${RED}✗${NC} Documentation missing: ${doc}"
        ((TESTS_FAILED++))
    fi
done

echo ""
echo "6. Checking Configuration..."
echo "----------------------------"

if [ -f ".claude/settings.json" ]; then
    echo -e "${GREEN}✓${NC} Configuration file found"
    ((TESTS_PASSED++))
    
    # Validate JSON structure
    if python3 -m json.tool ".claude/settings.json" > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} Valid JSON configuration"
        ((TESTS_PASSED++))
    else
        echo -e "${RED}✗${NC} Invalid JSON configuration"
        ((TESTS_FAILED++))
    fi
else
    echo -e "${RED}✗${NC} Configuration file missing"
    ((TESTS_FAILED++))
fi

echo ""
echo "========================================="
echo "Test Results Summary"
echo "========================================="
echo -e "Tests Passed: ${GREEN}${TESTS_PASSED}${NC}"
echo -e "Tests Failed: ${RED}${TESTS_FAILED}${NC}"

if [ $TESTS_FAILED -eq 0 ]; then
    echo ""
    echo -e "${GREEN}🎉 All tests passed! Your agent ecosystem is ready!${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Try a simple command in Claude Code:"
    echo "   'Create a function to calculate text similarity'"
    echo ""
    echo "2. Watch the agents collaborate:"
    echo "   - test-driven-developer will write tests first"
    echo "   - You implement the function"
    echo "   - test-runner validates automatically"
    echo ""
else
    echo ""
    echo -e "${YELLOW}⚠ Some tests failed. Please check the missing components.${NC}"
    echo ""
    echo "To fix:"
    echo "1. Check the error messages above"
    echo "2. Ensure all agent files are in .claude/agents/"
    echo "3. Verify YAML frontmatter in each agent file"
    echo ""
fi

echo "========================================="
echo "Agent Ecosystem Status: $([ $TESTS_FAILED -eq 0 ] && echo "READY" || echo "NEEDS ATTENTION")"
echo "========================================="