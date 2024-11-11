# src/simulation/market_simulation_controller.py

import random
import time
import threading
import logging
from typing import List, Dict, Optional
from datetime import timedelta

from src.core.Market.item_type import ItemType
from src.core.Client.buyer_client import BuyerClient
from src.core.Server.message import Message
from src.core.Server.message_type import MessageType
from src.simulation.simulated_client import SimulatedClient
from src.simulation.simulated_seller import SimulatedSeller

class SimulationConfig:
    def __init__(
        self,
        real_buyers: int,
        sim_buyers: int,
        sim_sellers: int = 1,
        duration: timedelta = timedelta(hours=24),
        transaction_rate: float = 0.1,
        base_port: int = 5000,
        failure_rate: float = 0.1
    ):
        self.real_buyers = real_buyers
        self.sim_buyers = sim_buyers
        self.sim_sellers = sim_sellers
        self.duration = duration
        self.transaction_rate = transaction_rate
        self.base_port = base_port
        self.failure_rate = failure_rate

class MarketSimulationController:
    def __init__(self, config: SimulationConfig):
        self.config = config
        self.running = False
        self.logger = logging.getLogger(f'{self.__class__.__name__}')
        self.setup_logging()
        
        # Initialize client lists
        self.real_clients: List[BuyerClient] = []
        self.simulated_clients: List[SimulatedClient] = []
        self.simulated_sellers: List[SimulatedSeller] = []

    def setup_logging(self):
        """Setup debug logging"""
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.DEBUG)

    def setup_mixed_clients(self, real_buyers: int, sim_buyers: int):
        """Setup both real and simulated buyers"""
        try:
            # Setup sellers first
            self.setup_sellers()
            time.sleep(1)  # Give sellers time to initialize
            
            # Start real clients
            for i in range(real_buyers):
                try:
                    client = BuyerClient('localhost', self.config.base_port)
                    self.logger.info(f"Created BuyerClient {i}")
                    
                    client.connect()
                    time.sleep(0.1)  # Brief delay between connections
                    
                    if client.register():
                        self.real_clients.append(client)
                        self.logger.info(f"Successfully registered real client {i}")
                    else:
                        self.logger.error(f"Failed to register real client {i}")
                        
                except Exception as e:
                    self.logger.error(f"Failed to setup real client {i}: {e}")
                    continue

            # Start simulated clients
            for i in range(sim_buyers):
                try:
                    client = SimulatedClient(
                        node_id=f"sim_client_{i}",
                        controller=self
                    )
                    client.connect()
                    time.sleep(0.1)  # Brief delay between connections
                    self.simulated_clients.append(client)
                    self.logger.info(f"Started simulated client {i}")
                    
                except Exception as e:
                    self.logger.error(f"Failed to setup simulated client {i}: {e}")
                    continue

        except Exception as e:
            self.logger.error(f"Error setting up clients: {e}")
            raise

    def setup_sellers(self):
        """Setup simulated sellers"""
        try:
            for i in range(self.config.sim_sellers):
                seller = SimulatedSeller(
                    node_id=f"sim_seller_{i+1}",
                    controller=self
                )
                seller.connect()
                self.simulated_sellers.append(seller)
                self.logger.info(f"Started simulated seller {i+1}")
                time.sleep(0.1)  # Brief delay between sellers
        except Exception as e:
            self.logger.error(f"Error setting up sellers: {e}")
            raise

    def handle_simulated_message(self, client, message: Message):
        """Handle messages from simulated clients"""
        try:
            self.logger.debug(f"Processing simulated message type: {message.type} from {client.node_id}")
            
            if isinstance(client, (SimulatedClient, SimulatedSeller)):
                # Send the message using client's connection
                client.send_message(message)
                
                # Wait for and process response
                response = client.wait_for_response()
                if response:
                    client.process_update(response)
                    return response
                    
        except Exception as e:
            self.logger.error(f"Error handling simulated message: {e}")
            error_message = Message(
                type=MessageType.ERROR,
                data={"error": str(e)},
                sender_id="server"
            )
            client.process_update(error_message)

    def run_mixed_simulation(self):
        """Run simulation with both types of clients"""
        self.running = True
        self.logger.info("Starting mixed simulation")
        
        try:
            while self.running:
                # Process real clients
                for client in self.real_clients:
                    if random.random() < self.config.transaction_rate:
                        try:
                            # List items first
                            client.list_items()
                            time.sleep(0.1)  # Wait for response
                            
                            # Then attempt purchase if items available
                            if client.available_items:
                                item_type = random.choice([
                                    item["name"] for item in client.available_items
                                ])
                                quantity = random.uniform(0.5, 2.0)
                                client.attempt_purchase(item_type, quantity)
                                
                        except Exception as e:
                            self.logger.error(f"Error in real client action: {e}")

                # Process simulated buyers
                for client in self.simulated_clients:
                    if random.random() < self.config.transaction_rate:
                        try:
                            # List items
                            list_msg = Message(
                                type=MessageType.LIST_ITEMS,
                                data={},
                                sender_id=client.node_id
                            )
                            response = self.handle_simulated_message(client, list_msg)
                            
                            # Try to buy if items available
                            if response and response.type == MessageType.LIST_ITEMS:
                                items = response.data.get("items", [])
                                if items:
                                    item = random.choice(items)
                                    buy_msg = Message(
                                        type=MessageType.BUY_REQUEST,
                                        data={
                                            "item_id": item["item_id"],
                                            "quantity": random.uniform(0.5, 2.0)
                                        },
                                        sender_id=client.node_id
                                    )
                                    self.handle_simulated_message(client, buy_msg)
                                    
                        except Exception as e:
                            self.logger.error(f"Error in simulated buyer action: {e}")

                # Process simulated sellers
                for seller in self.simulated_sellers:
                    try:
                        if not seller.current_sale and random.random() < 0.2:
                            item_type = random.choice(list(ItemType))
                            quantity = random.uniform(3.0, 8.0)
                            sale_msg = Message(
                                type=MessageType.SALE_START,
                                data={
                                    "name": item_type.value,
                                    "quantity": quantity
                                },
                                sender_id=seller.node_id
                            )
                            self.handle_simulated_message(seller, sale_msg)
                            
                    except Exception as e:
                        self.logger.error(f"Error in simulated seller activity: {e}")

                # Add some randomness to timing
                time.sleep(random.uniform(0.5, 1.5))

        except Exception as e:
            self.logger.error(f"Simulation error: {e}")
        finally:
            self.cleanup()

    def cleanup(self):
        """Cleanup simulation resources"""
        self.logger.info("Cleaning up simulation...")
        self.running = False
        
        # Cleanup clients
        for client in self.real_clients:
            try:
                client.disconnect()
            except:
                pass

        for client in self.simulated_clients:
            try:
                client.disconnect()
            except:
                pass

        for seller in self.simulated_sellers:
            try:
                seller.disconnect()
            except:
                pass