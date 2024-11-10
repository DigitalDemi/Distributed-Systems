from dataclasses import dataclass

@dataclass
class MarketItem:
    item_id: str
    name: str
    quantity: float
    seller_id: str
    sale_start_time: float
    max_sale_duration: float = 60.0
