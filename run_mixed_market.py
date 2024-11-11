import time
import logging
import threading
from datetime import timedelta
from src.simulation.market_simulation_controller import (
    MarketSimulationController,
    SimulationConfig
)

def setup_logging():
    """Setup root logging configuration"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler()]
    )

def main():
    setup_logging()
    logger = logging.getLogger("MixedMarketMain")
    
    try:
        # Create simulation config
        config = SimulationConfig(
            real_buyers=3,
            sim_buyers=3,
            sim_sellers=2,
            duration=timedelta(hours=24),
            transaction_rate=0.1,
            base_port=5000,
            failure_rate=0.1
        )
        
        # Wait for main server to be ready
        print("Please ensure the main server (main.py) is running.")
        input("Press Enter once the server is ready...")
        
        # Create simulation controller
        simulation = MarketSimulationController(config)
        
        try:
            # Setup clients
            simulation.setup_mixed_clients(
                real_buyers=config.real_buyers,
                sim_buyers=config.sim_buyers
            )
            
            # Run simulation in separate thread
            sim_thread = threading.Thread(target=simulation.run_mixed_simulation)
            sim_thread.daemon = True
            sim_thread.start()
            
            logger.info(f"""
Market simulation is running!
Connecting to server port: {config.base_port}

Simulation running with:
- {config.real_buyers} real buyers
- {config.sim_buyers} simulated buyers
- {config.sim_sellers} simulated sellers

You can also connect additional clients using:
- Buyer CLI:  python client_main.py buyer
- Seller CLI: python client_main.py seller
            """)
            
            # Keep main thread alive
            while True:
                time.sleep(1)
                
        except KeyboardInterrupt:
            logger.info("\nShutting down simulation...")
        finally:
            simulation.cleanup()
            
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        return 1
        
    return 0

if __name__ == "__main__":
    exit(main())