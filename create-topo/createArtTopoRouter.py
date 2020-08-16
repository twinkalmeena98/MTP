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

# from artificial_sim import runInit,runRealInit
from newArtSim import runInit,runRealInit

import json

delay = {1 : '2.5ms', 2 : '2.5ms', 3 : '0.75ms', 41 : '75us' , 42 : '75us', 5 : '5us', 6 : '2.5ms', 7: '2.5ms', 8 : '0.75ms', 9: '5us'}
class LinuxRouter( Node ):
	def config( self, **params ):
		super( LinuxRouter, self).config( **params )
		# Enable forwarding on the router
		self.cmd( 'sysctl net.ipv4.ip_forward=1' )

	def terminate( self ):
		self.cmd( 'sysctl net.ipv4.ip_forward=0' )
		super( LinuxRouter, self ).terminate()

class NetworkTopo( Topo ):

	# def __init__( self ):
	#     Topo.__init__( self )
	#     filename = '/home/twinkal/Desktop/mininet/symmetricGraph.graphml'
	#     initialize(filename)
	#     for rname,rnode in routerDict.items():
	#         # print("rname")
	#         hnum = 0
	#         #number of hosts connected to it has to be 1 at least
	#         #setting the default IP of the router equal to the first host
	#         if rnode.gw == None:
	#             router = self.addNode( rname, cls=LinuxRouter)
	#         else:
	#             router = self.addNode( rname, cls=LinuxRouter, defaultRoute = "via " + rnode.gw[1][:-3] + " dev " + rnode.gw[0])
	#         for (host,addr) in rnode.hosts:
	#             # switch = self.addSwitch('sh' + host)
	#             newAddr = addr[:-4] + '2/24'
	#             dr = 'via ' + newAddr[:-3]
	#             host = self.addHost('h' + host, ip = addr, defaultRoute = dr)
	#             hosts[host] = [(addr,dr,'eth0')]
	#             # self.addLink(host,switch)
	#             self.addLink(host,router, intfName2 = rname + "-eth" + str(hnum) , params2 = {'ip' : newAddr})
	#             #adding link between switch and router
	#             hnum += 1

				
	#     #Adding links to the topology between routers
	#     for (r1,r2),rlink in linkDict.items():
	#         self.addLink(r1,r2, intfName1 = rlink.intfName1, intfName2 = rlink.intfName2, params1 = {'ip' : rlink.ip1}, params2 = {'ip' : rlink.ip2})

	def build( self, **_opts ):
		
		for rname,rnode in routerDict.items():
			hnum = 0
			#number of hosts connected to it has to be 1 at least
			#setting the default IP of the router equal to the first host
			# print(rname, "address", rnode.addr )
			if rnode.gw == None:
				# print("no gateway", rname)
				router = self.addNode( rname, cls=LinuxRouter ,ip = rnode.addr)
			else:
				# print(rname, "defaultRoute", "via " + rnode.gw[1][:-3] + " dev " + rnode.gw[0] )
				router = self.addNode( rname, cls=LinuxRouter ,ip = rnode.addr ,defaultRoute = "via " + rnode.gw[1][:-3] + " dev " + rnode.gw[0])
			for (host,addr,intfAddr) in rnode.hosts:
				# switch = self.addSwitch('sw' + host)
				# newAddr = addr[:-4] + '2/24'
				# dr = 'via ' + newAddr[:-3]
				dr = 'via ' + intfAddr[:-3]
				# dr = 'dev h' + host + '-eth0'
				# h0 route add default gw 200.0.1.1
				# print(dr)
				host = self.addHost('h' + host, ip = addr, defaultRoute = dr)
				hosts[host] = [(addr,dr,'eth0')]
				# self.addLink(host,switch,intfName2 = 'sw' + host + "-eth0")
				self.addLink(host,router, intfName2 = rname + "-eth" + str(hnum) , params2 = {'ip' : intfAddr},
				bw = 20, delay = delay[9])
				# print("hostlink", rname + "-eth" + str(hnum))
				#adding link between switch and router
				hnum += 1

				
		#Adding links to the topology between routers
		for (r1,r2),rlink in linkDict.items():
			# print(rlink.intfName1, rlink.intfName2, rlink.ip1,rlink.ip2)
			self.addLink(r1,r2, intfName1 = rlink.intfName1, intfName2 = rlink.intfName2, params1 = {'ip' : rlink.ip1}, params2 = {'ip' : rlink.ip2},
			bw = 20, delay = delay[rlink.linkType])
			
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
		routerDict,linkDict, adjListDict,routingTable,r_node_dict = runRealInit(filename,p4)
def addRoutesNet(net):

	for router,table in routingTable.items():
		r = net[router]
		for entry in table:
			if entry[0] == '-1':
				continue
			r.cmd('ip route add to '+ getAddr(entry[0]) +' via '+ entry[1]+' dev ' + entry[2])
			# print(router, 'ip route add to '+ getAddr(entry[0]) +' via '+ entry[1]+' dev ' + entry[2])


topos = { 'mytopo': ( lambda: NetworkTopo() ) }
# command
# sudo mn --custom ./code/createArtTopoRouter.py --topo=mytopo
# sudo ./miniedit-2.1.0.7.py ./code/createArtTopoRouter.py --topo=mytopo
if __name__ == "__main__":
	setLogLevel( 'info' )
	filename = '/home/twinkal/Desktop/mininet/network/realAsymmetricGraph.graphml'
	initialize(filename,True,False)
	topo = NetworkTopo()
	# import csv
	# with open('nodeMap.csv', 'w') as file:
	#     writer = csv.writer(file)
	#     # writer.writerow(["SN", "Name", "Contribution"])
	#     # writer.writerow([1, "Linus Torvalds", "Linux Kernel"])
	#     # writer.writerow([2, "Tim Berners-Lee", "World Wide Web"])
	#     # writer.writerow([3, "Guido van Rossum", "Python Programming"])
	#     for r,n in r_node_dict.items():
	#         writer.writerow([r,n])
	#         print(r,n)

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
	
	


	net = Mininet(topo=topo, link=TCLink)
	addRoutesNet(net)


	import time
	import threading

	# h0 = 1.1.1.0
	# h16 = 1.2.1.0
	# h31 = 1.3.1.0
	# h36 = 1.3.2.0
	# h41 = 1.3.3.0
	# h37 = 1.3.2.2
	# h44 = 1.3.4.0
	# h8 = 1.1.1.16
	# h21 = 1.2.2.0

	h0 = net['h0']
	h16 = net['h16']
	h31 = net['h31']
	h36 = net['h36']
	h41 = net['h41']
	h37 = net['h37']
	h44 = net['h44']
	h8 = net['h8']
	h21 = net['h21']

	# h8.cmd('iperf -s -p 5201 -i 0.5 -u > r8_20 &')
	# h44.cmd('iperf -s -p 5201 -i 0.5 -u > r44_20 &')
	# h37.cmd('iperf -s -p 5201 -i 0.5 -u > r37_20 &')
	# h21.cmd('iperf -s -p 5201 -i 0.5 -u > r21_20 &')
	# h41.cmd('iperf -s -p 5201 -i 0.5 -u > r41_20 &')

	# h0.cmd('iperf -c 1.1.1.16 -p 5201 -u -b 20m &')
	# time.sleep(4)
	# h31.cmd('iperf -c 1.3.4.0 -p 5201 -u -b 20m &')
	# time.sleep(4)
	# h31.cmd('iperf -c 1.3.2.2 -p 5201 -u -b 20m &')
	# time.sleep(4)
	# h0.cmd('iperf -c 1.2.2.0 -p 5201 -u -b 20m &')
	# time.sleep(4)
	# h0.cmd('iperf -c 1.3.3.0 -p 5201 -u -b 20m &')


	# h8.cmd('iperf -s -p 5201 -i 0.5 > r8_10t &')
	# h44.cmd('iperf -s -p 5201 -i 0.5 > r44_10t &')
	# h37.cmd('iperf -s -p 5201 -i 0.5 > r37_10t &')
	# h21.cmd('iperf -s -p 5201 -i 0.5 > r21_10t &')
	# h41.cmd('iperf -s -p 5201 -i 0.5 > r41_10t &')

	# h0.cmd('iperf -c 1.1.1.16 -p 5201 &')
	# time.sleep(4)
	# h31.cmd('iperf -c 1.3.4.0 -p 5201 &')
	# time.sleep(4)
	# h31.cmd('iperf -c 1.3.2.2 -p 5201 &')
	# time.sleep(4)
	# h0.cmd('iperf -c 1.2.2.0 -p 5201 &')
	# time.sleep(4)
	# h0.cmd('iperf -c 1.3.3.0 -p 5201 &')

	# h31.cmd('iperf -s -p 5201 -i 0.5 -u > resultsh31_20p &')
	# h41.cmd('iperf -s -p 5201 -i 0.5 -u > resultsh41_20p &')

	# start = [h0,h0,h16,h36,h36,h36]
	# end = ['1.3.1.0','1.3.1.0','1.3.3.0', '1.3.3.0', '1.3.3.0', '1.3.3.0']

	# t1 = threading.Thread(target=h0.cmd, args=('iperf -c 1.3.1.0 -p 5201 -u -b 10m &',))
	# t2 = threading.Thread(target=h0.cmd, args=('iperf -c 1.3.1.0 -p 5201 -u -b 10m &',))
	# t3 = threading.Thread(target=h16.cmd, args=('iperf -c 1.3.3.0 -p 5201 -u -b 10m &',))
	# t4 = threading.Thread(target=h36.cmd, args=('iperf -c 1.3.3.0 -p 5201 -u -b 10m &',))
	# t5 = threading.Thread(target=h36.cmd, args=('iperf -c 1.3.3.0 -p 5201 -u -b 10m &',))
	# t6 = threading.Thread(target=h36.cmd, args=('iperf -c 1.3.3.0 -p 5201 -u -b 10m &',))
	
	# t1.start()
	# t2.start()
	# t3.start()
	# t4.start()
	# t5.start()
	# t6.start()


	# t1.join()
	# t2.join()
	# t3.join()
	# t4.join()
	# t5.join()
	# t6.join()

	# threads = []
	# for i in range(len(start)):
	# 	cmd = 'iperf -c ' + end[i] + '-p 5201 -u -b 20m &'
	# 	t = threading.Thread(target=start[i].cmd, args=(cmd,))
	# 	threads.append(t)

	# for i in range(len(threads)):
	# 	threads[i].start()
	
	# for i in range(len(threads)):
	# 	threads[i].join()


	CLI( net )
	net.stop()