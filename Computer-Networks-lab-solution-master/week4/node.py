import hashlib
import os
import socket
import threading
import time
from ast import literal_eval
from os import curdir, listdir
from os.path import isfile, join

node = 0
IP = '172.16.147.128'
PORT = 8080
Address = str((IP, PORT))
ID = int(hashlib.sha256(Address.encode('utf-8')).hexdigest(), 16) % 32


class Node(threading.Thread):

    def run(self):
        self.sock_listen = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock_listen.bind((self.ip, self.port))

        while True:
            data, address = self.sock_listen.recvfrom(4096)
            data = str(data, 'utf-8')
            data = data.split(' ', 1)

            function_called = data[0]
            if function_called == "closest_preceding_finger":
                node = self.closest_preceding_finger(int(data[1]))
                self.sock_listen.sendto(str(node).encode(), address)
            if function_called == "successor":
                send_data = self.finger[0]
                self.sock_listen.sendto(str(send_data).encode(), address)

            if function_called == "find_succ":
                send_data = self.find_succ(int(data[1]))
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
                self.update_finger_table(s, i)
                self.sock_listen.sendto("OK".encode(), address)

            if function_called == "transfer_files":
                transferlist = self.transfer_files(int(data[1]))
                self.sock_listen.sendto(str(transferlist).encode(), address)

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

    def find_succ(self, id):
        n_dash = self.find_pred(id)
        if n_dash[2] == self.id:
            return self.finger[0]
        else:
            self.sock_send.sendto("successor".encode(), (n_dash[0], n_dash[1]))
            rcv_data, temp = self.sock_send.recvfrom(4096)
            rcv_data = literal_eval(str(rcv_data, 'utf-8'))
            return rcv_data

    def find_pred(self, id):
        n_dash = [self.ip, self.port, self.id]
        n_dash_successor = self.finger[0]

        while True:
            if n_dash_successor[2] <= n_dash[2] and (n_dash[2] < id <= 31 or 0 <= id <= n_dash_successor[2]):
                break
            elif n_dash[2] < id <= n_dash_successor[2]:
                break
            send_msg = "closest_preceding_finger " + str(id)

            if n_dash == [self.ip, self.port, self.id]:
                n_dash = self.closest_preceding_finger(id)

            else:
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
        succ = self.finger[0]
        send_msg = "find_pred " + str(id)
        self.sock_send.sendto(send_msg.encode(), (succ[0], succ[1]))
        rcv_data, address = self.sock_send.recvfrom(4096)
        rcv_data = str(rcv_data, 'utf-8')
        ans = literal_eval(rcv_data)
        return ans

    def join_node(self):
        self.init_finger_table()
        self.update_others()

    def print_finger_table(self):
        for i in range(len(self.finger)):
            print("%d  |  %d  |  %d" % (i, (self.id + 2 ** i) % 32, self.finger[i][2]))

    def init_finger_table(self):
        key = self.id + 1
        msg_send = "find_succ " + str(key)
        self.sock_send.sendto(msg_send.encode(), (IP, PORT))
        rcv_data, temp = self.sock_send.recvfrom(4096)
        rcv_data = literal_eval(str(rcv_data, 'utf-8'))
        self.finger[0] = rcv_data

        # get predecessor of successor
        self.sock_send.sendto("predecessor".encode(), (self.finger[0][0], self.finger[0][1]))
        rcv_data, temp = self.sock_send.recvfrom(4096)
        rcv_data = literal_eval(str(rcv_data, 'utf-8'))
        self.predecessor = rcv_data

        # update predecessor of successor
        send_msg = "update_predecessor " + str([self.ip, self.port, self.id])
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
        if (self.finger[i][2] <= self.id and (self.id <= s[2] <= 31 or 0 <= s[2] < self.finger[i][2])) \
                or (self.finger[i][2] > self.id and self.id <= s[2] < self.finger[i][2]):
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

    def transfer_files(self, id_requesting_node):
        id_requesting_node = int(id_requesting_node)
        file_list = [f for f in listdir(curdir) if isfile(join(curdir, f))]
        # print(file_list)
        transfer_list = []
        for file in file_list:
            hash_value = int(hashlib.sha256(file.encode('utf-8')).hexdigest(), 16) % 32
            # print(hash_value)
            succ = self.find_succ(hash_value)
            if succ[2] == id_requesting_node:
                # print("Yes")
                transfer_list.append(file)
        # print(transfer_list)
        return transfer_list

    def request_files(self):
        succ = self.finger[0]
        send_msg = "transfer_files " + str(self.id)
        self.sock_send.sendto(send_msg.encode(), (succ[0], succ[1]))
        rcv_data, address = self.sock_send.recvfrom(4096)
        rcv_data = str(rcv_data, 'utf-8')
        transfer_list = literal_eval(rcv_data)
        print(transfer_list)
        for file in transfer_list:
            open(file, 'a').close()

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
    global node
    while True:
        x = int(input(
            "1 to join\n2 to delete\n3 to print finger table\n4 to get successor\n5 to get predecessor\n6to exit"))
        if x == 1:
            ip = input("Enter the ip of the new node")
            port = input("Enter the port of the new node")
            node = Node(ip, port)
            print("id of new node %d" % node.id)
            node.start()
            node.join_node()
            print("Joining node %d" % node.id)
            threading.Thread(name="dafsf", target=node.fix_fingers).start()
            time.sleep(7)
            print("Done joining %d\nWaiting to stabiilise..." % node.id)
            time.sleep(10)
            print("The finger table of the new node %d is " % node.id)
            node.print_finger_table()
            print("Transferring files")
            node.request_files()
            print("Done")

        elif x == 3:
            node.print_finger_table()
        elif x == 4:
            print(node.finger[0])
        elif x == 6:
            print("Exiting")
            os._exit(1)
        elif x == 2:
            node.remove()
            del node
        elif x == 5:
            print(node.predecessor)


if __name__ == "__main__":
    main()
