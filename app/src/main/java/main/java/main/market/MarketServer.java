package main.java.main.market;

import java.io.*;
import java.net.*;
import java.util.*;
import java.util.concurrent.*;
import java.time.Instant;
import java.util.logging.*;
import main.java.main.market.Event;


public class MarketServer {
    private static final Logger logger = Logger.getLogger(MarketServer.class.getName());
    private final int port;
    private final MarketManager marketManager;
    private final ExecutorService executorService;
    private final ConcurrentHashMap<String, ClientHandler> clients;
    private volatile boolean running;
    private ServerSocket serverSocket;
    private final int TIMEOUT_SECONDS = 60;
    private final BlockingQueue<Event> eventQueue;
    private final ExecutorService eventProcessor;

    public MarketServer(int port) {
        this.port = port;
        this.marketManager = new MarketManager();
        this.executorService = Executors.newCachedThreadPool();
        this.clients = new ConcurrentHashMap<>();
        this.eventQueue = new LinkedBlockingQueue<>();
        this.eventProcessor = Executors.newSingleThreadExecutor();
        setupLogging();
        startEventProcessor();
    }

    private void setupLogging() {
        ConsoleHandler handler = new ConsoleHandler();
        handler.setFormatter(new SimpleFormatter());
        logger.addHandler(handler);
        logger.setLevel(Level.ALL);
    }

    private void startEventProcessor() {
        eventProcessor.submit(() -> {
            while (running || !eventQueue.isEmpty()) {
                try {
                    Event event = eventQueue.poll(100, TimeUnit.MILLISECONDS);
                    if (event != null) {
                        processEvent(event);
                    }
                } catch (InterruptedException e) {
                    Thread.currentThread().interrupt();
                    break;
                }
            }
        });
    }

    private void processEvent(Event event) {
        switch (event.getType()) {
            case STOCK_UPDATE:
                clients.values().forEach(client -> client.sendMessage(event.getMessage()));
                break;
            case SALE_START:
                clients.values().forEach(client -> client.sendMessage(event.getMessage()));
                break;
            case SALE_END:
                clients.values().forEach(client -> client.sendMessage(event.getMessage()));
                break;
            case PURCHASE:
                String sellerId = marketManager.getSellerIdForItem(event.getItemId());
                clients.values().stream()
                    .filter(client -> client.clientId.equals(sellerId))
                    .forEach(client -> client.sendMessage(event.getMessage()));
                break;
        }
    }

    public void start() {
        try {
            serverSocket = new ServerSocket(port);
            running = true;
            logger.info("Server started on port " + port);

            while (running) {
                Socket clientSocket = serverSocket.accept();
                ClientHandler handler = new ClientHandler(clientSocket);
                executorService.submit(handler);
                logger.info("New client connected: " + clientSocket.getInetAddress());
            }
        } catch (IOException e) {
            logger.severe("Server error: " + e.getMessage());
        } finally {
            shutdown();
        }
    }

    void shutdown() {
        running = false;
        try {
            if (serverSocket != null && !serverSocket.isClosed()) {
                serverSocket.close();
            }
            executorService.shutdown();
            eventProcessor.shutdown();
            clients.values().forEach(ClientHandler::close);
            logger.info("Server shutdown complete");
        } catch (IOException e) {
            logger.severe("Error during shutdown: " + e.getMessage());
        }
    }

    private class ClientHandler implements Runnable {
        private final Socket socket;
        private final ObjectOutputStream out;
        private final ObjectInputStream in;
        private String clientId;
        private ClientType clientType;
        private Instant lastHeartbeat;

        public ClientHandler(Socket socket) throws IOException {
            this.socket = socket;
            this.out = new ObjectOutputStream(socket.getOutputStream());
            this.in = new ObjectInputStream(socket.getInputStream());
            this.lastHeartbeat = Instant.now();
        }

        @Override
        public void run() {
            try {
                handleRegistration();
                
                while (running && socket.isConnected()) {
                    Message message = (Message) in.readObject();
                    handleMessage(message);
                    lastHeartbeat = Instant.now();
                }
            } catch (IOException | ClassNotFoundException e) {
                logger.warning("Client disconnected: " + clientId);
            } finally {
                close();
            }
        }

        private void handleRegistration() throws IOException, ClassNotFoundException {
            Message registration = (Message) in.readObject();
            if (registration.getType() != MessageType.REGISTER) {
                throw new IllegalStateException("First message must be registration");
            }

            this.clientType = ClientType.valueOf(registration.getData().get("clientType").toString());
            this.clientId = generateClientId();
            clients.put(clientId, this);

            // Initialize resources for seller
            if (clientType == ClientType.SELLER) {
                marketManager.initializeSellerStock(clientId);
            }

            // Send acknowledgment
            sendMessage(new Message(
                MessageType.ACK,
                Map.of("clientId", clientId),
                "server"
            ));

            logger.info("Client registered: " + clientId + " as " + clientType);
        }

        private void handleMessage(Message message) {
            try {
                logger.info("Handling message: " + message.getType() + " from " + clientId);
                
                switch (message.getType()) {
                    case SALE_START:
                        handleSaleStart(message);
                        break;
                    case SALE_END:
                        handleSaleEnd(message);
                        break;
                    case BUY_REQUEST:
                        handleBuyRequest(message);
                        break;
                    case LIST_ITEMS:
                        handleListItems();
                        break;
                    case HEARTBEAT:
                        // Just update lastHeartbeat
                        break;
                    default:
                        logger.warning("Unknown message type: " + message.getType());
                }
            } catch (Exception e) {
                logger.severe("Error handling message: " + e.getMessage());
                sendError(e.getMessage());
            }
        }

        private void handleSaleStart(Message message) {
            Map<String, Object> data = message.getData();
            String itemName = (String) data.get("name");
            double quantity = ((Number) data.get("quantity")).doubleValue();

            Item item = marketManager.startSale(clientId, itemName, quantity);
            
            // Send immediate response
            sendMessage(new Message(
                MessageType.SALE_START,
                Map.of(
                    "success", true,
                    "itemId", item.getId(),
                    "name", item.getName(),
                    "quantity", item.getQuantity(),
                    "remainingTime", item.getRemainingTime()
                ),
                "server"
            ));

            // Broadcast update to all clients
            broadcastStockUpdate(item.getId());
            eventQueue.offer(new Event(EventType.SALE_START, item.getId(), 
                new Message(MessageType.SALE_START, 
                    Map.of("itemId", item.getId(), "sellerId", clientId),
                    "server")));
        }

        private void handleSaleEnd(Message message) {
            if (clientType != ClientType.SELLER) {
                sendError("Only sellers can end sales");
                return;
            }

            try {
                marketManager.endSale(clientId);  // Pass sellerId instead of itemId
                
                // Send confirmation to the seller
                sendMessage(new Message(
                    MessageType.SALE_END,
                    Map.of("success", true),
                    "server"
                ));

                // Broadcast updated stock list
                List<Item> items = marketManager.getActiveItems();
                Message update = new Message(
                    MessageType.STOCK_UPDATE,
                    Map.of("items", items),
                    "server"
                );
                
                // Add event to queue
                eventQueue.offer(new Event(
                    EventType.SALE_END,
                    clientId,
                    update
                ));

                logger.info("Sales ended for seller: " + clientId);
            } catch (Exception e) {
                logger.warning("Error ending sales: " + e.getMessage());
                sendError(e.getMessage());
            }
        }

        private void handleBuyRequest(Message message) {
            Map<String, Object> data = message.getData();
            String itemId = (String) data.get("itemId");
            double quantity = ((Number) data.get("quantity")).doubleValue();

            boolean success = marketManager.handleBuyRequest(itemId, quantity, clientId);
            
            sendMessage(new Message(
                MessageType.BUY_RESPONSE,
                Map.of(
                    "success", success,
                    "itemId", itemId,
                    "quantity", quantity
                ),
                "server"
            ));

            if (success) {
                broadcastStockUpdate(itemId);
                eventQueue.offer(new Event(EventType.PURCHASE, itemId,
                    new Message(MessageType.PURCHASE_NOTIFICATION,
                        Map.of("itemId", itemId, "quantity", quantity, "buyerId", clientId),
                        "server")));
            }
        }

        private void handleListItems() {
            List<Item> items = marketManager.getActiveItems();
            sendMessage(new Message(
                MessageType.LIST_ITEMS,
                Map.of("items", items),
                "server"
            ));
        }

        private void broadcastStockUpdate(String itemId) {
            List<Item> items = marketManager.getActiveItems();
            Message update = new Message(
                MessageType.STOCK_UPDATE,
                Map.of("items", items),
                "server"
            );
            
            eventQueue.offer(new Event(EventType.STOCK_UPDATE, itemId, update));
        }

        private synchronized void sendMessage(Message message) {
            try {
                out.writeObject(message);
                out.flush();
                logger.fine("Sent message: " + message.getType() + " to " + clientId);
            } catch (IOException e) {
                logger.warning("Failed to send message to " + clientId + ": " + e.getMessage());
            }
        }

        private void sendError(String error) {
            sendMessage(new Message(
                MessageType.ERROR,
                Map.of("error", error),
                "server"
            ));
        }

        private void close() {
            try {
                clients.remove(clientId);
                socket.close();
                logger.info("Client handler closed: " + clientId);
            } catch (IOException e) {
                logger.warning("Error closing client handler: " + e.getMessage());
            }
        }
    }

    private String generateClientId() {
        return UUID.randomUUID().toString().substring(0, 8);
    }
}