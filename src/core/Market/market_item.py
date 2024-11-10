from threading import Lock, Timer
import time
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
        self.sale_start_time = time.time()
        self.max_sale_duration = max_sale_duration
        self._lock = Lock()
        self._timer: Timer | None = None

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization"""
        return {
            "item_id": self.item_id,
            "name": self.item_type.value,
            "quantity": self.quantity,
            "seller_id": self.seller_id,
            "sale_start_time": self.sale_start_time,
            "max_sale_duration": self.max_sale_duration,
            "remaining_time": self.get_remaining_time(),
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

    def is_expired(self) -> bool:
        """Check if sale duration has expired"""
        return time.time() - self.sale_start_time > self.max_sale_duration

    def get_remaining_time(self) -> float:
        """Get remaining sale time in seconds"""
        return max(0, self.max_sale_duration - (time.time() - self.sale_start_time))
