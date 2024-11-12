package main.java.main.simulation;

import java.io.IOException;
import java.time.Instant;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.UUID;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.ScheduledExecutorService;
import java.util.concurrent.TimeUnit;
import java.util.logging.Logger;

public class MarketSimulation {
    private static final Logger logger = Logger.getLogger(MarketSimulation.class.getName());
    private final ExecutorService executorService;
    private final ScheduledExecutorService scheduler;
    private final List<SimulatedBuyer> buyers = new ArrayList<>();
    private final List<SimulatedSeller> sellers = new ArrayList<>();
    private final SimulationConfig config;
    private volatile boolean running = false;
    private final Instant startTime;
    private final List<SimulationMetric> metrics = Collections.synchronizedList(new ArrayList<>());

    public MarketSimulation(SimulationConfig config) {
        this.config = config;
        this.executorService = Executors.newCachedThreadPool(r -> {
            Thread t = new Thread(r, "Simulation-" + UUID.randomUUID().toString().substring(0, 8));
            t.setDaemon(true);
            return t;
        });
        this.scheduler = Executors.newScheduledThreadPool(1);
        this.startTime = Instant.now();
    }

    public void start() throws IOException {
        if (running) {
            logger.warning("Simulation already running");
            return;
        }

        running = true;
        logger.info("Starting market simulation");

        try {
            initializeParticipants();
            scheduler.scheduleAtFixedRate(this::collectMetrics, 0, 1, TimeUnit.SECONDS);
            logger.info("Market simulation started successfully");
        } catch (Exception e) {
            running = false;
            throw new IOException("Failed to start simulation", e);
        }
    }

    private void initializeParticipants() throws IOException {
        CountDownLatch initLatch = new CountDownLatch(
            config.getNumSimulatedBuyers() + config.getNumSimulatedSellers()
        );

        // Initialize sellers
        for (int i = 0; i < config.getNumSimulatedSellers(); i++) {
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
                "localhost",
                config.getServerPort(),
                "seller_" + i,
                behavior
            );
            sellers.add(seller);

            executorService.submit(() -> {
                try {
                    seller.start();
                } finally {
                    initLatch.countDown();
                }
                return null;
            });
        }

        // Initialize buyers
        for (int i = 0; i < config.getNumSimulatedBuyers(); i++) {
            BuyerBehavior behavior = new BuyerBehavior(
                config.getMinPurchaseDelay(),
                config.getMaxPurchaseDelay(),
                config.getMinQuantity(),
                config.getMaxQuantity(),
                config.getMaxPrice()
            );

            SimulatedBuyer buyer = new SimulatedBuyer(
                "localhost",
                config.getServerPort(),
                behavior
            );
            buyers.add(buyer);

            executorService.submit(() -> {
                try {
                    buyer.start();
                } finally {
                    initLatch.countDown();
                }
                return null;
            });
        }

        try {
            if (!initLatch.await(30, TimeUnit.SECONDS)) {
                throw new IOException("Timeout waiting for participants to initialize");
            }
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            throw new IOException("Initialization interrupted", e);
        }
    }

    private void collectMetrics() {
        if (!running) return;

        SimulationMetric metric = new SimulationMetric(
            Instant.now(),
            buyers.stream().mapToInt(SimulatedBuyer::getTransactionCount).sum(),
            calculateAveragePrice(),
            buyers.stream().mapToDouble(SimulatedBuyer::getTotalVolume).sum(),
            (int) sellers.stream().filter(SimulatedSeller::isActive).count(),
            (int) buyers.stream().filter(SimulatedBuyer::isActive).count()
        );

        metrics.add(metric);
        logMetric(metric);
    }

    private double calculateAveragePrice() {
        // Implementation depends on how prices are tracked
        return 0.0; // Placeholder
    }

    private void logMetric(SimulationMetric metric) {
        logger.info(String.format(
            "Simulation Metrics - Transactions: %d, Average Price: %.2f, Volume: %.2f, " +
            "Active Sellers: %d, Active Buyers: %d",
            metric.getTotalTransactions(),
            metric.getAveragePrice(),
            metric.getTotalVolume(),
            metric.getActiveSellers(),
            metric.getActiveBuyers()
        ));
    }

    public void stop() {
        if (!running) return;

        running = false;
        buyers.forEach(SimulatedBuyer::stop);
        sellers.forEach(SimulatedSeller::stop);

        executorService.shutdown();
        scheduler.shutdown();

        try {
            executorService.awaitTermination(5, TimeUnit.SECONDS);
            scheduler.awaitTermination(5, TimeUnit.SECONDS);
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }

        logger.info("Market simulation stopped");
    }

    public List<SimulationMetric> getMetrics() {
        return Collections.unmodifiableList(metrics);
    }

    public boolean isRunning() {
        return running;
    }
}
