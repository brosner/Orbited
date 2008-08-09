from zope.interface import implements
from twisted.internet import reactor, interfaces
from twisted.internet.protocol import Protocol, Factory
class Port(object):
    
    implements(interfaces.IListeningPort)
    def __init__(self, port, factory, backlog=50, interface='', reactor=None):
        self.port = port
        self.factory = factory
        self.backlog = backlog
        self.interface = interface
        self.wrapped_factory = FakeTCPFactory(self, factory)
        self.wrapped_port = None
        self.listening = False
                
    def startListening(self):
        if not self.listening:
            self.listening = True
            self.wrapped_port = reactor.listenTCP(self.port, self.wrapped_factory, self.backlog, self.interface)
        
    def stopListening():
        if self.listening:
            self.wrapped_port.stopListening()
        
        
    def connectionMade(self, transportProtocol):
        """
            proto is the tcp-emulation protocol
            
            protocol is the real protocol on top of the transport that depends
            on proto
            
        """
        protocol = self.factory.buildProtocol(transportProtocol.getPeer())
        if protocol is None:
            transportProtocol.transport.loseConnection()
            return
        transport = FakeTCPTransport(transportProtocol, protocol)
        transportProtocol.parentTransport = transport
        protocol.makeConnection(transport)
        
    def getHost():
        return self.wrapped_port.getHost()
    

class FakeTCPTransport(object):
    implements(interfaces.ITransport)
    
    def __init__(self, transportProtocol, protocol):
        self.transportProtocol = transportProtocol
        self.protocol = protocol
        
    # ==========================
    # "Real" protocol facing API
    # ==========================
    
    def write(self, data):
        self.transportProtocol.write(data)

    def writeSequence(self, data):
        self.transportProtocol.writeSequence(data)

    def loseConnection():
        self.transportProtocol.loseConnection()

    def getPeer():
        return self.transportProtocol.getPeer()

    def getHost():
        return self.transportProtocol.getHost()

    # ==============================
    # transport emulation facing API
    # ==============================
        
    def dataReceived(self, data):
        self.protocol.dataReceived(data)
        
    def connectionLost(self):
        self.protocol.connectionLost()
        
        
class FakeTCPFactory(Factory):
    def __init__(self, listeningPort, real_factory):
        self.real_factory = real_factory
        self.listeningPort = listeningPort
        
    def buildProtocol(self, addr):
        p = FakeTCPProtocol()
        p.factory = self
        
        return p
        
    def connectionMade(self, proto):
        self.listeningPort.connectionMade(proto)
        
        
class FakeTCPProtocol(Protocol):
    
    #=================
    # Public interface
    # ================    

    def write(self, data):
        self.transport.write(data)
        
    def writeSequence(self, sequence):
        self.transport.writeSequence(sequence)
      
    def loseConnection(self):
        self.transport.loseConnection()
        
    def getPeer(self):
        return self._peer
    
    def getHost(self):
        return self._host
    
    # ==============
    # Implementation
    # ==============
    
    def connectionMade(self):
        self._peer = self.transport.getPeer()
        self._host = self.transport.getHost()
        self.factory.connectionMade(self)
        
    def dataReceived(self, data):
        newData = data.replace('\r\n', '').replace('+', '\r\n')
        self.parentTransport.dataReceived(newData)
    
    def connectionLost(self):
        self.parentTransport.connectionLost()
    
    
    

    
if __name__ == "__main__":
class EchoProtocol(Protocol):
    
    def dataReceived(self, data):
        print "RECV:", data
        self.transport.write("Echo: " + data)
        
    def connectionMade(self):
        print "Connection Opened"
        
    def connectionLost(self):
        print "Connection Lost"
        
class EchoFactory(Factory):
    protocol = EchoProtocol  
    factory = EchoFactory()
    reactor.listenWith(Port, 7777, factory)
    reactor.run()