import heapq
import functools
import math
import random
import abc

DEBUG = True
# EPSILON = 1e-8
EPSILON = 0

cwnd_updates = [[], []]
def add_cwnd_update(new_cwnd, timestamp):
    print("Changing cwnd to {} at time={}".format(new_cwnd, timestamp))
    if len(cwnd_updates[0]) > 0:
        cwnd_updates[0].append(cwnd_updates[0][-1])
        cwnd_updates[1].append(timestamp)
    cwnd_updates[0].append(new_cwnd)
    cwnd_updates[1].append(timestamp)

class CongestionControl(abc.ABC):
    @abc.abstractmethod
    def dup3_fn(self, timestamp, output):
        pass
    @abc.abstractmethod
    def timeout_fn(self, timestamp, output):
        pass
    @abc.abstractmethod
    def ack_received(self, num_packets_acked, timestamp):
        pass
    @abc.abstractmethod
    def window_update_time(self, timestamp, output):
        pass


class AIMD(CongestionControl):
    def __init__(self, source):
        self.source = source
        return

    def dup3_fn(self, timestamp, output):
        source = self.source
        source.reset_count += 1
        source.cwnd = max(int(source.cwnd / 2), 1)
        # print("Changing cwnd to {} at time={}".format(source.cwnd, timestamp))
        add_cwnd_update(source.cwnd, timestamp)
        
        # cwnd_updates[0].append(source.cwnd)
        # cwnd_updates[0].append(timestamp)

        creation_events = []
        temp_set = sorted(source.queued_packets.union(source.unacked_sent_packets))
        for packet in temp_set:
            creation_events.append(Event.packet_creation(packet))
        source.unqueued_packets = creation_events + source.unqueued_packets
        for packet in source.unqueued_packets:
            packet.reset_count = source.reset_count
        source.queued_packets = set()
        source.unacked_sent_packets = set()
        return source.enqueue_packets_in_window(timestamp, output)

    def timeout_fn(self, timestamp, output):
        source = self.source
        source.reset_count += 1
        source.cwnd = 1
        # print("Changing cwnd to {} at time={}".format(source.cwnd, timestamp))
        add_cwnd_update(source.cwnd, timestamp)
        creation_events = []

        temp_set = sorted(list(source.queued_packets.union(source.unacked_sent_packets)))
        for packet in temp_set:
            creation_events.append(Event.packet_creation(packet))

        source.unqueued_packets = sorted(creation_events + source.unqueued_packets)
        for packet in source.unqueued_packets:
            packet.reset_count = source.reset_count
        source.queued_packets = set()
        source.unacked_sent_packets = set()
        return source.enqueue_packets_in_window(timestamp, output)

    def ack_received(self, num_packets_acked, timestamp):
        if num_packets_acked <= 0 :
            return
        self.source.cwnd += 1.0 / math.floor(self.source.cwnd)
        # print("Changing cwnd to {} at time={}".format(self.source.cwnd, timestamp))
        add_cwnd_update(self.source.cwnd, timestamp)
        return

    def window_update_time(self, timestamp, output):
        return []


class Cubic(CongestionControl):
    def __init__(self, source, W_max=100, beta=0.125, C=10):
        self.source = source
        self.beta = beta
        self.C = C
        self.W_max = W_max
        return
    
    @staticmethod
    def cuberoot(x):
        if x > 0:
            return x ** (1./3.)
        else:
            return -(-x) ** (1./3.)

    def K(self):
        return Cubic.cuberoot(self.W_max * self.beta / self.C)

    def next_window_update_time(self, time, cwnd):
        # return time - (((cwnd - self.W_max) / self.C) ** (1.0 / 3.0) + self.K()) + ((cwnd + 1 - self.W_max) / self.C) ** (1.0 / 3.0) + self.K()
        return time - Cubic.cuberoot((cwnd - self.W_max) / self.C) + Cubic.cuberoot((cwnd + 1 - self.W_max) / self.C)

    def dup3_fn(self, timestamp, output):
        return []

    def timeout_fn(self, timestamp, output):
        source = self.source
        source.reset_count += 1
        print('Setting W_max to {}'.format(source.cwnd))
        self.W_max = source.cwnd
        source.cwnd = 1
        # print("Changing cwnd to {} at time={}".format(source.cwnd, timestamp))
        add_cwnd_update(source.cwnd, timestamp)
        creation_events = []

        temp_set = sorted(list(source.queued_packets.union(source.unacked_sent_packets)))
        for packet in temp_set:
            creation_events.append(Event.packet_creation(packet))

        source.unqueued_packets = sorted(creation_events + source.unqueued_packets)
        for packet in source.unqueued_packets:
            packet.reset_count = source.reset_count
        source.queued_packets = set()
        source.unacked_sent_packets = set()
        events = source.enqueue_packets_in_window(timestamp, output)
        events.append(Event.window_update(self.source, self.next_window_update_time(timestamp, self.source.cwnd)))
        return events


    def ack_received(self, num_packets_acked, timestamp):
        return

    def window_update_time(self, timestamp, output):
        self.source.cwnd += 1
        # print("Changing cwnd to {} at time={}".format(self.source.cwnd, timestamp))
        add_cwnd_update(self.source.cwnd, timestamp)
        events = self.source.enqueue_packets_in_window(timestamp, output)
        events.append(Event.window_update(self.source, self.next_window_update_time(timestamp, self.source.cwnd)))
        return events


class Source:
    id_count = 0

    def __init__(self, sending_rate, time_to_switch, congestion_control_type):
        self.id = Source.id_count
        Source.id_count += 1
        self.sending_rate = sending_rate
        self.time_to_switch = time_to_switch
        
        # Track number of timeouts and 3'DUPs (resets)
        self.reset_count = 0
        self.seq_no = -1
        self.dup = 0
        self.last_acked = None

        # Packets that have been created but not queued to be sent
        self.unqueued_packets = []
        self.queued_packets = set()
        self.unacked_sent_packets = set()

        if congestion_control_type == 'aimd':
            self.congestion_control = AIMD(self)
        elif  congestion_control_type == 'cubic':
            self.congestion_control = Cubic(self)
        else:
            print("Unknown congestion control algorithm '{}'. Defaulting to AIMD!".format(congestion_control_type))
            self.congestion_control = AIMD(self)
        self.mark_wire_free()
        
        self.packet_send_time = dict()
        # self.rtt_est = random.randint(0, 99)
        # self.rtt_dev = random.randint(0, 99)
        self.rtt_est = 4
        self.rtt_dev = 0
        self.rtt_alpha = 0.125
        self.rtt_beta = 0.25
        
        self.wnd_start = self.seq_no + 1
        self.cwnd = 1
        print("Starting with cwnd = {}".format(self.cwnd))
        
        self.clock = 0

        return

    def get_timeout_duration(self):
        return self.rtt_est + 4 * self.rtt_dev

    def get_next_packet_time(self):
        u = random.uniform(0., 1.)
        t = -1.0 * math.log(1 - u) / (self.sending_rate)
        return t
    
    def _next_seq_no(self):
        self.seq_no += 1
        return self.seq_no
    
    # Returns the event after creating a packet
    def create_packet(self):
        # increment clock
        self.clock += self.get_next_packet_time()
        packet = Packet(source=self, seq_no=self._next_seq_no(), creation_time=self.clock, reset_count=self.reset_count)
        creation_event = Event.packet_creation(packet)
        self.unqueued_packets.append(creation_event)
        return creation_event
    
    def mark_wire_busy(self, time):
        self._wire_busy = True
        self._wire_busy_till = time

    def mark_wire_free(self):
        self._wire_busy = False
        self._wire_busy_till = None

    def enqueue_packets_in_window(self, timestamp, output=True):
        events = []
        new_unqueued_packets = []
        self.unqueued_packets.sort()
        for creation_event in self.unqueued_packets:
            # if creation_event.packet.seq_no in range(self.wnd_start, self.wnd_start + self.cwnd):
            if self.wnd_start <= creation_event.packet.seq_no < self.wnd_start + self.cwnd + EPSILON:
                events.append(creation_event)
                if timestamp is None or creation_event.timestamp > timestamp:
                    creation_event.update(creation_event.timestamp, progress=True, output=output)
                else:
                    creation_event.update(timestamp, progress=True, output=output)
                self.queued_packets.add(creation_event.packet)
            else:
                new_unqueued_packets.append(creation_event)
        
        self.unqueued_packets = new_unqueued_packets
        return events

    # (Update source's RTT, window, Move window if needed and call congestion control op to change window size if needed)
    def receive_ack(self, packet, time, output):
        events = []

        # If duplicate ack
        if self.last_acked == packet.seq_no and packet.reset_count == self.reset_count:
            self.dup += 1
            if self.dup == 3:
                # Change no. of resets, window size, enqueue packets
                events.extend(self.congestion_control.dup3_fn(time, output))
                self.dup = 0
        else:
            self.dup = 1
            if packet.seq_no > self.wnd_start:
                # Update RTT
                sample_rtt = time - self.packet_send_time[packet.seq_no - 1]
                self.rtt_est, self.rtt_dev = (self.rtt_est * (1 - self.rtt_alpha) + sample_rtt * self.rtt_alpha,
                                            (1 - self.rtt_beta) * self.rtt_dev + self.rtt_beta * abs(sample_rtt - self.rtt_est))

                # Change window size if needed
                self.congestion_control.ack_received(num_packets_acked=(packet.seq_no - self.wnd_start), timestamp=time)

                self.wnd_start = packet.seq_no
                events.extend(self.enqueue_packets_in_window(time, output))

            # Remove all packets from unacked packets with seq_no < packet.seq_no
            for unacked_packet in self.unacked_sent_packets.copy():
                if unacked_packet.seq_no < packet.seq_no:
                    self.unacked_sent_packets.remove(unacked_packet)
        
        self.last_acked = packet.seq_no
        return events
    
    def receive_timeout(self, packet, reset_count, time, output):
        events = []
        # Check if ACK's already been received (before window)
        # Check if timeout is for the correct num_resets
        if reset_count != self.reset_count or packet.seq_no < self.wnd_start:
            print('reset_count (%d) != self.reset_count (%d) or packet.seq_no (%d) < self.wnd_start (%d)' % (reset_count, self.reset_count, packet.seq_no, self.wnd_start))
            return
        # Call congestion control operations to change window size, to update number of resets at the source and enqueue packets
        # Enqueue all packets in window and continue
        print('Calling timeout_fn')
        events.extend(self.congestion_control.timeout_fn(time, output))
        return events
    
    # Call congestion control operations to change window size
    # Enqueue all packets in window and continue
    # Returns the next window update event and the events to enqueue
    def window_update(self, event, time, output):
        if event.num_resets != self.reset_count:
            print("OLD_WINDOW_UPDATE: event.num_resets {} != self.reset_count {}".format(event.num_resets, self.reset_count))
            return []
        events = self.congestion_control.window_update_time(time, output)
        return events
    

class Switch:
    def __init__(self, time_to_sink, max_queue_size_fw, max_queue_size_bw, sources):
        self.time_to_sink = time_to_sink

        self.max_queue_size_fw = max_queue_size_fw
        self.queue_size_fw = 0
        self.max_queue_size_bw = max_queue_size_bw
        self.queue_size_bw = 0
        
        self.mark_wire_free_fw()
        self._wire_busy_bw = dict()
        self._wire_busy_till_bw = dict()
        for s in sources:
            self.mark_wire_free_bw(s.id)
        return
    
    def mark_wire_busy_fw(self, time):
        self._wire_busy_fw = True
        self._wire_busy_till_fw = time
    
    def mark_wire_free_fw(self):
        self._wire_busy_fw = False
        self._wire_busy_till_fw = None

    def mark_wire_busy_bw(self, time, source_id):
        self._wire_busy_bw[source_id] = True
        self._wire_busy_till_bw[source_id] = time
    
    def mark_wire_free_bw(self, source_id):
        self._wire_busy_bw[source_id] = False
        self._wire_busy_till_bw[source_id] = None


class Packet:
    packet_size = None
    id_count = 0
    # seq_no - specific to source
    def __init__(self, source, seq_no, creation_time, reset_count, is_ack=False, empty=False):
        if empty:
            self.id = None
        else:
            self.id = Packet.id_count
            Packet.id_count += 1
        self.seq_no = seq_no
        self.source = source
        self.creation_time = creation_time
        self.is_ack = is_ack
        self.reset_count = reset_count
        return
    
    @classmethod
    def get_ack(cls, packet, time, new_seq_no=None):
        if new_seq_no is None:
            new_seq_no = packet.seq_no
        return Packet(packet.source, new_seq_no, time, packet.reset_count, is_ack=True)
    
    # The lesser is retrieved first in a priority queue
    def __lt__(self, other):
        if (self.seq_no != other.seq_no):
            return self.seq_no < other.seq_no
        elif (self.creation_time != other.creation_time):
            return self.creation_time > other.creation_time
        else:
            return self.id < other.id


class Sink:
    def __init__(self, sources):
        self.packets_received = []
        self.seq_nos_received = set()
        # self.last_acked = {s.id: -1 for s in sources}
        self.expected_seq_no = {s.id: 0 for s in sources}
        # self.rwnd = 100
        self.mark_wire_free()
        return
    
    def mark_wire_busy(self, time):
        self._wire_busy = True
        self._wire_busy_till = time

    def mark_wire_free(self):
        self._wire_busy = False
        self._wire_busy_till = None
    
    def receive_packet(self, packet, time):
        self.seq_nos_received.add(packet.seq_no)
        # Check if it's the expected packet, create an ACK packet with the next expected seq_no
        while self.expected_seq_no[packet.source.id] in self.seq_nos_received:
            self.expected_seq_no[packet.source.id] += 1
        
        return Packet.get_ack(packet, time, new_seq_no=self.expected_seq_no[packet.source.id])

@functools.total_ordering
class Event:
    WINDOW_UPDATE = -3
    TIMEOUT = -2
    DROPPED = -1

    PACKET_CREATED = 0
    QUEUED_AT_SOURCE = 1
    SENT_FROM_SOURCE = 2
    
    QUEUED_AT_SWITCH = 3
    SENT_FROM_SWITCH = 4
    
    ACK_QUEUED_AT_SINK = 5
    ACK_SENT_FROM_SINK = 6
    
    ACK_QUEUED_AT_SWITCH = 7
    ACK_SENT_FROM_SWITCH = 8
    ACK_RECEIVED_AT_SOURCE = 9

    _event_id_count = 0
    
    @staticmethod
    def _next_id():
        Event._event_id_count += 1
        return Event._event_id_count - 1

    # event_str[event_id] should correspond
    event_str = ['PACKET_CREATED', 'QUEUED_AT_SOURCE', 'SENT_FROM_SOURCE', 'QUEUED_AT_SWITCH',
                 'SENT_FROM_SWITCH', 'ACK_QUEUED_AT_SINK', 'ACK_SENT_FROM_SINK', 'ACK_QUEUED_AT_SWITCH',
                 'ACK_SENT_FROM_SWITCH', 'ACK_RECEIVED_AT_SOURCE',
                 'WINDOW_UPDATE', 'TIMEOUT', 'DROPPED']
    
    def __init__(self, packet, event_type, timestamp, num_resets=None):
        self.packet = packet
        self.event_type = event_type
        if DEBUG:
            assert self.event_type in [self.PACKET_CREATED, self.WINDOW_UPDATE, self.TIMEOUT]
        self.timestamp = timestamp
        self.id = self._next_id()
        self.num_resets = num_resets

        # Store whether the packet progressed in the previous event
        self.last_progress = True
        return

    @classmethod
    def packet_creation(cls, packet):
        return Event(packet, Event.PACKET_CREATED, packet.creation_time)
    
    @classmethod
    def packet_timeout(cls, packet, timestamp):
        return Event(packet, Event.TIMEOUT, timestamp, packet.source.reset_count)
    
    @classmethod
    def window_update(cls, source, timestamp):
        packet = Packet(source, seq_no=None, creation_time=timestamp, reset_count=source.reset_count, is_ack=False, empty=True)
        return Event(packet, Event.WINDOW_UPDATE, timestamp, packet.source.reset_count)
    
    def update(self, timestamp, progress, output=True):
        # If same timestamp repeatedly without progress, there's some problem
        if DEBUG:
            assert not (timestamp == self.timestamp and progress == self.last_progress == False)
        
        # Drop
        if progress == 'drop':
            if DEBUG or output:
                print('Time: {}, Packet id: {}, Source id: {}, Seq no.: {}, Event: PACKET_DROPPED'
                .format(self.timestamp, self.packet.id, self.packet.source.id, self.packet.seq_no, Event.event_str[self.event_type], progress))
            self.event_type = self.DROPPED
            self.id = self._next_id()
            return

        if DEBUG or (output and (self.event_type == self.QUEUED_AT_SOURCE or self.event_type==self.ACK_QUEUED_AT_SINK or self.event_type==self.ACK_RECEIVED_AT_SOURCE)):
            print('Time: {}, Packet id: {}, Source id: {}, Seq no.: {}, Event: {}, Progress: {}'
            .format(self.timestamp, self.packet.id, self.packet.source.id, self.packet.seq_no, Event.event_str[self.event_type], progress))

        if isinstance(progress, bool) and progress:
            if self.event_type == Event.TIMEOUT:
                self.event_type = Event.ACK_RECEIVED_AT_SOURCE + 1
            elif  self.event_type == Event.WINDOW_UPDATE:
                self.event_type = Event.ACK_RECEIVED_AT_SOURCE + 1
            else:
                
                self.event_type += 1
            self.id = self._next_id()
        
        self.timestamp = timestamp
        self.last_progress = progress
        return
    
    # The lesser is retrieved first in a priority queue
    def __lt__(self, other):
        if (self.timestamp != other.timestamp):
            return self.timestamp < other.timestamp
        elif (self.event_type != other.event_type):
            return self.event_type > other.event_type
        else:
            return self.id < other.id


class Network:
    def __init__(self, packet_size, sending_rates, src_switch_bandwidths, switch_sink_bandwidth, max_queue_size, congestion_control_type):
        self.sources = []
        for rate, bandwidth in zip(sending_rates, src_switch_bandwidths):
            self.sources.append(Source(sending_rate=rate,
                                        time_to_switch=(packet_size * 1.0 / bandwidth),
                                        congestion_control_type=congestion_control_type))
        
        # process_time = 0 since the link from the input port to the output port has infinite bandwidth
        # self.switch = Switch(time_to_sink=(packet_size * 1.0 / switch_sink_bandwidth), max_queue_size=max_queue_size)
        self.switch = Switch(time_to_sink=(packet_size * 1.0 / switch_sink_bandwidth),
                             max_queue_size_fw=max_queue_size,
                             max_queue_size_bw=max_queue_size,
                             sources=self.sources)
        self.sink = Sink(self.sources)
        self.global_pq = []
        return
    
    def simulate(self, duration, output=True):
        Source.id_count = 0
        Packet.id_count = 0
        Event._event_id_count = 0

        self.global_pq = []
        for source in self.sources:
            while source.clock < duration:
                source.create_packet()
            self.global_pq.extend(source.enqueue_packets_in_window(timestamp=None, output=True))
            if isinstance(source.congestion_control, Cubic):
                self.global_pq.append(Event.window_update(source, source.congestion_control.next_window_update_time(0, source.cwnd)))

        heapq.heapify(self.global_pq)
        
        while len(self.global_pq) > 0:
            event = heapq.heappop(self.global_pq)
            if event.timestamp > duration:
                break
            new_event = self.process_event(event, print_output=output)
            if event.event_type == Event.PACKET_CREATED:
                print()
            if event.event_type <= Event.ACK_RECEIVED_AT_SOURCE and event.event_type != Event.DROPPED:
                heapq.heappush(self.global_pq, event)
            if new_event is not None and isinstance(new_event, Event):
                if new_event.event_type == Event.PACKET_CREATED:
                    print()
                heapq.heappush(self.global_pq, new_event)
            elif isinstance(new_event, list):
                for ev in new_event:
                    if ev.event_type == Event.PACKET_CREATED:
                        print()
                    heapq.heappush(self.global_pq, ev)
        
        # avg_delay, avg_source_delay = self.sink.get_avg_delay()
        # drop_rates = self.get_drop_rates()
        
        return
    
    def process_event(self, event, print_output=True):
        time = event.timestamp
        new_event = None

        if event.event_type == Event.QUEUED_AT_SOURCE:
            source = event.packet.source
            if event.packet not in source.queued_packets:
                event.update(timestamp=time, progress='drop', output=False)
            elif source._wire_busy:
                new_timestamp = source._wire_busy_till
                event.update(new_timestamp, progress=False, output=print_output)
                source.mark_wire_busy(new_timestamp + source.time_to_switch)
            else:
                source.queued_packets.remove(event.packet)
                source.unacked_sent_packets.add(event.packet)

                source.mark_wire_busy(time + source.time_to_switch)
                event.update(timestamp=time, progress=True, output=print_output)
                new_event = Event.packet_timeout(event.packet, time + event.packet.source.get_timeout_duration())
        
        elif event.event_type == Event.SENT_FROM_SOURCE:
            source = event.packet.source
            # if event.packet not in source.queued_packets:
            #     # Drop packet
            #     event.update(timestamp=time, progress='drop', output=False)
            #     # event.packet.source.mark_wire_free()
            # else:
            if True:
                # source.queued_packets.remove(event.packet)
                # source.unacked_sent_packets.add(event.packet)
                event.update(timestamp=time+source.time_to_switch, progress=True, output=print_output)
                # source.mark_wire_free()
        
        # Received at the switch. Drop packet if queue full, else enqueue. Progress event to send if possible.
        elif event.event_type == Event.QUEUED_AT_SWITCH:
            # See if the packet was received at the switch for the first time
            dropped = False
            if event.last_progress:
                event.packet.source.mark_wire_free()
                event.packet.source.packet_send_time[event.packet.seq_no] = time
                # check for overflow in queue
                if self.switch.queue_size_fw == self.switch.max_queue_size_fw:
                    # drop packet
                    event.update(timestamp=time, progress='drop', output=print_output)
                    dropped = True
                    # self.switch.packets_dropped += 1
                    # event.packet.source.num_packets_dropped += 1
                else:
                    self.switch.queue_size_fw += 1
            
            if not dropped:
                if self.switch._wire_busy_fw:
                    new_timestamp = self.switch._wire_busy_till_fw
                    event.update(new_timestamp, progress=False, output=print_output)
                    # self.switch._wire_busy_till = new_timestamp + self.switch.time_to_sink
                    self.switch.mark_wire_busy_fw(new_timestamp + self.switch.time_to_sink)
                else:
                    self.switch.mark_wire_busy_fw(time + self.switch.time_to_sink)
                    event.update(timestamp=time, progress=True, output=print_output)
                    # Pop out from queue
                    self.switch.queue_size_fw -= 1
        
        elif event.event_type == Event.SENT_FROM_SWITCH:
            event.update(timestamp=time+self.switch.time_to_sink, progress=True, output=print_output)
            # self.switch.mark_wire_free()
        
        # Received at the sink. Enqueue ACK. Progress to send if possible.
        elif event.event_type == Event.ACK_QUEUED_AT_SINK:
            if event.last_progress:
                self.switch.mark_wire_free_fw()
                ack_packet = self.sink.receive_packet(event.packet, time)
                event.packet = ack_packet
                self.sink.packets_received.append((event.packet, time))
            
            if self.sink._wire_busy:
                new_timestamp = self.sink._wire_busy_till
                event.update(new_timestamp, progress=False, output=print_output)
                self.sink.mark_wire_busy(new_timestamp + self.switch.time_to_sink)
            else:
                self.sink.mark_wire_busy(time + self.switch.time_to_sink)
                event.update(timestamp=time, progress=True, output=print_output)
        
        elif event.event_type == Event.ACK_SENT_FROM_SINK:
            event.update(timestamp=time+self.switch.time_to_sink, progress=True, output=print_output)
        
        # ACK received at the switch. Enqueue ACK. Progress to send if possible.
        elif event.event_type == Event.ACK_QUEUED_AT_SWITCH:
            # See if the ACK was received at the switch for the first time
            dropped = False
            target_source = event.packet.source
            if event.last_progress:
                self.sink.mark_wire_free()
                # check for overflow in queue
                if self.switch.queue_size_bw == self.switch.max_queue_size_bw:
                    # drop packet
                    event.update(timestamp=time, progress='drop', output=print_output)
                    dropped = True
                else:
                    self.switch.queue_size_bw += 1
            
            if not dropped:
                if self.switch._wire_busy_bw[target_source.id]:
                    new_timestamp = self.switch._wire_busy_till_bw[target_source.id]
                    event.update(new_timestamp, progress=False, output=print_output)
                    # self.switch._wire_busy_till = new_timestamp + self.switch.time_to_sink
                    self.switch.mark_wire_busy_bw(new_timestamp + self.switch.time_to_sink, target_source.id)
                else:
                    self.switch.mark_wire_busy_bw(time + self.switch.time_to_sink, target_source.id)
                    event.update(timestamp=time, progress=True, output=print_output)
                    # Pop out from queue
                    self.switch.queue_size_bw -= 1
        
        elif event.event_type == Event.ACK_SENT_FROM_SWITCH:
            event.update(timestamp=time+event.packet.source.time_to_switch, progress=True, output=print_output)

        elif event.event_type == Event.ACK_RECEIVED_AT_SOURCE:
            source = event.packet.source
            self.switch.mark_wire_free_bw(source.id)
            # Call receive ACK at the source
            # (Update source's RTT, window, Move window if needed and call congestion control op to change window size if needed)
            new_event = source.receive_ack(event.packet, time, print_output)
            event.update(timestamp=time, progress=True, output=print_output)
        
        elif event.event_type == Event.TIMEOUT:
            source = event.packet.source

            # Check if ACK's already been received
            # Check if timeout is for the correct num_resets
            # Update number of resets at the source
            # Call congestion control operations to change window size
            # Enqueue all packets in window and continue
            new_event = source.receive_timeout(event.packet, event.num_resets, time, print_output)

            # Progress current event out
            event.update(timestamp=time, progress=True, output=print_output)
        
        elif event.event_type == Event.WINDOW_UPDATE:
            # Call congestion control operations to change window size
            # Enqueue all packets in window and continue
            # Returns the next window update event and the events to enqueue
            new_event = event.packet.source.window_update(event, time, print_output)
            # Progress current event out
            event.update(timestamp=time, progress=True, output=print_output)
        else:
            if DEBUG:
                print("Illegal process_event call with event_type = {}!".format(Event.event_str[event.event_type]))
        
        return new_event


def get_positive_input(varname, vartype=int):
    print("Enter {}: ".format(varname), end='')
    try:
        a = vartype(input())
        while a <= 0:
            print("Enter positive number!: ")
            a = vartype(input())
    except ValueError as e:
        loopback = print("Invalid %s!" % (type))
        exit(1)
        
    return a


def menu():
    print("NETWORK SPECIFICATIONS")
    packet_size = get_positive_input('packet size (in kb, integer): ', int)
    num_sources = get_positive_input('number of sources', int)
    src_switch_bandwidths = []
    for i in range(num_sources):
        src_switch_bandwidths.append(get_positive_input('bandwidth of source %d to switch (in kb/sec)' % (i+1), float))
    
    switch_sink_bandwidth = get_positive_input('bandwidth of switch to sink (in kb/sec)', float)
    print('Enter max queue size at switch (enter 0 for infinite size): ')
    max_queue_size = int(input())
    # max_queue_size = 0
    if max_queue_size == 0:
        max_queue_size = float('inf')
        
    sending_rates = []
    # if sending_rate_type == 2:
    if True:
        for i in range(num_sources):
            sending_rates.append(get_positive_input('avg. sending rate of source %d (in packets/second)' % (i+1), float))

    duration = get_positive_input('length of simulation (in sec)', float)
    return (packet_size, src_switch_bandwidths, switch_sink_bandwidth, sending_rates, duration, max_queue_size)


def save_plot(xs, ys, xlabel, ylabel, title):
    import matplotlib
    import matplotlib.pyplot as plt
    import datetime
    plt.plot(xs, ys)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.title(title)
    print("Saving plot..")
    plt.savefig(str(datetime.datetime.now()) + '_plot.png')
    plt.close()
    return


def main():
    random.seed(11)
    
    rates = []
    avg_delays = []
    avg_source_delays = dict()
    drop_rates_list = dict()

    # packet_size, src_switch_bandwidths, switch_sink_bandwidth, sending_rates, duration, max_queue_size = menu()

    network = Network(packet_size=1, sending_rates=[10,], src_switch_bandwidths=[1,],
                      switch_sink_bandwidth=1, max_queue_size=1, congestion_control_type='aimd')
    # network = Network(packet_size=1, sending_rates=[10,], src_switch_bandwidths=[5,],
    #                   switch_sink_bandwidth=10, max_queue_size=1, congestion_control_type='aimd')
    # network = Network(packet_size=1, sending_rates=[10,], src_switch_bandwidths=[5,],
    #                   switch_sink_bandwidth=5, max_queue_size=1, congestion_control_type='aimd')
    # network = Network(packet_size=1, sending_rates=[10,], src_switch_bandwidths=[10,],
    #                   switch_sink_bandwidth=5, max_queue_size=1, congestion_control_type='cubic')

    network.simulate(100, output=True)
    # if len(sending_rates) > 0:
    # network = Network(packet_size=packet_size,
    #                     sending_rates=sending_rates,
    #                     src_switch_bandwidths=src_switch_bandwidths,
    #                     switch_sink_bandwidth=switch_sink_bandwidth,
    #                     max_queue_size=max_queue_size)
    # avg_delay, avg_source_delay, drop_rates = network.simulate(duration, True)
    # print("End of simulation. Average delay: %f" % avg_delay)
    save_plot(cwnd_updates[1], cwnd_updates[0], 'time', 'cwnd', 'cwnd vs time')
    
if __name__ == '__main__':
    main()
