import logging
from src.core.CLI.market_place import MarketplaceCLI
from src.core.Client.seller_client import SellerClient
import time


class SellerCLI(MarketplaceCLI):
    def __init__(self):
        super().__init__()
        self.setup_logging()
        host, port = self.get_server_details()
        self.client = SellerClient(host, port)

    def setup_logging(self):
        """Setup debug logging"""
        self.logger = logging.getLogger(__name__)
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.DEBUG)

    def print_help(self) -> None:
        print("\nAvailable commands:")
        print("start <item_name> <quantity> - Start selling an item")
        print("status - Show current sale status")
        print("stock - Show current stock levels")
        print("end - End current sale")
        print("debug on|off - Toggle debug logging")
        print("help - Show this help message")
        print("quit - Exit the marketplace")

    def run(self) -> None:
        """Run the seller CLI"""
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
                try:
                    command = input("\nEnter command: ").strip().lower()
                    parts = command.split()

                    match parts:
                        case ["start", item_name, quantity]:
                            self._start_sale(item_name, quantity)

                        case ["status"]:
                            self._show_status()

                        case ["stock"]:
                            self._show_stock()

                        case ["end"]:
                            self._end_sale()

                        case ["debug", setting]:
                            self._toggle_debug(setting)

                        case ["help"]:
                            self.print_help()

                        case ["quit"]:
                            break

                        case _:
                            print("Invalid command. Type 'help' for available commands")

                except Exception as e:
                    self.logger.error(f"Error executing command: {e}", exc_info=True)
                    print(f"Error: {e}")

        except Exception as e:
            self.logger.error(f"Fatal error: {e}", exc_info=True)
            print(f"Fatal error: {e}")
        finally:
            self.client.disconnect()

    def _start_sale(self, item_name: str, quantity_str: str):
        """Start sale with debug info"""
        try:
            quantity = float(quantity_str)
            self.logger.debug(f"Starting sale: {item_name} x {quantity}")
            self.client.start_sale(item_name, quantity)
            print(f"Started sale of {item_name}")
            self._show_status()
        except ValueError as e:
            print(f"Error: Invalid quantity - {e}")
        except Exception as e:
            self.logger.error(f"Failed to start sale: {e}", exc_info=True)
            print(f"Error: {e}")

    def _show_status(self):
        """Show detailed sale status"""
        if not self.client.current_item:
            print("\nNo active sale")
            return

        print("\nCurrent Sale:")
        for key, value in self.client.current_item.items():
            print(f"{key}: {value}")
        self.logger.debug(f"Full sale state: {self.client.current_item}")

    def _show_stock(self):
        """Show detailed stock information"""
        print("\nStock Levels:")
        if hasattr(self.client, "current_stock"):
            for item, qty in self.client.current_stock.items():
                print(f"{item}: {qty}")
            self.logger.debug(f"Full stock data: {self.client.current_stock}")
        else:
            print("Stock information not available")

    def _end_sale(self):
        """End sale with debug info"""
        try:
            self.client.end_sale()
            print("Sale ended")
            self.logger.debug("Sale ended successfully")
        except Exception as e:
            self.logger.error(f"Failed to end sale: {e}", exc_info=True)
            print(f"Error: {e}")

    def _toggle_debug(self, setting: str):
        """Toggle debug logging"""
        if setting == "on":
            self.logger.setLevel(logging.DEBUG)
            print("Debug logging enabled")
        elif setting == "off":
            self.logger.setLevel(logging.INFO)
            print("Debug logging disabled")
        else:
            print("Invalid debug setting. Use 'debug on' or 'debug off'")
