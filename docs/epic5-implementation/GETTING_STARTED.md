# Getting Started with Epic 5 Implementation

**Goal**: Set up environment and make first tool call in 1-2 hours
**Prerequisites**: Read README.md and MASTER_IMPLEMENTATION_PLAN.md

---

## Quick Setup (30 minutes)

### Step 1: Get API Keys (10 minutes)

#### OpenAI API Key
1. Go to https://platform.openai.com/api-keys
2. Sign in or create account
3. Click "Create new secret key"
4. Copy key (starts with `sk-`)
5. Add $10-20 credit to account

#### Anthropic API Key
1. Go to https://console.anthropic.com/settings/keys
2. Sign in or create account
3. Click "Create Key"
4. Copy key (starts with `sk-ant-`)
5. Verify free credits or add payment method

---

### Step 2: Environment Setup (10 minutes)

```bash
# Navigate to project
cd /home/user/rag-portfolio/project-1-technical-rag

# Activate conda environment
conda activate rag-portfolio

# Install Phase 1 dependencies
pip install anthropic>=0.8.0
pip install openai>=1.0.0

# Verify installations
python -c "import anthropic; print(f'Anthropic v{anthropic.__version__}')"
python -c "import openai; print(f'OpenAI v{openai.__version__}')"

# Set API keys
export OPENAI_API_KEY="sk-..."
export ANTHROPIC_API_KEY="sk-ant-..."

# Or create .env file
cat > .env << EOF
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
EOF

# Test API keys
python -c "
import os
import openai
import anthropic

# Test OpenAI
client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
response = client.chat.completions.create(
    model='gpt-3.5-turbo',
    messages=[{'role': 'user', 'content': 'Say hello'}],
    max_tokens=10
)
print(f'✅ OpenAI: {response.choices[0].message.content}')

# Test Anthropic
client = anthropic.Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
response = client.messages.create(
    model='claude-3-haiku-20240307',
    max_tokens=10,
    messages=[{'role': 'user', 'content': 'Say hello'}]
)
print(f'✅ Anthropic: {response.content[0].text}')
"
```

**Expected Output**:
```
Anthropic v0.8.1
OpenAI v1.3.5
✅ OpenAI: Hello!
✅ Anthropic: Hello!
```

---

### Step 3: Create Working Branch (5 minutes)

```bash
# Check current status
cd /home/user/rag-portfolio
git status

# Create Phase 1 branch from claude/add-rag-tools-01EnL4wwgeHH7d1RJq8HAWMm
git checkout -b claude/epic5-phase1-tools-01EnL4wwgeHH7d1RJq8HAWMm

# Verify branch
git branch

# Create directory structure
mkdir -p project-1-technical-rag/src/components/generators/llm_adapters/anthropic_tools
mkdir -p project-1-technical-rag/src/components/generators/llm_adapters/openai_tools
mkdir -p project-1-technical-rag/src/components/query_processors/tools
mkdir -p project-1-technical-rag/tests/epic5/phase1/{unit,integration,scenarios}
```

---

### Step 4: First Tool Call Example (15 minutes)

**Create test script**: `scripts/test_anthropic_tools.py`

```python
"""
Quick test of Anthropic tools API.

This demonstrates the basic pattern you'll implement in Phase 1.
"""

import os
import anthropic

# Initialize client
client = anthropic.Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))

# Define a simple calculator tool
calculator_tool = {
    "name": "calculator",
    "description": "Evaluate mathematical expressions. Supports basic arithmetic.",
    "input_schema": {
        "type": "object",
        "properties": {
            "expression": {
                "type": "string",
                "description": "Mathematical expression to evaluate (e.g., '25 * 47')"
            }
        },
        "required": ["expression"]
    }
}

# Make request with tool
print("🤖 Asking Claude: What is 25 * 47?")
print()

response = client.messages.create(
    model="claude-3-5-sonnet-20241022",
    max_tokens=1024,
    tools=[calculator_tool],
    messages=[
        {"role": "user", "content": "What is 25 * 47? Use the calculator tool."}
    ]
)

print(f"Stop reason: {response.stop_reason}")
print()

# Check if Claude wants to use the tool
if response.stop_reason == "tool_use":
    print("✅ Claude wants to use a tool!")
    print()

    # Extract tool use
    for block in response.content:
        if block.type == "text":
            print(f"Claude's thinking: {block.text}")
        elif block.type == "tool_use":
            print(f"Tool: {block.name}")
            print(f"Input: {block.input}")
            print()

            # Execute tool (mock)
            result = eval(block.input['expression'])  # DON'T DO THIS IN PRODUCTION!
            print(f"Tool result: {result}")
            print()

            # Continue conversation with tool result
            response2 = client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1024,
                tools=[calculator_tool],
                messages=[
                    {"role": "user", "content": "What is 25 * 47? Use the calculator tool."},
                    {"role": "assistant", "content": response.content},
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "tool_result",
                                "tool_use_id": block.id,
                                "content": str(result)
                            }
                        ]
                    }
                ]
            )

            # Get final answer
            for block2 in response2.content:
                if block2.type == "text":
                    print(f"Final answer: {block2.text}")

else:
    print("Claude answered directly without using tools")
    print(response.content[0].text)
```

**Run the test**:
```bash
python scripts/test_anthropic_tools.py
```

**Expected Output**:
```
🤖 Asking Claude: What is 25 * 47?

Stop reason: tool_use

✅ Claude wants to use a tool!

Claude's thinking: I'll use the calculator to compute this.
Tool: calculator
Input: {'expression': '25 * 47'}

Tool result: 1175

Final answer: 25 multiplied by 47 equals 1,175.
```

**🎉 Congratulations!** You just made your first tool call with Claude!

---

## Understanding What You Built

### The Pattern
1. **Define tool schema** - Tell Claude what tools are available
2. **Make request** - Claude decides whether to use a tool
3. **Check stop_reason** - If "tool_use", extract tool calls
4. **Execute tool** - Run the tool with Claude's input
5. **Return result** - Continue conversation with tool result
6. **Get final answer** - Claude synthesizes final response

### This is What Phase 1 Will Build
- **Task 1.1**: Wrap this in a clean `AnthropicAdapter` class
- **Task 1.2**: Do the same for OpenAI function calling
- **Task 1.3**: Create tool registry and real tool implementations
- **Task 1.4**: Integrate everything and test

---

## Quick OpenAI Example (10 minutes)

**Create**: `scripts/test_openai_functions.py`

```python
"""Quick test of OpenAI function calling."""

import os
import json
import openai

client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

# Define calculator function
calculator_function = {
    "type": "function",
    "function": {
        "name": "calculator",
        "description": "Evaluate mathematical expressions",
        "parameters": {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "Math expression to evaluate"
                }
            },
            "required": ["expression"]
        }
    }
}

print("🤖 Asking GPT: What is 25 * 47?")
print()

response = client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[
        {"role": "user", "content": "What is 25 * 47? Use the calculator."}
    ],
    tools=[calculator_function],
    tool_choice="auto"
)

message = response.choices[0].message

if message.tool_calls:
    print("✅ GPT wants to use a function!")
    print()

    for tool_call in message.tool_calls:
        print(f"Function: {tool_call.function.name}")
        args = json.loads(tool_call.function.arguments)
        print(f"Arguments: {args}")
        print()

        # Execute
        result = eval(args['expression'])
        print(f"Result: {result}")
        print()

        # Continue conversation
        response2 = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": "What is 25 * 47? Use the calculator."},
                message,
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": tool_call.function.name,
                    "content": str(result)
                }
            ],
            tools=[calculator_function]
        )

        print(f"Final answer: {response2.choices[0].message.content}")
else:
    print("GPT answered directly")
    print(message.content)
```

**Run**:
```bash
python scripts/test_openai_functions.py
```

---

## What's Different: OpenAI vs Anthropic

| Aspect | OpenAI | Anthropic |
|--------|--------|-----------|
| **API Parameter** | `tools=` | `tools=` |
| **Schema Format** | JSON Schema wrapped in `{"type": "function", "function": {...}}` | Direct JSON Schema |
| **Stop Reason** | `finish_reason` in choices | `stop_reason` in message |
| **Tool Calls** | `message.tool_calls` | Content blocks with `type: "tool_use"` |
| **Results** | Message with `role: "tool"` | Content blocks with `type: "tool_result"` |
| **Parallel Calls** | Yes (multiple tool_calls) | Yes (multiple tool_use blocks) |

**Both are excellent!** Phase 1 implements both so you can use either.

---

## Verify Your Setup

Run this checklist:

```bash
# Checklist script
python << 'EOF'
import os
import sys

checks = {
    "✅ OpenAI key set": bool(os.getenv('OPENAI_API_KEY')),
    "✅ Anthropic key set": bool(os.getenv('ANTHROPIC_API_KEY')),
}

try:
    import anthropic
    checks["✅ Anthropic installed"] = True
except ImportError:
    checks["❌ Anthropic NOT installed"] = False

try:
    import openai
    checks["✅ OpenAI installed"] = True
except ImportError:
    checks["❌ OpenAI NOT installed"] = False

print("Environment Setup Checklist:")
print("-" * 40)
for check, passed in checks.items():
    print(check if passed else check.replace("✅", "❌").replace("NOT", ""))

all_passed = all(checks.values())
print("-" * 40)
print(f"{'✅ All checks passed!' if all_passed else '❌ Some checks failed'}")
print()

if not all_passed:
    print("Fix issues above before continuing.")
    sys.exit(1)
else:
    print("🚀 Ready to start Phase 1!")
EOF
```

---

## Next Steps

### Immediate (Today)
1. ✅ Complete this setup guide
2. ✅ Run both example scripts successfully
3. ✅ Understand the tool calling pattern
4. ⏳ Read `phase1/PHASE1_DETAILED_GUIDE.md`
5. ⏳ Start Task 1.1: Anthropic Adapter

### This Week
- Complete Phase 1 (Tasks 1.1-1.4)
- Create Phase 1 demo
- Update portfolio documentation

### Next Week
- Start Phase 2
- Complete agent orchestration
- Create comprehensive demo

---

## Troubleshooting

### "Import Error: No module named anthropic"
```bash
pip install anthropic>=0.8.0
```

### "Invalid API key"
```bash
# Check key is set
echo $ANTHROPIC_API_KEY
echo $OPENAI_API_KEY

# Re-export if needed
export ANTHROPIC_API_KEY="sk-ant-..."
export OPENAI_API_KEY="sk-..."
```

### "Rate limit exceeded"
- Wait 60 seconds and retry
- You're testing too fast
- Check account has credits

### "Tool not executing"
- Verify tool schema is correct
- Check `stop_reason` or `finish_reason`
- Ensure tool result format is correct

---

## Resources

### Documentation
- [OpenAI Function Calling Guide](https://platform.openai.com/docs/guides/function-calling)
- [Anthropic Tools API](https://docs.anthropic.com/claude/docs/tool-use)
- [LangChain Documentation](https://python.langchain.com/docs/get_started/introduction)

### Examples
- `scripts/test_anthropic_tools.py` - Claude tools example
- `scripts/test_openai_functions.py` - OpenAI functions example
- More examples coming in Phase 1!

---

**✅ Setup Complete? → Go to `phase1/PHASE1_DETAILED_GUIDE.md`**
