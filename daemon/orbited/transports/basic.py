from orbited.util import formatBlock
from orbited.transports.raw import RawTransport
from orbited.http.content import HTTPContent

class BasicTransport(RawTransport):
    name = 'basic'
    initial_data = formatBlock('''
        HTTP/1.1 200 OK
        Content-Type: text/html
    ''') + '\r\n\r\n'
    
    def accept_browser_connection(self, conn):
        RawTransport.accept_browser_connection(self, conn)
        self.browser_conn.respond(HTTPContent(self.initial_data))
    
    def encode(self, data):
        data = '<b>%s</b><br>\r\n' % (data,)
        return data

    def ping_render(self):
        return '<i>Ping!</i><br>\r\n'

