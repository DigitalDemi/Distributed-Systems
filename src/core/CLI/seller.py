from src.core.CLI.market_place import MarketplaceCLI
from src.core.Client.seller_client import SellerClient
import time
import logging

class SellerCLI(MarketplaceCLI):
    def __init__(self):
        super().__init__()
        host, port = self.get_server_details()
        self.logger = logging.getLogger(__name__)
        logging.basicConfig(level=logging.DEBUG)
        self.client = SellerClient(host, port)
        
    def print_help(self) -> None:
        print("\nAvailable commands:")
        print("start <item_name> <quantity> - Start selling an item")
        print("update <quantity> - Update current item quantity")
        print("end - End current sale")
        print("status - Show current sale status")
        print("help - Show this help message")
        print("quit - Exit the marketplace")
        
    def run(self) -> None:
        """Run the seller CLI"""
        try:
            print("Connecting to market...")
            self.client.connect()
            
            print("Connected! Registering...")
            self.client.register()  # This will now wait for registration to complete
            
            if not self.client.registered:
                print("Failed to register with the market")
                return
                
            print("Connected to marketplace!")
            self.print_help()
            
            while True:
                command = input("\nEnter command: ").strip().lower()
                
                match command.split():
                    case ["start", item_name, quantity]:
                        try:
                            self.client.start_sale(item_name, float(quantity))
                            print(f"Started sale of {item_name}")
                        except ValueError as e:
                            print(f"Error: {e}")
                        except RuntimeError as e:
                            print(f"Error: {e}")

                    case ["stock"]:
                        self._display_stock()
                            
                    case ["update", quantity]:
                        try:
                            self.client.update_stock(float(quantity))
                            print("Stock updated")
                        except ValueError as e:
                            print(f"Error: {e}")
                        except RuntimeError as e:
                            print(f"Error: {e}")
                            
                    case ["end"]:
                        try:
                            self.client.end_sale()
                            print("Sale ended")
                        except RuntimeError as e:
                            print(f"Error: {e}")
                            
                    case ["status"]:
                        self._display_status()
                        
                    case ["help"]:
                        self.print_help()
                        
                    case ["quit"]:
                        break
                        
                    case _:
                        print("Invalid command. Type 'help' for available commands")
                        
        except Exception as e:
            self.logger.error(f"Error: {e}")
            print(f"Error: {e}")
        finally:
            self.client.disconnect()
            
    def _display_status(self) -> None:
        """Display current sale status"""
        if not self.client.current_item:
            print("No active sale")
            return
            
        item = self.client.current_item
        print("\nCurrent Sale:")
        print(f"Item: {item['name']}")
        print(f"Quantity: {item['quantity']}")

    def _display_stock(self) -> None:
        """Display current stock levels"""
        if not self.client.current_stock:
            print("Stock information not available")
            return
            
        print("\nCurrent Stock Levels:")
        for item_name, quantity in self.client.current_stock.items():
            print(f"{item_name}: {quantity}")
