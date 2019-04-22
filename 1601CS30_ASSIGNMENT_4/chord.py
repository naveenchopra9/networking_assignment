import random
import threading
import time
import os

import utils
import globals
from globals import m, Qtype, delim
from query import Query
from network_interface import NetworkInterface


# Contains finger info to put into the table
class Finger:
    def __init__(self, client_node_id, row_idx, node=None):
        self.client_node_id = client_node_id
        self.row_idx = row_idx
        self.node = node
        return
    
    def __getattr__(self, attr):
        if attr == 'start':
            return ((1 << self.row_idx) + self.client_node_id) % (1<<m)
        elif attr == 'end':
            return ((1 << (self.row_idx + 1)) + self.client_node_id - 1) % (1<<m)
        else:
            raise AttributeError


# Contains node info, abstraction that makes and sends queries
class Node:
    def __init__(self, id, ip, port):
        self.id = int(id)
        self.ip = str(ip)
        self.port = int(port)
        return
    
    def query(self, qtype, chord, args=()):
        networkInferface = chord.networkInferface
        qtype = Qtype(qtype)
        return Query(qtype, chord.node.id, self, *args).execute(chord, networkInferface)
    
    def __str__(self):
        return delim.join([str(i) for i in [self.id, self.ip, self.port]])
    

# Contains the finger table, executes queries
class Chord:
    def __init__(self, node, oldNode, files_dir):
        self.node = node
        self.finger_table = [Finger(client_node_id=self.node.id, row_idx=i) for i in range(m)]
        self.successor = None
        self.predecessor = None
        self.networkInferface = NetworkInterface(node=node, chord=self)
        self.files_dir = files_dir
        self.join(n_=oldNode)
        # Start stabilization thread
        threading.Thread(target=self._stabilize_thread, args=()).start()
        threading.Thread(target=self._fix_fingers_thread, args=()).start()
        self.user_input()
        return

    def find_successor(self, id):
        n_ = self.find_predecessor(id)
        return n_.query(Qtype.LOOKUP_SUCCESSOR, self)
    
    def find_predecessor(self, id):
        n_ = self.node
        # Check range wrap around # while not (n_ < id <= n_.successor):
        while not utils.check_in_node_interval(id, n_, n_.query(Qtype.LOOKUP_SUCCESSOR, self), beg_incl=False, end_incl=True):
            n_ = n_.query(Qtype.CLOSEST_PRECEDING_FINGER, self, args=(id,))
        return n_
    
    def closest_preceding_finger(self, id):
        n = self.node
        for i in range(m)[::-1]:
            # Check range wrap around # if self.id < self.finger_table[i].node < id:
            if utils.check_in_node_interval(self.finger_table[i].node, n, id, beg_incl=False, end_incl=False):
                return self.finger_table[i].node
        return n
    
    # n_ : older node used to join the network
    def join(self, n_=None):
        n = self.node
        # Joining an already created Chord network
        if n_ is not None:
            self.init_finger_table(n_)
            self.update_others()
            # move keys (predecessor, n] from successor
            self._distribute_files()
        
        # else, n is the only node in the network
        else:
            for i in range(m):
                self.finger_table[i].node = n
            self.predecessor = n
            self.successor = self.finger_table[0].node

        print("Successful join()")
        return
    
    # Initialize finger table of local node
    # n_ is an arbitrary node already in the network
    def init_finger_table(self, n_):
        n = self.node
        self.finger_table[0].node = n_.query(Qtype.FIND_SUCCESSOR, chord=self, args=(self.finger_table[0].start,))
        self.successor = self.finger_table[0].node
        self.predecessor = self.successor.query(Qtype.LOOKUP_PREDECESSOR, self)
        for i in range(m-1):
            if utils.check_in_node_interval(self.finger_table[i+1].start, n, self.finger_table[i].node, beg_incl=True, end_incl=False):
                self.finger_table[i+1].node = self.finger_table[i].node
            else:
                self.finger_table[i+1].node = n_.query(Qtype.FIND_SUCCESSOR, self, args=(self.finger_table[i+1].start,))
        return
    
    def update_others(self):
        n = self.node
        for i in range(m):
            # Find last node p whose ith finger might be n
            p = self.find_predecessor(n.id - 1 << i)
            p.query(Qtype.UPDATE_FINGER_TABLE, self, args=(n, i))
    
    def update_finger_table(self, s, i):
        if utils.check_in_node_interval(s, self.node.id, self.finger_table[i].node.id, beg_incl=True, end_incl=False):
            self.finger_table[i].node = s
            p = self.predecessor # get first node preceeding n
            p.query(Qtype.UPDATE_FINGER_TABLE, self, args=(s, i))
    
    def _stabilize_thread(self):
        print("Starting stabilization thread")
        while True:
            time.sleep(globals.stabilization_delay)
            self.stabilize()

    # Periodically verify n's immediate successor,
    #  and tell successor about n
    def stabilize(self):
        n = self.node
        x = self.successor.query(Qtype.LOOKUP_PREDECESSOR, self)
        if utils.check_in_node_interval(x, n, self.successor, beg_incl=False, end_incl=False):
            self.successor = x
        self.successor.query(Qtype.NOTIFY, self, args=(n,))

    def notify(self, n_):
        n = self.node
        if self.predecessor == None or utils.check_in_node_interval(n_, self.predecessor, n, beg_incl=False, end_incl=False):
            self.predecessor = n_
    
    def _fix_fingers_thread(self):
        print("Starting fix fingers thread")
        while True:
            time.sleep(globals.fix_fingers_delay)
            self.fix_fingers()

    # Periodically refresh finger table entries
    def fix_fingers(self):
        i = random.randint(0, len(self.finger_table) - 1)
        self.finger_table[i].node = self.find_successor(self.finger_table[i].start)
        return

    def shutdown(self):
        return

    def user_input(self):
        while True:
            # Print menu
            print("0. Exit")
            print("1. Print current node details")
            print("2. Print successor/predecessor")
            print("3. Print file IDs contained in current node")
            print("4. Print finger table")
            print("Enter choice: ")
            choice = int(input())
            if choice == 0:
                self.shutdown()
                return
            elif choice == 1:
                print(f"Node id: {self.node.id}, ip: {self.node.ip}, port: {self.node.port}")
                continue
            elif choice == 2:
                if self.predecessor is not None:
                    print(f"Predecessor node id: {self.predecessor.id}, ip: {self.predecessor.ip}, port: {self.predecessor.port}")
                else:
                    print("Predecessor node is uninitialized!")
                
                if self.successor is not None:
                    print(f"Successor node id: {self.successor.id}, ip: {self.successor.ip}, port: {self.successor.port}")
                else:
                    print("Successor node is uninitialized!")
                
                continue
            elif choice == 3:
                print(f"There are {len(os.listdir(self.files_dir))} files contained in this node:")
                for filename in os.listdir(self.files_dir):
                    print(filename)
                continue
            elif choice == 4:
                print("Finger table:")
                for i, finger in enumerate(self.finger_table):
                    print(f"i: {i}, "
                          f"start: {finger.start}, "
                          f"end: {finger.end} "
                          f"node: <id: {finger.node.id} ip: {finger.node.ip} port: {finger.node.port}>")
            else:
                print("Invalid choice!")
        return
    
    def transfer_files(self, new_id):
        # Transfer everything from (self.node.id, new_id]
        files = [f for f in os.listdir(self.files_dir)
                   if utils.check_in_node_interval(utils.get_hash(f), self.node.id, new_id, beg_incl=False, end_incl=True)]
        for f in files:
            os.remove(os.path.join(self.files_dir, f))
        return files

    def _distribute_files(self):
        files = self.predecessor.query(Qtype.TRANSFER_FILES, self, args=(self.node.id,))
        for f in files:
            if f:
                open(os.path.join(self.files_dir, f), 'a').close()
        return
