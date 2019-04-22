# globals.py: defines globals, constants
from enum import IntEnum, unique

PACKET_SIZE = 1024

# Delimiter for query, response strings
delim = "|||"

# Number of bits in ids and keys
m = 5

# Time between stabilization calls, in sec
stabilization_delay = 1
fix_fingers_delay = 1

@unique
class Qtype(IntEnum):
    LOOKUP_SUCCESSOR = 1
    LOOKUP_PREDECESSOR = 2
    FIND_SUCCESSOR = 3
    FIND_PREDECESSOR = 4
    CLOSEST_PRECEDING_FINGER = 5
    JOIN = 6
    UPDATE_FINGER_TABLE = 7
    NOTIFY = 8
    TRANSFER_FILES = 9

# Argument lengths for every query type
ArgsLength = dict()
ArgsLength[Qtype.LOOKUP_SUCCESSOR] = 0
ArgsLength[Qtype.LOOKUP_PREDECESSOR] = 0
ArgsLength[Qtype.FIND_SUCCESSOR] = 1
ArgsLength[Qtype.FIND_PREDECESSOR] = 1
ArgsLength[Qtype.CLOSEST_PRECEDING_FINGER] = 1
ArgsLength[Qtype.JOIN] = 1
ArgsLength[Qtype.UPDATE_FINGER_TABLE] = 2
ArgsLength[Qtype.NOTIFY] = 1
ArgsLength[Qtype.TRANSFER_FILES] = 1
