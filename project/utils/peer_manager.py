from utils.log_manager import LogManager
from utils.connection import ConnectionManager
from utils.message import Message
from threading import Lock
import random
import time


class PeerManager:
    def __init__(self, peer_id, total_pieces, file_manager):
        self.peer_id = peer_id
        self.total_pieces = total_pieces
        self.file_manager = file_manager
        self.connected_peers = {}
        self.bitfield = [0] * total_pieces
        self.downloaded_pieces = set()
        self.lock = Lock()

    def initialize_peer_bitfield(self, complete):
        try:
            with self.lock:
                self.bitfield = (
                    [1] * self.total_pieces if complete else [0] * self.total_pieces
                )
                LogManager.log(self.peer_id, f"Bitfield initialized: {self.bitfield}")
        except Exception as e:
            LogManager.log(self.peer_id, f"Error initializing bitfield: {e}")
            raise

    def add_peer(self, peer_id, conn):
        try:
            with self.lock:
                if peer_id not in self.connected_peers:
                    self.connected_peers[peer_id] = {
                        "socket": conn,
                        "bitfield": [0] * self.total_pieces,
                        "status": "connected",
                        "choked": True,
                        "interested": False,
                    }
                    LogManager.log(
                        self.peer_id, f"Added Peer {peer_id} to connections."
                    )
                else:
                    LogManager.log(self.peer_id, f"Peer {peer_id} already exists.")
        except Exception as e:
            LogManager.log(self.peer_id, f"Error adding Peer {peer_id}: {e}")
            raise

    def remove_peer(self, peer_id):
        try:
            with self.lock:
                if peer_id in self.connected_peers:
                    del self.connected_peers[peer_id]
                    LogManager.log(self.peer_id, f"Removed Peer {peer_id}.")
                else:
                    LogManager.log(
                        self.peer_id,
                        f"Attempted to remove non-existent Peer {peer_id}.",
                    )
        except Exception as e:
            LogManager.log(self.peer_id, f"Error removing Peer {peer_id}: {e}")
            raise

    def update_peer_bitfield(self, peer_id, piece_index):
        try:
            with self.lock:
                if (
                    peer_id in self.connected_peers
                    and 0 <= piece_index < self.total_pieces
                ):
                    self.connected_peers[peer_id]["bitfield"][piece_index] = 1
                    LogManager.log(
                        self.peer_id,
                        f"Updated bitfield of Peer {peer_id} for piece {piece_index}.",
                    )
                else:
                    LogManager.log(
                        self.peer_id,
                        f"Invalid operation for Peer {peer_id} or piece {piece_index}.",
                    )
        except Exception as e:
            LogManager.log(
                self.peer_id, f"Error updating bitfield for Peer {peer_id}: {e}"
            )
            raise

    def mark_piece_downloaded(self, piece_index, sender_peer_id=None):
        try:
            if 0 <= piece_index < self.total_pieces:
                self.bitfield[piece_index] = 1
                self.downloaded_pieces.add(piece_index)
                message = f"Downloaded piece {piece_index}."
                if sender_peer_id:
                    message += f" Source: Peer {sender_peer_id}."
                LogManager.log(self.peer_id, message)
                if len(self.downloaded_pieces) == self.total_pieces:
                    LogManager.log(
                        self.peer_id, "Download of complete file is complete."
                    )
            else:
                LogManager.log(self.peer_id, f"Invalid piece index: {piece_index}")
        except Exception as e:
            LogManager.log(
                self.peer_id, f"Error marking piece {piece_index} as downloaded: {e}"
            )
            raise

    def get_peers_with_piece(self, piece_index):
        try:
            if 0 <= piece_index < self.total_pieces:
                with self.lock:
                    peers = [
                        peer_id
                        for peer_id, peer in self.connected_peers.items()
                        if peer["bitfield"][piece_index] == 1
                    ]
                LogManager.log(self.peer_id, f"Peers with piece {piece_index}: {peers}")
                return peers
            LogManager.log(self.peer_id, f"Invalid piece index: {piece_index}")
            return []
        except Exception as e:
            LogManager.log(
                self.peer_id, f"Error retrieving peers with piece {piece_index}: {e}"
            )
            raise

    def all_pieces_downloaded(self):
        try:
            with self.lock:
                return len(self.downloaded_pieces) == self.total_pieces
        except Exception as e:
            LogManager.log(self.peer_id, f"Error checking downloaded pieces: {e}")
            raise

    def get_bitfield(self):
        try:
            with self.lock:
                return self.bitfield.copy()
        except Exception as e:
            LogManager.log(self.peer_id, f"Error retrieving bitfield: {e}")
            raise

    def mark_peer_choked(self, peer_id):
        try:
            with self.lock:
                if peer_id in self.connected_peers:
                    self.connected_peers[peer_id]["choked"] = True
                    LogManager.log(self.peer_id, f"Marked Peer {peer_id} as choked.")
                else:
                    LogManager.log(self.peer_id, f"Peer {peer_id} is not connected.")
        except Exception as e:
            LogManager.log(self.peer_id, f"Error marking Peer {peer_id} as choked: {e}")
            raise

    def mark_peer_unchoked(self, peer_id):
        try:
            with self.lock:
                if peer_id in self.connected_peers:
                    self.connected_peers[peer_id]["choked"] = False
                    LogManager.log(self.peer_id, f"Marked Peer {peer_id} as unchoked.")
                else:
                    LogManager.log(self.peer_id, f"Peer {peer_id} is not connected.")
        except Exception as e:
            LogManager.log(
                self.peer_id, f"Error marking Peer {peer_id} as unchoked: {e}"
            )
            raise

    def is_peer_choked(self, peer_id):
        try:
            peer_info = self.connected_peers.get(peer_id)
            return peer_info.get("choked", True) if peer_info else True
        except Exception as e:
            LogManager.log(
                self.peer_id, f"Error checking if Peer {peer_id} is choked: {e}"
            )
            raise

    def mark_peer_interested(self, peer_id):
        try:
            with self.lock:
                if peer_id in self.connected_peers:
                    self.connected_peers[peer_id]["interested"] = True
                    LogManager.log(
                        self.peer_id, f"Marked Peer {peer_id} as interested."
                    )
                else:
                    LogManager.log(self.peer_id, f"Peer {peer_id} is not connected.")
        except Exception as e:
            LogManager.log(
                self.peer_id, f"Error marking Peer {peer_id} as interested: {e}"
            )
            raise

    def mark_peer_not_interested(self, peer_id):
        try:
            with self.lock:
                if peer_id in self.connected_peers:
                    self.connected_peers[peer_id]["interested"] = False
                    LogManager.log(
                        self.peer_id, f"Marked Peer {peer_id} as not interested."
                    )
                else:
                    LogManager.log(self.peer_id, f"Peer {peer_id} is not connected.")
        except Exception as e:
            LogManager.log(
                self.peer_id, f"Error marking Peer {peer_id} as not interested: {e}"
            )
            raise

    def get_choked_peers(self):
        with self.lock:
            return [
                peer_id
                for peer_id, info in self.connected_peers.items()
                if info["choked"]
            ]

    def optimistic_unchoking(self):
        try:
            choked_peers = [
                peer_id
                for peer_id, info in self.connected_peers.items()
                if info["choked"] and peer_id != self.peer_id
            ]
            if not choked_peers:
                LogManager.log(self.peer_id, "No choked peers available for optimistic unchoking.")
                return

            optimistic_peer = random.choice(choked_peers)

            self.mark_peer_unchoked(optimistic_peer)
            ConnectionManager.send_message(
                self.peer_id,
                optimistic_peer,  # Target peer ID
                self.connected_peers[optimistic_peer]["socket"],
                Message.UNCHOKE,
            )
            LogManager.log(
                self.peer_id,
                f"Peer {self.peer_id} optimistically unchoked Peer {optimistic_peer}.",
            )
        except Exception as e:
            LogManager.log(self.peer_id, f"Error during optimistic unchoking: {e}")
