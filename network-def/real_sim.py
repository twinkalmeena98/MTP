#assuming that we have a graph object where the nodes either indicate an AS or an IXP, simulate the graph on mininet

from routerLink import RouterLink
from routerNode import RouterNode
import sys
# insert at 1, 0 is the script path (or '' in REPL)
sys.path.insert(1, '/home/twinkal/Desktop/mininet/pygraphml-master/pygraphml')

from graphml_parser import GraphMLParser
from graph import Graph
from node import Node as Gnode
from edge import Edge
from attribute import Attribute
from item import Item


nodeDict = {}
router2node = {}
routerDict = {}
intfPrefix = "100.1"
intfDict = {}
intfIP = {}
curIntf = 1
curPrefix = 1

peersRoutes = {}
routingTable = {}
nextAddr = 1
nextIntfAddr = 1
subnetDict = {}
adjListDict = {}
tierDict = {}
tierLinkName = {'1': 'tier1peer', '2': 'tier2peer', '3': 'tier3peer', '4': 'tier2tier1', '5': 'tier3tier2', '6': 'tier3tier1'}
linkDict = {}
tier2peer = {}
tier3peer = {}
tier2tier1 = {}
tier3tier2 = {}
tier3tier1 = {}
routerIntfNum = {}
routerAddr = {}
addrPrefix = "100.0"
curAddr = 1
linkTypeDict = {}
routerNodeDict = {}

def ip(prefix,subnet,host,mask=None):
    addr = str(prefix) + '.0.'+str(subnet)+'.' + str(host)
    if mask != None: addr = addr + '/' + str(mask)
    return addr

def generateSubnetAddr(hostNum):
	global nextAddr
	addr = "10.0." + str(nextAddr) + ".1/24"
	subnetDict['h' + str(hostNum)]  = addr
	nextAddr += 1
	#TODO: Update this function to generate random addresses
	return addr

def getIntfAddressPair():
	global nextIntfAddr
	addr1 = "101." + str(nextIntfAddr / 255) + "." + str(nextIntfAddr) + ".1/24"
	addr2 = "101." + str(nextIntfAddr / 255) + "." + str(nextIntfAddr) + ".2/24"
	nextIntfAddr += 1
	return (addr1,addr2)

def getDGRouter(rname):
	seq = 2
	for r in adjListDict[rname]:
		try:
			rlink = linkDict[rname,r]
			rnode2 = routerDict[rlink.r2]
			rnode1 = routerDict[rlink.r1]
			seq = 2
		except:
			rlink = linkDict[r,rname]
			rnode2 = routerDict[rlink.r1]
			rnode1 = routerDict[rlink.r2]
			seq = 1
		if rlink.linkType >= 4 and (rnode1.tierType > rnode2.tierType):
			return r, rnode2, rlink, seq
	return None,None,None,None

def getAddressList(rname):
	addresses = []
	for (addr,_,_) in routingTable[rname]:
		addresses.append(addr)
	return addresses


def populateTable(rname,addresses,rlink):

	for addr in addresses:
		if addr in getAddressList(rname):
			continue
		if rlink.r1 == rname:
			routingTable[rname].append((addr,rlink.ip2[:-3],rlink.intfName1))
		else:
			routingTable[rname].append((addr,rlink.ip1[:-3],rlink.intfName2))

def initHostRoute():
	for r,rnode in routerDict.items():
		routingTable[r] = []
		for _,addr in rnode.hosts:
			routingTable[r].append((addr,'-1','-1'))


def initRouteLink(linkType):
	if linkType == 1 or linkType == 2 or linkType == 3:
		# merge the routing tables of both the nodes of all such links
		tempAddr = {}
		tempLink = {}
		for (r1,r2) in linkTypeDict[linkType]:
			tempAddr[r1] = []
			tempAddr[r2] = []
			tempLink[r1] = []
			tempLink[r2] = []
		for (r1,r2) in linkTypeDict[linkType]:
			rlink = linkDict[(r1,r2)]
			tempAddr[r2].append(getAddressList(r1))
			tempLink[r2].append(rlink)
			tempAddr[r1].append(getAddressList(r2))
			tempLink[r1].append(rlink)

		for r, table in tempAddr.items():
			rlinkTable = tempLink[r]
			for i,addresses in enumerate(table):
				rlink = rlinkTable[i]
				populateTable(r,addresses,rlink)

	elif linkType == 4 or linkType == 5 or linkType == 6:
		for (r1,r2) in linkTypeDict[linkType]:
			rnode1 = routerDict[r1]
			rnode2 = routerDict[r2]
			rlink = linkDict[(r1,r2)]
			if rnode1.tierType > rnode2.tierType:
				addresses = getAddressList(r1)
				populateTable(r2,addresses,rlink)
			else:
				addresses = getAddressList(r2)
				populateTable(r1, addresses, rlink)



def initRoutingTable():
	initHostRoute()

	
	initRouteLink(5)
	initRouteLink(6)
	initRouteLink(4)
	initRouteLink(3)
	initRouteLink(2)
	initRouteLink(1)


def mergeTable(rname,r):
	toAdd1 = []
	toAdd2 = []
	try:
		rlink = linkDict[rname,r]
		for (addr,_,_) in routingTable[r]:
			toAdd1.append((addr,rlink.ip2[:-3],rlink.intfName1))
		for (addr,_,_) in routingTable[rname]:
			toAdd2.append((addr,rlink.ip1[:-3],rlink.intfName2))
	except:
		rlink = linkDict[r,rname]
		for (addr,_,_) in routingTable[r]:
			toAdd1.append((addr,rlink.ip1[:-3],rlink.intfName2))
		for (addr,_,_) in routingTable[rname]:
			toAdd2.append((addr,rlink.ip2[:-3],rlink.intfName1))
	peersRoutes[rname].extend(toAdd1)
	peersRoutes[r].extend(toAdd2)

def traverse(rname):
	retVal = []
	rnode = routerDict[rname]
	for r in adjListDict[rname]:
		curnode = routerDict[r]
		if curnode.tierType > rnode.tierType:
			val = []
			val = traverse(r)
			for (_,addr) in curnode.hosts:
				val.append(addr[:-4] + '0/24')
			try:
				rlink = linkDict[rname,r]
			except:
				rlink = linkDict[r,rname]
			populateTable(rname,val,rlink)
			retVal.extend(val)
	return retVal

# def initRoutingTable():
# 	for rname in routerDict.keys():
# 		routingTable[rname] = []

# 	#Add transit - customer routes
# 	for rname,rnode in routerDict.items():
# 		if rnode.tierType == 1:
# 			traverse(rname)
# 			#dfs kind of
	
# 	for rname,rnode in routerDict.items():
# 		peersRoutes[rname] = []
# 	#Add peer routes
# 	#TODO:check if peer routes are getting added correctly
# 	for (r1,r2) in linkDict.keys():
# 		rnode1 = routerDict[r1]
# 		rnode2 = routerDict[r2]
# 		if rnode1.tierType == rnode2.tierType:
# 				mergeTable(r1,r2)
# 	for rname, table in peersRoutes.items():
# 		routingTable[rname].extend(table)

def initLinkDictType():
	for i in range(1,7):
		linkTypeDict[i] = []

def initializeTiers(graphfile):
	global curAddr
	graphObj = Graph()
	parser = GraphMLParser()
	graphObj = parser.parse(graphfile)

	if graphObj == None:
		return -1
	r = 0
	h = 0

	#Adding nodes(ASes and IXPs) in the dicts
	for node in graphObj.nodes():
		tierType = int(node.attr['tier'].value)
		nodeID = node.id
		strRouter = 'r' + str(r)
		nodeDict[nodeID] = strRouter
		routerNodeDict[strRouter] = nodeID
		addr = generateSubnetAddr(h)
		hosts = [(str(h),addr)] #TODO: to take the number of hosts in a router as input from the graph
		h = h + 1
		nextIntfNum = len(hosts)
		address = addrPrefix + "." + str(curAddr) + ".1/24"
		prefix = addrPrefix + "." + str(curAddr)
		curAddr += 1
		r = r + 1
		rnode = RouterNode(nodeID, address, prefix, hosts, tierType,None, nextIntfNum)	
		routerDict[strRouter] = rnode
		adjListDict[strRouter] = []

	initLinkDictType()
	#Adding links between the nodes tier wise
	for edge in graphObj.edges():
		r1 = nodeDict[edge.node1.id]
		r2 = nodeDict[edge.node2.id]
		if (r1,r2) in linkDict.keys() or (r2,r1) in linkDict.keys():
			continue
		rnode1 = routerDict[r1]
		rnode2 = routerDict[r2]
		tierType1 = rnode1.tierType
		tierType2 = rnode2.tierType
		linkType = 0
		if tierType1 == tierType2:
			# linkDict[(r1,r2)] = tierType1
			linkType = tierType1
		else:
			if tierType1 == 1 and tierType2 == 2:
				# linkDict[(r2,r1)] = 4
				linkType = 4
			elif tierType1 == 2 and tierType2 == 1:
				# linkDict[(r1,r2)] = 4
				linkType = 4
			elif tierType1 == 2 and tierType2 == 3:
				# linkDict[(r2,r1)] = 5
				linkType = 5
			elif tierType1 == 3 and tierType2 == 2:
				# linkDict[(r1,r2)] = 5
				linkType = 5
			elif tierType1 == 1 and tierType2 == 3:
				# linkDict[(r2,r1)] = 6
				linkType = 6
			elif tierType1 == 3 and tierType2 == 1:
				# linkDict[(r1,r2)] = 6
				linkType = 6

		intfName1 = r1 + "-" + "eth" + str(rnode1.nextIntfNum)
		rnode1.nextIntfNum += 1
		intfName2 = r2 + "-" + "eth" + str(rnode2.nextIntfNum)
		rnode2.nextIntfNum += 1
		(ip1,ip2) = getIntfAddressPair()
		rlink = RouterLink(r1,r2,intfName1, intfName2, ip1, ip2, linkType)
		if (tierType1 - 1) == tierType2:
			if rnode1.dg == None:
				rnode1.dg = (intfName1,ip2)
		elif (tierType2 - 1) == tierType1:
			if rnode2.dg == None:
				rnode2.dg = (intfName2,ip1)
		# print("link", r1, r2, intfName1, intfName2, ip1, ip2, linkType)
		linkDict[(r1,r2)] = rlink
		adjListDict[r1].append(r2)
		adjListDict[r2].append(r1)
		linkTypeDict[linkType].append((r1,r2))
	initRoutingTable()

def runInit(filename):
	initializeTiers(filename)
	# print(routingTable)
	# for rname,table in routingTable.items():
	# 	print ("node ", rname)#, table)
	# 	for entry in table:
	# 		print('\t' + str(entry))
	return routerDict, linkDict, adjListDict, routingTable


if __name__ == "__main__":
	
	
	filename = '/home/twinkal/Desktop/mininet/firstTestnew.graphml'
	

	initializeTiers(filename)
	
	# for r1,adjList in adjListDict.items():
	# 	rnode1 = routerDict[r1]
	# 	if rnode1.tierType == 3:
	# 		for r2 in adjList:
	# 			rnode2 = routerDict[r2]
	# 			if rnode2.tierType == 1:
	# 				print(r1,r2)

	# print(peersRoutes)
	for rname,table in routingTable.items():
		rnode = routerDict[rname]
		if rnode.tierType == 2:
			print ("node ", rname, routerNodeDict[rname], (table))
			# break
		# for entry in table:
		# 	print('\t' + str(entry))

	