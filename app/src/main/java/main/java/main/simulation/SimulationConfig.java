package main.java.main.simulation;

import java.time.Duration;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

public class SimulationConfig {
    private final int numSimulatedBuyers;
    private final int numSimulatedSellers;
    private final double minQuantity;
    private final double maxQuantity;
    private final double minPrice;
    private final double maxPrice;
    private final Duration minPurchaseDelay;
    private final Duration maxPurchaseDelay;
    private final Duration minSaleDuration;
    private final Duration maxSaleDuration;
    private final List<String> itemTypes;
    private final int serverPort;

    private SimulationConfig(Builder builder) {
        this.numSimulatedBuyers = builder.numSimulatedBuyers;
        this.numSimulatedSellers = builder.numSimulatedSellers;
        this.minQuantity = builder.minQuantity;
        this.maxQuantity = builder.maxQuantity;
        this.minPrice = builder.minPrice;
        this.maxPrice = builder.maxPrice;
        this.minPurchaseDelay = builder.minPurchaseDelay;
        this.maxPurchaseDelay = builder.maxPurchaseDelay;
        this.minSaleDuration = builder.minSaleDuration;
        this.maxSaleDuration = builder.maxSaleDuration;
        this.itemTypes = new ArrayList<>(builder.itemTypes);
        this.serverPort = builder.serverPort;
    }

    // Getters
    public int getNumSimulatedBuyers() { return numSimulatedBuyers; }
    public int getNumSimulatedSellers() { return numSimulatedSellers; }
    public double getMinQuantity() { return minQuantity; }
    public double getMaxQuantity() { return maxQuantity; }
    public double getMinPrice() { return minPrice; }
    public double getMaxPrice() { return maxPrice; }
    public Duration getMinPurchaseDelay() { return minPurchaseDelay; }
    public Duration getMaxPurchaseDelay() { return maxPurchaseDelay; }
    public Duration getMinSaleDuration() { return minSaleDuration; }
    public Duration getMaxSaleDuration() { return maxSaleDuration; }
    public List<String> getItemTypes() { return new ArrayList<>(itemTypes); }
    public int getServerPort() { return serverPort; }

    public static class Builder {
        private int numSimulatedBuyers = 3;
        private int numSimulatedSellers = 2;
        private double minQuantity = 1.0;
        private double maxQuantity = 10.0;
        private double minPrice = 10.0;
        private double maxPrice = 100.0;
        private Duration minPurchaseDelay = Duration.ofSeconds(5);
        private Duration maxPurchaseDelay = Duration.ofSeconds(30);
        private Duration minSaleDuration = Duration.ofSeconds(30);
        private Duration maxSaleDuration = Duration.ofSeconds(60);
        private List<String> itemTypes = Arrays.asList("flower", "sugar", "potato", "oil");
        private int serverPort = 5000;

        public Builder setNumSimulatedBuyers(int value) {
            this.numSimulatedBuyers = value;
            return this;
        }

        public Builder setNumSimulatedSellers(int value) {
            this.numSimulatedSellers = value;
            return this;
        }

        public Builder setQuantityRange(double min, double max) {
            this.minQuantity = min;
            this.maxQuantity = max;
            return this;
        }

        public Builder setPriceRange(double min, double max) {
            this.minPrice = min;
            this.maxPrice = max;
            return this;
        }

        public Builder setPurchaseDelayRange(Duration min, Duration max) {
            this.minPurchaseDelay = min;
            this.maxPurchaseDelay = max;
            return this;
        }

        public Builder setSaleDurationRange(Duration min, Duration max) {
            this.minSaleDuration = min;
            this.maxSaleDuration = max;
            return this;
        }

        public Builder setItemTypes(List<String> itemTypes) {
            this.itemTypes = new ArrayList<>(itemTypes);
            return this;
        }

        public Builder setServerPort(int port) {
            this.serverPort = port;
            return this;
        }

        public SimulationConfig build() {
            return new SimulationConfig(this);
        }
    }
}
