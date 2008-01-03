from orbited.buffer import Buffer
from orbited.log import getLogger
import event
from orbited import io

logger = getLogger("RevolvedReplication")

class ReplicationConnection(object):

    def __init__(self, daemon, sock, addr):
        self.daemon = daemon
        self.sock = sock
        self.addr, self.port = addr
        self.state = "channel"
        self.revent = event.read(self.sock, self.read_ready)
        self.wevent = None
        self.write_queue = []
        self.write_buffer = Buffer(mode='consume')
        self.buffer = Buffer(mode='consume')
        self.channel = None
        self.sender = None
        self.payload = None
        self.connected = False
        
    def close(self, reason="unknown"):
        if self.revent:
            self.revent.delete()
            self.revent = None
        if self.wevent:
            self.wevent.delete()
            self.wevent = None
        self.daemon.disconnect(self, reason)
        
    def publish(self, channel, sender, payload):
        self.write(self.pack(channel))
        self.write('\r\n')
        self.write(self.pack(sender))
        self.write('\r\n')
        self.write(self.pack(payload))
        self.write('\r\n')
        
    def pack(self, data):
        if isinstance(data, tuple):
            print "packing:", data
            data = ", ".join(data)
        return data.replace('\r\n', '|\r|\n')
        
    def unpack(self, data):
        return data.replace('|\r|\n','\r\n')
        

    def write(self, data):
        self.write_queue.append(data)
        if not self.wevent:
            self.wevent = event.write(self.sock, self.write_ready)
        
    def write_ready(self):
        if self.write_buffer.empty():
            if not self.write_queue:
                self.wevent = None
                return None
            self.write_buffer.reset(self.write_queue.pop(0))
        try:
            bsent = self.sock.send(self.write_buffer.get_value())
            self.write_buffer.move(bsent)
            return True
        except io.socket.error, msg:
            self.logger.debug('io.socket.error: %s' % msg)
            self.close(msg)
            return None
        
    def read_ready(self):
        if not self.connected:
            self.connected = True
            logger.info("Connected to: %s" % self.addr)
        try:          
            data = self.sock.recv(io.BUFFER_SIZE)
            print "RECV: %s" % data
            if not data:
                return None
            self.buffer += data
            return self.read()
        except io.socket.error, msg:
            self.close(msg)
            return None
            
            
    def read(self):
        while True:
            i = self.buffer.find('\r\n')
            if i == -1:
                return True
            if self.state == "channel":
                self.channel = self.unpack(self.buffer.part(0,i))
                self.state = "sender"
            elif self.state == "sender":
                self.sender = self.unpack(self.buffer.part(0,i))
                self.sender = self.sender.split(', ')
                self.state = "payload"
            elif self.state == "payload":
                payload = self.unpack(self.buffer.part(0,i))
                self.daemon.revolved.publish(self.channel, self.sender, 
                                             payload, replicated=True)
                self.state = "channel"                
            self.buffer.move(i+2)
        
            