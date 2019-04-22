from node import Node
import threading
from node import always_on_node
import hashlib

# always on node
IP = '172.16.181.205'
PORT = 8080
Address = str((IP, PORT))
ID = int(hashlib.sha256(Address.encode('utf-8')).hexdigest(), 16) % 32

NODE = always_on_node()
threading.Thread(target=NODE.fix_fingers).start()
print("Always on node id is %d" % NODE.id)
print("The finger table of %d is " % NODE.id)
NODE.print_finger_table()

while True:
    x = int(input("Press 1 to print finger table"))
    if x == 1:
        NODE.print_finger_table()
