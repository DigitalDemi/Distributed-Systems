from src.core.Client.client import Client
from src.core.Server.message import Message
from src.core.Server.message_type import MessageType
from src.core.Market.item_type import ItemType
from src.core.Server.client_type import ClientType
from src.core.Queue.event import Event
from src.core.Queue.event_type import EventType

import random
import logging
from typing import Optional
from datetime import datetime


class SimulatedClient(Client):
    def __init__(self, node_id: str, controller):
        super().__init__("localhost", 5000)
        self.node_id = node_id
        self.controller = controller
        self.registered = False
        self.mock_socket = True
        self.available_items = []
        self.last_purchase_time = None
        self.purchase_history = []
        self.setup_logging()

    def setup_logging(self):
        self.logger = logging.getLogger(f"SimClient_{self.node_id}")
        self.logger.setLevel(logging.INFO)

    def register(self) -> None:
        """Register as simulated buyer with server"""
        if self.connected and not self.registered:
            register_msg = Message(
                type=MessageType.REGISTER,
                data={"client_type": ClientType.BUYER.value},
                sender_id="unregistered",
            )
            try:
                self.send_message(register_msg)
                self.registered = True
                self.logger.info(f"Simulated client {self.node_id} registered")
            except Exception as e:
                self.logger.error(f"Registration error: {e}")
                raise

    def connect(self) -> None:
        """Override connect to avoid real socket connection"""
        self.connected = True
        self.register()
        self.logger.info(f"Simulated client {self.node_id} connected")

    def send_message(self, message: Message) -> None:
        """Override to use controller's message handling"""
        if not self.connected:
            raise ConnectionError("Not connected")
        self.controller.handle_simulated_message(self, message)

    def simulate_behavior(self):
        """Simulate realistic buyer behavior"""
        try:
            # First, check available items
            if not self.available_items:
                self._request_item_list()
                return

            # Implement different behavior patterns
            behavior = self._select_behavior_pattern()

            match behavior:
                case "opportunistic":
                    self._opportunistic_buying()
                case "cautious":
                    self._cautious_buying()
                case "bulk":
                    self._bulk_buying()
                case "browse":
                    self._browsing_behavior()

        except Exception as e:
            self.logger.error(f"Error in behavior simulation: {e}")

    def _select_behavior_pattern(self) -> str:
        """Select a behavior pattern based on various factors"""
        patterns = {
            "opportunistic": 0.4,  # Buy when stock is high
            "cautious": 0.3,  # Small purchases
            "bulk": 0.2,  # Large purchases
            "browse": 0.1,  # Just look around
        }
        return random.choices(list(patterns.keys()), weights=list(patterns.values()))[0]

    def _opportunistic_buying(self):
        """Buy when stock is good"""
        best_item = self._find_best_stock_item()
        if best_item and best_item["quantity"] > 3:
            self._attempt_purchase(best_item["item_id"], random.uniform(1.0, 2.0))

    def _cautious_buying(self):
        """Make small, careful purchases"""
        available = [item for item in self.available_items if item["quantity"] > 0.5]
        if available:
            item = random.choice(available)
            self._attempt_purchase(item["item_id"], random.uniform(0.5, 1.0))

    def _bulk_buying(self):
        """Make larger purchases"""
        best_item = self._find_best_stock_item()
        if best_item and best_item["quantity"] > 4:
            self._attempt_purchase(best_item["item_id"], random.uniform(2.0, 4.0))

    def _browsing_behavior(self):
        """Just check items without buying"""
        self._request_item_list()
        # Maybe make a small purchase
        if random.random() < 0.2:  # 20% chance
            self._cautious_buying()

    def _find_best_stock_item(self) -> Optional[dict]:
        """Find item with highest stock"""
        if not self.available_items:
            return None
        return max(self.available_items, key=lambda x: x["quantity"])

    def _request_item_list(self):
        """Request current items"""
        list_msg = Message(type=MessageType.LIST_ITEMS, data={}, sender_id=self.node_id)
        self.send_message(list_msg)

    def _attempt_purchase(self, item_id: str, quantity: float):
        """Attempt to purchase an item"""
        # Avoid too frequent purchases
        if self.last_purchase_time:
            time_since_last = (datetime.now() - self.last_purchase_time).total_seconds()
            if time_since_last < 1.0:  # Minimum 1 second between purchases
                return

        message = Message(
            type=MessageType.BUY_REQUEST,
            data={"item_id": item_id, "quantity": quantity},
            sender_id=self.node_id,
        )
        self.send_message(message)
        self.last_purchase_time = datetime.now()
        self.purchase_history.append(
            {
                "timestamp": self.last_purchase_time,
                "item_id": item_id,
                "quantity": quantity,
            }
        )

    def process_update(self, update: Message):
        """Process market updates"""
        try:
            if update.type == MessageType.STOCK_UPDATE:
                self._handle_stock_update(update.data)
            elif update.type == MessageType.LIST_ITEMS:
                self.available_items = update.data.get("items", [])
        except Exception as e:
            self.logger.error(f"Error processing update: {e}")

    def _handle_stock_update(self, data: dict):
        """Handle stock update messages"""
        # Update available items list
        self.available_items = [
            item for item in self.available_items if item["item_id"] != data["item_id"]
        ]
        if data["quantity"] > 0:
            self.available_items.append(data)

    def get_statistics(self) -> dict:
        """Get client statistics"""
        return {
            "total_purchases": len(self.purchase_history),
            "total_quantity": sum(p["quantity"] for p in self.purchase_history),
            "last_purchase": self.last_purchase_time,
            "behavior_patterns": self._select_behavior_pattern(),
        }

    def simulate_purchase(self):
        """Simulate a purchase action"""
        try:
            # First get available items if needed
            if not self.available_items:
                self._request_item_list()
                return  # Wait for next cycle to purchase

            # Select random available item
            if self.available_items:
                item = random.choice(self.available_items)
                quantity = min(
                    random.uniform(0.5, 2.0),
                    item.get("quantity", 0),  # Don't try to buy more than available
                )

                purchase_msg = Message(
                    type=MessageType.BUY_REQUEST,
                    data={"item_id": item["item_id"], "quantity": quantity},
                    sender_id=self.node_id,
                )

                self.logger.debug(f"Simulated purchase request: {purchase_msg.data}")
                self.send_message(purchase_msg)
            else:
                self.logger.warning("No items available for purchase")

        except Exception as e:
            self.logger.error(f"Error in simulate_purchase: {e}")

    def handle_update(self, update):
        """Handle updates from the market"""
        try:
            if isinstance(update, Message):
                self.process_message_update(update)
            elif isinstance(update, Event):
                self.process_event_update(update)
            else:
                self.logger.warning(f"Unknown update type: {type(update)}")
        except Exception as e:
            self.logger.error(f"Error in simulate_purchase: {e}")

    def process_message_update(self, message: Message):
        """Process message updates"""
        try:
            match message.type:
                case MessageType.STOCK_UPDATE:
                    self.logger.debug(f"Stock update received: {message.data}")
                    # Update local state if tracking inventory

                case MessageType.BUY_RESPONSE:
                    success = message.data.get("success", False)
                    if success:
                        self.logger.info(
                            f"Simulated purchase successful: {message.data}"
                        )
                    else:
                        self.logger.warning(
                            f"Simulated purchase failed: {message.data}"
                        )

                case MessageType.ACK:
                    self.logger.debug(f"Acknowledgment received: {message.data}")
                    if "node_id" in message.data:
                        self.node_id = message.data["node_id"]
                        self.registered = True

                case MessageType.ERROR:
                    self.logger.error(f"Error from server: {message.data.get('error')}")

                case _:
                    self.logger.debug(f"Unhandled message type: {message.type}")

        except Exception as e:
            self.logger.error(f"Error processing message update: {e}")

    def process_event_update(self, event: Event):
        """Process event updates"""
        try:
            match event.type:
                case EventType.STOCK_UPDATE:
                    self.logger.debug(f"Stock update event: {event.data}")

                case EventType.BUYER_PURCASE_COMPLETE:
                    self.logger.info(f"Purchase completion event: {event.data}")

                case _:
                    self.logger.debug(f"Unhandled event type: {event.type}")

        except Exception as e:
            self.logger.error(f"Error processing event update: {e}")
