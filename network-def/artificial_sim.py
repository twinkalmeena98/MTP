#assuming that we have a graph object where the nodes either indicate an AS or an IXP, simulate the graph on mininet

from routerLink import RouterLink
from routerNode import RouterNode
from LevelNode import LevelNode
import sys
sys.path.insert(1, '/home/twinkal/Desktop/mininet/pygraphml-master/pygraphml')

from graphml_parser import GraphMLParser
from graph import Graph
from node import Node as Gnode
from edge import Edge
from attribute import Attribute
from item import Item
import string

#node of level 1, 2 and 3. Not for city level nodes
#levelUpList is a list of pair of interface name and router name that current node is connected to in the upper layer
#Similarly for levelDownList


#Takes graphml file as input that tells about the nodes and links in the artificial network. 
#The artificial network is a hierarchical structure containing nodes at the international, national, state and city level. 
#2 gateway routers from each level connected to routers at the above level.
#nodes at the city act as hubs with route servers and further route servers connected to ASes.


l1curAddr = 0
l2curAddr = 0
l3curAddr = 0
levelName = {1:'international', 2: 'national', 3: 'state', 41: 'city', 42 : 'cityhub', 5: 'subnet'}
levelLinkName = {1: 'level1peer', 2: 'level2peer', 3: 'level3peer', 41: 'level41peer',42: 'level42peer' , 5: 'level1level2', 6: 'level2level3', 7: 'level3level4', 8: 'level41level42', 9: 'level4subnet'}
nextS = 0
nextIntfAddr = [1,1,1,1,1,1,1,1,1]
nextHost = 0
nextAddr = 1
nextAS = 0
nodeDict = {}
r_node_dict = {}
routerDict = {}
linkDict = {}
adjListDict = {}
subnetDict = {}
linkTypeDict = {}
routingTable = {}
realRoutingTable = {}
gateways = []
alphabetKeys = [i for i in range(26)]
alphabetMapping = dict(zip(string.ascii_uppercase,alphabetKeys, ))


def initializeLinkTypeDict():
	linkTypeDict[1] = []
	linkTypeDict[2] = []
	linkTypeDict[3] = []
	linkTypeDict[41] = []
	linkTypeDict[42] = []
	linkTypeDict[5] = []
	linkTypeDict[6] = []
	linkTypeDict[7] = []
	linkTypeDict[8] = []
	linkTypeDict[9] = []


def getIntfAddressPair(linkType):
	if linkType == 41 or linkType == 42:
		linkType = 4
	# print(linkType)
	addr1 = "10" + str(linkType) + "." + str(nextIntfAddr[linkType-1] / 255) + "." + str(nextIntfAddr[linkType-1] % 255) + ".1/24"
	addr2 = "10" + str(linkType) + "." + str(nextIntfAddr[linkType-1] / 255) + "." + str(nextIntfAddr[linkType-1] % 255) + ".2/24"
	nextIntfAddr[linkType-1] += 1
	# print(linkType, nextIntfAddr[linkType-1])
	return (addr1,addr2)

def generateSubnetAddr(hostNum):
	global nextAddr
	addr = "10." + str(nextAddr/255) + "." + str(nextAddr%255) + ".1/24"
	subnetDict['h' + str(hostNum)]  = addr
	nextAddr += 1
	#TODO: Update this function to generate random addresses
	return addr

def generateHostIntfAddr(hostNum):
	global nextAddr
	addr = "200." + str(nextAddr/255) + "." + str(nextAddr%255) + ".1/24"
	subnetDict['h' + str(hostNum)]  = addr
	nextAddr += 1
	#TODO: Update this function to generate random addresses
	return addr

def getUniqueHostAddress(code):
	# code is the real address of the concerned AS
	codeArr = code.split('/')
	address = ''
	intf = ''
	for i in range(3):
		letters = codeArr[i]
		address += str(alphabetMapping[letters[0]]*26 + alphabetMapping[letters[1]] + 1) + '.'
	if len(codeArr) == 3:
		address += '0'
	else:
		num = 2*int(codeArr[-1][2:])
		intfnum = num + 1
		intf = address + str(intfnum)
		address += str(num)
		
	address += '/31'
	intf += '/31'
	return address,intf

def initializeLevels(filename):
	global nextS, nextHost
	graphObj = Graph()
	parser = GraphMLParser()
	graphObj = parser.parse(filename)

	if graphObj == None:
		return -1

	#Adding nodes(at levels) in the dicts
	for node in graphObj.nodes():
		level = int(node.attr['level'].value)
		code = str(node.attr['code'].value)
		nodeID = node.id
		strRouter = 's' + str(nextS)
		nodeDict[nodeID] = strRouter
		r_node_dict[strRouter] = nodeID
		nextS = nextS + 1
		hosts = []
		addr = None
		if level == 5 :
			# Creating only one host for now for an AS
			# addr = generateSubnetAddr(nextHost)
			# intfAddr = generateHostIntfAddr(nextHost)
			# addr = getUniqueHostAddress(code)
			addr,intfAddr = getUniqueHostAddress(code)
			hosts = [(str(nextHost),addr,intfAddr)]
			nextHost += 1
			addr = intfAddr
		
		nextIntfNum = len(hosts)

		#Remember because of the intf name specification, host has to be added to any router while creating mininet topology at first and then any other link
		rnode = LevelNode(nodeID, addr, level, code, None, hosts ,nextIntfNum)
		routerDict[strRouter] = rnode
		adjListDict[strRouter] = []


	initializeLinkTypeDict()

	#Adding links between the nodes tier wise
	for edge in graphObj.edges():
		r1 = nodeDict[edge.node1.id]
		r2 = nodeDict[edge.node2.id]
		rnode1 = routerDict[r1]
		rnode2 = routerDict[r2]
		level1 = rnode1.level
		level2 = rnode2.level

		if level1 == level2 :
			linkType = level1
		elif (level1 == 1 and level2 == 2) or (level2 == 1 and level1 == 2):
			linkType = 5
		elif (level1 == 2 and level2 == 3) or (level2 == 2 and level1 == 3):
			linkType = 6
		elif (level1 == 3 and level2 == 41) or (level2 == 3 and level1 == 41):
			linkType = 7
		elif (level1 == 41 and level2 == 42) or (level2 == 41 and level1 == 42):
			linkType = 8
		elif (level1 == 42 and level2 == 5) or (level2 == 42 and level1 == 5) or (level1 == 41 and level2 == 5) or (level2 == 41 and level1 == 5):
			linkType = 9
		
		intfName1 = r1 + "-" + "eth" + str(rnode1.nextIntfNum)
		rnode1.nextIntfNum += 1
		intfName2 = r2 + "-" + "eth" + str(rnode2.nextIntfNum)
		rnode2.nextIntfNum += 1
		(ip1,ip2) = getIntfAddressPair(linkType)
		# print(r1,r2,intfName1,intfName2,ip1,ip2)
		rlink = RouterLink(r1,r2,intfName1, intfName2, ip1, ip2, linkType)
		# print("intf", intfName1,ip1)
		# print("intf", intfName2,ip2)
		linkDict[(r1,r2)] = rlink
		adjListDict[r1].append(r2)
		adjListDict[r2].append(r1)
		linkTypeDict[linkType].append((r1,r2))
		if level1 == 5:
			rnode1.gw = (intfName1,ip2)
			# print(r1,intfName1,ip2)
			if r2 not in gateways:
				gateways.append(r2)
		elif level2 == 5:
			rnode2.gw = (intfName2,ip1)
			# print(r2,intfName2,ip1)
			if r1 not in gateways:
				gateways.append(r1)
		elif level1 > level2:
			rnode1.gw = (intfName1,ip2)
			# print(r1,intfName1,ip2)
			if r2 not in gateways:
				gateways.append(r2)
		elif level2 > level1:
			rnode2.gw = (intfName2,ip1)
			# print(r2,intfName2,ip1)
			if r1 not in gateways:
				gateways.append(r1)
		

	initRouterAddress()
	initGateway()

def initRouterAddress():
	for (r1,r2),rlink in linkDict.items():
		rnode1 = routerDict[r1]
		rnode2 = routerDict[r2]
		if rnode1.addr == None:
			rnode1.addr = rlink.ip1
		if rnode2.addr == None:
			rnode2.addr = rlink.ip2
        # print(rlink.intfName1, rlink.intfName2, rlink.ip1,rlsink.ip2)
            

def initGateway():
	# print("gateways",gateways)
	for r in gateways:
		rgw = routerDict[r]
		for rAdj in adjListDict[r]:
			try:
				rlink = linkDict[r,rAdj]
			except:
				rlink = linkDict[rAdj,r]
			rnode = routerDict[rAdj]
			if rnode.gw != None:
				continue
			if rnode.level == rgw.level:
				if rlink.r1 == r:
					rnode.gw = (rlink.intfName2, rlink.ip1)
				else:
					rnode.gw = (rlink.intfName1, rlink.ip2)

def populateTable(rname,addresses,rlink):
	for addr in addresses:
		if rlink.r1 == rname:
			routingTable[rname].append((addr,rlink.ip2[:-3],rlink.intfName1))
		else:
			routingTable[rname].append((addr,rlink.ip1[:-3],rlink.intfName2))


def populateRealTable(rname,addresses,rlink):
	for addr in addresses:
		# print(rname, 'populate', addr)
		if rlink.r1 == rname:
			realRoutingTable[rname].append((addr,rlink.ip2[:-3],rlink.intfName1))
		else:
			realRoutingTable[rname].append((addr,rlink.ip1[:-3],rlink.intfName2))
	# print("routing table", routingTable[rname])

def getAddressList(rname):
	addresses = []
	for (addr,_,_) in routingTable[rname]:
		addresses.append(addr)
	return addresses

def getRealAddressList(rname):
	addresses = []
	for (addr,_,_) in realRoutingTable[rname]:
		addresses.append(addr)
	return addresses

def getRealAddressListNew(rname, level, p4):
	addresses = []
	for (addr,_,_) in realRoutingTable[rname]:
		if p4 == True:
			addresses.append(addr)
		else:
			addrArr = addr.split('/')
			newAddr = ''
			for a in addrArr[:-1]:
				newAddr += a
			if level == 1:
				newAddr += '/8'
			elif level == 2:
				newAddr += '/16'
			elif level == 3:
				newAddr += '/24'
			elif level == 41 or level == 42:
				newAddr += '/32'
			addresses.append(newAddr)
	return addresses

def initRouteLink(linkType):
	if linkType == 9:
		for (r1,r2) in linkTypeDict[linkType]:
			rnode1 = routerDict[r1]
			rnode2 = routerDict[r2]
			rlink = linkDict[(r1,r2)]
			if rnode1.level == 5:
				addresses = []
				for (_,addr,intfAddr) in rnode1.hosts:
					# addresses.append(addr[:-4] + '0/24')
					addresses.append(addr)
					# newIntf = addr[:-4] + '2'
					# routingTable[r1].append((addr[:-4] + '0/24', newIntf, r1 + '-eth0'))
					routingTable[r1].append((addr, intfAddr[:-3], r1 + '-eth0'))
					# TODO: change interface name form eth0 to ethi. oh for i'th host
				populateTable(r2,addresses,rlink)
			elif rnode2.level == 5:
				addresses = []
				for (_,addr,intfAddr) in rnode2.hosts:
					# addresses.append(addr[:-4] + '0/24')
					addresses.append(addr)
					# newIntf = addr[:-4] + '2'
					# routingTable[r2].append((addr[:-4] + '0/24', newIntf, r2 + '-eth0'))
					routingTable[r2].append((addr, intfAddr[:-3], r2 + '-eth0'))
				populateTable(r1, addresses, rlink)

	elif linkType == 1 or linkType == 2 or linkType == 3 or linkType == 41 or linkType == 42 or linkType == 8:
		tempAddr = {}
		tempLink = {}
		for (r1,r2) in linkTypeDict[linkType]:
			tempAddr[r1] = []
			tempAddr[r2] = []
			tempLink[r1] = []
			tempLink[r2] = []
		for (r1,r2) in linkTypeDict[linkType]:
			rnode1 = routerDict[r1]
			rnode2 = routerDict[r2]
			rlink = linkDict[(r1,r2)]
			tempAddr[r2].append(getAddressList(r1))
			tempLink[r2].append(rlink)
			tempAddr[r1].append(getAddressList(r2))
			tempLink[r1].append(rlink)

		for r, table in tempAddr.items():
			rlinkTable = tempLink[r]
			# print('r',r)
			for i,addresses in enumerate(table):
				rlink = rlinkTable[i]       
				# print('i',i,len(addresses))     
				populateTable(r,addresses,rlink)
	else:
		# print(linkType, "######################")
		for (r1,r2) in linkTypeDict[linkType]:
			rnode1 = routerDict[r1]
			rnode2 = routerDict[r2]
			rlink = linkDict[(r1,r2)]
			# print(r1,r2)
			if rnode1.level > rnode2.level:
				addresses = getAddressList(r1)
				# print("addresses", addresses)
				populateTable(r2,addresses,rlink)
			else:
				addresses = getAddressList(r2)
				# print("addresses", addresses)
				populateTable(r1, addresses, rlink)


def initRoutingTable():
	for rname in routerDict.keys():
		routingTable[rname] = []

	initRouteLink(9)
	initRouteLink(42)
	initRouteLink(8)
	initRouteLink(41)
	initRouteLink(7)
	initRouteLink(3)
	initRouteLink(6)
	initRouteLink(2)
	initRouteLink(5)
	# initRouteLink(1)
	

def getUniqueAddress(code, level):
	codeArr = code.split('/')
	address = ''
	if level == 1:
		for i in range(level):
			letters = codeArr[i]
			address += str(alphabetMapping[letters[0]]*26 + alphabetMapping[letters[1]] + 1) + '.'
		address += '0.'
		address += '0.'
		address += '0'
		address += '/8'
	elif level == 2:
		for i in range(level):
			letters = codeArr[i]
			address += str(alphabetMapping[letters[0]]*26 + alphabetMapping[letters[1]] + 1) + '.'
		address += '0.'
		address += '0'
		address += '/16'
	elif level == 3:
		for i in range(level):
			letters = codeArr[i]
			address += str(alphabetMapping[letters[0]]*26 + alphabetMapping[letters[1]] + 1) + '.'
		address += '0'
		address += '/24'
	elif level == 41 or level == 42 or level == 5:
		address += getUniqueHostAddress(code)[0]
	return address
	

def initRealRouteLink(linkType, p4 = False):
	if linkType == 9:
		for (r1,r2) in linkTypeDict[linkType]:
			rnode1 = routerDict[r1]
			rnode2 = routerDict[r2]
			rlink = linkDict[(r1,r2)]
			if rnode1.level == 5:
				addresses = []
				if p4 != False:
					addresses.append(rnode1.code)
				else:
					addresses.append(getUniqueAddress(rnode1.code,rnode2.level))
				for (_,addr,intfAddr) in rnode1.hosts:
					# newIntf = addr[:-4] + '2'
					# realRoutingTable[r1].append((addr[:-4] + '0/24', newIntf, r1 + '-eth0'))
					realRoutingTable[r1].append((addr, intfAddr[:-3], r1 + '-eth0'))
					# TODO: change interface name form eth0 to ethi. oh for i'th host
				populateRealTable(r2,addresses,rlink)
			elif rnode2.level == 5:
				addresses = []
				if p4 != False:
					addresses.append(rnode2.code)
				else:
					addresses.append(getUniqueAddress(rnode2.code,rnode1.level))
				for (_,addr,intfAddr) in rnode2.hosts:
					# newIntf = addr[:-4] + '2'
					# realRoutingTable[r2].append((addr[:-4] + '0/24', newIntf, r2 + '-eth0'))
					realRoutingTable[r2].append((addr, intfAddr[:-3], r2 + '-eth0'))
				populateRealTable(r1, addresses, rlink)
	elif linkType == 1 or linkType == 2 or linkType == 3 or linkType == 41 or linkType == 42 or linkType == 8:
		tempAddr = {}
		tempLink = {}
		for (r1,r2) in linkTypeDict[linkType]:
			tempAddr[r1] = []
			tempAddr[r2] = []
			tempLink[r1] = []
			tempLink[r2] = []
		for (r1,r2) in linkTypeDict[linkType]:
			rnode1 = routerDict[r1]
			rnode2 = routerDict[r2]
			rlink = linkDict[(r1,r2)]
			tempAddr[r2].append(getRealAddressList(r1))
			tempLink[r2].append(rlink)
			tempAddr[r1].append(getRealAddressList(r2))
			tempLink[r1].append(rlink)

		for r, table in tempAddr.items():
			rlinkTable = tempLink[r]
			# print('r',r)
			for i,addresses in enumerate(table):
				rlink = rlinkTable[i]       
				# print('i',i,(addresses))     
				populateRealTable(r,addresses,rlink)
	else:
		
		for (r1,r2) in linkTypeDict[linkType]:
			rnode1 = routerDict[r1]
			rnode2 = routerDict[r2]
			rlink = linkDict[(r1,r2)]
			if rnode1.level > rnode2.level:
				if p4 != False:
					addresses = [rnode1.code]
				else:
					addresses = [getUniqueAddress(rnode1.code,rnode2.level)]
				populateRealTable(r2,addresses,rlink)
			else:
				if p4 != False:
					addresses = [rnode2.code]
				else:
					addresses = [getUniqueAddress(rnode2.code,rnode1.level)]
				populateRealTable(r1, addresses, rlink)


def initRealRoutingTable(p4 = False):
	for rname in routerDict.keys():
		realRoutingTable[rname] = []

	initRealRouteLink(9,p4)
	initRealRouteLink(42,p4)
	initRealRouteLink(8,p4)
	initRealRouteLink(41,p4)
	initRealRouteLink(7,p4)
	initRealRouteLink(3,p4)
	initRealRouteLink(6,p4)
	initRealRouteLink(2,p4)
	initRealRouteLink(5,p4)
	# initRouteLink(1,p4)



def runInit(filename):
	initializeLevels(filename)
	initRoutingTable()
	print("nextaddrrrrrrr",nextAddr)
	return routerDict, linkDict, adjListDict,routingTable, r_node_dict

def runRealInit(filename,p4):
	initializeLevels(filename)
	initRealRoutingTable(p4)
	return routerDict, linkDict, adjListDict, realRoutingTable


if __name__ == "__main__":
	filename = '/home/twinkal/Desktop/mininet/symmetricGraph.graphml'
	# runInit(filename)
	runRealInit(filename,False)
	for r,table in realRoutingTable.items():
		rnode = routerDict[r]
		if rnode.level == 41:
			if (r =='s28'):
				print(r,rnode.level,(table))
			# break
	# print(nextIntfAddr)
		# if rnode.level == 5:
		#     print(r,len(table))
		#     print(r,table)
			# break
		# break
	# print(len(adjListDict['s2']))
	# for key,val in linkTypeDict.items():
	#     print(key,val)

	