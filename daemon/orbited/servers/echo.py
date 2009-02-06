from twisted.internet import protocol

class Echo(protocol.Protocol):
    def dataReceived(self, data):
        self.transport.write(data)
