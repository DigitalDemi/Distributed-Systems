from enum import Enum
from dataclasses import dataclass


class ClientType(Enum):
    REAL_USER = "real_user"
    SIMULATED = "simulated"
    VIRTUAL_SOCKET = "virtual_socket"


@dataclass
class ClientConfig:
    client_type: ClientType
    count: int
    base_port: int = 5000
