import event
from orbited.log import getLogger
from orbited.config import map as config
from orbited import io
from http import HTTPConnection

logger = getLogger('HTTPDaemon')
access = getLogger('ACCESS')
            
class HTTPDaemon(object):
    
    def __init__(self, app):
        self.app = app
        self.port = int(config['[global]']['http.port'])
        sock = io.server_socket(self.port)
        self.listen = event.event(self.accept_connection, handle=sock, evtype=event.EV_READ | event.EV_PERSIST)
        self.listen.add()
    
    def accept_connection(self, ev, sock, event_type, *arg):
        logger.debug('Accept Connection, ev: %s, sock: %s, event_type: %s, *arg: %s' % (ev, sock, event_type, arg))
        sock, addr = sock.accept()
        HTTPConnection(self, sock, addr)
    
