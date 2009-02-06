from twisted.internet import protocol

class Announce(protocol.Protocol):
    def __init__(self):
        self.num = 1
        reactor.callLater(1, self.publish)

    def publish(self):
        self.transport.write("message %s"%self.num)
        self.num += 1
        reactor.callLater(1, self.publish)
