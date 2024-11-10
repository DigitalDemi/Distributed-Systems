from src.core.Client.client import Client
from src.core.Server.message import Message
from src.core.Server.message_type import MessageType
from src.core.Server.client_type import ClientType
from src.core.Market.item_type import ItemType
import logging
import threading
import queue
from typing import Optional


class SellerClient(Client):
    def __init__(self, host: str, port: int):
        super().__init__(host, port)
        # Initialize all attributes
        self.current_item: Optional[dict] = None
        self.logger = logging.getLogger(__name__)
        self.registered = False
        self.message_queue = queue.Queue()

        # Events for synchronization
        self.registration_event = threading.Event()
        self.response_lock = threading.Lock()
        self.response_received = threading.Event()
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
        """Register as seller with server"""
        try:
            self.registration_event.clear()
            register_msg = Message(
                type=MessageType.REGISTER,
                data={"client_type": ClientType.SELLER.value},
                sender_id="unregistered",
            )
            self.send_message(register_msg)

            # Start message handling
            self.start_message_handling()

            if not self.registration_event.wait(timeout=5.0):
                raise RuntimeError("Registration timed out")

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
            ItemType.from_string(item_name)

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
                raise RuntimeError(response.data["error"])
            elif response.type == MessageType.SALE_START:
                if not response.data.get("success"):
                    raise RuntimeError("Sale start failed")
                self.current_item = {
                    "item_id": response.data["item_id"],
                    "name": response.data["name"],
                    "quantity": response.data["quantity"],
                    "remaining_time": response.data.get("remaining_time", 60.0),
                }
                self.logger.info("Sale started successfully")
            else:
                raise RuntimeError(f"Unexpected response type: {response.type}")

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

        update_msg = Message(
            type=MessageType.STOCK_UPDATE,
            data={"item_id": self.current_item["item_id"], "quantity": quantity},
            sender_id=self.node_id,
        )
        self.send_message(update_msg)

        # Wait for response
        response = self.wait_for_response()
        if response and response.type == MessageType.ERROR:
            raise RuntimeError(response.data["error"])

    def end_sale(self) -> None:
        """End current sale"""
        if not self.registered:
            raise RuntimeError("Not registered with server")

        if not self.current_item:
            raise RuntimeError("No active sale")

        end_msg = Message(type=MessageType.SALE_END, data={}, sender_id=self.node_id)
        self.send_message(end_msg)

        # Wait for response
        response = self.wait_for_response()
        if response and response.type == MessageType.ERROR:
            raise RuntimeError(response.data["error"])

        self.current_item = None

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

                    case MessageType.SALE_START:
                        if message.data.get("success"):
                            self.current_item = {
                                "item_id": message.data["item_id"],
                                "name": message.data["name"],
                                "quantity": message.data["quantity"],
                                "remaining_time": message.data.get(
                                    "remaining_time", 60.0
                                ),
                            }
                            self.logger.info(
                                f"Sale started successfully: {self.current_item}"
                            )
                        with self.response_lock:
                            self.last_response = message
                        self.response_received.set()

                    case MessageType.STOCK_UPDATE:
                        # Only update our item if it matches
                        if self.current_item and message.data.get(
                            "item_id"
                        ) == self.current_item.get("item_id"):
                            self.current_item.update(
                                {
                                    "quantity": message.data["quantity"],
                                    "remaining_time": message.data.get(
                                        "remaining_time", 60.0
                                    ),
                                }
                            )
                            self.logger.debug(
                                f"Updated item status: {self.current_item}"
                            )

                    case MessageType.BUY_RESPONSE:
                        self._handle_buy_response(message.data)

                    case MessageType.ERROR:
                        self.logger.error(f"Error from server: {message.data['error']}")
                        with self.response_lock:
                            self.last_response = message
                        self.response_received.set()

                    case MessageType.SALE_END:
                        self._handle_sale_end()
                        with self.response_lock:
                            self.last_response = message
                        self.response_received.set()

            except Exception as e:
                self.logger.error(f"Error handling message: {e}")
                self.is_running = False

    def _handle_buy_response(self, data: dict) -> None:
        """Handle successful purchase"""
        if self.current_item:
            buyer_id = data["buyer_id"]
            quantity = data["quantity"]
            self.logger.info(
                f"Sold {quantity} of {self.current_item['name']} to {buyer_id}"
            )
            self.current_item["quantity"] -= quantity

    def _display_status(self) -> None:
        """Display current sale status"""
        if not self.current_item:
            print("\nNo active sale")
            return

        print("\nCurrent Sale:")
        print(f"Item: {self.current_item['name']}")
        print(f"Quantity: {self.current_item['quantity']}")
        print(f"Time remaining: {self.current_item.get('remaining_time', 0):.1f}s")
