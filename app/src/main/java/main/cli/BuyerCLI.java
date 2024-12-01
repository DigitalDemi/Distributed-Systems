package main.java.main.cli;

import java.util.*;
import java.util.logging.*;

import main.java.main.client.BuyerClient;
import main.java.main.market.Item;

public class BuyerCLI {
    private static final Logger logger = Logger.getLogger(BuyerCLI.class.getName());
    private final BuyerClient client;
    private final Scanner scanner;
    private static final String DEFAULT_HOST = "localhost";
    private static final int DEFAULT_PORT = 5000;

    public BuyerCLI(Scanner scanner) {
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
        client = new BuyerClient(host, port);
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
                        case "list":
                            listItems();
                            break;
                        case "buy":
                            if (parts.length < 3) {
                                System.out.println("Usage: buy <item_id> <quantity>");
                                break;
                            }
                            buyItem(parts[1], Double.parseDouble(parts[2]));
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

    private void listItems() throws Exception {
        List<Item> items = client.listItems();
        if (items.isEmpty()) {
            System.out.println("No items available");
            return;
        }

        System.out.println("\nAvailable Items:");
        for (Item item : items) {
            System.out.println("-------------------------");
            System.out.println("ID: " + item.getId());
            System.out.println("Name: " + item.getName());
            System.out.printf("Quantity: %.2f%n", item.getQuantity());
            System.out.printf("Time remaining: %.1fs%n", item.getRemainingTime());
        }
    }

    private void buyItem(String itemId, double quantity) throws Exception {
        boolean success = client.buyItem(itemId, quantity);
        if (success) {
            System.out.println("Purchase successful!");
        } else {
            System.out.println("Purchase failed.");
        }
    }

    private void printHelp() {
        System.out.println("\nAvailable commands:");
        System.out.println("list - List available items");
        System.out.println("buy <item_id> <quantity> - Buy an item");
        System.out.println("help - Show this help message");
        System.out.println("quit - Exit the marketplace");
    }

    public static void main(String[] args) {
        Scanner scanner = new Scanner(System.in);
        BuyerCLI cli = new BuyerCLI(scanner);
        cli.run();
        scanner.close();
    }
}