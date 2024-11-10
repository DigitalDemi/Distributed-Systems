import socket
import logging
import threading
from typing import Optional

from src.core.Server.message import Message
from src.core.Server.message_encoder import MessageEncoder


class Client:
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port
        self.socket: Optional[socket.socket] = None
        self.node_id: Optional[str] = None
        self.is_running = False
        self.message_thread: Optional[threading.Thread] = None
        self.logger = logging.getLogger(__name__)
        self.response_received = threading.Event()
        self.response_lock = threading.Lock()
        self.last_response: Optional[Message] = None

    def connect(self) -> None:
        """Connect to server"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))
            self.is_running = True

        except Exception as e:
            self.logger.error(f"Connection failed: {e}")
            raise

    def disconnect(self) -> None:
        """Disconnect from server"""
        self.is_running = False
        if self.socket:
            try:
                self.socket.close()
            except:
                pass
            self.socket = None

    def send_message(self, message: Message) -> None:
        """Send message to server"""
        try:
            if not self.socket:
                raise RuntimeError("Not connected to server")

            data = MessageEncoder.serialize(message)
            length = len(data)
            self.socket.send(length.to_bytes(4, byteorder="big"))
            self.socket.send(data)

        except Exception as e:
            self.logger.error(f"Failed to send message: {e}")
            raise

    def receive_message(self) -> Message:
        """Receive message from server"""
        try:
            if not self.socket:
                raise RuntimeError("Not connected to server")

            length_bytes = self.socket.recv(4)
            if not length_bytes:
                raise ConnectionError("Server closed connection")

            length = int.from_bytes(length_bytes, byteorder="big")

            data = b""
            while len(data) < length:
                chunk = self.socket.recv(min(length - len(data), 4096))
                if not chunk:
                    raise ConnectionError("Connection closed during receive")
                data += chunk

            return MessageEncoder.deserialize(data)

        except Exception as e:
            self.logger.error(f"Failed to receive message: {e}")
            raise

    def start_message_handling(self) -> None:
        """Start message handling thread"""
        if self.message_thread is None or not self.message_thread.is_alive():
            self.message_thread = threading.Thread(target=self.handle_messages)
            self.message_thread.daemon = True
            self.message_thread.start()

    def handle_messages(self) -> None:
        while self.is_running:
            try:
                message = self.receive_message()
                self.logger.debug(f"Received message: {message.type}")

                # Store response and notify waiters
                with self.response_lock:
                    self.last_response = message
                self.response_received.set()

            except Exception as e:
                self.logger.error(f"Error handling message: {e}")
                self.is_running = False

    def wait_for_response(self, timeout: float = 5.0) -> Optional[Message]:
        """Wait for a response from the server"""
        try:
            self.response_received.clear()
            if not self.response_received.wait(timeout=timeout):
                raise RuntimeError("Server did not respond in time")
            with self.response_lock:
                response = self.last_response
                self.last_response = None
                return response
        finally:
            self.response_received.clear()
