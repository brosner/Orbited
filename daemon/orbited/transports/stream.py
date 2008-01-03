from orbited.log import getLogger
from orbited.util import formatBlock
from orbited.transports.raw import RawTransport
from orbited.config import map as config
from orbited.http.content import HTTPClose, HTTPContent

class StreamTransport(RawTransport):
    name = 'stream'
    initial_data = formatBlock('''
        HTTP/1.1 200 OK
        Content-Type: text/html
    ''') + '\r\n\r\n'
    
    def accept_browser_connection(self, conn):
        RawTransport.accept_browser_connection(self, conn)
        self.browser_conn.respond(HTTPContent(self.initial_data))
    
