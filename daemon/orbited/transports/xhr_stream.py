from orbited.log import getLogger
from orbited.util import formatBlock
from orbited.transports.stream import StreamTransport
from orbited.config import map as config
from orbited.http.content import HTTPClose, HTTPContent

class XHRStreamTransport(StreamTransport):
    name = 'xhr_stream'
    boundary = '\r\n|O|\r\n'
    initial_data = formatBlock('''
        HTTP/1.1 200 OK
        Content-Type: application/x-orbited-event-stream
    ''') + '\r\n\r\n'
    
    # initial data for safari
    initial_data += '.'*256 + '\r\n\r\n'
        
    def encode(self, data):        
        return data + self.boundary
    
    def ping_render(self):
        return self.boundary + 'ping' + self.boundary
