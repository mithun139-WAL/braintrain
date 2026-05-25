import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

logger = logging.getLogger("conversation_memory")

@dataclass
class ConversationMessage:
    role: str  # user, assistant, system, panelist
    content: str
    speaker: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.utcnow)
    metadata: dict = field(default_factory=dict)

class ConversationMemory:
    def __init__(self, messages: list[ConversationMessage] = None, max_messages: int = 20):
        """
        Manages live conversation memory.
        
        :param messages: Initial message list.
        :param max_messages: Max number of messages to retain before trimming (excludes system message).
        """
        self._messages = messages or []
        self._max_messages = max_messages

    def add_user_message(self, content: str, speaker: str = "Candidate", metadata: dict = None) -> None:
        msg = ConversationMessage(
            role="user",
            content=content,
            speaker=speaker,
            timestamp=datetime.utcnow(),
            metadata=metadata or {},
        )
        self._messages.append(msg)
        self.trim()

    def add_agent_message(self, content: str, speaker: str = "Interviewer", metadata: dict = None) -> None:
        msg = ConversationMessage(
            role="assistant",
            content=content,
            speaker=speaker,
            timestamp=datetime.utcnow(),
            metadata=metadata or {},
        )
        self._messages.append(msg)
        self.trim()

    def get_messages(self) -> list[ConversationMessage]:
        return self._messages

    def clear(self) -> None:
        self._messages.clear()

    def trim(self) -> None:
        """
        Trims older messages if the log exceeds max_messages.
        Always preserves the system message at index 0.
        """
        total_count = len(self._messages)
        if total_count <= self._max_messages:
            return

        has_system = total_count > 0 and self._messages[0].role == "system"
        start_idx = 1 if has_system else 0
        
        # Calculate how many message inputs need to be pruned
        excess = len(self._messages) - self._max_messages
        pruned_msgs = self._messages[start_idx + excess:]

        if has_system:
            self._messages = [self._messages[0]] + pruned_msgs
        else:
            self._messages = pruned_msgs

        logger.info("memory_trimmed | old_count: %d | new_count: %d", total_count, len(self._messages))
