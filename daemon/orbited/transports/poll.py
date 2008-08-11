from twisted.internet import reactor
from orbited import logging
from orbited.transports.base import CometTransport


class PollingTransport(CometTransport):

    logger = logging.get_logger('orbited.transports.longpoll.PollingTransport')

    def opened(self):
        self.request.setHeader('cache-control', 'no-cache, must-revalidate')

    def triggerCloseTimeout(self):
        self.close()

    # NOTE: we override this so we can close as soon as we send out any waiting
    #       packets. We can't put the self.close call inside of self.write 
    #       because sometimes there will be no packets to write.
    def flush(self):
        CometTransport.flush(self)
        self.close()

    def write(self, packets):
        self.logger.debug('write %r' % packets)
        payload = self.encode(packets)
        self.logger.debug('WRITE ' + payload)        
        self.request.write(payload)
        
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
        # NOTE: no heartbeats...
        pass
