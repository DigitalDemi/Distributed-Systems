import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.Server.server import Server
from core.Queue.event_queue import EventQueue
import time

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
