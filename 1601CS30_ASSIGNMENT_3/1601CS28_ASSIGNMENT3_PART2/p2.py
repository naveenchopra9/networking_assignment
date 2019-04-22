"""
Author: naveen
ROllNO-1601CS28
"""
# "signal" Allow socket destruction on Ctrl+C
import socket
import signal
import sys
import time
import threading
# Class for describing simple HTTP server objects
class ApplicationServer(object):
    def __init__(self, port=9000):
        # Default to any avialable network interface
        self.host="172.16.141.138"
        self.content_dir = '/Users/naveen/Desktop/6th/networking/1601CS28_Assignment4' # Directory where webpage files are stored
        self.port = port
    # Attempts to create and bind a socket to launch the server
    def start(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        try:
            print("Server Host name {host}:{port}".format(host=self.host, port=self.port))
            self.socket.bind((self.host, self.port))
            print("Server port number {port}.".format(port=self.port))
        except Exception as e:
            print("Error:  not bind to port number {port}".format(port=self.port))
            self.shutdown()
            sys.exit(1)

        self._listen() # Start listening for connections
    # Shuts down the server
    def shutdown(self):
        try:
            print("Shutting down server")
            s.socket.shutdown(socket.SHUT_RDWR)

        except Exception as e:
            pass # Pass if socket is already closed
        # Generate HTTP response headers.
        # Parameters:
        #     - response_code: HTTP response code to add to the header. 200 and 404 supported
        # Returns:
        #     A formatted HTTP header for the given response_code
    
    def generate_head(self, response_code):
        header = ''
        if response_code == 200:
            header += 'HTTP/1.1 200 OK\n'
        elif response_code == 404:
            header += 'HTTP/1.1 404 Not Found\n'

        time_now = time.strftime("%a, %d %b %Y %H:%M:%S", time.localtime())
        header += 'Date: {now}\n'.format(now=time_now)
        header += 'Server: Simple-Python-Server\n'
        header += 'Connection: close\n\n' # Signal that connection will be closed after completing the request
        return header
    # Listens on self.port for any incoming connections
    def _listen(self):
        self.socket.listen(5)
        while True:
            (client, address) = self.socket.accept()
            client.settimeout(60)
            print("Recieved connection from {addr}".format(addr=address))
            threading.Thread(target=self._handle_client, args=(client, address)).start()
     # Main loop for handling connecting clients and serving files from content_dir
     #    Parameters:
     #        - client: socket client from accept()
     #        - address: socket address from accept()
    def _handle_client(self, client, address):
        PACKET_SIZE = 1024
        while True:
            print("CLIENT",client)
            data = client.recv(PACKET_SIZE).decode() # Recieve data packet from client and decode

            if not data: break

            request_method = data.split(' ')[0]
            print("Method: {m}".format(m=request_method))
            print("Request Body: {b}".format(b=data))

            if request_method == "GET" or request_method == "HEAD":
                # Ex) "GET /index.html" split on space
                file_requested = data.split(' ')[1]

                # If get has parameters ('?'), ignore them
                file_requested =  file_requested.split('?')[0]

                if file_requested == "/":
                    file_requested = "/index.html"

                filepath_to_serve = self.content_dir + file_requested
                print("Serving web page [{fp}]".format(fp=filepath_to_serve))

                # Load and Serve files content
                try:
                    f = open(filepath_to_serve, 'rb')
                    if request_method == "GET": # Read only for GET
                        response_data = f.read()
                    f.close()
                    response_header = self.generate_head(200)

                except Exception as e:
                    print("File not found. Serving 404 page.")
                    response_header = self.generate_head(404)

                    if request_method == "GET": # Temporary 404 Response Page
                        response_data = b"<html><body><center><h1>Error 404: File not found</h1></center><p>Head back to <a>dry land</a>.</p></body></html>"

                response = response_header.encode()
                if request_method == "GET":
                    response += response_data

                client.send(response)
                client.close()
                break
            else:
                print("Unknown HTTP request method: {method}".format(method=request_method))
# Shutsdown server from a SIGINT recieved signal
def shutdownServer(sig, unused):
    server.shutdown()
    sys.exit(1)

signal.signal(signal.SIGINT, shutdownServer)
server = ApplicationServer(8000)
server.start()
print("Press Ctrl+C to shut down server.")










