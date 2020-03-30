import socket
import os

pid = 1540
server_address = f'/tmp/trace-{pid}.uds'

sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
sock.connect(server_address)
sock.sendall(b'hello, this is client')
data = sock.recv(10240)
print(data)
