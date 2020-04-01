class PeerMessage:
    Choke = 0
    Unchoke = 1
    Interested = 2
    NotInterested = 3
    Have = 4
    Bitfield = 5
    Request = 6
    Piece = 7
    Cancel = 8
    Port = 9

class Choke(PeerMessage):
    def _encode():
        return None

    @classmethod
    def _decode():
        return None

class Unchoke(PeerMessage):
    def _encode():
        return None

    @classmethod
    def _decode():
        return None


class Handshake(PeerMessage):

    def __init__(self, info_hash, peer_id):
        if isinstance(peer_id, str):
            peer_id = peer_id.encode('UTF-8')

        if isinstance(info_hash, str):
            info_hash = info_hash.encode('UTF-8')

        self.info_hash = info_hash
        self.peer_id = peer_id

    def _encode(self,info_hash, peer_id):

        return pack(
            '>B19s8s20s20s',
            19,
            b'BitTorrent protocol',
            b'\x00' * 8,
            info_hash,
            peer_id
            )

    @classmethod
    def _decode(cls, data : bytes):
        response = unpack('>B19s8s20s20s',data)
        return cls(info_hash = response[3], peer_id = response[4])
