import chord as chord_module
from network_interface import NetworkInterface
from globals import m, Qtype, ArgsLength, delim

# Provides bridge between a Chord and a NetworkInterface, to get results from queries
# Can be used to send out queries using the networkinterface or to execute queries on a Chord
class Query:
    def __init__(self, qtype, from_node_id, to_node, *args):
        self.qtype = Qtype(qtype)
        # Validate length of args
        assert ArgsLength[qtype] == len(args)
        self.from_node_id = from_node_id
        self.to_node = to_node
        self.args = args
        self.qstring = self._create_qstring()
        return
    
    def _create_qstring(self):
        query_li = [self.qtype.value, self.from_node_id, self.to_node, *self.args]
        qstring = delim.join([str(i) for i in query_li])
        return qstring
    
    @classmethod
    def from_string(cls, qstring):
        li = qstring.split(delim)
        qtype = Qtype(int(li[0]))
        from_node_id = li[1]
        to_node = chord_module.Node(*li[2: 5])
        # Extract args from the string query
        if qtype == Qtype.LOOKUP_SUCCESSOR:
            args = li[5:]
        elif qtype == Qtype.LOOKUP_PREDECESSOR:
            args = li[5:]
        elif qtype == Qtype.FIND_SUCCESSOR:
            args = (int(li[5]),)
        elif qtype == Qtype.FIND_PREDECESSOR:
            args = (int(li[5]),)
        elif qtype == Qtype.CLOSEST_PRECEDING_FINGER:
            args = (int(li[5]),)
        elif qtype == Qtype.JOIN:
            args = (chord_module.Node(*li[5:]),)
        elif qtype == Qtype.UPDATE_FINGER_TABLE:
            args = (chord_module.Node(*li[5:8]), int(li[8]))
        elif qtype == Qtype.NOTIFY:
            args = (chord_module.Node(*li[5:]),)
        elif qtype == Qtype.TRANSFER_FILES:
            args = (int(li[5]),)
        else:
            # print(f"Query.from_string: Undefined Qtype: {self.qtype}!")
            pass

        return cls(qtype, from_node_id, to_node, *args)
    
    # Response encoding, decoding
    def execute(self, chord, networkInterface, str_out=False):
        # If self referential query, args are parsed, command is executed
        #  and the response is encoded in a string
        success = False
        if chord.node.id == self.to_node.id:
            if self.qtype == Qtype.LOOKUP_SUCCESSOR:
                if not str_out:
                    retval = chord.successor
                else:
                    n = chord.successor
                    retval = delim.join([str(i) for i in [n.id, n.ip, n.port]])
                success = True
            elif self.qtype == Qtype.LOOKUP_PREDECESSOR:
                if not str_out:
                    retval = chord.predecessor
                else:
                    n = chord.predecessor
                    retval = delim.join([str(i) for i in [n.id, n.ip, n.port]])
                success = True
            elif self.qtype == Qtype.CLOSEST_PRECEDING_FINGER:
                n = chord.closest_preceding_finger(self.args[0])
                if not str_out:
                    retval = n
                else:
                    retval = delim.join([str(i) for i in [n.id, n.ip, n.port]])
                success = True
            elif self.qtype == Qtype.FIND_SUCCESSOR:
                n = chord.find_successor(self.args[0])
                if not str_out:
                    retval = n
                else:
                    retval = delim.join([str(i) for i in [n.id, n.ip, n.port]])
                success = True
            elif self.qtype == Qtype.FIND_PREDECESSOR:
                n = chord.find_predecessor(self.args[0])
                if not str_out:
                    retval = n
                else:
                    retval = delim.join([str(i) for i in [n.id, n.ip, n.port]])
                success = True
            elif self.qtype == Qtype.JOIN:
                chord.join(*self.args)
                retval = ''
                success = True
            elif self.qtype == Qtype.UPDATE_FINGER_TABLE:
                chord.update_finger_table(*self.args)
                retval = ''
                success = True
            elif self.qtype == Qtype.NOTIFY:
                chord.notify(*self.args)
                retval = ''
                success = True
            elif self.qtype == Qtype.TRANSFER_FILES:
                files = chord.transfer_files(self.args[0])
                if not str_out:
                    retval = files
                else:
                    retval = delim.join(files)
                success = True
            else:
                # print(f"Query.execute: Undefined Qtype: {self.qtype}!")
                retval = ''
                success = False
            if not str_out:
                return retval
            else:
                return delim.join([str(success), retval])
        
        # Network query: compiles into a string query and sends it
        ## defines how responses are decoded from the string
        else:
            # Send query through network interface, get response
            data = networkInterface.send_query(self.qstring, self.to_node).decode('ascii')
            if str_out:
                return data
            # Decode response string
            split_data = data.split(delim)
            success = bool(split_data[0])
            assert success
            
            split_data = split_data[1:]
            if self.qtype == Qtype.LOOKUP_SUCCESSOR:
                return chord_module.Node(*split_data)
            elif self.qtype == Qtype.LOOKUP_PREDECESSOR:
                return chord_module.Node(*split_data)
            elif self.qtype == Qtype.FIND_SUCCESSOR:
                return chord_module.Node(*split_data)
            elif self.qtype == Qtype.FIND_PREDECESSOR:
                return chord_module.Node(*split_data)
            elif self.qtype == Qtype.CLOSEST_PRECEDING_FINGER:
                return chord_module.Node(*split_data)
            elif self.qtype == Qtype.JOIN:
                return
            elif self.qtype == Qtype.UPDATE_FINGER_TABLE:
                return
            elif self.qtype == Qtype.NOTIFY:
                return
            elif self.qtype == Qtype.TRANSFER_FILES:
                return split_data
            else:
                # print(f"Query.execute: Undefined Qtype: {self.qtype}!")
                return
