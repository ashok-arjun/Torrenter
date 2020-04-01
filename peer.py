import asyncio
from protocol import *


class ProtocolError(BaseException):
    pass

class PeerConnection:

    def __init__(self, common_peer_queue, remote_peer_id, info_hash, my_peer_id):
        self.common_peer_queue = asyncio.Queue
        self.remote_peer_id = remote_peer_id
        self.info_hash = info_hash
        self.my_peer_id = my_peer_id
        self.states = []
        self.connection = asyncio.create_task(self._start_connection())

    async def _start_connection(self):
        ip, port = await self.common_peer_queue.get()

        #try opening a socket asynchronouly

        
        try:
            reader, writer = asyncio.open_connection(ip, port)
        except ConnectionRefusedError:
            return None

        stream = PeerStreamIterator(self.remote_peer_id,reader,writer)
        
        buffer = await self._handshake()
        
        self.states.append('choked')

        await self._send_interested()

        self.states.append('interested')

        # for message in PeerStreamIterator(self.remote_peer_id,reader,buffer):

            #match the class of the message, and perform the required operation





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

        self.remote_peer_id = response_handshake.remote_peer_id

        return buffer[68:]


class PeerStreamIterator:

    def __init__(self, peer_id, reader, buffer):
        self.peer_id = peer_id
        self.reader = reader
        self.buffer = buffer | b''


    async def __aiter__(self):
        return self

    async def __anext__(self):
        #keep reading until 4 bytes, then particular length and the buffer
        #parse the message_id ONLY, based on that, return the class to the PeerConnection


        #this should be an infinite loop

        while(True):
            if message_class = self._parse():
                return message_class
            else:
                buffer += await self.reader.read(10 * 1024)



    def _parse(self):

        def _get_data_len():
            return int(unpack('>I',buffer[0:4])[0])

        def _get_message_id():
            return int(unpack('>B',buffer[4:])[0])

    
        def _consume():
            #adjust buffer

        def _data():
            #return payload part (the length specified)


        if(len(buffer) >= 4):
            data_length = _get_data_len()
            if(len(buffer) - 4 >= data_length):
                message_id = _get_message_id()

                if message_id == PeerMessage.Choke:
                    _consume()
                    return 

            else:
                return None       
        else:
            return None