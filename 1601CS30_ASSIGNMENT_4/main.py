from chord import Chord, Node
from utils import get_hash
import os
import random

def main():
    print("Entering new node details...")
    print("Enter files directory: ")
    files_dir = input()
    if not os.path.isdir(files_dir):
        print("Path does not exist!")
        exit(1)
    
    print("Enter node ip/hostname: ", end='')
    ip = input()

    print("Enter node port: ", end='')
    port = int(input())
    id = get_hash((ip, port))
    node = Node(id, ip, port)

    print("\nEntering details of an existing node...")
    print("Enter ip/hostname (enter -1 if current node is the first node): ", end='')
    oldNode = None
    ip = input()
    
    if ip != '-1':
        print("Enter port: ", end='')
        port = int(input())
        id = get_hash((ip, port))
        oldNode = Node(id, ip, port)
        print("Joining chord network...")
    else:
        print("Populating with 100 empty files with random names...")
        for i in range(100):
            open(os.path.join(files_dir, f"{random.randint(0, 10000)}.txt"), 'a').close()
        print("Creating chord network...")
    
    ch = Chord(node, oldNode, files_dir)
    return

if __name__ == '__main__':
    main()