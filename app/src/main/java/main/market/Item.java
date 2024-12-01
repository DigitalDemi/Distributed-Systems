package main.java.main.market;

import java.io.Serializable;
import java.time.Instant;

public class Item implements Serializable {
    private final String id;
    private final String name;
    private double quantity;
    private final String sellerId;
    private final Instant saleStartTime;
    private final int maxSaleDuration;

    public Item(String id, String name, double quantity, String sellerId) {
        this.id = id;
        this.name = name;
        this.quantity = quantity;
        this.sellerId = sellerId;
        this.saleStartTime = Instant.now();
        this.maxSaleDuration = 60; // 60 seconds
    }

    public synchronized boolean tryPurchase(double amount) {
        if (amount <= 0) {
            throw new IllegalArgumentException("Purchase amount must be positive");
        }
        if (quantity >= amount) {
            quantity -= amount;
            return true;
        }
        return false;
    }

    public String getId() { return id; }
    public String getName() { return name; }
    public double getQuantity() { return quantity; }
    public String getSellerId() { return sellerId; }
    
    public double getRemainingTime() {
        long elapsedSeconds = Instant.now().getEpochSecond() - saleStartTime.getEpochSecond();
        return Math.max(0, maxSaleDuration - elapsedSeconds);
    }

    public boolean isExpired() {
        return getRemainingTime() <= 0;
    }
}