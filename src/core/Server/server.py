import socket
import logging
import threading
from concurrent.futures import ThreadPoolExecutor
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
        self.server_thread: threading.Thread | None = None
        self.client_threads: list[threading.Thread] = []
        self.thread_lock:threading.Lock = threading.Lock()
        self.max_clients = 200
        self.thread_pool = ThreadPoolExecutor(max_workers=self.max_clients)
        self.active_client: set[socket.socket] = set()

    def start_server(self) -> None:
        self.socket_init()
        self.is_running = True
        self.server_thread = threading.Thread(target=self.accept_connections)
        self.server_thread.start()
        self.logger.info("Server Started")

    def stop_server(self) -> None:
        self.logger.info("Stopping server...")
        self.is_running = False
        for client in list(self.active_client):
            self.cleanup_client(client, ("unknown", 0))
        self.thread_pool.shutdown(wait=True)
        self.cleanup()

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

    def cleanup_client(self, client_socket: socket.socket, client_address: tuple[str, int]) -> None:
        try:
            client_socket.close()
            with self.thread_lock:
                self.active_client.remove(client_socket)
            self.logger.info(f"Cleaned up client {client_address}")
        except Exception as e:
            self.logger.error(f"Error cleaning up client {client_address}: {e}")

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
                if len(self.active_client) >= self.max_clients:
                    self.logger.warning("Maxium client reached, rejecting connection")
                    client_socket.close()
                    continue

                with self.thread_lock:
                    self.active_client.add(client_socket)

                future = self.thread_pool.submit(
                        self.handle_client,
                        client_socket,
                        client_address
                        )
                self.logger.info(f"New connection from {client_address}")
            except Exception as e: 
                self.logger.error(f"Unexcepted error: {e}")

    def handle_client(self, client_socket: socket.socket, client_address: tuple[str,int]) -> None:
        try:
            pass
        except Exception as e:
            self.logger.error(f"Error handling client {client_address} : {e}")
        finally:
            client_socket.close()
