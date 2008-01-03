from orbited.log import getLogger
from orbited.util import formatBlock
from orbited.transports.stream import StreamTransport
from orbited.config import map as config

class ServerSentEventsTransport(StreamTransport):
    name = 'server_sent_events'
    
    initial_data = formatBlock('''
        HTTP/1.1 200 OK
        Content-Type: application/x-dom-event-stream
    ''') + '\r\n\r\n'
    
    def encode(self, data):
        return (
            'Event: orbited\n' +
            '\n'.join(['data: %s' % line for line in data.splitlines()]) +
            '\n\n'
        )
    
    def ping_render(self):
        return (
            'Event: ping\n' +
            'data: \o/' +
            '\n\n'
        )
    
