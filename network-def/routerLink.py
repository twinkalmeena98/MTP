# -*- coding: utf-8 -*-


class RouterLink():

    def __init__(self,r1, r2, intfName1, intfName2, ip1, ip2, linkType):
        self.r1 = r1
        self.r2 = r2
        self.intfName1 = intfName1
        self.intfName2 = intfName2
        self.ip1 = ip1
        self.ip2 = ip2
        self.linkType = linkType