import pkg_resources
from orbited.log import getLogger
from orbited.exceptions import DuplicateTransportName
from orbited.config import map as config

access = getLogger('ACCESS')
logger = getLogger('Transports')
map = {}

def create(app, name, key):
    return map[name](app, key)

def load_transports():
    for transport_entry in pkg_resources.iter_entry_points('orbited.transports'):
        transport = transport_entry.load()
        if transport.name in map:
            raise DuplicateTransportName, 'The name %s exists twice' % transport.name
        logger.info('Loaded %s from %s' % (transport_entry.name, transport_entry.module_name))
        map[transport.name] = transport

class TransportContent(object):
    
    def __init__(self, transport, request, browser_conn):
        self.request = request
        self.transport = transport
        self.browser_conn = browser_conn
    
    def content(self):
        return self.transport.encode(self.request.payload)
    
    def success(self, conn):
        self.transport.success(self.request, self.browser_conn)
    
    def failure(self, conn, reason):
        self.transport.failure(self.request, self.browser_conn, reason)
    
class TransportMeta(type):
    _target = ['close', 'event', 'encode', 'accept_browser_connection',
               'expire_connection', 'success', 'failure']
    logger = getLogger('TransportMeta')
    
    def __init__(cls, name, bases, dct):
        logger.debug('__init__ %s, %s, %s, %s' % (cls, name, bases, dct))
        super(TransportMeta, cls).__init__(name, bases, dct)        
        if name == 'Transport':
            logger.debug("don't setup Transport")
            return
        for key in TransportMeta._target:
            if key not in dct:
                def dec(fname):
                    def meta_wrapper(self, *args):
                        if self.__class__ == cls:
                            args = getattr(Transport, fname)(self, *args)
                        return getattr(super(cls, self), fname)(*args)
                    return meta_wrapper    
                replacement = dec(key)
            else:
                orig_func = dct[key]
                def dec(fname, orig):
                    def meta_wrapper(self, *args):
                        if self.__class__ == cls:
                            args = getattr(Transport, fname)(self, *args)
                        return orig(self, *args)
                    return meta_wrapper                        
                replacement = dec(key, orig_func)
            setattr(cls, key, replacement)
    

class Transport(object):
    __metaclass__ = TransportMeta
    logger = getLogger("Transport")
    
    def __init__(self, app, key):
        self.setup(app, key)
    
    def setup(self, app, key):
        return app, key
    
    def close(self):
        return ()
    
    def event(self, request):
        return request,
    
    def ping(self):
        return ()
    
    def encode(self, data):
        return data,
    
    def accept_browser_connection(self, conn):
        return conn,
    
    def expire_connection(self, conn):
        return conn,
    
    def success(self, request, conn):
        return request, conn
    
    def failure(self, request, conn, reason):
        return request, conn, reason
    
