import socket
import logging
from src.core.Queue.event_queue import EventQueue

class Server:
    host: str
    port: int
    queue : EventQueue
    server_socket  : socket.socket | None
    is_running: bool
    logger: logging.Logger

    def __init__(self, host: str, port: int, queue: EventQueue):
        self.logger =  logging.getLogger(__name__)
        self.host = host
        self.port = port
        self.queue = queue
        self.server_socket = None
        self.is_running = False

    def socket_init(self):
        try:
            self.server_socket = socket.socket(family=socket.AF_INET,type=socket.SOCK_STREAM)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen()
            self.logger.info(f"Failed to initialise on {self.host} : {self.port}")
        except socket.error as e:
            self.logger.error(f"Failed to init socket: {e}")
            self.cleanup()
            raise

    def cleanup(self) -> None:
        if self.server_socket:
            try: 
                self.server_socket.close()
            except socket.error as e:
                self.logger.error(f"Error closing server socket: {e}")
            finally: 
                self.server_socket = None
        self.is_running =  False

    def accept_connection(self) -> tuple[socket.socket, tuple[str, int]]:
        if self.server_socket is None:
            self.logger.error("Server socket is not initialized")
            raise RuntimeError("Server socket is not initialized")
        try:
            return self.server_socket.accept()
        except socket.error as e: 
            self.logger.error(f"Socket accept failed : {e}")
            raise RuntimeError(f"Socket accept failed : {e}")

    def accept_connections(self):
        while self.is_running:
            try:
                client_socket, client_address = self.accept_connection()
                self.logger.info(f"New connection from {client_address}")
            except RuntimeError as e: 
                print(f"Runtime error: {e}")
            except socket.error as e: 
                self.logger.error(f"Socket error: {e}")
                self.cleanup()
            except Exception as e: 
                self.logger.error(f"Unexcepted error: {e}")
                self.cleanup()
                break
