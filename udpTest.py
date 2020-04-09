from struct import pack,unpack
import socket
from urllib.parse import urlparse
import random
import errno

class UdpTrackerConnection:
    """
        connect = <connection_id><action><transaction_id>
            - connection_id = 64-bit integer
            - action = 32-bit integer
            - transaction_id = 32-bit integer
        Total length = 64 + 32 + 32 = 128 bytes
    """

    def __init__(self):
        self.conn_id = pack('>Q', 0x41727101980)
        self.action = pack('>I', 0)
        self.trans_id = pack('>I', random.randint(0, 100000))

    def to_bytes(self):
        return self.conn_id + self.action + self.trans_id

    def from_bytes(self, payload):
        self.action, = unpack('>I', payload[:4])
        self.trans_id, = unpack('>I', payload[4:8])
        self.conn_id, = unpack('>Q', payload[8:])



def send_message(conn, sock, tracker_message):
    message = tracker_message.to_bytes()
    trans_id = tracker_message.trans_id
    action = tracker_message.action
    size = len(message)

    sock.sendto(message, conn)

    try:
        response = _read_from_socket(sock)
    except socket.timeout as e:
        print("Timeout : %s" % e)
        return
    except Exception as e:
        print("Unexpected error when sending message : %s" % e.__str__())
        return

    if len(response) < size:
        print("Did not get full message.")

    if action != response[0:4] or trans_id != response[4:8]:
        print("Transaction or Action ID did not match")

    return response



def _read_from_socket(sock):
    data = b''

    while True:
        try:
            buff = sock.recv(4096)
            if len(buff) <= 0:
                break

            data += buff
        except socket.error as e:
            err = e.args[0]
            if err != errno.EAGAIN or err != errno.EWOULDBLOCK:
                print("Wrong errno {}".format(err))
            break
        except Exception:
            print("Recv failed")
            break

    return data

announce = 'udp://tracker.openbittorrent.com:80/announce'
parsed = urlparse(announce)

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
sock.settimeout(4)
ip, port = socket.gethostbyname(parsed.hostname), parsed.port

tracker_connection_input = UdpTrackerConnection()
response = send_message((ip, port), sock, tracker_connection_input)