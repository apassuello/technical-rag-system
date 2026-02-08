"""
Query analyzer for intelligent query classification.

This module provides heuristic-based query analysis without LLM overhead.
Analyzes query type, complexity, intent, and tool requirements.

Architecture:
- Fast heuristic analysis (<100ms)
- No LLM required for classification
- Keyword and pattern-based detection
- Extensible for future LLM integration

Usage:
    >>> analyzer = QueryAnalyzer()
    >>> analysis = analyzer.analyze("Calculate 25 * 47 and explain the result")
    >>> print(f"Type: {analysis.query_type}")
    >>> print(f"Complexity: {analysis.complexity:.2f}")
    >>> print(f"Tools: {analysis.requires_tools}")
"""

import logging
import re
from typing import List

from ..models import QueryAnalysis, QueryType

logger = logging.getLogger(__name__)


class QueryAnalyzer:
    """
    Analyze query characteristics using heuristics.

    This analyzer classifies queries and estimates complexity without LLM overhead.
    Uses keyword detection, pattern matching, and structural analysis.

    Attributes:
        complexity_keywords: Keywords indicating complex queries
        tool_patterns: Patterns for tool requirement detection
        entity_patterns: Patterns for entity extraction

    Example:
        >>> analyzer = QueryAnalyzer()
        >>> analysis = analyzer.analyze("What is machine learning?")
        >>> assert analysis.query_type == QueryType.SIMPLE
        >>> assert analysis.complexity < 0.5
    """

    def __init__(self) -> None:
        """Initialize query analyzer with heuristic patterns."""
        # Keywords for complexity detection
        self.complexity_keywords = {
            "sequential": ["and then", "after that", "following", "next", "subsequently"],
            "analytical": ["calculate", "analyze", "compute", "evaluate", "assess", "measure"],
            "research": ["research", "find all", "search for", "investigate", "explore"],
            "comparison": ["compare", "contrast", "difference", "versus", "vs"],
            "synthesis": ["summarize", "synthesize", "combine", "integrate", "merge"],
        }

        # Tool requirement patterns
        self.tool_patterns = {
            "calculator": ["calculate", "compute", "multiply", "divide", "add", "subtract"],
            "document_search": ["find", "search", "retrieve", "look up", "locate"],
            "code_analyzer": ["code", "function", "debug", "error", "stack trace"],
        }

        # Query type patterns
        self.type_keywords = {
            QueryType.CODE: ["code", "function", "debug", "error", "exception", "stack trace"],
            QueryType.ANALYTICAL: ["calculate", "analyze", "compute", "evaluate", "measure"],
            QueryType.RESEARCH: ["research", "find", "search", "papers", "articles", "studies"],
            QueryType.MULTI_STEP: ["and then", "after", "next", "following", "subsequently"],
        }

        # Intent patterns
        self.intent_patterns = {
            "information_retrieval": ["what", "who", "where", "when", "which"],
            "analysis": ["why", "how", "analyze", "evaluate"],
            "code_debug": ["debug", "error", "fix", "issue", "problem"],
            "calculation": ["calculate", "compute", "solve"],
            "comparison": ["compare", "contrast", "difference"],
        }

    def analyze(self, query: str) -> QueryAnalysis:
        """
        Analyze query and return classification.

        Args:
            query: User query to analyze

        Returns:
            QueryAnalysis with type, complexity, intent, entities, tools, steps

        Example:
            >>> analyzer = QueryAnalyzer()
            >>> analysis = analyzer.analyze("Calculate 25 * 47")
            >>> assert analysis.query_type == QueryType.ANALYTICAL
            >>> assert "calculator" in analysis.requires_tools
        """
        logger.debug(f"Analyzing query: {query[:100]}...")

        # Normalize query
        query_lower = query.lower()

        # Classify query type
        query_type = self._classify_type(query_lower)

        # Estimate complexity
        complexity = self._estimate_complexity(query, query_lower)

        # Extract intent
        intent = self._extract_intent(query_lower)

        # Extract entities
        entities = self._extract_entities(query)

        # Predict required tools
        requires_tools = self._predict_tools(query_lower)

        # Estimate reasoning steps
        estimated_steps = self._estimate_steps(complexity, query_type)

        analysis = QueryAnalysis(
            query_type=query_type,
            complexity=complexity,
            intent=intent,
            entities=entities,
            requires_tools=requires_tools,
            estimated_steps=estimated_steps,
            metadata={
                "query_length": len(query),
                "word_count": len(query.split()),
                "question_marks": query.count("?"),
            },
        )

        logger.debug(
            f"Analysis complete: type={query_type.value}, "
            f"complexity={complexity:.2f}, "
            f"tools={requires_tools}"
        )

        return analysis

    def _classify_type(self, query_lower: str) -> QueryType:
        """
        Classify query type based on keywords.

        Args:
            query_lower: Lowercase query string

        Returns:
            QueryType enum value
        """
        # Check each type's keywords
        for query_type, keywords in self.type_keywords.items():
            if any(keyword in query_lower for keyword in keywords):
                return query_type

        # Default: simple query
        return QueryType.SIMPLE

    def _estimate_complexity(self, query: str, query_lower: str) -> float:
        """
        Estimate query complexity (0.0-1.0).

        Factors considered:
        - Query length
        - Number of questions
        - Complex keywords
        - Tool requirements
        - Logical connectors

        Args:
            query: Original query string
            query_lower: Lowercase query string

        Returns:
            Complexity score (0.0 = simple, 1.0 = very complex)
        """
        score = 0.0

        # Factor 1: Length (longer queries often more complex)
        if len(query) > 300:
            score += 0.3
        elif len(query) > 150:
            score += 0.2
        elif len(query) > 75:
            score += 0.1

        # Factor 2: Multiple questions
        question_count = query.count("?")
        score += min(question_count * 0.15, 0.3)

        # Factor 3: Complex keywords
        for category, keywords in self.complexity_keywords.items():
            for keyword in keywords:
                if keyword in query_lower:
                    score += 0.1
                    break  # Only count once per category

        # Factor 4: Logical connectors (indicates multi-step)
        connectors = ["and", "then", "after", "before", "first", "second"]
        connector_count = sum(1 for conn in connectors if conn in query_lower)
        score += min(connector_count * 0.05, 0.15)

        # Factor 5: Multiple sentences
        sentence_count = len([s for s in query.split(".") if s.strip()])
        if sentence_count > 3:
            score += 0.2
        elif sentence_count > 2:
            score += 0.1

        # Ensure score is in [0.0, 1.0]
        return min(score, 1.0)

    def _extract_intent(self, query_lower: str) -> str:
        """
        Extract query intent.

        Args:
            query_lower: Lowercase query string

        Returns:
            Intent string (e.g., "information_retrieval", "analysis")
        """
        # Check each intent pattern
        for intent, keywords in self.intent_patterns.items():
            if any(keyword in query_lower for keyword in keywords):
                return intent

        # Default intent
        return "information_retrieval"

    def _extract_entities(self, query: str) -> List[str]:
        """
        Extract entities from query.

        Simple heuristic-based extraction:
        - Capitalized words (potential names/concepts)
        - Numbers
        - Technical terms

        Args:
            query: Original query string

        Returns:
            List of extracted entities
        """
        entities = []

        # Extract capitalized words (not at start of sentence)
        words = query.split()
        for i, word in enumerate(words):
            # Skip first word of sentences
            if i > 0 and not words[i - 1].endswith((".", "?", "!")):
                if word and word[0].isupper() and len(word) > 1:
                    # Remove punctuation
                    clean_word = re.sub(r'[^\w\s]', '', word)
                    if clean_word:
                        entities.append(clean_word)

        # Extract numbers
        numbers = re.findall(r'\b\d+(?:\.\d+)?\b', query)
        entities.extend(numbers)

        return list(set(entities))  # Remove duplicates

    def _predict_tools(self, query_lower: str) -> List[str]:
        """
        Predict required tools based on query content.

        Args:
            query_lower: Lowercase query string

        Returns:
            List of predicted tool names
        """
        tools = []

        # Check each tool pattern
        for tool, keywords in self.tool_patterns.items():
            if any(keyword in query_lower for keyword in keywords):
                tools.append(tool)

        return tools

    def _estimate_steps(self, complexity: float, query_type: QueryType) -> int:
        """
        Estimate number of reasoning steps required.

        Args:
            complexity: Query complexity score (0.0-1.0)
            query_type: Classified query type

        Returns:
            Estimated number of reasoning steps (minimum 1)
        """
        # Base steps by complexity
        if complexity < 0.3:
            base_steps = 1
        elif complexity < 0.6:
            base_steps = 2
        else:
            base_steps = 3

        # Adjust by query type
        if query_type == QueryType.MULTI_STEP:
            base_steps += 2
        elif query_type in (QueryType.RESEARCH, QueryType.ANALYTICAL):
            base_steps += 1

        return max(base_steps, 1)
