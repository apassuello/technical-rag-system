"""
Response Assembler Sub-components.

This module contains implementations of ResponseAssembler for formatting
final Answer objects with consistent structure and metadata.

Available Assemblers:
- StandardAssembler: Minimal metadata for performance-critical applications
- RichAssembler: Comprehensive metadata with detailed source information
- StreamingAssembler: Support for streaming response assembly (future)
"""

from ..base import ResponseAssembler, Answer
from .base_assembler import BaseResponseAssembler
from .standard_assembler import StandardAssembler
from .rich_assembler import RichAssembler

# Future implementations
# from .streaming_assembler import StreamingAssembler

__all__ = [
    'ResponseAssembler',
    'Answer',
    'BaseResponseAssembler',
    'StandardAssembler',
    'RichAssembler',
    # 'StreamingAssembler'
]