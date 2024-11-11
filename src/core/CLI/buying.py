import logging
from src.core.CLI.market_place import MarketplaceCLI
from src.core.Client.buyer_client import BuyerClient


class BuyerCLI(MarketplaceCLI):
    def __init__(self):
        super().__init__()
        self.setup_logging()
        host, port = self.get_server_details()
        self.client = BuyerClient(host, port)

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
        print("list - List available items")
        print("status - Show current market status")
        print("buy <item_name> <quantity> - Buy an item")
        print("debug on|off - Toggle debug logging")
        print("help - Show this help message")
        print("quit - Exit the marketplace")

    def run(self) -> None:
        """Run the buyer CLI"""
        try:
            print("Connecting to market...")
            self.client.connect()

            print("Connected! Registering...")
            if not self.client.register():
                print("Failed to register with the market")
                return

            print("Connected to marketplace!")
            self.print_help()

            while True:
                try:
                    command = input("\nEnter command: ").strip().lower()
                    parts = command.split()

                    match parts:
                        case ["list"]:
                            self._list_items()

                        case ["status"]:
                            self._show_status()

                        case ["buy", item_name, quantity]:
                            self._buy_item(item_name, quantity)

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

    def _list_items(self):
        """List available items with debug info"""
        try:
            self.client.list_items()
            if not self.client.available_items:
                print("\nNo items available")
                self.logger.debug("Received empty items list")
                return

            print("\nAvailable Items:")
            for item in self.client.available_items:
                print(f"ID: {item.get('item_id', 'unknown')}")
                print(f"Name: {item.get('name', 'unknown')}")
                print(f"Quantity: {item.get('quantity', 0)}")
                print(f"Time remaining: {item.get('remaining_time', 0):.1f}s")
                print("-" * 20)

            self.logger.debug(f"Raw items data: {self.client.available_items}")
        except Exception as e:
            self.logger.error(f"Error listing items: {e}", exc_info=True)
            print(f"Error: {e}")

    def _buy_item(self, item_name: str, quantity_str: str):
        """Buy item with debug info"""
        try:
            quantity = float(quantity_str)
            self.logger.debug(f"Attempting to buy {quantity} of {item_name}")
            self.client.attempt_purchase(item_name, quantity)
            print("Purchase successful!")
        except ValueError as e:
            print(f"Error: Invalid quantity - {e}")
        except Exception as e:
            self.logger.error(f"Purchase failed: {e}", exc_info=True)
            print(f"Error: {e}")

    def _show_status(self):
        """Show detailed market status"""
        try:
            print("\nMarket Status:")
            print(f"Connected: {self.client.connected}")
            print(f"Registered: {self.client.registered}")
            print(f"Node ID: {self.client.node_id}")
            print("\nAvailable Items Count:", len(self.client.available_items))
            self.logger.debug(f"Full client state: {vars(self.client)}")
        except Exception as e:
            self.logger.error(f"Error showing status: {e}", exc_info=True)
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
