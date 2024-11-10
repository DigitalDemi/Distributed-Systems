from src.core.Client.client import Client
from src.core.Server.market_item import MarketItem
from src.core.Server.message import Message
from src.core.Server.message_type import MessageType
from src.core.Server.client_type import ClientType

class BuyerClient(Client):
    def __init__(self, host: str, port: int):
        super().__init__(host, port)
        self.available_items: list[MarketItem] = []

    def register(self) -> None:
        """Register as buyer with server"""
        register_msg = Message(
            type=MessageType.REGISTER,
            data={"client_type": ClientType.BUYER.value},
            sender_id="unregistered"
        )
        self.send_message(register_msg)

    def list_items(self) -> None:
        """Request list of available items"""
        list_msg = Message(
            type=MessageType.LIST_ITEMS,
            data={},
            sender_id=self.node_id
        )
        self.send_message(list_msg)

    def buy_item(self, item_id: str, quantity: float) -> None:
        """Send buy request to server"""
        buy_msg = Message(
            type=MessageType.BUY_REQUEST,
            data={"item_id": item_id, "quantity": quantity},
            sender_id=self.node_id
        )
        self.send_message(buy_msg)

    def handle_messages(self) -> None:
        """Handle incoming server messages"""
        while self.is_running:
            try:
                message = self.receive_message()
                match message.type:
                    case MessageType.ACK:
                        self.node_id = message.data["node_id"]
                        self.logger.info(f"Registered with ID: {self.node_id}")
                        
                    case MessageType.LIST_ITEMS:
                        self.available_items = [
                            MarketItem(**item_data) 
                            for item_data in message.data["items"]
                        ]
                        self.logger.info("Updated available items")
                        
                    case MessageType.STOCK_UPDATE:
                        self._handle_stock_update(message.data)
                        
                    case MessageType.ERROR:
                        self.logger.error(f"Error from server: {message.data['error']}")
                        
            except Exception as e:
                self.logger.error(f"Error handling message: {e}")
                self.is_running = False

    def _handle_stock_update(self, item_data: dict) -> None:
        """Handle stock update message"""
        updated_item = MarketItem(**item_data)
        # Update local item list
        self.available_items = [
            item for item in self.available_items 
            if item.item_id != updated_item.item_id
        ]
        if updated_item.quantity > 0:
            self.available_items.append(updated_item)
