import socket
import os
from os import curdir, sep

PORT_NUMBER = 8080

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

server_address = ('', PORT_NUMBER)

sock.bind(server_address)

sock.listen(1)


def foo(file):
    with open(file, 'rb') as f:
        return f.read()


while True:
    print("Waiting for connection")
    connection_socket, client_address = sock.accept()
    print("Connection received from %s" % str(client_address))
    message_received = str(connection_socket.recv(4096), 'utf-8')

    lines = message_received.splitlines()
    request, path, version = lines[0].split()
    print(lines[0])
    print(request, path, version)
    if os.path.isfile(curdir + path):
        x = foo(curdir+path)
        msg_to_send = "HTTP/1.1 200 OK\n" + "Content-Type: image/jpg\n" + "\n"
        msg_to_send=msg_to_send.encode()+x
        connection_socket.sendall(msg_to_send)
