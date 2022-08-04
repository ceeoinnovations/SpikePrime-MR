"""Test file that receives UDP messages"""

import socket

UDP_IP = "10.245.95.56"
UDP_PORT = 21024

sock = socket.socket(socket.AF_INET, # Internet
                     socket.SOCK_DGRAM) # UDP
sock.bind((UDP_IP, UDP_PORT))

while True:
    data, addr = sock.recvfrom(1024) # buffer size is 1024 bytes
    data = data.decode('UTF-8')
    print("received message: %s" % data)