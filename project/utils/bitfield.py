class BitField:
    @staticmethod
    def initialize(has_complete_file, total_pieces):
        if has_complete_file:
            return [1] * total_pieces
        return [0] * total_pieces

    @staticmethod
    def update(bitfield, piece_index):
        bitfield[piece_index] = 1
