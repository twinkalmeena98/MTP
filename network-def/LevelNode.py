class LevelNode():

    def __init__(self,nodeID, addr,level, code, gw, hosts, nextIntfNum):
        self.nodeID = nodeID
        self.addr = addr
        self.level = level
        self.code = code
        self.gw = gw
        self.hosts = hosts
        self.nextIntfNum = nextIntfNum