package main.java.main.simulation;

import java.time.Instant;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicLong;
import java.util.concurrent.atomic.AtomicReference;

/**
 * Tracks metrics for a market simulation, including transaction counts, sales data,
 * participant numbers, and trading volume. All metrics are thread-safe using atomic variables.
 */
public class SimulationMetrics {
    private final AtomicInteger totalTransactions = new AtomicInteger(0);
    private final AtomicInteger totalSales = new AtomicInteger(0);
    private final AtomicReference<Double> totalVolume = new AtomicReference<>(0.0);
    private final AtomicInteger totalBuyers = new AtomicInteger(0);
    private final AtomicInteger totalSellers = new AtomicInteger(0);
    private final AtomicInteger activeBuyers = new AtomicInteger(0);
    private final AtomicInteger activeSellers = new AtomicInteger(0);
    private final Instant startTime = Instant.now();

    /**
     * Updates all simulation metrics with new values.
     * 
     * @param transactions Total number of transactions attempted
     * @param sales Total number of successful sales
     * @param volume Total trading volume
     * @param buyers Total number of buyers in system
     * @param sellers Total number of sellers in system
     * @param activeBuyerCount Number of currently active buyers
     * @param activeSellerCount Number of currently active sellers
     */
    public void updateMetrics(
        int transactions,
        int sales,
        double volume,
        int buyers,
        int sellers,
        int activeBuyerCount,
        int activeSellerCount
    ) {
        totalTransactions.set(transactions);
        totalSales.set(sales);
        totalVolume.set(volume);
        totalBuyers.set(buyers);
        totalSellers.set(sellers);
        activeBuyers.set(activeBuyerCount);
        activeSellers.set(activeSellerCount);
    }

    /**
     * @return Total number of transactions attempted in the simulation
     */
    public int getTotalTransactions() {
        return totalTransactions.get();
    }

    /**
     * @return Total number of successful sales completed
     */
    public int getTotalSales() {
        return totalSales.get();
    }

    /**
     * @return Total trading volume across all transactions
     */
    public double getTotalVolume() {
        return totalVolume.get();
    }

    /**
     * @return Total number of buyers registered in the system
     */
    public int getTotalBuyers() {
        return totalBuyers.get();
    }

    /**
     * @return Total number of sellers registered in the system
     */
    public int getTotalSellers() {
        return totalSellers.get();
    }

    /**
     * @return Number of currently active buyers
     */
    public int getActiveBuyers() {
        return activeBuyers.get();
    }

    /**
     * @return Number of currently active sellers
     */
    public int getActiveSellers() {
        return activeSellers.get();
    }

    /**
     * Calculates the percentage of successful transactions.
     * 
     * @return Success rate as a percentage, or 0 if no transactions attempted
     */
    public double getSuccessRate() {
        int total = totalTransactions.get();
        return total > 0 ? (totalSales.get() * 100.0) / total : 0.0;
    }

    /**
     * @return The time when this metrics tracking started
     */
    public Instant getStartTime() {
        return startTime;
    }
}