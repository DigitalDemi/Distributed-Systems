package main.java.main.client;

import java.io.IOException;
import java.util.HashMap;
import java.util.Map;

import main.java.main.market.Item;
import main.java.main.market.Message;
import main.java.main.market.MessageType;

public class SellerClient extends MarketClient {
    private Item currentItem;
    private volatile boolean activeSale = false;

    public SellerClient(String host, int port) {
        super(host, port);
    }

    @Override
    protected void register() throws IOException {
        Map<String, Object> data = new HashMap<>();
        data.put("clientType", "SELLER");
        sendMessage(new Message(MessageType.REGISTER, data, null));
        
        try {
            Message response = readMessage();
            if (response.getType() == MessageType.ACK) {
                this.clientId = (String) response.getData().get("clientId");
                logger.info("Registered as seller with ID: " + clientId);
            } else {
                throw new IOException("Registration failed");
            }
        } catch (ClassNotFoundException e) {
            throw new IOException("Error during registration", e);
        }
    }

    public boolean startSale(String itemName, double quantity) throws IOException {
        if (activeSale) {
            logger.warning("Cannot start new sale while another is active");
            return false;
        }

        Map<String, Object> data = new HashMap<>();
        data.put("name", itemName);
        data.put("quantity", quantity);
        
        sendMessage(new Message(MessageType.SALE_START, data, clientId));
        
        try {
            Message response = readMessage();
            if (response.getType() == MessageType.SALE_START) {
                boolean success = (boolean) response.getData().get("success");
                if (success) {
                    this.currentItem = new Item(
                        (String) response.getData().get("itemId"),
                        itemName,
                        quantity,
                        clientId, port
                    );
                    this.activeSale = true;
                }
                return success;
            }
        } catch (ClassNotFoundException e) {
            throw new IOException("Error starting sale", e);
        }
        return false;
    }

    public boolean endSale() throws IOException {
        if (!activeSale) {
            logger.warning("No active sale to end");
            return false;
        }

        sendMessage(new Message(MessageType.SALE_END, new HashMap<>(), clientId));
        
        this.activeSale = false;
        this.currentItem = null;
        return true;
    }

    public Item getCurrentItem() {
        return currentItem;
    }

    public boolean hasActiveSale() {
        return activeSale;
    }
}