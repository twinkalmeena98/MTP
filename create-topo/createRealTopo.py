#assuming that we have a graph object where the nodes either indicate an AS or an IXP, simulate the graph on mininet

from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import Node
from mininet.log import setLogLevel, info, warn, output
from mininet.cli import CLI
from mininet.link import TCLink
from mininet.util import waitListening

from routerLink import RouterLink
from routerNode import RouterNode


from real_sim import runInit,getDGRouter




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

            # #For default gateway
            # dgr, _, rlink, seq = getDGRouter(rname)#default gateway router
            # if dgr != None:
            #     #do something
            #     if seq == 2:
            #         #i.e. rlink node1 = r1 and rlink node2 = r2
            #         dgrIntfIP = rlink.ip2
            #         dgrIntf = rlink.intfName1
            #     else:
            #         #the rlink node1 = r2 and rlink node2 = r1
            #         dgrIntfIP = rlink.ip1
            #         dgrIntf = rlink.intfName2
                
            hnum = 0
            #number of hosts connected to it has to be 1 at least
            #setting the default IP of the router equal to the first host
            (_,addr0) = rnode.hosts[0]
            rAddr = addr0[:-4] + '2/24'
            if rnode.dg == None:
                router = self.addNode( rname, cls=LinuxRouter, ip = rAddr)
            else:
                dgrIntfIP = rnode.dg[1]
                dgrIntf = rnode.dg[0]
                router = self.addNode( rname, cls=LinuxRouter, ip = rAddr, defaultRoute = "via " + dgrIntfIP[:-3] + " dev " + dgrIntf)
            for (host,addr) in rnode.hosts:
                switch = self.addSwitch('s' + host)
                newAddr = addr[:-4] + '2/24'
                dr = 'via ' + newAddr[:-3]
                host = self.addHost('h' + host, ip = addr, defaultRoute = dr)
                self.addLink(host,switch)
                self.addLink(switch,router, intfName2 = rname + "-eth" + str(hnum) , params2 = {'ip' : newAddr})
                #adding link between switch and router
                hnum += 1
                
        #Adding links to the topology between routers
        for (r1,r2),rlink in linkDict.items():
            self.addLink(r1,r2, intfName1 = rlink.intfName1, intfName2 = rlink.intfName2, params1 = {'ip' : rlink.ip1}, params2 = {'ip' : rlink.ip2})
            
def getAddr(ipAddr):
    addrs = ipAddr.split(".")
    return addrs[0] + "." + addrs[1] + "." + addrs[2] + '.0' + '/24'

def addRoutesNet(net):

    for router,table in routingTable.items():
        r = net[router]
        for entry in table:
            if entry[0] == '-1':
                continue
            r.cmd('ip route add to '+ getAddr(entry[0]) +' via '+ entry[1]+' dev ' + entry[2])
            print(router, 'ip route add to '+ getAddr(entry[0]) +' via '+ entry[1]+' dev ' + entry[2])

routerDict = {}
routingTable = {}
adjListDict = {}
linkDict = {}

def initialize(filename):
    global routerDict, linkDict, adjListDict,routingTable
    routerDict,linkDict, adjListDict,routingTable = runInit(filename)
    


def setupNetwork():
    "Create network and run simple performance test"
    topo = NetworkTopo()

    # Controller for KTR network
    net = Mininet(topo=topo, link=TCLink)
    return net


def connectToRootNS( network, switch, ip, prefixLen, routes ):
    """Connect hosts to root namespace via switch. Starts network.
      network: Mininet() network object
      switch: switch to connect to root namespace
      ip: IP address for root namespace node
      prefixLen: IP address prefix length (e.g. 8, 16, 24)
      routes: host networks to route to"""
    # Create a node in root namespace and link to switch 0
    root = Node( 'root', inNamespace=False )
    intf = TCLink( root, switch ).intf1
    root.setIP( ip, prefixLen, intf )
    # Start network that now includes link to root namespace
    network.start()
    # Add routes from root ns to hosts
    for route in routes:
        root.cmd( 'route add -net ' + route + ' dev ' + str( intf ) )


def sshd( network, cmd='/usr/sbin/sshd', opts='-D' ):
    "Start a network, connect it to root ns, and run sshd on all hosts."
    ip = '10.123.123.1'  # our IP address on host network
    routes = [ '10.0.0.0/8' ]  # host networks to route to
    switch = network.switches[ 0 ]  # switch to use
    connectToRootNS( network, switch, ip, 8, routes )
    for host in network.hosts:
        host.cmd( cmd + ' ' + opts + '&' )
        # print( cmd ,' ' , opts ,'&' )
    info( "*** Waiting for ssh daemons to start\n" )
    # for server in network.hosts:
    #     listening = waitListening( server=server, port=22, timeout=5 )
    #     if listening:
    #         output( "*** You may now ssh into", server.name, "at", server.IP(), '\n' )
    #     else:
    #         warn( "*** Warning: after %s seconds, %s is not listening on port 22"
    #                 % ( 5, server.name ), '\n' )

    info( "\n*** Hosts are running sshd at the following addresses:\n" )
    for host in network.hosts:
        info( host.name, host.IP(), '\n' )
    info( "\n*** Type 'exit' or control-D to shut down network\n" )
    addRoutesNet(network)
    CLI( network )
    for host in network.hosts:
        host.cmd( 'kill %' + cmd )
    network.stop()




if __name__ == "__main__":
    setLogLevel( 'info' )
    filename = '/home/twinkal/Desktop/mininet/firstTestnew.graphml'
    initialize(filename)	
    # sshd( setupNetwork() )
    topo = NetworkTopo()
    net = Mininet(topo=topo, link=TCLink)
    net.start()
    # # r = net['r9']
    # # r.cmd('ip route add '+ "10.0.31.1/24" +' via '+ '101.0.28.1' +' dev ' + 'r9-eth1')
    # # ip route add to 10.0.31.0 via 101.0.28.2 dev r9-eth1
    addRoutesNet(net)
    CLI( net )
    net.stop()
    
    # run()