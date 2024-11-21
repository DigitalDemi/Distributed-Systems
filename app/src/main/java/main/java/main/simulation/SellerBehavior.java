package main.java.main.simulation;

import java.time.Duration;
import java.util.ArrayList;
import java.util.List;
import java.util.Random;

/**
 * Defines behavior patterns for simulated sellers in the market.
 * Controls item selection, pricing, quantities, and sale timing.
 */
public class SellerBehavior {
    private final List<String> itemTypes;
    private final double minQuantity;
    private final double maxQuantity;
    private final double minPrice;
    private final double maxPrice;
    private final Duration minSaleDuration;
    private final Duration maxSaleDuration;
    private final Random random = new Random();
    private int currentItemIndex = -1;

    /**
     * Creates a new seller behavior configuration.
     * @param itemTypes List of available item types to sell
     * @param minQuantity Minimum quantity per sale
     * @param maxQuantity Maximum quantity per sale
     * @param minPrice Minimum price per item
     * @param maxPrice Maximum price per item
     * @param minSaleDuration Minimum duration of a sale
     * @param maxSaleDuration Maximum duration of a sale
     */
    public SellerBehavior(
            List<String> itemTypes,
            double minQuantity,
            double maxQuantity,
            double minPrice,
            double maxPrice,
            Duration minSaleDuration,
            Duration maxSaleDuration) {
        this.itemTypes = new ArrayList<>(itemTypes);
        this.minQuantity = minQuantity;
        this.maxQuantity = maxQuantity;
        this.minPrice = minPrice;
        this.maxPrice = maxPrice;
        this.minSaleDuration = minSaleDuration;
        this.maxSaleDuration = maxSaleDuration;
    }

    /**
     * Selects the next item to sell in round-robin fashion.
     * @return Name of the next item to sell
     */
    public String getNextItem() {
        currentItemIndex = (currentItemIndex + 1) % itemTypes.size();
        return itemTypes.get(currentItemIndex);
    }

    /**
     * Generates a random quantity for the next sale.
     * @return Quantity between minQuantity and maxQuantity
     */
    public double generateQuantity() {
        return minQuantity + random.nextDouble() * (maxQuantity - minQuantity);
    }

    /**
     * Generates a random price for the next sale.
     * @return Price between minPrice and maxPrice
     */
    public double generatePrice() {
        return minPrice + random.nextDouble() * (maxPrice - minPrice);
    }

    /**
     * Determines the duration for the next sale.
     * @return Duration between minSaleDuration and maxSaleDuration
     */
    public Duration getSaleDuration() {
        long duration = minSaleDuration.toMillis() + 
                       random.nextLong(maxSaleDuration.toMillis() - minSaleDuration.toMillis());
        return Duration.ofMillis(duration);
    }

    public long getInitialDelay() {
        return 1000; // 1 second initial delay
    }

    public long getDelayBetweenSales() {
        return 2000; // 2 seconds between sales
    }
}