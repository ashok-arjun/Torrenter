"""
Initial implementation:

Reference websites:
Unofficial specification: https://wiki.theory.org/index.php/BitTorrentSpecification#peer_id
How-to: http://www.kristenwidman.com/blog/33/how-to-write-a-bittorrent-client-part-1/
        http://www.kristenwidman.com/blog/71/how-to-write-a-bittorrent-client-part-2/

Stages:

Stage 1: Single-threaded application which can 
        parse a torrent
        GET request a tracker SYNCHRONOUSLY
        read the response and store the PEERS
        handshake all the peers and get their bit fields - SYNCHRONOUSLY
        choose pieces from step 1 decoding and request pieces from PEERS - SYNCHRONOUSLY
        get all the pieces and write to the file - SYNCHRONOULY WRITING TO THE FILE - IMMEDIATELY AFTER PREVIOUS STEP


Stage 2: 
        Make the GET request ASYNC
        Make the peer handshakes ASYNC
        Make the piece_manager allocating pieces to peers and downloading them - ASYNC
        Make the writing to the file - ASYNC

"""