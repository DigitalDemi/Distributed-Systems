import threading

from src.core.Client.client import Client
from src.core.Server.market_item import MarketItem
from src.core.Server.message import Message
from src.core.Server.message_type import MessageType
from src.core.Server.client_type import ClientType


class SellerClient(Client):
    def __init__(self, host: str, port: int):
        super().__init__(host, port)
        self.current_item: MarketItem | None = None
        self.sale_timer: threading.Timer | None = None

    def register(self) -> None:
        """Register as seller with server"""
        register_msg = Message(
            type=MessageType.REGISTER,
            data={"client_type": ClientType.SELLER.value},
            sender_id="unregistered"
        )
        self.send_message(register_msg)

    def start_sale(self, item_name: str, quantity: float) -> None:
        """Start selling an item"""
        if self.current_item:
            raise RuntimeError("Already have active sale")
            
        sale_msg = Message(
            type=MessageType.SALE_START,
            data={
                "name": item_name,
                "quantity": quantity
            },
            sender_id=self.node_id
        )
        self.send_message(sale_msg)

    def update_stock(self, quantity: float) -> None:
        """Update current item stock"""
        if not self.current_item:
            raise RuntimeError("No active sale")
            
        update_msg = Message(
            type=MessageType.STOCK_UPDATE,
            data={
                "item_id": self.current_item.item_id,
                "quantity": quantity
            },
            sender_id=self.node_id
        )
        self.send_message(update_msg)

    def end_sale(self) -> None:
        """End current sale"""
        if not self.current_item:
            raise RuntimeError("No active sale")
            
        end_msg = Message(
            type=MessageType.SALE_END,
            data={},
            sender_id=self.node_id
        )
        self.send_message(end_msg)
        self.current_item = None

    def handle_messages(self) -> None:
        """Handle incoming server messages"""
        while self.is_running:
            try:
                message = self.receive_message()
                match message.type:
                    case MessageType.ACK:
                        self.node_id = message.data["node_id"]
                        self.logger.info(f"Registered with ID: {self.node_id}")
                        
                    case MessageType.BUY_RESPONSE:
                        self._handle_buy_response(message.data)
                        
                    case MessageType.SALE_END:
                        self._handle_sale_end()
                        
                    case MessageType.ERROR:
                        self.logger.error(f"Error from server: {message.data['error']}")
                        
            except Exception as e:
                self.logger.error(f"Error handling message: {e}")
                self.is_running = False

    def _handle_buy_response(self, data: dict) -> None:
        """Handle successful purchase"""
        if self.current_item:
            buyer_id = data["buyer_id"]
            quantity = data["quantity"]
            self.logger.info(
                f"Sold {quantity} of {self.current_item.name} to {buyer_id}"
            )
            self.current_item.quantity -= quantity

    def _handle_sale_end(self) -> None:
        """Handle sale ending"""
        self.current_item = None
        if self.sale_timer:
            self.sale_timer.cancel()
            self.sale_timer = None
        self.logger.info("Sale ended")
