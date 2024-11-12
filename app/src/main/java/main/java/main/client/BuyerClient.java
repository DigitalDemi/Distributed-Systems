package main.java.main.client;

import java.io.IOException;
import java.util.*;
import java.util.concurrent.CopyOnWriteArrayList;

import main.java.main.market.Item;
import main.java.main.market.Message;
import main.java.main.market.MessageType;

public class BuyerClient extends MarketClient {
    private final List<Item> availableItems = new CopyOnWriteArrayList<>();

    public BuyerClient(String host, int port) {
        super(host, port);
    }

    @Override
    protected void register() throws IOException {
        Map<String, Object> data = new HashMap<>();
        data.put("clientType", "BUYER");
        sendMessage(new Message(MessageType.REGISTER, data, null));
        
        try {
            Message response = readMessage();
            if (response.getType() == MessageType.ACK) {
                this.clientId = (String) response.getData().get("clientId");
                logger.info("Registered as buyer with ID: " + clientId);
            } else {
                throw new IOException("Registration failed");
            }
        } catch (ClassNotFoundException e) {
            throw new IOException("Error during registration", e);
        }
    }

    public List<Item> listItems() throws IOException {
        sendMessage(new Message(MessageType.LIST_ITEMS, new HashMap<>(), clientId));
        
        try {
            Message response = readMessage();
            if (response.getType() == MessageType.LIST_ITEMS) {
                @SuppressWarnings("unchecked")
                List<Item> items = (List<Item>) response.getData().get("items");
                availableItems.clear();
                availableItems.addAll(items);
                return new ArrayList<>(items);
            }
        } catch (ClassNotFoundException e) {
            throw new IOException("Error listing items", e);
        }
        return new ArrayList<>();
    }

    public boolean buyItem(String itemId, double quantity) throws IOException {
        Map<String, Object> data = new HashMap<>();
        data.put("itemId", itemId);
        data.put("quantity", quantity);
        
        sendMessage(new Message(MessageType.BUY_REQUEST, data, clientId));
        
        try {
            Message response = readMessage();
            if (response.getType() == MessageType.BUY_RESPONSE) {
                return (boolean) response.getData().get("success");
            }
        } catch (ClassNotFoundException e) {
            throw new IOException("Error processing buy request", e);
        }
        return false;
    }
}