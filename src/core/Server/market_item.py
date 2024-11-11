from dataclasses import dataclass
import time


@dataclass
class MarketItem:
    item_id: str
    name: str
    quantity: float
    seller_id: str
    sale_start_time: float = 0.0
    max_sale_duration: float = 60.0

    def to_dict(self) -> dict:
        """Convert to dictionary representation"""
        return {
            "item_id": self.item_id,
            "name": self.name,
            "quantity": self.quantity,
            "seller_id": self.seller_id,
            "remaining_time": self.get_remaining_time(),
            "sale_start_time": self.sale_start_time,
        }

    def get_remaining_time(self) -> float:
        """Get remaining sale time in seconds"""
        if self.sale_start_time == 0:
            return self.max_sale_duration
        elapsed = time.time() - self.sale_start_time
        return max(0, self.max_sale_duration - elapsed)
