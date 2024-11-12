package main.java.main.client;

import main.java.main.market.*;
import java.io.*;
import java.net.*;
import java.util.*;
import java.util.concurrent.*;
import java.util.logging.*;

public abstract class MarketClient implements AutoCloseable {
    protected static final Logger logger = Logger.getLogger(MarketClient.class.getName());
    protected final String host;
    protected final int port;
    protected Socket socket;
    protected ObjectOutputStream out;
    protected ObjectInputStream in;
    protected String clientId;
    protected volatile boolean running;
    protected final ScheduledExecutorService heartbeatScheduler = Executors.newSingleThreadScheduledExecutor();
    protected final BlockingQueue<Message> responseQueue = new LinkedBlockingQueue<>();

    public MarketClient(String host, int port) {
        this.host = host;
        this.port = port;
    }

    public void connect() throws IOException {
        socket = new Socket(host, port);
        out = new ObjectOutputStream(socket.getOutputStream());
        in = new ObjectInputStream(socket.getInputStream());
        running = true;

        // Start message receiver thread
        Thread receiverThread = new Thread(this::receiveMessages);
        receiverThread.setDaemon(true);
        receiverThread.start();

        // Register with server
        register();

        // Start heartbeat
        startHeartbeat();

        logger.info("Connected to server: " + host + ":" + port);
    }

    protected abstract void register() throws IOException;

    protected void startHeartbeat() {
        heartbeatScheduler.scheduleAtFixedRate(() -> {
            try {
                if (running && clientId != null) {
                    sendMessage(new Message(
                        MessageType.HEARTBEAT,
                        Map.of("timestamp", System.currentTimeMillis()),
                        clientId
                    ));
                }
            } catch (Exception e) {
                logger.warning("Failed to send heartbeat: " + e.getMessage());
            }
        }, 0, 10, TimeUnit.SECONDS);
    }

    protected void receiveMessages() {
        while (running) {
            try {
                Message message = (Message) in.readObject();
                handleMessage(message);
            } catch (EOFException | SocketException e) {
                if (running) {
                    logger.warning("Connection lost: " + e.getMessage());
                    running = false;
                }
                break;
            } catch (Exception e) {
                logger.severe("Error receiving message: " + e.getMessage());
            }
        }
    }

    protected void handleMessage(Message message) {
        try {
            switch (message.getType()) {
                case ACK:
                    if (message.getData().containsKey("clientId")) {
                        clientId = (String) message.getData().get("clientId");
                        logger.info("Registered with ID: " + clientId);
                    }
                    break;
                default:
                    responseQueue.put(message);
                    break;
            }
        } catch (Exception e) {
            logger.severe("Error handling message: " + e.getMessage());
        }
    }

    protected synchronized void sendMessage(Message message) throws IOException {
        out.writeObject(message);
        out.flush();
        logger.fine("Sent message: " + message.getType());
    }

    protected Message waitForResponse(long timeout, TimeUnit unit) throws InterruptedException {
        Message response = responseQueue.poll(timeout, unit);
        if (response == null) {
            throw new TimeoutException("No response received within " + timeout + " " + unit);
        }
        return response;
    }

    @Override
    public void close() {
        running = false;
        heartbeatScheduler.shutdown();
        try {
            if (socket != null && !socket.isClosed()) {
                socket.close();
            }
        } catch (IOException e) {
            logger.warning("Error closing socket: " + e.getMessage());
        }
    }

    protected static class TimeoutException extends RuntimeException {
        public TimeoutException(String message) {
            super(message);
        }
    }
}