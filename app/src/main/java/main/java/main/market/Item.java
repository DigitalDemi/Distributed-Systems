package main.java.main.market;

import java.io.Serializable;
import java.time.Instant;
import java.util.concurrent.atomic.AtomicReference;

public class Item implements Serializable {
    private static final long serialVersionUID = 1L;
    
    private final String id;
    private final String name;
    private final AtomicReference<Double> quantity;
    private final String sellerId;
    private final Instant saleStartTime;
    private final long saleDurationMillis;
    private volatile boolean forceClosed = false;

    public Item(String id, String name, double quantity, String sellerId, int durationSeconds) {
        if (durationSeconds <= 0) {
            throw new IllegalArgumentException("Sale duration must be positive");
        }
        this.id = id;
        this.name = name;
        this.quantity = new AtomicReference<>(quantity);
        this.sellerId = sellerId;
        this.saleStartTime = Instant.now();
        this.saleDurationMillis = durationSeconds * 1000L;
    }

    public synchronized boolean tryPurchase(double amount) {
        if (amount <= 0) {
            throw new IllegalArgumentException("Purchase amount must be positive");
        }
        
        if (isExpired() || forceClosed) {
            return false;
        }

        Double currentQuantity = quantity.get();
        if (currentQuantity >= amount) {
            if (quantity.compareAndSet(currentQuantity, currentQuantity - amount)) {
                return true;
            }
        }
        return false;
    }

    public String getId() { 
        return id; 
    }
    
    public String getName() { 
        return name; 
    }
    
    public double getQuantity() { 
        return quantity.get(); 
    }
    
    public String getSellerId() { 
        return sellerId; 
    }
    
    public long getRemainingTime() {
        if (forceClosed) {
            return 0;
        }
        long elapsed = System.currentTimeMillis() - saleStartTime.toEpochMilli();
        return Math.max(0, saleDurationMillis - elapsed);
    }

    public boolean isExpired() {
        return getRemainingTime() <= 0 || forceClosed;
    }

    public void forceClose() {
        this.forceClosed = true;
    }

    @Override
    public String toString() {
        return String.format("Item[id=%s, name=%s, quantity=%.2f, remainingTime=%d]",
            id, name, quantity.get(), getRemainingTime());
    }
}