"""
Abstract base class for memory systems.

This module defines the memory interface for agent conversation history
and working memory. Ensures consistent API across different memory implementations.

Architecture:
- Abstract interface using ABC
- Type-safe with comprehensive type hints
- Support for conversation history and working memory
- Optional persistence capabilities

Usage:
    >>> from src.components.query_processors.agents.base_memory import BaseMemory
    >>> from src.components.query_processors.agents.memory import ConversationMemory
    >>>
    >>> # Create memory
    >>> memory = ConversationMemory(max_messages=100)
    >>>
    >>> # Add messages
    >>> memory.add_message("user", "Hello!")
    >>> memory.add_message("assistant", "Hi! How can I help?")
    >>>
    >>> # Get messages
    >>> messages = memory.get_messages(last_n=10)
"""

import logging
from abc import ABC, abstractmethod
from typing import List, Optional

from .models import Message

logger = logging.getLogger(__name__)


class BaseMemory(ABC):
    """
    Abstract base class for memory systems.

    Memory systems store conversation history and working context for agents.
    Different implementations can provide:
    - Simple in-memory storage
    - Persistent storage (file, database)
    - Limited buffer (e.g., last N messages)
    - Token-aware buffers (for LLM context limits)
    - Semantic search over history

    Key Principles:
    - add_message() adds to history
    - get_messages() retrieves history
    - clear() removes all history
    - Thread-safe operations (if needed)

    Example:
        >>> class MyMemory(BaseMemory):
        ...     def __init__(self):
        ...         self.messages = []
        ...
        ...     def add_message(self, role, content):
        ...         self.messages.append(Message(role, content))
        ...
        ...     def get_messages(self, last_n=None):
        ...         if last_n:
        ...             return self.messages[-last_n:]
        ...         return self.messages
        ...
        ...     def clear(self):
        ...         self.messages = []
    """

    @abstractmethod
    def add_message(self, role: str, content: str) -> None:
        """
        Add message to memory.

        Args:
            role: Message role ("user", "assistant", or "system")
            content: Message content

        Raises:
            ValueError: If role is invalid or content is empty

        Example:
            >>> memory = ConversationMemory()
            >>> memory.add_message("user", "What is machine learning?")
            >>> memory.add_message("assistant", "Machine learning is...")
        """
        pass

    @abstractmethod
    def get_messages(self, last_n: Optional[int] = None) -> List[Message]:
        """
        Get messages from memory.

        Args:
            last_n: Optional limit to last N messages.
                   If None, returns all messages.

        Returns:
            List of Message objects in chronological order

        Example:
            >>> memory = ConversationMemory()
            >>> # ... add several messages ...
            >>> recent = memory.get_messages(last_n=5)  # Last 5 messages
            >>> all_msgs = memory.get_messages()  # All messages
        """
        pass

    @abstractmethod
    def clear(self) -> None:
        """
        Clear all messages from memory.

        Example:
            >>> memory = ConversationMemory()
            >>> memory.add_message("user", "Hello")
            >>> len(memory.get_messages())  # 1
            >>> memory.clear()
            >>> len(memory.get_messages())  # 0
        """
        pass

    def get_message_count(self) -> int:
        """
        Get total number of messages in memory.

        Returns:
            Total message count

        Default implementation counts via get_messages().

        Example:
            >>> memory = ConversationMemory()
            >>> memory.add_message("user", "Hello")
            >>> memory.add_message("assistant", "Hi!")
            >>> memory.get_message_count()  # 2
        """
        return len(self.get_messages())

    def save(self, filepath: str) -> None:
        """
        Save memory to file.

        Optional method for persistent memory implementations.
        Default implementation raises NotImplementedError.

        Args:
            filepath: Path to save memory

        Raises:
            NotImplementedError: If persistence not supported

        Example:
            >>> memory = ConversationMemory(persistent=True)
            >>> # ... add messages ...
            >>> memory.save("conversation.json")
        """
        raise NotImplementedError("save() not implemented for this memory type")

    def load(self, filepath: str) -> None:
        """
        Load memory from file.

        Optional method for persistent memory implementations.
        Default implementation raises NotImplementedError.

        Args:
            filepath: Path to load memory from

        Raises:
            NotImplementedError: If persistence not supported

        Example:
            >>> memory = ConversationMemory(persistent=True)
            >>> memory.load("conversation.json")
            >>> messages = memory.get_messages()
        """
        raise NotImplementedError("load() not implemented for this memory type")

    def __len__(self) -> int:
        """Return number of messages in memory."""
        return self.get_message_count()

    def __repr__(self) -> str:
        """String representation of memory."""
        count = self.get_message_count()
        return f"{self.__class__.__name__}(messages={count})"


class MemoryError(Exception):
    """Base exception for memory errors."""

    pass


class MemoryCapacityError(MemoryError):
    """Memory capacity exceeded."""

    pass


class MemoryPersistenceError(MemoryError):
    """Error in memory persistence operations."""

    pass
