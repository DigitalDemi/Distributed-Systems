# Distributed Electronic Food Market Simulator

## Overview
This project implements a distributed electronic marketplace system where multiple buyers and sellers can trade items (flower, sugar, potato, and oil). The system supports concurrent transactions, real-time stock updates, and timed sales management.

### Key Features
- Multi-threaded server supporting concurrent client connections
- Real-time stock management and synchronization
- Configurable sale durations (maximum 60 seconds)
- Support for both real and simulated market participants
- Command-line interfaces for buyers and sellers
- Automated sale lifecycle management

## System Requirements
- Java JDK 21
- Gradle 8.8 or higher
- Windows operating system (for demo purposes)
- No additional frameworks or containers required

## Project Structure
```
project/
├── build.gradle     # Gradle build configuration
├── settings.gradle  # Gradle settings
├── src/
│   ├── main/
│   │   ├── java/
│   │   │   ├── main/
│   │   │   │   ├── client/          # Client implementations
│   │   │   │   ├── cli/             # Command-line interfaces
│   │   │   │   ├── market/          # Core market components
│   │   │   │   └── simulation/      # Simulation components
│   └── test/
│       └── java/                    # Test classes
```

## Building and Running

### 1. Starting the Market Server
```bash
# Build the project
./gradlew build

# Start the market server
./gradlew run
```

### 2. Running a Buyer
```bash
# Open a new terminal and run
./gradlew runBuyer
```

### 3. Running a Seller
```bash
# Open a new terminal and run
./gradlew runSeller
```
### 4. Running without Simulation
```bash
# Open a new terminal and run
./gradlew run -PnoSim
```
## Gradle Tasks
The project includes several custom Gradle tasks:

- `run` - Starts the market server
- `runBuyer` - Launches a buyer client
- `runSeller` - Launches a seller client
- `build` - Compiles the project and runs tests

## Usage Instructions

### Buyer Commands
- `list` - View all available items
- `buy <item_id> <quantity>` - Purchase an item
- `help` - Show available commands
- `quit` - Exit the marketplace

### Seller Commands
- `start <item_name> <quantity>` - Start selling an item
- `end` - End current sale
- `status` - Check current sale status
- `help` - Show available commands
- `quit` - Exit the marketplace

## Configuration

### Build Configuration
The project uses Gradle for build configuration:
- Java version: 21
- Main application class: `main.java.main.market.MarketApplication`
- Dependencies:
  - JUnit Jupiter for testing
  - Google Guava library

### Runtime Configuration
Default settings (can be overridden):
- Default host: localhost
- Default port: 5000
- Maximum sale duration: 60 seconds
- Available items: flower, sugar, potato, oil

## Demo Setup
1. Start the server using `./gradlew run`
2. Start at least one seller using `./gradlew runSeller`
3. Start multiple buyers (minimum 4) using `./gradlew runBuyer`
4. Test various transactions and interactions between buyers and sellers

## Error Handling
The system implements comprehensive error handling for:
- Network disconnections
- Concurrent access conflicts
- Invalid transactions
- Timeout scenarios
- Resource cleanup



To verify the system is working correctly:
1. Check that multiple buyers can connect simultaneously
2. Verify that stock updates are reflected in real-time
3. Confirm that sales end properly after duration expires
4. Test concurrent purchase requests
5. Verify proper cleanup after sales end

## Troubleshooting
If you encounter issues:
1. Check your Java version matches the required version (21)
2. Verify Gradle is properly installed
3. Ensure all components are running on the same network
4. Check for firewall restrictions
5. Verify the port (5000) is not in use
6. Check Gradle build output for errors

Common Gradle Issues:
- If Gradle wrapper is missing: `gradle wrapper`
- For permission issues: `chmod +x gradlew`
- For Java version mismatch: Check JAVA_HOME environment variable

## Additional Notes
- The system is designed to handle both manual and automated participants
- All transactions are processed synchronously to maintain consistency
- The simulation can be disabled using the --no-simulation flag
- Logging is available for debugging purposes
- The project uses Gradle's toolchain feature to ensure consistent Java version

