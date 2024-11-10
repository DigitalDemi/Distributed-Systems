import socket
import logging
import threading
import time

from dataclasses import dataclass, asdict

from concurrent.futures import ThreadPoolExecutor
from src.core.Market.item_type import ItemType
from src.core.Queue.event import Event
from src.core.Queue.event_type import EventType
from src.core.Queue.event_queue import EventQueue
from src.core.Server.client import ClientInfo
from src.core.Server.client_type import ClientType
from src.core.Server.client_state import ClientState
from src.core.Server.message import Message
from src.core.Server.message_type import MessageType
from src.core.Server.message_encoder import MessageEncoder
from src.core.Server.market_item import MarketItem
from src.core.Market.market_manager import MarketManager


class Server:
    host: str
    port: int
    queue: EventQueue
    server_socket: socket.socket | None
    is_running: bool
    logger: logging.Logger

    def __init__(self, host: str, port: int, queue: EventQueue):
        self.logger = logging.getLogger(__name__)
        self.host = host
        self.port = port
        self.queue = queue
        self.server_socket = None
        self.server_thread = None
        self.is_running = False
        self.thread_lock = threading.Lock()
        self.max_clients = 200
        self.thread_pool = ThreadPoolExecutor(max_workers=self.max_clients)
        self.active_client = set()
        self.next_node_id = 0
        self.clients: dict[str, ClientInfo] = {}
        self.market_manager = MarketManager()

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
            self.server_socket = socket.socket(
                family=socket.AF_INET, type=socket.SOCK_STREAM
            )
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
        self.is_running = False

    def cleanup_client(
        self, client_socket: socket.socket, client_address: tuple[str, int]
    ) -> None:
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

                _ = self.thread_pool.submit(
                    self.handle_client, client_socket, client_address
                )
                self.logger.info(f"New connection from {client_address}")
            except Exception as e:
                self.logger.error(f"Unexcepted error: {e}")

    def register_client(
        self,
        client_socket: socket.socket,
        client_address: tuple[str, int],
        client_type: ClientType,
    ) -> str:
        """Register a new client and initialize their resources"""
        with self.thread_lock:
            try:
                # Generate node ID
                node_id = f"{client_type.value}_{self.next_node_id}"
                self.next_node_id += 1

                # Create client info
                client_info = ClientInfo(
                    socket=client_socket,
                    address=client_address,
                    client_type=client_type,
                    state=ClientState.REGISTERED,
                    node_id=node_id,
                )

                # Store client info
                self.clients[node_id] = client_info

                # Initialize seller resources
                if client_type == ClientType.SELLER:
                    self.market_manager.initialize_seller_stock(
                        node_id, initial_quantity=5.0
                    )
                    self.logger.info(f"Initialized stock for seller {node_id}")

                # Log registration
                self.logger.info(
                    f"Registered new {client_type.value} with ID: {node_id}"
                )

                return node_id

            except Exception as e:
                self.logger.error(f"Failed to register client: {e}")
                raise

    def handle_client(
        self, client_socket: socket.socket, client_address: tuple[str, int]
    ) -> None:
        """Handle individual client connection"""
        client_id = None
        registration_complete = False

        try:
            while self.is_running:
                message = self.receive_message(client_socket)

                # Handle registration first
                if not registration_complete:
                    if message.type == MessageType.REGISTER:
                        client_type = ClientType(message.data["client_type"])
                        client_id = self.register_client(
                            client_socket, client_address, client_type
                        )

                        # Send acknowledgment
                        ack_message = Message(
                            type=MessageType.ACK,
                            data={"node_id": client_id},
                            sender_id="server",
                        )
                        self.send_message(client_socket, ack_message)
                        registration_complete = True
                        continue
                    else:
                        raise ValueError("First message must be registration")

                # Handle regular messages after registration
                client_info = self.clients.get(client_id)
                if not client_info:
                    raise ValueError("Client not found")

                if client_info.client_type == ClientType.BUYER:
                    self.handle_buyer_message(message, client_info)
                else:
                    self.handle_seller_message(message, client_info)

        except Exception as e:
            self.logger.error(f"Error handling client {client_address}: {e}")
        finally:
            if client_id:
                self.remove_client(client_id)
            try:
                client_socket.close()
            except:
                pass

    def remove_client(self, client_id: str) -> None:
        """Remove client and cleanup resources"""
        try:
            with self.thread_lock:
                if client_id in self.clients:
                    client_info = self.clients[client_id]
                    self.active_client.remove(client_info.socket)
                    client_info.socket.close()
                    del self.clients[client_id]
                    self.logger.info(f"Removed client {client_id}")
        except Exception as e:
            self.logger.error(f"Error removing client {client_id}: {e}")

    def send_message(self, client_socket: socket.socket, message: Message) -> None:
        """Send message to client"""
        try:
            data = MessageEncoder.serialize(message)
            # Send message length first
            length = len(data)
            client_socket.send(length.to_bytes(4, byteorder="big"))
            # Send actual message
            client_socket.send(data)
        except Exception as e:
            self.logger.error(f"Failed to send message: {e}")
            raise

    def receive_message(self, client_socket: socket.socket) -> Message:
        """Receive message from client"""
        try:
            # Receive message length first
            length_bytes = client_socket.recv(4)
            if not length_bytes:
                raise ConnectionError("Connection closed by client")

            length = int.from_bytes(length_bytes, byteorder="big")

            # Receive message data
            data = b""
            while len(data) < length:
                chunk = client_socket.recv(min(length - len(data), 4096))
                if not chunk:
                    raise ConnectionError("Connection closed during receive")
                data += chunk

            return MessageEncoder.deserialize(data)
        except Exception as e:
            self.logger.error(f"Failed to receive message: {e}")
            raise

    def handle_buyer_message(self, message: Message, client_info: ClientInfo) -> None:
        """Handle messages from buyer clients"""
        try:
            match message.type:
                case MessageType.LIST_ITEMS:
                    self.handle_list_items_request(client_info)

                case MessageType.BUY_REQUEST:
                    self.handle_buy_request(message.data, client_info)

                case MessageType.BUYER_MARKET_LEAVE:
                    self.remove_client(client_info.node_id)

                case _:
                    self.logger.warning(f"Unknown buyer message type: {message.type}")
                    self.send_error(client_info.socket, "Invalid message type")

        except Exception as e:
            self.logger.error(f"Error handling buyer message: {e}")
            self.send_error(client_info.socket, str(e))

    def handle_seller_message(self, message: Message, client_info: ClientInfo) -> None:
        """Handle messages from seller clients"""
        try:
            match message.type:
                case MessageType.STOCK_UPDATE:
                    self.handle_stock_update(message.data, client_info)

                case MessageType.SALE_START:
                    self.handle_sale_start(message.data, client_info)

                case MessageType.SALE_END:
                    self.handle_sale_end(client_info)

                case _:
                    self.logger.warning(f"Unknown seller message type: {message.type}")
                    self.send_error(client_info.socket, "Invalid message type")

        except Exception as e:
            self.logger.error(f"Error handling seller message: {e}")
            self.send_error(client_info.socket, str(e))

    def broadcast_to_all(self, message: Message) -> None:
        """Broadcast message to all connected clients"""
        with self.thread_lock:
            for client in self.clients.values():
                try:
                    self.send_message(client.socket, message)
                except Exception as e:
                    self.logger.error(f"Failed to broadcast to {client.node_id}: {e}")

    def broadcast_to_buyers(self, message: Message) -> None:
        """Broadcast message to all buyers"""
        with self.thread_lock:
            buyers = self.get_clients_by_type(ClientType.BUYER)
            for buyer in buyers:
                try:
                    self.send_message(buyer.socket, message)
                except Exception as e:
                    self.logger.error(
                        f"Failed to broadcast to buyer {buyer.node_id}: {e}"
                    )

    def broadcast_to_sellers(self, message: Message) -> None:
        """Broadcast message to all sellers"""
        with self.thread_lock:
            sellers = self.get_clients_by_type(ClientType.SELLER)
            for seller in sellers:
                try:
                    self.send_message(seller.socket, message)
                except Exception as e:
                    self.logger.error(
                        f"Failed to broadcast to seller {seller.node_id}: {e}"
                    )

    def send_error(self, client_socket: socket.socket, error_msg: str) -> None:
        """Send error message to client"""
        error_message = Message(
            type=MessageType.ERROR, data={"error": error_msg}, sender_id="server"
        )
        try:
            self.send_message(client_socket, error_message)
        except Exception as e:
            self.logger.error(f"Failed to send error message: {e}")

    def handle_list_items_request(self, client_info: ClientInfo) -> None:
        """Handle request to list available items"""
        try:
            active_items = self.market_manager.get_active_items()

            response = Message(
                type=MessageType.LIST_ITEMS,
                data={"items": [item.to_dict() for item in active_items]},
                sender_id="server",
            )

            self.send_message(client_info.socket, response)

        except Exception as e:
            self.logger.error(f"Error handling list items request: {e}")
            self.send_error(client_info.socket, "Failed to list items")

    def handle_stock_update(self, data: dict, client_info: ClientInfo) -> None:
        """Handle seller stock update"""
        try:
            item_id = data["item_id"]
            quantity = data["quantity"]

            with self.thread_lock:
                if item_id in self.active_sales:
                    item = self.active_sales[item_id]
                    item.quantity = quantity
                    self.broadcast_stock_update(item)

        except Exception as e:
            self.logger.error(f"Error handling stock update: {e}")
            self.send_error(client_info.socket, str(e))

    def handle_sale_end(self, client_info: ClientInfo) -> None:
        """Handle seller ending a sale"""
        try:
            with self.thread_lock:
                # Find seller's active sale
                seller_items = [
                    item
                    for item in self.active_sales.values()
                    if item.seller_id == client_info.node_id
                ]

                for item in seller_items:
                    # Remove from active sales
                    del self.active_sales[item.item_id]

                    # Notify all buyers
                    end_notification = Message(
                        type=MessageType.SALE_END,
                        data={"item_id": item.item_id},
                        sender_id="server",
                    )
                    self.broadcast_to_buyers(end_notification)

        except Exception as e:
            self.logger.error(f"Error handling sale end: {e}")
            self.send_error(client_info.socket, str(e))

    def handle_sale_timeout(self, item_id: str) -> None:
        """Handle sale timeout after max duration"""
        try:
            with self.thread_lock:
                if item_id in self.active_sales:
                    item = self.active_sales[item_id]
                    seller = self.clients[item.seller_id]
                    self.handle_sale_end(seller)

        except Exception as e:
            self.logger.error(f"Error handling sale timeout: {e}")

    def get_active_items(self) -> list[MarketItem]:
        """Get list of all active items for sale"""
        with self.thread_lock:
            return list(self.active_sales.values())

    def handle_seller_message(self, message: Message, client_info: ClientInfo) -> None:
        """Handle messages from seller clients"""
        try:
            match message.type:
                case MessageType.STOCK_UPDATE:
                    self.handle_stock_update(message.data, client_info)

                case MessageType.SALE_START:
                    self.handle_sale_start(message.data, client_info)

                case MessageType.SALE_END:
                    self.handle_sale_end(client_info)

                case _:
                    self.logger.warning(f"Unknown seller message type: {message.type}")
                    self.send_error(client_info.socket, "Invalid message type")

        except Exception as e:
            self.logger.error(f"Error handling seller message: {e}")
            self.send_error(client_info.socket, str(e))

    def handle_buyer_message(self, message: Message, client_info: ClientInfo) -> None:
        """Handle messages from buyer clients"""
        try:
            match message.type:
                case MessageType.LIST_ITEMS:
                    self.handle_list_items_request(client_info)

                case MessageType.BUY_REQUEST:
                    self.handle_buy_request(message.data, client_info)

                case _:
                    self.logger.warning(f"Unknown buyer message type: {message.type}")
                    self.send_error(client_info.socket, "Invalid message type")

        except Exception as e:
            self.logger.error(f"Error handling buyer message: {e}")
            self.send_error(client_info.socket, str(e))

    def handle_sale_start(self, data: dict, client_info: ClientInfo) -> None:
        """Handle seller starting a new sale"""
        try:
            item_type = ItemType.from_string(data["name"])
            quantity = float(data["quantity"])

            # Start the sale
            item = self.market_manager.start_sale(
                client_info.node_id, item_type, quantity
            )

            # Send confirmation to seller
            confirm_msg = Message(
                type=MessageType.SALE_START,
                data={
                    "success": True,
                    "item_id": item.item_id,
                    "name": item.item_type.value,
                    "quantity": item.quantity,
                    "remaining_time": item.get_remaining_time(),
                },
                sender_id="server",
            )
            self.send_message(client_info.socket, confirm_msg)

            # Broadcast stock update to buyers
            stock_msg = Message(
                type=MessageType.STOCK_UPDATE, data=item.to_dict(), sender_id="server"
            )
            self.broadcast_to_buyers(stock_msg)

        except Exception as e:
            error_msg = str(e)
            self.logger.error(f"Error handling sale start: {error_msg}")
            error_response = Message(
                type=MessageType.ERROR, data={"error": error_msg}, sender_id="server"
            )
            self.send_message(client_info.socket, error_response)

    def handle_buy_request(self, data: dict, client_info: ClientInfo) -> None:
        """Handle buyer purchase request"""
        try:
            item_id = data["item_id"]
            quantity = float(data["quantity"])

            # Attempt purchase
            success = self.market_manager.try_purchase(item_id, quantity)
            if not success:
                raise ValueError("Purchase failed - insufficient quantity")

            item = self.market_manager.active_items[item_id]

            # Notify seller
            purchase_notification = Message(
                type=MessageType.BUY_RESPONSE,
                data={
                    "buyer_id": client_info.node_id,
                    "item_id": item_id,
                    "quantity": quantity,
                    "remaining": item.quantity,
                },
                sender_id="server",
            )

            seller = self.clients[item.seller_id]
            self.send_message(seller.socket, purchase_notification)

            # Send confirmation to buyer
            buy_confirmation = Message(
                type=MessageType.BUY_RESPONSE,
                data={"item_id": item_id, "quantity": quantity, "success": True},
                sender_id="server",
            )
            self.send_message(client_info.socket, buy_confirmation)

            # Notify all buyers of updated stock
            self.broadcast_stock_update(item)

            # Check if item is sold out
            if item.quantity == 0:
                next_item = self.market_manager.end_sale(item_id)
                if next_item:
                    self.broadcast_stock_update(next_item)

        except Exception as e:
            error_msg = str(e)
            self.logger.error(f"Error handling buy request: {error_msg}")
            error_response = Message(
                type=MessageType.ERROR, data={"error": error_msg}, sender_id="server"
            )
            self.send_message(client_info.socket, error_response)

    def broadcast_stock_update(self, item: MarketItem) -> None:
        """Broadcast item stock update to all buyers"""
        update_message = Message(
            type=MessageType.STOCK_UPDATE, data=item.to_dict(), sender_id="server"
        )
        self.broadcast_to_buyers(update_message)

    def get_clients_by_type(self, client_type: ClientType) -> list[ClientInfo]:
        """Get all clients of a specific type"""
        with self.thread_lock:
            return [
                client
                for client in self.clients.values()
                if client.client_type == client_type
            ]

    def handle_client_error(self, client_info: ClientInfo, error: Exception) -> None:
        """Handle client errors with recovery attempts"""
        try:
            error_msg = str(error)
            self.logger.error(f"Error for client {client_info.node_id}: {error_msg}")

            # Send error to client
            error_message = Message(
                type=MessageType.ERROR, data={"error": error_msg}, sender_id="server"
            )
            self.send_message(client_info.socket, error_message)

            # Handle specific error types
            if isinstance(error, ConnectionError):
                self.remove_client(client_info.node_id)
            elif isinstance(error, ValueError):
                # Invalid request - client can continue
                pass
            else:
                # Unknown error - log and continue
                self.logger.warning(f"Unknown error type: {type(error)}")

        except Exception as e:
            self.logger.error(f"Error handling client error: {e}")
            self.remove_client(client_info.node_id)
