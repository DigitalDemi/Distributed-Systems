package main.java.main.market;

import main.java.main.market.MarketServer;
import java.util.logging.*;

public class MarketApplication {
    private static final Logger logger = Logger.getLogger(MarketApplication.class.getName());
    
    public static void main(String[] args) {
        setupLogging();
        
        int port = 5000;
        MarketServer server = new MarketServer(port);
        
        Runtime.getRuntime().addShutdownHook(new Thread(() -> {
            logger.info("Shutting down server...");
            server.shutdown();
        }));
        
        server.start();
    }
    
    private static void setupLogging() {
        LogManager.getLogManager().reset();
        ConsoleHandler handler = new ConsoleHandler();
        handler.setFormatter(new SimpleFormatter() {
            @Override
            public String format(LogRecord record) {
                return String.format("[%1$tF %1$tT] [%2$s] %3$s %n",
                    record.getMillis(),
                    record.getLevel().getLocalizedName(),
                    record.getMessage()
                );
            }
        });
        Logger rootLogger = Logger.getLogger("");
        rootLogger.addHandler(handler);
        rootLogger.setLevel(Level.INFO);
    }
}