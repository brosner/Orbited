from orbited.log import getLogger
from orbited.util import formatBlock
from orbited.transports.stream import StreamTransport
from orbited.config import map as config
from orbited.http.content import HTTPClose, HTTPContent

class XHRMultipartTransport(StreamTransport):
    name = 'xhr_multipart'
    boundary = config['[transport]'].get('xhr_multipart.boundary','orbited--')
    multipart_content_type = 'application/json'
    
    def get_initial_data(self):
        data = formatBlock('''
            HTTP/1.1 200 OK
            Content-Type: multipart/x-mixed-replace;boundary="%s"
        ''') % self.boundary + '\r\n\r\n'
        return data
    
    initial_data = property(get_initial_data)
        
    def encode(self, data):
        boundary = "\r\n--%s\r\n" % self.boundary
        headers = (formatBlock('''
            Content-type: %s
            Content-length: %s
        ''') + '\r\n\r\n') % (self.multipart_content_type, len(data))
        return ''.join([headers, data, boundary])
    
    def ping_render(self):
        return self.encode('')
    
