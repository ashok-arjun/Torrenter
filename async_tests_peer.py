"""
Stage 1: Implement N peer connections and see if all of them are performing the handshake automatically. Also decode their bitfield messages and see if they work.
Stage 2: Handshake limit - to reduce the traffic
"""

import asyncio
from struct import  pack,unpack
from own_bencoding import Encoder, Decoder
from hashlib import sha1
import random
from bitarray import bitarray


async def _interested(writer):
    writer.write(pack('>IB',1,2))
    await writer.drain()


def encode_handshake(info_hash,peer_id):
    if isinstance(peer_id, str):
        peer_id = peer_id.encode('UTF-8')

    if isinstance(info_hash, str):
        info_hash = info_hash.encode('UTF-8')
    return pack(
        '>B19s8s20s20s',
        19,
        b'BitTorrent protocol',
        b'\x00' * 8,
        info_hash,
        peer_id
        )

def decode_handshake(data : bytes):
    response = unpack('>B19s8s20s20s',data)
    return response[3]



async def _handshake(reader, writer,info_hash,peer_id):
    writer.write(encode_handshake(info_hash,peer_id))
    await writer.drain()
    buffer = b''
    while len(buffer) < 68:
        buffer += await reader.read(10 * 1024)
        
    response_handshake_info_hash = decode_handshake(buffer[:68])

    if(response_handshake_info_hash == info_hash):
        print('Handshakes infohash match!')

    return buffer[68:]






def _decode_bitfield(full_message):
    len_field = int(unpack('>I',full_message[0:4])[0])
    a = bitarray()
    a.frombytes(unpack('>' + str(len_field - 1) + 's',full_message[5:])[0])
    return a







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

            if message_id == 5:
                print('Bitfield message is received')

                complete_message = _get_full_message()
                _consume()
                return _decode_bitfield(complete_message)
            
            elif message_id == 1:
                print('Unchoke')
                return 'Unchoke'
            
            else: 
                print('Unknown message ID, cannot be decoded', message_id)
                return None

        else:
            return None       
    else:
        return None



async def iterate(reader, buffer):
    while(True):
        try:
            data = await reader.read(10 * 1024)
            if data:
                buffer[0] = buffer[0] + data
                decoded = _parse(buffer)
                if decoded:
                    yield decoded
            else:
                print('Nothing received from the socket')
                if buffer[0]:
                    decoded = _parse(buffer)
                    if decoded:
                        yield decoded 

        except ConnectionResetError:
            print('Connection terminated by peer')



async def main():

    with open('ubuntu.torrent','rb') as torrent_file:
        torrent = torrent_file.read()
        torrent_data = Decoder(torrent).decode()
        info = torrent_data[b'info']
        bencoded_info = Encoder(info).encode()
        info_hash = sha1(bencoded_info).digest()

    peer_id = '-PC0001-' + ''.join([str(random.randint(0,9)) for _ in range(12)])

    ip = '184.55.137.108'
    port = '50061'


    reader, writer = await asyncio.open_connection(ip,port)

    print('Opened socket!')

    buffer = [await _handshake(reader, writer, info_hash, peer_id)]

    print('Successfully handshaked, this is the buffer', buffer[0])

    await _interested(writer)

    async for message in iterate(reader, buffer):
        pass
        # print(message)









loop = asyncio.get_event_loop()
loop.run_until_complete(main())
loop.close()


