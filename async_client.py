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
from tracker import Tracker


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
        #done

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
    
    tracker = Tracker(announce_list,info_hash,peer_id,total_length)
    peer_list = None
    while(peer_list == None):
        print('Trying to obtain peers from trackers...')
        peer_list, interval = tracker.get_peers_from_announce_list(0,0)
    print('Got',len(peer_list),'peers')
    previous = time()

    total_peers_obtained = len(peer_list)

    """
    We have the list of peers.
    Now we have to create num_peers PeerConnection instances, which will automatically asynchronouly perform handshake and print the bitfield
    """

    peer_queue = asyncio.Queue()
    for peer in peer_list:
        peer_queue.put_nowait(peer)
    
    MAX_PEER_CONNECTIONS = len(peer_list)
    peer_connections = [PeerConnection(peer_queue,info_hash,piece_manager,peer_id) for peer in peer_list[:MAX_PEER_CONNECTIONS]]



    while(True):

    # Uncomment the following lines if you want atleast 5 unchoked peers at all times/ if you want trackers to get updated frequently

    #     if(time() - previous >= 20 and PeerConnection.total_unchoked < 5) or (time() - previous >= interval):
    #         peer_list = None
    #         while(peer_list == None):
    #             print('Reconnecting with tracker for peers')
    #             peer_list, interval = tracker._update_peer_list(piece_manager.downloaded_bytes,piece_manager.uploaded_bytes) 
    #         print('Got',len(peer_list),'peers')
    #         total_peers_obtained += len(peer_list)
    #         for peer in peer_list:
    #             peer_queue.put_nowait(peer)
            
    #         previous = time()
                        
        await asyncio.sleep(5)          
        print( piece_manager.percentage_complete_pieces, '%', ', ', piece_manager.get_download_speed()/1000,'kilobytes per second')

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
