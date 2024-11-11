import socket
import logging
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, Optional

from src.core.Market.market_manager import MarketManager
from src.core.Queue.event_queue import EventQueue
from src.core.Server.client import ClientInfo
from src.core.Server.client_type import ClientType
from src.core.Server.client_state import ClientState
from src.core.Server.message import Message
from src.core.Server.message_type import MessageType
from src.core.Server.message_encoder import MessageEncoder
from src.core.Market.item_type import ItemType

class Server:
    def __init__(self, host: str, port: int, queue: EventQueue):
        self.host = host
        self.port = port
        self.queue = queue
        self.server_socket = None
        self.is_running = False
        self.clients: Dict[str, ClientInfo] = {}
        self.next_node_id = 0
        self.thread_lock = threading.Lock()
        self.max_clients = 200
        self.thread_pool = ThreadPoolExecutor(max_workers=self.max_clients)
        self.active_clients = set()
        self.market_manager = MarketManager()
        self.logger = logging.getLogger(__name__)

    def start_server(self) -> None:
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(self.max_clients)
            self.is_running = True
            
            accept_thread = threading.Thread(target=self.accept_connections)
            accept_thread.daemon = True
            accept_thread.start()
            
            self.logger.info(f"Server started on {self.host}:{self.port}")
        except Exception as e:
            self.logger.error(f"Failed to start server: {e}")
            raise

    def accept_connections(self) -> None:
        while self.is_running:
            try:
                client_socket, client_address = self.server_socket.accept()
                client_socket.setblocking(True)
                
                with self.thread_lock:
                    self.active_clients.add(client_socket)
                
                self.thread_pool.submit(self.handle_client, client_socket, client_address)
                self.logger.info(f"Accepted connection from {client_address}")
                
            except Exception as e:
                if self.is_running:
                    self.logger.error(f"Error accepting connection: {e}")

    def handle_client(self, client_socket: socket.socket, client_address: tuple[str, int]) -> None:
        client_id = None
        try:
            message = self.receive_message(client_socket)
            if message.type != MessageType.REGISTER:
                raise ValueError("First message must be registration")

            client_type = ClientType(message.data["client_type"])
            client_id = f"{client_type.value}_{self.next_node_id}"
            self.next_node_id += 1

            client_info = ClientInfo(
                socket=client_socket,
                address=client_address,
                client_type=client_type,
                state=ClientState.REGISTERED,
                node_id=client_id
            )

            with self.thread_lock:
                self.clients[client_id] = client_info

            # Initialize seller resources if needed
            if client_type == ClientType.SELLER:
                self.market_manager.initialize_seller_stock(client_id)

            # Send registration acknowledgment
            ack_message = Message(
                type=MessageType.ACK,
                data={"node_id": client_id},
                sender_id="server"
            )
            self.send_message(client_socket, ack_message)

            # Main message handling loop
            while self.is_running:
                message = self.receive_message(client_socket)
                if client_type == ClientType.BUYER:
                    self.handle_buyer_message(message, client_info)
                else:
                    self.handle_seller_message(message, client_info)

        except ConnectionError:
            self.logger.info(f"Client {client_address} disconnected")
        except Exception as e:
            self.logger.error(f"Error handling client {client_address}: {e}")
        finally:
            if client_id:
                self.remove_client(client_id)

    def handle_buyer_message(self, message: Message, client_info: ClientInfo) -> None:
        try:
            if message.type == MessageType.LIST_ITEMS:
                items = self.market_manager.get_active_items()
                response = Message(
                    type=MessageType.LIST_ITEMS,
                    data={"items": items},
                    sender_id="server"
                )
                self.send_message(client_info.socket, response)

            elif message.type == MessageType.BUY_REQUEST:
                success = self.market_manager.handle_buy_request(
                    message.data["item_id"],
                    message.data["quantity"],
                    client_info.node_id
                )
                
                response = Message(
                    type=MessageType.BUY_RESPONSE,
                    data={
                        "success": success,
                        "item_id": message.data["item_id"],
                        "quantity": message.data["quantity"],
                    },
                    sender_id="server"
                )
                self.send_message(client_info.socket, response)

                if success:
                    item = self.market_manager.get_item_by_id(message.data["item_id"])
                    if item:
                        self.broadcast_stock_update(item)

        except Exception as e:
            self.logger.error(f"Error handling buyer message: {e}")
            self.send_error(client_info.socket, str(e))

    def handle_seller_message(self, message: Message, client_info: ClientInfo) -> None:
        try:
            if message.type == MessageType.SALE_START:
                item_type = ItemType.from_string(message.data["name"])
                quantity = float(message.data["quantity"])
                item = self.market_manager.start_sale(
                    client_info.node_id,
                    item_type,
                    quantity
                )
                
                response = Message(
                    type=MessageType.SALE_START,
                    data={
                        "success": True,
                        "item_id": item.item_id,
                        "name": item.item_type.value,
                        "quantity": item.quantity,
                        "remaining_time": item.get_remaining_time()
                    },
                    sender_id="server"
                )
                self.send_message(client_info.socket, response)
                self.broadcast_stock_update(item)

            elif message.type == MessageType.SALE_END:
                self.market_manager.end_sale(message.data["item_id"])
                response = Message(
                    type=MessageType.SALE_END,
                    data={"success": True},
                    sender_id="server"
                )
                self.send_message(client_info.socket, response)

        except Exception as e:
            self.logger.error(f"Error handling seller message: {e}")
            self.send_error(client_info.socket, str(e))

    def broadcast_stock_update(self, item) -> None:
        """Broadcast stock update to all buyers"""
        update = Message(
            type=MessageType.STOCK_UPDATE,
            data=item.to_dict(),
            sender_id="server"
        )
        
        for client_info in self.clients.values():
            if client_info.client_type == ClientType.BUYER:
                try:
                    self.send_message(client_info.socket, update)
                except Exception as e:
                    self.logger.error(f"Failed to send update to {client_info.node_id}: {e}")

    def send_message(self, client_socket: socket.socket, message: Message) -> None:
        try:
            data = MessageEncoder.serialize(message)
            length = len(data)
            length_bytes = length.to_bytes(4, byteorder='big')
            
            # Send as one complete message
            complete_message = length_bytes + data
            client_socket.sendall(complete_message)
            
            self.logger.debug(f"Sent message type: {message.type}")
        except Exception as e:
            self.logger.error(f"Failed to send message: {e}")
            raise

    def receive_message(self, client_socket: socket.socket) -> Message:
        try:
            # Receive length
            length_bytes = self._recv_all(client_socket, 4)
            if not length_bytes:
                raise ConnectionError("Connection closed")
            
            length = int.from_bytes(length_bytes, byteorder='big')
            
            # Receive data
            data = self._recv_all(client_socket, length)
            if not data:
                raise ConnectionError("Connection closed")
                
            return MessageEncoder.deserialize(data)
            
        except Exception as e:
            self.logger.error(f"Failed to receive message: {e}")
            raise

    def _recv_all(self, sock: socket.socket, n: int) -> bytes:
        """Helper function to receive n bytes or return None if EOF is hit"""
        data = bytearray()
        while len(data) < n:
            packet = sock.recv(n - len(data))
            if not packet:
                return None
            data.extend(packet)
        return bytes(data)

    def send_error(self, client_socket: socket.socket, error_msg: str) -> None:
        error_message = Message(
            type=MessageType.ERROR,
            data={"error": error_msg},
            sender_id="server"
        )
        try:
            self.send_message(client_socket, error_message)
        except Exception as e:
            self.logger.error(f"Failed to send error message: {e}")

    def remove_client(self, client_id: str) -> None:
        try:
            with self.thread_lock:
                if client_id in self.clients:
                    client_info = self.clients[client_id]
                    self.active_clients.remove(client_info.socket)
                    client_info.socket.close()
                    del self.clients[client_id]
                    self.logger.info(f"Removed client {client_id}")
        except Exception as e:
            self.logger.error(f"Error removing client {client_id}: {e}")

    def stop_server(self) -> None:
        self.logger.info("Stopping server...")
        self.is_running = False
        
        # Close all client connections
        for client_info in list(self.clients.values()):
            try:
                client_info.socket.close()
            except:
                pass
                
        # Close server socket
        if self.server_socket:
            try:
                self.server_socket.close()
            except:
                pass
            
        self.thread_pool.shutdown(wait=True)