package main.java.main.market;

import java.util.concurrent.*;
import java.util.logging.*;
import java.util.Map;
import java.util.HashMap;

/**
 * Manages asynchronous processing of market events using a blocking queue.
 * Provides thread-safe event submission and handling for market operations.
 */
public class MarketEventQueue {
    private static final Logger logger = Logger.getLogger(MarketEventQueue.class.getName());
    private final BlockingQueue<MarketEvent> eventQueue = new LinkedBlockingQueue<>();
    private final ScheduledExecutorService scheduler = Executors.newSingleThreadScheduledExecutor();
    private final MarketManager marketManager;
    private volatile boolean running = true;

    /**
     * Creates a new market event queue.
     * 
     * @param marketManager The manager handling market operations
     */
    public MarketEventQueue(MarketManager marketManager) {
        this.marketManager = marketManager;
        // Start event processing thread
        Thread processorThread = new Thread(this::processEvents, "MarketEventProcessor");
        processorThread.setDaemon(true);
        processorThread.start();
    }

    /**
     * Submits an event for asynchronous processing.
     * 
     * @param event The market event to process
     */
    public void submitEvent(MarketEvent event) {
        if (!running) return;
        
        try {
            eventQueue.put(event);
            if (event.getCallback() != null) {
                event.getCallback().accept(new MarketResponse(true));
            }
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            logger.warning("Interrupted while submitting event: " + e.getMessage());
            if (event.getCallback() != null) {
                event.getCallback().accept(new MarketResponse(false, "Event submission interrupted"));
            }
        }
    }

    private void processEvents() {
        while (running) {
            try {
                MarketEvent event = eventQueue.take();
                handleEvent(event);
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
                logger.warning("Event processor interrupted: " + e.getMessage());
                break;
            }
        }
    }

    private void handleEvent(MarketEvent event) {
        try {
            switch (event.getType()) {
                case SALE_START:
                    handleSaleStart(event);
                    break;
                case SALE_END:
                    handleSaleEnd(event);
                    break;
                case BUY_REQUEST:
                    handleBuyRequest(event);
                    break;
                default:
                    logger.warning("Unknown event type: " + event.getType());
            }
        } catch (Exception e) {
            logger.log(Level.SEVERE, "Error processing event: " + e.getMessage(), e);
            // Send error response if callback exists
            if (event.getCallback() != null) {
                event.getCallback().accept(new MarketResponse(false, "Error: " + e.getMessage()));
            }
        }
    }

    private void handleSaleStart(MarketEvent event) {
        Map<String, Object> data = event.getData();
        String sellerId = (String) data.get("sellerId");
        String itemName = (String) data.get("itemName");
        double quantity = (double) data.get("quantity");

        try {
            Item item = marketManager.startSale(sellerId, itemName, quantity);
            
            // Schedule automatic sale end
            scheduler.schedule(() -> {
                if (item.getQuantity() > 0) {
                    submitEvent(new MarketEvent(
                        MarketEventType.SALE_END,
                        Map.of("itemId", item.getId(), "sellerId", sellerId),
                        null
                    ));
                }
            }, 60, TimeUnit.SECONDS);

            // Send success response
            if (event.getCallback() != null) {
                event.getCallback().accept(new MarketResponse(true, Map.of(
                    "itemId", item.getId(),
                    "item", item
                )));
            }
        } catch (Exception e) {
            if (event.getCallback() != null) {
                event.getCallback().accept(new MarketResponse(false, e.getMessage()));
            }
        }
    }

    private void handleSaleEnd(MarketEvent event) {
        Map<String, Object> data = event.getData();
        String itemId = (String) data.get("itemId");
        String sellerId = (String) data.get("sellerId");

        try {
            marketManager.endSale(itemId);
            // Send success response
            if (event.getCallback() != null) {
                event.getCallback().accept(new MarketResponse(true));
            }
        } catch (Exception e) {
            if (event.getCallback() != null) {
                event.getCallback().accept(new MarketResponse(false, e.getMessage()));
            }
        }
    }

    private void handleBuyRequest(MarketEvent event) {
        Map<String, Object> data = event.getData();
        String itemId = (String) data.get("itemId");
        double quantity = (double) data.get("quantity");
        String buyerId = (String) data.get("buyerId");

        try {
            boolean success = marketManager.handleBuyRequest(itemId, quantity, buyerId);
            if (event.getCallback() != null) {
                event.getCallback().accept(new MarketResponse(success));
            }
        } catch (Exception e) {
            if (event.getCallback() != null) {
                event.getCallback().accept(new MarketResponse(false, e.getMessage()));
            }
        }
    }

    /**
     * Stops event processing and cleans up resources.
     */
    public void shutdown() {
        running = false;
        scheduler.shutdown();
        try {
            scheduler.awaitTermination(5, TimeUnit.SECONDS);
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
            scheduler.shutdownNow();
        }
    }
}

/**
 * Represents different types of market events that can be processed.
 */
enum MarketEventType {
    SALE_START,
    SALE_END,
    BUY_REQUEST
}

/**
 * Represents a market event with its type, data, and callback.
 */
class MarketEvent {
    private final MarketEventType type;
    private final Map<String, Object> data;
    private final java.util.function.Consumer<MarketResponse> callback;

    public MarketEvent(
        MarketEventType type, 
        Map<String, Object> data,
        java.util.function.Consumer<MarketResponse> callback
    ) {
        this.type = type;
        this.data = new HashMap<>(data);
        this.callback = callback;
    }

    public MarketEventType getType() { return type; }
    public Map<String, Object> getData() { return data; }
    public java.util.function.Consumer<MarketResponse> getCallback() { return callback; }
}

/**
 * Represents the response to a market event processing.
 */
class MarketResponse {
    private final boolean success;
    private final String error;
    private final Map<String, Object> data;

    public MarketResponse(boolean success) {
        this(success, null, new HashMap<>());
    }

    public MarketResponse(boolean success, String error) {
        this(success, error, new HashMap<>());
    }

    public MarketResponse(boolean success, Map<String, Object> data) {
        this(success, null, data);
    }

    public MarketResponse(boolean success, String error, Map<String, Object> data) {
        this.success = success;
        this.error = error;
        this.data = data;
    }

    public boolean isSuccess() { return success; }
    public String getError() { return error; }
    public Map<String, Object> getData() { return data; }
}