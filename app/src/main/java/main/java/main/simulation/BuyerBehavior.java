package main.java.main.simulation;

import java.time.Duration;
import java.util.*;

/**
 * Defines the behavior patterns for simulated buyers in the market.
 * Controls purchase timing, quantities, and price acceptance decisions.
 */
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

    /**
     * Calculates the delay until the next purchase attempt.
     * @return delay in milliseconds between minimum and maximum purchase delay
     */
    public long getPurchaseDelay() {
        return minPurchaseDelay.toMillis() + 
               random.nextLong(maxPurchaseDelay.toMillis() - minPurchaseDelay.toMillis());
    }

    /**
     * Generates a random quantity for the next purchase.
     * @return quantity between minQuantity and maxQuantity
     */
    public double getQuantity() {
        return minQuantity + random.nextDouble() * (maxQuantity - minQuantity);
    }

    /**
     * Determines if an item should be purchased at the given price.
     * @param price The price of the item
     * @return true if the price is acceptable, false otherwise
     */
    public boolean shouldBuy(double price) {
        return price <= maxPrice;
    }
}