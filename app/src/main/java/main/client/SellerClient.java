package main.java.main.client;


import main.java.main.market.Item;
import main.java.main.market.Message;
import main.java.main.market.MessageType;

import java.io.*;
import java.util.*;
import java.util.concurrent.TimeUnit;

public class SellerClient extends MarketClient {
    private Item currentItem;

    public SellerClient(String host, int port) {
        super(host, port);
    }

    @Override
    protected void register() throws IOException {
        sendMessage(new Message(
            MessageType.REGISTER,
            Map.of("clientType", "SELLER"),
            "unregistered"
        ));
    }

    public void startSale(String itemName, double quantity) throws IOException, InterruptedException {
        if (currentItem != null) {
            throw new IllegalStateException("Already have active sale");
        }

        sendMessage(new Message(
            MessageType.SALE_START,
            Map.of(
                "name", itemName,
                "quantity", quantity
            ),
            clientId
        ));

        Message response = waitForResponse(5, TimeUnit.SECONDS);
        if (response.getType() == MessageType.SALE_START) {
            if ((Boolean) response.getData().get("success")) {
                currentItem = new Item(
                    (String) response.getData().get("itemId"),
                    (String) response.getData().get("name"),
                    (Double) response.getData().get("quantity"),
                    clientId
                );
                logger.info("Sale started: " + currentItem.getName());
            }
        } else if (response.getType() == MessageType.ERROR) {
            throw new RuntimeException((String) response.getData().get("error"));
        } else {
            throw new RuntimeException("Unexpected response type: " + response.getType());
        }
    }

    public void endSale() throws IOException, InterruptedException {
        if (currentItem == null) {
            throw new IllegalStateException("No active sale");
        }

        sendMessage(new Message(
            MessageType.SALE_END,
            Map.of("itemId", currentItem.getId()),
            clientId
        ));

        Message response = waitForResponse(5, TimeUnit.SECONDS);
        if (response.getType() == MessageType.SALE_END) {
            if ((Boolean) response.getData().get("success")) {
                currentItem = null;
                logger.info("Sale ended");
            }
        } else if (response.getType() == MessageType.ERROR) {
            throw new RuntimeException((String) response.getData().get("error"));
        } else {
            throw new RuntimeException("Unexpected response type: " + response.getType());
        }
    }

    public Item getCurrentItem() {
        return currentItem;
    }

    @Override
    protected void handleMessage(Message message) {
        super.handleMessage(message);
        if (message.getType() == MessageType.STOCK_UPDATE && currentItem != null) {
            @SuppressWarnings("unchecked")
            List<Item> items = (List<Item>) message.getData().get("items");
            for (Item item : items) {
                if (item.getId().equals(currentItem.getId())) {
                    currentItem = item;
                    logger.info("Stock updated for current item: " + item.getQuantity());
                    break;
                }
            }
        }
    }
}