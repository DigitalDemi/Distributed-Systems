import logging
from src.core.CLI.buying import BuyerCLI
from src.core.CLI.seller import SellerCLI


def setup_logging():
    """Setup root logging configuration"""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler()],
    )


def run_buyer():
    setup_logging()
    cli = BuyerCLI()
    cli.run()


def run_seller():
    setup_logging()
    cli = SellerCLI()
    cli.run()


def main():
    import sys

    if len(sys.argv) != 2 or sys.argv[1] not in ["buyer", "seller"]:
        print("Usage: python client_main.py [buyer|seller]")
        return 1

    try:
        if sys.argv[1] == "buyer":
            run_buyer()
        else:
            run_seller()
    except Exception as e:
        logging.error(f"Fatal error: {e}", exc_info=True)
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
