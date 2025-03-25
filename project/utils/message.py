import logging


class InvalidMessageError(Exception):
    def __init__(self, message="Invalid message format"):
        super().__init__(message)
        self.message = message

    def __str__(self):
        return f"InvalidMessageError: {self.message}"


class Message:
    CHOKE = 0
    UNCHOKE = 1
    INTERESTED = 2
    NOT_INTERESTED = 3
    HAVE = 4
    BITFIELD = 5
    REQUEST = 6
    PIECE = 7

    @staticmethod
    def get_message_type_name(msg_type):
        message_type_map = {
            Message.CHOKE: "CHOKE",
            Message.UNCHOKE: "UNCHOKE",
            Message.INTERESTED: "INTERESTED",
            Message.NOT_INTERESTED: "NOT_INTERESTED",
            Message.HAVE: "HAVE",
            Message.BITFIELD: "BITFIELD",
            Message.REQUEST: "REQUEST",
            Message.PIECE: "PIECE",
        }
        return message_type_map.get(msg_type, "UNKNOWN")

    @staticmethod
    def create_message(msg_type, payload=b""):
        if not isinstance(payload, (bytes, bytearray)):
            raise TypeError("Payload must be bytes or bytearray.")
        try:
            length = len(payload) + 1
            message = length.to_bytes(4, "big") + msg_type.to_bytes(1, "big") + payload
            logging.debug(
                f"Created message: type={msg_type}, length={length}, payload_length={len(payload)}"
            )
            return message
        except Exception as e:
            logging.error(f"Error creating message: {e}")
            raise

    @staticmethod
    def parse_message(data):
        if len(data) < 5:
            raise InvalidMessageError("Message too short to parse.")
        try:
            length = int.from_bytes(data[:4], "big")
            msg_type = int.from_bytes(data[4:5], "big")
            payload = data[5:]
            if len(payload) != length - 1:
                raise InvalidMessageError(
                    f"Payload length mismatch: expected {length - 1}, got {len(payload)}"
                )
            logging.debug(
                f"Parsed message: type={msg_type}, length={length}, payload_length={len(payload)}"
            )
            return msg_type, payload
        except InvalidMessageError as ime:
            logging.warning(f"Invalid message encountered: {ime}")
            raise
        except Exception as e:
            logging.error(f"Error parsing message: {e}")
            raise


class Choke:
    @staticmethod
    def create():
        return Message.create_message(Message.CHOKE)


class Unchoke:
    @staticmethod
    def create():
        return Message.create_message(Message.UNCHOKE)


class Interested:
    @staticmethod
    def create():
        return Message.create_message(Message.INTERESTED)


class NotInterested:
    @staticmethod
    def create():
        return Message.create_message(Message.NOT_INTERESTED)


class Have:
    @staticmethod
    def create(piece_index):
        if not isinstance(piece_index, int) or piece_index < 0:
            raise ValueError("Piece index must be a non-negative integer.")
        try:
            payload = piece_index.to_bytes(4, "big")
            return Message.create_message(Message.HAVE, payload)
        except Exception as e:
            logging.error(f"Error creating HAVE message: {e}")
            raise


class Request:
    @staticmethod
    def create(piece_index):
        if not isinstance(piece_index, int) or piece_index < 0:
            raise ValueError("Piece index must be a non-negative integer.")
        try:
            payload = b"\x06" + piece_index.to_bytes(4, "big")
            return Message.create_message(Message.REQUEST, payload)
        except Exception as e:
            logging.error(f"Error creating REQUEST message: {e}")
            raise


class Piece:
    @staticmethod
    def create(piece_index, piece_data):
        if not isinstance(piece_index, int) or piece_index < 0:
            raise ValueError("Piece index must be a non-negative integer.")
        if not isinstance(piece_data, (bytes, bytearray)):
            raise TypeError("Piece data must be bytes or bytearray.")
        try:
            payload = piece_index.to_bytes(4, "big") + piece_data
            return Message.create_message(Message.PIECE, payload)
        except Exception as e:
            logging.error(f"Error creating PIECE message: {e}")
            raise


class Handshake:
    HEADER = b"P2PFILESHARINGPROJ0000000000"

    @staticmethod
    def create_handshake(peer_id):
        if not (0 <= peer_id < 2**32):
            raise ValueError("Peer ID must be a 32-bit unsigned integer.")
        try:
            return Handshake.HEADER + peer_id.to_bytes(4, "big")
        except Exception as e:
            logging.error(f"Error creating handshake: {e}")
            raise

    @staticmethod
    def parse_handshake(handshake):
        if len(handshake) != 32:
            raise ValueError("Invalid handshake length.")
        try:
            if handshake[:28] != Handshake.HEADER:
                raise ValueError("Invalid handshake header.")
            return int.from_bytes(handshake[28:], "big")
        except Exception as e:
            logging.error(f"Error parsing handshake: {e}")
            raise
