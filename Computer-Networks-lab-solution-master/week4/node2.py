import socket
import threading
from ast import literal_eval
import hashlib
import time
import pprint

# always on node
IP = '172.16.181.205'
PORT = 8080
Address = str((IP, PORT))
ID = int(hashlib.sha256(Address.encode('utf-8')).hexdigest(), 16) % 32


class Node():

    def __init__(self, ip, port):
        ip = str(ip)
        port = int(port)
        self.ip = str(ip)
        self.port = int(port)
        address = str((ip, port))
        id = int(hashlib.sha256(address.encode('utf-8')).hexdigest(), 16) % 32
        self.id = id
        self.finger = [[ip, port, id], [ip, port, id], [ip, port, id], [ip, port, id], [ip, port, id], ]
        self.successor = [ip, port, id]
        self.predecessor = [ip, port, id]
        self.create_send_socket()

    def create_send_socket(self):
        self.sock_send = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock_send.bind((self.ip, self.port + 1))
        # print("created send socket %s" % str(self.sock_send.getsockname()))

    def find_succ(self, id):
        # print("Inside find_succ")
        n_dash = self.find_pred(id)
        if n_dash[2] == self.id:
            return self.successor
        else:
            # print("Inside else of find_succ. Sending to %s" % str((n_dash[0], n_dash[1])))
            self.sock_send.sendto("successor".encode(), (n_dash[0], n_dash[1]))
            rcv_data, temp = self.sock_send.recvfrom(4096)
            rcv_data = literal_eval(str(rcv_data, 'utf-8'))
            return rcv_data

    def find_pred(self, id):
        # print("Inside find_pred")
        n_dash = [self.ip, self.port, self.id]
        n_dash_successor = self.successor
        # print("n_dash %d n_dash_succ %d id %d" % (n_dash[2], n_dash_successor[2], id))

        while True:
            if n_dash_successor[2] <= n_dash[2] and (n_dash[2] < id <= 31 or 0 <= id < n_dash_successor[2]):
                break
            elif n_dash[2] < id <= n_dash_successor[2]:
                break
            send_msg = "closest_preceding_finger " + str(id)

            if n_dash == [self.ip, self.port, self.id]:
                n_dash = self.closest_preceding_finger(id)

            else:
                # print("Sending message %s to %s by %s" % (
                #     send_msg, str((n_dash[0], n_dash[1])), str(self.sock_send.getsockname())))
                self.sock_send.sendto(send_msg.encode(), (n_dash[0], n_dash[1]))
                data, address = self.sock_send.recvfrom(4096)
                n_dash = literal_eval(str(data, 'utf-8'))
            if n_dash_successor == [self.ip, self.port, self.id]:
                n_dash_successor = self.successor
            else:
                self.sock_send.sendto("successor".encode(), (n_dash[0], n_dash[1]))
                data, address = self.sock_send.recvfrom(4096)
                n_dash_successor = literal_eval(str(data, 'utf-8'))
        return n_dash

    def closest_preceding_finger(self, id):
        for i in range(4, -1, -1):
            if id <= self.id and (self.id < self.finger[i][2] <= 31 or 0 <= self.finger[i][2] < self.id):
                return self.finger[i]
            elif id > self.id and self.id < self.finger[i][2] < id:
                return self.finger[i]
        return [self.ip, self.port, self.id]

    def join_node(self):
        # print("inside join_node")
        self.init_finger_table()
        self.update_others()
        # print("finished joining")

    def print_finger_table(self):
        for i in range(len(self.finger)):
            print("%d  |  %d  |  %d" % (i, (self.id + 2 ** i) % 32, self.finger[i][2]))

    def init_finger_table(self):
        # print("inside init_finger_table id: %d" % self.id)
        key = self.id + 1
        msg_send = "find_succ " + str(key)
        self.sock_send.sendto(msg_send.encode(), (IP, PORT))
        rcv_data, temp = self.sock_send.recvfrom(4096)
        rcv_data = literal_eval(str(rcv_data, 'utf-8'))
        # print("received data by %s is" % str(self.sock_send.getsockname()))
        # print(rcv_data)
        # print("Data recevied by %s is %s" % (str((self.ip, self.port)), str(rcv_data)))
        self.finger[0] = rcv_data
        self.successor = self.finger[0]

        # get predecessor of successor
        self.sock_send.sendto("predecessor".encode(), (self.successor[0], self.successor[1]))
        rcv_data, temp = self.sock_send.recvfrom(4096)
        # print("Data received is %s" % str(rcv_data))
        rcv_data = literal_eval(str(rcv_data, 'utf-8'))
        self.predecessor = rcv_data

        # update predecessor of successor
        send_msg = "update_predecessor " + str([self.ip, self.port, self.id])
        # print("Message sending to %s is %s" % (str((self.successor[0], self.successor[1])), send_msg))
        self.sock_send.sendto(send_msg.encode(), (self.successor[0], self.successor[1]))
        self.sock_send.recvfrom(4096)

        for i in range(1, 5):
            if self.finger[i - 1][2] <= self.id and \
                    (self.id <= (self.id + 2 ** i) % 32 <= 31 or 0 <= (self.id + 2 ** i) % 32 < self.finger[i - 1][2]):
                self.finger[i] = self.finger[i - 1]

            elif self.id <= (self.id + 2 ** i) % 32 < self.finger[i - 1][2]:
                self.finger[i] = self.finger[i - 1]
            else:
                send_msg = "find_succ " + str((self.id + 2 ** i) % 32)
                self.sock_send.sendto(send_msg.encode(), (IP, PORT))
                rcv_data, temp = self.sock_send.recvfrom(4096)
                rcv_data = literal_eval(str(rcv_data, 'utf-8'))
                self.finger[i] = rcv_data

    def update_others(self):
        for i in range(0, 5):
            p = self.find_pred((self.id - 2 ** i) % 32)
            s = [self.ip, self.port, self.id]
            send_msg = "update_finger_table " + str([s, i])
            if p != [self.ip, self.port, self.id]:
                self.sock_send.sendto(send_msg.encode(), (p[0], p[1]))
                self.sock_send.recvfrom(4096)
            else:
                self.update_finger_table(s, i)

    def update_finger_table(self, s, i):
        if self.id == s[2]:
            return
        # print("inside update_finger_table of %d. s is %d i is %d" % (self.id, s[2], i))
        if (self.finger[i][2] <= self.id and (self.id <= s[2] <= 31 or 0 <= s[2] < self.finger[i][2])) \
                or (self.finger[i][2] > self.id and self.id < s[2] < self.finger[i][2]):
            # print("updated finger entry %d" % i)
            # print("calling update_finger_table of predecessor")
            self.finger[i] = s
            p = self.predecessor
            send_msg = "update_finger_table " + str([s, i])
            self.sock_send.sendto(send_msg.encode(), (p[0], p[1]))
            self.sock_send.recvfrom(4096)


def fix_fingers(node):
    while True:
        for i in range(0, 5):
            succ = node.find_succ((node.id + 2 ** i) % 32)
            node.finger[i] = succ
            time.sleep(1)
            print("fixing %d of %d" % (i, node.id))


def run(node):
    node.sock_listen = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    node.sock_listen.bind((node.ip, node.port))
    # print("inside run of %s" % str(self.sock_listen.getsockname()))

    while True:
        data, address = node.sock_listen.recvfrom(4096)
        data = str(data, 'utf-8')
        data = data.split(' ', 1)

        # list of string of data received is data
        function_called = data[0]
        # print("function called inside %d is %s by %s" % (self.id, function_called, str(address)))
        if function_called == "closest_preceding_finger":
            node = node.closest_preceding_finger(int(data[1]))
            node.sock_listen.sendto(str(node).encode(), address)
        if function_called == "successor":
            send_data = node.successor
            node.sock_listen.sendto(str(send_data).encode(), address)

        if function_called == "find_succ":
            send_data = node.find_succ(int(data[1]))
            # print("value returned by find_succ is %s Sending to %s" % (str(send_data), str(address)))
            node.sock_listen.sendto(str(send_data).encode(), address)

        if function_called == "predecessor":
            send_data = node.predecessor
            node.sock_listen.sendto(str(send_data).encode(), address)

        if function_called == "update_predecessor":
            node.predecessor = literal_eval(data[1])
            node.sock_listen.sendto("OK".encode(), address)

        if function_called == "update_finger_table":
            s, i = literal_eval(data[1])
            # print("going to update_finger_table")
            node.update_finger_table(s, i)
            # print("done")
            node.sock_listen.sendto("OK".encode(), address)


def always_on_node():
    node = Node(IP, PORT)
    print("Id of always on %d" % node.id)
    return node


def main():
    NODE = always_on_node()
    threading.Thread(target=run, args=(NODE)).start()
    threading.Thread(target=fix_fingers, args=(NODE)).start()

    # print("OK")
    # x = int(input("1 to join\n2 to delete"))
    x = 1
    if x == 1:
        # ip = input("Enter the ip of the new node")
        # port = input("Enter the port of the new node")
        # node = Node(ip, port)
        print("Making new node")
        node1 = Node('172.16.181.205', 1234)
        print("id of new node %d" % node1.id)
        threading.Thread(target=run, args=(node1))

        print("Done joining %d" % node1.id)
        threading.Thread(target=fix_fingers, args=(node1))
        # thread2 = threading.Thread(name="dafsf", target=node1.fix_fingers())
        time.sleep(7)
        node2 = Node('172.16.181.205', 1238)
        threading.Thread(target=run , args=(node2))

        print("id of new node %d" % node2.id)
        # node2.join()
        print("done joining %d" % node2.id)
        threading.Thread(target=fix_fingers, args=(node2))
        # thread3 = threading.Thread(name="dafsaf", target=node2.fix_fingers())
        # thread1 = threading.Thread(name="dfas", target=NODE.fix_fingers())

        # thread3.start()
        # thread3.join()
        # thread1.start()
        # thread1.join()
        # thread2.start()
        # thread2.join()
        time.sleep(20)
        print("The finger table of %d is " % node1.id)
        node1.print_finger_table()
        print("The finger table of %d is " % node2.id)
        node2.print_finger_table()
        print("The finger table of always on %d is " % NODE.id)
        NODE.print_finger_table()


if __name__ == "__main__":
    main()
