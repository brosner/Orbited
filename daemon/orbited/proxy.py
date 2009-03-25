from twisted.internet import reactor
from twisted.internet.protocol import ClientCreator
from twisted.internet.protocol import Factory
from twisted.internet.protocol import Protocol

from orbited import config
from orbited import logging

ERRORS = {
    'InvalidHandshake': 102,
    'RemoteConnectionTimeout': 104,
    'Unauthorized': 106,
    'RemoteConnectionFailed': 108,
}
pingTimeout  = int(config.map['[global]']['session.ping_timeout'])
pingInterval = int(config.map['[global]']['session.ping_interval'])


class ProxyIncomingProtocol(Protocol):
    """
    Handles the protocol between the browser and orbited, and proxies
    the data to a backend server.
    """

    logger = logging.get_logger('orbited.proxy.ProxyIncomingProtocol')

    def connectionMade(self):
        # TODO: add handshake timer
        self.transport.pingTimeout = pingTimeout
        self.transport.pingInterval = pingInterval
        self.logger.debug("connectionMade")
        self.state = 'handshake'
        # TODO rename this to outgoingProtocol
        self.outgoingConn = None
        self.completedHandshake = False

    def dataReceived(self, data):
        # NB: this only receives whole frames;  so we will just decode
        #     data as-is.
        # NB: its cometsession.py:TCPConnectionResource that makes sure
        #     we receive whole frames here.
        self.logger.debug('dataReceived: data=%r' % data)
        self.logger.debug('self.outgoingConn is', self.outgoingConn)

        if self.outgoingConn:
            # NB: outgoingConn is-a ProxyOutgoingProtocol
            self.logger.debug("write (out): %r" % data)
            return self.outgoingConn.transport.write(data)
        if self.state == "handshake":
            try:
                data = data.strip()
                host, port = data.split(':')
                port = int(port)
                self.completedHandshake = True
            except:
                self.logger.error("failed to connect on handshake", tb=True)
                self.transport.write("0" + str(ERRORS['InvalidHandshake']))
                self.transport.loseConnection()
                return
            peer = self.transport.getPeer()
            self.fromHost = peer.host
            self.fromPort = peer.port
            self.toHost = host
            self.toPort = port
            allowed = False
            for source in config.map['[access]'].get((host, port), []):
                if source == self.transport.hostHeader or source == '*':
                    allowed = True
                    break
            if not allowed:
                self.logger.warn('Unauthorized connect from %r:%d to %r:%d' % (self.fromHost, self.fromPort, self.toHost, self.toPort))
                self.transport.write("0" + str(ERRORS['Unauthorized']))
                self.transport.loseConnection()
                return
            self.logger.access('new connection from %s:%s to %s:%d' % (self.fromHost, self.fromPort, self.toHost, self.toPort))
            self.state = 'connecting'
            client = ClientCreator(reactor, ProxyOutgoingProtocol, self)
            client.connectTCP(host, port).addErrback(self.errorConnection) 
                # TODO: connect timeout or onConnectFailed handling...
        else:
            self.transport.write("0" + str(ERRORS['InvalidHandshake']))            
            self.state = 'closed'
            self.transport.loseConnection()

    def errorConnection(self, err):
        self.logger.warn("Connection Error %s" % (err,))
        self.transport.write("0" + str(ERRORS['RemoteConnectionFailed']))
        self.transport.loseConnection()
                
    def connectionLost(self, reason):
        self.logger.debug("connectionLost %s" % reason)
        if self.outgoingConn:
            self.outgoingConn.transport.loseConnection()
        if self.completedHandshake:
            self.logger.access('connection closed from %s:%s to %s:%s'%(self.fromHost, self.fromPort, self.toHost, self.toPort))

    def outgoingConnectionEstablished(self, outgoingConn):
        if self.state == 'closed':
            return outgoingConn.transport.loseConnection()
        self.outgoingConn = outgoingConn
        self.transport.write('1')
        self.state = 'proxy' # Not really necessary...
        
    def outgoingConnectionLost(self, outgoingConn, reason):
        self.logger.debug("remoteConnectionLost %s" % reason)
        self.transport.loseConnection()

    def write(self, data):
#        data = base64.b64encode(data)
        self.logger.debug("write %r" % data)
        self.transport.write(data)

class ProxyOutgoingProtocol(Protocol):
    """
    Handles the protocol between orbited and backend server.
    """

    logger = logging.get_logger('orbited.proxy.ProxyOutgoingProtocol')

    def __init__(self, incomingConn):
        # TODO rename this to incomingProtocol
        self.incomingConn = incomingConn

    def connectionMade(self):
        self.incomingConn.outgoingConnectionEstablished(self)
        config.map['globalVars']['connections'] += 1

    def dataReceived(self, data):
        self.logger.debug("dataReceived %r" % data)
        self.incomingConn.write(data)

    def connectionLost(self, reason):
        self.incomingConn.outgoingConnectionLost(self, reason)
        config.map['globalVars']['connections'] -= 1

class ProxyFactory(Factory):

    protocol = ProxyIncomingProtocol

