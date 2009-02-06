from twisted.internet import protocol, reactor

class Rude(protocol.Protocol):
    def __init__(self):
        reactor.callLater(0.0001, self.hang_up)

    def hang_up(self):
        self.transport.loseConnection()