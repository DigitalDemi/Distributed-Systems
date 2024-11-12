package main.java.main.market;

public enum MessageType {
    REGISTER,
    ACK,
    SALE_START,
    SALE_END,
    BUY_REQUEST,
    BUY_RESPONSE,
    LIST_ITEMS,
    STOCK_UPDATE,
    ERROR,
    HEARTBEAT
}