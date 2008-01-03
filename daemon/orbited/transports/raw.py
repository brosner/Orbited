from orbited.log import getLogger
from orbited.transport import Transport, TransportContent
from orbited.http.content import HTTPContent
from orbited.config import map as config
import event
access = getLogger('ACCESS')

class RawTransport(Transport):
#    import logging
    logger = getLogger('RawTransport')
#    logger.setLevel(logging.DEBUG)
    name = 'raw'
    
    def setup(self, session, key):
        self.key = key
        self.session = session
        self.browser_conn = None
        self.active = True
        self.ping_timer = event.timeout(0.5, self.ping)
    
    def close(self):
        self.browser_conn.close()
        self.active = False
        self.ping_timer.delete()
        self.session.remove_transport(self)
        self.ping_timer.delete()
    
    def accept_browser_connection(self, conn):
        self.logger.debug('entered accept_browser_connection')
        if self.browser_conn is not None:
            self.logger.debug('self.browser_conn already exists, closing.')
            c = self.browser_conn
            self.browser_conn = None
            c.close()
        self.browser_conn = conn
        self.ping_reset()
        self.session.set_ready()
    
    # TODO: add "events" function which takes batched events, and returns a
    #       list of unsent events
    def event(self, request):        
        self.logger.debug('dispatch event, request: %s' % request)
        self.browser_conn.respond(TransportContent(self, request, self.browser_conn))
        self.ping_reset()

    def ping(self):
        self.browser_conn.respond(HTTPContent(self.ping_render()))
        return True

    def ping_render(self):
        return ""

    def ping_reset(self):
        self.ping_timer.delete()
        self.ping_timer = event.timeout(60, self.ping)

    def success(self, request, conn):
        self.logger.debug('event sent successfuly, request: %s' % request)
        access.info('EVENT DELIVERED\t%s -> %s' % (request.id, conn.recipient()))
        request.success()

    def failure(self, request, conn, reason):
        self.logger.debug('event failed, request: %s' % request)
        access.warn('EVENT FAILED\t%s/%s -> %s\n\t\t%s' % (request.addr, request.id, conn.recipient(), reason))
        request.failure()
    
    def expire_connection(self, browser_conn):
        if browser_conn == self.browser_conn:
            self.session.remove_transport(self)
            self.ping_timer.delete()
    
    def encode(self, data):
        return data
    
