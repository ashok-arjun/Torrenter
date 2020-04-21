from struct import  pack,unpack
from bitarray import bitarray

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
    def encode():
        pass

    @classmethod
    def decode():
        pass








class Unchoke(PeerMessage):
    def _encode():
        pass

    @classmethod
    def _decode():
        pass










class Handshake(PeerMessage):

    def __init__(self, info_hash, peer_id):
        if isinstance(peer_id, str):
            peer_id = peer_id.encode('UTF-8')

        if isinstance(info_hash, str):
            info_hash = info_hash.encode('UTF-8')

        self.info_hash = info_hash
        self.peer_id = peer_id

    def encode(self):

        return pack(
            '>B19s8s20s20s',
            19,
            b'BitTorrent protocol',
            b'\x00' * 8,
            self.info_hash,
            self.peer_id
            )

    @classmethod
    def decode(cls, data : bytes):
        response = unpack('>B19s8s20s20s',data)
        return cls(info_hash = response[3], peer_id = response[4])










class Interested(PeerMessage):
    
    def encode(self):
        return pack('>IB',1,2)

    @classmethod
    def decode(cls,data):
        pass
        #left for later










class BitField(PeerMessage):

    def __init__(self, data):
        self.bitfield = bitarray(data)

    def encode(self):
        pass

    @classmethod
    def decode(cls,full_message):
        len_field = int(unpack('>I',full_message[0:4])[0])
        a = bitarray()
        a.frombytes(unpack('>' + str(len_field - 1) + 's',full_message[5:])[0])
        return cls(a)



class Request(PeerMessage):

    def __init__(self, pieceIndex, blockOffset, blockLength):
        self.pieceIndex = int(pieceIndex)
        self.blockOffset = int(blockOffset)
        self.blockLength = int(blockLength)

    def encode(self):
        return pack('>IBIII',
                    13,
                    6,
                    self.pieceIndex,
                    self.blockOffset,
                    self.blockLength)

    @classmethod
    def decode(cls,data):
        pass




class Piece(PeerMessage):
    def __init__(self, piece_index, block_offset, block_data):
        self.piece_index = int(piece_index)
        self.block_offset = int(block_offset)
        self.block_data = block_data

    def encode(self):
        pass

    @classmethod
    def decode(cls, message):
        response_length = int(unpack('>I',message[0:4])[0])
        block_length = int(response_length - 9)
        response_payload = unpack('>II' + str(block_length) + 's',message[5:])
        return cls(response_payload[0],response_payload[1],response_payload[2])



class Have(PeerMessage):
    
    def __init__(self, piece_index):
        self.piece_index = int(piece_index)
    
    @classmethod
    def decode(cls, message):
        return cls(unpack('>IBI',message)[2])        