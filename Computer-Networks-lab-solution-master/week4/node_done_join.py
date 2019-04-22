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


class Node(threading.Thread):

    def run(self):
        self.sock_listen = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock_listen.bind((self.ip, self.port))
        # print("inside run of %s" % str(self.sock_listen.getsockname()))

        while True:
            data, address = self.sock_listen.recvfrom(4096)
            data = str(data, 'utf-8')
            data = data.split(' ', 1)

            # list of string of data received is data
            function_called = data[0]
            # print("function called inside %d is %s by %s" % (self.id, function_called, str(address)))
            if function_called == "closest_preceding_finger":
                node = self.closest_preceding_finger(int(data[1]))
                self.sock_listen.sendto(str(node).encode(), address)
            if function_called == "successor":
                send_data = self.finger[0]
                self.sock_listen.sendto(str(send_data).encode(), address)

            if function_called == "find_succ":
                send_data = self.find_succ(int(data[1]))
                # print("value returned by find_succ is %s Sending to %s" % (str(send_data), str(address)))
                self.sock_listen.sendto(str(send_data).encode(), address)

            if function_called == "find_pred":
                send_data = self.find_pred(int(data[1]))
                self.sock_listen.sendto(str(send_data).encode(), address)

            if function_called == "predecessor":
                send_data = self.predecessor
                self.sock_listen.sendto(str(send_data).encode(), address)

            if function_called == "update_predecessor":
                self.predecessor = literal_eval(data[1])
                self.sock_listen.sendto("OK".encode(), address)

            if function_called == "update_finger_table":
                s, i = literal_eval(data[1])
                # print("going to update_finger_table")
                self.update_finger_table(s, i)
                # print("done")
                self.sock_listen.sendto("OK".encode(), address)

            if function_called == "update_successor":
                succ = literal_eval(data[1])
                self.finger[0] = succ
                self.sock_listen.sendto("OK".encode(), address)

    def __init__(self, ip, port):
        threading.Thread.__init__(self)
        ip = str(ip)
        port = int(port)
        self.ip = str(ip)
        self.port = int(port)
        address = str((ip, port))
        id = int(hashlib.sha256(address.encode('utf-8')).hexdigest(), 16) % 32
        self.id = id
        self.finger = [[ip, port, id], [ip, port, id], [ip, port, id], [ip, port, id], [ip, port, id], ]
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
            return self.finger[0]
        else:
            # print("Inside else of find_succ. Sending to %s" % str((n_dash[0], n_dash[1])))
            self.sock_send.sendto("successor".encode(), (n_dash[0], n_dash[1]))
            rcv_data, temp = self.sock_send.recvfrom(4096)
            rcv_data = literal_eval(str(rcv_data, 'utf-8'))
            return rcv_data

    def find_pred(self, id):
        # print("Inside find_pred")
        n_dash = [self.ip, self.port, self.id]
        n_dash_successor = self.finger[0]
        # print("n_dash %d n_dash_succ %d id %d" % (n_dash[2], n_dash_successor[2], id))

        while True:
            if n_dash_successor[2] <= n_dash[2] and (n_dash[2] < id <= 31 or 0 <= id <= n_dash_successor[2]):
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
                n_dash_successor = self.finger[0]
            else:
                self.sock_send.sendto("successor".encode(), (n_dash[0], n_dash[1]))
                data, address = self.sock_send.recvfrom(4096)
                n_dash_successor = literal_eval(str(data, 'utf-8'))
        return n_dash

    def closest_preceding_finger(self, id):
        for i in range(4, -1, -1):
            if id <= self.id and (self.id < self.finger[i][2] <= 31 or 0 <= self.finger[i][2] < id):
                return self.finger[i]
            elif id > self.id and self.id < self.finger[i][2] < id:
                return self.finger[i]
        # return [self.ip, self.port, self.id]
        succ = self.finger[0]
        send_msg = "find_pred " + str(id)
        self.sock_send.sendto(send_msg.encode(), (succ[0], succ[1]))
        rcv_data, address = self.sock_send.recvfrom(4096)
        rcv_data = str(rcv_data, 'utf-8')
        ans = literal_eval(rcv_data)
        return ans

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
        # self.successor = self.finger[0]

        # get predecessor of successor
        self.sock_send.sendto("predecessor".encode(), (self.finger[0][0], self.finger[0][1]))
        rcv_data, temp = self.sock_send.recvfrom(4096)
        # print("Data received is %s" % str(rcv_data))
        rcv_data = literal_eval(str(rcv_data, 'utf-8'))
        self.predecessor = rcv_data

        # update predecessor of successor
        send_msg = "update_predecessor " + str([self.ip, self.port, self.id])
        # print("Message sending to %s is %s" % (str((self.successor[0], self.successor[1])), send_msg))
        self.sock_send.sendto(send_msg.encode(), (self.finger[0][0], self.finger[0][1]))
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
            key = (self.id - 2 ** i) % 32
            p = self.find_pred(key)
            if p != [self.ip, self.port, self.id]:
                self.sock_send.sendto("successor".encode(), (p[0], p[1]))
                rcv_data, address = self.sock_send.recvfrom(4096)
                p_succ = literal_eval(str(rcv_data, 'utf-8'))
            else:
                p_succ = self.finger[0]
            if p_succ[2] == key:
                p = p_succ

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

    def fix_fingers(self):
        while True:
            for i in range(0, 5):
                succ = self.find_succ((self.id + 2 ** i) % 32)
                self.finger[i] = succ
                time.sleep(1)
                # print("fixing %d of %d" % (i, self.id))

    def remove(self):
        succ = self.finger[0]
        pred = self.predecessor
        send_msg = "update_successor " + str(succ)
        self.sock_send.sendto(send_msg.encode(), (pred[0], pred[1]))
        self.sock_send.recvfrom(4096)
        send_msg = "update_predecessor " + str(pred)
        self.sock_send.sendto(send_msg.encode(), (succ[0], succ[1]))
        self.sock_send.recvfrom(4096)


def always_on_node():
    node = Node(IP, PORT)
    print("Id of always on %d" % node.id)
    node.start()
    return node


def main():
    NODE = always_on_node()
    threading.Thread(target=NODE.fix_fingers).start()
    # x = int(input("1 to join\n2 to delete"))
    x = 1
    if x == 1:
        # ip = input("Enter the ip of the new node")
        # port = input("Enter the port of the new node")
        # node = Node(ip, port)
        print("Making new node")
        node1 = Node('172.16.181.205', 1234)
        print("id of new node %d" % node1.id)
        node1.start()
        node1.join_node()
        print("Done joining %d" % node1.id)
        threading.Thread(name="dafsf", target=node1.fix_fingers).start()
        time.sleep(7)
        node2 = Node('172.16.181.205', 1238)
        print("id of new node %d" % node2.id)
        node2.start()
        # node2.join()
        node2.join_node()
        print("done joining %d" % node2.id)
        threading.Thread(target=node2.fix_fingers).start()
        time.sleep(7)
        # print("Wait for it")
        node3 = Node('172.16.181.205', 1242)
        print("id of the new node is %d" % node3.id)
        node3.start()
        node3.join_node()
        print("Done joining %d" % node3.id)
        threading.Thread(target=node3.fix_fingers).start()
        time.sleep(7)
        print("Wait for it")
        # thread3 = threading.Thread(name="dafsaf", target=node2.fix_fingers())
        # thread1 = threading.Thread(name="dfas", target=NODE.fix_fingers())

        # thread3.start()
        # thread3.join()
        # thread1.start()
        # thread1.join()
        # thread2.start()
        # thread2.join()
        time.sleep(10)
        print("The finger table of %d is " % node1.id)
        node1.print_finger_table()
        print("The finger table of %d is " % node2.id)
        node2.print_finger_table()
        print("The finger table of always on %d is " % NODE.id)
        NODE.print_finger_table()
        print("The finger tale of %d is " % node3.id)
        node3.print_finger_table()
        print("deleting %d" %node3.id)
        node3.remove()
        del node3
        print("Wait for it")
        time.sleep(10)
        print("The finger table of %d is " % node1.id)
        node1.print_finger_table()
        print("The finger table of %d is " % node2.id)
        node2.print_finger_table()
        print("The finger table of always on %d is " % NODE.id)
        NODE.print_finger_table()



if __name__ == "__main__":
    main()
