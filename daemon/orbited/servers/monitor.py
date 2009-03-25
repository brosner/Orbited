from twisted.internet import protocol, reactor
from orbited.config import map as config
from orbited import json
import os, platform

class Monitor(protocol.Protocol):
    def __init__(self):
        self.pid = os.getpid()
        fd = os.popen("ps -p %s -o user"%self.pid)
        self.user = fd.readlines()[1].strip()
        self.cpu = None
        self.mem = None
        self.connections = None
        self.timer = reactor.callLater(0, self.sendInitial)

    def getConnections(self):
        return config['globalVars']['connections']

    def connectionLost(self, reason):
        self.timer.cancel()
        self.timer = None

    def send(self, data):
        self.transport.write(json.encode(data)+'~')

    def init(self, data):
        self.send(['INIT', data])

    def update(self, data):
        self.send(['UPDATE', data])

    def sendInitial(self):
        if platform.system() == 'Windows':
            self.init(['connections'])
            self.timer = reactor.callLater(1, self.reportWindows)
        else:
            self.init(['user','pid','cpu','mem','connections'])
            self.update({'user':self.user,'pid':self.pid})
            self.timer = reactor.callLater(1, self.report)

    def reportWindows(self):
        connections = self.getConnections()
        if connections != self.connections:
            self.connections = connections
            self.update({'connections':connections})
        self.timer = reactor.callLater(1, self.reportWindows)

    def report(self):
        fd = os.popen("ps -p %s -o %%cpu,%%mem"%os.getpid())
        row = fd.readlines()[1].strip()
        fd.close()
        cpu, mem = [word for word in row.split(' ') if word]
        connections = self.getConnections()
        data = {}
        if cpu != self.cpu:
            data['cpu'] = cpu
            self.cpu = cpu
        if mem != self.mem:
            data['mem'] = mem
            self.mem = mem
        if connections != self.connections:
            data['connections'] = connections
            self.connections = connections
        if data:
            self.update(data)
        self.timer = reactor.callLater(1, self.report)