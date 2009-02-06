from twisted.internet import protocol

class LineEcho(protocol.Protocol):
    def __init__(self):
        self.buffer = ''

    def dataReceived(self, data):
        self.buffer += data
        chunks = self.buffer.split('\n')
        self.buffer = chunks.pop()
        for chunk in chunks:
            self.transport.write(chunk+'\n')
