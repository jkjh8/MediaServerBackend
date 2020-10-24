import socket
import struct

# MCAST_GRP = '224.1.1.1'
# MCAST_PORT = 5007

sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
# sock.bind((MCAST_GRP, MCAST_PORT))
sock.bind(('', 9999))
mreq = struct.pack("4sl", socket.inet_aton('239.192.168.110'), socket.INADDR_ANY)
sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)

while True:
    recv = sock.recv(2048)
    print (recv)

