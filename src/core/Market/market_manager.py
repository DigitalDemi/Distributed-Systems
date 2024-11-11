import logging
import time
import threading
from threading import Lock
from typing import Dict, List, Optional
from src.core.Market.item_type import ItemType
from src.core.Market.market_item import MarketItem
from src.core.Market.item_stock import ItemStock


class MarketManager:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._lock = Lock()
        self.active_items: Dict[str, MarketItem] = {}
        self.seller_stocks: Dict[str, Dict[ItemType, ItemStock]] = {}
        self.logger.info("Initializing market manager")
        self.initialize_market_items()

    def initialize_market_items(self):
        """Initialize the market with basic items"""
        with self._lock:
            try:
                for item_type in ItemType:
                    item_id = f"market_{item_type.value}"
                    item = MarketItem(
                        item_id=item_id,
                        item_type=item_type,
                        quantity=5.0,
                        seller_id="market",
                        max_sale_duration=60,
                    )
                    self.active_items[item_id] = item
                    self.logger.info(f"Initialized market item: {item.to_dict()}")
            except Exception as e:
                self.logger.error(f"Error initializing market items: {e}")
                raise

    def initialize_seller_stock(self, seller_id: str, initial_quantity: float = 5.0):
        """Initialize a seller's stock"""
        with self._lock:
            if seller_id in self.seller_stocks:
                return  # Already initialized

            self.seller_stocks[seller_id] = {}
            for item_type in ItemType:
                self.seller_stocks[seller_id][item_type] = ItemStock(
                    item_type=item_type,
                    quantity=initial_quantity,
                    max_quantity=initial_quantity,
                )
            self.logger.info(f"Initialized stock for seller {seller_id}")

    def get_active_items(self) -> List[dict]:
        """Get list of all active items"""
        with self._lock:
            items = []
            for item in self.active_items.values():
                if not item.is_expired():
                    try:
                        items.append(item.to_dict())
                    except Exception as e:
                        self.logger.error(f"Error serializing item: {e}")
            return items

    def try_purchase(self, item_id: str, quantity: float) -> bool:
        """Attempt to purchase an item"""
        with self._lock:
            if item_id not in self.active_items:
                raise ValueError(f"Item {item_id} not found")

            item = self.active_items[item_id]
            if item.is_expired():
                raise ValueError("Item sale has expired")

            return item.try_purchase(quantity)

    def start_sale(
        self, seller_id: str, item_type: ItemType, quantity: float
    ) -> MarketItem:
        """Start a new sale"""
        with self._lock:
            # Validate seller and check stock
            if seller_id not in self.seller_stocks:
                raise ValueError(f"Seller {seller_id} not found")

            seller_stock = self.seller_stocks[seller_id]
            if item_type not in seller_stock:
                raise ValueError(f"Seller does not have {item_type.value} in stock")

            stock = seller_stock[item_type]
            if stock.quantity < quantity:
                raise ValueError(f"Insufficient stock for {item_type.value}")

            # Create new sale
            item_id = f"sale_{seller_id}_{int(time.time())}"
            item = MarketItem(
                item_id=item_id,
                item_type=item_type,
                quantity=quantity,
                seller_id=seller_id,
            )

            # Update stock and add to active items
            stock.quantity -= quantity
            self.active_items[item_id] = item

            self.logger.info(f"Started sale: {item.to_dict()}")
            return item

    def end_sale(self, item_id: str) -> None:
        """End a sale"""
        with self._lock:
            if item_id not in self.active_items:
                return

            item = self.active_items[item_id]
            if item.quantity > 0 and item.seller_id in self.seller_stocks:
                # Return unsold quantity to stock
                seller_stock = self.seller_stocks[item.seller_id]
                if item.item_type in seller_stock:
                    stock = seller_stock[item.item_type]
                    stock.quantity += item.quantity

            del self.active_items[item_id]
            self.logger.info(f"Ended sale: {item_id}")

    def get_seller_stock(self, seller_id: str) -> Dict[str, float]:
        """Get current stock levels for a seller"""
        with self._lock:
            if seller_id not in self.seller_stocks:
                raise ValueError(f"Seller {seller_id} not found")

            return {
                item_type.value: stock.quantity
                for item_type, stock in self.seller_stocks[seller_id].items()
            }

    def handle_buy_request(self, item_id: str, quantity: float, buyer_id: str) -> bool:
        """Handle a buy request"""
        with self._lock:
            try:
                if item_id not in self.active_items:
                    self.logger.warning(f"Item {item_id} not found for purchase")
                    return False

                result = self.try_purchase(item_id, quantity)
                if result:
                    self.logger.info(
                        f"Buyer {buyer_id} purchased {quantity} of {item_id}"
                    )
                return result
            except Exception as e:
                self.logger.error(f"Error processing buy request: {e}")
                return False

    def get_market_status(self) -> dict:
        """Get current market status"""
        with self._lock:
            active_items = self.get_active_items()
            return {
                "active_items": len(active_items),
                "items": active_items,
                "sellers": len(self.seller_stocks),
                "total_quantity": sum(item["quantity"] for item in active_items),
            }

    def cleanup_expired_items(self) -> None:
        """Remove expired items"""
        with self._lock:
            expired = [
                item_id
                for item_id, item in self.active_items.items()
                if item.is_expired()
            ]
            for item_id in expired:
                self.end_sale(item_id)
