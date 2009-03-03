#from twisted.internet import reactor
from orbited import logging
from orbited.transports.base import CometTransport

MAXBYTES = 1048576
#MAXBYTES = 64
class XHRStreamingTransport(CometTransport):

    logger = logging.get_logger('orbited.transports.xhrstream.XHRStreamingTransport')

    def opened(self):
        self.totalBytes = 0
        # Force reconnect ever 45 seconds
#        self.close_timer = reactor.callLater(45, self.triggerCloseTimeout)
        self.request.setHeader('content-type', 'application/x-orbited-event-stream')
        # Safari/Tiger may need 256 bytes
        self.request.write(' ' * 256)

    def triggerCloseTimeout(self):
        self.logger.debug('triggerCloseTimeout called')
        self.close()

    def write(self, packets):
        self.logger.debug('write %r' % packets)
        # TODO why join the packets here?  why not do N request.write?
        payload = self.encode(packets)
        self.logger.debug('WRITE ' + payload)
        self.request.write(payload)
        self.totalBytes += len(payload)
        if (self.totalBytes > MAXBYTES):
            self.logger.debug('over maxbytes limit')
            self.close()

    def encode(self, packets):
        output = []
        for packet in packets:
            for i, arg in enumerate(packet):
                if i == len(packet) -1:
                    output.append('0')
                else:
                    output.append('1')
                output.append(str(len(arg)))
                output.append(',')
                output.append(arg)
        return "".join(output)

    def writeHeartbeat(self):
        self.logger.debug('writeHeartbeat, ' + repr(self))
        self.request.write('x')