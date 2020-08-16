#assuming that we have a graph object where the nodes either indicate an AS or an IXP, simulate the graph on mininet

import sys
# insert at 1, 0 is the script path (or '' in REPL)
sys.path.insert(1, '/home/twinkal/Desktop/mininet/pygraphml-master/pygraphml')

from graphml_parser import GraphMLParser
from graph import Graph
from node import Node as Gnode
from edge import Edge
from attribute import Attribute
from item import Item
import random
# print("Random integer is", random.randint(0, 9))
graphObj = None
tier1Nodes = {}
tier2Nodes = {}
tier3Nodes = {}

def createTier(tier, numTier):
	if tier == 1:
		for i in range(numTier):
			n = graphObj.add_node("t1_"+str(i))
			n['tier'] = '1'
			tier1Nodes["t1_"+str(i)] = n
	elif tier ==2:
		for i in range(numTier):
			n = graphObj.add_node("t2_"+str(i))
			n['tier'] = '2'
			tier2Nodes["t2_"+str(i)] = n
	elif tier == 3:
		for i in range(numTier):
			n = graphObj.add_node("t3_"+str(i))
			n['tier'] = '3'
			tier3Nodes["t3_"+str(i)] = n


def createLinks(tier1, tier2, ratio = 0.5):
	# for each tier1 node, connect it to ratio based number of tier 2 nodes.
	# ratio = 0.5 means each tier 1 node connects to numTier2*0.5 number of nodes
	t1NodeList = []
	t2NodeList = []
	print(tier1,tier2,ratio)

	
	if ratio == 0.0:
		return 

	if tier1 == 1:
		t1NodeList = tier1Nodes.values()
	elif tier1 == 2:
		t1NodeList = tier2Nodes.values()
	elif tier1 == 3:
		t1NodeList = tier3Nodes.values()
	
	if tier2 == 1:
		t2NodeList = tier1Nodes.values()
	elif tier2 == 2:
		t2NodeList = tier2Nodes.values()
	elif tier2 == 3:
		t2NodeList = tier3Nodes.values()



	total1 = len(t1NodeList)
	total2 = len(t2NodeList)
	numRatio = max(1,int(total1*ratio))

	if ratio == 1.0:
		for i in range(total1):
			n1 = t1NodeList[i]
			for j in range(i + 1,total2):
				n2 = t2NodeList[j]
				graphObj.add_edge(n1,n2)
		return

	mapping = {}
	if tier1 != tier2:
		for i2 in range(total2):
			i1 = random.randint(0, total1-1)
			n2 = t2NodeList[i2]
			n1 = t1NodeList[i1]
			graphObj.add_edge(n1,n2)
			mapping[i2] = i1
		numRatio = numRatio - 1
	print("numratio", numRatio)
	for i1 in range(total1):
		ix1 = i1
		temp = [ix1]
		for i2 in range(numRatio):
			ix2 = random.randint(0, total2-1)
			if tier1 != tier2:
				while ix2 in temp or ix1 != mapping[ix2]:
					ix2 = random.randint(0, total2-1)
			else:
				while ix2 in temp:
					ix2 = random.randint(0, total2-1)
			temp.append(ix2)
			n1 = t1NodeList[ix1]
			n2 = t2NodeList[ix2]
			graphObj.add_edge(n1,n2)


def initGraph(numTier1, numTier2, numTier3, t1ratio, t2ratio, t3ratio, t1t2ratio, t1t3ratio, t2t3ratio):
	createTier(1,numTier1)
	createTier(2,numTier2)
	createTier(3,numTier3)
	createLinks(1,1,t1ratio)
	createLinks(2,2,t2ratio)
	createLinks(3,3,t3ratio)
	createLinks(1,2,t1t2ratio)
	createLinks(1,3,t1t3ratio)
	# createLinks(2,3,t2t3ratio)
	# Not working properly

if __name__ == "__main__":
	

	parser = GraphMLParser()
	graphObj = Graph()

	initGraph(2, 7, 10, 1.0, 0.3, 0.1, 0.5, 0.1, 0.3)

	'''
	g = Graph()
	
	total = 34
	adjMat = []
	temp = []
	nodes = []
	for i in range(total):
		n = g.add_node("n"+str(i))
		nodes.append(n)
		if (i >=0 and i <= 9) or (i >=10 and i <= 19) or (i >=20 and i <= 29) :
			n['tier'] = '3'
		elif i ==33:
			n['tier'] = '1'
		else:
			n['tier'] = '2'
		for j in range(total):
			temp.append(0)
		adjMat.append(temp)
		temp = []
	

	# n1 = g.add_node("A")
	# n2 = g.add_node("B")
	# n3 = g.add_node("C")
	# n4 = g.add_node("D")
	# n5 = g.add_node("E")

	for i in range(10):
		g.add_edge(nodes[i],nodes[-4])
		g.add_edge(nodes[10+i],nodes[-3])
		g.add_edge(nodes[20+i],nodes[-2])
		adjMat[i][-4] = 1
		adjMat[10+i][-3] = 1
		adjMat[20+i][-2] = 1
	
	g.add_edge(nodes[30],nodes[31])
	g.add_edge(nodes[30],nodes[32])
	g.add_edge(nodes[31],nodes[32])
	g.add_edge(nodes[30],nodes[33])
	g.add_edge(nodes[31],nodes[33])
	g.add_edge(nodes[32],nodes[33])
	adjMat[30][31] = 1
	adjMat[30][32] = 1
	adjMat[31][32] = 1
	adjMat[30][33] = 1
	adjMat[31][33] = 1
	adjMat[32][33] = 1

	# g.add_edge(n1, n3)
	# g.add_edge(n2, n3)
	# g.add_edge(n3, n4)
	# g.add_edge(n3, n5)

	'''
	fname = "firstTestnew1.graphml"
	parser = GraphMLParser()

	parser.write(graphObj, fname)
	# parser.write(g, fname)