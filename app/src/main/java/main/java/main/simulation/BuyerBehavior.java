package main.java.main.simulation;

import java.time.Duration;
import java.util.*;

public class BuyerBehavior {
    private final Duration minPurchaseDelay;
    private final Duration maxPurchaseDelay;
    private final double minQuantity;
    private final double maxQuantity;
    private final double maxPrice;
    private final Random random = new Random();

    public BuyerBehavior(
            Duration minPurchaseDelay,
            Duration maxPurchaseDelay,
            double minQuantity,
            double maxQuantity,
            double maxPrice) {
        this.minPurchaseDelay = minPurchaseDelay;
        this.maxPurchaseDelay = maxPurchaseDelay;
        this.minQuantity = minQuantity;
        this.maxQuantity = maxQuantity;
        this.maxPrice = maxPrice;
    }

    public long getPurchaseDelay() {
        return minPurchaseDelay.toMillis() + 
               random.nextLong(maxPurchaseDelay.toMillis() - minPurchaseDelay.toMillis());
    }

    public double getQuantity() {
        return minQuantity + random.nextDouble() * (maxQuantity - minQuantity);
    }

    public boolean shouldBuy(double price) {
        return price <= maxPrice;
    }
}