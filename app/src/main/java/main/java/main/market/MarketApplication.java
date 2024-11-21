package main.java.main.market;

import main.java.main.simulation.MixedMarketSimulation;
import main.java.main.simulation.SimulationConfig;

import java.time.Duration;
import java.util.*;
import java.util.logging.*;

/**
 * Main entry point for the market application.
 * Handles server startup, simulation configuration, and system shutdown.
 */
public class MarketApplication {
    private static final Logger logger = Logger.getLogger(MarketApplication.class.getName());
    
    /**
     * Application entry point.
     * 
     * @param args Command line arguments for port and simulation configuration
     */
    public static void main(String[] args) {
        setupLogging();
        
        // Parse command line arguments
        MarketConfig config = parseArgs(args);
        
        // Start market server
        MarketServer server = new MarketServer(config.getPort());
        Thread serverThread = new Thread(() -> server.start(), "MarketServer");
        serverThread.start();
        
        logger.info(String.format("Market server started on port %d", config.getPort()));
        logger.info("Waiting for server initialization...");
        
        // Give server time to initialize
        try {
            Thread.sleep(2000);
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }
        
        // Start simulation if enabled
        MixedMarketSimulation simulation = null;
        if (config.isSimulationEnabled()) {
            // Convert comma-separated string to List
            List<String> itemTypes = Arrays.asList("flower", "sugar", "potato", "oil");
            
            SimulationConfig simConfig = new SimulationConfig.Builder()
                .setNumSimulatedBuyers(100)
                .setNumSimulatedSellers(100)
                .setQuantityRange(1.0, 100.0)
                .setPriceRange(10.0, 100.0)
                .setPurchaseDelayRange(Duration.ofSeconds(5), Duration.ofSeconds(30))
                .setSaleDurationRange(Duration.ofSeconds(30), Duration.ofSeconds(60))
                .setItemTypes(itemTypes)
                .setServerPort(config.getPort())
                .build();
                
            simulation = new MixedMarketSimulation("localhost", config.getPort(), simConfig);
            simulation.start();
            
            logger.info("""
                Market simulation started with:
                - Simulated Buyers: %d
                - Simulated Sellers: %d
                - Available Items: %s
                - Real users can connect to port: %d
                """.formatted(
                    simConfig.getNumSimulatedBuyers(),
                    simConfig.getNumSimulatedSellers(),
                    String.join(", ", itemTypes),
                    config.getPort()
                ));
        }
        
        // Add shutdown hook
        final MixedMarketSimulation finalSim = simulation;
        Runtime.getRuntime().addShutdownHook(new Thread(() -> {
            logger.info("Shutting down market system...");
            if (finalSim != null) {
                finalSim.stop();
            }
            server.shutdown();
        }));
        
        // Print connection info
        logger.info("""
            Market system is running!
            
            To connect real clients:
            1. Run buyer:  ./gradlew runBuyer
            2. Run seller: ./gradlew runSeller
            
            Press Ctrl+C to stop the system
            """);
    }
    
    /**
     * Parses command line arguments into market configuration.
     * 
     * @param args Command line arguments
     * @return Configured MarketConfig object
     */
    private static MarketConfig parseArgs(String[] args) {
        MarketConfig config = new MarketConfig();
        
        for (int i = 0; i < args.length; i++) {
            switch (args[i]) {
                case "--port":
                    config.setPort(Integer.parseInt(args[++i]));
                    break;
                case "--no-simulation":
                    config.setSimulationEnabled(false);
                    break;
            }
        }
        
        return config;
    }
    
    /**
     * Sets up system-wide logging configuration.
     */
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
    
    /**
     * Configuration class for market server settings.
     */
    private static class MarketConfig {
        private int port = 5000;
        private boolean simulationEnabled = true;
        
        public int getPort() { return port; }
        public void setPort(int port) { this.port = port; }
        public boolean isSimulationEnabled() { return simulationEnabled; }
        public void setSimulationEnabled(boolean enabled) { this.simulationEnabled = enabled; }
    }
}