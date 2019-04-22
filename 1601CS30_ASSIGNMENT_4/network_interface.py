import socket
import threading
import query
import time
import globals


# Listens for queries, sends out queries
class NetworkInterface:
    def __init__(self, node, chord):
        self.node = node
        self.chord = chord
        threading.Thread(target=self._start_listening, args=()).start()
        return
    
    # Start listening for queries on the self.node's (ip, port)
    def _start_listening(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        # try:
        if True:
            print("Starting server on {host}:{port}...".format(host=self.node.ip, port=self.node.port))
            self.socket.bind((self.node.ip, self.node.port))
            print("Server started on port {host}:{port}.".format(host=self.node.ip, port=self.node.port))
        
        # except OSError:
        #     print("Error binding to port!")
        #     self.shutdown()
        #     return False
        
        self.socket.listen(1)
        while True:
            (client, address) = self.socket.accept()
            client.settimeout(60)
            print("Recieved connection from {addr}".format(addr=address))
            threading.Thread(target=self._handle_query_thread, args=(client, address)).start()
        return

    # Handles a query returns data through the socket and dies    
    def _handle_query_thread(self, client, address):
        data = client.recv(globals.PACKET_SIZE).decode()
        query_str = ''.join(data)
        print(f"Received {query_str} from {address}")
        q = query.Query.from_string(query_str)
        response = q.execute(chord=self.chord, networkInterface=self, str_out=True).encode('ascii')
        print(f"Sending response {response.decode('ascii')}")
        client.send(response)
        client.close()
    
    def send_query(self, qstring, to_node):
        unsuccessful = True
        while unsuccessful:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                # connect to host server
                s.connect((to_node.ip, to_node.port))
                print(f"Sending request: {qstring} to {(to_node.ip, to_node.port)}")
                s.send(qstring.encode('ascii'))
                data = s.recv(globals.PACKET_SIZE)
                print(f"Got data: {data.decode('ascii')}")
                s.close()
                unsuccessful = False
            except Exception as e:
                print(f"Exception caught: {e}. Retrying in 5...")
                time.sleep(5)
                pass
        
        return data
    
    def shutdown(self):
        return
