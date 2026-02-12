"""Unit tests for DomainAwareQueryProcessor bug fixes."""

import pytest
from unittest.mock import MagicMock, patch
from src.components.query_processors.domain_aware_query_processor import (
    DomainAwareQueryProcessor,
)
from src.core.interfaces import Answer


pytestmark = [pytest.mark.unit]


class TestProcessQueryFallback:
    """Verify the exception handler delegates to the correct parent method."""

    @pytest.fixture
    def processor(self):
        """Create a DomainAwareQueryProcessor with mocked dependencies."""
        mock_retriever = MagicMock()
        mock_generator = MagicMock()
        proc = DomainAwareQueryProcessor(
            retriever=mock_retriever,
            generator=mock_generator,
            enable_domain_filtering=False,
        )
        return proc

    def test_fallback_on_exception_calls_parent_process(self, processor):
        """When process_query() raises internally, fallback must call super().process(), not super().process_query()."""
        expected = Answer(text="fallback answer", sources=[], confidence=0.5)

        with patch.object(
            type(processor).__bases__[0],  # ModularQueryProcessor
            'process',
            return_value=expected,
        ) as mock_process:
            # Sabotage the try-block: enable domain filtering with a failing filter
            processor.enable_domain_filtering = True
            processor.domain_filter = MagicMock()
            processor.domain_filter.analyze_domain_relevance.side_effect = RuntimeError("test error")

            result = processor.process_query("test query")

            # The except handler should call super().process(), not super().process_query()
            mock_process.assert_called_once_with("test query", None)
            assert result == expected
