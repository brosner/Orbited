import event
from orbited.log import getLogger
from orbited.config import map as config
from orbited import io
from connection import ReplicationConnection

revconf = config.get('[revolved]', {})
logger = getLogger('ReplicationDaemon')
access = getLogger('ACCESS')
            
class ReplicationClient(object):
    
    def __init__(self, revolved, addr, port):
        self.revolved = revolved
        self.port = port
        self.addr = addr
        self.sock = io.client_socket(addr, port)
        self.connection = ReplicationConnection(self, self.sock, (addr, port))


    def publish(self, channel, sender, payload):
        self.connection.publish(channel, sender, payload)
