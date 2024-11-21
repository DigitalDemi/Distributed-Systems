package main.java.main.market;

import java.util.concurrent.*;
import java.util.*;
import java.util.logging.*;
import java.util.stream.Collectors;

public class MarketManager {
    private static final Logger logger = Logger.getLogger(MarketManager.class.getName());
    private final ConcurrentHashMap<String, Item> activeItems = new ConcurrentHashMap<>();
    private final ConcurrentHashMap<String, Map<String, Double>> sellerStocks = new ConcurrentHashMap<>();
    private final ScheduledExecutorService scheduler = Executors.newSingleThreadScheduledExecutor();

    public MarketManager() {
        scheduler.scheduleAtFixedRate(this::cleanupExpiredItems, 1, 1, TimeUnit.SECONDS);
    }

    public void initializeSellerStock(String sellerId) {
        Map<String, Double> stock = new ConcurrentHashMap<>();
        stock.put("flower", 1000.0);
        stock.put("sugar", 1000.0);
        stock.put("potato", 1000.0);
        stock.put("oil", 1000.0);
        sellerStocks.put(sellerId, stock);
        logger.info("Initialized stock for seller: " + sellerId);
    }

    public synchronized Item startSale(String sellerId, String itemName, double quantity) {
        Map<String, Double> stock = sellerStocks.get(sellerId);
        if (stock == null) {
            throw new IllegalStateException("Seller not found: " + sellerId);
        }

        Double available = stock.get(itemName);
        if (available == null || available < quantity) {
            throw new IllegalStateException("Insufficient stock for " + itemName);
        }

        // Update stock
        stock.put(itemName, available - quantity);

        // Create new item
        String itemId = "sale_" + sellerId + "_" + System.currentTimeMillis();
        // Pass the duration in seconds (60 is the max allowed per requirements)
        Item item = new Item(itemId, itemName, quantity, sellerId, 60);
        activeItems.put(itemId, item);

        logger.info(String.format("Sale started: %s, quantity: %.2f, seller: %s", 
                    itemName, quantity, sellerId));
        return item;
    }

    public synchronized boolean handleBuyRequest(String itemId, double quantity, String buyerId) {
        Item item = activeItems.get(itemId);
        if (item == null) {
            logger.warning("Item not found: " + itemId);
            return false;
        }

        if (item.isExpired()) {
            logger.warning("Item expired: " + itemId);
            return false;
        }

        boolean success = item.tryPurchase(quantity);
        if (success) {
            logger.info(String.format("Purchase successful: %.2f of %s by %s", 
                        quantity, itemId, buyerId));
        } else {
            logger.warning(String.format("Purchase failed: %.2f of %s by %s", 
                        quantity, itemId, buyerId));
        }
        return success;
    }

    public synchronized void endSale(String sellerId) {
        List<Item> sellerItems = activeItems.values().stream()
                .filter(item -> item.getSellerId().equals(sellerId))
                .collect(Collectors.toList());

        if (sellerItems.isEmpty()) {
            logger.info("No active sales found for seller: " + sellerId);
            return;
        }

        for (Item item : sellerItems) {
            endSingleSale(item.getId());
        }
        logger.info("Ended all sales for seller: " + sellerId);
    }

    private synchronized void endSingleSale(String itemId) {
    Item item = activeItems.get(itemId);
    if (item != null) {
        item.forceClose(); // Force close the item
        activeItems.remove(itemId);
        double remainingQuantity = item.getQuantity();
        if (remainingQuantity > 0) {
            Map<String, Double> stock = sellerStocks.get(item.getSellerId());
            if (stock != null) {
                stock.merge(item.getName(), remainingQuantity, Double::sum);
                logger.info(String.format("Sale ended: Returned %.2f %s to seller %s stock", 
                    remainingQuantity, item.getName(), item.getSellerId()));
            }
        }
    }
}
   

    public List<Item> getActiveItems() {
        return activeItems.values().stream()
                .filter(item -> !item.isExpired())
                .collect(Collectors.toList());
    }

    public String getSellerIdForItem(String itemId) {
        Item item = activeItems.get(itemId);
        return item != null ? item.getSellerId() : null;
    }

    private void cleanupExpiredItems() {
        List<Item> expiredItems = activeItems.values().stream()
                .filter(Item::isExpired)
                .collect(Collectors.toList());

        for (Item item : expiredItems) {
            endSingleSale(item.getId());
            logger.info("Cleaned up expired item: " + item.getId() + 
                       " (Remaining time: " + item.getRemainingTime() + "ms)");
        }
    }

    public void shutdown() {
        scheduler.shutdown();
        try {
            if (!scheduler.awaitTermination(5, TimeUnit.SECONDS)) {
                scheduler.shutdownNow();
            }
        } catch (InterruptedException e) {
            scheduler.shutdownNow();
            Thread.currentThread().interrupt();
        }
    }
}