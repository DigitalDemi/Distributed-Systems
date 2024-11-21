
package main.java.main.market;

public class Event {
    private final EventType type;
    private final String itemId;
    private final Message message;

    public Event(EventType type, String itemId, Message message) {
        this.type = type;
        this.itemId = itemId;
        this.message = message;
    }

    public EventType getType() {
        return type;
    }

    public String getItemId() {
        return itemId;
    }

    public Message getMessage() {
        return message;
    }
}

enum EventType {
    STOCK_UPDATE,
    SALE_START,
    SALE_END,
    PURCHASE
}