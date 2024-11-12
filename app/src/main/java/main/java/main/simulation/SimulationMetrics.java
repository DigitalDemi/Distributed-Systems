package main.java.main.simulation;

import java.time.Instant;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicLong;
import java.util.concurrent.atomic.AtomicReference;

public class SimulationMetrics {
    private final AtomicInteger totalTransactions = new AtomicInteger(0);
    private final AtomicInteger totalSales = new AtomicInteger(0);
    private final AtomicReference<Double> totalVolume = new AtomicReference<>(0.0);
    private final AtomicInteger totalBuyers = new AtomicInteger(0);
    private final AtomicInteger totalSellers = new AtomicInteger(0);
    private final AtomicInteger activeBuyers = new AtomicInteger(0);
    private final AtomicInteger activeSellers = new AtomicInteger(0);
    private final Instant startTime = Instant.now();

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

    public int getTotalTransactions() {
        return totalTransactions.get();
    }

    public int getTotalSales() {
        return totalSales.get();
    }

    public double getTotalVolume() {
        return totalVolume.get();
    }

    public int getTotalBuyers() {
        return totalBuyers.get();
    }

    public int getTotalSellers() {
        return totalSellers.get();
    }

    public int getActiveBuyers() {
        return activeBuyers.get();
    }

    public int getActiveSellers() {
        return activeSellers.get();
    }

    public double getSuccessRate() {
        int total = totalTransactions.get();
        return total > 0 ? (totalSales.get() * 100.0) / total : 0.0;
    }

    public Instant getStartTime() {
        return startTime;
    }
}