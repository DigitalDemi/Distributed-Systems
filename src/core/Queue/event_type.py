from enum import Enum


class EventType(Enum):
    # Market events
    BUYER_MARKET_JOIN = "buyer_joined"
    BUYER_MARKET_LEAVE = "buyer_left"
    BUYER_PURCASE = "buyer_item_request"
    BUYER_PURCASE_COMPLETE = "buyer_item_purchased"
    BUYER_LIST_ITEM = "buyer_listing_items"

    SELLER_JOIN = "seller_joined"

    # Simulation events
    TIME_TICK = "time_tick"
    STOCK_UPDATE = "stock_update"
    ITEM_ROTATION = "item_rotation"
