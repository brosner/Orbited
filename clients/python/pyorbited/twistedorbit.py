# Author: Michael Carter
# Email: CarterMichael@gmail.com
#
# Please note that this is an incomplete implementation of the client api. As
# of version 0.1 it works only with a single server
from twisted.internet import reactor, defer
from twisted.python import log
from twisted.internet.protocol import Protocol, ClientFactory
from twisted import internet
import simplejson
import sys

make_json = simplejson.encoder.JSONEncoder().encode

class OrbitRequest(object):
    def __init__(self, id, deferred, recipients, data):
        self.id = id
        self.deferred = deferred
        self.recipients = recipients
        self.data = data
    
    def render(self):
        out = "Orbit 1.0\r\nEvent\r\nid: %s\r\nlength: %s\r\n" % (self.id, len(self.data))
        for r in self.recipients:
            out += "recipient: %s\r\n" % r
        out += "\r\n"
        out += self.data
        return out
    
    def success(self, status, headers):
        response = OrbitResponse(status, headers)
        self.deferred.callback(response)
    

class OrbitResponse(object):
    def __init__(self, status, headers):
        self.status = status
        self.headers = headers
    

class OrbitProtocol(Protocol):
    def __init__(self, factory):
        self.factory = factory
        self.buffer = ""
        self.write_buffer = ""
        self.requests = dict()
        self.pending = []
        self.id = 0
    
    def event(self, recipients, data, jscript=True):
        self.id+=1
        if jscript:
            data = make_json(data)
        d = defer.Deferred()
        self.requests[self.id] = OrbitRequest(self.id, d, recipients, data)
        self.transport.write(self.requests[self.id].render())
        return d
    
    def dataReceived(self, data):
        self.buffer += data
        self.process()
    
    def process(self):
        while '\r\n\r\n' in self.buffer:
            req, self.buffer = self.buffer.split('\r\n\r\n', 1)                
            lines = req.split('\r\n')
            action = lines[0]
            headers = {}
            recipients = []
            for line in lines[1:]:
                key, val = line.split(': ')
                if key == 'recipient':
                    recipients.append(val)
                else:
                    headers[key] = val
            if recipients:
                headers['recipients'] = recipients
            self.requests[int(headers['id'])].success(action, headers)
            self.requests.pop(int(headers['id']))
    

class OrbitFactory(ClientFactory):
    protocol = OrbitProtocol
    def __init__(self):
        self.client = None
    
    def buildProtocol(self, addr):
        self.client = self.protocol(self)
        return self.client
    

class OrbitClient(object):
    def __init__(self, addr="localhost", port=9000):
        self.factory = OrbitFactory()
        reactor.connectTCP(addr, port, self.factory)
    
    def event(self, recipients, event, jscript=True):
        return self.factory.client.event(recipients, event, jscript)
    
