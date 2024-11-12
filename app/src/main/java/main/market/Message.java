package main.java.main.market;

import java.io.Serializable;
import java.util.Map;

public class Message implements Serializable {
    private final MessageType type;
    private final Map<String, Object> data;
    private final String senderId;
    private final long timestamp;

    public Message(MessageType type, Map<String, Object> data, String senderId) {
        this.type = type;
        this.data = data;
        this.senderId = senderId;
        this.timestamp = System.currentTimeMillis();
    }

    public MessageType getType() {
        return type;
    }

    public Map<String, Object> getData() {
        return data;
    }

    public String getSenderId() {
        return senderId;
    }

    public long getTimestamp() {
        return timestamp;
    }

    @Override
    public String toString() {
        return "Message{" +
                "type=" + type +
                ", data=" + data +
                ", senderId='" + senderId + '\'' +
                ", timestamp=" + timestamp +
                '}';
    }
}