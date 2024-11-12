package main.java.main.client;

import java.io.*;
import java.net.Socket;
import java.util.logging.Logger;

import main.java.main.market.Message;

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

    public void connect() throws IOException {
        socket = new Socket(host, port);
        out = new ObjectOutputStream(socket.getOutputStream());
        in = new ObjectInputStream(socket.getInputStream());
        connected = true;
        register();
        logger.info("Connected to server at " + host + ":" + port);
    }

    protected abstract void register() throws IOException;

    protected void sendMessage(Message message) throws IOException {
        synchronized(out) {
            out.writeObject(message);
            out.flush();
        }
    }

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