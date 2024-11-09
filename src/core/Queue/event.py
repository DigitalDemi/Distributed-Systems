from dataclasses import dataclass
from typing import  Any
from core.Queue.event_type import EventType

@dataclass
class Event:
    type: EventType
    data : dict[str, Any]
    time : float
    sender_id : str

