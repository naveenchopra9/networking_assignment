import globals
import utils
import socket
import threading

# class Finger:
#     def __init__(self, start, end, node=None, node_ip=None, node_port=None):
#         self.start = start
#         self.end = end
#         self.update_node(node, node_ip, node_port)
#         return
    
#     def update_node(self, node, node_ip, node_port):
#         self.node = node
#         self.node_ip = node_ip
#         self.node_port = node_port
#         return


class Finger:
    def __init__(self, interval_beg, interval_end, node=None):
        self.interval_beg = interval_beg
        self.interval_end = interval_end
        self.node = node
        return


class Node:
    def __init__(self, id, ip, port):
        self.id = id
        self.ip = ip
        self.port = port
        return

    def _query(self, qname, *args):
        query_li = [qname, self.id, self.ip, self.port, *args]
        query_str = '|||'.join([str(i) for i in query_li])
        query = Query(query_str)
        return query.execute()
    
    def q_successor(self):
        return self._query('get_successor')
    
    def q_closest_preceding_finger(self):
        return self._query('get_successor')


class Query:
    GET_SUCCESSOR = 'get_successor'
    CLOSEST_PRECEDING_FINGER = 'CLOSEST_PRECEDING_FINGER'

    def __init__(self, qname, from_node, to_node, *args):
        self.qname = qname
        self.from_node_id = from_node.id
        self.to_node = to_node
        self._parse_q_str(query_str)
        return
    
    @classmethod
    def from_data(cls, qname, from_node, to_node, *args):
        query_li = [qname, from_node.id, to_node.id, to_node.ip, to_node.port, *args]
        query_str = '|||'.join([str(i) for i in query_li])
        return cls(query_str)

    #  Parses str and sets variables
    def _parse_q_str(self, query_str):
        self.query_str = query_str
        li = query_str.split('|||')
        self.qtype = li[0]
        self.node = li[1:4]
        return
    
    # If the query is self refential, no request is sent
    # Otherwise, send a request, parse the response and return
    def execute(self):
        return

    def __str__(self):
        return str(self.query_str)

# Listens for requests, makes queries and executes them
class Listener:
    def __init__(self, node):
        self.node = node
        self.finger_table = []
        self.successor = None
        self.predecessor = None
        self._start_listening()
        return

    # Compile and send a query to the given node
    def query_node(self, node, query):
        return
    
    # Start listening for queries on the self.node's (ip, port)
    def _start_listening(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            print("Starting server on {host}:{port}".format(host=self.node.ip, port=self.node.port))
            self.socket.bind((self.node.ip, self.node.port))
            print("Server started on port {host}:{port}.".format(host=self.node.ip, port=self.node.port))

        except OSError:
            print("Error binding to port!")
            self.shutdown()
            return False

        self.socket.listen(1)
        while True:
            (client, address) = self.socket.accept()
            client.settimeout(60)
            print("Recieved connection from {addr}".format(addr=address))
            threading.Thread(target=self._handle_query_thread, args=(client, address)).start()
        return

    # Handles a query returns data through the socket and dies    
    def _handle_query_thread(self, client, address, query):
        obtained_data = []
        while True:
            data = client.recv(1024).decode()
            if not data:
                break
            obtained_data.append(data)
        query_str = ''.join(obtained_data)
        query = Query(query_str)
        response = query.execute()
        client.send(response)
        client.close()

    def shutdown(self):
        return

    def find_successor(self, id):
        n_ = self.find_predecessor(id)
        return n_.q_successor()
    
    def find_predecessor(self, id):
        n_ = self.node
        # Check range wrap around # while not (n_ < id <= n_.successor):
        while not utils.check_in_node_interval(id, n_, n_.successor, beg_incl=False, end_incl=True):
            n_ = n_.q_closest_preceding_finger(id)
        return n_
    
    def closest_preceding_finger(self, id):
        for i in range(globals.m)[::-1]:
            # Check range wrap around # if self.id < self.finger_table[i].node < id:
            if utils.check_in_node_interval(self.finger_table[i], self.node.id, id, beg_incl=False, end_incl=False):
                return self.finger_table[i].node
