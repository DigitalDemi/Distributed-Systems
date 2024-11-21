package main.java.main.market;

/**
 * Defines types of messages that can be exchanged between clients and the market server.
 * Each type represents a different kind of market interaction or system event.
 */
public enum MessageType {
    /** Client registration request message */
    REGISTER,
    /** Server acknowledgment message */
    ACK,
    /** Message announcing start of a new sale */
    SALE_START,
    /** Message indicating end of a sale */
    SALE_END,
    /** Purchase request from buyer to server */
    BUY_REQUEST,
    /** Server's response to a purchase request */
    BUY_RESPONSE,
    /** Request to list available market items */
    LIST_ITEMS,
    /** Update notification for item inventory changes */
    STOCK_UPDATE,
    /** Error notification message */
    ERROR,
    /** Connection health check message */
    HEARTBEAT,
    /** Notification of successful purchase */
    PURCHASE_NOTIFICATION
}