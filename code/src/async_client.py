from own_bencoding import Encoder, Decoder #for decoding torrent file and tracker repsonse
import requests #for HTTP requests
import socket #for peer connections and UDP tracker
import asyncio #for asynchronous operations
import uvloop #faster operations for asyncio
from hashlib import sha1 #to compute hash of info dictionary
import random #for generating the peer IDs
from time import time #for calculating number of seconds the program ran
import datetime #to convert seconds to h:m:s
from concurrent.futures import CancelledError #an inbuilt exception
import argparse #for command line arguments
from os import path #to check if the torrent is valid(the path exists)
from pprint import pprint

#CUSTOM CLASSES
from peer import PeerConnection #TO CONNECT TO PEERS
from piece_manager import PieceManager #TO MANAGE THE TORRENT'S FILES
from tracker import Tracker #TO REQUEST TRACKER AND GET THE RESPONSE

async def _create_piece_manager(pieces_hash,piece_length,total_length,name, files):
    piece_manager = PieceManager(pieces_hash,piece_length,total_length,name, files)
    await piece_manager.initialise_file_pointers()
    return piece_manager


async def main(torrent_path):
    """
    Open torrent, bdecode the data
    """
    with open(torrent_path,'rb') as torrent_file:
        torrent = torrent_file.read()
        torrent_data = Decoder(torrent).decode()
        pprint(torrent_data)
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

    name = b'../output/' + name

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

    pprint(peer_list)

    """
    We have the list of peers.
    Now we have to create num_peers PeerConnection instances, which will automatically asynchronouly perform handshake and print the bitfield
    """

    peer_queue = asyncio.Queue()
    for peer in peer_list:
        peer_queue.put_nowait(peer)
    
    MAX_PEER_CONNECTIONS = len(peer_list)
    peer_connections = [PeerConnection(peer_queue,info_hash,piece_manager,peer_id) for peer in peer_list[:MAX_PEER_CONNECTIONS]]


    i = 0 #to check for minimum number of peers, we increment i every 2 seconds, and when we reach 40 seconds, we check(for optimality)
    while(True):

    # Uncomment the following lines if you want atleast 5 unchoked peers at all times/ if you want trackers to get updated frequently
        # if i == 20:      
        #     i = 0  
        #     current = time()

        #     if(current - previous >= 20 and PeerConnection.total_unchoked < 5) or (current - previous >= interval):
        #         peer_list = None
        #         while(peer_list == None):
        #             print('Reconnecting with tracker for more peers')
        #             peer_list, interval = tracker._update_peer_list(piece_manager.downloaded_bytes,piece_manager.uploaded_bytes) 
        #         print('Got',len(peer_list),'peers')
        #         for peer in peer_list:
        #             peer_queue.put_nowait(peer)
                
        #         previous = current
                        
        await asyncio.sleep(2)          
        print( round(piece_manager.percentage_complete_pieces,4), '%', ', ', round(piece_manager.get_download_speed()/1000,4),'kilobytes per second')
        i += 1
    return None

    """
    End of main function
    """









if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='To get the input torrent file')
    parser.add_argument('torrent', help= 'the torrent to be downloaded')

    args = parser.parse_args()

    torrent_path = args.torrent

    if not path.exists(torrent_path):
        print('The torrent path is invalid!')
        quit()

    start_time = time()

    try:
        uvloop.install()
        loop = asyncio.get_event_loop()
        loop.run_until_complete(main(torrent_path))
    except KeyboardInterrupt as e:
        print('Keyboard interrupt')
        pass
    except CancelledError:
        print('Event loop was cancelled')

    print('The torrent ran for ',str(datetime.timedelta(seconds= time() - start_time)) ,'seconds')
