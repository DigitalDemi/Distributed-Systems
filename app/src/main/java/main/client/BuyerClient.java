package main.java.main.client;

import java.io.IOException;
import java.util.*;
import java.util.concurrent.TimeUnit;
import java.util.logging.Logger;

import main.java.main.market.ClientType;
import main.java.main.market.Item;
import main.java.main.market.Message;
import main.java.main.market.MessageType;

public class BuyerClient extends MarketClient {
    private static final Logger logger = Logger.getLogger(BuyerClient.class.getName());
    private List<Item> availableItems = new ArrayList<>();

    public BuyerClient(String host, int port) {
        super(host, port);
    }

    @Override
    protected void register() throws IOException {
        sendMessage(new Message(
            MessageType.REGISTER,
            Map.of("clientType", ClientType.BUYER.name()),
            "unregistered"
        ));
    }

    public List<Item> listItems() throws IOException, InterruptedException {
        sendMessage(new Message(
            MessageType.LIST_ITEMS,
            Collections.emptyMap(),
            clientId
        ));

        Message response = waitForResponse(5, TimeUnit.SECONDS);
        if (response.getType() == MessageType.LIST_ITEMS) {
            @SuppressWarnings("unchecked")
            List<Item> items = (List<Item>) response.getData().get("items");
            availableItems = items;
            return items;
        } else if (response.getType() == MessageType.ERROR) {
            throw new RuntimeException((String) response.getData().get("error"));
        }
        throw new RuntimeException("Unexpected response type: " + response.getType());
    }

    public boolean buyItem(String itemId, double quantity) throws IOException, InterruptedException {
        sendMessage(new Message(
            MessageType.BUY_REQUEST,
            Map.of(
                "itemId", itemId,
                "quantity", quantity
            ),
            clientId
        ));

        Message response = waitForResponse(5, TimeUnit.SECONDS);
        if (response.getType() == MessageType.BUY_RESPONSE) {
            return (Boolean) response.getData().get("success");
        } else if (response.getType() == MessageType.ERROR) {
            throw new RuntimeException((String) response.getData().get("error"));
        }
        throw new RuntimeException("Unexpected response type: " + response.getType());
    }

    @Override
    protected void handleMessage(Message message) {
        super.handleMessage(message);
        if (message.getType() == MessageType.STOCK_UPDATE) {
            @SuppressWarnings("unchecked")
            List<Item> items = (List<Item>) message.getData().get("items");
            availableItems = items;
            logger.info("Stock update received: " + availableItems.size() + " items available");
        }
    }

    public List<Item> getAvailableItems() {
        return Collections.unmodifiableList(availableItems);
    }
}