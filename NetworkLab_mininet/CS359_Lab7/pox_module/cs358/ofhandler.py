# Copyright 2011 James McCauley
#
# This file is part of POX.
#
# POX is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# POX is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with POX.  If not, see <http://www.gnu.org/licenses/>.

"""
This is an L2 learning switch written directly against the OpenFlow library.
"""

from pox.core import core
import pox.openflow.libopenflow_01 as of
from pox.lib.revent import *
from pox.lib.util import dpidToStr
from pox.lib.util import str_to_bool
from pox.lib.packet.ethernet import ethernet
from pox.lib.packet.ipv4 import ipv4
import pox.lib.packet.icmp as icmp
from pox.lib.packet.arp import arp
from pox.lib.packet.udp import udp
from pox.lib.packet.dns import dns
from pox.lib.addresses import IPAddr, EthAddr


import time
import code
import os
import struct
import sys

log = core.getLogger()
FLOOD_DELAY = 5
#TOPOCHANGE
IPCONFIG_FILE = 'IP_CONFIG_TOPOA'
IP_SETTING={}
RTABLE = {}
VHOST_RTABLE = {}
VHOST_HW = {}
ROUTER_IP_DICT = {}

class RouterInfo(Event):
  '''Event to raise upon the information about an openflow router is ready'''

  def __init__(self, info, rtable, vhost):
    Event.__init__(self)
    self.info = info
    self.rtable = rtable
    self.vhost = vhost


class OFHandler (EventMixin):
  def __init__ (self, connection, transparent):
    self.connection = connection
    self.transparent = transparent
    self.sw_info = {}
    self.connection.send(of.ofp_set_config(miss_send_len = 65535))
    # Vhost Demuxer
    self.vhost_id = ''
    for port in connection.features.ports:
        intf_name = port.name.split('-')
        if(len(intf_name) < 2):
          continue
        else:
          self.vhost_id = intf_name[0] #get the first part of vhost1-eth0 
          intf_name = intf_name[1]
        if self.vhost_id not in self.sw_info.keys():
          self.sw_info[self.vhost_id] = {}
        #if intf_name in VHOST_HW[self.vhost_id].keys():
        self.sw_info[self.vhost_id][intf_name] = (ROUTER_IP_DICT[self.vhost_id][intf_name], port.hw_addr.toStr(), '10Gbps', port.port_no)
        print self.sw_info
        
    self.rtable = RTABLE
    # We want to hear Openflow PacketIn messages, so we listen
    self.listenTo(connection)
    self.listenTo(core.cs123_srhandler)
    core.cs123_ofhandler.raiseEvent(RouterInfo(self.sw_info[self.vhost_id], self.rtable[self.vhost_id], self.vhost_id))

  def _handle_PacketIn (self, event):
    """
    Handles packet in messages from the switch to implement above algorithm.
    """
    vhost = "sw%s" % event.dpid
    pkt = event.parse()
    raw_packet = pkt.raw
    core.cs123_ofhandler.raiseEvent(SRPacketIn(raw_packet, event.port, vhost))
    msg = of.ofp_packet_out()
    msg.buffer_id = event.ofp.buffer_id
    msg.in_port = event.port
    self.connection.send(msg)


  def _handle_SRPacketOut(self, event):
    if event.vhost == self.vhost_id:
        msg = of.ofp_packet_out()
        new_packet = event.pkt
        msg.actions.append(of.ofp_action_output(port=event.port))
        msg.buffer_id = -1
        msg.in_port = of.OFPP_NONE
        msg.data = new_packet
        self.connection.send(msg)

class SRPacketIn(Event):
  '''Event to raise upon a receive a packet_in from openflow'''

  def __init__(self, packet, port, vhost):
    Event.__init__(self)
    self.pkt = packet
    self.port = port
    self.vhost = vhost

class cs123_ofhandler (EventMixin):
  """
  Waits for OpenFlow switches to connect and makes them learning switches.
  """
  _eventMixin_events = set([SRPacketIn, RouterInfo])

  def __init__ (self, transparent):
    EventMixin.__init__(self)
    self.listenTo(core.openflow)
    self.transparent = transparent

  def _handle_ConnectionUp (self, event):
    log.debug("Connection %s" % (event.connection,))
    OFHandler(event.connection, self.transparent)


def get_ip_setting():
  if (not os.path.isfile(IPCONFIG_FILE)):
    return -1
  f = open(IPCONFIG_FILE, 'r')
  for line in f:
    if(len(line.split()) == 0):
      break
    name, ip = line.split()
    if ip == "<ELASTIC_IP>":
      log.info("ip configuration is not set, please put your Elastic IP addresses into %s" % IPCONFIG_FILE)
      sys.exit(2)
    #print name, ip
    IP_SETTING[name] = ip

  #TOPOCHANGE
  RTABLE['sw1'] = []
  RTABLE['sw1'].append( ('%s' % IP_SETTING['client1'], '%s' % IP_SETTING['client1'], '255.255.255.255', 'eth1') )
  RTABLE['sw1'].append( ('%s' % IP_SETTING['client2'], '%s' % IP_SETTING['client2'], '255.255.255.255', 'eth2') )
  RTABLE['sw1'].append( ('%s' % IP_SETTING['client3'], '%s' % IP_SETTING['client3'], '255.255.255.255', 'eth3') )
  RTABLE['sw1'].append( ('%s' % IP_SETTING['client4'], '%s' % IP_SETTING['client4'], '255.255.255.255', 'eth4') )
  RTABLE['sw1'].append( ('%s' % IP_SETTING['client5'], '%s' % IP_SETTING['client5'], '255.255.255.255', 'eth5') )
  RTABLE['sw1'].append( ('%s' % IP_SETTING['client6'], '%s' % IP_SETTING['client6'], '255.255.255.255', 'eth6') )
  RTABLE['sw1'].append( ('%s' % IP_SETTING['client7'], '%s' % IP_SETTING['client7'], '255.255.255.255', 'eth7') )
  RTABLE['sw1'].append( ('0.0.0.0', '20.0.0.2', '0.0.0.0', 'eth8') ) # The all-powerful default

  RTABLE['sw2'] = []
  RTABLE['sw2'].append( ('%s' % IP_SETTING['server1'], '%s' % IP_SETTING['server1'], '255.255.255.255', 'eth1') )
  RTABLE['sw2'].append( ('%s' % IP_SETTING['server2'], '%s' % IP_SETTING['server2'], '255.255.255.255', 'eth2') )
  RTABLE['sw2'].append( ('%s' % IP_SETTING['server3'], '%s' % IP_SETTING['server3'], '255.255.255.255', 'eth3') )
  RTABLE['sw2'].append( ('%s' % IP_SETTING['server4'], '%s' % IP_SETTING['server4'], '255.255.255.255', 'eth4') )
  RTABLE['sw2'].append( ('%s' % IP_SETTING['server5'], '%s' % IP_SETTING['server5'], '255.255.255.255', 'eth5') )
  RTABLE['sw2'].append( ('0.0.0.0', '20.0.0.1', '0.0.0.0', 'eth6') )

  # TOPOCHANGE - For Router sw1
  ROUTER_IP = {}
  ROUTER_IP['eth1'] = '%s' % IP_SETTING['sw1-eth1']
  ROUTER_IP['eth2'] = '%s' % IP_SETTING['sw1-eth2']
  ROUTER_IP['eth3'] = '%s' % IP_SETTING['sw1-eth3']
  ROUTER_IP['eth4'] = '%s' % IP_SETTING['sw1-eth4']
  ROUTER_IP['eth5'] = '%s' % IP_SETTING['sw1-eth5']
  ROUTER_IP['eth6'] = '%s' % IP_SETTING['sw1-eth6']
  ROUTER_IP['eth7'] = '%s' % IP_SETTING['sw1-eth7']
  ROUTER_IP['eth8'] = '%s' % IP_SETTING['sw1-eth8']
  ROUTER_IP_DICT['sw1'] = ROUTER_IP

  # TOPOCHANGE - For Router sw2
  ROUTER_IP = {}
  ROUTER_IP['eth1'] = '%s' % IP_SETTING['sw2-eth1']
  ROUTER_IP['eth2'] = '%s' % IP_SETTING['sw2-eth2']
  ROUTER_IP['eth3'] = '%s' % IP_SETTING['sw2-eth3']
  ROUTER_IP['eth4'] = '%s' % IP_SETTING['sw2-eth4']
  ROUTER_IP['eth5'] = '%s' % IP_SETTING['sw2-eth5']
  ROUTER_IP['eth6'] = '%s' % IP_SETTING['sw2-eth6']
  ROUTER_IP_DICT['sw2'] = ROUTER_IP

  return 0


def launch (transparent=False):
  """
  Starts an Simple Router Topology
  """    
  core.registerNew(cs123_ofhandler, str_to_bool(transparent))
  
  r = get_ip_setting()
  if r == -1:
    log.debug("Couldn't load config file for ip addresses, check whether %s exists" % IPCONFIG_FILE)
    sys.exit(2)
  else:
    log.debug('*** ofhandler: Successfully loaded ip settings for hosts\n %s\n' % IP_SETTING)
