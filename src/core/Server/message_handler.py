from abc import ABC, abstractmethod
import logging
from src.core.Server.server import Server
from src.core.Server.message import Message
from src.core.Server.client import ClientInfo


class MessageHandler(ABC):
    def __init__(self, server: "Server"):
        self.server = server
        self.logger = logging.getLogger(__name__)

    @abstractmethod
    def handle_message(self, message: Message, client_info: ClientInfo) -> None:
        """Handle incoming message"""
        pass
