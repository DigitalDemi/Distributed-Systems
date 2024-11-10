import logging
import time
from threading import Lock, Timer
from typing import Optional, Dict, List
from src.core.Market.item_type import ItemType
from src.core.Market.item_stock import ItemStock
from src.core.Market.market_item import MarketItem

class MarketManager:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._lock = Lock()
        self.active_items: Dict[str, MarketItem] = {}
        self.seller_stocks: Dict[str, Dict[ItemType, ItemStock]] = {}
        self.item_rotation_timers: Dict[str, Timer] = {}
        
    def initialize_seller_stock(self, seller_id: str, initial_quantity: float = 5.0):
        """Initialize a seller's stock with all item types"""
        with self._lock:
            if initial_quantity <= 0:
                raise ValueError("Initial quantity must be positive")
                
            if seller_id in self.seller_stocks:
                self.logger.warning(f"Reinitializing stock for seller {seller_id}")
                
            self.seller_stocks[seller_id] = {}
            for item_type in ItemType:
                self.seller_stocks[seller_id][item_type] = ItemStock(
                    item_type=item_type,
                    quantity=initial_quantity,
                    max_quantity=initial_quantity
                )
            self.logger.info(f"Initialized stock for seller {seller_id} with {initial_quantity} units each")

    def start_sale(self, seller_id: str, item_type: ItemType, quantity: float) -> MarketItem:
        """Start a new sale for a seller"""
        with self._lock:
            # Check if seller exists
            if seller_id not in self.seller_stocks:
                raise RuntimeError(f"Seller {seller_id} not found. Have they registered?")
                
            # Check for existing sales
            existing_items = [item for item in self.active_items.values() 
                            if item.seller_id == seller_id]
            if existing_items:
                raise RuntimeError("Seller already has an active sale")
                
            # Get seller's stock
            stock = self.seller_stocks[seller_id].get(item_type)
            if not stock:
                raise RuntimeError(f"No stock found for item type {item_type.value}")
                
            # Check quantity
            if quantity <= 0:
                raise ValueError("Quantity must be positive")
            if quantity > stock.quantity:
                raise ValueError(f"Insufficient stock. Available: {stock.quantity}")
                
            # Create new item
            item_id = f"item_{seller_id}_{time.time()}"
            new_item = MarketItem(
                item_id=item_id,
                item_type=item_type,
                quantity=quantity,
                seller_id=seller_id
            )
            
            # Update stock and add item
            stock.quantity -= quantity
            self.active_items[item_id] = new_item
            
            # Start expiration timer
            self._start_expiration_timer(new_item)
            
            self.logger.info(f"Started sale for seller {seller_id}: {quantity} units of {item_type.value}")
            return new_item
            
            
    def end_sale(self, item_id: str, auto_rotate: bool = True) -> Optional[MarketItem]:
        """End a sale and optionally start next item"""
        with self._lock:
            item = self.active_items.get(item_id)
            if not item:
                return None
                
            # Return unsold quantity to stock
            if item.quantity > 0:
                stock = self.seller_stocks[item.seller_id][item.item_type]
                stock.quantity += item.quantity
                
            # Remove item
            del self.active_items[item_id]
            
            # Cancel timer if exists
            if item_id in self.item_rotation_timers:
                self.item_rotation_timers[item_id].cancel()
                del self.item_rotation_timers[item_id]
                
            # Auto-rotate to next item if enabled
            next_item = None
            if auto_rotate:
                next_item = self._start_next_item(item.seller_id)
                
            return next_item
            
    def try_purchase(self, item_id: str, quantity: float) -> bool:
        """Attempt to purchase an item"""
        item = self.active_items.get(item_id)
        if not item:
            raise RuntimeError("Item not found")
            
        return item.try_purchase(quantity)
        
    def get_active_items(self) -> List[MarketItem]:
        """Get list of all active items"""
        with self._lock:
            return list(self.active_items.values())
            
    def _start_expiration_timer(self, item: MarketItem) -> None:
        """Start timer for item expiration"""
        timer = Timer(
            item.max_sale_duration,
            self._handle_item_expiration,
            args=[item.item_id]
        )
        timer.daemon = True  # So timer doesn't prevent program exit
        timer.start()
        self.item_rotation_timers[item.item_id] = timer
        
    def _handle_item_expiration(self, item_id: str) -> None:
        """Handle item expiration"""
        try:
            self.end_sale(item_id)
        except Exception as e:
            self.logger.error(f"Error handling item expiration: {e}")
            
    def _start_next_item(self, seller_id: str) -> Optional[MarketItem]:
        """Start sale of next available item"""
        if seller_id not in self.seller_stocks:
            return None
            
        # Find next item with stock
        for item_type in ItemType:
            stock = self.seller_stocks[seller_id][item_type]
            if stock.quantity > 0:
                return self.start_sale(seller_id, item_type, stock.quantity)
                
        return None

    def get_seller_stock(self, seller_id: str) -> Dict[str, float]:
            """Get current stock levels for a seller"""
            with self._lock:
                if seller_id not in self.seller_stocks:
                    raise RuntimeError(f"Seller {seller_id} not found")
                    
                return {
                    item_type.value: stock.quantity 
                    for item_type, stock in self.seller_stocks[seller_id].items()
                }
