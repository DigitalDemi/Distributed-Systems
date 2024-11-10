import time

from src.core.CLI.market_place import MarketplaceCLI
from src.core.Client.seller_client import SellerClient


class SellerCLI(MarketplaceCLI):
    def __init__(self):
        super().__init__()
        host, port = self.get_server_details()
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
            self.client.register()
            
            print("Connected to marketplace!")
            self.print_help()
            
            while True:
                command = input("\nEnter command: ").strip().lower()
                
                match command.split():
                    case ["start", item_name, quantity]:
                        try:
                            self.client.start_sale(item_name, float(quantity))
                            print(f"Started sale of {item_name}")
                        except ValueError:
                            print("Invalid quantity")
                        except RuntimeError as e:
                            print(f"Error: {e}")
                            
                    case ["update", quantity]:
                        try:
                            self.client.update_stock(float(quantity))
                            print("Stock updated")
                        except ValueError:
                            print("Invalid quantity")
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
        finally:
            self.client.disconnect()
            
    def _display_status(self) -> None:
        """Display current sale status"""
        if not self.client.current_item:
            print("No active sale")
            return
            
        item = self.client.current_item
        print("\nCurrent Sale:")
        print(f"Item: {item.name}")
        print(f"Quantity: {item.quantity}")
        print(f"Time remaining: {item.max_sale_duration - (time.time() - item.sale_start_time):.1f}s")
