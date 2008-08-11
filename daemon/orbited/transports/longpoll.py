from twisted.internet import reactor
from orbited import logging
from orbited.transports.base import CometTransport


class LongPollingTransport(CometTransport):

    logger = logging.get_logger('orbited.transports.longpoll.LongPollingTransport')

    def opened(self):
        self.totalBytes = 0
        # Force reconnect ever 45 seconds
        self.close_timer = reactor.callLater(30, self.triggerCloseTimeout)
        self.request.setHeader('content-type', 'orbited/event-stream')
        # Safari/Tiger may need 256 bytes
        self.request.write(' ' * 256)

    def triggerCloseTimeout(self):
        self.close()

    def write(self, packets):
        self.logger.debug('write %r' % packets)
        # TODO why join the packets here?  why not do N request.write?
        payload = "".join([ self.encode(packet) for packet in packets])
        self.logger.debug('WRITE ' + payload)
        
        self.request.write(payload)
        self.close()

    def encode(self, packet):
        id, name, info = packet
        output = ""
        args = (id, name) + info
        return self.encode_args(args)
    
    def encode_args(self, args):
        output = ""
        for i, arg in enumerate(args):
            if i == len(args) -1:
                output += '0'
            else:
                output += '1'
            data = str(arg)
            output += str(len(data)) + ','
            output += data
        return output

    def writeHeartbeat(self):
        self.logger.debug('writeHeartbeat, ' + repr(self))
        self.request.write('x')
