import event
from orbited.log import getLogger
from orbited.config import map as config
from orbited import io
from connection import ReplicationConnection

# TODO: accept conf as arg to ReplicationDaemon.__init__ instead.
revconf = config.get('[revolved]', {})
logger = getLogger('ReplicationDaemon')
access = getLogger('ACCESS')
            
class ReplicationDaemon(object):
    
    def __init__(self, revolved):
        self.revolved = revolved
        self.port = int(revconf.get('replication.port', 8500))
        sock = io.server_socket(self.port)
        logger.info("Listening on port %s" % self.port)
        self.listen = event.event(self.accept_connection, handle=sock, evtype=event.EV_READ | event.EV_PERSIST)
        self.listen.add()
        self.connections = []
        self.initial_connects()
        
    def accept_connection(self, ev, sock, event_type, *arg):
        logger.debug('Accept Connection, ev: %s, sock: %s, event_type: %s, *arg: %s' % (ev, sock, event_type, arg))        
        sock, addr = sock.accept()
        self.connections.append(ReplicationConnection(self, sock, addr))
    
    
    def publish(self, channel, sender, payload):
        for connection in self.connections:
            connection.publish(channel, sender, payload)
        
    def disconnect(self, conn, reason):
        logger.info("Disconnect: %s:%s (%s)" % (conn.addr, conn.port, reason))
        self.connections.remove(conn)
        
    def initial_connects(self):
        
        servers = revconf.get('replication.peers')
        if not servers:
            return
        servers = servers.split(',')
        parsed = []
        for server in servers:
            if ':' in server:
                host, port = server.strip().split(':')
                port = int(port)
                parsed.append((host, port))
            else:
                parsed.append((server, 8500))
        
        for host, port in parsed:
            self.connect(host, port)
            
    def connect(self, host, port):
        sock = io.client_socket(host, port)
        logger.info("Connecting to %s:%s" % (host, port))
        self.connections.append(ReplicationConnection(self, sock, (host, port)))
