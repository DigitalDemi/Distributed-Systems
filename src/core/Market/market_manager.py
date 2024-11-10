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
        self.sale_history: dict[str, list[MarketItem]] = {}

    def initialize_seller_stock(self, seller_id: str, initial_quantity: float = 5.0):
        """Initialize a seller's stock with all item types"""
        with self._lock:
            self.seller_stocks[seller_id] = {}
            for item_type in ItemType:
                self.seller_stocks[seller_id][item_type] = ItemStock(
                    item_type=item_type,
                    quantity=initial_quantity,
                    max_quantity=initial_quantity,
                )

    def _handle_item_expiration(self, item_id: str) -> None:
        """Handle item expiration"""
        try:
            next_item = self.end_sale(item_id, auto_rotate=True)
            if next_item:
                self.logger.info(
                    f"Rotated to next item for seller {next_item.seller_id}"
                )
        except Exception as e:
            self.logger.error(f"Error handling item expiration: {e}")

    def _start_sale_timer(self, item: MarketItem) -> None:
        """Start timer for item expiration"""
        timer = Timer(
            item.max_sale_duration, self._handle_item_expiration, args=[item.item_id]
        )
        timer.daemon = True
        timer.start()
        self.item_rotation_timers[item.item_id] = timer

    def start_sale(
        self, seller_id: str, item_type: ItemType, quantity: float
    ) -> MarketItem:
        """Start a new sale for a seller"""
        with self._lock:
            # Check if seller exists
            if seller_id not in self.seller_stocks:
                raise RuntimeError(
                    f"Seller {seller_id} not found. Have they registered?"
                )

            # Check for existing sales
            existing_items = [
                item
                for item in self.active_items.values()
                if item.seller_id == seller_id
            ]
            if existing_items:
                raise RuntimeError("Seller already has an active sale")

            # Create new item
            item_id = f"item_{seller_id}_{time.time()}"
            new_item = MarketItem(
                item_id=item_id,
                item_type=item_type,
                quantity=quantity,
                seller_id=seller_id,
            )

            # Start sale timer
            self._start_sale_timer(new_item)

            # Add to active sales
            self.active_items[item_id] = new_item

            return new_item

    def end_sale(self, item_id: str, auto_rotate: bool = True) -> Optional[MarketItem]:
        """End a sale and optionally start next item"""
        with self._lock:
            if item_id not in self.active_items:
                return None

            # Get item info
            item = self.active_items[item_id]

            # Return unsold quantity to stock
            if item.quantity > 0:
                stock = self.seller_stocks[item.seller_id][item.item_type]
                stock.quantity += item.quantity

            # Remove item and cancel timer
            del self.active_items[item_id]
            if item_id in self.item_rotation_timers:
                self.item_rotation_timers[item_id].cancel()
                del self.item_rotation_timers[item_id]

            # Auto-rotate to next item if enabled
            next_item = None
            if auto_rotate:
                next_item = self._start_next_item(item.seller_id)

            return next_item

    def try_purchase(self, item_id: str, quantity: float) -> bool:
        """Thread-safe purchase attempt"""
        with self._lock:
            if item_id not in self.active_items:
                raise ValueError("Item not found")

            item = self.active_items[item_id]

            if quantity <= 0:
                raise ValueError("Purchase amount must be positive")

            if item.quantity >= quantity:
                item.quantity -= quantity
                return True

            return False

    def get_active_items(self) -> List[MarketItem]:
        """Get list of all active items"""
        with self._lock:
            return list(self.active_items.values())

    def _start_expiration_timer(self, item: MarketItem) -> None:
        """Start timer for item expiration"""
        timer = Timer(
            item.max_sale_duration, self._handle_item_expiration, args=[item.item_id]
        )
        timer.daemon = True  # So timer doesn't prevent program exit
        timer.start()
        self.item_rotation_timers[item.item_id] = timer

    def _start_next_item(self, seller_id: str) -> Optional[MarketItem]:
        """Start sale of next available item"""
        if seller_id not in self.seller_stocks:
            return None

        # Find next item with stock
        stocks = self.seller_stocks[seller_id]
        for item_type in ItemType:
            stock = stocks[item_type]
            if stock.quantity > 0:
                try:
                    return self.start_sale(seller_id, item_type, stock.quantity)
                except Exception as e:
                    self.logger.error(f"Failed to start next item: {e}")
                    continue

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

    def handle_unsold_items(self, item: MarketItem) -> None:
        """Handle items that weren't sold within time limit"""
        with self._lock:
            if item.quantity > 0:
                # Return to seller's stock
                seller_stock = self.seller_stocks[item.seller_id][item.item_type]
                seller_stock.quantity += item.quantity

                # Record in history
                if item.seller_id not in self.sale_history:
                    self.sale_history[item.seller_id] = []
                self.sale_history[item.seller_id].append(item)

    def rotate_seller_items(self, seller_id: str) -> Optional[MarketItem]:
        """Rotate through seller's items"""
        with self._lock:
            if seller_id not in self.seller_stocks:
                return None

            # Get current stocks
            stocks = self.seller_stocks[seller_id]

            # Find next item with stock
            current_type = None
            if seller_id in self.active_items:
                current_type = self.active_items[seller_id].item_type

            # Try to find next item type with stock
            found_next = False
            for item_type in ItemType:
                if current_type:
                    if not found_next:
                        if item_type == current_type:
                            found_next = True
                        continue

                stock = stocks[item_type]
                if stock.quantity > 0:
                    return self.start_sale(seller_id, item_type, stock.quantity)

            # If we didn't find anything after current type, start from beginning
            if current_type:
                for item_type in ItemType:
                    if item_type == current_type:
                        break
                    stock = stocks[item_type]
                    if stock.quantity > 0:
                        return self.start_sale(seller_id, item_type, stock.quantity)

            return None

    def _start_sale_timer(self, item: MarketItem) -> None:
        """Start timer for item sale duration"""

        def timer_callback():
            try:
                self.logger.info(f"Sale timer expired for {item.item_id}")
                self.handle_unsold_items(item)
                next_item = self.rotate_seller_items(item.seller_id)
                if next_item:
                    self.logger.info(
                        f"Rotated to {next_item.item_type} for {item.seller_id}"
                    )
            except Exception as e:
                self.logger.error(f"Error in sale timer callback: {e}")

        timer = threading.Timer(item.max_sale_duration, timer_callback)
        timer.daemon = True
        timer.start()
        self.item_rotation_timers[item.item_id] = timer
