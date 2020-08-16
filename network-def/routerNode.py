# -*- coding: utf-8 -*-


class RouterNode():

    def __init__(self,nodeID, address, prefix, hosts, tierType, dg,  nextIntfNum):
        self.nodeID = nodeID
        self.address = address
        self.prefix = prefix
        self.tierType = tierType
        self.dg = dg
        self.hosts = hosts
        self.nextIntfNum = nextIntfNum