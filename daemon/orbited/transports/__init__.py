import xhrstream
import htmlfile
import sse
map = {
    'xhrstream': xhrstream.XHRStreamingTransport,
    'htmlfile': htmlfile.HTMLFileTransport,
    'sse': sse.SSETransport
}
def create(transport_name, conn):
#    transport_name = request.args.get('transport', ['xhrstream'])[0]    
    x = map.get(transport_name, None)
    if not x:
        return None
    return x(conn)
