"""
Stage 1: Implement N peer connections and see if all of them are performing the handshake automatically. Also decode their bitfield messages and see if they work.
Stage 2: Requesting pieces and receiving them. Check if full pieces are being received, persist them to file. 
Stage 3: Check if asyncio is working with multiple peers and multiple pieces. 
Stage 4: Multi file torrent downloading
Stage 5: UDP Protocol - add protocol checking, timeout for tracker responses.
Stage 6: Add frequent tracker requests + torrent completion, add GUI for percentage completed.
Stage 7: Rarest piece first algorithm + Try to improve speeds
Stage 8: Uploading(seeding) - By sending listening, sending bitfields, unchokes, chokes, listening to requests, we already have an iterator
Stage 9: Resume and pause
"""

from own_bencoding import Encoder, Decoder
import requests
import socket
import asyncio
import uvloop
from hashlib import sha1
import random
from urllib.parse import urlencode,urlparse
from struct import unpack,pack
from peer import PeerConnection
from pprint import pprint
from time import time
from concurrent.futures import CancelledError
from classes import PieceManager
import datetime


def get_peers_from_announce_list(announce_list, peer_id, info_hash, total_length, tracker = ''):
    peer_list = set()
    if tracker != '':
        announce_list = [tracker]
    for tracker in announce_list:
        if tracker.startswith('udp'):
            peerID = peer_id.encode()
            parsed_url = urlparse(tracker)
            hostname = parsed_url.hostname
            port = parsed_url.port
            ip = socket.gethostbyname(hostname)

            conn = (ip, port)

            s = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
            s.settimeout(10)

            transaction_id, connection_request = get_conn_request_udp()
            try:
                s.sendto(connection_request,conn)
                response = s.recv(2048)
            

                if len(response) < 16:
                    print('Response is less than 16 bytes',tracker)
                    continue

                decoded_response = decode_connection_response(response)

                if decoded_response[0] == 0 and decoded_response[1] == transaction_id:
                    connection_id = decoded_response[2]
                else:
                    print('Wrong response',tracker)
                    continue


                announce_request = get_announce_request_udp(info_hash,connection_id,peerID)
                s.sendto(announce_request,conn)
                response = s.recv(2048)

                if len(response) < 20:
                    print('Response is less than 20 bytes',tracker)

                peers = response[20:]
                peers = [peers[i:i + 6] for i in range(0,len(peers),6)]
                for peer in peers:
                    peer_list.add(peer)
                print(tracker, 'success')
                break
            except socket.timeout:
                print('Timeout',tracker)

        elif tracker.startswith('http'):
            try:
                params = {
                'info_hash': info_hash,
                'peer_id': peer_id,
                'port': 6889,
                'uploaded': 0,
                'downloaded': 0,
                'left': total_length,
                'compact': 1
                }

                url = tracker + '?' + urlencode(params)

                response = requests.get(url,timeout = 10)
                response = Decoder(response.content).decode()
                if b'failure reason' in response:
                    print('Tracker request failed!',tracker)
                else:
                    interval = response[b'interval']
                    complete = response[b'complete']
                    incomplete = response[b'incomplete']
                    peers = response[b'peers']
                    peers = [peers[i:i + 6] for i in range(0,len(peers),6)]
                    for peer in peers:
                        peer_list.add(peer)
                    print(tracker, 'success')
                    break
            except requests.exceptions.Timeout:
                print(tracker,' timed out')
                continue

    peer_list = list(peer_list)
    # return peer_list, tracker
    return peer_list 

def get_conn_request_udp():
    transaction_id = random.randint(1,1000) 
    message = pack('>QII',
                        0x41727101980,
                        0,
                        transaction_id)

    return transaction_id,message
    
    
def decode_connection_response(response):
    decoded_response = unpack('>IIQ',response)
    return decoded_response


def get_announce_request_udp(info_hash,connection_id,peer_id):
    connection_id = pack('>Q',connection_id)
    action = pack('>I', 1)
    trans_id = pack('>I', random.randint(0, 100000))

    downloaded = pack('>Q', 0)
    left = pack('>Q', 0)
    uploaded = pack('>Q', 0)

    event = pack('>I', 0)
    ip = pack('>I', 0)
    key = pack('>I', 0)
    num_want = pack('>i', -1)
    port = pack('>h', 8000)

    msg = (connection_id + action + trans_id + info_hash + peer_id + downloaded + 
            left + uploaded + event + ip + key + num_want + port)

    return msg


def _decode_port(binary_port):
    return unpack('>H',binary_port)[0]

async def _create_piece_manager(pieces_hash,piece_length,total_length,name, files):
    piece_manager = PieceManager(pieces_hash,piece_length,total_length,name, files)
    await piece_manager.initialise_file_pointers()
    return piece_manager


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
    files = []
    total_length = 0
    name = info[b'name']
    if b'files' in info.keys():
        #multi-file torrent
        for i,file in enumerate(info[b'files']):
            len_file = file[b'length']
            path_file = file[b'path']
            files.append({'index':i, 'path': (name + b'/') + (b'/'.join(path_file)), 'length': len_file, 'offset': 0})
            total_length += len_file
    else:
        #single-file torrent
        total_length = info[b'length'] 
        files.append({'index': 0, 'path': name, 'length': total_length, 'offset': 0})

    """
    Pieces
    """
    piece_length = info[b'piece length']
    pieces_hash_concatenated = info[b'pieces']

    """
    Split the concatenated pieces_hash into a list of pieces_hash
    """
    pieces_hash = []

    offset = 0
    while(offset < len(pieces_hash_concatenated)):
        pieces_hash.append(pieces_hash_concatenated[offset:offset + 20])
        offset += 20


    """
    Create a single instance of piece_manager from the above data
    """
    piece_manager = await _create_piece_manager(pieces_hash,piece_length,total_length,name,files)
    """
    Create peer ID
    """
    peer_id = '-PC0001-' + ''.join([str(random.randint(0,9)) for _ in range(12)])


    """
    Populate announce list
    """

    announce_list = []
    if b'announce-list' in torrent_data.keys():
        for announce in torrent_data[b'announce-list']:
            announce_list.append((b''.join(announce)).decode('UTF-8'))
    else:
        announce_list.append(torrent_data[b'announce'].decode('UTF-8'))

    """
    Make requests and response from either the HTTP tracker or the UDP tracker
    """
    
    peer_list = get_peers_from_announce_list(announce_list,peer_id,info_hash, total_length)
    previous = time()
    num_peers = len(peer_list)
    peer_list = [(socket.inet_ntoa(p[0:4]),_decode_port(p[4:])) for p in peer_list]

    """
    We have the list of peers.
    Now we have to create num_peers PeerConnection instances, which will automatically asynchronouly perform handshake and print the bitfield
    """

    peer_queue = asyncio.Queue()
    for peer in peer_list:
        peer_queue.put_nowait(peer)


    MAX_PEER_CONNECTIONS = len(peer_list)

    print('No. of peers: ',MAX_PEER_CONNECTIONS)


    peer_connections = [PeerConnection(peer_queue,info_hash,piece_manager,peer_id) for peer in peer_list[:MAX_PEER_CONNECTIONS]]

    while(True):
        if piece_manager.complete:
            print('Torrent completed')
            break
        else:
            # if(time() - previous > 20):
            #     previous = time()
            #     p_list, tracker = get_peers_from_announce_list(announce_list,peer_id,info_hash, total_length, tracker)
            #     p_list = [(socket.inet_ntoa(p[0:4]),_decode_port(p[4:])) for p in p_list]
                
            #     peer_queue = asyncio.Queue()
            #     for p in p_list:
            #         peer_queue.put_nowait(p)


            #     for peer_connection in peer_connections:
            #         if not peer_connection.alive:
            #             peer_connection.__init__(peer_queue,info_hash,piece_manager,peer_id)
            await asyncio.sleep(2)
        print( piece_manager.percentage_complete_pieces, '%', ', ', piece_manager.get_download_speed()/1000,'kilobytes per second',end = '\r')
        

    return None

    """
    End of main function
    """






start_time = time()

try:
    uvloop.install()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
except KeyboardInterrupt as e:
    print('Keyboard interrupt')
    pass
except CancelledError:
    print('Event loop was cancelled')

print('The torrent ran for ',str(datetime.timedelta(seconds= time() - start_time)) ,'seconds')
