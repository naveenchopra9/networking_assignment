#!/usr/bin/python

"""
Start up a Simple topology for CS123 - Base code for creating new topologies
"""

from mininet.net import Mininet
from mininet.node import Controller, RemoteController
from mininet.log import setLogLevel, info
from mininet.cli import CLI
from mininet.topo import Topo
from mininet.util import quietRun
from mininet.moduledeps import pathCheck

from sys import exit
import os.path
from subprocess import Popen, STDOUT, PIPE

IPBASE = '10.3.0.0/16'
ROOTIP = '10.3.0.100/16'
#TOPOCHANGE
IPCONFIG_FILE = './IP_CONFIG_TOPOA'
IP_SETTING={}

class CS123Topo( Topo ):
    "CS 123 Lab 2 Topology"
    
    def __init__( self, *args, **kwargs ):
        Topo.__init__( self, *args, **kwargs )
        #TOPOCHANGE
        servers = [0]*5
        clients = [0]*7
        routers = [0]*2
        servers[0] = self.addHost( 'server1' )
        servers[1] = self.addHost( 'server2' )
        servers[2] = self.addHost( 'server3' )
        servers[3] = self.addHost( 'server4' )
        servers[4] = self.addHost( 'server5' )

        routers[0] = self.addSwitch( 'sw1' )
        routers[1] = self.addSwitch( 'sw2' )
        
        clients[0] = self.addHost('client1')
        clients[1] = self.addHost('client2')
        clients[2] = self.addHost('client3')
        clients[3] = self.addHost('client4')
        clients[4] = self.addHost('client5')
        clients[5] = self.addHost('client6')
        clients[6] = self.addHost('client7')
        for h in servers:
            self.addLink( h, routers[1] )
        for h in clients:
            self.addLink( h, routers[0] )
        self.addLink( routers[0], routers[1])


def starthttp( host ):
    "Start simple Python web server on hosts"
    info( '*** Starting SimpleHTTPServer on host', host, '\n' )
    host.cmd( 'cd ./http_%s/; nohup python2.7 ./webserver.py &' % (host.name) )


def stophttp():
    "Stop simple Python web servers"
    info( '*** Shutting down stale SimpleHTTPServers', 
          quietRun( "pkill -9 -f SimpleHTTPServer" ), '\n' )    
    info( '*** Shutting down stale webservers', 
          quietRun( "pkill -9 -f webserver.py" ), '\n' )    
    
def set_default_route(host):
    info('*** setting default gateway of host %s\n' % host.name)

    #TOPOCHANGE
    if(host.name == 'server1'):
        routerip = IP_SETTING['sw2-eth1']
    elif(host.name == 'server2'):
        routerip = IP_SETTING['sw2-eth2']
    elif(host.name == 'server3'):
        routerip = IP_SETTING['sw2-eth3']
    elif(host.name == 'server4'):
        routerip = IP_SETTING['sw2-eth4']
    elif(host.name == 'server5'):
        routerip = IP_SETTING['sw2-eth5']

    elif(host.name == 'client1'):
        routerip = IP_SETTING['sw1-eth1']
    elif(host.name == 'client2'):
        routerip = IP_SETTING['sw1-eth2']
    elif(host.name == 'client3'):
        routerip = IP_SETTING['sw1-eth3']
    elif(host.name == 'client4'):
        routerip = IP_SETTING['sw1-eth4']
    elif(host.name == 'client5'):
        routerip = IP_SETTING['sw1-eth5']
    elif(host.name == 'client6'):
        routerip = IP_SETTING['sw1-eth6']
    elif(host.name == 'client7'):
        routerip = IP_SETTING['sw1-eth7']

    print host.name, routerip

    # Be careful while you change the following lines. Hard to debug. 
    host.cmd('route add %s/32 dev %s-eth0' % (routerip, host.name))
    host.cmd('route add default gw %s dev %s-eth0' % (routerip, host.name))
    ips = IP_SETTING[host.name].split(".") 
    host.cmd('route del -net %s.0.0.0/8 dev %s-eth0' % (ips[0], host.name))

def get_ip_setting():
    try:
        with open(IPCONFIG_FILE, 'r') as f:
            for line in f:
                if( len(line.split()) == 0):
                  break
                name, ip = line.split()
                print name, ip
                IP_SETTING[name] = ip
            info( '*** Successfully loaded ip settings for hosts\n %s\n' % IP_SETTING)
    except EnvironmentError:
        exit("Couldn't load config file for ip addresses, check whether %s exists" % IPCONFIG_FILE)

def cs123net():
    stophttp()
    "Create a simple network for cs123"
    get_ip_setting()
    topo = CS123Topo()
    info( '*** Creating network\n' )
    net = Mininet( topo=topo, controller=RemoteController, ipBase=IPBASE )
    net.start()

    # TOPOCHANGE
    server1, server2, server3, server4, server5, client1, client2, client3, client4, client5, client6, client7, router1, router2 = net.get( 'server1', 'server2', 'server3', 'server4', 'server5','client1', 'client2', 'client3', 'client4', 'client5', 'client6', 'client7', 'sw1', 'sw2')
    s1intf = server1.defaultIntf()
    s1intf.setIP('%s/8' % IP_SETTING['server1'])
    s2intf = server2.defaultIntf()
    s2intf.setIP('%s/8' % IP_SETTING['server2'])
    s3intf = server3.defaultIntf()
    s3intf.setIP('%s/8' % IP_SETTING['server3'])
    s4intf = server4.defaultIntf()
    s4intf.setIP('%s/8' % IP_SETTING['server4'])
    s5intf = server5.defaultIntf()
    s5intf.setIP('%s/8' % IP_SETTING['server5'])
    
    cl1intf = client1.defaultIntf()
    cl1intf.setIP('%s/8' % IP_SETTING['client1'])
    cl2intf = client2.defaultIntf()
    cl2intf.setIP('%s/8' % IP_SETTING['client2'])
    cl3intf = client3.defaultIntf()
    cl3intf.setIP('%s/8' % IP_SETTING['client3'])
    cl4intf = client4.defaultIntf()
    cl4intf.setIP('%s/8' % IP_SETTING['client4'])
    cl5intf = client5.defaultIntf()
    cl5intf.setIP('%s/8' % IP_SETTING['client5'])
    cl6intf = client6.defaultIntf()
    cl6intf.setIP('%s/8' % IP_SETTING['client6'])
    cl7intf = client7.defaultIntf()
    cl7intf.setIP('%s/8' % IP_SETTING['client7'])

    for host in net.hosts:
        set_default_route(host)

    starthttp( server1 )
    starthttp( server2 )
    starthttp( server3 )
    starthttp( server4 )
    starthttp( server5 )
    
    CLI( net )
    stophttp()
    net.stop()


if __name__ == '__main__':
    setLogLevel( 'info' )
    cs123net()
