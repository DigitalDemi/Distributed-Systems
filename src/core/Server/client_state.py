from enum import Enum


class ClientState(Enum):
    CONNECTED = "connected"
    REGISTERED = "registered"
    ACTIVE = "active"
    INACTIVE = "inactive"
    DISCONNECTED = "disconnected"
