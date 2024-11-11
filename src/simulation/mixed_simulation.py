import random

from src.core.Server.server import Server
from src.simulation.client_types import ClientType, ClientConfig
from src.simulation.virtual_socket_client import VirtualSocketClient
from src.simulation.simulated_client import SimulatedClient


class MarketSimulationController:
    def __init__(self, config: SimulationConfig):
        # self.server = Server('localhost', 5000)
        self.config = config
        self.server = Server("localhost", config.server_port)
        self.real_clients: List[BuyerClient] = []
        self.simulated_clients: List[SimulatedClient] = []
        self.logger = config.logger  # Assuming the logger is passed in config
        self.running = True  # Set a flag to control the simulation loop

        # Track both types of clients
        self.real_clients: List[Client] = []
        self.simulated_clients: List[SimulatedClient] = []

        # Start with mix of real and simulated
        self.setup_mixed_clients(
            real_buyers=config.real_buyers, sim_buyers=config.sim_buyers
        )

    # def setup_mixed_clients(self, real_buyers: int, sim_buyers: int):
    #     """Setup both real and simulated buyers"""
    #     # Start real clients
    #     for i in range(real_buyers):
    #         client = BuyerClient('localhost', 5000)
    #         client.connect()
    #         self.real_clients.append(client)
    #
    #     # Start simulated clients
    #     for i in range(sim_buyers):
    #         client = SimulatedBuyer(self.server)
    #         client.connect()  # Uses mock connection
    #         self.simulated_clients.append(client)
    #
    #     self.logger.info(f"Started {real_buyers} real and {sim_buyers} simulated clients")

    # def run_mixed_simulation(self):
    #     """Run simulation with both types of clients"""
    #     try:
    #         while self.running:
    #             # Real clients make real network calls
    #             for client in self.real_clients:
    #                 if random.random() < self.config.transaction_rate:
    #                     client.attempt_purchase(
    #                         random.choice(["flower", "sugar", "potato", "oil"]),
    #                         random.uniform(0.5, 2.0)
    #                     )
    #
    #             # Simulated clients use mock network
    #             for client in self.simulated_clients:
    #                 if random.random() < self.config.transaction_rate:
    #                     client.simulate_purchase()
    #
    #             # Both types receive updates from server
    #             self.process_server_updates()
    #
    #             # Add some randomness to timing
    #             time.sleep(random.uniform(0.1, 0.5))
    #
    #     except Exception as e:
    #         self.logger.error(f"Simulation error: {e}")
    #     finally:
    #         self.cleanup()
    #

    def run_mixed_simulation(self):
        """Run simulation with both types of clients"""
        try:
            while self.running:
                # Real clients make real network calls
                for client in self.real_clients:
                    if random.random() < self.config.transaction_rate:
                        client.attempt_purchase(
                            random.choice(["flower", "sugar", "potato", "oil"]),
                            random.uniform(0.5, 2.0),
                        )

                # Simulated clients use mock network
                for client in self.simulated_clients:
                    if random.random() < self.config.transaction_rate:
                        client.simulate_purchase()

                # Process server updates for both client types
                self.process_server_updates()

                # Add some randomness to timing
                time.sleep(random.uniform(0.1, 0.5))

        except Exception as e:
            self.logger.error(f"Simulation error: {e}")
        finally:
            self.cleanup()

    def process_server_updates(self):
        """Process updates for all clients"""
        updates = self.server.get_pending_updates()

        for update in updates:
            # Broadcast to real clients through sockets
            for client in self.real_clients:
                client.handle_update(update)

            # Send to simulated clients directly
            for client in self.simulated_clients:
                client.process_update(update)

    def cleanup(self):
        """Clean up resources and stop clients"""
        self.logger.info("Cleaning up resources...")
        for client in self.real_clients + self.simulated_clients:
            client.disconnect()

    # def setup_mixed_clients(self, real_buyers: int, sim_buyers: int):
    #     """Setup both real and simulated buyers"""
    #     try:
    #         # Start real clients
    #         for i in range(real_buyers):
    #             client = BuyerClient('localhost', self.config.base_port)
    #             client.connect()
    #             self.real_clients.append(client)
    #             self.logger.info(f"Started real client {i}")
    #
    #         # Start simulated clients
    #         for i in range(sim_buyers):
    #             # Changed: only pass node_id and controller
    #             client = SimulatedClient(
    #                 node_id=f"sim_client_{i}",
    #                 controller=self  # Pass the controller itself
    #             )
    #             client.connect()
    #             self.simulated_clients.append(client)
    #             self.logger.info(f"Started simulated client {i}")
    #
    #     except Exception as e:
    #         self.logger.error(f"Error setting up clients: {e}")
    #         raise

    def setup_mixed_clients(self, real_buyers: int, sim_buyers: int):
        """Setup both real and simulated buyers"""
        try:
            # Start real clients
            for i in range(real_buyers):
                client = BuyerClient("localhost", self.config.base_port)
                client.connect()
                self.real_clients.append(client)
                self.logger.info(f"Started real client {i}")

            # Start simulated clients
            for i in range(sim_buyers):
                # Changed: only pass node_id and controller
                client = SimulatedClient(
                    node_id=f"sim_client_{i}",
                    controller=self,  # Pass the controller itself
                )
                client.connect()
                self.simulated_clients.append(client)
                self.logger.info(f"Started simulated client {i}")

        except Exception as e:
            self.logger.error(f"Error setting up clients: {e}")
            raise
