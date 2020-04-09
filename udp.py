from urllib.parse import urlparse
import socket
from struct import pack, unpack
import random

def _decode_port(binary_port):
    return unpack('>H',binary_port)[0]

def get_conn_request():
    transaction_id = random.randint(1,1000) 
    message = pack('>QII',
                        0x41727101980,
                        0,
                        transaction_id)

    return transaction_id,message
    
    
def decode_connection_response(response):
    decoded_response = unpack('>IIQ',response)
    return decoded_response


def get_announce_request(info_hash,connection_id,peer_id):
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

info_hash = b'P\xe3\xf4\x129\xe5t\xcaAj\x0f0\xd1v]p\xbe\x0c2\x98'
announce = 'udp://tracker.openbittorrent.com:80/announce'
peer_id = '-PC0001-' + ''.join([str(random.randint(0,9)) for _ in range(12)])
peer_id = peer_id.encode()
"""
Parse the announce URL
"""

parsed_url = urlparse(announce)
hostname = parsed_url.hostname
port = parsed_url.port
ip = socket.gethostbyname(hostname)

conn = (ip, port)

print(conn)

s = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
s.settimeout(15)

transaction_id, connection_request = get_conn_request()
try:
    s.sendto(connection_request,conn)

    response = s.recv(2048)
except socket.timeout:
    print('Timemout')
    exit()

print(response)

if len(response) < 16:
    print('Response is less than 16 bytes')
    exit()

decoded_response = decode_connection_response(response)

if decoded_response[0] == 0 and decoded_response[1] == transaction_id:
    connection_id = decoded_response[2]
else:
    print('Wrong response')


announce_request = get_announce_request(info_hash,connection_id,peer_id)
print(announce_request,len(announce_request))


s.sendto(announce_request,conn)
response = s.recv(2048)

if len(response) < 20:
    print('Response is less than 20 bytes')
    exit()



peers = response[20:]


peer_list = [peers[i:i + 6] for i in range(0,len(peers),6)]
num_peers = len(peer_list)
peer_list = [(socket.inet_ntoa(p[0:4]),_decode_port(p[4:])) for p in peer_list]

print(peer_list,num_peers)

