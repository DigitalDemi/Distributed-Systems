package main.java.main.simulation;

import java.time.Duration;
import java.util.ArrayList;
import java.util.List;
import java.util.Random;

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

    public String getNextItem() {
        currentItemIndex = (currentItemIndex + 1) % itemTypes.size();
        return itemTypes.get(currentItemIndex);
    }

    public double generateQuantity() {
        return minQuantity + random.nextDouble() * (maxQuantity - minQuantity);
    }

    public double generatePrice() {
        return minPrice + random.nextDouble() * (maxPrice - minPrice);
    }

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