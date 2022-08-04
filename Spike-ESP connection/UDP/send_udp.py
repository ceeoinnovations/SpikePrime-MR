"""Test file that sends UDP messages"""

import socket

UDP_IP = "10.245.95.56"
UDP_PORT = 21024
MESSAGE = b"1300"

print("UDP target IP: %s" % UDP_IP)
print("UDP target port: %s" % UDP_PORT)
print("message: %s" % MESSAGE)

sock = socket.socket(socket.AF_INET, # Internet
                     socket.SOCK_DGRAM) # UDP
sock.sendto(MESSAGE, (UDP_IP, UDP_PORT))

