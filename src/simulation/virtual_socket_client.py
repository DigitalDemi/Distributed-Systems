from src.core.Client.client import Client
import socket


class VirtualSocketClient(Client):
    def __init__(self, socket: socket.socket, node_id: str, port: int):
        super().__init__("localhost", port)
        self.socket = socket
        self.node_id = node_id

    def connect(self) -> None:
        """Using existing socket"""
        self.connected = True
        self.register()
