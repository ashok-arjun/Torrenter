import asyncio
from protocol import *
from struct import pack,unpack


class ProtocolError(BaseException):
    pass


class PeerConnection:

    def __init__(self, common_peer_queue, info_hash, piece_manager, my_peer_id):
        self.common_peer_queue = common_peer_queue
        self.remote_peer_id = None
        self.info_hash = info_hash
        self.my_peer_id = my_peer_id
        self.states = []
        self.reader = None
        self.writer = None
        self.piece_manager = piece_manager
        self.connection = asyncio.ensure_future(self._start_connection())


    async def _start_connection(self):
        ip, port = await self.common_peer_queue.get()

        
        try:
            self.reader, self.writer = await asyncio.open_connection(ip, port)
        except ConnectionRefusedError:
            return None
        
        buffer = [await self._handshake()]
        print('Handshake successful for ',ip,port)
        
        self.states.append('choked')

        await self._send_interested()

        self.states.append('interested')

        async for message in PeerStreamIterator.iterate(self.reader, buffer):
            if type(message) is BitField:
                peer_bitfield = message.bitfield
                print('Bitfield message received from',ip,port) 
            elif type(message) is Unchoke:
                if 'choked' in self.states:
                    self.states.remove('choked')
                print('Unchoke received from ',ip,port)
            elif type(message) is Choke:
                if 'choked' not in self.states:
                    self.states.append('choked')    
                print('Choke received from ',ip,port)
            # else
            #     if 'choked' not in self.states:
            #         if 'interested' in self.states:
            #             if 'pending_request' not in self.states:
            #                 self.states.append('pending_request')
            #                 #await self._request_piece()



    async def _request_piece(self):
        block = self.piece_manager.next_request(self.remote_peer_id)

        if block :
            pass
            #encode the request using the block's variables
            #drain writer



                
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

    @staticmethod
    def _parse(buffer):

        def _get_data_len():
            return int(unpack('>I',buffer[0][0:4])[0])

        def _get_message_id():
            return int(unpack('>B',buffer[0][4:5])[0])


        def _consume():
            nonlocal buffer
            buffer[0] = buffer[0][4 + data_length:]

        def _get_full_message():
            return buffer[0][:4 + data_length]


        if(len(buffer[0]) >= 4):
            data_length = _get_data_len()

            #keepalive message is of zero length - should be ignored

            if data_length == 0:
                _consume()
                return None

            if(len(buffer[0]) - 4 >= data_length):
                message_id = _get_message_id()

                if message_id == PeerMessage.Bitfield:
                    complete_message = _get_full_message()
                    _consume()
                    return BitField.decode(complete_message)
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
                else: 
                    raise ProtocolError('Unknown message ID, cannot be decoded')

            else:
                return None       
        else:
            return None


    @staticmethod
    async def iterate(reader, buffer):
        while(True):
            try:
                data = await reader.read(1024)
                if data:
                    buffer[0] = buffer[0] + data
                    decoded = PeerStreamIterator._parse(buffer)
                    if decoded:
                        yield decoded
                else:
                    print('Nothing received from the socket')
                    if buffer[0]:
                        decoded = PeerStreamIterator._parse(buffer)
                        if decoded:
                            yield decoded 

            except ConnectionResetError:
                print('Connection terminated by peer')