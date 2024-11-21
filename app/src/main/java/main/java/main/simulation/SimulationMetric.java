package main.java.main.simulation;

import java.time.Instant;

/**
 * Represents a snapshot of market simulation metrics at a specific point in time.
 * This class holds various statistics about the market simulation state.
 */
public class SimulationMetric {
    /** The timestamp when these metrics were captured */
    private final Instant timestamp;
    /** Total number of transactions completed */
    private final int totalTransactions;
    /** Average price across all transactions */
    private final double averagePrice;
    /** Total volume of goods traded */
    private final double totalVolume;
    /** Number of sellers currently active in the market */
    private final int activeSellers;
    /** Number of buyers currently active in the market */
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
