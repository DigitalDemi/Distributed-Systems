import logging


class MarketplaceCLI:
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def get_server_details(self) -> tuple[str, int]:
        """Get server connection details from user"""
        host = input("Enter server host (default: localhost): ").strip() or "localhost"
        while True:
            try:
                port = int(input("Enter server port: ").strip())
                return host, port
            except ValueError:
                print("Please enter a valid port number")

    def print_help(self) -> None:
        """Print available commands"""
        pass
