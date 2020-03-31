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

MAKE_REQUEST = True

import own_bencoding as bencoding
import pprint
from hashlib import sha1
import random
from urllib.parse import urlencode
import requests
import socket
from struct import pack,unpack



"""
Open the torrent file and decode the data, and compute the sha1 hash of the info dictionary, compute the peer_id
"""
def main():

	with open('ubuntu.torrent','rb') as torrent_file:
		torrent = torrent_file.read()
		torrent_data = bencoding.Decoder(torrent).decode()
		info = torrent_data[b'info']
		bencoded_info = bencoding.Encoder(info).encode()
		info_hash = sha1(bencoded_info).digest()


	length = info[b'length']
	name = info[b'name']
	piece_length = info[b'piece length']
	pieces_hash = info[b'pieces']
	peer_id = '-PC0001-' + ''.join([str(random.randint(0,9)) for _ in range(12)])

	"""
	Send a GET request to the tracker with the parameters
	"""

	if(MAKE_REQUEST):
		params = {
		'info_hash': info_hash,
		'peer_id': peer_id,
		'port': 6889,
		'uploaded': 0,
		'downloaded': 0,
		'left': length,
		'compact': 1}

		tracker = torrent_data[b'announce'].decode('utf-8')
		url = tracker + '?' + urlencode(params)

		print('Making a request to: ', url)

		response = requests.get(url)
		response = bencoding.Decoder(response.content).decode()



		"""

		WE HAVE GOT THE RESPONSE FROM THE TRACKER WITH THE PEERS AND OTHER INFORMATION

		"""




		if b'failure reason' in response:
			print('Tracker request failed!')
		else:
			print('Tracker request success!')

		
		interval = response[b'interval']
		complete = response[b'complete']
		incomplete = response[b'incomplete']
		peers = response[b'peers']






		peer_list = [peers[i:i + 6] for i in range(0,len(peers),6)]

		peer_list = [(socket.inet_ntoa(p[0:4]),_decode_port(p[4:])) for p in peer_list]


	"""

	We have retrieved the peers

	"""


	pstr = b'BitTorrent protocol'
	pstrlen = len(pstr)
	reserved = b'\x00' * 8

	peer_id = peer_id.encode('UTF-8')

	handshake = pack(
		'>B19s8s20s20s',
		pstrlen,
		pstr,
		reserved,
		info_hash,
		peer_id
		)


	# Now open a socket for this peer and send this handshake and get a reply


	s = socket.create_connection(peer_list[0],timeout=10)
	# s.setblocking(False)


	s.send(handshake)

	peer_response = s.recv(10 * 1024)



	if len(peer_response) >= 68:
		buffer = peer_response[68:]
		peer_response = peer_response[0:68]
		peer_response = unpack('>B19s8s20s20s',peer_response)
		if(peer_response[3] != info_hash):
			RuntimeError('Info hash not equal')
		print('Hash verified!')

		#decode buffer
		while(len(buffer) < 4):
			buffer += s.recv(10 * 1024)
		len_field = unpack('>I',buffer[0:4])[0]
		while(len(buffer) - 4 < len_field):
			buffer += s.recv(10 * 1024)

		message_id = int(unpack('>B',buffer[4:5])[0])

		if(message_id == 5):
			print('BITFIELD MESSAGE RECEIVED!')
			bitfield = unpack('>' + str(len_field - 1) + 's',buffer[5:])

	"""
	SEND INTERESTED MESSAGE AND GET RESPONSE
	"""


	#KEEP READING FROM BUFFER AND DECODE THE MESSAGES EVERY TIME WE GET 4 BYTES

	#receive 10 * 1024 bytes

	#while True loop -> check if length of the buffer is > 4, if so, unpack the first 4 bytes

	#now decode the first 4 bytes and see the data length PORTION

	#check if that the length has been received i.e. len(buffer) >= header_length

	#if so, decode the next byte - the message_id

	#depending on the message_id, 1. consume the message, 2. update the parameters

	"""
	Now send an interested message AND wait for an unchoke
	"""

	# connection_state = ['choked']

	#interested message
	#<len=0001><id=2>

	# interested_message = pack('>IB',1,2)

	# s.send(interested_message)

	# peer_response = s.recv(10 * 1024)

	# if(len(peer_response) >= 4):
	# 	len_field = peer_response[0:4]
	# 	len_field = unpack('>I',len_field)
	# 	print(len_field)











	return None



def _decode_port(binary_port):
	#returns the decimal equivalent of the binary_port which is 2 bytes long, encoded in ASCII or direct hexadecimal \xab (ab is hexadecimal)
	"""

	The port number is in big endian format

	"""
	
	return unpack('>H',binary_port)[0]


main()


