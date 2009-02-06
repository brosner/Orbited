from twisted.internet import protocol

class Rude(protocol.Protocol):
    def dataReceived(self, data):
        self.transport.loseConnection()
