from orbited.util import format_block
from orbited import json
from twisted.internet import reactor
from base import CometTransport

from orbited import logging
logger = logging.get_logger('orbited.transports.sse.SSETransport')

class SSETransport(CometTransport):
    HEARTBEAT_INTERVAL = 30
    def opened(self):
        self.request.setHeader('content-type', 'application/x-dom-event-stream')
        self.request.setHeader('cache-control', 'no-cache, must-revalidate')   
            
    def write(self, packets):
        payload = json.encode(packets)
        data = (
            'Event: payload\n' +
            '\n'.join(['data: %s' % line for line in payload.splitlines()]) +
            '\n\n'
        )
        self.request.write(data)
        
    def writeHeartbeat(self):
        logger.debug('writeHeartbeat');
        self.request.write('Event: heartbeat\n\n')