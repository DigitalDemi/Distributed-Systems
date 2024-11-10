from src.core.CLI.market_place import MarketplaceCLI
from src.core.Client.buyer_client import BuyerClient
import logging

class BuyerCLI(MarketplaceCLI):
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        host, port = self.get_server_details()
        self.client = BuyerClient(host, port)
        
    def print_help(self) -> None:
        print("\nAvailable commands:")
        print("list - List available items")
        print("buy <item_id> <quantity> - Buy an item")
        print("help - Show this help message")
        print("quit - Exit the marketplace")
        
    def run(self) -> None:
        """Run the buyer CLI"""
        try:
            print("Connecting to market...")
            self.client.connect()

            print("Connected! Registering...")
            self.client.register()

            if not self.client.registered:
                print("Failed to register with the market")
                return

            print("Connected to marketplace!")
            self.print_help()
            
            while True:
                command = input("\nEnter command: ").strip().lower()
                
                match command.split():
                    case ["list"]:
                        try:
                            self.client.list_items()
                            self._display_items()
                        except Exception as e:
                            print(f"Error: {e}")
                        
                    case ["buy", item_id, quantity]:
                        try:
                            self.client.buy_item(item_id, float(quantity))
                            print("Purchase successful")
                        except Exception as e:
                            print(f"Error: {e}")
                            
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
            
    def _display_items(self) -> None:
        """Display available items"""
        if not self.client.available_items:
            print("\nNo items available")
            return
            
        print("\nAvailable Items:")
        for item in self.client.available_items:
            print(f"ID: {item['item_id']}")
            print(f"Name: {item['name']}")
            print(f"Quantity: {item['quantity']}")
            print(f"Time remaining: {item.get('remaining_time', 0):.1f}s")
            print("-" * 20)
