import asyncio
from protocol import *


class ProtocolError(BaseException):
    pass









class PeerConnection:

    def __init__(self, common_peer_queue, info_hash, my_peer_id):
        self.common_peer_queue = common_peer_queue
        self.remote_peer_id = None
        self.info_hash = info_hash
        self.my_peer_id = my_peer_id
        self.states = []
        self.connection = asyncio.ensure_future(self._start_connection())

    async def _start_connection(self):
        ip, port = await self.common_peer_queue.get()

        #try opening a socket asynchronouly

        
        try:
            reader, writer = asyncio.open_connection(ip, port)
        except ConnectionRefusedError:
            return None
        
        buffer = await self._handshake()
        
        self.states.append('choked')

        # await self._send_interested()

        # self.states.append('interested')

        async for message in PeerStreamIterator(self.reader,buffer):
            if type(message) is BitField:
                peer_bitfield = message
                print(ip, port, peer_bitfield, '\n')
                break
        return None

    async def _handshake(self):
        self.writer.write(Handshake(self.info_hash, self.my_peer_id).encode())
        await self.writer.drain()
        buffer = b''
        while len(buffer) < 68:
            buffer += await self.reader.read(10 * 1024)
            
        response_handshake = Handshake.decode(buffer[:68])

        if response_handshake == None:
            raise ProtocolError('Handshake failed!')
        if response_handshake.info_hash != self.info_hash:
            raise ProtocolError('Info hash different in handshake!')

        self.remote_peer_id = response_handshake.peer_id

        return buffer[68:]

    async def _send_interested(self):
        self.writer.write(Interested().encode())
        await self.writer.drain()
















class PeerStreamIterator:

    def __init__(self, reader, buffer):
        self.reader = reader
        self.buffer = buffer | b''


    async def __aiter__(self):
        return self

    async def __anext__(self):
        #keep reading until 4 bytes, then particular length and the buffer
        #parse the message_id ONLY, based on that, return the class to the PeerConnection


        #this should be an infinite loop - as it is an iterator

        while(True):
            message_class = self._parse()
            if message_class != None:
                return message_class
            else:
                buffer += await self.reader.read(10 * 1024)



    def _parse(self):

        def _get_data_len():
            return int(unpack('>I',buffer[0:4])[0])

        def _get_message_id():
            return int(unpack('>B',buffer[4:5])[0])

    
        def _consume():
            self.buffer = self.buffer[4 + data_length:]

        def _get_full_message():
            return self.buffer[:4 + data_length]


        if(len(buffer) >= 4):
            data_length = _get_data_len()

            #keepalive message is of zero length - should be ignored

            if data_length == 0:
                _consume()
                return None

            if(len(buffer) - 4 >= data_length):
                message_id = _get_message_id()

                if message_id == PeerMessage.Choke:
                    _consume()
                    return Choke()
                elif message_id == PeerMessage.Unchoke:
                    _consume()
                    return Unchoke()
                elif message_id == PeerMessage.Interested:
                    _consume()
                    return Interested()
                elif message_id == PeerMessage.NotInterested:
                    _consume()
                    return NotInterested()
                elif message_id == PeerMessage.Have:
                    complete_message = _get_full_message()
                    _consume()
                    return Have.decode(complete_message)
                elif message_id == PeerMessage.Bitfield:
                    complete_message = _get_full_message()
                    _consume()
                    return Bitfield.decode(complete_message)
                elif message_id == PeerMessage.Request:
                    complete_message = _get_full_message()
                    _consume()
                    return Request.decode(complete_message)
                elif message_id == PeerMessage.Piece:
                    complete_message = _get_full_message()
                    _consume()
                    return Piece.decode(complete_message)
                elif message_id == PeerMessage.Cancel:
                    complete_message = _get_full_message()
                    _consume()
                    return Cancel.decode(complete_message)
                else 
                    raise ProtocolError('Unknown message ID, cannot be decoded')

            else:
                return None       
        else:
            return None