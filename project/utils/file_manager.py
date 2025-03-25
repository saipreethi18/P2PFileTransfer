import os
from utils.log_manager import LogManager

class FileManager:
    @staticmethod
    def parse_common_config():
        config = {}
        try:
            with open("Common.cfg", "r") as file:
                for line in file:
                    key, value = line.strip().split(maxsplit=1)
                    config[key.lower()] = value
        except FileNotFoundError:
            raise FileNotFoundError("Common.cfg not found.")
        except Exception as e:
            raise Exception(f"Error parsing Common.cfg: {e}")
        return config

    @staticmethod
    def parse_peer_info():
        peers = {}
        try:
            with open("PeerInfo.cfg", "r") as file:
                for line in file:
                    parts = line.strip().split()
                    peer_id = int(parts[0])
                    peers[peer_id] = {
                        "hostname": parts[1],
                        "port": int(parts[2]),
                        "has_file": bool(int(parts[3]))
                    }
        except FileNotFoundError:
            raise FileNotFoundError("PeerInfo.cfg not found.")
        except Exception as e:
            raise Exception(f"Error parsing PeerInfo.cfg: {e}")
        return peers

    def __init__(self, peer_id, piece_size, file_name, total_pieces):
        self.peer_id = peer_id
        self.piece_size = piece_size
        self.file_name = file_name
        self.total_pieces = total_pieces
        self.pieces = {}
        self.peer_dir = f"peer_{peer_id}"
        self.file_path = os.path.join(self.peer_dir, file_name)
        self._initialize_directory()
        LogManager.log(self.peer_id, "FileManager initialized.")

    def _initialize_directory(self):
        try:
            if not os.path.exists(self.peer_dir):
                os.makedirs(self.peer_dir, exist_ok=True)
                LogManager.log(self.peer_id, f"Directory created at {self.peer_dir}.")
            if not os.path.exists(self.file_path):
                with open(self.file_path, "wb") as file:
                    file.truncate(self.piece_size * self.total_pieces)
                LogManager.log(self.peer_id, f"File '{self.file_name}' created at {self.file_path}.")
        except Exception as e:
            raise Exception(f"Error initializing directory or file for Peer {self.peer_id}: {e}")

    def save_piece(self, piece_index, piece_data):
        try:
            if not (0 <= piece_index < self.total_pieces):
                raise ValueError(f"Invalid piece index {piece_index}.")
            self.pieces[piece_index] = piece_data
            with open(self.file_path, "r+b") as file:
                file.seek(piece_index * self.piece_size)
                file.write(piece_data)
            LogManager.log(self.peer_id, f"Piece {piece_index} saved. Size: {len(piece_data)} bytes.")
        except Exception as e:
            raise Exception(f"Error saving piece {piece_index}: {e}")

    def get_piece(self, piece_index):
        try:
            with open(self.file_path, "rb") as file:
                file.seek(piece_index * self.piece_size)
                piece_data = file.read(self.piece_size)
                if piece_data:
                    LogManager.log(self.peer_id, f"Piece {piece_index} retrieved.")
                    return piece_data
            LogManager.log(self.peer_id, f"Piece {piece_index} not found.")
            return None
        except FileNotFoundError:
            LogManager.log(self.peer_id, f"File '{self.file_path}' not found.")
            return None
        except Exception as e:
            LogManager.log(self.peer_id, f"Error retrieving piece {piece_index}: {e}")
            return None

    def reconstruct_file(self):
        try:
            if sorted(self.pieces.keys()) != list(range(self.total_pieces)):
                raise Exception("Missing or invalid pieces.")
            file_data = b"".join(self.pieces[i] for i in range(self.total_pieces))
            LogManager.log(self.peer_id, "File reconstructed successfully.")
            return file_data
        except Exception as e:
            raise Exception(f"Error reconstructing file: {e}")

    def initialize_pieces(self, has_complete_file):
        try:
            if has_complete_file:
                file_data = b"X" * (self.piece_size * self.total_pieces)
                for index in range(self.total_pieces):
                    start = index * self.piece_size
                    end = start + self.piece_size
                    piece_data = file_data[start:end]
                    self.save_piece(index, piece_data)
                LogManager.log(self.peer_id, "All pieces initialized.")
            else:
                self.pieces = {}
                LogManager.log(self.peer_id, "Initialized with empty pieces.")
        except Exception as e:
            raise Exception(f"Error initializing pieces: {e}")
