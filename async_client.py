"""
Stage 1: Implement N peer connections and see if all of them are performing the handshake automatically. Also decode their bitfield messages and see if they work.
Stage 2: Handshake limit - to reduce the traffic
"""

from own_bencoding import Encoder, Decoder
import requests
import socket
import asyncio
from hashlib import sha1
import random
from urllib.parse import urlencode
from struct import unpack
from peer import PeerConnection
from pprint import pprint


def _decode_port(binary_port):
    return unpack('>H',binary_port)[0]


async def main():
    """
    Open torrent, bdecode the data
    """
    with open('ubuntu.torrent','rb') as torrent_file:
        torrent = torrent_file.read()
        torrent_data = Decoder(torrent).decode()
        info = torrent_data[b'info']
        bencoded_info = Encoder(info).encode()
        info_hash = sha1(bencoded_info).digest()


    """
    Get items from info dictionary
    """
    length = info[b'length']
    name = info[b'name']
    piece_length = info[b'piece length']
    pieces_hash = info[b'pieces']


    """
    Create peer ID
    """
    peer_id = '-PC0001-' + ''.join([str(random.randint(0,9)) for _ in range(12)])


    """
    Send GET request
    """
    params = {
    'info_hash': info_hash,
    'peer_id': peer_id,
    'port': 6889,
    'uploaded': 0,
    'downloaded': 0,
    'left': length,
    'compact': 1
    }

    tracker = torrent_data[b'announce'].decode('utf-8')
    url = tracker + '?' + urlencode(params)

    print('Sending a request to', url)


    """
    Receive and decode the response
    """

    response = requests.get(url)
    response = Decoder(response.content).decode()

    if b'failure reason' in response:
        print('Tracker request failed!')
    else:
        print('Tracker request success!')


    interval = response[b'interval']
    complete = response[b'complete']
    incomplete = response[b'incomplete']
    peers = response[b'peers']



    """
    Decode the peers
    """

    peer_list = [peers[i:i + 6] for i in range(0,len(peers),6)]
    num_peers = len(peer_list)
    peer_list = [(socket.inet_ntoa(p[0:4]),_decode_port(p[4:])) for p in peer_list]


    """
    We have the list of peers.
    Now we have to create num_peers PeerConnection instances, which will automatically asynchronouly perform handshake and print the bitfield
    """

    peer_queue = asyncio.Queue()
    for peer in peer_list:
        peer_queue.put_nowait(peer)

    peer_connections = [PeerConnection(peer_queue,info_hash,peer_id) for peer in peer_list[:5]]

    while(True):
        #now it stops executing this function, and starts executing the waiting tasks(the _start_connection() functions of all the peers)
        await asyncio.sleep(20)





    return None

    """
    End of main function
    """







loop = asyncio.get_event_loop()
loop.run_until_complete(main())
loop.close()