from src.core.Client.client import Client
from src.core.Server.message import Message
from src.core.Server.message_type import MessageType
from src.core.Server.client_type import ClientType
import logging
import threading
from typing import List, Optional

class BuyerClient(Client):
    def __init__(self, host: str, port: int):
        super().__init__(host, port)
        self.available_items: List[dict] = []
        self.logger = logging.getLogger(__name__)
        self.registered = False
        self.registration_event = threading.Event()
        self.response_received = threading.Event()
        self.response_lock = threading.Lock()
        self.last_response: Optional[Message] = None

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

    def register(self) -> None:
        """Register as buyer with server"""
        try:
            self.registration_event.clear()
            register_msg = Message(
                type=MessageType.REGISTER,
                data={"client_type": ClientType.BUYER.value},
                sender_id="unregistered"
            )
            self.send_message(register_msg)
            
            # Start message handling thread
            self.start_message_handling()
            
            if not self.registration_event.wait(timeout=5.0):
                raise RuntimeError("Registration timed out")
            
        except Exception as e:
            self.logger.error(f"Registration error: {e}")
            raise

    def list_items(self) -> None:
        """Request list of available items"""
        if not self.registered:
            raise RuntimeError("Not registered with server")

        list_msg = Message(
            type=MessageType.LIST_ITEMS,
            data={},
            sender_id=self.node_id
        )
        self.send_message(list_msg)
        
        # Wait for response
        response = self.wait_for_response()
        if response and response.type == MessageType.LIST_ITEMS:
            self.available_items = response.data.get("items", [])

    def buy_item(self, item_id: str, quantity: float) -> None:
        """Send buy request to server"""
        if not self.registered:
            raise RuntimeError("Not registered with server")
            
        if quantity <= 0:
            raise ValueError("Quantity must be positive")

        buy_msg = Message(
            type=MessageType.BUY_REQUEST,
            data={
                "item_id": item_id,
                "quantity": quantity
            },
            sender_id=self.node_id
        )
        self.send_message(buy_msg)
        
        # Wait for response
        response = self.wait_for_response()
        if response and response.type == MessageType.ERROR:
            raise RuntimeError(response.data["error"])

    def handle_messages(self) -> None:
        """Handle incoming server messages"""
        while self.is_running:
            try:
                message = self.receive_message()
                self.logger.debug(f"Received message: {message.type}")
                
                match message.type:
                    case MessageType.ACK:
                        self.node_id = message.data["node_id"]
                        self.registered = True
                        self.registration_event.set()
                        self.logger.info(f"Registered with ID: {self.node_id}")
                        
                    case MessageType.LIST_ITEMS | MessageType.ERROR | \
                         MessageType.BUY_RESPONSE:
                        with self.response_lock:
                            self.last_response = message
                        self.response_received.set()
                        
                    case MessageType.STOCK_UPDATE:
                        self._handle_stock_update(message.data)
                        
            except Exception as e:
                self.logger.error(f"Error handling message: {e}")
                self.is_running = False

    def _handle_stock_update(self, item_data: dict) -> None:
        """Handle stock update message"""
        # Update available items list
        self.available_items = [
            item for item in self.available_items 
            if item["item_id"] != item_data["item_id"]
        ]
        if item_data["quantity"] > 0:
            self.available_items.append(item_data)
            self.logger.debug(f"Updated item: {item_data}")

    def get_item_by_id(self, item_id: str) -> Optional[dict]:
        """Get item details by ID"""
        return next((item for item in self.available_items if item["item_id"] == item_id), None)
