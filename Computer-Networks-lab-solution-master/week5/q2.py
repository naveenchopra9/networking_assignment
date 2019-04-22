#!/usr/bin/python


from mininet.link import TCLink
from mininet.net import Mininet
from mininet.node import CPULimitedHost
from mininet.node import OVSController
from mininet.topo import Topo
from mininet.util import dumpNodeConnections


class SingleSwitchTopo(Topo):
    "Single switch connected to n hosts."

    def build(self):

        s = self.addSwitch('s1')

        t = self.addSwitch('t1')

        a = self.addHost('a')

        b = self.addHost('b')

        c = self.addHost('c')

        d = self.addHost('d')

        e = self.addHost('e')

        u = self.addHost('u')

        self.addLink(a, s, bw=5, delay='3ms', loss=2, max_queue_size=300)

        self.addLink(b, s, bw=5, delay='3ms', loss=2, max_queue_size=300)

        self.addLink(e, s, bw=5, delay='3ms', loss=2, max_queue_size=300)

        self.addLink(c, t, bw=5, delay='3ms', loss=2, max_queue_size=300)

        self.addLink(d, t, bw=5, delay='3ms', loss=2, max_queue_size=300)

        self.addLink(u, t, bw=5, delay='3ms', loss=2, max_queue_size=300)

        self.addLink(t, s, bw=15, delay='2ms')


topo = SingleSwitchTopo()

net = Mininet(topo, controller=OVSController,
              host=CPULimitedHost, link=TCLink, autoStaticArp=True)

# setLogLevel('info')

net.start()

print("Dumping connections")

dumpNodeConnections(net.hosts)

net.pingAll()

net.stop()
