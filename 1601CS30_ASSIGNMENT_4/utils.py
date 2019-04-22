from hashlib import sha256
import globals
import chord

max_nodes = 1<<globals.m

def get_hash(a):
    m = globals.m
    hexdigest = sha256(str(a).encode()).hexdigest()
    hashval = 0
    for i in range(0, len(hexdigest), m):
        hashval += int(hexdigest[i : i + m], 16)
    hashval %= max_nodes
    return hashval


# def check_in_node_interval(n, beg, end, beg_incl=True, end_incl=False):
#     if isinstance(n, chord.Node):
#         n = n.id
#     if isinstance(beg, chord.Node):
#         beg = beg.id
#     if isinstance(end, chord.Node):
#         end = end.id
#     if isinstance(n, str):
#         n = int(n)
#     if isinstance(beg, str):
#         beg = int(beg)
#     if isinstance(end, str):
#         end = int(end)
    
#     if beg_incl:
#         beg -= 1
#     if end_incl:
#         end += 1
#     n = (n - beg + max_nodes) % max_nodes
#     end = (end - beg + max_nodes) % max_nodes
#     beg = 0
#     return beg < n < end


def check_in_node_interval(n, beg, end, beg_incl=True, end_incl=False):
    if isinstance(n, chord.Node):
        n = n.id
    if isinstance(beg, chord.Node):
        beg = beg.id
    if isinstance(end, chord.Node):
        end = end.id
    if isinstance(n, str):
        n = int(n)
    if isinstance(beg, str):
        beg = int(beg)
    if isinstance(end, str):
        end = int(end)
    
    n = (n - beg + max_nodes) % max_nodes
    end = (end - beg + max_nodes) % max_nodes
    beg = 0
    if end == beg:
        return True
    
    if not beg_incl and not end_incl:
        return beg < n < end
    elif not beg_incl and end_incl:
        return beg < n <= end
    elif beg_incl and not end_incl:
        return beg <= n < end
    elif beg_incl and end_incl:
        return beg <= n <= end
