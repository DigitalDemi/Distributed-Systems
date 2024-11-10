import time
from src.core.Server.server import Server
from src.core.Queue.event_queue import EventQueue

if __name__ == "__main__":
    queue = EventQueue()
    server = Server("localhost", 5000, queue)
    
    try:
        server.start_server()
        print("Server started on localhost:5000")
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Shutting down server...")
        server.stop_server()
