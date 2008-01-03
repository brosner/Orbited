from config import map as config
import transport
import event
timeout = int(config['[global]']['session.timeout'])
retry_limit = int(config['[global]']['event.retry_limit'])

def create(app,key):
    return Session(app,key)

class EventRequestWrapper(object):

    def __init__(self, session, request):
        self.session = session
        self.request = request
        self.failure_count = 0

    def success(self):
        self.request.success(self.session.key)

    def failure(self):
        self.failure_count += 1
        self.session.retry(self)

    def __getattr__(self, attr):
        return getattr(self.request, attr)


class Session(object):

    def __init__(self, app, key):
        self.key = key
        self.app = app
        self.transport = None
        self.timer = None
        self.events = []
        self.transport_ready = False

    def close(self):
        if self.transport:
            self.transport.close()
        if self.timer:
            self.timer.delete()
            self.timer = None
        self.app.remove_session(self)

    def event(self, request):
        self.events.append(EventRequestWrapper(self, request))
        self.flush()

    def flush(self):
        while self.events and self.transport_ready:
            # TODO: figure out how to batch events
            e = self.events.pop(0)
            self.transport.event(e) # actually send event using transport

    def set_ready(self):
        self.transport_ready = True
        self.flush()

    def set_unready(self):
        self.transport_ready = False

    def retry(self, request_wrapper):
        if request_wrapper.failure_count > retry_limit:
            request_wrapper.request.failure(self.key)
        else:
            self.events.append(request_wrapper)
            self.flush()

    def unset_timer(self):
        self.timer.delete()
        self.timer = None

    def reset_timer(self):
        if self.timer:
            self.unset_timer()
        self.timer = event.timeout(timeout, self.timed_out)

    def timed_out(self):
        self.timer = None
        self.app.remove_session(self)
#        self.transport.close()

    def remove_transport(self, transport):
        if self.transport is transport:
            self.transport = None
            self.set_unready()
            self.reset_timer() 

    def accept_browser_connection(self, conn):
        # cannot find transport
        if conn.transport not in transport.map:
            raise InvalidTransport, '%s is not a valid Orbited Transport' % conn.transport

        # existing connection, wrong transport
        if self.transport and conn.transport != self.transport.name:
            # logger.warn('Connect key exists. Switching transports %s -> %s' %
            # self.transport will be set to None            
            self.transport.close()
            # TODO: this case causes the timer to be reset then unset. fix it.

        if not self.transport:
            self.transport = transport.create(self, conn.transport, self.key)
            if self.timer:
                self.unset_timer()

        self.transport.accept_browser_connection(conn)


    def expire_browser_connection(self, browser_conn):
        self.transport.expire_connection(browser_conn)

