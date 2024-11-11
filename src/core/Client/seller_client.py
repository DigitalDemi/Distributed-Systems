from src.core.Client.client import Client
from src.core.Server.message import Message
from src.core.Server.message_type import MessageType
from src.core.Server.client_type import ClientType
from src.core.Market.item_type import ItemType
import logging
import threading
from typing import Optional, Dict


class SellerClient(Client):
    def __init__(self, host: str, port: int):
        super().__init__(host, port)
        self.current_item: Optional[dict] = None
        self.current_stock: Dict[str, float] = {}
        self.logger = logging.getLogger(__name__)
        self.registered = False
        self.registration_event = threading.Event()
        self.message_lock = threading.Lock()
        self.response_received = threading.Event()
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

                case MessageType.SALE_START:
                    if message.data.get("success"):
                        self.current_item = {
                            "item_id": message.data["item_id"],
                            "name": message.data["name"],
                            "quantity": message.data["quantity"],
                            "remaining_time": message.data.get("remaining_time", 60.0),
                        }
                        self.logger.info(f"Sale started: {self.current_item}")
                    with self.response_lock:
                        self.last_response = message
                    self.response_received.set()

                case MessageType.STOCK_UPDATE:
                    self._handle_stock_update(message.data)

                case MessageType.BUY_RESPONSE:
                    self._handle_buy_response(message.data)
                    with self.response_lock:
                        self.last_response = message
                    self.response_received.set()

                case MessageType.SALE_END:
                    self.current_item = None
                    with self.response_lock:
                        self.last_response = message
                    self.response_received.set()
                    self.logger.info("Sale ended")

                case MessageType.ERROR:
                    with self.response_lock:
                        self.last_response = message
                    self.response_received.set()
                    self.logger.error(f"Error from server: {message.data.get('error')}")

        except Exception as e:
            self.logger.error(f"Error processing message update: {e}")

    def register(self) -> None:
        """Register as seller with server"""
        try:
            self.registration_event.clear()
            register_msg = Message(
                type=MessageType.REGISTER,
                data={"client_type": ClientType.SELLER.value},
                sender_id="unregistered",
            )
            self.send_message(register_msg)

            if not self.registration_event.wait(timeout=5.0):
                raise TimeoutError("Registration timed out")

            self.logger.info(f"Registration complete. Node ID: {self.node_id}")

        except Exception as e:
            self.logger.error(f"Registration error: {e}")
            raise

    def start_sale(self, item_name: str, quantity: float) -> None:
        """Start selling an item"""
        if not self.registered:
            raise RuntimeError("Not registered with server")

        if self.current_item:
            raise RuntimeError("Already have active sale")

        try:
            # Validate item type
            item_type = ItemType.from_string(item_name)

            sale_msg = Message(
                type=MessageType.SALE_START,
                data={"name": item_name, "quantity": quantity},
                sender_id=self.node_id,
            )
            self.logger.info(f"Sending sale start request: {sale_msg.data}")
            self.send_message(sale_msg)

            # Wait for response
            response = self.wait_for_response()
            if not response:
                raise RuntimeError("No response received from server")

            if response.type == MessageType.ERROR:
                raise RuntimeError(response.data.get("error", "Unknown error"))

        except Exception as e:
            raise RuntimeError(f"Failed to start sale: {e}")

    def update_stock(self, quantity: float) -> None:
        """Update current item stock"""
        if not self.registered:
            raise RuntimeError("Not registered with server")

        if not self.current_item:
            raise RuntimeError("No active sale")

        if quantity < 0:
            raise ValueError("Quantity cannot be negative")

        try:
            update_msg = Message(
                type=MessageType.STOCK_UPDATE,
                data={"item_id": self.current_item["item_id"], "quantity": quantity},
                sender_id=self.node_id,
            )
            self.send_message(update_msg)

            # Wait for response
            response = self.wait_for_response()
            if response and response.type == MessageType.ERROR:
                raise RuntimeError(response.data.get("error", "Unknown error"))

        except Exception as e:
            raise RuntimeError(f"Failed to update stock: {e}")

    def end_sale(self) -> None:
        """End current sale"""
        if not self.registered:
            raise RuntimeError("Not registered with server")

        if not self.current_item:
            raise RuntimeError("No active sale")

        try:
            end_msg = Message(
                type=MessageType.SALE_END,
                data={"item_id": self.current_item["item_id"]},
                sender_id=self.node_id,
            )
            self.send_message(end_msg)

            # Wait for response
            response = self.wait_for_response()
            if response and response.type == MessageType.ERROR:
                raise RuntimeError(response.data.get("error", "Unknown error"))

            self.current_item = None

        except Exception as e:
            raise RuntimeError(f"Failed to end sale: {e}")

    def _handle_buy_response(self, data: dict) -> None:
        """Handle successful purchase"""
        if self.current_item:
            quantity = data.get("quantity", 0)
            buyer_id = data.get("buyer_id", "unknown")
            self.logger.info(
                f"Sold {quantity} of {self.current_item['name']} to {buyer_id}"
            )
            self.current_item["quantity"] -= quantity

    def _handle_stock_update(self, data: dict) -> None:
        """Handle stock update"""
        try:
            if (
                self.current_item
                and data.get("item_id") == self.current_item["item_id"]
            ):
                self.current_item.update(
                    {
                        "quantity": data["quantity"],
                        "remaining_time": data.get("remaining_time", 60.0),
                    }
                )
                self.logger.debug(f"Updated stock: {self.current_item}")
        except Exception as e:
            self.logger.error(f"Error handling stock update: {e}")
