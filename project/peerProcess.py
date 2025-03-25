import threading
import signal
import sys
import time
from utils.file_manager import FileManager
from utils.log_manager import LogManager
from utils.peer_manager import PeerManager
from utils.connection import ServerListener, ClientListener, ConnectionManager
from utils.message import Have, Message


class PeerProcess:
    def __init__(self, peer_id):
        self.peer_id = peer_id
        self.file_manager = None
        self.peer_manager = None
        self.bitfield = None
        self.client_listener = None
        self.server_listener = None
        self.total_pieces = None
        self.file_name = None
        self.piece_size = None
        self.port = None
        self.has_complete_file = None

    def initialize(self):
        try:
            LogManager.log(self.peer_id, "Initializing peer process...")
            common_config = FileManager.parse_common_config()
            peer_info = FileManager.parse_peer_info()
            self.file_name = common_config.get("filename")
            self.piece_size = int(common_config.get("piecesize"))
            file_size = int(common_config.get("filesize"))
            self.total_pieces = -(-file_size // self.piece_size)
            self.port = peer_info[self.peer_id]["port"]
            self.has_complete_file = peer_info[self.peer_id]["has_file"]
            self.file_manager = FileManager(
                self.peer_id, self.piece_size, self.file_name, self.total_pieces
            )
            self.peer_manager = PeerManager(
                self.peer_id, self.total_pieces, self.file_manager
            )
            self.bitfield = [1 if self.has_complete_file else 0] * self.total_pieces
            LogManager.log(self.peer_id, "Peer process initialized successfully.")
        except Exception as e:
            LogManager.log(self.peer_id, f"Failed to initialize peer process: {e}")
            raise

    def start_server_listener(self):
        try:
            self.server_listener = ServerListener(
                self.peer_id, self.port, self.peer_manager
            )
            server_thread = threading.Thread(
                target=self.server_listener.start, daemon=True
            )
            server_thread.start()
            LogManager.log(self.peer_id, "Server listener started successfully.")
        except Exception as e:
            LogManager.log(self.peer_id, f"Error starting server listener: {e}")
            raise

    def start_client_listener(self):
        try:
            peer_info = FileManager.parse_peer_info()
            self.client_listener = ClientListener(
                self.peer_id,
                list(peer_info.keys()),
                {pid: data["port"] for pid, data in peer_info.items()},
                self.peer_manager,
            )
            client_thread = threading.Thread(
                target=self.client_listener.connect_to_peers, daemon=True
            )
            client_thread.start()
            LogManager.log(self.peer_id, "Client listener started successfully.")
        except Exception as e:
            LogManager.log(self.peer_id, f"Error starting client listener: {e}")
            raise

    def announce_pieces(self):
        try:
            for i in range(self.total_pieces):
                have_message = Have.create(i)
                for target_peer_id, conn in self.peer_manager.connected_peers.items():
                    if conn["socket"]:
                        ConnectionManager.send_message(
                            self.peer_id,
                            target_peer_id,
                            conn["socket"],
                            Message.HAVE,
                            have_message,
                        )
            LogManager.log(
                self.peer_id, "Announced available pieces to connected peers."
            )
        except Exception as e:
            LogManager.log(self.peer_id, f"Error announcing pieces: {e}")
            raise

    def handle_shutdown(self, stop_event):
        while not stop_event.is_set():
            stop_event.wait(1)
        if self.server_listener:
            self.server_listener.stop()
        if self.client_listener:
            LogManager.log(self.peer_id, "Client listener stopped.")
        LogManager.log(self.peer_id, "Peer process exited cleanly.")

    def start(self):
        try:
            LogManager.start_logger(self.peer_id)
            self.initialize()

            if self.has_complete_file:
                self.file_manager.initialize_pieces(has_complete_file=True)
                self.peer_manager.initialize_peer_bitfield(complete=True)
            else:
                self.file_manager.initialize_pieces(has_complete_file=False)
                self.peer_manager.initialize_peer_bitfield(complete=False)

            self.start_server_listener()
            self.start_client_listener()

            if self.has_complete_file:
                self.announce_pieces()
            # common_config = FileManager.parse_common_config()
            # optimistic_interval = int(common_config.get("optimisticunchokinginterval"))
            # self.start_optimistic_unchoking(self.peer_manager, optimistic_interval)
            stop_event = threading.Event()
            signal.signal(signal.SIGINT, lambda s, f: stop_event.set())
            signal.signal(signal.SIGTERM, lambda s, f: stop_event.set())
            self.handle_shutdown(stop_event)
        except Exception as e:
            LogManager.log(self.peer_id, f"Error during peer process execution: {e}")
            raise
    def start_optimistic_unchoking(self,peer_manager, interval):
        def run_unchoking():
            while True:
                time.sleep(interval)
                peer_manager.optimistic_unchoking()

        threading.Thread(target=run_unchoking, daemon=True).start()


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python PeerProcess.py <peerID>")
        sys.exit(1)

    peer_id = int(sys.argv[1])
    PeerProcess(peer_id).start()
