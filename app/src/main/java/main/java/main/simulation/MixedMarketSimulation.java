package main.java.main.simulation;

import java.util.*;
import java.util.concurrent.*;
import java.util.logging.*;
import java.time.Duration;
import java.time.Instant;
import java.io.IOException;

public class MixedMarketSimulation {
    private static final Logger logger = Logger.getLogger(MixedMarketSimulation.class.getName());
    private final ExecutorService executorService;
    private final ScheduledExecutorService scheduler;
    private final String host;
    private final int port;
    private final List<SimulatedBuyer> simBuyers = new ArrayList<>();
    private final List<SimulatedSeller> simSellers = new ArrayList<>();
    private volatile boolean running = false;
    private final SimulationMetrics metrics;

    public MixedMarketSimulation(String host, int port, SimulationConfig config) {
        this.host = host;
        this.port = port;
        this.executorService = Executors.newCachedThreadPool(new ThreadFactory() {
            private int count = 0;
            @Override
            public Thread newThread(Runnable r) {
                Thread thread = new Thread(r, "SimulatedClient-" + count++);
                thread.setDaemon(true);
                return thread;
            }
        });
        this.scheduler = Executors.newScheduledThreadPool(1);
        this.metrics = new SimulationMetrics();

        initializeSimulatedParticipants(config);
    }

    private void initializeSimulatedParticipants(SimulationConfig config) {
        // Create simulated buyers
        for (int i = 0; i < config.getNumSimulatedBuyers(); i++) {
            try {
                BuyerBehavior behavior = new BuyerBehavior(
                    config.getMinPurchaseDelay(),
                    config.getMaxPurchaseDelay(),
                    config.getMinQuantity(),
                    config.getMaxQuantity(),
                    config.getMaxPrice()
                );

                SimulatedBuyer buyer = new SimulatedBuyer(host, port, behavior);
                simBuyers.add(buyer);
            } catch (IOException e) {
                logger.log(Level.SEVERE, "Failed to create simulated buyer", e);
            }
        }

        // Create simulated sellers
        for (int i = 0; i < config.getNumSimulatedSellers(); i++) {
            try {
                SellerBehavior behavior = new SellerBehavior(
                    config.getItemTypes(),
                    config.getMinQuantity(),
                    config.getMaxQuantity(),
                    config.getMinPrice(),
                    config.getMaxPrice(),
                    config.getMinSaleDuration(),
                    config.getMaxSaleDuration()
                );

                SimulatedSeller seller = new SimulatedSeller(
                    host,
                    port,
                    "seller_" + i,
                    behavior
                );
                simSellers.add(seller);
            } catch (IOException e) {
                logger.log(Level.SEVERE, "Failed to create simulated seller", e);
            }
        }
    }

    public void start() {
        if (running) {
            logger.warning("Simulation already running");
            return;
        }

        running = true;
        logger.info("Starting mixed market simulation");

        // Start simulated participants
        simSellers.forEach(seller -> executorService.submit(() -> {
            try {
                seller.start();
            } catch (Exception e) {
                logger.log(Level.SEVERE, "Error starting simulated seller", e);
            }
        }));

        // Give sellers time to initialize
        try {
            Thread.sleep(2000);
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }

        simBuyers.forEach(buyer -> executorService.submit(() -> {
            try {
                buyer.start();
            } catch (Exception e) {
                logger.log(Level.SEVERE, "Error starting simulated buyer", e);
            }
        }));

        // Start metrics collection
        scheduler.scheduleAtFixedRate(this::collectMetrics, 1, 1, TimeUnit.SECONDS);

        logger.info("Mixed market simulation started successfully");
    }

    public void stop() {
        running = false;
        simBuyers.forEach(SimulatedBuyer::stop);
        simSellers.forEach(SimulatedSeller::stop);
        
        executorService.shutdown();
        scheduler.shutdown();
        
        try {
            if (!executorService.awaitTermination(5, TimeUnit.SECONDS)) {
                executorService.shutdownNow();
            }
            if (!scheduler.awaitTermination(5, TimeUnit.SECONDS)) {
                scheduler.shutdownNow();
            }
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            executorService.shutdownNow();
            scheduler.shutdownNow();
        }
        
        logger.info("Mixed market simulation stopped");
        logFinalMetrics();
    }

    private void collectMetrics() {
        if (!running) return;
        
        metrics.updateMetrics(
            simBuyers.stream().mapToInt(SimulatedBuyer::getTransactionCount).sum(),
            simSellers.stream().mapToInt(SimulatedSeller::getSalesCount).sum(),
            simBuyers.stream().mapToDouble(SimulatedBuyer::getTotalVolume).sum(),
            simBuyers.size(),
            simSellers.size(),
            (int) simBuyers.stream().filter(SimulatedBuyer::isActive).count(),
            (int) simSellers.stream().filter(SimulatedSeller::isActive).count()
        );

        logCurrentMetrics();
    }

    private void logCurrentMetrics() {
        logger.info(String.format(
            "Simulation Metrics - Transactions: %d, Sales: %d, Volume: %.2f, " +
            "Active Buyers: %d/%d, Active Sellers: %d/%d",
            metrics.getTotalTransactions(),
            metrics.getTotalSales(),
            metrics.getTotalVolume(),
            metrics.getActiveBuyers(),
            metrics.getTotalBuyers(),
            metrics.getActiveSellers(),
            metrics.getTotalSellers()
        ));
    }

    private void logFinalMetrics() {
        logger.info("=== Final Simulation Metrics ===");
        logger.info(String.format("Total Transactions: %d", metrics.getTotalTransactions()));
        logger.info(String.format("Total Sales: %d", metrics.getTotalSales()));
        logger.info(String.format("Total Volume: %.2f", metrics.getTotalVolume()));
        logger.info(String.format("Average Success Rate: %.2f%%", metrics.getSuccessRate()));
        logger.info("==============================");
    }

    public SimulationMetrics getMetrics() {
        return metrics;
    }
}