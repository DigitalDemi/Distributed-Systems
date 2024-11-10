from src.core.CLI.buying import BuyerCLI
from src.core.CLI.seller import SellerCLI

def run_buyer():
    cli = BuyerCLI()
    cli.run()

def run_seller():
    cli = SellerCLI()
    cli.run()

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2 or sys.argv[1] not in ["buyer", "seller"]:
        print("Usage: python client_main.py [buyer|seller]")
        sys.exit(1)
        
    if sys.argv[1] == "buyer":
        run_buyer()
    else:
        run_seller()
