from dataclasses import dataclass
from src.core.Market.item_type import ItemType

@dataclass
class ItemStock:
    item_type: ItemType
    quantity: float
    max_quantity: float

    def __post_init__(self):
        if self.quantity < 0:
            raise ValueError("Quantity cannot be negative")
        if self.max_quantity < 0:
            raise ValueError("Max quantity cannot be negative")
        if self.quantity > self.max_quantity:
            raise ValueError("Quantity cannot exceed max quantity")
