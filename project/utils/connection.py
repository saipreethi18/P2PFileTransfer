import socket
import time
import threading
from utils.message import (
    Message,
    Choke,
    Unchoke,
    Interested,
    NotInterested,
    Have,
    Request,
    Piece,
    Handshake,
)
from utils.log_manager import LogManager


class ConnectionManager:
    @staticmethod
    def send_message(peer_id, target_peer_id, socket, msg_type, payload=b""):
        try:
            if msg_type is None:
                raise ValueError("Message type is None. Cannot send message.")

            message_name = Message.get_message_type_name(msg_type)

            if payload is None:
                LogManager.log(
                    peer_id,
                    f"Warning: Payload for message {message_name} is None. Defaulting to empty payload.",
                )
                payload = b""

            message = Message.create_message(msg_type, payload)
            if message is None:
                raise ValueError(
                    f"Failed to create message {message_name}. Message object is None."
                )

            if socket is None:
                LogManager.log(
                    peer_id,
                    f"Socket is None. Cannot send message {message_name} to Peer {target_peer_id}.",
                )
                return

            socket.sendall(message)
            LogManager.log(
                peer_id,
                f"Peer {peer_id} successfully sent message {message_name} to Peer {target_peer_id}. Payload Length: {len(payload)}",
            )
        except BrokenPipeError:
            LogManager.log(
                peer_id,
                f"Broken pipe error while sending message {message_name} to Peer {target_peer_id}. Peer may have disconnected.",
            )
        except ValueError as ve:
            LogManager.log(
                peer_id,
                f"Validation error while sending message {message_name} to Peer {target_peer_id}: {ve}",
            )
        except Exception as e:
            LogManager.log(
                peer_id,
                f"Unexpected error sending message {message_name} to Peer {target_peer_id}: {e}",
            )

    @staticmethod
    def receive_message(peer_id, source_peer_id, socket):
        try:
            LogManager.log(
                peer_id,
                f"Peer {peer_id} waiting to receive a message header from Peer {source_peer_id}...",
            )

            header = socket.recv(4)
            if not header:
                LogManager.log(
                    peer_id,
                    f"Connection closed by Peer {source_peer_id}. No header received.",
                )
                return None

            length = int.from_bytes(header, "big")
            if length <= 0:
                raise ValueError(
                    f"Invalid message length received: {length} from Peer {source_peer_id}"
                )

            LogManager.log(
                peer_id,
                f"Message length {length} bytes received from Peer {source_peer_id}. Receiving full message...",
            )

            data = b""
            while len(data) < length:
                chunk = socket.recv(length - len(data))
                if not chunk:
                    raise ConnectionError(
                        f"Connection closed by Peer {source_peer_id} before full message was received."
                    )
                data += chunk

            msg_type, payload = Message.parse_message(header + data)
            message_name = Message.get_message_type_name(msg_type)

            LogManager.log(
                peer_id,
                f"Peer {peer_id} received message {message_name} from Peer {source_peer_id}. Payload Length: {len(payload)}",
            )
            return msg_type, payload
        except socket.timeout:
            LogManager.log(
                peer_id,
                f"Socket timed out while waiting for a message from Peer {source_peer_id}.",
            )
            return None
        except ConnectionResetError:
            LogManager.log(peer_id, f"Connection reset by Peer {source_peer_id}.")
            return None
        except ValueError as ve:
            LogManager.log(
                peer_id, f"Message validation error from Peer {source_peer_id}: {ve}"
            )
            return None
        except Exception as e:
            LogManager.log(
                peer_id,
                f"Unexpected error while receiving message from Peer {source_peer_id}: {e}",
            )
            return None


class ServerListener:
    def __init__(self, peer_id, port, peer_manager):
        self.peer_id = peer_id
        self.port = port
        self.peer_manager = peer_manager
        self.server_socket = None
        self.running = True

    def start(self):
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind(("localhost", self.port))
            self.server_socket.listen(5)
            LogManager.log(
                self.peer_id, f"Peer {self.peer_id} listening on port {self.port}..."
            )

            while self.running:
                conn, addr = self.server_socket.accept()
                LogManager.log(
                    self.peer_id,
                    f"Peer {self.peer_id} is connected from Peer at {addr}.",
                )
                threading.Thread(
                    target=self.handle_connection, args=(conn, addr)
                ).start()
        except Exception as e:
            LogManager.log(self.peer_id, f"Error starting server listener: {e}")
        finally:
            if self.server_socket:
                self.server_socket.close()

    def stop(self):
        self.running = False
        if self.server_socket:
            self.server_socket.close()

    def handle_connection(self, conn, addr):
        try:
            handshake_data = conn.recv(32)
            peer_id = Handshake.parse_handshake(handshake_data)
            LogManager.log(self.peer_id, f"Handshake received from Peer {peer_id}.")
            LogManager.log(
                self.peer_id, f"Peer {self.peer_id} is connected from Peer {peer_id}."
            )
            self.peer_manager.add_peer(self.peer_id, conn=None)
            self.peer_manager.add_peer(peer_id, conn)
            self.send_bitfield(conn, peer_id)

            while True:
                result = ConnectionManager.receive_message(self.peer_id, peer_id, conn)
                if result is None:
                    LogManager.log(
                        self.peer_id, f"Connection closed by Peer {peer_id}."
                    )
                    break
                msg_type, payload = result
                self.handle_message(conn, peer_id, msg_type, payload)
        except Exception as e:
            LogManager.log(self.peer_id, f"Error handling connection from {addr}: {e}")
        finally:
            conn.close()

    def send_bitfield(self, conn, target_peerid):
        bitfield = self.peer_manager.get_bitfield()
        if bitfield:
            LogManager.log(self.peer_id, "Sending BITFIELD message.")
            ConnectionManager.send_message(
                self.peer_id, target_peerid, conn, Message.BITFIELD, bytearray(bitfield)
            )

    def handle_message(self, conn, peer_id, msg_type, payload):
        try:
            if msg_type == Message.INTERESTED:
                LogManager.log(
                    self.peer_id,
                    f"Peer {self.peer_id} received the 'interested' message from Peer {peer_id}.",
                )
                self.peer_manager.mark_peer_interested(peer_id)

                self.send_unchoke(conn, peer_id)

            elif msg_type == Message.NOT_INTERESTED:
                LogManager.log(
                    self.peer_id,
                    f"Peer {self.peer_id} received the 'not interested' message from Peer {peer_id}.",
                )
                self.peer_manager.mark_peer_not_interested(peer_id)
                self.send_choke(conn, peer_id)

            elif msg_type == Message.HAVE:
                piece_index = int.from_bytes(payload[7:10], "big")
                LogManager.log(
                    self.peer_id,
                    f"Peer {self.peer_id} received the 'have' message from Peer {peer_id} for the piece {piece_index}.",
                )
                self.peer_manager.update_peer_bitfield(peer_id, piece_index)

            elif msg_type == Message.REQUEST:
                piece_index = int.from_bytes(payload[7:10], "big")
                LogManager.log(self.peer_id, f"Extracted piece index: {piece_index}")

                if piece_index < 0 or piece_index >= self.peer_manager.total_pieces:
                    LogManager.log(
                        self.peer_id,
                        f"Invalid piece index {piece_index} requested by Peer {peer_id}.",
                    )
                    return
                if self.peer_manager.is_peer_choked(peer_id):
                    LogManager.log(
                        self.peer_id,
                        f"Cannot send piece {piece_index} to Peer {peer_id}: Peer is choked.",
                    )
                else:
                    piece_data = self.peer_manager.file_manager.get_piece(piece_index)
                    if piece_data:
                        piece_message = Piece.create(piece_index, piece_data)
                        ConnectionManager.send_message(
                            self.peer_id, peer_id, conn, Message.PIECE, piece_message
                        )
                    else:
                        LogManager.log(self.peer_id, f"Piece {piece_index} not found.")

            elif msg_type == Message.CHOKE:
                LogManager.log(
                    self.peer_id, f"Peer {self.peer_id} is choked by Peer {peer_id}."
                )
                self.peer_manager.mark_peer_choked(peer_id)

            elif msg_type == Message.UNCHOKE:
                LogManager.log(
                    self.peer_id, f"Peer {self.peer_id} is unchoked by Peer {peer_id}."
                )
                self.peer_manager.mark_peer_unchoked(self.peer_id)
            elif msg_type == Message.BITFIELD:
                LogManager.log(self.peer_id, f"Received BITFIELD from Peer {peer_id}.")
                peer_bitfield = list(payload)
                self.peer_manager.connected_peers[peer_id]["bitfield"] = peer_bitfield
                LogManager.log(
                    self.peer_id, f"Updated Peer {peer_id}'s bitfield: {peer_bitfield}"
                )

        except Exception as e:
            LogManager.log(self.peer_id, f"Error handling message: {e}")

    def send_choke(self, target_peer_id, conn):
        LogManager.log(self.peer_id, "Sending CHOKE message.")
        ConnectionManager.send_message(
            self.peer_id, target_peer_id, conn, Message.CHOKE
        )

    def send_unchoke(self, conn, peer_id):
        LogManager.log(self.peer_id, f"Sending UNCHOKE message to Peer {peer_id}.")
        try:

            ConnectionManager.send_message(self.peer_id, peer_id, conn, Message.UNCHOKE)
            self.peer_manager.mark_peer_unchoked(peer_id)

        except Exception as e:
            LogManager.log(
                self.peer_id, f"Failed to send UNCHOKE message to Peer {peer_id}: {e}"
            )

    def trigger_have(self, target_peer_id, piece_index):
        payload = piece_index.to_bytes(4, "big")
        for peer_id, peer_info in self.peer_manager.connected_peers.items():
            ConnectionManager.send_message(
                self.peer_id, target_peer_id, peer_info["socket"], Message.HAVE, payload
            )
            LogManager.log(
                self.peer_id,
                f"Peer {self.peer_id} sent 'have' message for piece {piece_index} to Peer {peer_id}.",
            )


class ClientListener:
    def __init__(self, peer_id, all_peer_ids, peer_ports, peer_manager):
        self.peer_id = peer_id
        self.all_peer_ids = all_peer_ids
        self.peer_ports = peer_ports
        self.peer_manager = peer_manager

    def connect_to_peers(self):
        for target_peer_id in self.all_peer_ids:
            if target_peer_id != self.peer_id:
                port = self.peer_ports[target_peer_id]
                threading.Thread(
                    target=self.connect_to_peer, args=(target_peer_id, port)
                ).start()

    def connect_to_peer(self, target_peer_id, port):
        try:
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.connect(("localhost", port))

            handshake = Handshake.create_handshake(self.peer_id)
            client_socket.sendall(handshake)
            LogManager.log(
                self.peer_id,
                f"Peer {self.peer_id} makes a connection to Peer {target_peer_id}.",
            )

            self.peer_manager.add_peer(self.peer_id, conn=None)
            self.peer_manager.add_peer(target_peer_id, client_socket)

            self.send_bitfield(client_socket, target_peer_id)
            LogManager.log(
                self.peer_id,
                f"Waiting to receive BITFIELD message from Peer {target_peer_id}...",
            )
            bitfield_message = ConnectionManager.receive_message(
                self.peer_id, target_peer_id, client_socket
            )
            if bitfield_message:
                LogManager.log(
                    self.peer_id, f"Received BITFIELD message: {bitfield_message}"
                )
            else:
                LogManager.log(
                    self.peer_id,
                    f"Failed to receive BITFIELD message from Peer {target_peer_id}.",
                )

            if bitfield_message and bitfield_message[0] == Message.BITFIELD:
                peer_bitfield = list(bitfield_message[1])
                LogManager.log(
                    self.peer_id,
                    f"Peer {self.peer_id} received the BITFIELD message from Peer {target_peer_id}.",
                )
                for i, bit in enumerate(peer_bitfield):
                    if bit == 1:
                        self.peer_manager.update_peer_bitfield(target_peer_id, i)
            else:
                LogManager.log(
                    self.peer_id,
                    f"Peer {self.peer_id} did not receive BITFIELD from Peer {target_peer_id}. Using an empty bitfield.",
                )
                peer_bitfield = [0] * self.peer_manager.total_pieces

            if self.is_interested(peer_bitfield):
                ConnectionManager.send_message(
                    self.peer_id, target_peer_id, client_socket, Message.INTERESTED
                )
                LogManager.log(
                    self.peer_id,
                    f"Peer {self.peer_id} sent the 'interested' message to Peer {target_peer_id}.",
                )
            else:
                ConnectionManager.send_message(
                    self.peer_id, target_peer_id, client_socket, Message.NOT_INTERESTED
                )
                LogManager.log(
                    self.peer_id,
                    f"Peer {self.peer_id} sent the 'not interested' message to Peer {target_peer_id}.",
                )

            threading.Thread(
                target=self.handle_messages, args=(client_socket, target_peer_id)
            ).start()

        except Exception as e:
            LogManager.log(
                self.peer_id, f"Error connecting to Peer {target_peer_id}: {e}"
            )

    def send_bitfield(self, conn, target_peer_id):
        bitfield = self.peer_manager.get_bitfield()
        if bitfield:
            LogManager.log(self.peer_id, "Sending BITFIELD message.")
            ConnectionManager.send_message(
                self.peer_id,
                target_peer_id,
                conn,
                Message.BITFIELD,
                bytearray(bitfield),
            )
        else:
            LogManager.log(self.peer_id, "No BITFIELD to send.")

    def is_interested(self, peer_bitfield):
        for i in range(len(peer_bitfield)):
            if peer_bitfield[i] == 1 and self.peer_manager.bitfield[i] == 0:
                return True
        return False

    def handle_messages(self, conn, target_peer_id):
        try:
            while True:
                result = ConnectionManager.receive_message(
                    self.peer_id, target_peer_id, conn
                )
                if result is None:
                    LogManager.log(
                        self.peer_id, f"Connection closed by Peer {target_peer_id}."
                    )
                    break

                msg_type, payload = result
                if msg_type == Message.CHOKE:
                    LogManager.log(
                        self.peer_id,
                        f"Peer {self.peer_id} is choked by Peer {target_peer_id}.",
                    )
                    self.peer_manager.mark_peer_choked(target_peer_id)

                elif msg_type == Message.UNCHOKE:
                    LogManager.log(
                        self.peer_id,
                        f"Peer {self.peer_id} is unchoked by Peer {target_peer_id}.",
                    )
                    self.peer_manager.mark_peer_unchoked(self.peer_id)
                    self.peer_manager.mark_peer_unchoked(target_peer_id)
                    LogManager.log(
                        self.peer_id,
                        f"Peer {self.peer_id} is requesting pieces from Peer {target_peer_id}.",
                    )
                    self.request_pieces(conn, target_peer_id)

                elif msg_type == Message.HAVE:
                    piece_index = int.from_bytes(payload[:4], "big")
                    LogManager.log(
                        self.peer_id,
                        f"Peer {self.peer_id} received the 'have' message from Peer {target_peer_id} for the piece {piece_index}.",
                    )
                    self.peer_manager.update_peer_bitfield(target_peer_id, piece_index)

                elif msg_type == Message.PIECE:
                    piece_index = int.from_bytes(payload[6:9], "big")
                    piece_data = payload[9:]
                    LogManager.log(
                        self.peer_id,
                        f"Extracted piece index: {piece_index}, Piece data length: {len(piece_data)}",
                    )
                    self.peer_manager.file_manager.save_piece(piece_index, piece_data)
                    self.peer_manager.mark_piece_downloaded(piece_index, target_peer_id)
                    self.trigger_have(target_peer_id, piece_index)

                elif msg_type == Message.NOT_INTERESTED:
                    LogManager.log(
                        self.peer_id,
                        f"Peer {self.peer_id} received the 'not interested' message from Peer {target_peer_id}.",
                    )

                elif msg_type == Message.INTERESTED:
                    LogManager.log(
                        self.peer_id,
                        f"Peer {self.peer_id} received the 'interested' message from Peer {target_peer_id}.",
                    )
                    if self.peer_manager.is_peer_choked(target_peer_id):
                        LogManager.log(
                            self.peer_id,
                            f"Sending UNCHOKE message to Peer {target_peer_id}.",
                        )
                        ConnectionManager.send_message(
                            self.peer_id, target_peer_id, conn, Message.UNCHOKE
                        )
                        self.peer_manager.mark_peer_unchoked(target_peer_id)

                else:
                    LogManager.log(
                        self.peer_id,
                        f"Unknown message type received from Peer {target_peer_id}: {msg_type}",
                    )
        except Exception as e:
            LogManager.log(
                self.peer_id,
                f"Error processing message from Peer {target_peer_id}: {e}",
            )
        finally:
            LogManager.log(
                self.peer_id, f"Closing connection with Peer {target_peer_id}."
            )
            conn.close()

    def request_pieces(self, conn, target_peer_id):
        try:
            for piece_index in range(self.peer_manager.total_pieces):
                with self.peer_manager.lock:
                    if piece_index < 0 or piece_index >= self.peer_manager.total_pieces:
                        LogManager.log(
                            self.peer_id, f"Invalid piece index {piece_index} received."
                        )
                        return
                    is_needed = self.peer_manager.bitfield[piece_index] == 0
                    is_available = (
                        self.peer_manager.connected_peers[target_peer_id]["bitfield"][
                            piece_index
                        ]
                        == 1
                    )
                    is_not_choked = not self.peer_manager.is_peer_choked(target_peer_id)

                    if is_needed and is_available and is_not_choked:
                        request_message = Request.create(piece_index)
                        ConnectionManager.send_message(
                            self.peer_id,
                            target_peer_id,
                            conn,
                            Message.REQUEST,
                            request_message,
                        )
                        LogManager.log(
                            self.peer_id,
                            f"Peer {self.peer_id} requested piece {piece_index} from Peer {target_peer_id}.",
                        )
                        time.sleep(0.1)
        except Exception as e:
            LogManager.log(
                self.peer_id, f"Error requesting pieces from Peer {target_peer_id}: {e}"
            )

    def trigger_have(self, target_peer_id, piece_index):
        payload = piece_index.to_bytes(4, "big")
        for peer_id, peer_info in self.peer_manager.connected_peers.items():
            if peer_id != self.peer_id:
                if peer_info["socket"] is not None:
                    ConnectionManager.send_message(
                        self.peer_id,
                        peer_id,
                        peer_info["socket"],
                        Message.HAVE,
                        payload,
                    )
                    LogManager.log(
                        self.peer_id,
                        f"Peer {self.peer_id} sent 'have' message for piece {piece_index} to Peer {peer_id}.",
                    )
                else:
                    LogManager.log(
                        self.peer_id,
                        f"Socket is None. Cannot send message HAVE to Peer {peer_id}.",
                    )
