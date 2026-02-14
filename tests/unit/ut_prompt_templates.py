"""
Unit tests for shared_utils.generation.prompt_templates module.

Tests cover:
- QueryType enum values
- detect_query_type() keyword matching for all query types
- All template getter methods return valid PromptTemplate instances
- get_template_for_query() routing
- format_prompt_with_template() with/without few-shot, with explicit template
- get_base_system_prompt() content
- Edge cases: empty query, ambiguous queries, case insensitivity
"""

import pytest

from shared_utils.generation.prompt_templates import (
    PromptTemplate,
    QueryType,
    TechnicalPromptTemplates,
)


# ---------------------------------------------------------------------------
# QueryType enum
# ---------------------------------------------------------------------------

class TestQueryType:
    """Verify QueryType enum has all expected members and values."""

    def test_all_members_present(self):
        expected = {
            "DEFINITION", "IMPLEMENTATION", "COMPARISON", "TROUBLESHOOTING",
            "SPECIFICATION", "CODE_EXAMPLE", "HARDWARE_CONSTRAINT", "GENERAL",
        }
        assert set(QueryType.__members__.keys()) == expected

    @pytest.mark.parametrize("member,value", [
        ("DEFINITION", "definition"),
        ("IMPLEMENTATION", "implementation"),
        ("COMPARISON", "comparison"),
        ("TROUBLESHOOTING", "troubleshooting"),
        ("SPECIFICATION", "specification"),
        ("CODE_EXAMPLE", "code_example"),
        ("HARDWARE_CONSTRAINT", "hardware_constraint"),
        ("GENERAL", "general"),
    ])
    def test_enum_values(self, member, value):
        assert QueryType[member].value == value


# ---------------------------------------------------------------------------
# PromptTemplate dataclass
# ---------------------------------------------------------------------------

class TestPromptTemplate:
    """Verify PromptTemplate dataclass fields and defaults."""

    def test_required_fields(self):
        tpl = PromptTemplate(
            system_prompt="sys",
            context_format="ctx: {context}",
            query_format="q: {query}",
            answer_guidelines="guidelines",
        )
        assert tpl.system_prompt == "sys"
        assert tpl.context_format == "ctx: {context}"
        assert tpl.query_format == "q: {query}"
        assert tpl.answer_guidelines == "guidelines"

    def test_few_shot_defaults_to_none(self):
        tpl = PromptTemplate(
            system_prompt="s",
            context_format="c",
            query_format="q",
            answer_guidelines="a",
        )
        assert tpl.few_shot_examples is None

    def test_few_shot_can_be_set(self):
        examples = ["ex1", "ex2"]
        tpl = PromptTemplate(
            system_prompt="s",
            context_format="c",
            query_format="q",
            answer_guidelines="a",
            few_shot_examples=examples,
        )
        assert tpl.few_shot_examples == examples


# ---------------------------------------------------------------------------
# get_base_system_prompt
# ---------------------------------------------------------------------------

class TestGetBaseSystemPrompt:
    """Verify base system prompt content."""

    def test_returns_string(self):
        result = TechnicalPromptTemplates.get_base_system_prompt()
        assert isinstance(result, str)
        assert len(result) > 0

    def test_contains_key_phrases(self):
        prompt = TechnicalPromptTemplates.get_base_system_prompt()
        assert "embedded systems" in prompt.lower()
        assert "RISC-V" in prompt
        assert "[chunk_X]" in prompt
        assert "technical accuracy" in prompt.lower()


# ---------------------------------------------------------------------------
# detect_query_type
# ---------------------------------------------------------------------------

class TestDetectQueryType:
    """Verify keyword-based query type detection."""

    # --- DEFINITION ---
    @pytest.mark.parametrize("query", [
        "What is RISC-V?",
        "What are the main features of FreeRTOS?",
        "Define interrupt latency",
        "Give me a definition of DMA",
        "What is the meaning of ISR?",
        "Explain what a semaphore is",
    ])
    def test_definition_detection(self, query):
        assert TechnicalPromptTemplates.detect_query_type(query) == QueryType.DEFINITION

    # --- IMPLEMENTATION ---
    @pytest.mark.parametrize("query", [
        "How to configure UART in STM32?",
        "How do I implement a timer interrupt?",
        "Implement a mutex wrapper for shared resources",
        "How to setup FreeRTOS on an ARM Cortex-M4",
        "Configure the SPI peripheral",
        "Install the RISC-V toolchain",
    ])
    def test_implementation_detection(self, query):
        assert TechnicalPromptTemplates.detect_query_type(query) == QueryType.IMPLEMENTATION

    # --- COMPARISON ---
    @pytest.mark.parametrize("query", [
        "What's the difference between FreeRTOS and Zephyr?",
        "Compare ARM and RISC-V architectures",
        "FreeRTOS vs Zephyr for IoT",
        "ARM versus RISC-V for edge ML",
        "Is Rust better than C for embedded?",
        "Which is more suitable for real-time?",
    ])
    def test_comparison_detection(self, query):
        assert TechnicalPromptTemplates.detect_query_type(query) == QueryType.COMPARISON

    # --- SPECIFICATION ---
    @pytest.mark.parametrize("query", [
        "Give the specification details for STM32F4",
        "Show me the specs of the nRF52840",
        "List the parameters this peripheral supports",
        "Tell me the limits of the ADC",
        "The range of the PWM timer is needed",
        "Maximum clock frequency supported?",
        "Minimum voltage for stable operation?",
    ])
    def test_specification_detection(self, query):
        assert TechnicalPromptTemplates.detect_query_type(query) == QueryType.SPECIFICATION

    # --- CODE_EXAMPLE ---
    @pytest.mark.parametrize("query", [
        "Show me an example of GPIO configuration",
        "Give me a code snippet for SPI transfer",
        "Provide a code sample for I2C read",
        "Any demo of task creation in FreeRTOS?",
        "Show me the peripheral usage pattern",
    ])
    def test_code_example_detection(self, query):
        assert TechnicalPromptTemplates.detect_query_type(query) == QueryType.CODE_EXAMPLE

    # --- HARDWARE_CONSTRAINT ---
    @pytest.mark.parametrize("query", [
        "Need to check memory requirements for this model",
        "Will it fit in 256KB RAM?",
        "Flash requirements for the firmware",
        "Can I run this on an MCU?",
        "Constraint analysis for running on Cortex-M0",
        "Will this fit on a low-power device?",
        "Can it run on a small processor?",
        "Estimate the power consumption of this approach",
    ])
    def test_hardware_constraint_detection(self, query):
        assert TechnicalPromptTemplates.detect_query_type(query) == QueryType.HARDWARE_CONSTRAINT

    # --- TROUBLESHOOTING ---
    @pytest.mark.parametrize("query", [
        "I'm getting an error with the linker",
        "There's a problem with my interrupt handler",
        "UART communication issue on STM32",
        "Need to debug a hardfault",
        "Steps to troubleshoot boot failures",
        "I need to fix a stack overflow in FreeRTOS",
        "Need to solve a segfault in the ISR",
        "Timer is not working correctly",
    ])
    def test_troubleshooting_detection(self, query):
        assert TechnicalPromptTemplates.detect_query_type(query) == QueryType.TROUBLESHOOTING

    # --- GENERAL (fallback) ---
    @pytest.mark.parametrize("query", [
        "Tell me about embedded development",
        "Discuss the future of RISC-V",
        "Thoughts on open-source hardware?",
        "",
    ])
    def test_general_fallback(self, query):
        assert TechnicalPromptTemplates.detect_query_type(query) == QueryType.GENERAL

    def test_case_insensitivity(self):
        """Keywords should match regardless of case."""
        assert TechnicalPromptTemplates.detect_query_type("WHAT IS DMA?") == QueryType.DEFINITION
        assert TechnicalPromptTemplates.detect_query_type("HOW TO SETUP UART") == QueryType.IMPLEMENTATION
        assert TechnicalPromptTemplates.detect_query_type("COMPARE x and y") == QueryType.COMPARISON

    def test_priority_ordering(self):
        """When multiple keywords match, the first check in order wins."""
        # "What is" (DEFINITION) beats "error" (TROUBLESHOOTING)
        assert TechnicalPromptTemplates.detect_query_type(
            "What is the most common error in FreeRTOS?"
        ) == QueryType.DEFINITION
        # "How to" (IMPLEMENTATION) beats "example" (CODE_EXAMPLE)
        assert TechnicalPromptTemplates.detect_query_type(
            "How to write an example driver?"
        ) == QueryType.IMPLEMENTATION


# ---------------------------------------------------------------------------
# Template getter methods
# ---------------------------------------------------------------------------

class TestTemplateGetters:
    """Verify each template getter returns a well-formed PromptTemplate."""

    GETTER_METHODS = [
        "get_definition_template",
        "get_implementation_template",
        "get_comparison_template",
        "get_specification_template",
        "get_code_example_template",
        "get_hardware_constraint_template",
        "get_troubleshooting_template",
        "get_general_template",
    ]

    @pytest.mark.parametrize("method_name", GETTER_METHODS)
    def test_returns_prompt_template(self, method_name):
        method = getattr(TechnicalPromptTemplates, method_name)
        result = method()
        assert isinstance(result, PromptTemplate)

    @pytest.mark.parametrize("method_name", GETTER_METHODS)
    def test_non_empty_fields(self, method_name):
        tpl = getattr(TechnicalPromptTemplates, method_name)()
        assert len(tpl.system_prompt) > 0
        assert len(tpl.context_format) > 0
        assert len(tpl.query_format) > 0
        assert len(tpl.answer_guidelines) > 0

    @pytest.mark.parametrize("method_name", GETTER_METHODS)
    def test_context_format_has_placeholder(self, method_name):
        tpl = getattr(TechnicalPromptTemplates, method_name)()
        assert "{context}" in tpl.context_format

    @pytest.mark.parametrize("method_name", GETTER_METHODS)
    def test_query_format_has_placeholder(self, method_name):
        tpl = getattr(TechnicalPromptTemplates, method_name)()
        assert "{query}" in tpl.query_format

    @pytest.mark.parametrize("method_name", GETTER_METHODS)
    def test_system_prompt_contains_base(self, method_name):
        """Every template's system_prompt should start with the base prompt."""
        tpl = getattr(TechnicalPromptTemplates, method_name)()
        base = TechnicalPromptTemplates.get_base_system_prompt()
        assert tpl.system_prompt.startswith(base)

    def test_definition_has_few_shot(self):
        tpl = TechnicalPromptTemplates.get_definition_template()
        assert tpl.few_shot_examples is not None
        assert len(tpl.few_shot_examples) == 2

    def test_implementation_has_few_shot(self):
        tpl = TechnicalPromptTemplates.get_implementation_template()
        assert tpl.few_shot_examples is not None
        assert len(tpl.few_shot_examples) == 2

    def test_comparison_no_few_shot(self):
        tpl = TechnicalPromptTemplates.get_comparison_template()
        assert tpl.few_shot_examples is None

    def test_general_no_few_shot(self):
        tpl = TechnicalPromptTemplates.get_general_template()
        assert tpl.few_shot_examples is None


# ---------------------------------------------------------------------------
# get_template_for_query
# ---------------------------------------------------------------------------

class TestGetTemplateForQuery:
    """Verify routing from query string to correct template."""

    @pytest.mark.parametrize("query,expected_type", [
        ("What is a mutex?", QueryType.DEFINITION),
        ("How to configure DMA?", QueryType.IMPLEMENTATION),
        ("Compare SPI vs I2C", QueryType.COMPARISON),
        ("Give me the specs of STM32", QueryType.SPECIFICATION),
        ("Show me an example of UART init", QueryType.CODE_EXAMPLE),
        ("Will this fit in 64KB RAM?", QueryType.HARDWARE_CONSTRAINT),
        ("I have a problem with my ISR", QueryType.TROUBLESHOOTING),
        ("Tell me about embedded systems", QueryType.GENERAL),
    ])
    def test_routing_matches_detect(self, query, expected_type):
        """get_template_for_query should route to the same type as detect_query_type."""
        detected = TechnicalPromptTemplates.detect_query_type(query)
        assert detected == expected_type
        # And the template should be returned without error
        tpl = TechnicalPromptTemplates.get_template_for_query(query)
        assert isinstance(tpl, PromptTemplate)

    def test_definition_template_content(self):
        """Routing a definition query should return the definition template."""
        tpl = TechnicalPromptTemplates.get_template_for_query("What is RISC-V?")
        expected = TechnicalPromptTemplates.get_definition_template()
        assert tpl.system_prompt == expected.system_prompt
        assert tpl.context_format == expected.context_format
        assert tpl.query_format == expected.query_format

    def test_general_template_for_empty_query(self):
        tpl = TechnicalPromptTemplates.get_template_for_query("")
        expected = TechnicalPromptTemplates.get_general_template()
        assert tpl.system_prompt == expected.system_prompt


# ---------------------------------------------------------------------------
# format_prompt_with_template
# ---------------------------------------------------------------------------

class TestFormatPromptWithTemplate:
    """Verify prompt formatting logic."""

    SAMPLE_QUERY = "What is DMA?"
    SAMPLE_CONTEXT = "DMA stands for Direct Memory Access [chunk_1]."

    def test_returns_dict_with_system_and_user(self):
        result = TechnicalPromptTemplates.format_prompt_with_template(
            query=self.SAMPLE_QUERY,
            context=self.SAMPLE_CONTEXT,
        )
        assert isinstance(result, dict)
        assert "system" in result
        assert "user" in result

    def test_auto_detects_template(self):
        """Without explicit template, should auto-detect from query."""
        result = TechnicalPromptTemplates.format_prompt_with_template(
            query=self.SAMPLE_QUERY,
            context=self.SAMPLE_CONTEXT,
        )
        # "What is" -> DEFINITION template
        expected_tpl = TechnicalPromptTemplates.get_definition_template()
        assert result["system"] == expected_tpl.system_prompt

    def test_context_is_formatted_into_user_prompt(self):
        result = TechnicalPromptTemplates.format_prompt_with_template(
            query=self.SAMPLE_QUERY,
            context=self.SAMPLE_CONTEXT,
        )
        assert self.SAMPLE_CONTEXT in result["user"]

    def test_query_is_formatted_into_user_prompt(self):
        result = TechnicalPromptTemplates.format_prompt_with_template(
            query=self.SAMPLE_QUERY,
            context=self.SAMPLE_CONTEXT,
        )
        assert self.SAMPLE_QUERY in result["user"]

    def test_includes_few_shot_by_default(self):
        """Definition template has few-shot; they should appear in user prompt."""
        result = TechnicalPromptTemplates.format_prompt_with_template(
            query=self.SAMPLE_QUERY,
            context=self.SAMPLE_CONTEXT,
            include_few_shot=True,
        )
        assert "examples of how to answer" in result["user"].lower()
        assert "RISC-V" in result["user"]  # from definition few-shot

    def test_excludes_few_shot_when_disabled(self):
        result = TechnicalPromptTemplates.format_prompt_with_template(
            query=self.SAMPLE_QUERY,
            context=self.SAMPLE_CONTEXT,
            include_few_shot=False,
        )
        assert "examples of how to answer" not in result["user"].lower()

    def test_few_shot_absent_when_template_has_none(self):
        """General template has no few-shot; even with include_few_shot=True, no examples."""
        general_tpl = TechnicalPromptTemplates.get_general_template()
        result = TechnicalPromptTemplates.format_prompt_with_template(
            query="Tell me something",
            context="some context",
            template=general_tpl,
            include_few_shot=True,
        )
        assert "examples of how to answer" not in result["user"].lower()

    def test_explicit_template_overrides_auto(self):
        """Providing a template should bypass auto-detection."""
        # Query would auto-detect as DEFINITION, but we force TROUBLESHOOTING
        troubleshooting_tpl = TechnicalPromptTemplates.get_troubleshooting_template()
        result = TechnicalPromptTemplates.format_prompt_with_template(
            query=self.SAMPLE_QUERY,
            context=self.SAMPLE_CONTEXT,
            template=troubleshooting_tpl,
        )
        assert result["system"] == troubleshooting_tpl.system_prompt
        # The context format should be from troubleshooting, not definition
        assert "Troubleshooting Documentation:" in result["user"]

    def test_answer_guidelines_in_user_prompt(self):
        result = TechnicalPromptTemplates.format_prompt_with_template(
            query=self.SAMPLE_QUERY,
            context=self.SAMPLE_CONTEXT,
        )
        tpl = TechnicalPromptTemplates.get_definition_template()
        assert tpl.answer_guidelines in result["user"]

    def test_empty_context(self):
        """Should handle empty context string without error."""
        result = TechnicalPromptTemplates.format_prompt_with_template(
            query=self.SAMPLE_QUERY,
            context="",
        )
        assert isinstance(result, dict)
        assert "system" in result
        assert "user" in result

    def test_empty_query(self):
        """Should handle empty query string without error."""
        result = TechnicalPromptTemplates.format_prompt_with_template(
            query="",
            context=self.SAMPLE_CONTEXT,
        )
        assert isinstance(result, dict)

    def test_user_prompt_ordering(self):
        """User prompt should have: few-shot (if any), context, query, guidelines in order."""
        result = TechnicalPromptTemplates.format_prompt_with_template(
            query=self.SAMPLE_QUERY,
            context=self.SAMPLE_CONTEXT,
            include_few_shot=True,
        )
        user = result["user"]
        # few-shot intro comes before context
        few_shot_pos = user.index("examples of how to answer")
        context_pos = user.index(self.SAMPLE_CONTEXT)
        query_pos = user.index(self.SAMPLE_QUERY)
        assert few_shot_pos < context_pos < query_pos

    def test_format_with_special_characters_in_context(self):
        """Context with curly braces (other than {context}) should not cause KeyError."""
        # The context_format uses .format(context=...) so only {context} is replaced.
        # If the context itself contains braces, they get inserted as literal text
        # because they are the replacement value, not the format string.
        result = TechnicalPromptTemplates.format_prompt_with_template(
            query=self.SAMPLE_QUERY,
            context="value = {x: 1, y: 2}",
        )
        assert "value = {x: 1, y: 2}" in result["user"]

    def test_all_query_types_produce_valid_output(self):
        """Smoke test: every query type should produce a valid formatted prompt."""
        queries = [
            "What is an ISR?",
            "How to implement a watchdog timer?",
            "Compare RTOS vs bare-metal",
            "What are the specs of Cortex-M7?",
            "Show me code for I2C read",
            "Will this run on 128KB RAM?",
            "My timer is not working",
            "Tell me about embedded AI",
        ]
        for query in queries:
            result = TechnicalPromptTemplates.format_prompt_with_template(
                query=query,
                context="Some technical context [chunk_1].",
            )
            assert isinstance(result, dict)
            assert len(result["system"]) > 0
            assert len(result["user"]) > 0
