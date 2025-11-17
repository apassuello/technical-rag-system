"""
Unit tests for memory implementations.

Tests ConversationMemory and WorkingMemory.
"""

import pytest
import tempfile
from pathlib import Path
from src.components.query_processors.agents.memory import (
    ConversationMemory,
    WorkingMemory
)
from src.components.query_processors.agents.base_memory import (
    MemoryCapacityError,
    MemoryPersistenceError
)


class TestConversationMemory:
    """Test ConversationMemory implementation."""

    def test_initialization_default(self):
        """Test creating memory with default settings."""
        memory = ConversationMemory()
        assert len(memory) == 0
        assert memory._max_messages is None
        assert memory._persistent is False

    def test_initialization_with_capacity(self):
        """Test creating memory with capacity limit."""
        memory = ConversationMemory(max_messages=10)
        assert memory._max_messages == 10

    def test_add_single_message(self):
        """Test adding a single message."""
        memory = ConversationMemory()
        memory.add_message("user", "Hello!")

        assert len(memory) == 1
        messages = memory.get_messages()
        assert len(messages) == 1
        assert messages[0].role == "user"
        assert messages[0].content == "Hello!"

    def test_add_multiple_messages(self):
        """Test adding multiple messages."""
        memory = ConversationMemory()
        memory.add_message("user", "Hello!")
        memory.add_message("assistant", "Hi! How can I help?")
        memory.add_message("user", "What is ML?")

        assert len(memory) == 3
        messages = memory.get_messages()
        assert messages[0].role == "user"
        assert messages[1].role == "assistant"
        assert messages[2].role == "user"

    def test_capacity_limit_enforced(self):
        """Test that capacity limit is enforced (FIFO)."""
        memory = ConversationMemory(max_messages=3)

        memory.add_message("user", "Message 1")
        memory.add_message("user", "Message 2")
        memory.add_message("user", "Message 3")
        assert len(memory) == 3

        # Add 4th message - should remove oldest
        memory.add_message("user", "Message 4")
        assert len(memory) == 3

        messages = memory.get_messages()
        assert messages[0].content == "Message 2"  # Message 1 removed
        assert messages[1].content == "Message 3"
        assert messages[2].content == "Message 4"

    def test_get_all_messages(self):
        """Test getting all messages."""
        memory = ConversationMemory()
        memory.add_message("user", "Hello")
        memory.add_message("assistant", "Hi")
        memory.add_message("user", "Bye")

        messages = memory.get_messages()
        assert len(messages) == 3

    def test_get_last_n_messages(self):
        """Test getting last N messages."""
        memory = ConversationMemory()
        for i in range(10):
            memory.add_message("user", f"Message {i}")

        last_3 = memory.get_messages(last_n=3)
        assert len(last_3) == 3
        assert last_3[0].content == "Message 7"
        assert last_3[1].content == "Message 8"
        assert last_3[2].content == "Message 9"

    def test_get_last_n_zero(self):
        """Test getting last 0 messages returns empty list."""
        memory = ConversationMemory()
        memory.add_message("user", "Hello")

        messages = memory.get_messages(last_n=0)
        assert len(messages) == 0

    def test_get_last_n_more_than_available(self):
        """Test getting more messages than available returns all."""
        memory = ConversationMemory()
        memory.add_message("user", "Message 1")
        memory.add_message("user", "Message 2")

        messages = memory.get_messages(last_n=10)
        assert len(messages) == 2

    def test_clear_memory(self):
        """Test clearing all messages."""
        memory = ConversationMemory()
        memory.add_message("user", "Hello")
        memory.add_message("assistant", "Hi")
        assert len(memory) == 2

        memory.clear()
        assert len(memory) == 0
        assert memory.get_messages() == []

    def test_save_without_persistent_raises_error(self):
        """Test that save() without persistent=True raises error."""
        memory = ConversationMemory(persistent=False)
        memory.add_message("user", "Hello")

        with pytest.raises(NotImplementedError, match="Save/load not enabled"):
            memory.save("test.json")

    def test_load_without_persistent_raises_error(self):
        """Test that load() without persistent=True raises error."""
        memory = ConversationMemory(persistent=False)

        with pytest.raises(NotImplementedError, match="Save/load not enabled"):
            memory.load("test.json")

    def test_save_and_load(self):
        """Test saving and loading memory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = Path(tmpdir) / "conversation.json"

            # Create and save memory
            memory1 = ConversationMemory(persistent=True)
            memory1.add_message("user", "Hello!")
            memory1.add_message("assistant", "Hi! How can I help?")
            memory1.add_message("user", "What is ML?")
            memory1.save(str(filepath))

            # Load into new memory
            memory2 = ConversationMemory(persistent=True)
            memory2.load(str(filepath))

            # Verify
            assert len(memory2) == 3
            messages = memory2.get_messages()
            assert messages[0].role == "user"
            assert messages[0].content == "Hello!"
            assert messages[1].role == "assistant"
            assert messages[2].content == "What is ML?"

    def test_load_nonexistent_file_raises_error(self):
        """Test loading from nonexistent file raises error."""
        memory = ConversationMemory(persistent=True)

        with pytest.raises(MemoryPersistenceError, match="File not found"):
            memory.load("/nonexistent/path/file.json")

    def test_get_message_count(self):
        """Test get_message_count()."""
        memory = ConversationMemory()
        assert memory.get_message_count() == 0

        memory.add_message("user", "Hello")
        assert memory.get_message_count() == 1

        memory.add_message("assistant", "Hi")
        assert memory.get_message_count() == 2

    def test_len_operator(self):
        """Test len() operator."""
        memory = ConversationMemory()
        assert len(memory) == 0

        memory.add_message("user", "Hello")
        assert len(memory) == 1

    def test_repr(self):
        """Test string representation."""
        memory = ConversationMemory(max_messages=10)
        memory.add_message("user", "Hello")

        repr_str = repr(memory)
        assert "ConversationMemory" in repr_str
        assert "messages=1" in repr_str
        assert "max=10" in repr_str


class TestWorkingMemory:
    """Test WorkingMemory implementation."""

    def test_initialization(self):
        """Test creating working memory."""
        working = WorkingMemory()
        assert len(working) == 0

    def test_set_context_string(self):
        """Test setting string context variable."""
        working = WorkingMemory()
        working.set_context("task_id", "task-123")

        assert working.get_context("task_id") == "task-123"

    def test_set_context_integer(self):
        """Test setting integer context variable."""
        working = WorkingMemory()
        working.set_context("step", 5)

        assert working.get_context("step") == 5

    def test_set_context_dict(self):
        """Test setting dict context variable."""
        working = WorkingMemory()
        data = {"key": "value", "count": 42}
        working.set_context("data", data)

        assert working.get_context("data") == data

    def test_set_context_list(self):
        """Test setting list context variable."""
        working = WorkingMemory()
        results = [1, 2, 3, 4, 5]
        working.set_context("results", results)

        assert working.get_context("results") == results

    def test_set_context_empty_key_raises_error(self):
        """Test that empty key raises ValueError."""
        working = WorkingMemory()

        with pytest.raises(ValueError, match="Context key cannot be empty"):
            working.set_context("", "value")

    def test_get_context_existing_key(self):
        """Test getting existing context variable."""
        working = WorkingMemory()
        working.set_context("user_id", "user-456")

        assert working.get_context("user_id") == "user-456"

    def test_get_context_nonexistent_key_returns_none(self):
        """Test getting nonexistent key returns None."""
        working = WorkingMemory()

        assert working.get_context("nonexistent") is None

    def test_get_context_with_default(self):
        """Test getting nonexistent key with default value."""
        working = WorkingMemory()

        value = working.get_context("nonexistent", default="default_value")
        assert value == "default_value"

    def test_has_context_existing(self):
        """Test has_context() for existing key."""
        working = WorkingMemory()
        working.set_context("task_id", "task-123")

        assert working.has_context("task_id") is True

    def test_has_context_nonexistent(self):
        """Test has_context() for nonexistent key."""
        working = WorkingMemory()

        assert working.has_context("nonexistent") is False

    def test_remove_context(self):
        """Test removing context variable."""
        working = WorkingMemory()
        working.set_context("temp", "temporary_data")
        assert working.has_context("temp") is True

        working.remove_context("temp")
        assert working.has_context("temp") is False

    def test_remove_nonexistent_context_no_error(self):
        """Test removing nonexistent key doesn't raise error."""
        working = WorkingMemory()

        # Should not raise error
        working.remove_context("nonexistent")

    def test_get_all_context(self):
        """Test getting all context variables."""
        working = WorkingMemory()
        working.set_context("task_id", "task-123")
        working.set_context("step", 1)
        working.set_context("data", {"key": "value"})

        all_context = working.get_all_context()
        assert len(all_context) == 3
        assert all_context["task_id"] == "task-123"
        assert all_context["step"] == 1
        assert all_context["data"] == {"key": "value"}

    def test_get_all_context_returns_copy(self):
        """Test that get_all_context() returns a copy."""
        working = WorkingMemory()
        working.set_context("task_id", "task-123")

        context1 = working.get_all_context()
        context1["new_key"] = "new_value"

        # Original should be unchanged
        context2 = working.get_all_context()
        assert "new_key" not in context2

    def test_clear_memory(self):
        """Test clearing all context variables."""
        working = WorkingMemory()
        working.set_context("task_id", "task-123")
        working.set_context("step", 1)
        assert len(working) == 2

        working.clear()
        assert len(working) == 0
        assert working.get_all_context() == {}

    def test_update_multiple_variables(self):
        """Test updating multiple variables at once."""
        working = WorkingMemory()

        context = {
            "task_id": "task-123",
            "step": 1,
            "data": {"key": "value"}
        }
        working.update(context)

        assert len(working) == 3
        assert working.get_context("task_id") == "task-123"
        assert working.get_context("step") == 1
        assert working.get_context("data") == {"key": "value"}

    def test_update_overwrites_existing(self):
        """Test that update() overwrites existing values."""
        working = WorkingMemory()
        working.set_context("task_id", "task-old")

        working.update({"task_id": "task-new"})
        assert working.get_context("task_id") == "task-new"

    def test_len_operator(self):
        """Test len() operator."""
        working = WorkingMemory()
        assert len(working) == 0

        working.set_context("key1", "value1")
        assert len(working) == 1

        working.set_context("key2", "value2")
        assert len(working) == 2

    def test_contains_operator(self):
        """Test 'in' operator."""
        working = WorkingMemory()
        working.set_context("task_id", "task-123")

        assert "task_id" in working
        assert "nonexistent" not in working

    def test_repr(self):
        """Test string representation."""
        working = WorkingMemory()
        working.set_context("key1", "value1")
        working.set_context("key2", "value2")

        repr_str = repr(working)
        assert "WorkingMemory" in repr_str
        assert "variables=2" in repr_str
