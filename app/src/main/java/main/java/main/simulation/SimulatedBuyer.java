package main.java.main.simulation;

import main.java.main.client.BuyerClient;
import main.java.main.market.Item;
import java.util.*;
import java.util.concurrent.*;
import java.util.logging.*;
import java.io.IOException;

/**
 * Simulates a buyer client that automatically purchases items from the market.
 * Uses configured behavior patterns to determine purchase timing and quantities.
 */
public class SimulatedBuyer {
    private static final Logger logger = Logger.getLogger(SimulatedBuyer.class.getName());
    private final BuyerClient client;
    private final BuyerBehavior behavior;
    private volatile boolean running = false;
    private final ScheduledExecutorService scheduler;
    private int transactionCount = 0;
    private double totalVolume = 0.0;
    private final String simulatedId;

    /**
     * Creates a new simulated buyer.
     * @param host Market server host
     * @param port Market server port
     * @param behavior Configured buyer behavior pattern
     * @throws IOException if connection fails
     */
    public SimulatedBuyer(String host, int port, BuyerBehavior behavior) throws IOException {
        this.client = new BuyerClient(host, port);
        this.behavior = behavior;
        this.simulatedId = "sim_buyer_" + UUID.randomUUID().toString().substring(0, 8);
        this.scheduler = Executors.newSingleThreadScheduledExecutor(r -> {
            Thread t = new Thread(r, "SimBuyer-" + simulatedId);
            t.setDaemon(true);
            return t;
        });
    }

    /**
     * Starts the simulated buyer's purchase cycle.
     * @throws IOException if connection fails
     */
    public void start() throws IOException {
        client.connect();
        running = true;
        schedulePurchases();
        logger.info("Simulated buyer started: " + simulatedId);
    }

    private void schedulePurchases() {
        scheduler.scheduleWithFixedDelay(
            this::attemptPurchase,
            0,
            behavior.getPurchaseDelay(),
            TimeUnit.MILLISECONDS
        );
    }

    private void attemptPurchase() {
        if (!running) return;

        try {
            List<Item> items = client.listItems();
            if (!items.isEmpty()) {
                Item selectedItem = items.get(ThreadLocalRandom.current().nextInt(items.size()));
                double quantity = behavior.getQuantity();

                logger.fine(String.format("Buyer %s attempting to purchase %.2f of %s", 
                    simulatedId, quantity, selectedItem.getName()));

                if (client.buyItem(selectedItem.getId(), quantity)) {
                    transactionCount++;
                    totalVolume += quantity;
                    logger.info(String.format("Buyer %s successfully purchased %.2f of %s (Total purchases: %d)", 
                        simulatedId, quantity, selectedItem.getName(), transactionCount));
                } else {
                    logger.fine(String.format("Buyer %s failed to purchase %.2f of %s", 
                        simulatedId, quantity, selectedItem.getName()));
                }
            }
        } catch (Exception e) {
            logger.log(Level.WARNING, String.format("Buyer %s encountered error during purchase: %s", 
                simulatedId, e.getMessage()), e);
        }
    }

    /**
     * Stops the simulated buyer and cleans up resources.
     */
    public void stop() {
        running = false;
        scheduler.shutdown();
        try {
            if (!scheduler.awaitTermination(5, TimeUnit.SECONDS)) {
                scheduler.shutdownNow();
            }
        } catch (InterruptedException e) {
            scheduler.shutdownNow();
            Thread.currentThread().interrupt();
        }
        client.close();
        logger.info("Simulated buyer stopped: " + simulatedId);
    }

    public String getSimulatedId() {
        return simulatedId;
    }

    /**
     * Returns the total number of successful transactions.
     * @return Number of completed purchases
     */
    public int getTransactionCount() {
        return transactionCount;
    }

    public double getTotalVolume() {
        return totalVolume;
    }

    public boolean isActive() {
        return running && !scheduler.isShutdown();
    }
}
