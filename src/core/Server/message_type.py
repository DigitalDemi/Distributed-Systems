from enum import Enum


class MessageType(Enum):
    LIST_ITEMS = "list_items"
    ITEM_UPDATE = "item_update"
    BUY_REQUEST = "buy_request"
    BUY_RESPONSE = "buy_response"
    STOCK_UPDATE = "stock_update"
    SALE_START = "sale_start"
    SALE_END = "sale_end"
    ERROR = "error"
    ACK = "acknowledgment"
    REGISTER = "register"
