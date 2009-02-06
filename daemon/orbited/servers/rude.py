from twisted.internet import reactor, protocol

class Rude(protocol.Protocol):
    def dataReceived(self, data):
        self.transport.loseConnection()