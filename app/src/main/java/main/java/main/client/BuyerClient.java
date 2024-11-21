package main.java.main.client;

import java.io.IOException;
import java.util.*;
import java.util.concurrent.CopyOnWriteArrayList;

import main.java.main.market.Item;
import main.java.main.market.Message;
import main.java.main.market.MessageType;

/**
 * Client implementation for market buyers.
 * Handles communication with market server for item listing and purchasing.
 */
public class BuyerClient extends MarketClient {
    private final List<Item> availableItems = new CopyOnWriteArrayList<>();

    /**
     * Creates a new buyer client.
     * 
     * @param host Market server host
     * @param port Market server port
     */
    public BuyerClient(String host, int port) {
        super(host, port);
    }

    /**
     * Registers this client as a buyer with the market server.
     * 
     * @throws IOException if registration fails
     */
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

    /**
     * Gets list of available items from market.
     * 
     * @return List of available items
     * @throws IOException if communication fails
     */
    public List<Item> listItems() throws IOException {
        sendMessage(new Message(MessageType.LIST_ITEMS, new HashMap<>(), clientId));
        
        try {
            Message response = readMessage();
            if (response.getType() == MessageType.LIST_ITEMS) {
                @SuppressWarnings("unchecked")
                List<Item> items = (List<Item>) response.getData().get("items");
                synchronized(availableItems) {
                    availableItems.clear();
                    if (items != null && !items.isEmpty()) {
                        availableItems.addAll(items);
                        logger.info("Updated available items, new count: " + availableItems.size());
                    }
                }
                return new ArrayList<>(items);
            }
        } catch (ClassNotFoundException e) {
            throw new IOException("Error listing items", e);
        }
        return new ArrayList<>();
    }

    /**
     * Attempts to purchase an item from the market.
     * 
     * @param itemId ID of item to purchase
     * @param quantity Amount to purchase
     * @return true if purchase successful, false otherwise
     * @throws IOException if communication fails
     */
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