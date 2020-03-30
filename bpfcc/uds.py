import socket
import os

pid = 1540
server_address = f'/tmp/trace-{pid}.uds'
try:
    os.unlink(server_address)
except OSError:
    if os.path.exists(server_address):
        raise

sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
sock.bind(server_address)
sock.listen(1)
while True:
    print('listening...')
    conn, client = sock.accept()
    print(f'accepted: {client}')
    data = conn.recv(20480)
    conn.sendall(b'hello unix domain socket')
