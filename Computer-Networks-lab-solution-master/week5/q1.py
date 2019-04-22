#!/usr/bin/python

import threading

from mininet.net import Mininet
from mininet.node import OVSController
from mininet.topo import Topo


class SingleSwitchTopo(Topo):
    "Single switch connected to n hosts."

    def build(self, n=2):
        switch = self.addSwitch('s1')
        for h in range(n):
            host = self.addHost('h%s' % (h + 1))
            self.addLink(host, switch)


def server():
    global h1
    print(h1.IP())
    print(h1.cmd('iperf -s - D -i 2 -p 5111 > log.txt'))


topo = SingleSwitchTopo(2)
net = Mininet(topo, controller=OVSController)
net.start()
h1 = net.get('h1')
h2 = net.get('h2')
a = threading.Thread(target=server)
a.setDaemon(True)
a.start()
cmd_h2 = "iperf -p 5111 -t 20 -c " + h1.IP()
h2.cmd(cmd_h2)
# net.stop()

# topos = {'x':  (lambda: SingleSwitchTopo(2))}
