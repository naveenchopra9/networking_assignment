import socket
import os
from os import curdir, sep
import threading

PORT_NUMBER = 8080

sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

server_address = ('localhost', PORT_NUMBER)

sock.bind(server_address)

sock.listen(1)


def foo(file):
    with open(file, 'rb') as f:
        return f.read()


class ClientThread(threading.Thread):
    def __init__(self, client_address, client_socket):
        threading.Thread.__init__(self)
        self.client_socket = client_socket
        self.client_address = client_address
        print("New connection added : %s" % str(client_address))

    def run(self):
        foos(self.client_socket)


def foos(temp):
    connection_socket = temp
    print("Connection received from %s" % str(client_address))
    message_received = str(connection_socket.recv(4096), 'utf-8')

    lines = message_received.splitlines()
    request, path, version = lines[0].split()
    print(lines[0])
    print(request, path, version)
    if os.path.isfile(curdir + path):
        x = foo(curdir + path)
        msg_to_send = "HTTP/1.1 200 OK\n" + "Content-Type: text/html\n" + "\n"
        msg_to_send = msg_to_send.encode() + x
        connection_socket.send(msg_to_send)


while True:
    print("Waiting for connection")
    connection_socket, client_address = sock.accept()
    new_thread = ClientThread(client_address, connection_socket)
    new_thread.start()
