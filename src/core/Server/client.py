from dataclasses import dataclass
import socket
from src.core.Server.client_type import ClientType
from src.core.Server.client_state import ClientState



@dataclass
class ClientInfo:
    socket : socket.socket
    address: tuple[str,int]
    client_type: ClientType | None = None
    state: ClientState = ClientState.CONNECTED
    node_id: str | None = None

