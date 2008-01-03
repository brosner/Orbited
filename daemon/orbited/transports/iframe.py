from orbited.log import getLogger
from orbited.util import formatBlock
from orbited.transports.stream import StreamTransport
from orbited.config import map as config

class IFrameTransport(StreamTransport):
    name = 'iframe'
    headers = formatBlock('''
        HTTP/1.1 200 OK
        Content-Length: 1000000
        Content-Type: text/html
        Cache-Control: no-cache
    ''') + '\r\n\r\n'
    
    initial_html = formatBlock('''
        <html>
        <head>
          <script src="/_/iframe.js" charset="utf-8"></script>
        </head>
        <body onLoad="reload();">
    ''')
    initial_html += '<span></span>' * 100
    
    initial_data = headers + initial_html
    
    def encode(self, data):
        data = '<script>e(%s);</script>' % (data,)
        return data
    
    def ping_render(self):
        return '<script>p();</script>'
    
