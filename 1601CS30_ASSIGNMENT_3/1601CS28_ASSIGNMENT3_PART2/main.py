"""
Author: naveen
ROllNO-1601CS28
"""
# signal Allow socket destruction on Ctrl+C
import socket
import signal
import sys
import time
import threading

host="172.16.184.88"
port = 9000
content_dir = '/Users/naveen/Desktop/6th/networking/1601CS28_Assignment4'

def start(self):
    self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        print("Starting server on {host}:{port}".format(host=host, port=port))
        socket.bind((host, port))
        print("Server started on port {port}.".format(port=port))

    except Exception as e:
        print("Error: Could not bind to port {port}".format(port=port))
        shutdown()
        sys.exit(1)

    _listen() 
    def shutdown(self):
        try:
            print("Shutting down server")
            s.socket.shutdown(socket.SHUT_RDWR)

        except Exception as e:
            pass # Pass if socket is already closed

    def _generate_headers(self, response_code):
        header = ''
        if response_code == 200:
            header += 'HTTP/1.1 200 OK\n'
        elif response_code == 404:
            header += 'HTTP/1.1 404 Not Found\n'

        time_now = time.strftime("%a, %d %b %Y %H:%M:%S", time.localtime())
        header += 'Date: {now}\n'.format(now=time_now)
        header += 'Server: Simple-Python-Server\n'
        header += 'Connection: close\n\n' 
        return header

    def _listen(self):
        self.socket.listen(5)
        while True:
            (client, address) = self.socket.accept()
            client.settimeout(60)
            print("Recieved connection from {addr}".format(addr=address))
            threading.Thread(target=self._handle_client, args=(client, address)).start()

    def _handle_client(self, client, address):
        PACKET_SIZE = 1024
        while True:
            print("CLIENT",client)
            data = client.recv(PACKET_SIZE).decode() 

            if not data: break

            request_method = data.split(' ')[0]
            print("Method: {m}".format(m=request_method))
            print("Request Body: {b}".format(b=data))

            if request_method == "GET" or request_method == "HEAD":
                file_requested = data.split(' ')[1]
                file_requested =  file_requested.split('?')[0]

                if file_requested == "/":
                    file_requested = "/index.html"

                filepath_to_serve = self.content_dir + file_requested
                print("Serving web page [{fp}]".format(fp=filepath_to_serve))
                try:
                    f = open(filepath_to_serve, 'rb')
                    if request_method == "GET": 
                        response_data = f.read()
                    f.close()
                    response_header = self._generate_headers(200)

                except Exception as e:
                    print("File not found. Serving 404 page.")
                    response_header = self._generate_headers(404)

                    if request_method == "GET":
                        response_data = b"<html><body><center><h1>Error 404: File not found</h1></center><p>Head back to <a>dry land</a>.</p></body></html>"

                response = response_header.encode()
                if request_method == "GET":
                    response += response_data

                client.send(response)
                client.close()
                break
            else:
                print("Unknown HTTP request method: {method}".format(method=request_method))

def shutdownServer(sig, unused):
    server.shutdown()
    sys.exit(1)

signal.signal(signal.SIGINT, shutdownServer)
server = WebServer(9000)
server.start()
print("Press Ctrl+C to shut down server.")






