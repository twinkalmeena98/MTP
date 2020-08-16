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
import string 
nodeNum = 0
edgeNum = 0
alphabetKeys = [i for i in range(26)]
alphabet = dict(zip(alphabetKeys, string.ascii_uppercase))
curasn = 0
l1num = 0
l2num = 0
l3num = 0
l41num = 0
l42num = 0
l5num = 0

defaultChild = 2

def getTwoLetterCode(number):
    first = alphabet[number/26]
    second = alphabet[number%26]
    return first + second

def addNode(graphObj,nodeNum,level,one,two,three,asn = False):
    global curasn,l1num,l2num,l3num,l41num,l42num,l5num
    if asn == True:
        code = getTwoLetterCode(one) + '/' + getTwoLetterCode(two) + '/' + getTwoLetterCode(three) + '/AS' + str(curasn)
        curasn = curasn + 1
    else:
        code = getTwoLetterCode(one) + '/' + getTwoLetterCode(two) + '/' + getTwoLetterCode(three)
        # code = 'C' + alphabet[one] + '/' + 'S' + alphabet[two] + '/' + 'D' + alphabet[three]
    if level == 5:
        print("code", code)
    if level == 1:
        nodeid = 'i' + str(l1num)
        l1num += 1
    elif level == 2:
        nodeid = 'n' + str(l2num)
        l2num += 1
    elif level == 3:
        nodeid = 's' + str(l3num)
        l3num += 1
    elif level == 41:
        nodeid = 'h' + str(l41num)
        l41num += 1
    elif level == 42:
        nodeid = 'hr' + str(l42num)
        l42num += 1
    elif level == 5:
        nodeid = 'as' + str(l5num)
        l5num += 1
    n = graphObj.add_node(nodeid)
    n['level'] = level
    n['code'] = code

    return n

def connectMesh(graphObj, rlist):
    global edgeNum
    for temp_i in range(len(rlist)):
        none = rlist[temp_i]
        for ntwo in rlist[temp_i+1:]:
            graphObj.add_edge(none, ntwo)
            edgeNum += 1

# international : number of nodes at the international level or level 1
# national : number of nodes at the national level or level 2
# state : number of nodes at the state level or level 3
# city : number of hubs at the city level or level 4, each hubs consists of hub_r number of routers in mesh connection
# hub_r : number of routers in a hub at the city level
# ases : number of ases that a rotuers at the hub is connected to
def createSymmetricGraph(graphObj, international, national, state, city, hub_r, ases):
    global nodeNum, edgeNum
    #TODO: adding default write using this section of code only
    temp1 = []
    for i in range(international):
        n1 = addNode(graphObj,nodeNum,1,i,0,0)
        temp1.append(n1)
        nodeNum += 1
        # print(i, nodeNum)
        # Special case for India/Country level only
        defaultChildException = 1
        for z1 in range(defaultChildException):
            temp2 = []
            for j in range(national):
                n2 = addNode(graphObj,nodeNum,2,i*defaultChildException + z1,j*defaultChild,0)
                temp2.append(n2)
                nodeNum += 1
                # print(i, nodeNum)
                print("nodenum", nodeNum)
                if j == 0:
                    graphObj.add_edge(n1,n2)
                    edgeNum += 1
                
                for z2 in range(defaultChild):
                    temp3 = []
                    for k in range(state):
                        n3 = addNode(graphObj,nodeNum,3,i*defaultChildException + z1,j*defaultChild + z2, k*defaultChild)
                        temp3.append(n3)
                        nodeNum += 1
                        if k == 0:
                            graphObj.add_edge(n2,n3)
                            edgeNum += 1
                        
                        for z3 in range(defaultChild):
                            temp4 = []
                            for l in range(city):
                                temp = []
                                for m in range(hub_r):
                                    n4 = ""
                                    if m == 0 and l == 0:
                                        
                                        n4 = addNode(graphObj,nodeNum,41,i*defaultChildException + z1, j*defaultChild + z2, k*defaultChild + z3)
                                        temp4.append(n4)
                                        graphObj.add_edge(n3,n4)
                                        edgeNum += 1
                                    elif m == 0:
                                        n4 = addNode(graphObj,nodeNum,41,i*defaultChildException + z1, j*defaultChild + z2, k*defaultChild + z3)
                                        temp4.append(n4)
                                    else: 
                                        n4 = addNode(graphObj,nodeNum,42,i*defaultChildException + z1, j*defaultChild + z2, k*defaultChild + z3)
                                    temp.append(n4)
                                    nodeNum += 1
                                    for n in range(ases):
                                        n5 = addNode(graphObj,nodeNum,5,i*defaultChildException + z1, j*defaultChild + z2, k*defaultChild + z3,True)
                                        nodeNum += 1
                                        graphObj.add_edge(n4,n5)
                                        edgeNum += 1
                                connectMesh(graphObj,temp)
                            connectMesh(graphObj,temp4)
                    connectMesh(graphObj,temp3)
            connectMesh(graphObj,temp2)
    connectMesh(graphObj,temp1)

if __name__ == "__main__":
    
    parser = GraphMLParser()
    g = Graph()
    
    createSymmetricGraph(g, 1, 2, 2, 2, 2, 1)
    
    
    print(nodeNum)
    print(edgeNum)
    print(l1num,l2num,l3num,l41num,l42num,l5num)
    fname = "symmetricGraph.graphml"
    parser = GraphMLParser()
    parser.write(g, fname)