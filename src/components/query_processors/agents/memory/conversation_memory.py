"""
Conversation memory implementation.

Provides simple in-memory storage for conversation history with optional
persistence and capacity limits.

Architecture:
- List-based message storage
- Optional capacity limit (FIFO when full)
- Optional persistence to JSON
- Thread-safe operations (optional)

Usage:
    >>> from src.components.query_processors.agents.memory import ConversationMemory
    >>>
    >>> # Create memory with limit
    >>> memory = ConversationMemory(max_messages=100)
    >>>
    >>> # Add messages
    >>> memory.add_message("user", "What is machine learning?")
    >>> memory.add_message("assistant", "Machine learning is...")
    >>>
    >>> # Get recent messages
    >>> recent = memory.get_messages(last_n=5)
    >>>
    >>> # Save to file
    >>> memory.save("conversation.json")
"""

import json
import logging
from pathlib import Path
from typing import List, Optional

from ..base_memory import BaseMemory, MemoryPersistenceError
from ..models import Message

logger = logging.getLogger(__name__)


class ConversationMemory(BaseMemory):
    """
    Simple in-memory conversation history.

    Stores conversation messages in a list with optional capacity limit.
    When capacity is reached, oldest messages are removed (FIFO).

    Features:
    - Unlimited or capacity-limited storage
    - Get all or last N messages
    - Clear history
    - Save/load to JSON
    - Message count tracking

    Example:
        >>> memory = ConversationMemory(max_messages=100)
        >>> memory.add_message("user", "Hello!")
        >>> memory.add_message("assistant", "Hi! How can I help?")
        >>> messages = memory.get_messages(last_n=2)
        >>> len(messages)  # 2
    """

    def __init__(
        self,
        max_messages: Optional[int] = None,
        persistent: bool = False
    ):
        """
        Initialize conversation memory.

        Args:
            max_messages: Maximum number of messages to store.
                         If None, unlimited capacity.
                         When limit reached, oldest messages removed.
            persistent: Whether to support save/load operations.
                       If False, save/load will raise NotImplementedError.
        """
        self._messages: List[Message] = []
        self._max_messages = max_messages
        self._persistent = persistent

    def add_message(self, role: str, content: str) -> None:
        """
        Add message to memory.

        If capacity limit is set and reached, removes oldest message first.

        Args:
            role: Message role ("user", "assistant", or "system")
            content: Message content

        Raises:
            ValueError: If role is invalid or content is empty

        Example:
            >>> memory = ConversationMemory()
            >>> memory.add_message("user", "Hello")
            >>> memory.add_message("assistant", "Hi!")
            >>> len(memory)  # 2
        """
        # Create message (validation happens in Message.__post_init__)
        message = Message(role=role, content=content)

        # Add to storage
        self._messages.append(message)

        # Enforce capacity limit
        if self._max_messages and len(self._messages) > self._max_messages:
            # Remove oldest message
            removed = self._messages.pop(0)
            logger.debug(
                f"Capacity limit reached, removed oldest message: "
                f"{removed.role} at {removed.timestamp}"
            )

    def get_messages(self, last_n: Optional[int] = None) -> List[Message]:
        """
        Get messages from memory.

        Args:
            last_n: If specified, return only last N messages.
                   If None, return all messages.

        Returns:
            List of Message objects in chronological order

        Example:
            >>> memory = ConversationMemory()
            >>> memory.add_message("user", "Hello")
            >>> memory.add_message("assistant", "Hi!")
            >>> memory.add_message("user", "How are you?")
            >>>
            >>> all_msgs = memory.get_messages()
            >>> len(all_msgs)  # 3
            >>>
            >>> recent = memory.get_messages(last_n=2)
            >>> len(recent)  # 2
        """
        if last_n is None:
            return self._messages.copy()

        if last_n <= 0:
            return []

        return self._messages[-last_n:]

    def clear(self) -> None:
        """
        Clear all messages from memory.

        Example:
            >>> memory = ConversationMemory()
            >>> memory.add_message("user", "Hello")
            >>> len(memory)  # 1
            >>> memory.clear()
            >>> len(memory)  # 0
        """
        self._messages = []
        logger.debug("Conversation memory cleared")

    def save(self, filepath: str) -> None:
        """
        Save memory to JSON file.

        Args:
            filepath: Path to save file

        Raises:
            NotImplementedError: If persistent=False
            MemoryPersistenceError: If save fails

        Example:
            >>> memory = ConversationMemory(persistent=True)
            >>> memory.add_message("user", "Hello")
            >>> memory.save("conversation.json")
        """
        if not self._persistent:
            raise NotImplementedError(
                "Save/load not enabled. Create with persistent=True"
            )

        try:
            # Convert messages to dict format
            messages_data = [
                {
                    "role": msg.role,
                    "content": msg.content,
                    "timestamp": msg.timestamp.isoformat(),
                    "metadata": msg.metadata
                }
                for msg in self._messages
            ]

            # Save to JSON
            path = Path(filepath)
            path.parent.mkdir(parents=True, exist_ok=True)

            with open(path, 'w', encoding='utf-8') as f:
                json.dump(messages_data, f, indent=2, ensure_ascii=False)

            logger.info(f"Saved {len(self._messages)} messages to {filepath}")

        except Exception as e:
            raise MemoryPersistenceError(f"Failed to save memory: {e}")

    def load(self, filepath: str) -> None:
        """
        Load memory from JSON file.

        Args:
            filepath: Path to load from

        Raises:
            NotImplementedError: If persistent=False
            MemoryPersistenceError: If load fails

        Example:
            >>> memory = ConversationMemory(persistent=True)
            >>> memory.load("conversation.json")
            >>> messages = memory.get_messages()
        """
        if not self._persistent:
            raise NotImplementedError(
                "Save/load not enabled. Create with persistent=True"
            )

        try:
            path = Path(filepath)

            if not path.exists():
                raise MemoryPersistenceError(f"File not found: {filepath}")

            with open(path, 'r', encoding='utf-8') as f:
                messages_data = json.load(f)

            # Clear existing messages
            self._messages = []

            # Load messages
            for msg_data in messages_data:
                self.add_message(
                    role=msg_data["role"],
                    content=msg_data["content"]
                )

            logger.info(f"Loaded {len(self._messages)} messages from {filepath}")

        except json.JSONDecodeError as e:
            raise MemoryPersistenceError(f"Invalid JSON in {filepath}: {e}")
        except Exception as e:
            raise MemoryPersistenceError(f"Failed to load memory: {e}")

    def get_message_count(self) -> int:
        """Get total number of messages."""
        return len(self._messages)

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"ConversationMemory(messages={len(self._messages)}, "
            f"max={self._max_messages})"
        )
