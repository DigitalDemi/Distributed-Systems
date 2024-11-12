package main.java.main.simulation;

import java.io.IOException;
import java.time.Duration;
import java.util.concurrent.Executors;
import java.util.concurrent.ScheduledExecutorService;
import java.util.concurrent.TimeUnit;

import main.java.main.client.SellerClient;

public class SimulatedSeller {
    private final SellerClient client;
    private final SellerBehavior behavior;
    private volatile boolean running = false;
    private final ScheduledExecutorService scheduler = Executors.newSingleThreadScheduledExecutor();
    private int salesCount = 0;

    public SimulatedSeller(String host, int port, String id, SellerBehavior behavior) throws IOException {
        this.client = new SellerClient(host, port);
        this.behavior = behavior;
    }

    public void start() throws IOException {
        client.connect();
        running = true;
        scheduleSales();
    }

    private void scheduleSales() {
        scheduler.schedule(this::startNextSale, behavior.getInitialDelay(), TimeUnit.MILLISECONDS);
    }

    private void startNextSale() {
        if (!running) return;

        try {
            String itemName = behavior.getNextItem();
            double quantity = behavior.generateQuantity();
            
            if (client.startSale(itemName, quantity)) {
                salesCount++;
                Duration duration = behavior.getSaleDuration();
                
                scheduler.schedule(() -> {
                    try {
                        if (running && client.hasActiveSale()) {
                            client.endSale();
                            scheduler.schedule(this::startNextSale, 
                                behavior.getDelayBetweenSales(), TimeUnit.MILLISECONDS);
                        }
                    } catch (Exception e) {
                        // Log error and continue
                    }
                }, duration.toMillis(), TimeUnit.MILLISECONDS);
            }
        } catch (Exception e) {
            // Log error and retry
            if (running) {
                scheduler.schedule(this::startNextSale, 5000, TimeUnit.MILLISECONDS);
            }
        }
    }

    public void stop() {
        running = false;
        scheduler.shutdown();
        client.close();
    }

    public int getSalesCount() { return salesCount; }
    public boolean isActive() { return running; }
}
