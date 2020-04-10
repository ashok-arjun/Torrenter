import asyncio
from protocol import *
from struct import pack,unpack
from concurrent.futures import CancelledError

class ProtocolError(BaseException):
    pass


class PeerConnection:

    total_unchoked = 0

    def __init__(self, common_peer_queue, info_hash, piece_manager, my_peer_id):
        self.common_peer_queue = common_peer_queue
        self.remote_peer_id = None
        self.info_hash = info_hash
        self.my_peer_id = my_peer_id #only for the purpose of handshaking
        self.states = []
        self.reader = None
        self.writer = None
        self.piece_manager = piece_manager
        self.pending_request = None
        self.connection = asyncio.ensure_future(self._start_connection())

    async def _get_socket(self,ip,port):
        fut = asyncio.open_connection(ip, port) 
        self.reader, self.writer = await asyncio.wait_for(fut,timeout = 10)
            
    async def _start_connection(self):
        while('stopped' not in self.states):
            # print('Waiting for a peer')
            el = await self.common_peer_queue.get()
            # print('From the queue, this PeerConnection got',el)
            ip, port = el
            self.ip, self.port = ip, port
            try:
                await self._get_socket(ip,port)
                buffer = [await self._handshake()]
                if buffer[0] == -1:
                    self.cancel()
                    continue
                # print('Handshake successful for ',ip,port)
                
                self.states.append('choked')

                await self._send_interested()

                self.states.append('interested')

                async for message in PeerStreamIterator.iterate(self.reader, buffer):
                    if type(message) is BitField:
                        self.piece_manager.update_peer(self.remote_peer_id, bitfield = message.bitfield)
                        # print('Bitfield message received from',self.ip,self.port) 
                    
                    elif type(message) is Unchoke:
                        if 'choked' in self.states:
                            self.states.remove('choked')
                        # print('Unchoke received from ',self.ip,self.port)
                        PeerConnection.total_unchoked += 1

                    elif type(message) is Choke:
                        if 'choked' not in self.states:
                            self.states.append('choked')    
                        # print('Choke received from ',self.ip,self.port)
                        # print(self.states)

                    elif type(message) is Piece:
                        await self.piece_manager._receive_block(message, self.pending_request)
                        # print('Passed the received block to piece manager',self.ip,self.port)
                        self.pending_request = None 

                    elif type(message) is Have:
                        self.piece_manager.update_peer(self.remote_peer_id, have = message.piece_index)
                        # print('Have message has been received',self.ip,self.port)


                    if 'choked' not in self.states:
                        if 'interested' in self.states:
                            if self.pending_request == None:
                                await self._request_piece()


            except asyncio.TimeoutError:
                pass
                # print('Timeout',ip,port)
            except (ConnectionRefusedError,ConnectionError):
                pass
                # print('Connection refused by',ip,port)
            except ProtocolError as e:
                pass
                # print('Protocol error')
            except (ConnectionResetError, CancelledError):
                pass
                # print('Connection reset!',ip,port)
            except Exception as e:
                pass
                # print('Unknown error!')
            self.cancel()


    async def _request_piece(self):
        block = self.piece_manager.next_request(self.remote_peer_id)
        # print('Requesting block',block.piece_index,block.offset,block.block_length,' from peer', self.ip,self.port)
        if block :
            message = Request(block.piece_index,block.offset,block.block_length)
            self.pending_request = message
            try:
                self.writer.write(message.encode())
                await self.writer.drain()
            except:
                print('Problem in request piece')
                self.cancel()
        # print('Finished requesting ',block.piece_index,block.offset,block.block_length,' from peer', self.ip,self.port)
                
    async def _handshake(self):
        self.writer.write(Handshake(self.info_hash, self.my_peer_id).encode())
        await self.writer.drain()
        buffer = b''
        tries = 0
        while len(buffer) < 68 and tries < 10:
            tries += 1
            buffer += await self.reader.read(10 * 1024)
        if len(buffer) < 68:
            return -1
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

    def cancel(self):

        if self.remote_peer_id != None:
            self.piece_manager._peer_connection_closed(self.remote_peer_id,self.pending_request)
        self.states = []
        # print('Connection cancelled')

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
                reading_operation = reader.read(1024)
                data = await asyncio.wait_for(reading_operation,2)
                if data:
                    buffer[0] = buffer[0] + data
                    decoded = PeerStreamIterator._parse(buffer)
                    if decoded:
                        yield decoded
                else:
                    if buffer[0]:
                        decoded = PeerStreamIterator._parse(buffer)
                        if decoded:
                            yield decoded 

            except asyncio.TimeoutError:
                # print(' 1 Exception in iterate line 225')
                raise StopAsyncIteration()          
            except (ConnectionResetError,ConnectionError):
                # print('Connection terminated by peer - PSI 1')
                raise StopAsyncIteration()
            except CancelledError:
                # print('Cancelled error - PSI 2')
                raise StopAsyncIteration()
            except StopAsyncIteration as e:
                # print('PSI 3')
                raise e
            except Exception as e:
                print(e)
                raise StopAsyncIteration()

        raise StopAsyncIteration()