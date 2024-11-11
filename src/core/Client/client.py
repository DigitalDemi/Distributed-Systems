import socket
import logging
import threading
import time
from typing import Optional
from abc import ABC, abstractmethod

from src.core.Server.message import Message
from src.core.Server.message_encoder import MessageEncoder
from src.core.Market.item_type import ItemType


class Client(ABC):
    def __init__(self, host: str, port: int):
        self.host = host
        self.port = port
        self.socket: Optional[socket.socket] = None
        self.node_id: Optional[str] = None
        self.is_running = False
        self.connected = False
        self.message_thread: Optional[threading.Thread] = None
        self.logger = logging.getLogger(__name__)
        self.response_received = threading.Event()
        self.response_lock = threading.Lock()
        self.last_response: Optional[Message] = None
        self.MAX_RETRY_ATTEMPTS = 3
        self.RETRY_DELAY = 0.5
        self.SOCKET_TIMEOUT = 5.0


    def connect(self) -> None:
        """Connect to server"""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.host, self.port))
            self.is_running = True
            self.connected = True
            self.logger.info(f"Connected to server at {self.host}:{self.port}")

            self.message_thread = threading.Thread(target=self.handle_messages)
            self.message_thread.daemon = True
            self.message_thread.start()

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
        self.connected = False
        self.logger.info("Disconnected from server")


    def send_message(self, message: Message) -> None:
        """Send message with retry logic"""
        if not self.socket or not self.connected:
            raise ConnectionError("Not connected to server")
            
        attempts = 0
        last_error = None
        
        while attempts < self.MAX_RETRY_ATTEMPTS:
            try:
                data = MessageEncoder.serialize(message)
                length = len(data)
                self.socket.send(length.to_bytes(4, byteorder="big"))
                self.socket.send(data)
                self.logger.debug(f"Sent message: {message.type}")
                return
            except Exception as e:
                last_error = e
                attempts += 1
                if attempts < self.MAX_RETRY_ATTEMPTS:
                    time.sleep(self.RETRY_DELAY)
                    self.logger.debug(f"Retrying send, attempt {attempts}")
                    
        self.logger.error(f"Failed to send message after {attempts} attempts")
        raise last_error
    
    def receive_message(self) -> Message:
        """Receive message with timeout handling"""
        try:
            if not self.socket:
                raise RuntimeError("Not connected to server")

            self.socket.settimeout(self.SOCKET_TIMEOUT)
            
            # Receive message length
            length_bytes = self.socket.recv(4)
            if not length_bytes:
                raise ConnectionError("Server closed connection")

            length = int.from_bytes(length_bytes, byteorder="big")
            
            # Receive message data with progress tracking
            data = bytearray()
            bytes_received = 0
            while bytes_received < length:
                chunk_size = min(4096, length - bytes_received)
                chunk = self.socket.recv(chunk_size)
                if not chunk:
                    raise ConnectionError("Connection closed during receive")
                data.extend(chunk)
                bytes_received += len(chunk)

            self.socket.settimeout(None)  # Reset timeout
            
            message = MessageEncoder.deserialize(bytes(data))
            self.logger.debug(f"Received message: {message.type}")
            return message

        except socket.timeout:
            raise TimeoutError("Server did not respond in time")
        except Exception as e:
            self.logger.error(f"Failed to receive message: {e}")
            raise


    def handle_messages(self) -> None:
        """Handle incoming messages"""
        while self.is_running:
            try:
                message = self.receive_message()
                self.process_message_update(message)

                # Also store as last response for those waiting
                with self.response_lock:
                    self.last_response = message
                self.response_received.set()

            except ConnectionError:
                self.logger.error("Lost connection to server")
                self.is_running = False
                break
            except Exception as e:
                self.logger.error(f"Error handling message: {e}")
                continue

    def wait_for_response(self, timeout: float = 5.0) -> Optional[Message]:
        """Wait for response with improved timeout handling"""
        try:
            self.response_received.clear()
            
            # Wait in smaller intervals to allow for interruption
            remaining_time = timeout
            while remaining_time > 0:
                if self.response_received.wait(timeout=min(0.5, remaining_time)):
                    with self.response_lock:
                        response = self.last_response
                        self.last_response = None
                        return response
                remaining_time -= 0.5
                
            raise TimeoutError("Server did not respond in time")
            
        finally:
            self.response_received.clear()

    @abstractmethod
    def process_message_update(self, message: Message) -> None:
        """Process received message updates - must be implemented by subclasses"""
        pass
