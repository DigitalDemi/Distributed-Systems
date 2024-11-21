package main.java.main.simulation;

import java.io.IOException;
import java.time.Duration;
import java.util.concurrent.*;
import java.util.logging.*;
import java.util.concurrent.atomic.AtomicBoolean;

import main.java.main.client.SellerClient;

public class SimulatedSeller {
    private static final Logger logger = Logger.getLogger(SimulatedSeller.class.getName());
    private final SellerClient client;
    private final SellerBehavior behavior;
    private final ScheduledExecutorService scheduler;
    private volatile boolean running = false;
    private int salesCount = 0;
    private final AtomicBoolean currentlySelling = new AtomicBoolean(false);
    private ScheduledFuture<?> currentSaleTask;
    private final String sellerId;
    
    public SimulatedSeller(String host, int port, String id, SellerBehavior behavior) throws IOException {
        this.client = new SellerClient(host, port);
        this.behavior = behavior;
        this.sellerId = id;
        this.scheduler = Executors.newScheduledThreadPool(2, r -> {
            Thread t = new Thread(r, "SimSeller-" + id);
            t.setDaemon(true);
            return t;
        });
    }

    public void start() throws IOException {
        client.connect();
        running = true;
        scheduleSales();
        logger.info("Simulated seller started: " + sellerId);
    }

    private void scheduleSales() {
        // Initial delay before first sale
        scheduler.schedule(this::startNextSale, behavior.getInitialDelay(), TimeUnit.MILLISECONDS);
    }

    private void startNextSale() {
        if (!running || currentlySelling.get()) {
            return;
        }

        try {
            String itemName = behavior.getNextItem();
            double quantity = behavior.generateQuantity();
            Duration saleDuration = behavior.getSaleDuration();
            
            if (currentlySelling.compareAndSet(false, true)) {
                boolean success = client.startSale(itemName, quantity);
                
                if (success) {
                    salesCount++;
                    logger.info(String.format("Seller %s started sale: %s, quantity: %.2f, duration: %ds", 
                        sellerId, itemName, quantity, saleDuration.toSeconds()));
                    
                    // Schedule the end of this sale
                    currentSaleTask = scheduler.schedule(() -> {
                        try {
                            endCurrentSale();
                        } catch (Exception e) {
                            logger.log(Level.WARNING, "Error ending sale for " + sellerId, e);
                        }
                    }, saleDuration.toMillis(), TimeUnit.MILLISECONDS);
                } else {
                    logger.warning("Failed to start sale for seller " + sellerId);
                    currentlySelling.set(false);
                    retryAfterDelay();
                }
            }
        } catch (Exception e) {
            logger.log(Level.WARNING, "Error during sale start for " + sellerId, e);
            currentlySelling.set(false);
            retryAfterDelay();
        }
    }

    private void endCurrentSale() {
        if (!running || !currentlySelling.get()) {
            return;
        }

        try {
            if (client.hasActiveSale()) {
                client.endSale();
                logger.info("Seller " + sellerId + " ended sale");
            }
        } catch (Exception e) {
            logger.log(Level.WARNING, "Error ending sale for " + sellerId, e);
        } finally {
            cleanupCurrentSale();
        }
    }

    private void cleanupCurrentSale() {
        currentlySelling.set(false);
        if (currentSaleTask != null && !currentSaleTask.isDone()) {
            currentSaleTask.cancel(false);
        }
        
        // Schedule next sale after a delay
        if (running) {
            scheduler.schedule(
                this::startNextSale,
                behavior.getDelayBetweenSales(),
                TimeUnit.MILLISECONDS
            );
        }
    }

    private void retryAfterDelay() {
        if (running) {
            scheduler.schedule(
                this::startNextSale,
                5000, // 5 second retry delay
                TimeUnit.MILLISECONDS
            );
        }
    }

    public void stop() {
        running = false;
        
        // Cancel any ongoing sale
        if (currentlySelling.get()) {
            try {
                endCurrentSale();
            } catch (Exception e) {
                logger.log(Level.WARNING, "Error during stop for " + sellerId, e);
            }
        }

        // Shutdown scheduler
        scheduler.shutdown();
        try {
            if (!scheduler.awaitTermination(5, TimeUnit.SECONDS)) {
                scheduler.shutdownNow();
            }
        } catch (InterruptedException e) {
            scheduler.shutdownNow();
            Thread.currentThread().interrupt();
        }
        
        // Close client connection
        client.close();
        logger.info("Simulated seller stopped: " + sellerId);
    }

    public int getSalesCount() { return salesCount; }
    public boolean isActive() { return running && client.isConnected(); }
    public String getSellerId() { return sellerId; }
}