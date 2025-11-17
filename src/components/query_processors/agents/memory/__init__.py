"""
Memory implementations for agent systems.

This package provides memory systems for maintaining conversation history
and working context in agent applications.

Available memory types:
- ConversationMemory: Simple in-memory conversation history
- WorkingMemory: Task execution context and state

Usage:
    >>> from src.components.query_processors.agents.memory import (
    ...     ConversationMemory,
    ...     WorkingMemory
    ... )
    >>>
    >>> # Create conversation memory
    >>> memory = ConversationMemory(max_messages=100)
    >>> memory.add_message("user", "Hello!")
    >>> memory.add_message("assistant", "Hi! How can I help?")
    >>>
    >>> # Create working memory
    >>> working = WorkingMemory()
    >>> working.set_context("task_id", "task-123")
    >>> working.set_context("current_step", 1)
"""

from .conversation_memory import ConversationMemory
from .working_memory import WorkingMemory

__all__ = [
    "ConversationMemory",
    "WorkingMemory",
]
