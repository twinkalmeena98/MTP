#assuming that we have a graph object where the nodes either indicate an AS or an IXP, simulate the graph on mininet

from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import Node
from mininet.log import setLogLevel, info, warn, output
from mininet.cli import CLI
from mininet.link import TCLink
from mininet.util import waitListening
import sys
sys.path.insert(1, '/home/twinkal/Desktop/mininet/code')
from routerLink import RouterLink
from routerNode import RouterNode
from LevelNode import LevelNode

from artificial_sim import runInit,runRealInit

import json




class LinuxRouter( Node ):
    def config( self, **params ):
        super( LinuxRouter, self).config( **params )
        # Enable forwarding on the router
        self.cmd( 'sysctl net.ipv4.ip_forward=1' )

    def terminate( self ):
        self.cmd( 'sysctl net.ipv4.ip_forward=0' )
        super( LinuxRouter, self ).terminate()

class NetworkTopo( Topo ):

    def build( self, **_opts ):
        
        for rname,rnode in routerDict.items():
            hnum = 0
            if rnode.gw == None:
                router = self.addSwitch( rname,ip = rnode.addr)
            else:
                router = self.addSwitch( rname,ip = rnode.addr ,defaultRoute = "via " + rnode.gw[1][:-3] + " dev " + rnode.gw[0])
            for (host,addr,intfAddr) in rnode.hosts:
                dr = 'via ' + intfAddr[:-3]
                host = self.addHost('h' + host, ip = addr, defaultRoute = dr)
                hosts[host] = [(addr,dr,'eth0')]
                self.addLink(host,router, intfName2 = rname + "-eth" + str(hnum) , params2 = {'ip' : intfAddr})
                hnum += 1

                
        #Adding links to the topology between routers
        for (r1,r2),rlink in linkDict.items():
            print(rlink.intfName1, rlink.intfName2, rlink.ip1,rlink.ip2)
            self.addLink(r1,r2, intfName1 = rlink.intfName1, intfName2 = rlink.intfName2, params1 = {'ip' : rlink.ip1}, params2 = {'ip' : rlink.ip2})
            
def getAddr(ipAddr):
    return ipAddr
    if ipAddr[-3:] == '/31':
        return ipAddr
    addrs = ipAddr.split(".")
    return addrs[0] + "." + addrs[1] + "." + addrs[2] + '.0' + '/24'


routerDict = {}
routingTable = {}
adjListDict = {}
linkDict = {}
hosts = {}
r_node_dict = {}
def initialize(filename,real, p4):
    global routerDict, linkDict, adjListDict, routingTable, r_node_dict
    if real == False:
        routerDict,linkDict, adjListDict,routingTable,r_node_dict = runInit(filename)
    else:
        routerDict,linkDict, adjListDict,routingTable = runRealInit(filename,p4)
def addRoutesNet(net):

    for router,table in routingTable.items():
        r = net[router]
        for entry in table:
            if entry[0] == '-1':
                continue
            r.cmd('ip route add to '+ getAddr(entry[0]) +' via '+ entry[1]+' dev ' + entry[2])
            print(router, 'ip route add to '+ getAddr(entry[0]) +' via '+ entry[1]+' dev ' + entry[2])


topos = { 'mytopo': ( lambda: NetworkTopo() ) }
if __name__ == "__main__":
    setLogLevel( 'info' )
    filename = '/home/twinkal/Desktop/mininet/symmetricGraph.graphml'
    initialize(filename,True,False)
    topo = NetworkTopo()
    # for r,n in r_node_dict.items():
        # print(r,n)

    # print(r_node_dict)
    # print(hosts)
    # y = json.dumps(hosts,indent=4)

    # the result is a JSON string:
    # print(y)
    # with open('hosts.txt', 'w') as outfile:
    #     json.dump(hosts, outfile, indent = 4)
    # for key in routingTable.keys():
    #     with open(key + '-commands.txt', 'w') as outfile:
    #         json.dump(routingTable[key], outfile, indent = 4)
    
    
    # net = Mininet(topo=topo, link=TCLink)
    # addRoutesNet(net)
    # CLI( net )
    # net.stop()