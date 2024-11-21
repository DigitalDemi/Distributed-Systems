package main.java.main.market;

import java.io.Serializable;
import java.util.Map;

/**
 * Represents a message exchanged between clients and the market server.
 * Messages are serializable and contain type, data, sender information, and timing.
 */
public class Message implements Serializable {
    private final MessageType type;
    private final Map<String, Object> data;
    private final String senderId;
    private final long timestamp;

    /**
     * Creates a new message with the specified parameters.
     * @param type The type of message (e.g., REGISTER, BUY_REQUEST)
     * @param data Additional data carried by the message
     * @param senderId Identifier of the message sender
     */
    public Message(MessageType type, Map<String, Object> data, String senderId) {
        this.type = type;
        this.data = data;
        this.senderId = senderId;
        this.timestamp = System.currentTimeMillis();
    }

    public MessageType getType() { return type; }
    public Map<String, Object> getData() { return data; }
    public String getSenderId() { return senderId; }
    public long getTimestamp() { return timestamp; }
}