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
        stock.put("flower", 5.0);
        stock.put("sugar", 5.0);
        stock.put("potato", 5.0);
        stock.put("oil", 5.0);
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
        Item item = new Item(itemId, itemName, quantity, sellerId);
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

    public synchronized void endSale(String itemId) {
        Item item = activeItems.remove(itemId);
        if (item != null && item.getQuantity() > 0) {
            // Return unsold quantity to stock
            Map<String, Double> stock = sellerStocks.get(item.getSellerId());
            if (stock != null) {
                stock.merge(item.getName(), item.getQuantity(), Double::sum);
            }
        }
        logger.info("Sale ended: " + itemId);
    }

    public List<Item> getActiveItems() {
        return activeItems.values().stream()
                .filter(item -> !item.isExpired())
                .collect(Collectors.toList());
    }

    private void cleanupExpiredItems() {
        activeItems.values().stream()
                .filter(Item::isExpired)
                .map(Item::getId)
                .forEach(this::endSale);
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