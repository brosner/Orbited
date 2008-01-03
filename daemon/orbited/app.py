import sys
import traceback
import StringIO
import event
from config import map as config
from http import HTTPDaemon
from log import getLogger
from orbited import session
from orbited.exceptions import InvalidTransport
from orbited.orbit import OPDaemon
#config = config.map

logger = getLogger('Application')
access = getLogger('ACCESS')
class Application(object):
    ''' Top-level Orbited object, which encapsulates an HTTP daemon, and an
        Orbit protocol daemon, each of which listens for connections on a
        different port.
    '''
    def __init__(self):
        self.http = HTTPDaemon(self)
        self.op = OPDaemon(self)
        self.sessions = {}
        self.requests = {}
    
    def dispatch_event(self, request):
        access.info('EVENT REQUEST\t%s/%s\t%s' % (request.connection.addr[0], request.id, request.length))
        self.requests[request.key()] = request
        for recipient in request.recipients:
            if recipient in self.sessions:
                self.sessions[recipient].event(request)
            else:
                access.info('EVENT FAILED\t%s/%s\t\n|---------------------- Recipient %s not Found' % (request.addr, request.id, recipient))
                request.failure(recipient)

        self.requests.pop(request.key())

    def accept_browser_connection(self, conn):
        conn_key = conn.key()
        if conn_key not in self.sessions:
            self.sessions[conn_key] = session.create(self, conn_key)
        self.sessions[conn_key].accept_browser_connection(conn)

    def expire_browser_connection(self, conn):
        if conn.key() in self.sessions:
            self.sessions[conn.key()].expire_browser_connection(conn)

    def remove_session(self, session):
        if session.key not in self.sessions:
            print 'remove_session error: %s not in self.sessions' % (session.key,)
            return
        del self.sessions[session.key]

    def start(self):

        def collect_toplevel_exceptions():
            return True

        event.timeout(1, collect_toplevel_exceptions)
        while True:
            try:
                event.dispatch()
            except KeyboardInterrupt, k:
                event.abort()
                print 'Received Ctr+c shutdown'
                sys.stdout.flush()
                sys.exit(0)

            except Exception, e:
                exception, instance, tb = traceback.sys.exc_info()
                if 'exceptions must be strings' in str(instance):
                    print "Error in pyevent 0.3 on ubuntu in python 2.5. See http://orbited.org/pyevent.html for details"
                    event.abort()
                    sys.exit(0)
                # TODO: Start: There is certainly a better way of doing this
                x = StringIO.StringIO()
                traceback.print_tb(tb, file=x)
                x = x.getvalue()
                relevant_line = x.split('\n')[-3]
                # End: Find a better way

                logger.critical('%s:%s\t%s' % (exception, instance, relevant_line))
                print x

