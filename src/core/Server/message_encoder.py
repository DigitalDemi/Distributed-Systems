import json
from typing import Any
from src.core.Server.message import Message 
from src.core.Server.message_type import MessageType 


class MessageEncoder:
    @staticmethod
    def serialize(message: Message) -> bytes:
        """Convert Message object to bytes for network transmission"""
        msg_dict = {
            "type": message.type.value,
            "data": message.data,
            "sender_id": message.sender_id
        }
        return json.dumps(msg_dict).encode('utf-8')
    
    @staticmethod
    def deserialize(data: bytes) -> Message:
        """Convert received bytes back to Message object"""
        try:
            msg_dict = json.loads(data.decode('utf-8'))
            return Message(
                type=MessageType(msg_dict["type"]),
                data=msg_dict["data"],
                sender_id=msg_dict["sender_id"]
            )
        except Exception as e:
            raise ValueError(f"Failed to deserialize message: {e}")
