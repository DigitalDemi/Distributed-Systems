package main.java.main.cli;

import java.util.*;
import java.util.logging.*;

import main.java.main.client.SellerClient;
import main.java.main.market.Item;

public class SellerCLI {
    private static final Logger logger = Logger.getLogger(SellerCLI.class.getName());
    private final SellerClient client;
    private final Scanner scanner;
    private static final String DEFAULT_HOST = "localhost";
    private static final int DEFAULT_PORT = 5000;

    public SellerCLI(Scanner scanner) {
        this.scanner = scanner;
        
        String host = DEFAULT_HOST;
        int port = DEFAULT_PORT;

        try {
            System.out.print("Enter server host (default: localhost): ");
            String inputHost = scanner.nextLine().trim();
            if (!inputHost.isEmpty()) {
                host = inputHost;
            }

            System.out.print("Enter server port (default: 5000): ");
            String inputPort = scanner.nextLine().trim();
            if (!inputPort.isEmpty()) {
                port = Integer.parseInt(inputPort);
            }
        } catch (NoSuchElementException e) {
            logger.info("Using default connection settings");
        }

        logger.info(String.format("Connecting to %s:%d", host, port));
        client = new SellerClient(host, port);
    }

    public void run() {
        try {
            client.connect();
            printHelp();

            while (true) {
                try {
                    System.out.print("\nEnter command: ");
                    String command = scanner.nextLine().trim().toLowerCase();
                    if (command.isEmpty()) continue;
                    
                    String[] parts = command.split("\\s+");

                    switch (parts[0]) {
                        case "start":
                            if (parts.length < 3) {
                                System.out.println("Usage: start <item_name> <quantity>");
                                break;
                            }
                            startSale(parts[1], Double.parseDouble(parts[2]));
                            break;
                        case "end":
                            endSale();
                            break;
                        case "status":
                            showStatus();
                            break;
                        case "help":
                            printHelp();
                            break;
                        case "quit":
                            return;
                        default:
                            System.out.println("Unknown command. Type 'help' for available commands.");
                    }
                } catch (NoSuchElementException e) {
                    break;
                } catch (Exception e) {
                    logger.log(Level.WARNING, "Error executing command", e);
                    System.out.println("Error: " + e.getMessage());
                }
            }
        } catch (Exception e) {
            logger.log(Level.SEVERE, "Fatal error", e);
            System.out.println("Fatal error: " + e.getMessage());
        } finally {
            client.close();
        }
    }

    private void startSale(String itemName, double quantity) throws Exception {
        client.startSale(itemName, quantity);
        System.out.println("Sale started successfully!");
        showStatus();
    }

    private void endSale() throws Exception {
        client.endSale();
        System.out.println("Sale ended successfully!");
    }

    private void showStatus() {
        Item currentItem = client.getCurrentItem();
        if (currentItem == null) {
            System.out.println("No active sale");
            return;
        }

        System.out.println("\nCurrent Sale:");
        System.out.println("Name: " + currentItem.getName());
        System.out.println(String.format("Quantity: %.2f", currentItem.getQuantity()));
        
       
        long remainingSeconds = currentItem.getRemainingTime() / 1000;
        System.out.println("Time remaining: " + remainingSeconds + "s");
    }

    private void printHelp() {
        System.out.println("\nAvailable commands:");
        System.out.println("start <item_name> <quantity> - Start selling an item");
        System.out.println("end - End current sale");
        System.out.println("status - Show current sale status");
        System.out.println("help - Show this help message");
        System.out.println("quit - Exit the marketplace");
    }

    public static void main(String[] args) {
        Scanner scanner = new Scanner(System.in);
        SellerCLI cli = new SellerCLI(scanner);
        cli.run();
        scanner.close();
    }
}