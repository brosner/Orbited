import os
from twisted.internet import reactor

class Graph(object):

    def __init__(self, filename):
        self.index = self.config()
        self.filename = filename

    def reset(self):
        self.mpstat = os.popen2('/usr/bin/mpstat 1')[1]
        self.mpstat.read(136)

    def config(self):
        r = open('/proc/meminfo','r').read().split('\n')
        for n,line in enumerate(r):
            if 'MemTotal:' in line:
                return n
        pass
    def update(self):        
#        cpu = 100 - float(self.mpstat.read(91)[75:80])
        r = open('/proc/meminfo','r').read()
        mem = 100 - 100*(float(r.split('\n')[self.index+1][9:][:-2].strip()) / float(r.split('\n')[self.index][9:][:-2].strip()))
#        return [cpu, mem]
        f = open(self.filename, 'r')
        data = f.read()
        try:
            email_rate = float(data)
#            return [0, float(data)]
        except:
            email_rate = 0
        return [float(data), mem]


