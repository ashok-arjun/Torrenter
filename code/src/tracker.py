from own_bencoding import Encoder, Decoder
import requests
import socket
import random
from urllib.parse import urlencode,urlparse
from struct import unpack,pack
import time


class Tracker:
    def __init__(self, announce_list, info_hash, peer_id, total_length):
        self.announce_list = announce_list
        self.info_hash = info_hash
        self.peer_id = peer_id.encode()
        self.last_used_tracker = None
        self.total_length = total_length


    def _get_UDP_socket(self, tracker):
        parsed_url = urlparse(tracker)
        hostname = parsed_url.hostname
        port = parsed_url.port
        ip = socket.gethostbyname(hostname)

        conn = (ip, port)

        s = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
        s.settimeout(5)

        return s,conn


    def _decode_port(self,binary_port):
        return unpack('>H',binary_port)[0]



    def get_conn_request_udp(self):
        transaction_id = random.randint(1,1000) 
        message = pack('>QII',
                            0x41727101980,
                            0,
                            transaction_id)

        return transaction_id,message

    def _connect_UDP(self,s,conn):
        transaction_id, connect_message = self.get_conn_request_udp()
        try:
            s.sendto(connect_message,conn)
            response = s.recv(2048)
        

            if len(response) < 16:
                return None

            decoded_response = unpack('>IIQ',response)

            if decoded_response[0] == 0 and decoded_response[1] == transaction_id:
                return decoded_response[2]
            else:
                return None


        except socket.timeout:
            # print('UDP Timeout')
            return None




    def _announce_UDP(self,s,conn,downloaded,uploaded):
        connection_id = pack('>Q',self.connection_id)
        action = pack('>I', 1)
        trans_id = pack('>I', random.randint(0, 100000))

        left = pack('>Q', self.total_length - downloaded)
        downloaded = pack('>Q', downloaded)
        uploaded = pack('>Q', uploaded)

        event = pack('>I', 0)
        ip = pack('>I', 0)
        key = pack('>I', 0)
        num_want = pack('>i', -1)
        port = pack('>h', 8000)

        msg = (connection_id + action + trans_id + self.info_hash + self.peer_id + downloaded + 
                left + uploaded + event + ip + key + num_want + port)

        # print(trans_id)
        
        try:
            s.sendto(msg,conn)
            response = s.recv(2048)
            if len(response) < 20 or unpack('>I',response[0:4])[0] != 1 or response[4:8] != trans_id:
                # print('Response is not right')
                return None, None
            
            interval = unpack('>I',response[8:12])[0]
            peers = response[20:]
            peers = [peers[i:i + 6] for i in range(0,len(peers),6)]
            peer_list = []
            for peer in peers:
                peer_list.append(peer)
            peer_list = [(socket.inet_ntoa(p[0:4]),self._decode_port(p[4:])) for p in peer_list]
            return peer_list, interval
        except socket.timeout:
            return None, None



    def _announce_HTTP(self, tracker, downloaded, uploaded):
        try:
            params = {
            'info_hash': self.info_hash,
            'peer_id': self.peer_id,
            'port': 6889,
            'uploaded': uploaded,
            'downloaded': downloaded,
            'left': self.total_length - downloaded,
            'compact': 1
            }

            url = tracker + '?' + urlencode(params)

            response = requests.get(url,timeout = 5)
            try:
                response = Decoder(response.content).decode()
            except RuntimeError:
                print('Wrong response from tracker')
                return None, None
            if b'failure reason' in response:
                # print('Tracker request failed!',tracker)
                return None, None
            else:
                interval = response[b'interval']
                peers = response[b'peers']
                peers = [peers[i:i + 6] for i in range(0,len(peers),6)]
                peer_list = []
                for peer in peers:
                    peer_list.append(peer)
                peer_list = [(socket.inet_ntoa(p[0:4]),self._decode_port(p[4:])) for p in peer_list]
                return peer_list, interval
        except requests.exceptions.Timeout:
            # print(tracker,' timed out')
            return None, None

    def get_peers_from_announce_list(self,downloaded, uploaded):
        for tracker in self.announce_list:
            if tracker.startswith('udp'):
                s,conn = self._get_UDP_socket(tracker)
                self.s = s
                self.conn = conn
                self.connection_id = self._connect_UDP(s,conn)
                if(self.connection_id == None):
                    continue
                
                peer_list, interval = self._announce_UDP(s,conn,downloaded,uploaded)
                if peer_list == None:
                    continue

                self.last_used_tracker = tracker

                return peer_list,interval

            elif tracker.startswith('http'):
                peer_list, interval = self._announce_HTTP(tracker, downloaded, uploaded)
                if peer_list == None:
                    continue

                self.last_used_tracker = tracker
                return peer_list, interval

        
        return None, None


    def _update_peer_list(self, downloaded, uploaded):
        tracker = self.last_used_tracker

        if tracker.startswith('udp'):
            peer_list, interval = self._announce_UDP(self.s,self.conn,downloaded,uploaded)
            return peer_list,interval

        elif tracker.startswith('http'):
            peer_list, interval = self._announce_HTTP(tracker, downloaded, uploaded)
            return peer_list, interval

        elif tracker == None:
            return self.get_peers_from_announce_list(downloaded, uploaded)