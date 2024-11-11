import logging
import random
import time
from src.core.Client.client import Client
from src.core.Server.message import Message
from src.core.Server.message_type import MessageType
from src.core.Server.client_type import ClientType
from src.core.Market.item_type import ItemType


class SimulatedSeller(Client):
    def __init__(self, node_id: str, controller, behavior: dict | None = None):
        super().__init__("localhost", 5000)
        self.node_id = node_id
        self.controller = controller
        self.behavior = behavior or {
            "specialty": random.choice(list(ItemType)),
            "restock_rate": 0.15,
            "quantity_range": (3.0, 8.0),
            "sale_duration": 45,
        }
        self.registered = False
        self.current_sale = None
        self.logger = logging.getLogger(f"SimSeller_{self.node_id}")

    def start_new_sale(self):
        """Start selling a new item"""
        try:
            if self.current_sale:
                return  # Already has active sale

            # Choose item based on behavior
            min_qty, max_qty = self.behavior["quantity_range"]
            quantity = random.uniform(min_qty, max_qty)

            sale_msg = Message(
                type=MessageType.SALE_START,
                data={
                    "name": self.behavior["specialty"].value,
                    "quantity": quantity,
                    "duration": self.behavior["sale_duration"],
                },
                sender_id=self.node_id,
            )

            self.logger.info(
                f"Starting sale: {self.behavior['specialty'].value}, quantity: {quantity}"
            )
            self.send_message(sale_msg)

        except Exception as e:
            self.logger.error(f"Error starting sale: {e}")

    def process_message_update(self, message: Message):
        """Process message updates"""
        try:
            match message.type:
                case MessageType.ACK:
                    if "node_id" in message.data:
                        self.registered = True
                        self.node_id = message.data["node_id"]
                        self.logger.info(f"Seller registered: {self.node_id}")
                        # Start initial sale after registration
                        self.start_new_sale()

                case MessageType.SALE_START:
                    if message.data.get("success"):
                        self.current_sale = {
                            "item_id": message.data["item_id"],
                            "name": message.data["name"],
                            "quantity": message.data["quantity"],
                            "start_time": time.time(),
                        }
                        self.logger.info(f"Sale started: {self.current_sale}")

                case MessageType.BUY_RESPONSE:
                    if self.current_sale:
                        self.current_sale["quantity"] -= message.data.get("quantity", 0)
                        self.logger.info(f"Item sold: {message.data}")

                case MessageType.SALE_END:
                    self.current_sale = None
                    # Start new sale after small delay
                    time.sleep(random.uniform(1, 3))
                    self.start_new_sale()

                case MessageType.ERROR:
                    self.logger.error(f"Error from server: {message.data.get('error')}")

        except Exception as e:
            self.logger.error(f"Error processing message update: {e}")

    def send_message(self, message: Message) -> None:
        """Override to use controller's message handling"""
        if not self.connected:
            raise ConnectionError("Not connected")
        self.controller.handle_simulated_message(self, message)
