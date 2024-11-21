package main.java.main.client;

import java.io.*;
import java.net.Socket;
import java.util.logging.Logger;

import main.java.main.market.Message;

/**
 * Base class for market clients implementing common connection handling and messaging.
 * Provides abstract registration mechanism for specialized client types.
 */
public abstract class MarketClient implements AutoCloseable {
    protected static final Logger logger = Logger.getLogger(MarketClient.class.getName());
    
    protected final String host;
    protected final int port;
    protected Socket socket;
    protected ObjectOutputStream out;
    protected ObjectInputStream in;
    protected String clientId;
    protected volatile boolean connected = false;

    public MarketClient(String host, int port) {
        this.host = host;
        this.port = port;
    }

    /**
     * Establishes connection to the market server and performs registration.
     * @throws IOException if connection or registration fails
     */
    public void connect() throws IOException {
        socket = new Socket(host, port);
        out = new ObjectOutputStream(socket.getOutputStream());
        in = new ObjectInputStream(socket.getInputStream());
        connected = true;
        register();
        logger.info("Connected to server at " + host + ":" + port);
    }

    protected abstract void register() throws IOException;

    /**
     * Sends a message to the market server.
     * @param message Message to send
     * @throws IOException if sending fails
     */
    protected void sendMessage(Message message) throws IOException {
        synchronized(out) {
            out.writeObject(message);
            out.flush();
        }
    }

    /**
     * Reads a message from the market server.
     * @return Received message
     * @throws IOException if reading fails
     * @throws ClassNotFoundException if message type is unknown
     */
    protected Message readMessage() throws IOException, ClassNotFoundException {
        return (Message) in.readObject();
    }

    @Override
    public void close() {
        connected = false;
        try {
            if (out != null) out.close();
            if (in != null) in.close();
            if (socket != null) socket.close();
        } catch (IOException e) {
            logger.warning("Error during client cleanup: " + e.getMessage());
        }
    }

    public boolean isConnected() {
        return connected;
    }
}