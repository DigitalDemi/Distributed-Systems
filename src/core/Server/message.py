from dataclasses import dataclass
from typing import Any
from src.core.Server.message_type import MessageType

@dataclass
class Message:
    type: MessageType
    data: dict[str, Any]
    sender_id: str
