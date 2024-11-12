package main.java.main.market;

import java.io.*;
import java.net.*;
import java.util.*;
import java.util.concurrent.*;
import java.time.Instant;
import java.util.logging.*;

public class MarketServer {
    private static final Logger logger = Logger.getLogger(MarketServer.class.getName());
    private final int port;
    private final MarketManager marketManager;
    private final ExecutorService executorService;
    private final ConcurrentHashMap<String, ClientHandler> clients;
    private volatile boolean running;
    private ServerSocket serverSocket;
    private final int TIMEOUT_SECONDS = 60;

    public MarketServer(int port) {
        this.port = port;
        this.marketManager = new MarketManager();
        this.executorService = Executors.newCachedThreadPool();
        this.clients = new ConcurrentHashMap<>();
        setupLogging();
    }

    private void setupLogging() {
        ConsoleHandler handler = new ConsoleHandler();
        handler.setFormatter(new SimpleFormatter());
        logger.addHandler(handler);
        logger.setLevel(Level.ALL);
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

            // Broadcast update to buyers
            broadcastStockUpdate(item.getId());
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

            clients.values().stream()
                  .filter(client -> client.clientType == ClientType.BUYER)
                  .forEach(client -> client.sendMessage(update));
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