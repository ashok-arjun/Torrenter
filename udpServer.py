import socket

s = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)
s.bind(('',1876))
response = s.recv(1024)
print(response)