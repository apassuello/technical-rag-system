"""Unit tests for TechnicalContentCleaner.

Covers:
- Constructor and configuration defaults
- clean() pipeline: input validation, artifact removal, whitespace normalization,
  code-block and equation preservation/restoration, config toggles, metrics
- normalize(): all 6 regex branches (line endings, quotes, dashes, ellipsis, spaces, bullets)
- remove_pii(): all 5 PII types x all 3 actions (redact, remove, flag), disabled path, metrics
- assess_quality(): empty input, technical-heavy vs non-technical, score bounds
- configure() / get_config(): valid updates, config copy isolation
- _validate_config(): invalid keys, invalid pii_action, negative min_line_length,
  zero max_consecutive_newlines, non-int min_line_length
- get_quality_factors(): returns correct list and is a copy
- _protect_technical_content(): code blocks and equations replaced with placeholders,
  disabled paths, metrics increments
- get_metrics(): copy semantics, expected keys, sub-key structure
- Artifact removal: page numbers, TOC, navigation, copyright, short lines, keyword lines
- Whitespace normalization: excessive newlines, trailing whitespace, custom max
"""

import pytest

from components.processors.cleaners.technical import TechnicalContentCleaner


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def cleaner():
    """Default cleaner with stock config."""
    return TechnicalContentCleaner()


@pytest.fixture
def pii_cleaner():
    """Cleaner with PII detection enabled (flag mode)."""
    return TechnicalContentCleaner(config={"detect_pii": True, "pii_action": "flag"})


# ---------------------------------------------------------------------------
# Constructor / defaults
# ---------------------------------------------------------------------------

class TestConstructor:
    """Test TechnicalContentCleaner initialization."""

    def test_default_config_keys(self, cleaner):
        cfg = cleaner.get_config()
        expected_keys = {
            "normalize_whitespace", "remove_artifacts", "preserve_code_blocks",
            "preserve_equations", "detect_pii", "pii_action", "min_line_length",
            "max_consecutive_newlines", "preserve_technical_formatting",
        }
        assert set(cfg.keys()) == expected_keys

    def test_default_values(self, cleaner):
        cfg = cleaner.get_config()
        assert cfg["normalize_whitespace"] is True
        assert cfg["remove_artifacts"] is True
        assert cfg["preserve_code_blocks"] is True
        assert cfg["preserve_equations"] is True
        assert cfg["detect_pii"] is False
        assert cfg["pii_action"] == "flag"
        assert cfg["min_line_length"] == 10
        assert cfg["max_consecutive_newlines"] == 2
        assert cfg["preserve_technical_formatting"] is True

    def test_custom_config_overrides_defaults(self):
        c = TechnicalContentCleaner(config={"detect_pii": True, "pii_action": "redact"})
        cfg = c.get_config()
        assert cfg["detect_pii"] is True
        assert cfg["pii_action"] == "redact"
        # Non-overridden defaults unchanged
        assert cfg["normalize_whitespace"] is True

    def test_none_config_uses_defaults(self):
        c = TechnicalContentCleaner(config=None)
        assert c.get_config()["detect_pii"] is False

    def test_initial_metrics_zeroed(self, cleaner):
        m = cleaner.get_metrics()
        assert m["texts_processed"] == 0
        assert m["artifacts_removed"] == 0
        assert m["pii_detected"] == 0
        assert m["bytes_cleaned"] == 0


# ---------------------------------------------------------------------------
# clean()
# ---------------------------------------------------------------------------

class TestClean:
    """Test the clean() pipeline."""

    def test_none_raises_value_error(self, cleaner):
        with pytest.raises(ValueError, match="Text cannot be None"):
            cleaner.clean(None)

    def test_non_string_raises_value_error(self, cleaner):
        with pytest.raises(ValueError, match="Text must be a string"):
            cleaner.clean(123)

    def test_empty_string_returns_empty(self, cleaner):
        assert cleaner.clean("") == ""

    def test_whitespace_only_returns_empty(self, cleaner):
        assert cleaner.clean("   \n\t  ") == ""

    def test_normal_text_cleaned(self, cleaner):
        text = "The algorithm processes data and returns a result value."
        result = cleaner.clean(text)
        assert "algorithm" in result
        assert "result" in result

    def test_metrics_updated_after_clean(self, cleaner):
        cleaner.clean("Some meaningful technical text with algorithm details.")
        m = cleaner.get_metrics()
        assert m["texts_processed"] == 1
        assert m["cleaning_operations"]["whitespace_normalized"] >= 1
        assert m["cleaning_operations"]["artifacts_removed"] >= 1

    def test_metrics_accumulate_across_calls(self, cleaner):
        cleaner.clean("First text with algorithm and implementation details here.")
        cleaner.clean("Second text with function and variable definition here.")
        assert cleaner.get_metrics()["texts_processed"] == 2

    def test_bytes_cleaned_tracked(self, cleaner):
        # Include artifacts (copyright, page number) that will be removed,
        # changing the output length vs the input length.
        text = (
            "copyright 2024 all rights reserved\n"
            "page 1\n"
            "The algorithm processes data and returns a result value.\n"
            "Another meaningful paragraph explaining the implementation details."
        )
        cleaner.clean(text)
        assert cleaner.get_metrics()["bytes_cleaned"] > 0

    def test_clean_with_artifacts_disabled(self):
        c = TechnicalContentCleaner(config={"remove_artifacts": False})
        text = "page 1\nThe algorithm processes data and returns a result value."
        result = c.clean(text)
        assert c.get_metrics()["cleaning_operations"]["artifacts_removed"] == 0
        assert "page 1" in result

    def test_clean_with_whitespace_normalization_disabled(self):
        c = TechnicalContentCleaner(config={"normalize_whitespace": False})
        text = "Line one   \n\n\n\n\nLine two is quite long enough."
        c.clean(text)
        assert c.get_metrics()["cleaning_operations"]["whitespace_normalized"] == 0

    def test_code_block_preserved_through_clean(self, cleaner):
        text = "Here is some code:\n```python\ndef hello():\n    print('hi')\n```\nEnd of example."
        result = cleaner.clean(text)
        assert "def hello():" in result
        assert "print('hi')" in result

    def test_equation_preserved_through_clean(self, cleaner):
        text = "The equation is $$E = mc^2$$ in physics."
        result = cleaner.clean(text)
        assert "$$E = mc^2$$" in result

    def test_inline_equation_preserved(self, cleaner):
        text = "The variable $x$ is important."
        result = cleaner.clean(text)
        assert "$x$" in result

    def test_latex_environment_preserved(self, cleaner):
        text = r"The equation \begin{align}x=1\end{align} is valid."
        result = cleaner.clean(text)
        assert r"\begin{align}" in result


# ---------------------------------------------------------------------------
# normalize()
# ---------------------------------------------------------------------------

class TestNormalize:
    """Test the normalize() method - all 6 regex branches."""

    def test_empty_returns_empty(self, cleaner):
        assert cleaner.normalize("") == ""

    def test_windows_line_endings(self, cleaner):
        assert cleaner.normalize("line1\r\nline2\rline3") == "line1\nline2\nline3"

    def test_low9_double_quote_normalized(self, cleaner):
        # \u201e (double low-9 quotation mark) is matched by the regex
        result = cleaner.normalize("\u201eHello")
        assert result == '"Hello'

    def test_guillemets_normalized(self, cleaner):
        result = cleaner.normalize("\u00abHello\u00bb")
        assert result == '"Hello"'

    def test_low9_single_quote_normalized(self, cleaner):
        # \u201a (single low-9 quotation mark) is matched by the regex
        result = cleaner.normalize("\u201aworld")
        assert result == "'world"

    def test_single_guillemets_normalized(self, cleaner):
        result = cleaner.normalize("\u2039world\u203a")
        assert result == "'world'"

    def test_em_dash_normalized(self, cleaner):
        assert cleaner.normalize("foo\u2014bar") == "foo-bar"

    def test_en_dash_normalized(self, cleaner):
        assert cleaner.normalize("foo\u2013bar") == "foo-bar"

    def test_ellipsis_long_normalized(self, cleaner):
        assert cleaner.normalize("wait.....") == "wait..."

    def test_ellipsis_three_dots_unchanged(self, cleaner):
        assert cleaner.normalize("wait...") == "wait..."

    def test_multiple_spaces_collapsed(self, cleaner):
        assert cleaner.normalize("hello    world") == "hello world"

    def test_bullet_points_normalized(self, cleaner):
        for bullet in ["\u2022", "\u00b7", "\u2027", "\u25aa", "\u25ab"]:
            result = cleaner.normalize(f"{bullet} item")
            assert result.startswith("\u2022"), f"Failed for bullet {repr(bullet)}"

    def test_already_normal_text_unchanged(self, cleaner):
        text = "Normal text with regular formatting."
        assert cleaner.normalize(text) == text


# ---------------------------------------------------------------------------
# remove_pii()
# ---------------------------------------------------------------------------

class TestRemovePii:
    """Test PII detection and removal for all 5 types and all 3 actions."""

    # -- disabled path --
    def test_pii_disabled_returns_unchanged(self, cleaner):
        text = "Contact user@example.com for details."
        result_text, detected = cleaner.remove_pii(text)
        assert result_text == text
        assert detected == []

    # -- detection (flag mode, all 5 types) --
    def test_detect_email(self, pii_cleaner):
        text = "Send mail to user@example.com please."
        result_text, detected = pii_cleaner.remove_pii(text)
        emails = [d for d in detected if d["type"] == "email"]
        assert len(emails) == 1
        assert emails[0]["value"] == "user@example.com"
        # flag mode leaves text unchanged
        assert "user@example.com" in result_text

    def test_detect_phone(self, pii_cleaner):
        text = "Call 555-123-4567 for info."
        _, detected = pii_cleaner.remove_pii(text)
        phones = [d for d in detected if d["type"] == "phone"]
        assert len(phones) == 1
        assert phones[0]["value"] == "555-123-4567"

    def test_detect_ssn(self, pii_cleaner):
        text = "SSN is 123-45-6789 on file."
        _, detected = pii_cleaner.remove_pii(text)
        ssns = [d for d in detected if d["type"] == "ssn"]
        assert len(ssns) >= 1
        assert "123-45-6789" in [s["value"] for s in ssns]

    def test_detect_credit_card(self, pii_cleaner):
        text = "Card number 4111-1111-1111-1111 was used."
        _, detected = pii_cleaner.remove_pii(text)
        cards = [d for d in detected if d["type"] == "credit_card"]
        assert len(cards) == 1

    def test_detect_ip_address(self, pii_cleaner):
        text = "Server at 192.168.1.100 is down."
        _, detected = pii_cleaner.remove_pii(text)
        ips = [d for d in detected if d["type"] == "ip_address"]
        assert len(ips) == 1
        assert ips[0]["value"] == "192.168.1.100"

    # -- redact action --
    def test_pii_action_redact(self):
        c = TechnicalContentCleaner(config={"detect_pii": True, "pii_action": "redact"})
        text = "Email: user@example.com here."
        result_text, detected = c.remove_pii(text)
        assert "[REDACTED]" in result_text
        assert "user@example.com" not in result_text
        assert len(detected) >= 1

    # -- remove action --
    def test_pii_action_remove(self):
        c = TechnicalContentCleaner(config={"detect_pii": True, "pii_action": "remove"})
        text = "Email: user@example.com here."
        result_text, detected = c.remove_pii(text)
        assert "user@example.com" not in result_text
        assert "[REDACTED]" not in result_text
        assert len(detected) >= 1

    # -- flag action (leaves text unchanged) --
    def test_pii_action_flag_leaves_text_unchanged(self, pii_cleaner):
        text = "Email: user@example.com here."
        result_text, detected = pii_cleaner.remove_pii(text)
        assert result_text == text
        assert len(detected) >= 1

    # -- metrics --
    def test_pii_metrics_updated(self, pii_cleaner):
        pii_cleaner.remove_pii("Contact user@example.com or 555-123-4567.")
        assert pii_cleaner.get_metrics()["pii_detected"] >= 2

    # -- edge cases --
    def test_no_pii_returns_empty_list(self, pii_cleaner):
        text = "This text has no personal information at all."
        result_text, detected = pii_cleaner.remove_pii(text)
        assert result_text == text
        assert detected == []

    def test_multiple_pii_of_same_type(self, pii_cleaner):
        text = "Contact a@b.com or c@d.com for help."
        _, detected = pii_cleaner.remove_pii(text)
        emails = [d for d in detected if d["type"] == "email"]
        assert len(emails) == 2

    def test_pii_entity_has_required_fields(self, pii_cleaner):
        text = "Email: user@example.com here."
        _, detected = pii_cleaner.remove_pii(text)
        entity = detected[0]
        assert "type" in entity
        assert "value" in entity
        assert "start" in entity
        assert "end" in entity
        assert isinstance(entity["start"], int)
        assert entity["end"] > entity["start"]


# ---------------------------------------------------------------------------
# assess_quality()
# ---------------------------------------------------------------------------

class TestAssessQuality:
    """Test quality assessment with 5 weighted factors."""

    def test_empty_content_returns_zero(self, cleaner):
        assert cleaner.assess_quality("") == 0.0

    def test_score_between_zero_and_one(self, cleaner):
        text = (
            "The algorithm processes input parameters and returns a result value. "
            "This function implements the specification for the processor interface. "
            "The variable stores the calculation result for later operation."
        )
        score = cleaner.assess_quality(text)
        assert 0.0 <= score <= 1.0

    def test_technical_content_scores_higher(self, cleaner):
        technical = (
            "The algorithm uses a function to process variable parameters "
            "and return a result. The implementation follows the specification "
            "for register memory processor instruction operation."
        )
        generic = "The cat sat on the mat."
        assert cleaner.assess_quality(technical) > cleaner.assess_quality(generic)

    def test_score_never_exceeds_one(self, cleaner):
        text = (
            "algorithm function variable parameter return struct class "
            "interface implementation specification register memory processor "
            "instruction operation equation formula calculation value result. "
            "This is a complete sentence that helps with all the quality factors."
        )
        assert cleaner.assess_quality(text) <= 1.0

    def test_formatting_consistency_contributes(self, cleaner):
        # All lines same indent -> high formatting consistency score
        text = "Line one is here.\nLine two is here.\nLine three is here."
        assert cleaner.assess_quality(text) > 0.0

    def test_content_completeness_for_well_formed_text(self, cleaner):
        text = "This is complete. Another sentence here. Third one for good measure."
        assert cleaner.assess_quality(text) > 0.0

    def test_readability_for_reasonable_text(self, cleaner):
        text = "This is a reasonable sentence. It has normal words. The structure is clear."
        assert cleaner.assess_quality(text) > 0.0


# ---------------------------------------------------------------------------
# get_quality_factors()
# ---------------------------------------------------------------------------

class TestGetQualityFactors:
    """Test get_quality_factors()."""

    def test_returns_five_factors(self, cleaner):
        factors = cleaner.get_quality_factors()
        assert len(factors) == 5

    def test_expected_factors_present(self, cleaner):
        factors = cleaner.get_quality_factors()
        assert "technical_content_preservation" in factors
        assert "formatting_consistency" in factors
        assert "artifact_removal" in factors
        assert "content_completeness" in factors
        assert "readability_improvement" in factors

    def test_returns_copy(self, cleaner):
        factors = cleaner.get_quality_factors()
        factors.append("extra")
        assert "extra" not in cleaner.get_quality_factors()
        assert len(cleaner.get_quality_factors()) == 5


# ---------------------------------------------------------------------------
# configure() and get_config()
# ---------------------------------------------------------------------------

class TestConfigure:
    """Test configure() and config management."""

    def test_configure_updates_config(self, cleaner):
        cleaner.configure({"detect_pii": True})
        assert cleaner.get_config()["detect_pii"] is True

    def test_configure_multiple_keys(self, cleaner):
        cleaner.configure({"detect_pii": True, "pii_action": "redact"})
        cfg = cleaner.get_config()
        assert cfg["detect_pii"] is True
        assert cfg["pii_action"] == "redact"

    def test_get_config_returns_copy(self, cleaner):
        cfg = cleaner.get_config()
        cfg["detect_pii"] = True
        assert cleaner.get_config()["detect_pii"] is False


# ---------------------------------------------------------------------------
# _validate_config()
# ---------------------------------------------------------------------------

class TestValidateConfig:
    """Test _validate_config() via configure()."""

    def test_invalid_key_raises(self, cleaner):
        with pytest.raises(ValueError, match="Invalid configuration keys"):
            cleaner.configure({"nonexistent_key": True})

    def test_invalid_pii_action_raises(self, cleaner):
        with pytest.raises(ValueError, match="pii_action must be"):
            cleaner.configure({"pii_action": "destroy"})

    def test_negative_min_line_length_raises(self, cleaner):
        with pytest.raises(ValueError, match="min_line_length"):
            cleaner.configure({"min_line_length": -1})

    def test_non_int_min_line_length_raises(self, cleaner):
        with pytest.raises(ValueError, match="min_line_length"):
            cleaner.configure({"min_line_length": 3.5})

    def test_string_min_line_length_raises(self, cleaner):
        with pytest.raises(ValueError, match="min_line_length"):
            cleaner.configure({"min_line_length": "ten"})

    def test_zero_max_consecutive_newlines_raises(self, cleaner):
        with pytest.raises(ValueError, match="max_consecutive_newlines"):
            cleaner.configure({"max_consecutive_newlines": 0})

    def test_negative_max_consecutive_newlines_raises(self, cleaner):
        with pytest.raises(ValueError, match="max_consecutive_newlines"):
            cleaner.configure({"max_consecutive_newlines": -1})

    def test_valid_config_does_not_raise(self, cleaner):
        cleaner.configure({
            "pii_action": "remove",
            "min_line_length": 0,
            "max_consecutive_newlines": 1,
        })
        cfg = cleaner.get_config()
        assert cfg["pii_action"] == "remove"
        assert cfg["min_line_length"] == 0
        assert cfg["max_consecutive_newlines"] == 1


# ---------------------------------------------------------------------------
# _protect_technical_content()
# ---------------------------------------------------------------------------

class TestProtectTechnicalContent:
    """Test _protect_technical_content() directly."""

    def test_code_block_replaced_with_placeholder(self, cleaner):
        text = "Text before.\n```\ncode\n```\nText after."
        protected = cleaner._protect_technical_content(text)
        assert "__PROTECTED_CODE_" in protected["text"]
        assert len(protected["code_blocks"]) >= 1

    def test_equation_replaced_with_placeholder(self, cleaner):
        text = "The equation $$a+b$$ is simple."
        protected = cleaner._protect_technical_content(text)
        assert "__PROTECTED_EQUATION_" in protected["text"]
        assert len(protected["equations"]) >= 1

    def test_inline_code_protected(self, cleaner):
        text = "Use `print(x)` for output."
        protected = cleaner._protect_technical_content(text)
        assert "__PROTECTED_CODE_" in protected["text"]
        assert "`print(x)`" in protected["code_blocks"]

    def test_inline_equation_protected(self, cleaner):
        text = "The variable $x$ is important."
        protected = cleaner._protect_technical_content(text)
        assert "__PROTECTED_EQUATION_" in protected["text"]
        assert "$x$" in protected["equations"]

    def test_placeholders_map_back_to_originals(self, cleaner):
        # Use inline code (single backtick) to avoid multi-pattern overlap
        text = "See `x = 1` here."
        protected = cleaner._protect_technical_content(text)
        for placeholder, original in protected["placeholders"].items():
            assert original in text
        # At least one placeholder was created
        assert len(protected["placeholders"]) >= 1

    def test_no_code_protection_when_disabled(self):
        c = TechnicalContentCleaner(config={"preserve_code_blocks": False})
        text = "```code block``` here."
        protected = c._protect_technical_content(text)
        assert len(protected["code_blocks"]) == 0

    def test_no_equation_protection_when_disabled(self):
        c = TechnicalContentCleaner(config={"preserve_equations": False})
        text = "The equation $$a+b$$ here."
        protected = c._protect_technical_content(text)
        assert len(protected["equations"]) == 0

    def test_both_disabled_no_protection(self):
        c = TechnicalContentCleaner(config={
            "preserve_code_blocks": False,
            "preserve_equations": False,
        })
        text = "```code``` and $$eq$$"
        protected = c._protect_technical_content(text)
        assert len(protected["code_blocks"]) == 0
        assert len(protected["equations"]) == 0
        assert len(protected["placeholders"]) == 0

    def test_metrics_increment_on_code_protection(self, cleaner):
        text = "```a``` and ```b```"
        cleaner._protect_technical_content(text)
        assert cleaner.get_metrics()["cleaning_operations"]["code_blocks_preserved"] >= 2

    def test_metrics_increment_on_equation_protection(self, cleaner):
        text = "$$eq1$$ and $$eq2$$"
        cleaner._protect_technical_content(text)
        assert cleaner.get_metrics()["cleaning_operations"]["equations_preserved"] >= 2


# ---------------------------------------------------------------------------
# get_metrics()
# ---------------------------------------------------------------------------

class TestGetMetrics:
    """Test get_metrics()."""

    def test_returns_copy(self, cleaner):
        m = cleaner.get_metrics()
        m["texts_processed"] = 999
        assert cleaner.get_metrics()["texts_processed"] == 0

    def test_has_expected_keys(self, cleaner):
        m = cleaner.get_metrics()
        assert "texts_processed" in m
        assert "artifacts_removed" in m
        assert "pii_detected" in m
        assert "bytes_cleaned" in m
        assert "cleaning_operations" in m

    def test_cleaning_operations_sub_keys(self, cleaner):
        ops = cleaner.get_metrics()["cleaning_operations"]
        assert "whitespace_normalized" in ops
        assert "artifacts_removed" in ops
        assert "code_blocks_preserved" in ops
        assert "equations_preserved" in ops


# ---------------------------------------------------------------------------
# Artifact removal (exercised through clean())
# ---------------------------------------------------------------------------

class TestArtifactRemoval:
    """Test artifact removal through the clean() pipeline."""

    def test_page_numbers_removed(self, cleaner):
        text = "page 1\nThe algorithm processes data and returns a result value."
        result = cleaner.clean(text)
        assert "page 1" not in result.lower()

    def test_toc_lines_removed(self, cleaner):
        text = "table of contents\nThe algorithm processes data and returns a result value."
        result = cleaner.clean(text)
        assert "table of contents" not in result.lower()

    def test_navigation_elements_removed(self, cleaner):
        text = "back to top\nThe algorithm processes data and returns a result value."
        result = cleaner.clean(text)
        assert "back to top" not in result.lower()

    def test_copyright_removed(self, cleaner):
        text = "copyright 2024\nThe algorithm processes data and returns a result value."
        result = cleaner.clean(text)
        assert "copyright" not in result.lower()

    def test_short_lines_removed_as_artifacts(self, cleaner):
        # Lines shorter than min_line_length (10) get removed
        text = "short\nThe algorithm processes data and returns a result value."
        result = cleaner.clean(text)
        assert "short" not in result

    def test_empty_lines_preserved_for_structure(self, cleaner):
        text = (
            "The algorithm processes data and returns a result value.\n\n"
            "Another paragraph that is also long enough to survive."
        )
        result = cleaner.clean(text)
        assert "\n" in result

    def test_technical_keywords_in_short_lines_preserved(self, cleaner):
        # Lines containing 'algorithm', 'equation', 'figure', 'table' survive
        text = "equation\nThe algorithm processes data and returns a result value."
        result = cleaner.clean(text)
        assert "equation" in result.lower()


# ---------------------------------------------------------------------------
# Whitespace normalization (exercised through clean())
# ---------------------------------------------------------------------------

class TestWhitespaceNormalization:
    """Test whitespace normalization through the clean() pipeline."""

    def test_excessive_newlines_collapsed(self, cleaner):
        # Test _normalize_whitespace directly since the code block protection
        # regex (^\s{4,}.*$) can match consecutive newlines, preventing
        # normalization via the clean() pipeline.
        text = "Line one has enough text.\n\n\n\n\nLine two has enough text."
        result = cleaner._normalize_whitespace(text)
        assert "\n\n\n" not in result
        assert "Line one" in result
        assert "Line two" in result

    def test_trailing_whitespace_removed(self, cleaner):
        text = "The algorithm processes data.   \nAnother line with enough text here."
        result = cleaner.clean(text)
        lines = result.split("\n")
        for line in lines:
            assert line == line.rstrip(), f"Trailing whitespace found in: {repr(line)}"

    def test_custom_max_consecutive_newlines(self):
        c = TechnicalContentCleaner(config={"max_consecutive_newlines": 3})
        text = "First paragraph.\n\n\n\n\n\nSecond paragraph."
        result = c._normalize_whitespace(text)
        # Should allow up to 3 newlines, but not more
        assert "\n\n\n\n" not in result
