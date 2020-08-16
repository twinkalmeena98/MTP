import csv
import sys
# insert at 1, 0 is the script path (or '' in REPL)
sys.path.insert(1, '/home/twinkal/Desktop/mininet/pygraphml-master/pygraphml')

from graphml_parser import GraphMLParser
from graph import Graph
from node import Node as Gnode
from edge import Edge
from attribute import Attribute
from item import Item
import string 

dictRegion = {'N' : [], 'S' : [], 'W' : [], 'E' : [], 'M' : [], 'NE' : []}
dictNational = {'R1' : [], 'R2' : [] }
graphObj = None
alldata = []
def readcsv(filename):
	with open(filename) as csv_file:
		csv_reader = csv.reader(csv_file, delimiter=',')
		for row in csv_reader:
			row[1] = int(row[1])
			row[-1] = row[-1].rstrip('\n')
			dictRegion[row[2]].append(row)
			dictNational[row[-1]].append(row)
			alldata.append(row)
		for region, rlist in dictRegion.items():
			rlist.sort(key = lambda x: x[1],reverse=True)
			# print(dictRegion[region])
		for n, nlist in dictNational.items():
			nlist.sort(key = lambda x: x[1],reverse=True)
			# print(dictNational[n])
		alldata.sort(key = lambda x: x[1],reverse=True)


def addNode(nodeid, level ,code):
	n = graphObj.add_node(nodeid)
	n['level'] = level
	n['code'] = code
	# print("adding node", nodeid, level, code)
	return n

def createHub(hub_num, code, hub_r):
	# two ases to a hub router
	asn = 0
	temp = []
	for i in range(hub_r):
		if i  == 0:
			n = addNode(code + '/h' + str(hub_num) + '/hr' + str(i), 41, code)
		else:
			n = addNode(code + '/h' + str(hub_num) + '/hr' + str(i), 42, code)
		for node in temp:
			graphObj.add_edge(node, n)
		temp.append(n)
		for j in range(2):
			n_as = addNode(code + '/h' + str(hub_num) + '/hr' + str(i) + '/as' + str(hub_num*2*hub_r + asn), 5, code + '/AS' + str(hub_num*2*hub_r + asn))
			asn = asn + 1
			graphObj.add_edge(n, n_as)
	return temp[0]

def createCity(code, num_hub, hub_r):
	# code = one + '/' + two + '/' + three
	temp = []
	for i in range(num_hub):
		n = createHub(i,code,hub_r)
		for node in temp:
			graphObj.add_edge(node, n)
		temp.append(n)
	return temp[0]

def createState(nodeList, cityMap):
	temp = []
	for i,code in enumerate(nodeList):
		n = addNode(code + '/s' + str(i),3,code)
		for node  in temp:
			graphObj.add_edge(node,n)
		temp.append(n)

	for i, (node_num, citycode, num_hub) in enumerate(cityMap):
		nstate = temp[node_num]
		ncity = createCity(citycode, num_hub, 2)
		graphObj.add_edge(nstate,ncity)
	return temp[0]

def createNational(nodeList,stateMap):
	temp = []
	for i,code in enumerate(nodeList):
		n = addNode(code + '/n' + str(i),2,code)
		for node  in temp:
			graphObj.add_edge(node,n)
		temp.append(n)

	for i, (node_num, newNodeList, cityMap) in enumerate(stateMap):
		nstate = temp[node_num]
		ncity = createState(newNodeList, cityMap)
		graphObj.add_edge(nstate,ncity)
	return temp[1]


def getCode(r , last):
	if len(r) == 1:
		r += 'R'
	return 'IN/' + r + '/' + last

def getNumStateNodes(state):
	total = sum([row[1] for row in dictRegion[state]])
	# print(state,total)
	if total > 10000000:
		return 4
	elif total > 1000000:
		return 3
	return 2
	# return 5

def getNumCityNodes(city):
	if city > 5000000:
		return 5
	elif city > 500000:
		return 4
	elif city > 50000:
		return 3
	else:
		return 2
	

def createGraph():
	n1 = addNode('IN/WR/MH/i0', 1,'IN/WR/MH' )
	nodeList = []
	nodeList.append(getCode(dictNational['R1'][0][2],dictNational['R1'][0][4]))
	nodeList.append(getCode(dictNational['R2'][0][2],dictNational['R2'][0][4]))
	stateMap = []
	for state,slist in dictRegion.items():
		if state == 'S' or state == 'W' or state == 'M':
			node_num = 1
		else:
			node_num = 0
		stateMap.append([node_num,[], []])
		numStateNodes = getNumStateNodes(state)
		
		for i in range(numStateNodes):
			stateMap[-1][1].append(getCode(state,slist[i][4]))
		
		for i,city in enumerate(slist):
			# print(city[0])
			numCityNodes = getNumCityNodes(city[1])
			new_node_num = i % numStateNodes
			code = getCode(state,city[4])
			stateMap[-1][-1].append([new_node_num, code, numCityNodes])
	
	n2 = createNational(nodeList,stateMap)
	# print(stateMap)
	for map in stateMap:
		print(map)
	graphObj.add_edge(n1,n2)

newDict = {}
	


if __name__ == "__main__":
	filename = "/home/twinkal/Desktop/mininet/regionData.csv"
	parser = GraphMLParser()
	graphObj = Graph()
	readcsv(filename)
	newDict['N'] = dictRegion['N']
	newDict['S'] = dictRegion['S']
	createGraph()
	# TODO: getNumCityNodes()
	fname = "asymmetricGraph.graphml"
	parser = GraphMLParser()
	parser.write(graphObj, fname)
	for state,slist in dictRegion.items():
		print(state, len(slist))
