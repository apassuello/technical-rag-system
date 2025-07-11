"""
Response parsers for answer generation.

This module provides parsers that extract structured information
from LLM responses in various formats.
"""

from .markdown_parser import MarkdownParser

# Future parsers will be imported here
# from .json_parser import JSONParser
# from .citation_parser import CitationParser

__all__ = [
    'MarkdownParser',
    # 'JSONParser',
    # 'CitationParser',
]

# Parser registry for easy lookup
PARSER_REGISTRY = {
    'markdown': MarkdownParser,
    # 'json': JSONParser,
    # 'citation': CitationParser,
}

def get_parser_class(parser_type: str):
    """
    Get response parser class by type.
    
    Args:
        parser_type: Parser type name
        
    Returns:
        Parser class
        
    Raises:
        ValueError: If parser type not found
    """
    if parser_type not in PARSER_REGISTRY:
        raise ValueError(f"Unknown response parser: {parser_type}. Available: {list(PARSER_REGISTRY.keys())}")
    return PARSER_REGISTRY[parser_type]