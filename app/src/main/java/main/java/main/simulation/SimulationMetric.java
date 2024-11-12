package main.java.main.simulation;

import java.time.Instant;

public class SimulationMetric {
    private final Instant timestamp;
    private final int totalTransactions;
    private final double averagePrice;
    private final double totalVolume;
    private final int activeSellers;
    private final int activeBuyers;

    public SimulationMetric(
        Instant timestamp,
        int totalTransactions,
        double averagePrice,
        double totalVolume,
        int activeSellers,
        int activeBuyers
    ) {
        this.timestamp = timestamp;
        this.totalTransactions = totalTransactions;
        this.averagePrice = averagePrice;
        this.totalVolume = totalVolume;
        this.activeSellers = activeSellers;
        this.activeBuyers = activeBuyers;
    }

    // Getters
    public Instant getTimestamp() { return timestamp; }
    public int getTotalTransactions() { return totalTransactions; }
    public double getAveragePrice() { return averagePrice; }
    public double getTotalVolume() { return totalVolume; }
    public int getActiveSellers() { return activeSellers; }
    public int getActiveBuyers() { return activeBuyers; }
}
