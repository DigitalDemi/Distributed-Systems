from src.core.Client.client import Client
from src.core.Server.message import Message
from src.core.Server.message_type import MessageType
from src.core.Server.client_type import ClientType
from src.core.Queue.event import Event
from src.core.Queue.event_type import EventType

import time
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

    def process_message_update(self, message: Message) -> None:
        """Process received message updates"""
        try:
            match message.type:
                case MessageType.ACK:
                    if "node_id" in message.data:
                        self.node_id = message.data["node_id"]
                        self.registered = True
                        self.registration_event.set()
                        self.logger.info(f"Registered with ID: {self.node_id}")

                case MessageType.LIST_ITEMS:
                    self.available_items = message.data.get("items", [])
                    with self.response_lock:
                        self.last_response = message
                    self.response_received.set()
                    self.logger.debug(f"Updated items list: {self.available_items}")

                case MessageType.STOCK_UPDATE:
                    self._handle_stock_update(message.data)

                case MessageType.BUY_RESPONSE:
                    with self.response_lock:
                        self.last_response = message
                    self.response_received.set()
                    if message.data.get("success"):
                        self.logger.info("Purchase successful")
                    else:
                        self.logger.warning("Purchase failed")

                case MessageType.ERROR:
                    with self.response_lock:
                        self.last_response = message
                    self.response_received.set()
                    self.logger.error(f"Error from server: {message.data.get('error')}")

        except Exception as e:
            self.logger.error(f"Error processing message update: {e}")

    def register(self) -> bool:
        """Register with the server"""
        try:
            self.logger.info("Attempting registration...")
            register_msg = Message(
                type=MessageType.REGISTER,
                data={"client_type": ClientType.BUYER.value},
                sender_id="unregistered",
            )
            self.send_message(register_msg)

            if not self.registration_event.wait(timeout=5.0):
                raise TimeoutError("Registration timed out")

            self.logger.info(f"Registration complete. Node ID: {self.node_id}")
            return True

        except Exception as e:
            self.logger.error(f"Registration failed: {e}")
            return False

    def list_items(self) -> None:
        """Request list of available items"""
        try:
            list_msg = Message(
                type=MessageType.LIST_ITEMS, data={}, sender_id=self.node_id
            )
            self.send_message(list_msg)

            response = self.wait_for_response()
            if response and response.type == MessageType.ERROR:
                raise RuntimeError(response.data.get("error", "Unknown error"))

        except Exception as e:
            self.logger.error(f"Error listing items: {e}")
            raise

    def buy_item(self, item_id: str, quantity: float) -> None:
        """Send buy request to server"""
        if not self.registered:
            raise RuntimeError("Not registered with server")

        if quantity <= 0:
            raise ValueError("Quantity must be positive")

        try:
            buy_msg = Message(
                type=MessageType.BUY_REQUEST,
                data={"item_id": item_id, "quantity": quantity},
                sender_id=self.node_id,
            )
            self.send_message(buy_msg)

            response = self.wait_for_response()
            if not response:
                raise RuntimeError("No response received from server")

            if response.type == MessageType.ERROR:
                raise RuntimeError(response.data.get("error", "Unknown error"))
            elif response.type == MessageType.BUY_RESPONSE:
                if not response.data.get("success", False):
                    raise RuntimeError("Purchase failed")

        except Exception as e:
            self.logger.error(f"Buy request failed: {e}")
            raise

    def _handle_stock_update(self, item_data: dict) -> None:
        """Handle stock update message"""
        try:
            # Update available items list
            item_id = item_data.get("item_id")
            if not item_id:
                return

            # Remove old entry if exists
            self.available_items = [
                item for item in self.available_items if item.get("item_id") != item_id
            ]

            # Add updated item if it has stock
            if item_data.get("quantity", 0) > 0:
                self.available_items.append(item_data)
                self.logger.debug(f"Updated item: {item_data}")

        except Exception as e:
            self.logger.error(f"Error handling stock update: {e}")

    def attempt_purchase(self, item_name: str, quantity: float):
        """Attempt to purchase an item by name"""
        try:
            # First ensure we have current item list
            self.list_items()
            time.sleep(0.1)  # Brief wait for response

            # Find item by name
            item = None
            for available_item in self.available_items:
                if available_item.get("name", "").lower() == item_name.lower():
                    item = available_item
                    break

            if not item:
                available_names = [i.get("name", "") for i in self.available_items]
                raise ValueError(
                    f"Item {item_name} not found in market. Available: {available_names}"
                )

            # Attempt purchase
            self.logger.info(f"Attempting to purchase {quantity} of {item['name']}")
            self.buy_item(item["item_id"], quantity)

        except Exception as e:
            self.logger.error(f"Error in attempt_purchase: {e}")
            raise
