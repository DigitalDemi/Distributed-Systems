import time
import threading
from src.core.Market.item_type import ItemType


class MarketItem:
    def __init__(
        self,
        item_id: str,
        item_type: ItemType,
        quantity: float,
        seller_id: str,
        max_sale_duration: int = 60,
    ):
        self.item_id = item_id
        self.item_type = item_type
        self.quantity = quantity
        self.seller_id = seller_id
        self.max_sale_duration = max_sale_duration
        self.sale_start_time = time.time()
        self._lock = threading.Lock()

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization"""
        return {
            "item_id": self.item_id,
            "name": self.item_type.value,
            "quantity": self.quantity,
            "seller_id": self.seller_id,
            "remaining_time": self.get_remaining_time(),
            "sale_start_time": self.sale_start_time,
        }

    def try_purchase(self, amount: float) -> bool:
        """Thread-safe purchase attempt"""
        with self._lock:
            if amount <= 0:
                raise ValueError("Purchase amount must be positive")
            if self.quantity >= amount:
                self.quantity -= amount
                return True
            return False

    def get_remaining_time(self) -> float:
        """Get remaining sale time in seconds"""
        elapsed = time.time() - self.sale_start_time
        return max(0, self.max_sale_duration - elapsed)

    def is_expired(self) -> bool:
        """Check if sale duration has expired"""
        return self.get_remaining_time() <= 0
